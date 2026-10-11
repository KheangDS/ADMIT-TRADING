"""Database-authoritative authentication, internal access authorization and CSRF."""
import hashlib
import hmac
import math
import secrets

import jwt
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlsplit

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.accounts import AuditEvent, AuthSession, SessionCredential, User, utcnow, uuid_string


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "agritrade"
JWT_AUDIENCE = "agritrade-api"


from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed or not isinstance(hashed, str):
        return False
    try:
        return password_hasher.verify(password, hashed)
    except Exception:
        return False


def audit(db: Session, user: User | str | None, action: str, entity_type: str, entity_id: str, details: dict | None = None):
    actor_id = getattr(user, "id", str(user) if user and isinstance(user, str) else None)
    event = AuditEvent(actor_id=actor_id, action=action, entity_type=entity_type,
                       entity_id=str(entity_id), details=details or {})
    db.add(event)
    try:
        from app.services.redis_service import redis_service
        redis_service.delete_by_pattern("admin:audit_events*")
    except Exception:
        pass
    return event


def revoke_user_sessions(db: Session, user_id: str):
    db.execute(update(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)).values(revoked_at=utcnow()))


def promote_email(db: Session, email: str, name: str | None = None, password: str | None = None, role: str = "admin"):
    email = email.strip().casefold()
    if not email or len(email) > 320:
        raise ValueError("An email address is required")
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    pwd_hash = hash_password(password) if password else None
    if user is None:
        user = User(email=email, name=name or email, role=role, password_hash=pwd_hash, google_sub=None)
        db.add(user)
        db.flush()
    else:
        user.role = role
        if pwd_hash:
            user.password_hash = pwd_hash
        if name:
            user.name = name
    revoke_user_sessions(db, user.id)
    audit(db, None, "account.promote", "user", user.id, {"provisioned_by": "operator_promotion", "role": role})
    return user


def safe_return_to(value: str) -> str:
    """Only relative application paths, including protection against encoded redirects."""
    if len(value) > 2048:
        raise HTTPException(400, "Invalid return URL")
    decoded = value
    for _ in range(4):
        decoded = unquote(decoded)
    parts = urlsplit(decoded)
    if not decoded.startswith("/") or decoded.startswith("//") or parts.scheme or parts.netloc or "\\" in decoded or any(ord(c) < 32 or ord(c) == 127 for c in decoded):
        raise HTTPException(400, "Return URL must be a local relative path")
    return value


def _signed_access(session: AuthSession, expires: datetime) -> str:
    if len(settings.SESSION_SIGNING_KEY.encode()) < 32:
        raise RuntimeError("Configure SESSION_SIGNING_KEY with at least 32 random bytes")
    payload = {"sid": session.id, "sub": session.user_id, "role": session.role_at_issue,
               "exp": as_utc(expires).timestamp(), "iat": utcnow().timestamp(),
               "iss": JWT_ISSUER, "aud": JWT_AUDIENCE}
    return jwt.encode(payload, settings.SESSION_SIGNING_KEY, algorithm=JWT_ALGORITHM)


def _valid_access(session: AuthSession, now: datetime) -> bool:
    if as_utc(session.access_expires_at) <= now:
        return False
    try:
        payload = jwt.decode(session.access_token, settings.SESSION_SIGNING_KEY,
                             algorithms=[JWT_ALGORITHM], issuer=JWT_ISSUER, audience=JWT_AUDIENCE,
                             options={"require": ["sid", "sub", "role", "exp", "iat", "iss", "aud"],
                                      "verify_exp": False, "verify_iat": False})
        # Use the same server clock as session rotation, retaining subsecond expiry.
        # PyJWT's default expiry check truncates NumericDate to integer seconds.
        expiry, issued = payload["exp"], payload["iat"]
        numeric = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        return (numeric(expiry) and numeric(issued) and (issued - 5.0) <= now.timestamp() < expiry
                and payload["sid"] == session.id and payload["sub"] == session.user_id
                and payload["role"] == session.role_at_issue)
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError, OverflowError):
        return False


def _is_admin_request(request: Request | None) -> bool:
    if not request:
        return False
    if request.headers.get("x-agritrade-portal") == "admin":
        return True
    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")
    host = request.headers.get("host", "")
    admin_url = settings.ADMIN_URL
    admin_netloc = urlsplit(admin_url).netloc or admin_url.replace("http://", "").replace("https://", "")
    if origin and (origin == admin_url or urlsplit(origin).netloc == admin_netloc or ":5174" in origin):
        return True
    if referer and (referer.startswith(admin_url) or urlsplit(referer).netloc == admin_netloc or ":5174" in referer):
        return True
    if host and (host == admin_netloc or ":5174" in host):
        return True
    if getattr(request, "url", None) and request.url.path.startswith(settings.API_V1_STR + "/admin"):
        return True
    return False


def _set_session_cookie(response: Response, secret: str, expires_at: datetime, cookie_name: str = settings.SESSION_COOKIE_NAME):
    response.set_cookie(cookie_name, secret, httponly=True, secure=settings.COOKIE_SECURE,
                        samesite="lax", path="/", max_age=max(0, int((as_utc(expires_at) - utcnow()).total_seconds())))


def set_session_cookie(response: Response, secret: str, session: AuthSession, request: Request | None = None, cookie_name: str | None = None):
    target = cookie_name or (settings.ADMIN_SESSION_COOKIE_NAME if _is_admin_request(request) else settings.SESSION_COOKIE_NAME)
    _set_session_cookie(response, secret, session.expires_at, target)


def clear_session_cookie(response: Response, request: Request | None = None, cookie_name: str | None = None):
    target = cookie_name or (settings.ADMIN_SESSION_COOKIE_NAME if _is_admin_request(request) else settings.SESSION_COOKIE_NAME)
    response.delete_cookie(target, path="/", httponly=True,
                           secure=settings.COOKIE_SECURE, samesite="lax")


def apply_pending_session_cookie(response: Response, state: dict):
    """Consume a rotation once, preserving explicit login/refresh/logout cookies."""
    pending = state.pop("auth_pending_cookie", None)
    if pending is None:
        return
    secret, expires_at, cookie_name = pending
    cookie_prefix = (cookie_name + "=").encode()
    if not any(key.lower() == b"set-cookie" and value.startswith(cookie_prefix)
               for key, value in response.raw_headers):
        _set_session_cookie(response, secret, expires_at, cookie_name)


class SessionResponseMiddleware:
    """Capture arrival before body/SQL waits; deliver rotations on the final response."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        state = scope.setdefault("state", {})
        state["auth_request_started_at"] = utcnow()

        async def send_response(message):
            if message["type"] == "http.response.start":
                response = Response()
                response.raw_headers = list(message.get("headers", []))
                apply_pending_session_cookie(response, state)
                message = {**message, "headers": response.raw_headers}
            await send(message)

        await self.app(scope, receive, send_response)


def create_session(db: Session, user: User) -> tuple[AuthSession, str]:
    if user.disabled:
        raise HTTPException(403, "Account is disabled")
    now = utcnow()
    days = settings.ADMIN_REFRESH_DAYS if user.role in {"admin", "superadmin"} else settings.MEMBER_REFRESH_DAYS
    session = AuthSession(id=uuid_string(), user_id=user.id, role_at_issue=user.role,
                          csrf_token=secrets.token_urlsafe(32), created_at=now, rotated_at=now,
                          access_expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
                          expires_at=now + timedelta(days=days))
    session.access_token = _signed_access(session, session.access_expires_at)
    db.add(session)
    db.flush()
    secret = secrets.token_urlsafe(48)
    db.add(SessionCredential(secret_hash=hash_secret(secret), session_id=session.id))
    return session, secret


def rotate_session(db: Session, session: AuthSession, credential: SessionCredential) -> str:
    now = utcnow()
    if credential.spent_at is not None or session.revoked_at is not None or as_utc(session.expires_at) <= now:
        session.revoked_at = now
        db.commit()
        raise HTTPException(401, "Session is expired or revoked")
    credential.spent_at = now
    session.rotated_at = now
    session.access_expires_at = min(now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES), as_utc(session.expires_at))
    session.access_token = _signed_access(session, session.access_expires_at)
    secret = secrets.token_urlsafe(48)
    db.add(SessionCredential(secret_hash=hash_secret(secret), session_id=session.id))
    db.commit()
    return secret


def csrf_protect(request: Request, user_or_session=None):
    if request.method in SAFE_METHODS:
        return
    session = user_or_session if isinstance(user_or_session, AuthSession) else getattr(request.state, "auth_session", None)
    if session is None:
        raise HTTPException(401, "Authentication required")
    origin = request.headers.get("origin")
    if not origin or origin not in settings.CORS_ORIGINS:
        raise HTTPException(403, "Untrusted or missing Origin")
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not hmac.compare_digest(supplied, session.csrf_token):
        raise HTTPException(403, "Invalid CSRF token")


def current_user(request: Request, db: Session = Depends(get_db), response: Response = None) -> User:
    cached = getattr(request.state, "auth_user", None)
    if cached is not None:
        return cached
    arrived_at = as_utc(getattr(request.state, "auth_request_started_at", utcnow()))
    
    secret = None
    if _is_admin_request(request):
        cookie_name = settings.ADMIN_SESSION_COOKIE_NAME
        secret = request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)
    else:
        cookie_name = settings.SESSION_COOKIE_NAME
        secret = request.cookies.get(settings.SESSION_COOKIE_NAME)
        
    if not secret or len(secret) > 256:
        raise HTTPException(401, "Authentication required")
    credential = db.scalar(select(SessionCredential).where(SessionCredential.secret_hash == hash_secret(secret)).with_for_update())
    if credential is None:
        raise HTTPException(401, "Invalid session")
    session = db.scalar(select(AuthSession).where(AuthSession.id == credential.session_id).with_for_update())
    now = utcnow()
    if session is None or session.revoked_at is not None or as_utc(session.expires_at) <= now:
        raise HTTPException(401, "Session is expired or revoked")
    if credential.spent_at is not None:
        # Parallel requests already in flight can carry the immediately previous
        # cookie while the rotating response updates the browser. They may use the
        # current internal authorization briefly, but never refresh/extend it.
        in_flight = (request.url.path != settings.API_V1_STR + "/auth/refresh"
                     and (arrived_at - as_utc(credential.spent_at)).total_seconds() < settings.SESSION_ROTATION_GRACE_SECONDS
                     and as_utc(credential.spent_at) == as_utc(session.rotated_at)
                     and _valid_access(session, now))
        if not in_flight:
            session.revoked_at = now
            audit(db, None, "auth.refresh_reuse", "auth_session", session.id)
            db.commit()
            raise HTTPException(401, "Session is expired or revoked")
    user = db.get(User, session.user_id, populate_existing=True)
    if user is None or user.disabled or user.role != session.role_at_issue:
        session.revoked_at = now
        db.commit()
        raise HTTPException(401, "Account authorization changed; sign in again")
    request.state.auth_session = session
    request.state.auth_credential = credential
    request.state.auth_cookie_name = cookie_name
    # Protect all authenticated mutations, even if an endpoint forgets its dependency.
    csrf_protect(request, session)
    if as_utc(session.access_expires_at) <= now:
        rotated = rotate_session(db, session, credential)
        request.state.auth_pending_cookie = (rotated, as_utc(session.expires_at), cookie_name)
        request.state.auth_rotated = True
    elif not _valid_access(session, now):
        session.revoked_at = now
        db.commit()
        raise HTTPException(401, "Invalid internal authorization")
    request.state.auth_user = user
    return user


def require_admin(request: Request, user: User = Depends(current_user)) -> User:
    if user.role not in {"admin", "superadmin"}:
        raise HTTPException(403, "Administrator access required")
    return user


def require_superadmin(request: Request, user: User = Depends(current_user)) -> User:
    if user.role != "superadmin":
        raise HTTPException(403, "Superadministrator access required")
    return user


def membership_for(db: Session, user_id: str):
    # Deliberately lazy: domain modules import these authentication dependencies.
    from app.services.membership_service import membership_info
    return membership_info(db, user_id)


def require_member(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)) -> User:
    if user.role not in {"admin", "superadmin"} and not (membership_for(db, user.id) or {}).get("active", False):
        raise HTTPException(403, "Active membership required")
    return user


def require_csrf(request: Request, user: User = Depends(current_user)) -> User:
    csrf_protect(request, user)
    return user


def auth_metadata(db: Session, user: User, session: AuthSession) -> dict:
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role},
            "csrf_token": session.csrf_token, "membership": membership_for(db, user.id)}
