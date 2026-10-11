import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import SessionLocal
from app.api.v1.router import api_router
from app.services.auth_service import SessionResponseMiddleware, apply_pending_session_cookie


from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create private storage directories on startup if they do not exist
    if settings.ENVIRONMENT != "test":
        storage_root = Path(settings.STORAGE_PATH).expanduser().resolve()
        storage_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for sub in ("documents", "receipts", "uploads", "trade-originals"):
            (storage_root / sub).mkdir(parents=True, exist_ok=True, mode=0o700)

    # Authoritative schema/data are changed only by explicit Alembic operations.
    if settings.ENVIRONMENT == "production":
        settings.validate_auth()
    elif settings.ENVIRONMENT != "test":
        if len(settings.SESSION_SIGNING_KEY.encode()) < 32:
            raise RuntimeError("Missing or invalid SESSION_SIGNING_KEY in .env (minimum 32 characters required)")
        try:
            with SessionLocal() as db:
                db.execute(text("ALTER TABLE membership_plans ADD COLUMN IF NOT EXISTS display_order INTEGER NOT NULL DEFAULT 0"))
                db.commit()
        except Exception:
            pass
    yield


class RequestBodyLimitMiddleware:
    """Bound declared and chunked bodies before multipart parsing/spooling.

    Buffer at most the file limit plus 1MiB multipart metadata. Deploy a matching
    reverse-proxy limit and timeouts as well; this does not replace edge DoS controls.
    Endpoint services still enforce the exact per-file MAX_UPLOAD_BYTES limit.
    """
    def __init__(self, app):
        self.app = app
        self.limit = settings.MAX_UPLOAD_BYTES + 1024 * 1024

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        lengths = [value for key, value in scope.get("headers", []) if key == b"content-length"]
        try:
            if len(lengths) > 1 or (lengths and not lengths[0].isdigit()):
                raise ValueError
            oversized = bool(lengths and int(lengths[0]) > self.limit)
        except ValueError:
            return await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
        if oversized:
            return await JSONResponse({"detail": "Request body exceeds upload limit"}, status_code=413)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.limit:
                return await JSONResponse({"detail": "Request body exceeds upload limit"}, status_code=413)(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        pending = True
        async def bounded_receive():
            nonlocal pending
            if pending:
                pending = False
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()
        await self.app(scope, bounded_receive, send)


from fastapi.middleware.gzip import GZipMiddleware
import time
import uuid

docs_enabled = settings.ENABLE_DOCS or (settings.ENVIRONMENT != "production")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs_enabled else None,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    lifespan=lifespan
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
                   allow_headers=["Content-Type", "X-CSRF-Token", "X-AgriTrade-Portal", "X-Request-ID"])
# Outer to body buffering: arrival time must precede uploads and SQL lock waits.
app.add_middleware(SessionResponseMiddleware)


@app.middleware("http")
async def request_tracing_and_timing(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000.0

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
    return response


@app.middleware("http")
async def private_responses(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.COOKIE_SECURE or settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    # ServerErrorMiddleware is outside user middleware, so its response must
    # deliver any committed rotation using the shared ASGI request state.
    response = JSONResponse(status_code=500, content={"detail": "Internal server error"},
                            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                                     "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer"})
    apply_pending_session_cookie(response, request.scope.setdefault("state", {}))
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(settings.API_V1_STR + "/health")
@app.get("/health", include_in_schema=False)
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unavailable"})


@app.get("/")
def root():
    return {"project": settings.PROJECT_NAME, "version": settings.VERSION, "status": "running"}


def start():
    import uvicorn
    uvicorn.run("app.main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")),
                reload=settings.ENVIRONMENT == "development", access_log=False)


if __name__ == "__main__":
    start()
