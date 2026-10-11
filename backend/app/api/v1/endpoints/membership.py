from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select, update

from app.db import get_db
from app.models.accounts import AuditEvent, User
from app.models.membership import OutboxJob, Plan, Receipt, utcnow
from app.services import membership_service as svc
from app.services.auth_service import audit, current_user, hash_password, require_admin, require_csrf, require_superadmin, revoke_user_sessions
from app.services.receipt_service import receipt_path
from app.services.redis_service import redis_service

router = APIRouter(tags=["membership"])
csrf = [Depends(require_csrf)]


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PlanInput(Payload):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    amount: Decimal
    currency: Literal["USD", "KHR"]
    duration_unit: Literal["month", "year"]
    duration_count: int = Field(ge=1, le=120, strict=True)
    display_order: int = Field(default=0, ge=0, le=10000)
    active: bool = True


class PlanPatch(Payload):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    amount: Decimal | None = None
    currency: Literal["USD", "KHR"] | None = None
    duration_unit: Literal["month", "year"] | None = None
    duration_count: int | None = Field(default=None, ge=1, le=120, strict=True)
    display_order: int | None = Field(default=None, ge=0, le=10000)
    active: bool | None = None


class PaymentInput(Payload):
    plan_id: str
    payer_name: str = Field(min_length=1, max_length=250)


class Empty(Payload):
    pass


class DelayInput(Payload):
    message: str = Field(default="", max_length=2000)


class ApprovalInput(Payload):
    bank_reference: str = Field(default="", max_length=200)
    paid_at: datetime | None = None


class ReasonInput(Payload):
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def meaningful(cls, value):
        if not value.strip():
            raise ValueError("A reason is required")
        return value


class GrantInput(ReasonInput):
    expires_at: datetime


class CreateAdminInput(Payload):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class UpdateAdminInput(Payload):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    disabled: bool | None = None


class ChangeRoleInput(Payload):
    role: Literal["superadmin", "admin", "member"]
    reason: str = Field(default="Role updated by administrator", max_length=500)


@router.get("/plans")
def plans(db=Depends(get_db)):
    return [svc.plan_dict(p) for p in db.scalars(select(Plan).where(Plan.active.is_(True)).order_by(Plan.display_order.asc(), Plan.name.asc()))]


@router.get("/admin/plans")
def all_plans(db=Depends(get_db), admin=Depends(require_admin)):
    return [svc.plan_dict(p) for p in db.scalars(select(Plan).order_by(Plan.display_order.asc(), Plan.name.asc()))]


@router.post("/admin/plans", dependencies=csrf, status_code=201)
def create_plan(body: PlanInput, db=Depends(get_db), admin=Depends(require_admin)):
    row = Plan(**svc.validate_plan(body.model_dump()))
    db.add(row)
    db.flush()
    audit(db, admin, "plan.create", "plan", row.id, {})
    db.commit()
    return svc.plan_dict(row)


@router.patch("/admin/plans/{plan_id}", dependencies=csrf)
def edit_plan(plan_id: str, body: PlanPatch, db=Depends(get_db), admin=Depends(require_admin)):
    row = db.scalar(select(Plan).where(Plan.id == plan_id).with_for_update())
    if not row:
        raise HTTPException(404, "Plan not found")
    changes = body.model_dump(exclude_unset=True)
    if any(v is None for v in changes.values()):
        raise HTTPException(422, "Plan fields cannot be null")
    values = {key: getattr(row, key) for key in PlanInput.model_fields}
    values.update(changes)
    for key, value in svc.validate_plan(values).items():
        setattr(row, key, value)
    audit(db, admin, "plan.update", "plan", row.id, {"fields": list(changes)})
    db.commit()
    return svc.plan_dict(row)


@router.get("/payments")
def payments(db=Depends(get_db), user=Depends(current_user)):
    from app.models.membership import PaymentRequest
    return [svc.payment_dict(db, row) for row in db.scalars(select(PaymentRequest).where(PaymentRequest.user_id == user.id).order_by(PaymentRequest.created_at.desc()))]


@router.post("/payments", dependencies=csrf, status_code=201)
def create_payment(body: PaymentInput, request: Request, db=Depends(get_db), user=Depends(current_user)):
    return svc.payment_dict(db, svc.create_payment(db, user, body.plan_id, body.payer_name, request))


@router.post("/payments/{payment_id}/confirm", dependencies=csrf)
def confirm(payment_id: str, body: Empty, db=Depends(get_db), user=Depends(current_user)):
    return svc.payment_dict(db, svc.confirm_payment(db, user, payment_id))


@router.post("/payments/{payment_id}/delay-report", dependencies=csrf)
def report(payment_id: str, body: DelayInput, db=Depends(get_db), user=Depends(current_user)):
    return svc.payment_dict(db, svc.delay_report(db, user, payment_id, body.message))


@router.get("/admin/payments")
def admin_payments(db=Depends(get_db), admin=Depends(require_admin)):
    from app.models.membership import PaymentRequest
    return [svc.payment_dict(db, row) for row in db.scalars(select(PaymentRequest).order_by(PaymentRequest.created_at.desc()).limit(1000))]


@router.post("/admin/payments/{payment_id}/approve", dependencies=csrf)
def approve(payment_id: str, body: ApprovalInput, db=Depends(get_db), admin=Depends(require_admin)):
    return svc.payment_dict(db, svc.approve_payment(db, admin, payment_id, body.bank_reference, body.paid_at))


@router.post("/admin/payments/{payment_id}/reject", dependencies=csrf)
def reject(payment_id: str, body: ReasonInput, db=Depends(get_db), admin=Depends(require_admin)):
    return svc.payment_dict(db, svc.reject_payment(db, admin, payment_id, body.reason))


@router.get("/admin/users")
def users(db=Depends(get_db), admin=Depends(require_admin)):
    return [{"id": u.id, "email": u.email, "name": u.name, "role": u.role, "disabled": u.disabled,
             "created_at": svc.iso(u.created_at),
             "membership": svc.membership_info(db, u.id)} for u in db.scalars(select(User).order_by(User.created_at.desc()).limit(1000))]


@router.post("/admin/users/{user_id}/grant", dependencies=csrf)
def grant(user_id: str, body: GrantInput, db=Depends(get_db), admin=Depends(require_admin)):
    return svc.change_membership(db, admin, user_id, body.reason, body.expires_at)


@router.post("/admin/users/{user_id}/revoke", dependencies=csrf)
def revoke(user_id: str, body: ReasonInput, db=Depends(get_db), admin=Depends(require_admin)):
    return svc.change_membership(db, admin, user_id, body.reason)


@router.post("/admin/users/create-admin", dependencies=csrf, status_code=201)
def create_admin_user(body: CreateAdminInput, db=Depends(get_db), superadmin=Depends(require_superadmin)):
    email = body.email.strip().casefold()
    if not email:
        raise HTTPException(422, "Please enter an email address")
    name = " ".join(body.name.split())
    if not name:
        raise HTTPException(422, "Please enter admin name")
    
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if user is not None:
        if user.role == "superadmin":
            raise HTTPException(400, "Cannot overwrite a superadministrator account")
        user.role = "admin"
        user.name = name
        user.password_hash = hash_password(body.password)
        user.disabled = False
        revoke_user_sessions(db, user.id)
        audit(db, superadmin, "account.promote", "user", user.id, {"email": email, "name": name, "by_superadmin": superadmin.email})
        db.commit()
        return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "disabled": user.disabled, "membership": svc.membership_info(db, user.id)}
    
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(body.password),
        role="admin",
    )
    db.add(user)
    db.flush()
    audit(db, superadmin, "account.create_admin", "user", user.id, {"email": email, "name": name, "by_superadmin": superadmin.email})
    db.commit()
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "disabled": user.disabled, "membership": svc.membership_info(db, user.id)}


@router.patch("/admin/users/{user_id}", dependencies=csrf)
def update_admin_user(user_id: str, body: UpdateAdminInput, db=Depends(get_db), superadmin=Depends(require_superadmin)):
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(404, "User not found")
    if user.role == "member":
        raise HTTPException(400, "Members cannot be modified through this endpoint")
    if user.role == "superadmin" and user.id != superadmin.id:
        raise HTTPException(403, "Superadministrator accounts cannot be modified by another user")
    if body.disabled is True and user.id == superadmin.id:
        raise HTTPException(400, "You cannot disable your own superadministrator account")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "disabled": user.disabled, "membership": svc.membership_info(db, user.id)}

    if body.name is not None:
        name = " ".join(body.name.split())
        if not name:
            raise HTTPException(422, "Name cannot be empty")
        user.name = name
    if body.email is not None:
        email = body.email.strip().casefold()
        if not email:
            raise HTTPException(422, "Email cannot be empty")
        existing = db.scalar(select(User).where(User.email == email, User.id != user.id))
        if existing:
            raise HTTPException(409, "Email is already taken by another user")
        user.email = email
    if body.password is not None:
        if len(body.password) < 8:
            raise HTTPException(422, "Password must be at least 8 characters")
        user.password_hash = hash_password(body.password)
        revoke_user_sessions(db, user.id)
    if body.disabled is not None:
        user.disabled = body.disabled
        if body.disabled:
            revoke_user_sessions(db, user.id)

    audit(db, superadmin, "account.update_admin", "user", user.id, {"changes": list(changes.keys()), "by": superadmin.email})
    db.commit()
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "disabled": user.disabled, "membership": svc.membership_info(db, user.id)}


@router.delete("/admin/users/{user_id}", dependencies=csrf)
def delete_admin_user(user_id: str, db=Depends(get_db), superadmin=Depends(require_superadmin)):
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(404, "User not found")
    if user.id == superadmin.id:
        raise HTTPException(400, "You cannot delete your own account")
    if user.role == "superadmin":
        raise HTTPException(403, "Superadministrator accounts cannot be deleted")
    if user.role == "member":
        raise HTTPException(400, "Members cannot be deleted through this endpoint")

    revoke_user_sessions(db, user.id)
    from app.models.accounts import AuthSession, SessionCredential
    sessions = list(db.scalars(select(AuthSession).where(AuthSession.user_id == user.id)))
    for s in sessions:
        db.execute(delete(SessionCredential).where(SessionCredential.session_id == s.id))
        db.delete(s)
    from app.models.membership import Membership
    db.execute(delete(Membership).where(Membership.user_id == user.id))
    db.execute(update(AuditEvent).where(AuditEvent.actor_id == user.id).values(actor_id=None))
    db.delete(user)
    audit(db, superadmin, "account.delete_admin", "user", user.id, {"deleted_email": user.email, "by": superadmin.email})
    db.commit()
    return {"deleted": True, "id": user_id}


@router.post("/admin/users/{user_id}/role", dependencies=csrf)
def change_user_role(user_id: str, body: ChangeRoleInput, db=Depends(get_db), superadmin=Depends(require_superadmin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == superadmin.id and body.role != "superadmin":
        raise HTTPException(400, "You cannot remove your own superadministrator role")
    if user.role == "superadmin" and user.id != superadmin.id:
        raise HTTPException(403, "Superadministrator accounts cannot be modified by another user")
    user.role = body.role
    revoke_user_sessions(db, user.id)
    audit(db, superadmin, "account.change_role", "user", user.id, {"new_role": body.role, "reason": body.reason})
    db.commit()
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "disabled": user.disabled, "membership": svc.membership_info(db, user.id)}


@router.get("/receipts")
def receipts(db=Depends(get_db), user=Depends(current_user)):
    return [svc.receipt_dict(row) for row in db.scalars(select(Receipt).where(Receipt.user_id == user.id).order_by(Receipt.approved_at.desc()))]


@router.get("/receipts/{receipt_id}/download")
def download_receipt(receipt_id: str, db=Depends(get_db), user=Depends(current_user)):
    row = db.get(Receipt, receipt_id)
    if not row or (row.user_id != user.id and user.role not in {"admin", "superadmin"}):
        raise HTTPException(404, "Receipt not found")
    if row.pdf_status != "ready" or not row.storage_name or not receipt_path(row).is_file():
        raise HTTPException(409, "Receipt PDF is not ready; approved access is unaffected")
    return FileResponse(receipt_path(row), media_type="application/pdf", filename=f"{row.number}.pdf",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"})


@router.get("/admin/audit")
def audit_events(db=Depends(get_db), admin=Depends(require_admin)):
    cache_key = "admin:audit_events:latest"
    cached = redis_service.get_json(cache_key)
    if cached is not None:
        return cached

    stmt = (
        select(AuditEvent, User.name, User.email)
        .outerjoin(User, AuditEvent.actor_id == User.id)
        .order_by(AuditEvent.created_at.desc())
        .limit(500)
    )
    results = [
        {
            "id": a.id,
            "actor_id": a.actor_id,
            "actor_name": actor_name,
            "actor_email": actor_email,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "details": a.details,
            "created_at": svc.iso(a.created_at),
        }
        for a, actor_name, actor_email in db.execute(stmt)
    ]
    redis_service.set_json(cache_key, results, ttl_seconds=60)
    return results


@router.get("/admin/jobs")
def jobs(db=Depends(get_db), admin=Depends(require_admin)):
    return [{"id": j.id, "kind": j.kind, "entity_id": j.entity_id, "status": j.status, "attempts": j.attempts,
             "last_error": j.last_error, "available_at": svc.iso(j.available_at), "created_at": svc.iso(j.created_at),
             "completed_at": svc.iso(j.completed_at)} for j in db.scalars(select(OutboxJob).order_by(OutboxJob.created_at.desc()).limit(500))]


@router.post("/admin/jobs/{job_id}/retry", dependencies=csrf)
def retry_job(job_id: str, db=Depends(get_db), admin=Depends(require_admin)):
    job = db.scalar(select(OutboxJob).where(OutboxJob.id == job_id).with_for_update())
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status in {"done", "processing"}:
        raise HTTPException(409, "Completed or running jobs cannot be retried")
    if job.kind == "receipt_email":
        from app.worker import email_window_expired
        if email_window_expired(job):
            raise HTTPException(409, "Email idempotency window expired; reconcile delivery with provider before any manual resend")
    job.status, job.available_at, job.last_error, job.attempts = "pending", utcnow(), None, 0
    if job.kind.startswith("receipt_"):
        receipt = db.get(Receipt, job.entity_id)
        if receipt:
            setattr(receipt, "pdf_status" if job.kind == "receipt_pdf" else "email_status", "pending")
    elif job.kind == "document_preview":
        from app.models.membership import Document
        document = db.get(Document, job.entity_id)
        if document:
            document.preview_status = "pending"
    audit(db, admin, "job.retry", "job", job.id, {})
    db.commit()
    return {"id": job.id, "status": job.status}
