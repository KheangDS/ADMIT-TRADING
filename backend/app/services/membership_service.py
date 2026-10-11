"""Manual review only: no user confirmation can grant an entitlement."""
import calendar
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.models.accounts import User
from app.models.membership import Membership, OutboxJob, PaymentRequest, Plan, Receipt, new_id, utcnow
from app.services.auth_service import audit


def aware(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def iso(value):
    return aware(value).isoformat() if value else None


def membership_info(db, user_id):
    row = db.get(Membership, user_id)
    return {"active": bool(row and not row.revoked and aware(row.expires_at) > utcnow()),
            "expires_at": iso(row.expires_at) if row else None, "source": row.source if row else None}


def validate_plan(values):
    try:
        amount = Decimal(str(values["amount"]))
    except (InvalidOperation, ValueError):
        raise HTTPException(422, "Invalid amount")
    currency = values["currency"]
    if not amount.is_finite() or amount <= 0 or amount >= Decimal('10000000000000000'):
        raise HTTPException(422, "Amount must be positive and within supported precision")
    precision = Decimal("1") if currency == "KHR" else Decimal("0.01")
    if currency not in {"USD", "KHR"} or amount != amount.quantize(precision):
        raise HTTPException(422, "KHR requires whole riel; USD supports at most two decimals")
    if values["duration_unit"] not in {"month", "year"} or not 1 <= values["duration_count"] <= 120:
        raise HTTPException(422, "Invalid calendar duration (1–120)")
    try:
        display_order = int(values.get("display_order", 0))
        if display_order < 0 or display_order > 10000:
            raise ValueError
        values["display_order"] = display_order
    except (ValueError, TypeError):
        raise HTTPException(422, "Display order must be an integer between 0 and 10000")
    values["amount"] = amount
    return values


def amount_text(amount, currency):
    return format(amount, ".0f" if currency == "KHR" else ".2f")


def plan_dict(row):
    return {"id": row.id, "name": row.name, "description": row.description,
            "amount": amount_text(row.amount, row.currency), "currency": row.currency,
            "duration_unit": row.duration_unit, "duration_count": row.duration_count,
            "display_order": getattr(row, "display_order", 0), "active": row.active}


def payment_dict(db, row):
    receipt = db.scalar(select(Receipt).where(Receipt.payment_id == row.id))
    is_expired = bool(row.created_at and (utcnow() >= aware(row.created_at) + timedelta(minutes=5)))
    if (row.status in {"cancelled", "rejected"} or (row.status == "created" and is_expired)) and getattr(row, "qr_url", None):
        row.qr_url = ""
        try:
            db.commit()
        except Exception:
            db.rollback()

    result = {key: getattr(row, key) for key in (
        "id", "user_id", "user_name", "user_email", "plan_id", "plan_name", "currency", "duration_unit",
        "duration_count", "payer_name", "status", "bank_reference", "rejection_reason", "checkout_ip",
        "device_type", "user_agent", "qr_url")}
    result["amount"] = amount_text(row.amount, row.currency)
    for key in ("created_at", "confirmed_at", "approved_at", "paid_at", "expires_at", "delayed_reported_at"):
        result[key] = iso(getattr(row, key))
    result["qr_expires_at"] = iso(aware(row.created_at) + timedelta(minutes=5)) if row.created_at else None
    result["receipt_id"] = receipt.id if receipt else None
    
    m_info = membership_info(db, row.user_id)
    result["is_access_granted"] = bool(m_info.get("active", False))
    result["access_status"] = "ACTIVE" if m_info.get("active") else ("EXPIRED" if m_info.get("expires_at") else "LOCKED")
    result["access_expires_at"] = m_info.get("expires_at")
    result["access_source"] = m_info.get("source")
    return result


def receipt_dict(row):
    return {"id": row.id, "payment_id": row.payment_id, "number": row.number, "user_name": row.user_name,
            "amount": amount_text(row.amount, row.currency), "currency": row.currency,
            "paid_at": iso(row.paid_at), "approved_at": iso(row.approved_at), "expires_at": iso(row.expires_at),
            "pdf_status": row.pdf_status, "email_status": row.email_status}


def payment_row(db, payment_id, user=None, lock=False):
    query = select(PaymentRequest).where(PaymentRequest.id == payment_id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query.execution_options(populate_existing=True))
    if not row or (user and row.user_id != user.id):
        raise HTTPException(404, "Payment not found")
    return row


def create_payment(db, user, plan_id, payer_name, request):
    plan = db.get(Plan, plan_id)
    if not plan or not plan.active:
        raise HTTPException(404, "Active plan not found")
        
    # Rule: 1 user is only allowed to submit 1 plan at a time while awaiting review
    pending_submitted = db.scalar(
        select(PaymentRequest)
        .where(PaymentRequest.user_id == user.id, PaymentRequest.status == "submitted")
    )
    if pending_submitted:
        raise HTTPException(
            409,
            "You already have a submitted plan payment awaiting review. Only 1 plan submission is allowed at a time."
        )

    # Cancel previous unconfirmed 'created' payments for this user if any
    old_created = list(db.scalars(
        select(PaymentRequest).where(PaymentRequest.user_id == user.id, PaymentRequest.status == "created")
    ))
    for old_req in old_created:
        old_req.status = "cancelled"
        old_req.qr_url = ""

    payer_name = " ".join(payer_name.split()).upper()
    if not payer_name or len(payer_name) > 250 or any(ord(c) < 32 for c in payer_name):
        raise HTTPException(422, "Enter the payer account-holder name")
        
    payment_id = new_id()
    custom_qr = getattr(settings, f"PAYMENT_QR_{plan.currency}_URL", "")
    if custom_qr and urlsplit(custom_qr).scheme == "https" and urlsplit(custom_qr).netloc:
        qr_url = custom_qr
    elif getattr(settings, "KHQR_BAKONG_ACCOUNT", "") and getattr(settings, "KHQR_MERCHANT_ID", ""):
        from app.services.khqr_service import generate_payment_qr
        try:
            _, data_uri = generate_payment_qr(
                amount=plan.amount,
                currency=plan.currency,
                bill_number=payment_id[:16],
            )
            qr_url = data_uri
        except Exception as e:
            raise HTTPException(500, f"KHQR generation failed: {e}")
    else:
        raise HTTPException(400, f"Payment QR destination for {plan.currency} is not configured; contact support")

    agent = request.headers.get("user-agent", "")[:1000]
    row = PaymentRequest(id=payment_id, user_id=user.id, user_name=user.name, user_email=user.email,
                         plan_id=plan.id, plan_name=plan.name, amount=plan.amount, currency=plan.currency,
                         duration_unit=plan.duration_unit, duration_count=plan.duration_count,
                         payer_name=payer_name, qr_url=qr_url, checkout_ip=request.client.host if request.client else None,
                         user_agent=agent, device_type="mobile" if any(x in agent.lower() for x in ("mobile", "android", "iphone")) else "desktop")
    db.add(row)
    db.flush()
    audit(db, user, "payment.create", "payment", row.id, {})
    db.commit()
    return row


def confirm_payment(db, user, payment_id):
    row = payment_row(db, payment_id, user, True)
    if row.status == "submitted":
        return row
    if row.status != "created":
        raise HTTPException(409, "Only an open payment can be confirmed")
    # Conditional write also protects the SQLite test adapter against two confirmations.
    changed = db.execute(update(PaymentRequest).where(PaymentRequest.id == row.id, PaymentRequest.status == "created")
                         .values(status="submitted", confirmed_at=utcnow())).rowcount
    if changed:
        audit(db, user, "payment.confirm", "payment", row.id, {})
    db.commit()
    return payment_row(db, payment_id, user)


def delay_report(db, user, payment_id, message=""):
    row = payment_row(db, payment_id, user, True)
    if row.status != "submitted" or not row.confirmed_at or utcnow() < aware(row.confirmed_at) + timedelta(hours=24):
        raise HTTPException(409, "Follow-up is available 24 hours after confirmation while awaiting review")
    if row.delayed_reported_at:
        return row
    changed = db.execute(update(PaymentRequest).where(PaymentRequest.id == row.id, PaymentRequest.delayed_reported_at.is_(None))
                         .values(delayed_reported_at=utcnow())).rowcount
    if changed:
        audit(db, user, "payment.delayed_report", "payment", row.id,
              {"name": user.name, "email": user.email, "message": message})
    db.commit()
    return payment_row(db, payment_id, user)


def calendar_extend(start, unit, count):
    months = count * (12 if unit == "year" else 1)
    year, month = divmod(start.year * 12 + start.month - 1 + months, 12)
    if year > 9999:
        raise HTTPException(422, "Membership expiry exceeds supported date range")
    return start.replace(year=year, month=month + 1, day=min(start.day, calendar.monthrange(year, month + 1)[1]))


def enqueue(db, kind, entity_id):
    db.add(OutboxJob(kind=kind, entity_id=entity_id, dedupe_key=f"{kind}:{entity_id}", payload={}))


def approve_payment(db, admin, payment_id, bank_reference=None, paid_at=None):
    now = utcnow()
    if not bank_reference or not str(bank_reference).strip():
        raise HTTPException(422, "Bank transaction reference is required")
    bank_reference = " ".join(str(bank_reference).split()).upper()
    if len(bank_reference) > 200:
        raise HTTPException(422, "Bank transaction reference is too long")
    if paid_at is None:
        paid_at = now
    elif paid_at.tzinfo is None:
        raise HTTPException(422, "Verified payment time must include a timezone")
    else:
        paid_at = paid_at.astimezone(timezone.utc)
    if paid_at > now:
        raise HTTPException(422, "Verified payment time cannot be in the future")
    try:
        row = payment_row(db, payment_id, lock=True)
        if row.status == "approved":
            if row.bank_reference == bank_reference and aware(row.paid_at) == paid_at:
                return row
            raise HTTPException(409, "Payment already approved with different review details")
        if row.status != "submitted":
            raise HTTPException(409, "Only submitted payments may be approved")
        # Serialize ALL renewals/manual grants for this account, including first membership creation.
        owner = db.scalar(select(User).where(User.id == row.user_id).with_for_update())
        if not owner or owner.disabled:
            raise HTTPException(409, "Account unavailable")
        member = db.get(Membership, row.user_id)
        base = max(now, aware(member.expires_at)) if member and not member.revoked else now
        expiry = calendar_extend(base, row.duration_unit, row.duration_count)
        changed = db.execute(update(PaymentRequest).where(PaymentRequest.id == row.id, PaymentRequest.status == "submitted")
                             .values(status="approved", bank_reference=bank_reference, paid_at=paid_at,
                                     approved_at=now, expires_at=expiry)).rowcount
        if not changed:
            raise HTTPException(409, "Payment review changed; reload")
        if not member:
            member = Membership(user_id=row.user_id)
            db.add(member)
        member.expires_at, member.revoked, member.source, member.updated_at = expiry, False, "payment", now
        receipt_id = new_id()
        receipt = Receipt(id=receipt_id, payment_id=row.id, user_id=owner.id, number=f"AGR-{receipt_id}",
                          user_name=owner.name, user_email=owner.email, amount=row.amount, currency=row.currency,
                          paid_at=paid_at, approved_at=now, expires_at=expiry, pdf_status="ready")
        db.add(receipt)
        enqueue(db, "receipt_email", receipt.id)
        audit(db, admin, "payment.approve", "payment", row.id,
              {"bank_reference": bank_reference, "paid_at": iso(paid_at), "expires_at": iso(expiry), "receipt_id": receipt.id})
        db.commit()
        return payment_row(db, payment_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bank reference already used or payment concurrently approved")
    except Exception:
        db.rollback()
        raise


def reject_payment(db, admin, payment_id, reason):
    row = payment_row(db, payment_id, lock=True)
    if row.status not in {"created", "submitted"}:
        raise HTTPException(409, "Only pending payments may be rejected")
    row.status, row.rejection_reason = "rejected", reason
    row.qr_url = ""
    audit(db, admin, "payment.reject", "payment", row.id, {"reason": reason})
    db.commit()
    return row


def change_membership(db, admin, user_id, reason, expires_at=None):
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise HTTPException(404, "User not found")
    member = db.get(Membership, user_id)
    now = utcnow()
    if expires_at is not None:
        if expires_at.tzinfo is None or expires_at <= now:
            raise HTTPException(422, "Expiry must be a future timezone-aware timestamp")
        expires_at = expires_at.astimezone(timezone.utc)
        if not member:
            member = Membership(user_id=user_id)
            db.add(member)
        member.expires_at, member.revoked, member.source = expires_at, False, "manual"
    else:
        if not member:
            member = Membership(user_id=user_id, expires_at=now, source="manual")
            db.add(member)
        member.revoked = True
    member.updated_at = now
    audit(db, admin, "membership.grant" if expires_at else "membership.revoke", "membership", user_id, {"reason": reason, "expires_at": iso(expires_at)})
    db.commit()
    return membership_info(db, user_id)
