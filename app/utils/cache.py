"""Cache utilities for the application."""

import time
from functools import lru_cache, wraps
from typing import Any, Callable, Optional


class timed_lru_cache:
    """LRU cache decorator with time-based expiration."""
    
    def __init__(self, seconds: int = 300, maxsize: int = 128):
        self.seconds = seconds
        self.maxsize = maxsize
    
    def __call__(self, func: Callable) -> Callable:
        # Apply LRU cache
        cached_func = lru_cache(maxsize=self.maxsize)(func)
        cached_func.expiration = time.time() + self.seconds
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if cache has expired
            if time.time() >= cached_func.expiration:
                cached_func.cache_clear()
                cached_func.expiration = time.time() + self.seconds
            return cached_func(*args, **kwargs)
        
        # Expose cache_clear method
        wrapper.cache_clear = cached_func.cache_clear
        wrapper.cache_info = cached_func.cache_info
        
        return wrapper


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)