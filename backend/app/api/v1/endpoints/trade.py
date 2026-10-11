"""Admin-only ingestion/review/publication; deliberately no public upload path."""
import csv
import io
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from app.db import get_db
from app.config import settings
from app.services.auth_service import require_admin, require_csrf
from app.models.trade import TradeImport, TradeRevision, TradeHead, TradeRow
from app.services import trade_service as service
from app.services.etl_service import COLUMNS
from app.services.redis_service import redis_service

router = APIRouter(prefix='/admin', dependencies=[Depends(require_admin)])


class RegistryFields(BaseModel):
    name_en: str = Field(min_length=1, max_length=300)
    name_km: str = Field(min_length=1, max_length=300)
    parent_code: str | None = Field(None, max_length=4)
    iso3: str | None = Field(None, max_length=3)
    aliases: list[str] = Field(default_factory=list, max_length=100)


class RegistryInput(RegistryFields):
    kind: Literal['hs4', 'hs8', 'country']
    code: str = Field(min_length=1, max_length=160)


class RegistryUpdate(RegistryFields):
    kind: Literal['hs4', 'hs8', 'country'] | None = None
    code: str | None = Field(None, max_length=160)


class CommitInput(BaseModel):
    review_token: str = Field(min_length=1, max_length=64)


class PublicationInput(BaseModel):
    revision_id: str = Field(min_length=1, max_length=36)
    start_month: str
    end_month: str


def transaction(db, callback):
    try:
        result = callback()
        db.commit()
        return result
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, 'Concurrent or conflicting change. Refresh review and retry')
    except Exception:
        db.rollback()
        raise


@router.get('/schema')
def schema():
    # Canonical machine headers also declare their unit; generic weight/value
    # headers are deliberately not accepted as kg/KHR guesses.
    columns = [{**column, 'key': {'weight': 'weight_kg', 'value': 'value_khr'}.get(column['key'], column['key'])} for column in COLUMNS]
    return {'columns': columns, 'units': {'weight': 'kg', 'value': 'KHR'}, 'formats': ['xlsx', 'csv']}


@router.get('/template')
def template():
    output = io.StringIO()
    csv.writer(output).writerow([column['english'] for column in COLUMNS])
    return Response('\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': 'attachment; filename="trade-template.csv"'})


@router.get('/registry')
def registry(db: Session = Depends(get_db)):
    snapshot = service.get_registry(db)
    return [entry for entries in snapshot.values() for entry in entries.values()]


@router.post('/registry', dependencies=[Depends(require_csrf)])
def create_registry(payload: RegistryInput, db: Session = Depends(get_db), actor=Depends(require_admin)):
    return transaction(db, lambda: service.save_registry(db, payload.model_dump(), actor))


@router.put('/registry/{kind}/{code}', dependencies=[Depends(require_csrf)])
def update_registry(kind: str, code: str, payload: RegistryUpdate, db: Session = Depends(get_db), actor=Depends(require_admin)):
    if (payload.kind is not None and payload.kind != kind) or (payload.code is not None and payload.code != code):
        raise HTTPException(422, 'Registry kind and code are immutable')
    return transaction(db, lambda: service.save_registry(db, {**payload.model_dump(), 'kind': kind, 'code': code}, actor, replace=True))


@router.post('/registry/seed-reviewed', dependencies=[Depends(require_csrf)])
def seed_registry(db: Session = Depends(get_db), actor=Depends(require_admin)):
    return transaction(db, lambda: {'created': service.seed_reviewed_registry(db, actor)})


@router.post('/imports', dependencies=[Depends(require_csrf)])
def stage(file: UploadFile = File(...), mode: Literal['complete', 'partial'] = Form('partial'),
          start_month: str | None = Form(None), end_month: str | None = Form(None),
          db: Session = Depends(get_db), actor=Depends(require_admin)):
    contents = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(contents) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'Import exceeds upload limit')
    return transaction(db, lambda: service.stage_import(db, contents, file.filename or '', mode, start_month, end_month, actor))


@router.get('/imports')
def imports(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return [service.import_view(db, staged) for staged in db.scalars(
        select(TradeImport).where(TradeImport.status == 'committed').order_by(TradeImport.created_at.desc()).limit(limit))]


@router.get('/imports/{import_id}')
def review(import_id: str, db: Session = Depends(get_db)):
    staged = db.get(TradeImport, import_id)
    if staged is None:
        raise HTTPException(404, 'Import not found')
    # Updating the server's review marker is not an authoritative data mutation;
    # GET lets the administrator explicitly review a fresh preview after a 409.
    return transaction(db, lambda: service.import_view(db, staged, refresh=True))


@router.post('/imports/{import_id}/commit', dependencies=[Depends(require_csrf)])
def commit(import_id: str, payload: CommitInput, db: Session = Depends(get_db), actor=Depends(require_admin)):
    return transaction(db, lambda: service.commit_import(db, import_id, payload.review_token, actor))


@router.delete('/imports/{import_id}', dependencies=[Depends(require_csrf)])
def discard(import_id: str, db: Session = Depends(get_db), actor=Depends(require_admin)):
    return transaction(db, lambda: service.discard_import(db, import_id, actor))


@router.get('/revisions')
def revisions(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    revs = list(db.scalars(select(TradeRevision).order_by(TradeRevision.created_at.desc()).limit(limit)))
    if not revs:
        return []
    rev_ids = [r.id for r in revs]
    ym_rows = db.execute(
        select(TradeRow.revision_id, TradeRow.year, TradeRow.month)
        .where(TradeRow.revision_id.in_(rev_ids))
        .distinct()
        .order_by(TradeRow.revision_id, TradeRow.year, TradeRow.month)
    ).all()
    from collections import defaultdict
    rev_months = defaultdict(list)
    for rid, y, m in ym_rows:
        rev_months[rid].append(f"{y:04d}-{m:02d}")

    return [
        {
            'id': revision.id,
            'created_at': revision.created_at.isoformat(),
            'row_count': revision.row_count,
            'status': revision.status,
            'source_import_id': revision.source_import_id,
            'start_month': rev_months[revision.id][0] if rev_months[revision.id] else None,
            'end_month': rev_months[revision.id][-1] if rev_months[revision.id] else None,
            'available_months': rev_months[revision.id],
        }
        for revision in revs
    ]


@router.delete('/revisions/{revision_id}', dependencies=[Depends(require_csrf)])
def delete_revision(revision_id: str, db: Session = Depends(get_db), actor=Depends(require_admin)):
    return transaction(db, lambda: service.delete_revision(db, revision_id, actor))



@router.get('/publication')
def get_publication(db: Session = Depends(get_db)):
    return service.publication_view(service.current_publication(db), db=db)


@router.post('/publication', dependencies=[Depends(require_csrf)])
def set_publication(payload: PublicationInput, db: Session = Depends(get_db), actor=Depends(require_admin)):
    return transaction(db, lambda: service.publish(db, **payload.model_dump(), actor=actor))


@router.get('/status')
def status(db: Session = Depends(get_db)):
    head = db.get(TradeHead, 1)
    revision_id = head.revision_id if head else None
    revision = db.get(TradeRevision, revision_id) if revision_id else None
    totals = db.execute(select(
        func.sum(TradeRow.val_khr), 
        func.sum(TradeRow.weight_kg),
        func.count(func.distinct(TradeRow.hs4_code)),
        func.count(func.distinct(TradeRow.country_code)),
        func.count(func.distinct(TradeRow.hs8_code))
    ).where(TradeRow.revision_id == revision_id)).one()
    recent = [service.import_view(db, staged) for staged in db.scalars(
        select(TradeImport).order_by(TradeImport.created_at.desc()).limit(15))]
    publication = service.publication_view(service.current_publication(db), db=db)
    return {'current_revision_id': revision_id, 'publication': publication, 'uploads': recent,
            'total_records': revision.row_count if revision else 0,
            'total_export_val_usd': float(totals[0] or 0) / 4000,
            'total_weight_tonnes': float(totals[1] or 0) / 1000,
            'hs4_chapters_count': totals[2] or 0,
            'destination_countries_count': totals[3] or 0,
            'total_commodities_count': totals[4] or 0,
            'last_updated': revision.created_at.isoformat() if revision else '',
            'reporting_period': f"{publication['start_month']} – {publication['end_month']}" if publication else '',
            'upload_history': [{'filename': item['filename'], 'rows_inserted': item['preview'].get('inserted', 0),
                                'rows_updated': item['preview'].get('updated', 0), 'total_records': item['row_count'],
                                'period_range': f"{item['start_month']} – {item['end_month']}",
                                'uploaded_at': item['created_at']} for item in recent]}


public_router = APIRouter(prefix='/trade')


@public_router.get('/status')
def public_status(db: Session = Depends(get_db)):
    head = db.get(TradeHead, 1)
    publication = service.publication_view(service.current_publication(db), db=db)
    
    if publication:
        pub_id = publication['id']
        cache_key = f"agritrade:trade:public_status:pub_{pub_id}"
        cached = redis_service.get_json(cache_key)
        if cached is not None:
            return cached

        rev_id = publication['revision_id']
        s_y, s_m = map(int, publication['start_month'].split('-'))
        e_y, e_m = map(int, publication['end_month'].split('-'))
        start_int = s_y * 100 + s_m
        end_int = e_y * 100 + e_m

        totals = db.execute(select(
            func.count(func.distinct(TradeRow.hs4_code)),
            func.count(func.distinct(TradeRow.country_code)),
            func.count(func.distinct(TradeRow.hs8_code)),
            func.count(TradeRow.id)
        ).where(
            TradeRow.revision_id == rev_id,
            (TradeRow.year * 100 + TradeRow.month) >= start_int,
            (TradeRow.year * 100 + TradeRow.month) <= end_int
        )).one()

        result = {
            'current_revision_id': rev_id,
            'total_records': totals[3] or 0,
            'hs4_chapters_count': totals[0] or 0,
            'destination_countries_count': totals[1] or 0,
            'total_commodities_count': totals[2] or 0,
            'reporting_period': f"{publication['start_month']} — {publication['end_month']}",
        }
        redis_service.set_json(cache_key, result, ttl_seconds=settings.REDIS_DASHBOARD_TTL)
        return result

    revision_id = head.revision_id if head else None
    revision = db.get(TradeRevision, revision_id) if revision_id else None
    if not revision:
        empty_res = {
            'current_revision_id': None,
            'total_records': 0,
            'hs4_chapters_count': 0,
            'destination_countries_count': 0,
            'total_commodities_count': 0,
            'reporting_period': '',
        }
        redis_service.set_json("agritrade:trade:public_status:empty", empty_res, ttl_seconds=60)
        return empty_res
    totals = db.execute(select(
        func.count(func.distinct(TradeRow.hs4_code)),
        func.count(func.distinct(TradeRow.country_code)),
        func.count(func.distinct(TradeRow.hs8_code)),
        func.count(TradeRow.id)
    ).where(TradeRow.revision_id == revision_id)).one()
    return {
        'current_revision_id': revision_id,
        'total_records': totals[3] or revision.row_count,
        'hs4_chapters_count': totals[0] or 0,
        'destination_countries_count': totals[1] or 0,
        'total_commodities_count': totals[2] or 0,
        'reporting_period': '',
    }
