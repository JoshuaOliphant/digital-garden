"""
Caching utilities for the digital garden application.
Extracted from main.py to improve modularity.
"""

import time
from typing import Dict, Any, TypeVar, Callable, Awaitable
from functools import wraps

T = TypeVar("T")


class timed_lru_cache:
    """Decorator that adds time-based expiration to an in-memory LRU cache.

    The cache uses regular Python dictionaries and is **not** thread safe.
    It is intended for single-threaded use such as development servers or
    scripts. Use an external cache if you need multi-process or multi-threaded
    safety.
    """

    def __init__(self, maxsize: int = 128, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.last_refresh: Dict[str, float] = {}

    def __call__(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:

        @wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> T:
            key = str((args, sorted(kwargs.items())))

            # Check if cache needs refresh
            now = time.time()
            if (
                key not in self.cache
                or now - self.last_refresh.get(key, 0) > self.ttl_seconds
            ):
                self.cache[key] = await func(*args, **kwargs)
                self.last_refresh[key] = now

                # LRU eviction if cache is full
                if len(self.cache) > self.maxsize:
                    # Remove oldest entry
                    oldest_key = min(self.last_refresh, key=self.last_refresh.get)
                    del self.cache[oldest_key]
                    del self.last_refresh[oldest_key]

            return self.cache[key]

        return wrapped