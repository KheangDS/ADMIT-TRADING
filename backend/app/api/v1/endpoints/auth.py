"""Google authorization code flow; codes and tokens are handled only server-side."""
import base64
import hashlib
import hmac
import secrets
from datetime import timedelta
from functools import partial
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from pydantic import BaseModel, Field
from app.config import settings
from app.db import get_db
from app.models.accounts import OAuthState, User, utcnow
from app.models.membership import OutboxJob
from app.services.auth_service import (as_utc, audit, auth_metadata, clear_session_cookie,
                                      create_session, current_user, hash_password, hash_secret,
                                      _is_admin_request, require_csrf, rotate_session, safe_return_to, set_session_cookie,
                                      verify_password)
from app.services.redis_service import redis_service
from app.services.rate_limit_service import auth_rate_limit

router = APIRouter(prefix="/auth")
OAUTH_COOKIE = "agritrade_oauth"


class RegisterInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ResetPasswordInput(BaseModel):
    token: str = Field(min_length=10, max_length=2048)
    password: str = Field(min_length=8, max_length=128)


def _clear_oauth_cookie(response: Response):
    response.delete_cookie(OAUTH_COOKIE, path=settings.API_V1_STR + "/auth/google",
                           secure=settings.COOKIE_SECURE, httponly=True, samesite="lax")


@router.post("/register", status_code=201, dependencies=[Depends(auth_rate_limit)])
def register(body: RegisterInput, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.strip().casefold()
    if not email:
        raise HTTPException(422, "Please enter an email address")
    name = " ".join(body.name.split())
    if not name:
        raise HTTPException(422, "Please enter your name")
    
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(409, "An account with this email address already exists")
    
    user = User(email=email, name=name, password_hash=hash_password(body.password), role="member")
    db.add(user)
    try:
        db.flush()
        target_cookie = settings.ADMIN_SESSION_COOKIE_NAME if _is_admin_request(request) else settings.SESSION_COOKIE_NAME
        if (old_secret := request.cookies.get(target_cookie)):
            from app.models.accounts import AuthSession, SessionCredential
            old = db.scalar(select(SessionCredential).where(SessionCredential.secret_hash == hash_secret(old_secret)))
            if old:
                previous = db.get(AuthSession, old.session_id)
                if previous:
                    previous.revoked_at = utcnow()
        session, secret = create_session(db, user)
        db.add(OutboxJob(kind="welcome_email", entity_id=user.id, dedupe_key=f"welcome:{user.id}"))
        audit(db, user, "auth.register", "user", user.id, {"email": user.email, "name": user.name, "role": user.role})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account creation conflict; please try again")
        
    set_session_cookie(response, secret, session, request=request)
    return auth_metadata(db, user, session)


@router.post("/login", dependencies=[Depends(auth_rate_limit)])
def login(body: LoginInput, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.strip().casefold()
    user = db.scalar(select(User).where(User.email == email))
    if user is not None and user.google_sub is not None and not user.password_hash:
        raise HTTPException(
            401,
            "This account was registered with Google Sign-In. Please click 'Sign in with Google' below, or use 'Forgot password' to set a local password."
        )
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password. Don't have an account yet? Click Create Account.")
    if user.disabled:
        raise HTTPException(403, "Account is disabled")
        
    try:
        target_cookie = settings.ADMIN_SESSION_COOKIE_NAME if _is_admin_request(request) else settings.SESSION_COOKIE_NAME
        old_secret = request.cookies.get(target_cookie)
        if old_secret:
            from app.models.accounts import AuthSession, SessionCredential
            old = db.scalar(select(SessionCredential).where(SessionCredential.secret_hash == hash_secret(old_secret)))
            if old:
                previous = db.get(AuthSession, old.session_id)
                if previous:
                    previous.revoked_at = utcnow()
        session, secret = create_session(db, user)
        audit(db, user, "auth.login_password", "user", user.id, {"email": user.email, "name": user.name, "role": user.role})
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "Could not create session")
        
    set_session_cookie(response, secret, session, request=request)
    return auth_metadata(db, user, session)


@router.get("/me")
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user = current_user(request, db, response)
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
        clear_session_cookie(response, request=request)
        return {"user": None, "csrf_token": None, "membership": None}
    return auth_metadata(db, user, request.state.auth_session)


async def exchange_google_code(code: str, verifier: str) -> dict:
    """Small mockable adapter, fixed provider URL, bounded timeout, no token logging."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code, "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET, "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code", "code_verifier": verifier,
            })
            response.raise_for_status()
            token = response.json().get("id_token")
        if not isinstance(token, str) or not token:
            raise ValueError("Missing identity token")
        claims = await run_in_threadpool(id_token.verify_oauth2_token, token, partial(GoogleRequest(), timeout=15), settings.GOOGLE_CLIENT_ID)
        return claims
    except (httpx.HTTPError, GoogleAuthError, ValueError, KeyError):
        raise HTTPException(400, "Google sign-in could not be verified") from None


@router.get("/google/start")
def google_start(return_to: str = "/account", db: Session = Depends(get_db)):
    settings.validate_auth()
    return_to = safe_return_to(return_to)
    state, browser, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(4))
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    db.add(OAuthState(state_hash=hash_secret(state), browser_hash=hash_secret(browser), nonce=nonce,
                      pkce_verifier=verifier, return_to=return_to,
                      expires_at=utcnow() + timedelta(minutes=settings.OAUTH_STATE_MINUTES)))
    db.commit()
    params = {"client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": settings.GOOGLE_REDIRECT_URI,
              "response_type": "code", "scope": "openid email profile", "state": state, "nonce": nonce,
              "code_challenge": challenge, "code_challenge_method": "S256", "prompt": "select_account"}
    response = RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params), status_code=302)
    response.set_cookie(OAUTH_COOKIE, browser, httponly=True, secure=settings.COOKIE_SECURE,
                        samesite="lax", path=settings.API_V1_STR + "/auth/google",
                        max_age=settings.OAUTH_STATE_MINUTES * 60)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/google/callback")
async def google_callback(request: Request, state: str = "", code: str = "", error: str = "",
                          db: Session = Depends(get_db)):
    settings.validate_auth()
    browser = request.cookies.get(OAUTH_COOKIE, "")

    if error:
        destination = f"{settings.FRONTEND_URL.rstrip('/')}/login?error={error}"
        if state and len(state) <= 256:
            oauth = db.scalar(select(OAuthState).where(OAuthState.state_hash == hash_secret(state)))
            if oauth and oauth.return_to == "/admin":
                destination = f"{settings.ADMIN_URL.rstrip('/')}/login?error={error}"
            elif oauth and oauth.return_to:
                destination = f"{settings.FRONTEND_URL.rstrip('/')}/login?return_to={safe_return_to(oauth.return_to)}&error={error}"
        response = RedirectResponse(destination, status_code=302)
        _clear_oauth_cookie(response)
        return response

    if not state or len(state) > 256 or not browser or len(browser) > 256 or not code or len(code) > 8192:
        raise HTTPException(400, "Invalid Google sign-in callback")
    oauth = db.scalar(select(OAuthState).where(OAuthState.state_hash == hash_secret(state)).with_for_update())
    if oauth is None or oauth.consumed_at is not None or as_utc(oauth.expires_at) <= utcnow() or not hmac.compare_digest(oauth.browser_hash, hash_secret(browser)):
        raise HTTPException(400, "Google sign-in state is invalid or expired")
    oauth.consumed_at = utcnow()
    # Consume before remote I/O so callback/code replay cannot race the network exchange.
    db.commit()
    claims = await exchange_google_code(code, oauth.pkce_verifier)
    nonce = claims.get("nonce")
    if not isinstance(nonce, str) or not hmac.compare_digest(nonce, oauth.nonce):
        raise HTTPException(400, "Google sign-in nonce is invalid")
    if claims.get("email_verified") is not True or claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"} or claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(400, "A verified Google email is required")
    sub, email = claims.get("sub"), claims.get("email")
    if not isinstance(sub, str) or not sub or len(sub) > 255 or not isinstance(email, str) or "@" not in email or len(email) > 320:
        raise HTTPException(400, "Invalid Google account identity")
    email = email.strip().casefold()
    is_new_user = False
    user = db.scalar(select(User).where(User.google_sub == sub).with_for_update())
    if user is None:
        invited = db.scalar(select(User).where(User.email == email).with_for_update())
        if invited is not None:
            if invited.google_sub is not None:
                raise HTTPException(409, "This email is linked to a different identity")
            user = invited
            user.google_sub = sub
        else:
            user = User(google_sub=sub, email=email, name=str(claims.get("name") or email)[:255], role="member")
            db.add(user)
            is_new_user = True
    if user.disabled:
        raise HTTPException(403, "Account is disabled")
    # The role is always the stored role, never a claim, query parameter or request field.
    user.email = email
    user.name = str(claims.get("name") or user.name)[:255]
    try:
        db.flush()
        target_cookie = settings.ADMIN_SESSION_COOKIE_NAME if (oauth.return_to == "/admin" or _is_admin_request(request)) else settings.SESSION_COOKIE_NAME
        if (old_secret := request.cookies.get(target_cookie)):
            # Reauthentication replaces the previous browser session rather than leaving it valid.
            from app.models.accounts import AuthSession, SessionCredential
            old = db.scalar(select(SessionCredential).where(SessionCredential.secret_hash == hash_secret(old_secret)))
            if old:
                previous = db.get(AuthSession, old.session_id)
                if previous:
                    previous.revoked_at = utcnow()
        session, secret = create_session(db, user)
        if is_new_user:
            db.add(OutboxJob(kind="welcome_email", entity_id=user.id, dedupe_key=f"welcome:{user.id}"))
        audit(db, user, "auth.login", "user", user.id, {"email": user.email, "name": user.name, "role": user.role})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account identity conflict; retry sign-in") from None
    destination = (settings.ADMIN_URL if oauth.return_to == "/admin"
                   else settings.FRONTEND_URL.rstrip("/") + safe_return_to(oauth.return_to))
    response = RedirectResponse(destination, status_code=302)
    set_session_cookie(response, secret, session, request=request, cookie_name=target_cookie)
    _clear_oauth_cookie(response)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.post("/refresh", dependencies=[Depends(require_csrf)])
def refresh(request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(current_user)):
    session = request.state.auth_session
    if not getattr(request.state, "auth_rotated", False):
        secret = rotate_session(db, session, request.state.auth_credential)
        set_session_cookie(response, secret, session, request=request)
    return auth_metadata(db, user, session)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user = current_user(request, db, response)
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
    else:
        request.state.auth_session.revoked_at = utcnow()
        audit(db, user, "auth.logout", "auth_session", request.state.auth_session.id, {"email": user.email, "name": user.name})
        db.commit()
    clear_session_cookie(response, request=request)
    response.status_code = 204
    return response


@router.post("/forgot-password", dependencies=[Depends(auth_rate_limit)])
def forgot_password(body: ForgotPasswordInput, db: Session = Depends(get_db)):
    email = body.email.strip().casefold()
    if not email:
        raise HTTPException(422, "Please enter an email address")

    user = db.scalar(select(User).where(User.email == email))
    if user and not user.disabled:
        # Generate 15-minute cryptographically signed token
        now = utcnow()
        exp = now + timedelta(minutes=15)
        payload = {
            "sub": user.id,
            "email": user.email,
            "purpose": "password_reset",
            "iat": now.timestamp(),
            "exp": exp.timestamp()
        }
        token = jwt.encode(payload, settings.SESSION_SIGNING_KEY, algorithm="HS256")

        # Store single-use tracking in Redis with 900s TTL
        token_hash = hash_secret(token)
        redis_service.set_json(f"auth:pwd_reset:{token_hash}", {"user_id": user.id, "email": user.email, "used": False}, ttl_seconds=900)

        # Send password reset email
        try:
            from app.services.email_service import send_password_reset_email
            send_password_reset_email(user, token)
        except Exception:
            pass

        audit(db, user, "auth.forgot_password_requested", "user", user.id, {"email": user.email})
        db.commit()

    return {"message": "A password reset link has been sent to your email address. Please check your inbox and spam folder."}


@router.post("/reset-password", dependencies=[Depends(auth_rate_limit)])
def reset_password(body: ResetPasswordInput, db: Session = Depends(get_db)):
    token = body.token.strip()
    new_password = body.password
    if len(new_password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")

    # Verify JWT Token
    try:
        payload = jwt.decode(
            token,
            settings.SESSION_SIGNING_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "email", "purpose", "exp", "iat"]}
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "Password reset link has expired. Please request a new one.")
    except jwt.InvalidTokenError:
        raise HTTPException(400, "Invalid password reset link")

    if payload.get("purpose") != "password_reset":
        raise HTTPException(400, "Invalid token purpose")

    user_id = payload.get("sub")
    email = payload.get("email")

    # Single-Use Verification in Redis
    token_hash = hash_secret(token)
    reset_record = redis_service.get_json(f"auth:pwd_reset:{token_hash}")

    if reset_record is not None:
        if reset_record.get("used"):
            raise HTTPException(400, "This password reset link has already been used. Please request a new one.")
        redis_service.set_json(f"auth:pwd_reset:{token_hash}", {"used": True}, ttl_seconds=300)

    user = db.scalar(select(User).where(User.id == user_id, User.email == email).with_for_update())
    if not user or user.disabled:
        raise HTTPException(400, "Account not found or disabled")

    # Update Password and Invalidate Existing Sessions
    user.password_hash = hash_password(new_password)
    from app.services.auth_service import revoke_user_sessions
    revoke_user_sessions(db, user.id)
    audit(db, user, "auth.reset_password_completed", "user", user.id, {"email": user.email})
    db.commit()

    return {"message": "Your password has been successfully reset. Please log in with your new password."}
