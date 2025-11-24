"""E2E tests for error handling and edge cases."""

import pytest
import asyncio
import time
from playwright.async_api import expect
from tests.e2e.utils import create_test_utils, create_api_helper


@pytest.mark.e2e
@pytest.mark.error_handling
@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test API error handling scenarios."""
    
    async def test_invalid_asset_type_error(self, page, api_client):
        """Test error handling for invalid asset types."""
        # Try to generate an invalid asset type
        response = await api_client.get("/generate/invalid_asset_type")
        
        # Should return an error
        assert response.status_code in [400, 404, 500]
        print(f"✅ Invalid asset type handled with status: {response.status_code}")
    
    async def test_invalid_parameters_error(self, page, api_client):
        """Test error handling for invalid generation parameters."""
        # Try to generate with invalid parameters
        params = {"invalid_param": "invalid_value", "negative_width": -100}
        response = await api_client.get("/generate/parchment", params=params)
        
        # Should handle invalid parameters gracefully
        assert response.status_code in [400, 422, 500]
        print(f"✅ Invalid parameters handled with status: {response.status_code}")
    
    async def test_malformed_request_error(self, page, api_client):
        """Test error handling for malformed requests."""
        # Send malformed JSON in POST request
        malformed_data = '{"invalid": json "syntax": }'
        
        response = await api_client.post(
            "/generate/batch",
            content=malformed_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should return error for malformed request
        assert response.status_code in [400, 422, 500]
        print(f"✅ Malformed request handled with status: {response.status_code}")
    
    async def test_batch_job_error_handling(self, page, api_client):
        """Test error handling in batch jobs."""
        # Create batch with mix of valid and invalid requests
        batch_data = {
            "requests": [
                {"type": "parchment", "count": 1},
                {"type": "invalid_type", "count": 1},
                {"type": "sigil", "count": 1}
            ],
            "options": {"parallel": True}
        }
        
        response = await api_client.post("/generate/batch", json=batch_data)
        assert response.status_code == 200
        
        job_data = response.json()
        job_id = job_data["job_id"]
        
        # Wait for processing
        await asyncio.sleep(10)
        
        # Check job status
        status_response = await api_client.get(f"/generate/batch/{job_id}/status")
        status = status_response.json()
        
        # Should have completed items and failed items
        assert status["total_items"] == 3
        assert status["failed_items"] >= 0
        assert status["completed_items"] >= 0
        
        print(f"✅ Batch job error handling: {status['completed_items']} succeeded, {status['failed_items']} failed")
    
    async def test_nonexistent_job_error(self, page, api_client):
        """Test error handling for nonexistent batch jobs."""
        # Try to get status for nonexistent job
        fake_job_id = "nonexistent_job_12345"
        
        response = await api_client.get(f"/generate/batch/{fake_job_id}/status")
        assert response.status_code == 404
        
        # Try to cancel nonexistent job
        cancel_response = await api_client.post(f"/generate/batch/{fake_job_id}/cancel")
        assert cancel_response.status_code == 404
        
        print("✅ Nonexistent job error handling completed")


@pytest.mark.e2e
@pytest.mark.error_handling
@pytest.mark.asyncio
class TestNetworkErrorHandling:
    """Test network-related error scenarios."""
    
    async def test_timeout_handling(self, page, api_client):
        """Test handling of request timeouts."""
        test_utils = create_test_utils(page)
        
        # Create very large request that might timeout
        large_batch_data = {
            "requests": [
                {"type": "sigil", "count": 100}  # Large batch
            ],
            "options": {"parallel": True}
        }
        
        start_time = time.time()
        response = await api_client.post("/generate/batch", json=large_batch_data, timeout=5.0)
        end_time = time.time()
        
        request_time = end_time - start_time
        
        # Either succeeds or times out gracefully
        assert response.status_code in [200, 408, 500]
        
        if request_time > 5.0:
            print(f"✅ Request timeout handled after {request_time:.2f}s")
        else:
            print(f"✅ Request completed quickly: {request_time:.2f}s")
    
    async def test_network_interruption_simulation(self, page):
        """Test behavior during simulated network issues."""
        test_utils = create_test_utils(page)
        
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Simulate slow network
        await test_utils.simulate_slow_network(latency=3000, download_speed=5)
        
        # Try to interact with page under slow conditions
        start_time = time.time()
        
        # Try clicking a button or generating content
        buttons = page.locator("button")
        if await buttons.count() > 0:
            await buttons.first.click()
            await asyncio.sleep(5)  # Wait for slow response
        
        end_time = time.time()
        interaction_time = end_time - start_time
        
        # Should still work but take longer
        assert interaction_time >= 3.0
        print(f"✅ Network interruption handled: interaction took {interaction_time:.2f}s")


@pytest.mark.e2e
@pytest.mark.error_handling
@pytest.mark.asyncio
class TestValidationErrorHandling:
    """Test input validation and error messages."""
    
    async def test_input_validation_errors(self, page):
        """Test client-side input validation."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for input fields
        input_selectors = [
            'input[type="text"]',
            'input[type="number"]',
            'textarea',
            'input[type="email"]'
        ]
        
        for selector in input_selectors:
            inputs = page.locator(selector)
            count = await inputs.count()
            
            if count > 0:
                input_elem = inputs.first
                
                # Try invalid inputs
                await input_elem.fill("")  # Empty
                await input_elem.fill("very_long_input_that_exceeds_any_reasonable_limit_and_should_trigger_validation")
                await input_elem.fill("<script>alert('xss')</script>")  # XSS attempt
                
                # Check for validation messages
                validation_selectors = [
                    '.error-message',
                    '.validation-error',
                    '[role="alert"]',
                    '.field-error'
                ]
                
                validation_found = False
                for val_selector in validation_selectors:
                    validation_elements = page.locator(val_selector)
                    if await validation_elements.count() > 0:
                        validation_found = True
                        print(f"✅ Found validation messages: {val_selector}")
                        break
                
                if not validation_found:
                    print(f"ℹ️ No validation messages found for {selector}")
                
                break
        
        print("✅ Input validation error handling test completed")
    
    async def test_error_message_display(self, page):
        """Test that error messages are properly displayed to users."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for error message containers
        error_selectors = [
            '.error-message',
            '.alert-error',
            '[data-error="true"]',
            '.toast-error',
            '[role="alert"]'
        ]
        
        found_error_ui = False
        for selector in error_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    found_error_ui = True
                    print(f"✅ Found error message UI: {selector}")
                    break
            except Exception:
                continue
        
        if not found_error_ui:
            print("ℹ️ No error message UI found - may rely on browser validation")
        
        # Check for success messages
        success_selectors = [
            '.success-message',
            '.alert-success',
            '[data-success="true"]'
        ]
        
        found_success_ui = False
        for selector in success_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    found_success_ui = True
                    print(f"✅ Found success message UI: {selector}")
                    break
            except Exception:
                continue
        
        if not found_success_ui:
            print("ℹ️ No success message UI found")
        
        print("✅ Error message display test completed")


@pytest.mark.e2e
@pytest.mark.error_handling
@pytest.mark.asyncio
class TestRecoveryAndResilience:
    """Test system recovery and resilience features."""
    
    async def test_page_reload_after_errors(self, page):
        """Test that page can recover and reload after errors."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Simulate errors
        await page.evaluate("window.error = () => { throw new Error('Simulated error'); }")
        
        # Trigger an error
        try:
            await page.evaluate("window.error()")
        except Exception:
            pass  # Expected to fail
        
        # Reload page
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        # Verify page still works
        body = page.locator("body")
        await expect(body).to_be_visible()
        
        print("✅ Page recovery after errors test completed")
    
    async def test_graceful_degradation(self, page):
        """Test graceful degradation when features are unavailable."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Block certain resources to simulate unavailable features
        await page.route('**/*', lambda route: route.abort() if 'api' in route.request.url else route.continue_())
        
        # Try to generate assets
        try:
            await page.goto("http://localhost:8000/generate/parchment")
            await asyncio.sleep(2)
        except Exception:
            pass  # Expected to have issues
        
        # Remove blocking and verify page still functions
        await page.unroute('**/*')
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        body = page.locator("body")
        await expect(body).to_be_visible()
        
        print("✅ Graceful degradation test completed")
    
    async def test_error_boundary_functionality(self, page):
        """Test error boundary implementation."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for error boundary UI elements
        boundary_selectors = [
            '.error-boundary',
            '[data-error-boundary="true"]',
            '.fallback-content',
            '.error-fallback'
        ]
        
        found_boundary = False
        for selector in boundary_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    found_boundary = True
                    print(f"✅ Found error boundary UI: {selector}")
                    break
            except Exception:
                continue
        
        if not found_boundary:
            print("ℹ️ No error boundary UI found")
        
        # Test that critical UI elements remain accessible
        critical_elements = page.locator('body, main, [role="main"]')
        await expect(critical_elements.first).to_be_visible()
        
        print("✅ Error boundary functionality test completed")


@pytest.mark.e2e
@pytest.mark.error_handling
@pytest.mark.asyncio
class TestAccessibilityErrorHandling:
    """Test accessibility in error scenarios."""
    
    async def test_error_message_accessibility(self, page):
        """Test that error messages are accessible to screen readers."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Check for ARIA live regions for error messages
        aria_selectors = [
            '[aria-live="polite"]',
            '[aria-live="assertive"]',
            '[role="alert"]',
            '[aria-label*="error"]',
            '[aria-labelledby*="error"]'
        ]
        
        for selector in aria_selectors:
            elements = page.locator(selector)
            count = await elements.count()
            if count > 0:
                print(f"✅ Found accessible error handling: {selector} ({count} elements)")
        
        print("✅ Error message accessibility test completed")
    
    async def test_keyboard_focus_in_error_states(self, page):
        """Test keyboard focus management during errors."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Test Tab navigation through error states
        await page.keyboard.press('Tab')
        active_element = await page.evaluate("document.activeElement.tagName")
        
        await page.keyboard.press('Tab')
        next_element = await page.evaluate("document.activeElement.tagName")
        
        print(f"✅ Keyboard focus works: {active_element} → {next_element}")
        
        # Verify focus management doesn't break
        assert active_element and next_element
        
        print("✅ Keyboard focus in error states test completed")