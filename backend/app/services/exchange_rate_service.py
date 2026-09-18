import time
import httpx
from typing import Optional
from pydantic import BaseModel

from app.models.schemas import ExchangeRateInfo

MEF_EXCHANGE_RATE_URL = "https://data.mef.gov.kh/api/v1/realtime-api/exchange-rate?currency_id=USD"
FALLBACK_RATE = 4000.0

class ExchangeRateService:
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl = cache_ttl_seconds
        self._cached_info: Optional[ExchangeRateInfo] = None
        self._last_fetched_time: float = 0.0

    async def fetch_live_rate_async(self, force_refresh: bool = False) -> ExchangeRateInfo:
        """
        Asynchronously fetches live real-time USD to KHR exchange rate from Cambodia MEF API.
        Falls back to 4000 KHR / 1 USD if the API call fails or times out.
        """
        current_time = time.time()
        if not force_refresh and self._cached_info and (current_time - self._last_fetched_time < self.cache_ttl):
            return self._cached_info

        try:
            async with httpx.AsyncClient(timeout=2.5, verify=False) as client:
                response = await client.get(MEF_EXCHANGE_RATE_URL)
                if response.status_code == 200:
                    json_data = response.json()
                    data = json_data.get("data", {})
                    live_rate = float(data.get("average") or data.get("bid") or data.get("ask") or FALLBACK_RATE)
                    valid_date = data.get("valid_date")
                    
                    info = ExchangeRateInfo(
                        rate=live_rate,
                        is_realtime=True,
                        currency="USD",
                        valid_date=valid_date,
                        source="Ministry of Economy and Finance (MEF)",
                        error_message=None
                    )
                    self._cached_info = info
                    self._last_fetched_time = current_time
                    return info
                else:
                    error_msg = f"MEF API returned HTTP status {response.status_code}"
        except Exception as e:
            error_msg = f"Could not connect to MEF API: {str(e)}"

        # Fallback response
        fallback_info = ExchangeRateInfo(
            rate=FALLBACK_RATE,
            is_realtime=False,
            currency="USD",
            valid_date=None,
            source="Default Fallback",
            error_message=error_msg or "Failed to fetch real-time exchange rate. Using default 4,000 KHR."
        )
        self._cached_info = fallback_info
        self._last_fetched_time = current_time
        return fallback_info

    def fetch_live_rate(self, force_refresh: bool = False) -> ExchangeRateInfo:
        """
        Synchronous wrapper with quick timeout for non-async contexts.
        """
        current_time = time.time()
        if not force_refresh and self._cached_info and (current_time - self._last_fetched_time < self.cache_ttl):
            return self._cached_info

        try:
            with httpx.Client(timeout=2.5, verify=False) as client:
                response = client.get(MEF_EXCHANGE_RATE_URL)
                if response.status_code == 200:
                    json_data = response.json()
                    data = json_data.get("data", {})
                    live_rate = float(data.get("average") or data.get("bid") or data.get("ask") or FALLBACK_RATE)
                    valid_date = data.get("valid_date")
                    
                    info = ExchangeRateInfo(
                        rate=live_rate,
                        is_realtime=True,
                        currency="USD",
                        valid_date=valid_date,
                        source="Ministry of Economy and Finance (MEF)",
                        error_message=None
                    )
                    self._cached_info = info
                    self._last_fetched_time = current_time
                    return info
                else:
                    error_msg = f"MEF API returned HTTP status {response.status_code}"
        except Exception as e:
            error_msg = f"Could not connect to MEF API: {str(e)}"

        fallback_info = ExchangeRateInfo(
            rate=FALLBACK_RATE,
            is_realtime=False,
            currency="USD",
            valid_date=None,
            source="Default Fallback",
            error_message=error_msg or "Failed to fetch real-time exchange rate. Using default 4,000 KHR."
        )
        self._cached_info = fallback_info
        self._last_fetched_time = current_time
        return fallback_info

    def get_current_rate_value(self) -> float:
        """Returns the current exchange rate numerical value (e.g. 4050.0 or 4000.0)."""
        return self.fetch_live_rate().rate

exchange_rate_service = ExchangeRateService()

