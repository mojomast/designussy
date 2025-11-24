"""Playwright fixtures and configuration for E2E tests."""

import asyncio
import os
from pathlib import Path
import pytest
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Generator
import json


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def playwright_instance():
    """Create a Playwright instance."""
    async with async_playwright() as p:
        yield p


@pytest.fixture(scope="session")
async def browser(playwright_instance) -> Browser:
    """Create a browser instance."""
    browser = await playwright_instance.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
        ]
    )
    yield browser
    await browser.close()


@pytest.fixture
async def context(browser) -> BrowserContext:
    """Create a browser context."""
    context = await browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    # Add common headers
    await context.set_extra_http_headers({
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    })
    
    yield context
    await context.close()


@pytest.fixture
async def page(context) -> Page:
    """Create a new page in the context."""
    page = await context.new_page()
    
    # Add request/response tracking for debugging
    page.on('response', lambda response: print(f"📡 {response.status} {response.url}"))
    page.on('request', lambda request: print(f"📤 {request.method} {request.url}"))
    
    yield page
    await page.close()


@pytest.fixture
async def authenticated_page(page, request) -> Page:
    """Create an authenticated page with common setup."""
    base_url = request.config.getoption('--base-url', 'http://localhost:8000')
    await page.goto(base_url)
    
    # Set common test data
    await page.add_init_script("""
        // Add common test utilities
        window.testUtils = {
            waitForNetworkIdle: async () => {
                await page.waitForLoadState('networkidle');
            },
            screenshot: async (name) => {
                await page.screenshot({ path: `test-results/screenshots/${name}.png` });
            }
        };
    """)
    
    yield page


@pytest.fixture
async def api_client():
    """Create an API client for backend testing."""
    import httpx
    
    base_url = os.getenv('TEST_API_URL', 'http://localhost:8001')
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Wait for API to be ready
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = await client.get('/health')
                if response.status_code == 200:
                    break
            except httpx.RequestError:
                pass
            await asyncio.sleep(1)
        else:
            raise Exception("API server not ready")
        
        yield client


@pytest.fixture
def test_data_dir():
    """Provide a directory for test data."""
    test_dir = Path(__file__).parent.parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def screenshots_dir():
    """Provide a directory for test screenshots."""
    screenshots_dir = Path(__file__).parent.parent.parent / "test-results" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    return screenshots_dir


@pytest.fixture
def videos_dir():
    """Provide a directory for test videos."""
    videos_dir = Path(__file__).parent.parent.parent / "test-results" / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    return videos_dir


# Custom markers configuration
pytest_plugins = ["pytest_playwright"]


def pytest_configure(config):
    """Configure pytest for E2E tests."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI interaction test"
    )
    config.addinivalue_line(
        "markers", "generation: mark test as asset generation workflow test"
    )
    config.addinivalue_line(
        "markers", "batch: mark test as batch processing workflow test"
    )
    config.addinivalue_line(
        "markers", "cache: mark test as cache behavior test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running test"
    )
    config.addinivalue_line(
        "markers", "skip_ci: mark test to skip in CI environment"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers."""
    if config.getoption("--run-slow"):
        # --run-slow given in cli: do not skip slow tests
        return
    
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--base-url", default="http://localhost:8000", help="base URL for the application"
    )
    parser.addoption(
        "--api-url", default="http://localhost:8001", help="API URL for testing"
    )