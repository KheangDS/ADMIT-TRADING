from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.db import get_db
from app.models.membership import Document
from app.services import document_service as svc
from app.services.auth_service import require_admin, require_csrf, require_member
from app.services.receipt_service import private_path

router = APIRouter(tags=["documents"])


class DocumentPatch(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = Field(default=None, max_length=10000)
    language: Literal['en', 'km', 'both'] | None = None
    status: Literal['draft', 'published'] | None = None
    publication_id: str | None = None


@router.get('/admin/documents')
def admin_documents(db=Depends(get_db), admin=Depends(require_admin)):
    rows = list(db.scalars(select(Document).order_by(Document.created_at.desc())))
    for row in rows:
        if row.preview_status != 'ready' and row.content_type != 'application/pdf' and svc.converter_path():
            try:
                gen_name = svc.convert_preview(row)
                row.preview_name = gen_name
                row.preview_status = 'ready'
                db.commit()
            except Exception:
                pass
    return [svc.document_dict(row) for row in rows]


@router.post('/admin/documents', dependencies=[Depends(require_csrf)], status_code=201)
async def upload(file: UploadFile = File(...), title: str = Form(...), description: str = Form(''),
                 language: str = Form(...), publication_id: str | None = Form(None),
                 db=Depends(get_db), admin=Depends(require_admin)):
    return svc.document_dict(await svc.upload_document(db, admin, file, title, description, language, publication_id))


@router.patch('/admin/documents/{document_id}', dependencies=[Depends(require_csrf)])
def edit(document_id: str, body: DocumentPatch, db=Depends(get_db), admin=Depends(require_admin)):
    return svc.document_dict(svc.update_document(db, admin, document_id, body.model_dump(exclude_unset=True)))


@router.delete('/admin/documents/{document_id}', dependencies=[Depends(require_csrf)], status_code=204)
def delete(document_id: str, db=Depends(get_db), admin=Depends(require_admin)):
    svc.delete_document(db, admin, document_id)
    return Response(status_code=204)


@router.get('/documents')
def documents(db=Depends(get_db), user=Depends(require_member)):
    rows = list(db.scalars(select(Document).where(Document.status == 'published').order_by(Document.created_at.desc())))
    for row in rows:
        if row.preview_status != 'ready' and row.content_type != 'application/pdf' and svc.converter_path():
            try:
                gen_name = svc.convert_preview(row)
                row.preview_name = gen_name
                row.preview_status = 'ready'
                db.commit()
            except Exception:
                pass
    return [svc.document_dict(row) for row in rows]


def authorized_file(db, user, document_id, preview):
    row = svc.document_row(db, document_id, user)
    if preview and (row.preview_status != 'ready' or not row.preview_name):
        if svc.converter_path():
            try:
                gen_name = svc.convert_preview(row)
                row.preview_name = gen_name
                row.preview_status = 'ready'
                db.commit()
            except Exception:
                pass
        if row.preview_status != 'ready' or not row.preview_name:
            raise HTTPException(409, f'PDF preview is {row.preview_status}; original download remains available')
    
    file_name_on_disk = row.preview_name if preview else row.storage_name
    path = private_path('documents', file_name_on_disk)
    if not path.is_file():
        raise HTTPException(409, 'Document file is currently unavailable')
    
    data = svc.read_stored_bytes(path)
    
    out_filename = file_name_on_disk
    if out_filename.endswith('.gz'):
        out_filename = out_filename[:-3]
    if preview:
        raw_stem = Path(row.filename).stem
        clean_stem = (raw_stem.replace(' ', '_')) or 'preview'
        out_filename = f'{clean_stem}_preview.pdf'

    headers = {
        'Cache-Control': 'private, no-store',
        'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': 'sandbox',
        'Content-Length': str(len(data))
    }
    return Response(
        content=data,
        media_type='application/pdf' if preview else row.content_type,
        headers=headers | {
            'Content-Disposition': f'{"inline" if preview else "attachment"}; filename="{out_filename}"'
        }
    )


@router.get('/documents/{document_id}/download')
def download(document_id: str, db=Depends(get_db), user=Depends(require_member)):
    return authorized_file(db, user, document_id, False)


@router.get('/documents/{document_id}/preview')
def preview(document_id: str, db=Depends(get_db), user=Depends(require_member)):
    return authorized_file(db, user, document_id, True)
