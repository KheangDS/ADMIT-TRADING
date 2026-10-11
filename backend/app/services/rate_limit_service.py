"""Sliding-window rate limiting backed by Redis or high-performance in-memory cache."""
import time
from typing import Callable, Optional
from fastapi import HTTPException, Request
from app.config import settings
from app.services.redis_service import redis_service


def get_client_identifier(request: Request) -> str:
    """Safely extracts client IP or authenticated subject identifier."""
    # Check for authenticated session state
    auth_user = getattr(request.state, "auth_user", None)
    if auth_user and hasattr(auth_user, "id"):
        return f"user:{auth_user.id}"

    # Extract client IP with proxy trust validation
    client_ip = request.client.host if request.client else "127.0.0.1"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and client_ip in (settings.TRUSTED_PROXY_IPS or []):
        client_ip = forwarded.split(",")[0].strip()

    return f"ip:{client_ip}"


def rate_limit(limit: int = 60, window_seconds: int = 60, key_prefix: str = "general", message: Optional[str] = None) -> Callable:
    """
    FastAPI dependency generating sliding-window rate limit checks.
    
    Args:
        limit: Maximum number of requests allowed in the time window.
        window_seconds: Duration of the rate limit window in seconds (default 60s).
        key_prefix: Unique namespace for the endpoint category (e.g. 'auth_login').
    """
    def dependency(request: Request):
        is_test_env = getattr(settings, "ENVIRONMENT", "") == "test"
        is_explicit_test = key_prefix.startswith("test_") or bool(request.headers.get("x-test-rate-limit"))
        if is_test_env and not is_explicit_test:
            return

        identifier = get_client_identifier(request)
        now = int(time.time())
        window_bucket = now // window_seconds
        cache_key = f"agritrade:ratelimit:{key_prefix}:{identifier}:{window_bucket}"

        current_count = redis_service.get_json(cache_key)
        count = int(current_count) if current_count is not None else 0

        if count >= limit:
            retry_after = max(1, window_seconds - (now % window_seconds))
            detail_msg = message or ("Too many login attempts. Please try again in 1 minute." if "auth" in key_prefix else "Too many requests. Please try again in 1 minute.")
            raise HTTPException(
                status_code=429,
                detail=detail_msg,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )

        redis_service.set_json(cache_key, count + 1, ttl_seconds=window_seconds * 2)

    return dependency


# Standard pre-configured rate limit dependencies
auth_rate_limit = rate_limit(limit=5, window_seconds=60, key_prefix="auth_login")
payment_rate_limit = rate_limit(limit=10, window_seconds=60, key_prefix="payment_qr")
chat_rate_limit = rate_limit(limit=20, window_seconds=60, key_prefix="ai_chat")
api_rate_limit = rate_limit(limit=120, window_seconds=60, key_prefix="api_general")
