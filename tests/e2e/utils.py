"""E2E test utilities and helper functions."""

import time
from typing import Optional, Dict, Any
from playwright.async_api import Page, Response
import json


class TestUtils:
    """Common test utilities for E2E testing."""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def wait_for_network_idle(self, timeout: int = 3000):
        """Wait for network to be idle."""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
        except Exception:
            # Fallback to DOM content loaded
            await self.page.wait_for_load_state('domcontentloaded', timeout=1000)
    
    async def wait_for_element(self, selector: str, timeout: int = 5000):
        """Wait for element to appear."""
        return await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def wait_for_text(self, text: str, timeout: int = 5000):
        """Wait for text to appear on page."""
        await self.page.wait_for_function(f"document.body.textContent.includes('{text}')", timeout=timeout)
    
    async def wait_for_response(self, url_pattern: str, timeout: int = 10000):
        """Wait for a specific response."""
        return await self.page.wait_for_response(url_pattern, timeout=timeout)
    
    async def take_screenshot(self, name: str, full_page: bool = False):
        """Take a screenshot with descriptive name."""
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}.png"
        await self.page.screenshot(path=f"test-results/screenshots/{filename}", full_page=full_page)
        return filename
    
    async def check_console_errors(self) -> list:
        """Check for JavaScript console errors."""
        errors = []
        def handle_console(msg):
            if msg.type == 'error':
                errors.append(msg.text)
        
        self.page.on('console', handle_console)
        await self.page.reload()
        return errors
    
    async def clear_cookies(self):
        """Clear all cookies."""
        await self.page.context.clear_cookies()
    
    async def set_viewport(self, width: int, height: int):
        """Set viewport size."""
        await self.page.set_viewport_size({'width': width, 'height': height})
    
    async def simulate_slow_network(self, latency: int = 1000, download_speed: int = 50):
        """Simulate slow network conditions."""
        await self.page.route('**/*', lambda route: self._slow_route_handler(route, latency, download_speed))
    
    async def _slow_route_handler(self, route, latency: int, download_speed: int):
        """Handle routing with simulated slow network."""
        await route.fulfill(
            body=route.request.resource_type,
            headers={'content-type': 'text/html'},
            status=200
        )
        await asyncio.sleep(latency / 1000)


class APIHelper:
    """Helper for API interactions."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
    
    async def generate_asset(self, asset_type: str, **params) -> Dict[str, Any]:
        """Generate an asset via API."""
        url = f"{self.base_url}/generate/{asset_type}"
        if params:
            query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_params}"
        
        response = await self.page.goto(url)
        if response.status == 200:
            # Return image data or success status
            return {"status": "success", "url": url}
        else:
            return {"status": "error", "status_code": response.status, "url": url}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/cache/stats")
            return response.json()
    
    async def clear_cache(self) -> Dict[str, Any]:
        """Clear the cache."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/cache/clear")
            return response.json()
    
    async def create_batch_job(self, requests: list) -> Dict[str, Any]:
        """Create a batch generation job."""
        import httpx
        
        batch_data = {
            "requests": requests,
            "options": {
                "parallel": True,
                "priority": "normal"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate/batch",
                json=batch_data
            )
            return response.json()
    
    async def get_batch_status(self, job_id: str) -> Dict[str, Any]:
        """Get batch job status."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/generate/batch/{job_id}/status")
            return response.json()


class UIHelper:
    """Helper for UI interactions."""
    
    def __init__(self, page: Page):
        self.page = page
        self.test_utils = TestUtils(page)
    
    async def click_element(self, selector: str, timeout: int = 5000):
        """Click an element with proper waiting."""
        await self.test_utils.wait_for_element(selector, timeout)
        await self.page.click(selector)
    
    async def fill_input(self, selector: str, text: str):
        """Fill an input field."""
        await self.test_utils.wait_for_element(selector)
        await self.page.fill(selector, text)
    
    async def select_option(self, selector: str, value: str):
        """Select an option from dropdown."""
        await self.test_utils.wait_for_element(selector)
        await self.page.select_option(selector, value)
    
    async def hover_element(self, selector: str):
        """Hover over an element."""
        await self.test_utils.wait_for_element(selector)
        await self.page.hover(selector)
    
    async def drag_and_drop(self, source_selector: str, target_selector: str):
        """Perform drag and drop operation."""
        await self.test_utils.wait_for_element(source_selector)
        await self.test_utils.wait_for_element(target_selector)
        await self.page.drag_and_drop(source_selector, target_selector)
    
    async def check_element_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        try:
            await self.test_utils.wait_for_element(selector, timeout=2000)
            return True
        except Exception:
            return False
    
    async def get_element_text(self, selector: str) -> Optional[str]:
        """Get text content of an element."""
        try:
            await self.test_utils.wait_for_element(selector, timeout=3000)
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return None
        except Exception:
            return None
    
    async def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value from an element."""
        try:
            await self.test_utils.wait_for_element(selector, timeout=3000)
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
            return None
        except Exception:
            return None


class AssetGenerationHelper:
    """Helper for asset generation workflow testing."""
    
    def __init__(self, page: Page):
        self.page = page
        self.ui_helper = UIHelper(page)
        self.api_helper = APIHelper()
    
    async def navigate_to_generation_page(self, url: str = "http://localhost:8000"):
        """Navigate to the main generation page."""
        await self.page.goto(url)
        await self.test_utils.wait_for_network_idle()
    
    async def generate_parchment(self) -> Dict[str, Any]:
        """Generate a parchment texture."""
        return await self.api_helper.generate_asset('parchment')
    
    async def generate_enso(self) -> Dict[str, Any]:
        """Generate an enso circle."""
        return await self.api_helper.generate_asset('enso')
    
    async def generate_sigil(self) -> Dict[str, Any]:
        """Generate a sigil."""
        return await self.api_helper.generate_asset('sigil')
    
    async def generate_giraffe(self) -> Dict[str, Any]:
        """Generate a giraffe."""
        return await self.api_helper.generate_asset('giraffe')
    
    async def generate_kangaroo(self) -> Dict[str, Any]:
        """Generate a kangaroo."""
        return await self.api_helper.generate_asset('kangaroo')
    
    async def verify_image_displayed(self, container_selector: str = "img") -> bool:
        """Verify that an image is displayed."""
        try:
            img_element = await self.ui_helper.wait_for_element(container_selector)
            if img_element:
                # Check if image has loaded and has valid dimensions
                bounding_box = await img_element.bounding_box()
                if bounding_box and bounding_box['width'] > 0 and bounding_box['height'] > 0:
                    return True
            return False
        except Exception:
            return False


# Global utility instances
def create_test_utils(page: Page) -> TestUtils:
    """Create a TestUtils instance."""
    return TestUtils(page)


def create_api_helper(base_url: str = "http://localhost:8001") -> APIHelper:
    """Create an APIHelper instance."""
    return APIHelper(base_url)


def create_ui_helper(page: Page) -> UIHelper:
    """Create a UIHelper instance."""
    return UIHelper(page)


def create_asset_helper(page: Page) -> AssetGenerationHelper:
    """Create an AssetGenerationHelper instance."""
    return AssetGenerationHelper(page)