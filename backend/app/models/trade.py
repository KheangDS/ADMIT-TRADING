"""Authoritative trade registry, staged imports and immutable revision snapshots."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Numeric, CheckConstraint, UniqueConstraint, Text, event
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class TradeRegistry(Base):
    __tablename__ = "trade_registry"
    kind: Mapped[str] = mapped_column(String(10), primary_key=True)
    code: Mapped[str] = mapped_column(String(160), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(300))
    name_km: Mapped[str] = mapped_column(String(300))
    parent_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    iso3: Mapped[str | None] = mapped_column(String(3), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    __table_args__ = (CheckConstraint("kind IN ('hs4','hs8','country')"),)


class TradeHead(Base):
    """One serialization/CAS point; initialized by a transaction, never startup."""
    __tablename__ = "trade_head"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision_id: Mapped[str | None] = mapped_column(ForeignKey("trade_revisions.id"), nullable=True)
    publication_id: Mapped[str | None] = mapped_column(ForeignKey("trade_publications.id"), nullable=True)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    registry_generation: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (CheckConstraint("id = 1"),)


class TradeImport(Base):
    __tablename__ = "trade_imports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    filename: Mapped[str] = mapped_column(String(255))
    storage_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(12), default="staged")
    start_month: Mapped[str | None] = mapped_column(String(7), nullable=True)
    end_month: Mapped[str | None] = mapped_column(String(7), nullable=True)
    rows: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    column_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    preview: Mapped[dict] = mapped_column(JSON, default=dict)
    base_revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    registry_generation: Mapped[int] = mapped_column(Integer, default=0)
    revision_id: Mapped[str | None] = mapped_column(ForeignKey("trade_revisions.id", use_alter=True, name="fk_trade_import_revision"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("mode IN ('complete','partial')"), CheckConstraint("status IN ('staged','invalid','committed')"))


class TradeRevision(Base):
    __tablename__ = "trade_revisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    source_import_id: Mapped[str] = mapped_column(ForeignKey("trade_imports.id"), unique=True)
    row_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="ready")
    registry_snapshot: Mapped[dict] = mapped_column(JSON)


class TradeRow(Base):
    __tablename__ = "trade_rows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    revision_id: Mapped[str] = mapped_column(ForeignKey("trade_revisions.id"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    hs4_code: Mapped[str] = mapped_column(String(4))
    hs8_code: Mapped[str] = mapped_column(String(8))
    country_code: Mapped[str] = mapped_column(String(160))
    weight_kg: Mapped[object] = mapped_column(Numeric(24, 6))
    val_khr: Mapped[object] = mapped_column(Numeric(24, 6))
    source_import_id: Mapped[str] = mapped_column(String(36))
    source_row: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("revision_id", "year", "month", "hs8_code", "country_code"),
        CheckConstraint("month BETWEEN 1 AND 12"), CheckConstraint("year BETWEEN 1900 AND 2200"),
        CheckConstraint("weight_kg >= 0 AND val_khr >= 0"),
    )


class TradePublication(Base):
    __tablename__ = "trade_publications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    revision_id: Mapped[str] = mapped_column(ForeignKey("trade_revisions.id"))
    start_month: Mapped[str] = mapped_column(String(7))
    end_month: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("start_month <= end_month"),)


def immutable(mapper, connection, target):
    raise ValueError("Trade snapshots and publications are immutable; create a new revision")


for model in (TradeRevision, TradeRow, TradePublication):
    event.listen(model, "before_update", immutable)
    event.listen(model, "before_delete", immutable)
