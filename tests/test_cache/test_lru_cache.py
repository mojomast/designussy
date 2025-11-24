"""
Unit tests for cache system.

Tests LRU cache implementation, TTL expiration,
thread safety, and cache statistics.
"""

import pytest
import time
import threading
from unittest.mock import Mock

from utils.cache import get_cache
from PIL import Image


class TestLRUCache:
    """Test LRU cache functionality."""
    
    def test_cache_set_and_get(self, test_cache):
        """Test basic cache set and get operations."""
        test_img = Image.new("RGB", (100, 100), (255, 0, 0))
        
        # Set value
        test_cache.set("test_key", test_img)
        
        # Get value
        result = test_cache.get("test_key")
        
        assert result is not None
        assert result.size == (100, 100)
    
    def test_cache_miss(self, test_cache):
        """Test cache miss returns None."""
        result = test_cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_clear(self, test_cache):
        """Test cache clear functionality."""
        test_img = Image.new("RGB", (100, 100), (255, 0, 0))
        
        test_cache.set("test_key", test_img)
        assert test_cache.get("test_key") is not None
        
        test_cache.clear_all()
        assert test_cache.get("test_key") is None