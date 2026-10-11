"""Durable DB worker: python -m app.worker --once (or --continuous).

Leases and conditional claims allow multiple workers. Network/PDF failures never
roll back membership. Resend's 24h idempotency window is respected fail-closed.
"""
import argparse
import time
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select, update

from app.db import SessionLocal
from app.models.accounts import User  # noqa: F401 - register FK target
from app.models.membership import Document, OutboxJob, Receipt, new_id, utcnow
from app.services.document_service import PreviewUnavailable, convert_preview
from app.services.email_service import EmailDeliveryError, send_receipt, send_welcome_email, send_membership_expiry_reminder
from app.services.membership_service import aware, iso
from app.services.receipt_service import ReceiptFontUnavailable, generate_receipt, private_path, receipt_path

MAX_ATTEMPTS = 8
LEASE_SECONDS = 600


class Deferred(Exception):
    pass


def email_window_expired(job):
    started = (job.payload or {}).get('email_first_attempt_at')
    return bool(started and utcnow() >= datetime.fromisoformat(started) + timedelta(hours=23))


def claim(db):
    now = utcnow()
    eligible = or_(and_(OutboxJob.status == 'pending', OutboxJob.available_at <= now),
                   and_(OutboxJob.status == 'processing', OutboxJob.locked_until <= now))
    job = db.scalar(select(OutboxJob).where(eligible).order_by(OutboxJob.available_at, OutboxJob.created_at)
                    .with_for_update(skip_locked=True).limit(1))
    if not job:
        db.rollback()
        return None
    token = new_id()
    changed = db.execute(update(OutboxJob).where(OutboxJob.id == job.id, eligible)
                         .values(status='processing', lock_token=token, locked_until=now + timedelta(seconds=LEASE_SECONDS),
                                 attempts=OutboxJob.attempts + 1).execution_options(synchronize_session=False)).rowcount
    job_id = job.id
    db.commit()
    return (job_id, token) if changed else None


def run_once(session_factory=SessionLocal):
    with session_factory() as db:
        claimed = claim(db)
    if not claimed:
        return False
    job_id, token = claimed
    generated = None
    result_error = None
    permanent = False
    deferred = False
    with session_factory() as db:
        job = db.scalar(select(OutboxJob).where(
            OutboxJob.id == job_id, OutboxJob.status == 'processing',
            OutboxJob.lock_token == token, OutboxJob.locked_until > utcnow()
        ).with_for_update().execution_options(populate_existing=True))
        if job is None:
            return True  # A stalled/reclaimed worker must not perform any effects.
        job.locked_until = utcnow() + timedelta(seconds=600)
        db.commit()
        job = db.scalar(select(OutboxJob).where(
            OutboxJob.id == job_id, OutboxJob.status == 'processing',
            OutboxJob.lock_token == token, OutboxJob.locked_until > utcnow()
        ).with_for_update().execution_options(populate_existing=True))
        if job is None:
            return True
        # Keep the ownership lock while bounded file/converter operations run.
        entity_id, kind = job.entity_id, job.kind
        try:
            if kind == 'receipt_pdf':
                receipt = db.get(Receipt, entity_id)
                if not receipt:
                    raise ValueError('missing_entity')
                if receipt.pdf_status != 'ready' or not receipt.storage_name or not receipt_path(receipt).is_file():
                    generated = generate_receipt(receipt)
            elif kind == 'receipt_email':
                receipt = db.get(Receipt, entity_id)
                if not receipt:
                    raise ValueError('missing_entity')
                if receipt.email_status != 'sent':
                    if email_window_expired(job):
                        permanent = True
                        raise EmailDeliveryError('email_retry_window_expired')
                    # Missing configuration has not contacted Resend, so it must
                    # not start the provider's finite idempotency retention window.
                    from app.config import settings
                    if not settings.RESEND_API_KEY or not settings.RESEND_FROM_EMAIL:
                        raise EmailDeliveryError('email_not_configured')
                    if not (job.payload or {}).get('email_first_attempt_at'):
                        job.payload = {'email_first_attempt_at': iso(utcnow())}
                        db.commit()  # Durable before a possibly ambiguous external request.
                    # The commit releases the lock. Re-read and fence ownership,
                    # lease and immutable first-attempt time before contacting Resend.
                    job = db.scalar(select(OutboxJob).where(
                        OutboxJob.id == job_id, OutboxJob.status == 'processing',
                        OutboxJob.lock_token == token, OutboxJob.locked_until > utcnow()
                    ).with_for_update().execution_options(populate_existing=True))
                    if job is None:
                        return True
                    if email_window_expired(job):
                        permanent = True
                        raise EmailDeliveryError('email_retry_window_expired')
                    send_receipt(receipt)
            elif kind == 'welcome_email':
                user = db.get(User, entity_id)
                if user and not user.disabled:
                    from app.config import settings
                    if not settings.RESEND_API_KEY or not settings.RESEND_FROM_EMAIL:
                        raise EmailDeliveryError('email_not_configured')
                    send_welcome_email(user)
            elif kind == 'membership_expiry_email':
                from app.models.membership import Membership
                user = db.get(User, entity_id)
                membership = db.get(Membership, entity_id)
                if user and not user.disabled and membership and not membership.revoked:
                    from app.config import settings
                    if not settings.RESEND_API_KEY or not settings.RESEND_FROM_EMAIL:
                        raise EmailDeliveryError('email_not_configured')
                    days_left = int((job.payload or {}).get('days_left', 2))
                    send_membership_expiry_reminder(user, membership, days_left=days_left)
            elif kind == 'document_preview':
                document = db.get(Document, entity_id)
                if document:  # deletion while a preview is pending is a harmless no-op
                    if document.preview_status != 'ready':
                        generated = convert_preview(document)
            else:
                permanent = True
                raise ValueError('unknown_job_kind')
        except Deferred:
            deferred = True
        except EmailDeliveryError as exc:
            result_error = exc.code
        except ReceiptFontUnavailable:
            result_error = 'receipt_font_unavailable'
        except PreviewUnavailable as exc:
            result_error = str(exc) if str(exc) in {'converter_unavailable', 'document_missing', 'conversion_failed', 'conversion_timeout'} else 'preview_failed'
            permanent = result_error in {'converter_unavailable', 'document_missing'}
        except Exception:
            # Never persist exception text: adapters/libraries may include credentials or private paths.
            result_error = 'job_processing_failed'
        db.rollback()
        job = db.scalar(select(OutboxJob).where(OutboxJob.id == job_id, OutboxJob.status == 'processing',
                                               OutboxJob.lock_token == token).with_for_update().execution_options(populate_existing=True))
        if not job:
            if generated and kind == 'document_preview':
                private_path('documents', generated).unlink(missing_ok=True)
            return True  # lease was recovered; do not overwrite the new owner's result
        now = utcnow()
        if deferred:
            job.status, job.available_at = 'pending', now + timedelta(seconds=30)
            job.attempts -= 1
        elif result_error:
            job.last_error = result_error
            job.status = 'failed' if permanent or job.attempts >= MAX_ATTEMPTS else 'pending'
            job.available_at = now + timedelta(seconds=min(3600, 30 * 2 ** min(job.attempts, 7)))
            if kind.startswith('receipt_'):
                receipt = db.get(Receipt, entity_id)
                if receipt:
                    setattr(receipt, 'pdf_status' if kind == 'receipt_pdf' else 'email_status',
                            'failed' if job.status == 'failed' else 'pending')
            elif kind == 'document_preview':
                document = db.get(Document, entity_id)
                if document:
                    document.preview_status = 'unavailable' if result_error == 'converter_unavailable' else ('failed' if job.status == 'failed' else 'pending')
        else:
            job.status, job.completed_at, job.last_error = 'done', now, None
            if kind == 'receipt_pdf':
                receipt = db.get(Receipt, entity_id)
                if generated:
                    receipt.storage_name = generated
                receipt.pdf_status = 'ready'
            elif kind == 'receipt_email':
                db.get(Receipt, entity_id).email_status = 'sent'
            elif kind == 'document_preview':
                document = db.get(Document, entity_id)
                if document and generated:
                    document.preview_name, document.preview_status = generated, 'ready'
                elif generated:
                    private_path('documents', generated).unlink(missing_ok=True)
        job.lock_token, job.locked_until = None, None
        db.commit()
    return True


def sweep_expiring_memberships(session_factory=SessionLocal):
    """Enqueues daily expiration reminder outbox jobs for memberships expiring within 48 hours."""
    import math
    from app.models.membership import Membership
    now = utcnow()
    two_days_later = now + timedelta(days=2)
    today_str = now.strftime("%Y-%m-%d")
    with session_factory() as db:
        expiring = db.scalars(
            select(Membership).where(
                Membership.revoked.is_(False),
                Membership.expires_at > now,
                Membership.expires_at <= two_days_later
            )
        ).all()
        enqueued = 0
        for m in expiring:
            diff_seconds = (aware(m.expires_at) - now).total_seconds()
            days_left = max(1, math.ceil(diff_seconds / 86400))
            dedupe = f"membership_expiry:{m.user_id}:{today_str}"
            existing = db.scalar(select(OutboxJob).where(OutboxJob.dedupe_key == dedupe))
            if not existing:
                db.add(OutboxJob(
                    kind="membership_expiry_email",
                    entity_id=m.user_id,
                    dedupe_key=dedupe,
                    payload={"days_left": days_left}
                ))
                enqueued += 1
        if enqueued:
            db.commit()
        return enqueued


def main():
    parser = argparse.ArgumentParser(description='ADMIT TRADING durable outbox worker')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--once', action='store_true', help='Claim and process at most one job')
    mode.add_argument('--continuous', action='store_true', help='Poll continuously (default)')
    parser.add_argument('--poll-seconds', type=float, default=2.0)
    args = parser.parse_args()
    if args.poll_seconds < 0.1:
        parser.error('--poll-seconds must be at least 0.1')
    try:
        last_sweep = 0
        while True:
            # Sweep expiring memberships roughly every 10 minutes in continuous mode
            now_ts = time.time()
            if now_ts - last_sweep > 600:
                try:
                    sweep_expiring_memberships()
                except Exception:
                    pass
                last_sweep = now_ts

            processed = run_once()
            if args.once:
                return
            if not processed:
                time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main()
