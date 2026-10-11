"""Authoritative manual payments, entitlements, private documents and durable jobs."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid4())


class Plan(Base):
    __tablename__ = "membership_plans"
    __table_args__ = (
        CheckConstraint("amount > 0", name="plan_positive_amount"),
        CheckConstraint("currency IN ('USD','KHR')", name="plan_currency"),
        CheckConstraint("currency != 'KHR' OR amount = CAST(amount AS BIGINT)", name="plan_whole_riel"),
        CheckConstraint("duration_unit IN ('month','year') AND duration_count > 0", name="plan_duration"),
        CheckConstraint("display_order >= 0", name="plan_display_order"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    duration_unit: Mapped[str] = mapped_column(String(5))
    duration_count: Mapped[int] = mapped_column(Integer)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Membership(Base):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(30))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    __table_args__ = (
        CheckConstraint("status IN ('created','submitted','approved','rejected','cancelled')", name="payment_status"),
        CheckConstraint("amount > 0 AND currency IN ('USD','KHR')", name="payment_amount_currency"),
        CheckConstraint("currency != 'KHR' OR amount = CAST(amount AS BIGINT)", name="payment_whole_riel"),
        CheckConstraint("duration_unit IN ('month','year') AND duration_count > 0", name="payment_duration"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user_name: Mapped[str] = mapped_column(String(250))
    user_email: Mapped[str] = mapped_column(String(320))
    plan_id: Mapped[str] = mapped_column(ForeignKey("membership_plans.id"))
    plan_name: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    duration_unit: Mapped[str] = mapped_column(String(5))
    duration_count: Mapped[int] = mapped_column(Integer)
    payer_name: Mapped[str] = mapped_column(String(250))
    status: Mapped[str] = mapped_column(String(15), default="created", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bank_reference: Mapped[str | None] = mapped_column(String(200), unique=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    checkout_ip: Mapped[str | None] = mapped_column(String(64))
    device_type: Mapped[str] = mapped_column(String(20), default="unknown")
    user_agent: Mapped[str] = mapped_column(String(1000), default="")
    qr_url: Mapped[str] = mapped_column(Text)
    delayed_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (
        CheckConstraint("pdf_status IN ('pending','ready','failed')", name="receipt_pdf_status"),
        CheckConstraint("email_status IN ('pending','sent','failed')", name="receipt_email_status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payment_requests.id"), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    number: Mapped[str] = mapped_column(String(50), unique=True)
    user_name: Mapped[str] = mapped_column(String(250))
    user_email: Mapped[str] = mapped_column(String(320))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pdf_status: Mapped[str] = mapped_column(String(10), default="pending")
    email_status: Mapped[str] = mapped_column(String(10), default="pending")
    storage_name: Mapped[str | None] = mapped_column(String(100))


class OutboxJob(Base):
    __tablename__ = "outbox_jobs"
    __table_args__ = (
        CheckConstraint("status IN ('pending','processing','done','failed')", name="outbox_status"),
        CheckConstraint("attempts >= 0", name="outbox_attempts"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(36))
    dedupe_key: Mapped[str] = mapped_column(String(150), unique=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(15), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lock_token: Mapped[str | None] = mapped_column(String(36))
    last_error: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("status IN ('draft','published')", name="document_status"),
        CheckConstraint("language IN ('en','km','both')", name="document_language"),
        CheckConstraint("preview_status IN ('ready','unavailable','pending','failed')", name="document_preview_status"),
        CheckConstraint("size_bytes > 0", name="document_positive_size"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(4))
    filename: Mapped[str] = mapped_column(String(250))
    content_type: Mapped[str] = mapped_column(String(150))
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="draft", index=True)
    # Optional link is opaque until the trade module is integrated; validated by service.
    publication_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    storage_name: Mapped[str] = mapped_column(String(100))
    preview_name: Mapped[str | None] = mapped_column(String(100))
    preview_status: Mapped[str] = mapped_column(String(15), default="unavailable")
