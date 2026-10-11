import json
import time
from typing import Optional, Any, Dict
from app.config import settings

class RedisCacheService:
    def __init__(self):
        self._redis_client = None
        self._in_memory_store: Dict[str, Dict[str, Any]] = {}
        self.is_redis_available: bool = False
        self._init_redis()

    def _init_redis(self):
        """Initializes connection to Redis server if available."""
        if settings.ENVIRONMENT == "test":
            self._redis_client = None
            self.is_redis_available = False
            return
        try:
            import redis
            if settings.REDIS_URL:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_connect_timeout=1.5
                )
            else:
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_connect_timeout=1.5
                )
            # Test connectivity
            self._redis_client.ping()
            self.is_redis_available = True
            print(f"[Redis Service] Successfully connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            self._redis_client = None
            self.is_redis_available = False
            print(f"[Redis Service] Redis server not detected ({e}). Using resilient in-memory fallback cache.")

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves and deserializes JSON from Redis or fallback in-memory store."""
        if self.is_redis_available and self._redis_client:
            try:
                raw = self._redis_client.get(key)
                if raw:
                    return json.loads(raw)
                return None
            except Exception as e:
                print(f"[Redis Service] Error fetching key '{key}': {e}")
                self.is_redis_available = False

        # In-Memory Fallback Check
        if key in self._in_memory_store:
            entry = self._in_memory_store[key]
            if entry['expires_at'] is None or time.time() < entry['expires_at']:
                return entry['data']
            else:
                del self._in_memory_store[key]
        return None

    def set_json(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Serializes and stores JSON in Redis or fallback in-memory store."""
        ttl = ttl_seconds or settings.REDIS_DASHBOARD_TTL
        payload_str = json.dumps(data, default=str)

        if self.is_redis_available and self._redis_client:
            try:
                self._redis_client.set(key, payload_str, ex=ttl)
                return True
            except Exception as e:
                print(f"[Redis Service] Error setting key '{key}': {e}")
                self.is_redis_available = False

        # In-Memory Fallback Storage
        expires_at = (time.time() + ttl) if ttl else None
        self._in_memory_store[key] = {
            'data': data if isinstance(data, dict) else json.loads(payload_str),
            'expires_at': expires_at
        }
        return True

    def delete_by_pattern(self, pattern: str) -> int:
        """Deletes keys matching a prefix or wildcard pattern from Redis and in-memory store."""
        count = 0
        if self.is_redis_available and self._redis_client:
            try:
                keys = self._redis_client.keys(pattern)
                if keys:
                    count = self._redis_client.delete(*keys)
            except Exception as e:
                print(f"[Redis Service] Error deleting pattern '{pattern}': {e}")
                self.is_redis_available = False

        # Clear matching in-memory keys
        prefix = pattern.replace('*', '')
        matching_in_mem = [k for k in self._in_memory_store if k.startswith(prefix)]
        for k in matching_in_mem:
            del self._in_memory_store[k]
            count += 1

        return count

    # --- Domain-Specific Helpers for AgriTrade AI ---

    def get_cached_dashboard(self, exchange_rate: float) -> Optional[Dict[str, Any]]:
        """Retrieves cached consolidated dashboard payload for a given exchange rate."""
        key = f"agritrade:dashboard:master:rate_{int(exchange_rate)}"
        return self.get_json(key)

    def set_cached_dashboard(self, exchange_rate: float, data: Dict[str, Any], ttl_seconds: Optional[int] = None):
        """Stores consolidated dashboard payload in cache."""
        key = f"agritrade:dashboard:master:rate_{int(exchange_rate)}"
        self.set_json(key, data, ttl_seconds)

    def get_cached_admin_status(self) -> Optional[Dict[str, Any]]:
        """Retrieves cached admin database status."""
        return self.get_json("agritrade:admin:status")

    def set_cached_admin_status(self, data: Dict[str, Any], ttl_seconds: int = 300):
        """Stores admin database status in cache."""
        self.set_json("agritrade:admin:status", data, ttl_seconds)

    def invalidate_all_trade_caches(self):
        """
        Invalidates all cached trade metrics, charts, and dashboard payloads
        when a new dataset is uploaded or merged.
        """
        self.delete_by_pattern("agritrade:dashboard:*")
        self.delete_by_pattern("agritrade:trade:*")
        self.delete_by_pattern("agritrade:admin:*")
        print("[Redis Service]  Invalidated all trade dashboard, public status & admin caches due to new data ingestion.")

    def get_status(self) -> Dict[str, Any]:
        """Returns current Redis caching health status."""
        return {
            "is_redis_connected": self.is_redis_available,
            "backend_engine": "Redis Server" if self.is_redis_available else "High-Performance In-Memory Cache",
            "host": settings.REDIS_HOST if self.is_redis_available else "N/A",
            "port": settings.REDIS_PORT if self.is_redis_available else "N/A",
            "cached_keys_count": len(self._in_memory_store) if not self.is_redis_available else "Live in Redis"
        }

redis_service = RedisCacheService()

