"""Simple in-memory cache for search results."""

import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    """Cached search result."""

    result: Any
    created_at: float
    hits: int = 0


class SearchCache:
    """LRU-style cache for search results."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _make_key(self, query: str, path: str, **kwargs) -> str:
        """Generate cache key from search parameters."""
        key_data = f"{query}:{path}:{sorted(kwargs.items())}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    async def get(self, query: str, path: str, **kwargs) -> Any | None:
        """Get cached result if exists and not expired."""
        key = self._make_key(query, path, **kwargs)

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check TTL
            if time.time() - entry.created_at > self.ttl_seconds:
                del self._cache[key]
                return None

            entry.hits += 1
            return entry.result

    async def set(self, query: str, path: str, result: Any, **kwargs) -> None:
        """Cache search result."""
        key = self._make_key(query, path, **kwargs)

        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[key] = CacheEntry(
                result=result,
                created_at=time.time(),
            )

    def _evict_oldest(self) -> None:
        """Remove oldest entry."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at,
        )
        del self._cache[oldest_key]

    async def clear(self) -> None:
        """Clear all cached entries."""
        async with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "entries": len(self._cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
        }
