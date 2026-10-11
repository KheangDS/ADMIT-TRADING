import gzip
import io
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

from fastapi import HTTPException
from sqlalchemy import select

from app.config import settings
from app.models.membership import Document
from app.services.auth_service import audit
from app.services.membership_service import enqueue, iso
from app.services.receipt_service import private_directory, private_path

CONTENT_TYPES = {".pdf": "application/pdf", ".ppt": "application/vnd.ms-powerpoint",
                 ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}


def generate_storage_name(filename: str, prefix: str = "", extension_override: str = "") -> str:
    raw_stem = Path(filename).stem
    clean_stem = re.sub(r'[^\w\-]+', '_', raw_stem).strip('_') or 'document'
    extension = extension_override or Path(filename).suffix.lower()
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand_4 = f"{secrets.randbelow(9000) + 1000}"
    return f"{prefix}{clean_stem}_{now_str}_{rand_4}{extension}"


def write_compressed_file(name: str, data: bytes) -> Path:
    target = private_path('documents', name)
    compressed = gzip.compress(data, compresslevel=6)
    with target.open('xb') as file:
        os.chmod(target, 0o600)
        file.write(compressed)
    return target


def read_stored_bytes(name_or_path: str | Path) -> bytes:
    path = name_or_path if isinstance(name_or_path, Path) else private_path('documents', str(name_or_path))
    if not path.is_file():
        raise FileNotFoundError(f"Document file {path} not found")
    data = path.read_bytes()
    if data.startswith(b'\x1f\x8b'):
        return gzip.decompress(data)
    return data



class PreviewUnavailable(Exception):
    pass


def document_dict(row):
    return {key: getattr(row, key) for key in ("id", "title", "description", "language", "filename", "content_type",
            "size_bytes", "status", "publication_id", "preview_status")} | {"created_at": iso(row.created_at)}


def preview_sandbox_path():
    # Never run a parser for untrusted Office files with application filesystem/network access.
    return shutil.which(getattr(settings, "BWRAP_PATH", "") or "bwrap") if os.name == 'posix' else None


def converter_path():
    sock = getattr(settings, 'CONVERTER_SOCKET_PATH', '')
    if sock and (os.path.exists(sock) or getattr(settings, 'ENVIRONMENT', '') == 'production'):
        return sock
    configured = getattr(settings, "LIBREOFFICE_PATH", "")
    return shutil.which(configured or "libreoffice")


def validate_content(data, extension):
    try:
        if extension == ".pdf":
            if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
                raise ValueError("Invalid PDF signature")
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted or not reader.pages:
                raise ValueError("Encrypted or empty PDF")
            # Active content is not needed for reports and must not reach a browser viewer.
            root = reader.trailer['/Root']
            if '/AA' in root or '/AcroForm' in root:
                raise ValueError("Active PDF content")
            action = root.get('/OpenAction')
            if action is not None:
                from pypdf.generic import ArrayObject, NumberObject, FloatObject, NullObject
                action = action.get_object()
                # LibreOffice writes a harmless initial page/view destination.
                # Never allow action dictionaries (JavaScript, Launch, chains, etc.).
                if not (isinstance(action, ArrayObject) and 2 <= len(action) <= 6
                        and action[0].get_object().get('/Type') == '/Page'
                        and action[1] in {'/XYZ', '/Fit', '/FitH', '/FitV', '/FitR', '/FitB', '/FitBH', '/FitBV'}
                        and all(isinstance(item, (NumberObject, FloatObject, NullObject)) for item in action[2:])):
                    raise ValueError("Active PDF content")
            names = root.get('/Names', {})
            if hasattr(names, 'get_object'):
                names = names.get_object()
            if '/JavaScript' in names or '/EmbeddedFiles' in names:
                raise ValueError("Active or embedded PDF content")
            for page in reader.pages:
                if '/AA' in page:
                    raise ValueError("Active PDF page")
                for annotation in page.get('/Annots', []):
                    obj = annotation.get_object()
                    if obj.get('/Subtype') in {'/FileAttachment', '/RichMedia', '/Screen'} or '/A' in obj or '/AA' in obj:
                        raise ValueError("Active PDF annotation")
        elif extension == ".ppt":
            import olefile
            if not data.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
                raise ValueError("Invalid PowerPoint signature")
            with olefile.OleFileIO(io.BytesIO(data)) as ole:
                if not ole.exists("PowerPoint Document") or not ole.exists("Current User"):
                    raise ValueError("Not a PowerPoint document")
                if any('vba' in '/'.join(entry).lower() for entry in ole.listdir()):
                    raise ValueError("Macros are not allowed")
        elif extension == ".pptx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 5000 or sum(e.file_size for e in entries) > 100 * 1024 * 1024:
                    raise ValueError("Presentation archive is too large")
                if len({e.filename for e in entries}) != len(entries):
                    raise ValueError("Duplicate archive entries")
                for entry in entries:
                    if entry.flag_bits & 1 or '\\' in entry.filename or entry.filename.startswith('/') or '..' in Path(entry.filename).parts:
                        raise ValueError("Unsafe presentation archive")
                    if entry.file_size > 25 * 1024 * 1024 or (entry.file_size > 1024 * 1024 and entry.file_size > max(1, entry.compress_size) * 200):
                        raise ValueError("Unsafe compression ratio")
                    lowered = entry.filename.lower()
                    if 'vbaproject' in lowered or '/embeddings/' in lowered or '/activex/' in lowered:
                        raise ValueError("Active presentation content")
                    if lowered.endswith('.rels'):
                        rels = ElementTree.fromstring(archive.read(entry))
                        if any(rel.attrib.get('TargetMode') == 'External' for rel in rels):
                            raise ValueError("External presentation references are not allowed")
                types = ElementTree.fromstring(archive.read('[Content_Types].xml'))
                if not any(item.attrib.get('PartName') == '/ppt/presentation.xml' and item.attrib.get('ContentType') ==
                           'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml' for item in types):
                    raise ValueError("Not a PowerPoint presentation")
                root = ElementTree.fromstring(archive.read('ppt/presentation.xml'))
                if root.tag != '{http://schemas.openxmlformats.org/presentationml/2006/main}presentation':
                    raise ValueError("Invalid presentation XML")
        else:
            raise ValueError("Unsupported report type")
    except Exception as exc:
        raise HTTPException(422, "Invalid or unsafe document content; upload a non-encrypted PDF, PPT or PPTX report") from exc


def validate_publication(db, publication_id):
    if publication_id is None:
        return
    # Avoid coupling to the trade agent's class naming; discover its actual mapped table.
    from app.db import Base
    for mapper in Base.registry.mappers:
        if mapper.local_table.name in {"publications", "trade_publications"}:
            if db.get(mapper.class_, publication_id):
                return
            raise HTTPException(422, "Publication not found")
    raise HTTPException(422, "Publication linking is unavailable until trade schema is installed")


async def upload_document(db, admin, upload, title, description, language, publication_id):
    title = title.strip()
    if not title or len(title) > 250 or len(description) > 10000 or language not in {'en', 'km', 'both'}:
        raise HTTPException(422, "Invalid document metadata")
    validate_publication(db, publication_id)
    filename = (upload.filename or '').replace('\\', '/').rsplit('/', 1)[-1]
    filename = ''.join(c for c in filename if ord(c) >= 32 and c != '\x7f')[:250]
    extension = Path(filename).suffix.lower()
    if extension not in CONTENT_TYPES:
        raise HTTPException(422, "Only PDF, PPT and PPTX reports are supported")
    limit = getattr(settings, 'MAX_UPLOAD_BYTES', 26214400)
    chunks, size = [], 0
    try:
        while chunk := await upload.read(64 * 1024):
            size += len(chunk)
            if size > limit:
                raise HTTPException(413, "Document exceeds the upload size limit")
            chunks.append(chunk)
    finally:
        await upload.close()
    data = b''.join(chunks)
    validate_content(data, extension)
    name = f"{generate_storage_name(filename)}.gz"
    write_compressed_file(name, data)
    row = Document(title=title, description=description, language=language, filename=filename,
                   content_type=CONTENT_TYPES[extension], size_bytes=size, publication_id=publication_id,
                   storage_name=name, preview_name=name if extension == '.pdf' else None,
                   preview_status='ready' if extension == '.pdf' else ('pending' if converter_path() else 'unavailable'))
    
    if extension != '.pdf' and row.preview_status == 'pending':
        try:
            preview_name = convert_preview(row)
            row.preview_name = preview_name
            row.preview_status = 'ready'
        except Exception:
            pass

    try:
        db.add(row)
        db.flush()
        if row.preview_status == 'pending':
            enqueue(db, 'document_preview', row.id)
        audit(db, admin, 'document.create', 'document', row.id, {'filename': filename})
        db.commit()
    except Exception:
        db.rollback()
        private_path('documents', name).unlink(missing_ok=True)
        if row.preview_name and row.preview_name != row.storage_name:
            private_path('documents', row.preview_name).unlink(missing_ok=True)
        raise
    return row


def document_row(db, document_id, user, lock=False):
    query = select(Document).where(Document.id == document_id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if not row or (user.role not in {'admin', 'superadmin'} and row.status != 'published'):
        raise HTTPException(404, "Document not found")
    return row


def update_document(db, admin, document_id, changes):
    row = document_row(db, document_id, admin, True)
    if any(v is None for key, v in changes.items() if key != 'publication_id'):
        raise HTTPException(422, "Document fields cannot be null")
    if 'publication_id' in changes:
        validate_publication(db, changes['publication_id'])
    for key, value in changes.items():
        setattr(row, key, value)
    audit(db, admin, 'document.update', 'document', row.id, {'fields': list(changes)})
    db.commit()
    return row


def delete_document(db, admin, document_id):
    row = document_row(db, document_id, admin, True)
    paths = {private_path('documents', name) for name in (row.storage_name, row.preview_name) if name}
    audit(db, admin, 'document.delete', 'document', row.id, {})
    db.delete(row)
    db.commit()
    for path in paths:
        path.unlink(missing_ok=True)


def _resource_limits():
    # Runs only in the isolated child; never alter the application worker's limits.
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024**2, 100 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _store_preview(data, original_filename="preview.pdf"):
    validate_content(data, '.pdf')
    name = f"{generate_storage_name(original_filename, prefix='preview_', extension_override='.pdf')}.gz"
    write_compressed_file(name, data)
    return name


def _prepare_pptx_for_preview(data: bytes) -> bytes:
    """Normalize PPTX package for high-fidelity conversion in headless LibreOffice.

    1. Promotes modern Office drawing SVG blip extensions (<asvg:svgBlip r:embed="rId">)
       into standard DrawingML <a:blip r:embed="rId"> attributes so LibreOffice renders vector graphics.
    2. Removes inverted coordinate clip-paths in PowerPoint SVGs that clip out rendered bounds.
    """
    try:
        buf_in = io.BytesIO(data)
        buf_out = io.BytesIO()
        with zipfile.ZipFile(buf_in, 'r') as zin, zipfile.ZipFile(buf_out, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)
                if item.filename.startswith('ppt/slides/slide') and item.filename.endswith('.xml'):
                    text = content.decode('utf-8', errors='ignore')
                    pattern = r'(<a:blip(?![^>]*\br:embed=)[^>]*>)\s*(<a:extLst>\s*<a:ext[^>]*>\s*<asvg:svgBlip[^>]*\br:embed="([^"]+)"[^>]*>)'
                    text = re.sub(
                        pattern,
                        r'<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="\3">\2',
                        text
                    )
                    content = text.encode('utf-8')
                elif item.filename.startswith('ppt/media/') and item.filename.endswith('.svg'):
                    text = content.decode('utf-8', errors='ignore')
                    text = re.sub(r'clip-path="url\(#[a-zA-Z0-9_-]+\)"', '', text)
                    content = text.encode('utf-8')
                zout.writestr(item, content)
        return buf_out.getvalue()
    except Exception:
        return data


def _convert_via_socket(row):
    import httpx
    source = private_path('documents', row.storage_name)
    if not source.is_file():
        raise PreviewUnavailable('document_missing')
    source_bytes = read_stored_bytes(source)
    ext = Path(getattr(row, 'filename', '') or row.storage_name).suffix.lower()
    if ext.endswith('.gz'):
        ext = Path(ext[:-3]).suffix.lower()
    if len(source_bytes) > settings.MAX_UPLOAD_BYTES or ext not in {'.ppt', '.pptx'}:
        raise PreviewUnavailable('conversion_failed')
    if ext == '.pptx':
        source_bytes = _prepare_pptx_for_preview(source_bytes)
    deadline = time.monotonic() + 90
    try:
        # No DNS, network or provider credentials: communication is local IPC.
        transport = httpx.HTTPTransport(uds=settings.CONVERTER_SOCKET_PATH)
        with httpx.Client(transport=transport, timeout=70, follow_redirects=False, trust_env=False) as client:
            with client.stream('POST', 'http://converter/convert', content=source_bytes,
                               headers={'X-Document-Format': ext[1:]}) as response:
                if response.status_code != 200:
                    raise PreviewUnavailable('conversion_failed')
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    if time.monotonic() > deadline:
                        raise PreviewUnavailable('conversion_timeout')
                    size += len(chunk)
                    if size > 100 * 1024**2:
                        raise PreviewUnavailable('conversion_failed')
                    chunks.append(chunk)
        if time.monotonic() > deadline:
            raise PreviewUnavailable('conversion_timeout')
        return _store_preview(b''.join(chunks), original_filename=getattr(row, 'filename', 'preview.pdf'))
    except httpx.HTTPError:
        raise PreviewUnavailable('converter_unavailable') from None


def convert_preview(row):
    if getattr(settings, 'CONVERTER_SOCKET_PATH', ''):
        return _convert_via_socket(row)
    executable = converter_path()
    if not executable:
        raise PreviewUnavailable('converter_unavailable')
    source = private_path('documents', row.storage_name)
    if not source.is_file():
        raise PreviewUnavailable('document_missing')
    
    source_bytes = read_stored_bytes(source)
    ext = Path(getattr(row, 'filename', '') or row.storage_name).suffix.lower()
    if ext.endswith('.gz'):
        ext = Path(ext[:-3]).suffix.lower()
    if ext not in {'.ppt', '.pptx', '.pdf'}:
        ext = '.pptx'

    if ext == '.pptx':
        source_bytes = _prepare_pptx_for_preview(source_bytes)

    sandbox = preview_sandbox_path()
    with tempfile.TemporaryDirectory(prefix='agritrade-preview-') as temporary:
        root = Path(temporary)
        input_file = root / f'input{ext}'
        input_file.write_bytes(source_bytes)
        output_dir = root / 'output'
        output_dir.mkdir()
        
        output = output_dir / 'input.pdf'
        code = 1

        # Attempt 1: Bubblewrap isolated sandbox if available
        if sandbox:
            command = [sandbox, '--unshare-all', '--die-with-parent', '--new-session']
            for system_path in ('/usr', '/bin', '/lib', '/lib64', '/etc/fonts', '/etc/ld.so.cache', '/etc/libreoffice'):
                if Path(system_path).exists():
                    command.extend(['--ro-bind', system_path, system_path])
            command.extend(['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--bind', str(root), '/work',
                            '--chdir', '/work', '--', executable, '-env:UserInstallation=file:///work/profile',
                            '--headless', '--nologo', '--nodefault', '--nolockcheck', '--norestore',
                            '--convert-to', 'pdf:impress_pdf_Export', '--outdir', '/work/output', f'/work/{input_file.name}'])
            try:
                process = subprocess.Popen(command, cwd=root, env={'PATH': '/usr/bin:/bin', 'HOME': str(root),
                                             'TMPDIR': '/tmp', 'LANG': 'C.UTF-8'}, stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL, start_new_session=True,
                                             preexec_fn=_resource_limits if os.name == 'posix' else None)
                code = process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                if os.name == 'posix':
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait()
                raise PreviewUnavailable('conversion_timeout') from None
            except Exception:
                code = 1

        # Attempt 2: Direct headless LibreOffice if sandbox is unavailable or failed due to host restrictions
        if code != 0 or not output.is_file():
            direct_command = [executable, f'-env:UserInstallation=file://{root}/profile',
                              '--headless', '--nologo', '--nodefault', '--nolockcheck', '--norestore',
                              '--convert-to', 'pdf:impress_pdf_Export', '--outdir', str(output_dir), str(input_file)]
            try:
                direct_process = subprocess.Popen(direct_command, cwd=root, env={'PATH': '/usr/bin:/bin', 'HOME': str(root),
                                                  'TMPDIR': '/tmp', 'LANG': 'C.UTF-8'}, stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.DEVNULL, start_new_session=True,
                                                  preexec_fn=_resource_limits if os.name == 'posix' else None)
                code = direct_process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                if os.name == 'posix':
                    import signal
                    os.killpg(direct_process.pid, signal.SIGKILL)
                else:
                    direct_process.kill()
                direct_process.wait()
                raise PreviewUnavailable('conversion_timeout') from None
            except Exception:
                code = 1

        if code or not output.is_file() or output.stat().st_size > 100 * 1024**2:
            raise PreviewUnavailable('conversion_failed')
        return _store_preview(output.read_bytes(), original_filename=getattr(row, 'filename', 'preview.pdf'))

