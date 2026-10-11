import datetime
import math
import time
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import ExchangeRateInfo

MEF_EXCHANGE_RATE_URL = "https://data.mef.gov.kh/api/v1/realtime-api/exchange-rate?currency_id=USD"
FALLBACK_RATE = 4000.0
DAILY_CACHE_TTL_SECONDS = 86400  # 24 hours / 1 day


class ExchangeRateService:
    def __init__(self, cache_ttl_seconds: int = DAILY_CACHE_TTL_SECONDS):
        self.cache_ttl = cache_ttl_seconds
        self._cached_info: Optional[ExchangeRateInfo] = None
        self._last_fetched_time = 0.0

    @staticmethod
    def _parse_response(response: httpx.Response) -> ExchangeRateInfo:
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ValueError("MEF response does not contain a rate object")
        rate = None
        for key in ("average", "bid", "ask"):
            raw = data.get(key)
            if raw is None or isinstance(raw, bool):
                continue
            try:
                candidate = float(raw)
            except (TypeError, ValueError):
                continue
            if math.isfinite(candidate) and candidate > 0:
                rate = candidate
                break
        if rate is None:
            raise ValueError("MEF response does not contain a positive finite rate")
        date = data.get("valid_date") or data.get("date") or datetime.date.today().isoformat()
        return ExchangeRateInfo(
            rate=rate,
            is_realtime=True,
            currency="USD",
            valid_date=str(date),
            source="Ministry of Economy and Finance (MEF)",
        )

    def _record(self, info: ExchangeRateInfo) -> ExchangeRateInfo:
        self._cached_info = info
        self._last_fetched_time = time.monotonic()
        if getattr(settings, "ENVIRONMENT", "") != "test":
            try:
                from app.services.redis_service import redis_service
                today_str = datetime.date.today().isoformat()
                redis_service.set_json(f"agritrade:exchange_rate:daily:{today_str}", info.model_dump(), ttl_seconds=self.cache_ttl)
            except Exception:
                pass
        return info

    def _cached(self, force_refresh: bool) -> Optional[ExchangeRateInfo]:
        if force_refresh:
            return None
        if self._cached_info and time.monotonic() - self._last_fetched_time < self.cache_ttl:
            return self._cached_info
        if getattr(settings, "ENVIRONMENT", "") != "test":
            try:
                from app.services.redis_service import redis_service
                today_str = datetime.date.today().isoformat()
                cached_data = redis_service.get_json(f"agritrade:exchange_rate:daily:{today_str}")
                if cached_data:
                    info = ExchangeRateInfo(**cached_data)
                    self._cached_info = info
                    self._last_fetched_time = time.monotonic()
                    return info
            except Exception:
                pass
        return None

    def _fallback(self, error: Exception) -> ExchangeRateInfo:
        # Do not expose upstream bodies, credentials, or potentially sensitive URLs.
        return self._record(ExchangeRateInfo(
            rate=FALLBACK_RATE,
            is_realtime=False,
            currency="USD",
            valid_date=datetime.date.today().isoformat(),
            source="Default Fallback (4,000 KHR/USD)",
            error_message=f"MEF rate unavailable ({type(error).__name__}); using the configured fallback.",
        ))

    async def fetch_live_rate_async(self, force_refresh: bool = False) -> ExchangeRateInfo:
        cached = self._cached(force_refresh)
        if cached:
            return cached
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
                return self._record(self._parse_response(await client.get(MEF_EXCHANGE_RATE_URL)))
        except Exception as error:
            return self._fallback(error)

    def fetch_live_rate(self, force_refresh: bool = False) -> ExchangeRateInfo:
        cached = self._cached(force_refresh)
        if cached:
            return cached
        try:
            with httpx.Client(timeout=10.0, verify=True) as client:
                return self._record(self._parse_response(client.get(MEF_EXCHANGE_RATE_URL)))
        except Exception as error:
            return self._fallback(error)

    def get_current_rate_value(self) -> float:
        return self.fetch_live_rate().rate


exchange_rate_service = ExchangeRateService()
