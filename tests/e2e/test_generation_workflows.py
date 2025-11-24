"""E2E tests for asset generation workflows."""

import pytest
import asyncio
from playwright.async_api import expect
from tests.e2e.utils import create_test_utils, create_api_helper, create_ui_helper


@pytest.mark.e2e
@pytest.mark.generation
@pytest.mark.asyncio
class TestGenerationWorkflows:
    """Test complete asset generation workflows."""
    
    async def test_navigate_to_generation_page(self, page):
        """Test navigation to the main generation page."""
        test_utils = create_test_utils(page)
        
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Verify page loaded correctly
        await expect(page).to_have_title("NanoBanana Generator")
        
        # Check if main content is visible
        main_content = page.locator("body")
        await expect(main_content).to_be_visible()
        
        print("✅ Successfully navigated to generation page")
    
    async def test_generate_parchment_texture(self, page):
        """Test generating a parchment texture."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Generate parchment via API
        result = await api_helper.generate_asset('parchment')
        
        # Verify generation was successful
        assert result["status"] == "success"
        
        # Navigate to generation page and verify UI shows generated image
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Look for generation buttons or interface
        parchment_button = page.locator('button:has-text("Parchment"), [data-asset-type="parchment"]')
        if await parchment_button.is_visible():
            await parchment_button.click()
            await asyncio.sleep(2)  # Wait for generation
            
            # Check if image is displayed
            img_elements = page.locator("img")
            if await img_elements.count() > 0:
                # Verify image has loaded
                first_img = img_elements.first
                await expect(first_img).to_be_visible()
                await expect(first_img).to_have_attribute("src")
        
        print("✅ Parchment generation test completed")
    
    async def test_generate_enso_circle(self, page):
        """Test generating an enso circle."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Generate enso via API
        result = await api_helper.generate_asset('enso')
        
        # Verify generation was successful
        assert result["status"] == "success"
        
        # Test directed enso if LLM is available
        try:
            from llm_director import get_enso_params_from_prompt
            directed_result = await api_helper.generate_asset(
                'directed_enso', 
                prompt="Mystical energy with golden glow"
            )
            print("✅ Directed enso generation also works")
        except ImportError:
            print("ℹ️ LLM Director not available, skipping directed enso test")
        
        print("✅ Enso generation test completed")
    
    async def test_generate_sigil(self, page):
        """Test generating a sigil."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Generate sigil via API
        result = await api_helper.generate_asset('sigil')
        
        # Verify generation was successful
        assert result["status"] == "success"
        
        # Navigate to generation page and verify UI interaction
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Look for sigil generation interface
        sigil_button = page.locator('button:has-text("Sigil"), [data-asset-type="sigil"]')
        if await sigil_button.is_visible():
            await sigil_button.click()
            await asyncio.sleep(2)
            
            # Check if image is displayed
            img_elements = page.locator("img")
            if await img_elements.count() > 0:
                first_img = img_elements.first
                await expect(first_img).to_be_visible()
        
        print("✅ Sigil generation test completed")
    
    async def test_generate_creatures(self, page):
        """Test generating creature assets (giraffe, kangaroo)."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Test giraffe generation
        giraffe_result = await api_helper.generate_asset('giraffe')
        assert giraffe_result["status"] == "success"
        
        # Test kangaroo generation
        kangaroo_result = await api_helper.generate_asset('kangaroo')
        assert kangaroo_result["status"] == "success"
        
        print("✅ Creature generation test completed")
    
    async def test_asset_generation_with_parameters(self, page):
        """Test generating assets with custom parameters."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Test generation with different sizes
        test_cases = [
            {"width": 512, "height": 512},
            {"width": 256, "height": 256},
            {"width": 1024, "height": 768},
        ]
        
        for params in test_cases:
            result = await api_helper.generate_asset('parchment', **params)
            assert result["status"] == "success"
            
            # Verify the response is a valid image
            assert "image" in result.get("headers", {}).get("content-type", "").lower()
        
        print("✅ Parameterized asset generation test completed")
    
    async def test_multiple_asset_generation_sequence(self, page):
        """Test generating multiple assets in sequence."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        asset_types = ['parchment', 'enso', 'sigil', 'giraffe', 'kangaroo']
        results = []
        
        for asset_type in asset_types:
            result = await api_helper.generate_asset(asset_type)
            results.append(result)
            
            # Verify each generation was successful
            assert result["status"] == "success"
            print(f"✅ Generated {asset_type}")
        
        # Verify we got successful results for all asset types
        success_count = sum(1 for r in results if r["status"] == "success")
        assert success_count == len(asset_types)
        
        print("✅ Multiple asset generation sequence test completed")
    
    async def test_generation_performance(self, page):
        """Test generation performance and timing."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        import time
        
        # Test generation speed
        start_time = time.time()
        result = await api_helper.generate_asset('parchment')
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Verify generation was successful
        assert result["status"] == "success"
        
        # Log performance metrics
        print(f"⚡ Generation took {generation_time:.2f} seconds")
        
        # Generation should complete within reasonable time (10 seconds max)
        assert generation_time < 10.0, f"Generation took too long: {generation_time:.2f}s"
        
        print("✅ Generation performance test completed")
    
    async def test_error_handling_for_invalid_asset_type(self, page):
        """Test error handling for invalid asset types."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Try to generate an invalid asset type
        result = await api_helper.generate_asset('invalid_asset_type')
        
        # Should fail gracefully
        assert result["status"] == "error"
        assert "error" in result
        
        print("✅ Error handling for invalid asset type test completed")
    
    async def test_image_display_verification(self, page):
        """Test that generated images are properly displayed in UI."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Generate an asset
        result = await api_helper.generate_asset('enso')
        assert result["status"] == "success"
        
        # Navigate to page with image display
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Check for image elements
        img_elements = page.locator("img")
        image_count = await img_elements.count()
        
        if image_count > 0:
            # Verify images have valid source URLs
            for i in range(min(image_count, 3)):  # Check first 3 images
                img = img_elements.nth(i)
                src = await img.get_attribute("src")
                if src:
                    assert src.startswith(("http", "data:image")), f"Invalid image source: {src}"
                    print(f"✅ Image {i+1} has valid source: {src[:50]}...")
        
        print("✅ Image display verification test completed")


@pytest.mark.e2e
@pytest.mark.generation
@pytest.mark.slow
@pytest.mark.asyncio
class TestAdvancedGenerationWorkflows:
    """Test advanced generation workflows and edge cases."""
    
    async def test_concurrent_generation_requests(self, page):
        """Test multiple concurrent generation requests."""
        import asyncio
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = api_helper.generate_asset('sigil', seed=f"test_seed_{i}")
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all requests completed successfully
        success_count = 0
        for result in results:
            if isinstance(result, dict) and result.get("status") == "success":
                success_count += 1
        
        assert success_count >= 4, f"Expected at least 4 successful requests, got {success_count}"
        
        print("✅ Concurrent generation requests test completed")
    
    async def test_generation_with_network_interruption(self, page):
        """Test generation behavior with simulated network issues."""
        test_utils = create_test_utils(page)
        api_helper = create_api_helper()
        
        # Simulate slow network
        await test_utils.simulate_slow_network(latency=2000, download_speed=10)
        
        # Try generation with slow network
        start_time = asyncio.get_event_loop().time()
        result = await api_helper.generate_asset('parchment')
        end_time = asyncio.get_event_loop().time()
        
        # Should still succeed but take longer
        assert result["status"] == "success"
        
        duration = end_time - start_time
        assert duration >= 2.0, "Generation should take longer with slow network"
        
        print(f"✅ Generation with network interruption test completed ({duration:.2f}s)")


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.generation
@pytest.mark.asyncio
class TestUIGenerationInterface:
    """Test the UI interface for asset generation."""
    
    async def test_generation_interface_responsiveness(self, page):
        """Test that the generation interface is responsive."""
        test_utils = create_test_utils(page)
        ui_helper = create_ui_helper(page)
        
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Test different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 768, "height": 1024},   # Tablet
            {"width": 375, "height": 667},    # Mobile
        ]
        
        for viewport in viewports:
            await test_utils.set_viewport(viewport["width"], viewport["height"])
            
            # Check if main interface elements are visible
            body = page.locator("body")
            await expect(body).to_be_visible()
            
            # Check if any generation buttons or controls are visible
            buttons = page.locator("button")
            if await buttons.count() > 0:
                await expect(buttons.first).to_be_visible()
            
            print(f"✅ Interface responsive at {viewport['width']}x{viewport['height']}")
    
    async def test_generation_interface_accessibility(self, page):
        """Test basic accessibility of generation interface."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Check for proper heading structure
        headings = page.locator("h1, h2, h3, h4, h5, h6")
        heading_count = await headings.count()
        
        if heading_count > 0:
            # Verify at least one heading exists
            first_heading = headings.first
            await expect(first_heading).to_be_visible()
            print(f"✅ Found {heading_count} headings in page")
        
        # Check for form labels
        labels = page.locator("label")
        label_count = await labels.count()
        print(f"✅ Found {label_count} form labels")
        
        # Check for alt text on images
        images = page.locator("img")
        img_count = await images.count()
        
        if img_count > 0:
            for i in range(min(img_count, 3)):
                img = images.nth(i)
                alt = await img.get_attribute("alt")
                if alt:
                    print(f"✅ Image {i+1} has alt text: '{alt}'")
                else:
                    print(f"⚠️ Image {i+1} missing alt text")
        
        print("✅ Basic accessibility test completed")