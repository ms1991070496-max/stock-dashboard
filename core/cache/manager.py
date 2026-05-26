"""TTL-based caching layer. Phase 1 uses diskcache; Phase 2 swaps to Redis."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

import diskcache

from core.config import settings

logger = logging.getLogger(__name__)

settings.cache_dir.mkdir(parents=True, exist_ok=True)
_cache = diskcache.Cache(str(settings.cache_dir))


class CacheManager:
    def __init__(self, cache: diskcache.Cache | None = None):
        self._cache = cache or _cache

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        expires_at = entry.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            return None
        return entry.get("value")

    def set(self, key: str, value: Any, ttl: int = 900) -> None:
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache.set(key, {"value": value, "expires_at": expires_at})

    def get_or_fetch(self, key: str, ttl: int, fetch_fn: Callable) -> Any:
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache HIT: {key}")
            return cached
        logger.debug(f"Cache MISS: {key}, fetching...")
        try:
            value = fetch_fn()
            self.set(key, value, ttl)
            return value
        except Exception:
            stale = self._cache.get(key)
            if stale:
                logger.warning(f"Fetch failed, serving stale cache: {key}")
                return stale.get("value")
            raise

    def invalidate(self, key: str) -> None:
        self._cache.delete(key)

    def clear_pattern(self, pattern: str) -> int:
        count = 0
        for key in list(self._cache):
            if pattern in str(key):
                self._cache.delete(key)
                count += 1
        return count


_cache_manager: CacheManager | None = None


def get_cache() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
