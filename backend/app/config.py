"""Environment-only configuration; no development credentials or production fallbacks."""
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AgriTrade API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = ""
    SESSION_COOKIE_NAME: str = "agritrade_session"
    ADMIN_SESSION_COOKIE_NAME: str = "agritrade_admin_session"
    COOKIE_SECURE: bool = True
    SESSION_SIGNING_KEY: str = ""
    ACCESS_TOKEN_MINUTES: int = 15
    ADMIN_REFRESH_DAYS: int = 1
    MEMBER_REFRESH_DAYS: int = 3
    OAUTH_STATE_MINUTES: int = 10
    SESSION_ROTATION_GRACE_SECONDS: int = 5
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    FRONTEND_URL: str = ""
    ADMIN_URL: str = ""
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_NAME: str = ""
    CORS_ORIGINS: list[str] = []
    STORAGE_PATH: str = str(Path(__file__).resolve().parents[1] / "storage" / "private")
    MAX_UPLOAD_BYTES: int = 26214400
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""
    PAYMENT_QR_USD_URL: str = ""
    PAYMENT_QR_KHR_URL: str = ""
    KHQR_MERCHANT_NAME: str = ""
    KHQR_MERCHANT_ID: str = ""
    KHQR_BAKONG_ACCOUNT: str = ""
    KHQR_BANK_NAME: str = ""
    KHQR_CITY: str = ""
    KHQR_MCC: str = ""
    KHQR_PAYWAY_REF: str = ""
    KHQR_USD_ACCOUNT: str = ""
    KHQR_KHR_ACCOUNT: str = ""
    RECEIPT_FONT_PATH: str | None = str(Path(__file__).resolve().parent / "assets" / "fonts" / "NotoSansKhmer.ttf")
    LIBREOFFICE_PATH: str = ""
    BWRAP_PATH: str = ""
    # Optional network-disabled container converter via a private Unix socket.
    CONVERTER_SOCKET_PATH: str = ""
    TRUSTED_PROXY_IPS: list[str] = []
    GEMINI_API_KEY: str = ""
    # Legacy read-only analytics dependencies retain these names during integration.
    DB_PATH: str = str(Path(__file__).resolve().parents[1] / "storage" / "trade_data.duckdb")
    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""
    REDIS_DASHBOARD_TTL: int = 86400

    # Automatically load .env from backend directory if present
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=(Path(__file__).resolve().parents[1] / ".env", ".env"),
        env_file_encoding="utf-8",
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_security(self):
        if self.ENVIRONMENT not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        if not self.COOKIE_SECURE and self.ENVIRONMENT not in {"development", "test"}:
            raise ValueError("COOKIE_SECURE=false is only allowed in development/test")
        if (self.ACCESS_TOKEN_MINUTES, self.ADMIN_REFRESH_DAYS, self.MEMBER_REFRESH_DAYS) != (15, 1, 3):
            raise ValueError("Auth lifetimes must be 15 minutes, admin 1 day, member 3 days")
        if not 0 <= self.SESSION_ROTATION_GRACE_SECONDS <= 5:
            raise ValueError("Session in-flight rotation grace must be between 0 and 5 seconds")
        if self.MAX_UPLOAD_BYTES <= 0 or not 1 <= self.OAUTH_STATE_MINUTES <= 10:
            raise ValueError("Upload limit and OAuth state lifetime must be positive and bounded")
        for origin in self.CORS_ORIGINS:
            if not origin:
                continue
            parts = urlsplit(origin)
            if parts.scheme not in {"http", "https"} or not parts.netloc or parts.path or parts.query or parts.fragment or parts.username:
                raise ValueError("CORS_ORIGINS must contain exact HTTP(S) origins, never wildcards")
        for url in (self.FRONTEND_URL, self.ADMIN_URL, self.GOOGLE_REDIRECT_URI):
            if not url:
                continue
            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.fragment:
                raise ValueError("UI and OAuth callback URLs must be absolute HTTP(S) URLs")
            if self.ENVIRONMENT == "production" and parts.scheme != "https":
                raise ValueError("Production UI and OAuth URLs require HTTPS")
        if self.ENVIRONMENT == "production" and any(not x.startswith("https://") for x in self.CORS_ORIGINS if x):
            raise ValueError("Production CORS origins require HTTPS")
        return self

    def validate_auth(self) -> None:
        if not self.GOOGLE_CLIENT_ID or not self.GOOGLE_CLIENT_SECRET:
            raise RuntimeError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env file")
        if len(self.SESSION_SIGNING_KEY.encode()) < 32:
            raise RuntimeError("Missing or invalid SESSION_SIGNING_KEY in .env (minimum 32 characters required)")


settings = Settings()
