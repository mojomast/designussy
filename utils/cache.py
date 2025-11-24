"""
NanoBanana In-Memory Cache Module

Implements a thread-safe LRU cache with TTL support for generated assets.
Provides cache statistics and metrics for monitoring performance.
"""

import threading
import time
import hashlib
import pickle
from collections import OrderedDict
from typing import Any, Optional, Dict, Tuple
from datetime import datetime


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.
    
    Implements Least Recently Used eviction policy with optional
    Time To Live for cached items.
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to store in cache
            default_ttl: Default time-to-live in seconds for cached items
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Tuple[Any, float, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0,
            'total_set': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Hexadecimal hash string representing the key
        """
        # Serialize arguments to create a unique key
        data = pickle.dumps((args, sorted(kwargs.items())))
        return hashlib.sha256(data).hexdigest()
    
    def _is_expired(self, timestamp: float, ttl: float) -> bool:
        """Check if a cached item has expired."""
        return time.time() > timestamp + ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            value, timestamp, ttl = self._cache[key]
            
            # Check if expired
            if self._is_expired(timestamp, ttl):
                del self._cache[key]
                self._stats['expired'] += 1
                self._stats['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store an item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        with self._lock:
            ttl = ttl or self.default_ttl
            timestamp = time.time()
            
            # Remove if exists (will be re-added at end)
            if key in self._cache:
                del self._cache[key]
            
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats['evictions'] += 1
            
            # Store with timestamp and TTL
            self._cache[key] = (value, timestamp, ttl)
            self._stats['total_set'] += 1
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                'size': len(self._cache),
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'hit_rate': (
                    stats['hits'] / (stats['hits'] + stats['misses'])
                    if (stats['hits'] + stats['misses']) > 0 else 0.0
                )
            })
            return stats
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information.
        
        Returns:
            Dictionary with cache configuration and current state
        """
        with self._lock:
            return {
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'current_size': len(self._cache),
                'stats': self.get_stats(),
                'keys': list(self._cache.keys())
            }


class GenerationalCache:
    """
    Multi-generational cache for different asset types.
    
    Manages separate LRU caches for different types of generated assets
    with individual TTL configurations.
    """
    
    def __init__(self):
        """Initialize generational cache with default configurations."""
        self._caches: Dict[str, LRUCache] = {}
        self._config = {
            'parchment': {'size': 50, 'ttl': 3600},
            'enso': {'size': 100, 'ttl': 3600},
            'sigil': {'size': 100, 'ttl': 3600},
            'giraffe': {'size': 100, 'ttl': 3600},
            'kangaroo': {'size': 100, 'ttl': 3600},
            'directed_enso': {'size': 200, 'ttl': 1800}  # Shorter TTL for directed
        }
        self._lock = threading.RLock()
    
    def _get_cache(self, asset_type: str) -> LRUCache:
        """
        Get or create cache for asset type.
        
        Args:
            asset_type: Type of asset (e.g., 'parchment', 'enso')
            
        Returns:
            LRUCache instance for the asset type
        """
        with self._lock:
            if asset_type not in self._caches:
                config = self._config.get(asset_type, {'size': 100, 'ttl': 3600})
                self._caches[asset_type] = LRUCache(
                    max_size=config['size'],
                    default_ttl=config['ttl']
                )
            return self._caches[asset_type]
    
    def get(self, asset_type: str, *args, **kwargs) -> Optional[Any]:
        """
        Retrieve asset from cache.
        
        Args:
            asset_type: Type of asset
            *args: Positional arguments for key generation
            **kwargs: Keyword arguments for key generation
            
        Returns:
            Cached asset if found, None otherwise
        """
        cache = self._get_cache(asset_type)
        key = cache._generate_key(*args, **kwargs)
        return cache.get(key)
    
    def set(self, asset_type: str, value: Any, *args, **kwargs) -> None:
        """
        Store asset in cache.
        
        Args:
            asset_type: Type of asset
            value: Asset to cache
            *args: Positional arguments for key generation
            **kwargs: Keyword arguments for key generation
        """
        cache = self._get_cache(asset_type)
        key = cache._generate_key(*args, **kwargs)
        
        # Get TTL from config
        ttl = self._config.get(asset_type, {}).get('ttl', 3600)
        cache.set(key, value, ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics from all caches.
        
        Returns:
            Dictionary with combined statistics
        """
        with self._lock:
            total_stats = {
                'total_hits': 0,
                'total_misses': 0,
                'total_evictions': 0,
                'total_expired': 0,
                'total_set': 0,
                'total_size': 0,
                'caches': {}
            }
            
            for asset_type, cache in self._caches.items():
                stats = cache.get_stats()
                total_stats['caches'][asset_type] = stats
                
                total_stats['total_hits'] += stats['hits']
                total_stats['total_misses'] += stats['misses']
                total_stats['total_evictions'] += stats['evictions']
                total_stats['total_expired'] += stats['expired']
                total_stats['total_set'] += stats['total_set']
                total_stats['total_size'] += stats['size']
            
            # Calculate overall hit rate
            total_accesses = total_stats['total_hits'] + total_stats['total_misses']
            total_stats['overall_hit_rate'] = (
                total_stats['total_hits'] / total_accesses
                if total_accesses > 0 else 0.0
            )
            
            return total_stats
    
    def clear_all(self) -> None:
        """Clear all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
    
    def configure(self, asset_type: str, size: int, ttl: int) -> None:
        """
        Configure cache for specific asset type.
        
        Args:
            asset_type: Type of asset
            size: Maximum cache size
            ttl: Time to live in seconds
        """
        with self._lock:
            self._config[asset_type] = {'size': size, 'ttl': ttl}
            
            # Recreate cache if it exists
            if asset_type in self._caches:
                self._caches[asset_type] = LRUCache(max_size=size, default_ttl=ttl)


# Global cache instance
_cache_instance: Optional[GenerationalCache] = None
_cache_lock = threading.Lock()


def get_cache() -> GenerationalCache:
    """
    Get or create global cache instance (singleton pattern).
    
    Returns:
        Global GenerationalCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = GenerationalCache()
    return _cache_instance


def cache_asset(asset_type: str):
    """
    Decorator to cache function results.
    
    Args:
        asset_type: Type of asset being cached
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Try to get from cache
            cached_result = cache.get(asset_type, *args, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # Generate and cache
            result = func(*args, **kwargs)
            cache.set(asset_type, result, *args, **kwargs)
            return result
        
        return wrapper
    return decorator