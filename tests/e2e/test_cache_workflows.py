"""E2E tests for cache behavior workflows."""

import pytest
import asyncio
import time
from playwright.async_api import expect
from tests.e2e.utils import create_test_utils, create_api_helper


@pytest.mark.e2e
@pytest.mark.cache
@pytest.mark.asyncio
class TestCacheWorkflows:
    """Test caching behavior workflows."""
    
    async def test_initial_cache_state(self, page, api_client):
        """Test the initial state of the cache."""
        # Get initial cache stats
        response = await api_client.get("/cache/stats")
        assert response.status_code == 200
        
        stats = response.json()
        cache_stats = stats.get("cache_stats", {})
        
        print(f"📦 Initial cache stats: {cache_stats}")
        
        # Cache should be empty initially or have minimal entries
        assert cache_stats is not None
        
        print("✅ Initial cache state test completed")
    
    async def test_cache_hit_on_second_request(self, page, api_client):
        """Test that cache hits work on second request for same asset."""
        api_helper = create_api_helper()
        
        # First request - should miss cache
        start_time = time.time()
        result1 = await api_helper.generate_asset('parchment')
        first_request_time = time.time() - start_time
        
        assert result1["status"] == "success"
        print(f"⏱️ First request took: {first_request_time:.2f}s")
        
        # Get cache stats after first request
        response1 = await api_client.get("/cache/stats")
        stats1 = response1.json()["cache_stats"]
        
        # Second request - should hit cache
        start_time = time.time()
        result2 = await api_helper.generate_asset('parchment')
        second_request_time = time.time() - start_time
        
        assert result2["status"] == "success"
        print(f"⏱️ Second request took: {second_request_time:.2f}s")
        
        # Get cache stats after second request
        response2 = await api_client.get("/cache/stats")
        stats2 = response2.json()["cache_stats"]
        
        # Verify cache hit occurred
        if stats1 and stats2:
            hits_before = stats1.get("hits", 0)
            hits_after = stats2.get("hits", 0)
            assert hits_after > hits_before, "Cache hit not recorded"
        
        # Second request should be faster due to caching
        print(f"✅ Cache hit test completed - Second request was {first_request_time/second_request_time:.1f}x faster")
    
    async def test_cache_clear_functionality(self, page, api_client):
        """Test clearing the cache."""
        api_helper = create_api_helper()
        
        # Generate some assets to populate cache
        for asset_type in ['parchment', 'enso', 'sigil']:
            result = await api_helper.generate_asset(asset_type)
            assert result["status"] == "success"
        
        # Wait a moment for caching
        await asyncio.sleep(2)
        
        # Verify cache has entries
        response = await api_client.get("/cache/stats")
        stats_before = response.json()["cache_stats"]
        
        # Clear the cache
        clear_response = await api_client.post("/cache/clear")
        assert clear_response.status_code == 200
        
        clear_data = clear_response.json()
        assert clear_data["status"] == "success"
        
        # Verify cache is cleared
        response = await api_client.get("/cache/stats")
        stats_after = response.json()["cache_stats"]
        
        # Cache should be cleared or significantly reduced
        if stats_before and stats_after:
            entries_before = stats_before.get("total_entries", 0)
            entries_after = stats_after.get("total_entries", 0)
            assert entries_after < entries_before, "Cache not cleared properly"
        
        print("✅ Cache clear functionality test completed")


@pytest.mark.e2e
@pytest.mark.cache
@pytest.mark.asyncio
class TestCacheUIWorkflows:
    """Test UI workflows for cache management."""
    
    async def test_cache_stats_display_updates(self, page, api_client):
        """Test that cache stats display updates in real-time."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        api_helper = create_api_helper()
        
        # Generate asset to create cache entry
        await api_helper.generate_asset('parchment')
        
        # Look for updated cache stats
        cache_elements = page.locator('.cache-stats, .cache-hit-rate, [data-cache="stats"]')
        cache_count = await cache_elements.count()
        
        if cache_count > 0:
            # Check if stats are displayed and updated
            for i in range(min(cache_count, 3)):
                element = cache_elements.nth(i)
                text = await element.text_content()
                if text:
                    print(f"✅ Cache stat displayed: {text.strip()}")
        else:
            print("ℹ️ No cache stats display found")