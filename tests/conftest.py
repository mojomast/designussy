"""
Pytest configuration and shared fixtures for NanoBanana Generator tests.

This module provides reusable test fixtures for generator, API, cache, and batch testing.
"""

import asyncio
import io
import os
import tempfile
import threading
import time
from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest
import numpy as np
from PIL import Image

# Optional imports that might not be available
try:
    from fastapi.testclient import TestClient
    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False

try:
    from httpx import AsyncClient
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import responses
    HAS_RESPONSES = True
except ImportError:
    HAS_RESPONSES = False

# Import project components
import backend
from generators import default_factory
from generators.base_generator import BaseGenerator
from utils.cache import get_cache
from utils.batch_job import get_job_manager, BatchRequest, GenerationRequest


# ===== Test Configuration Fixtures =====

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "test_image_size": (256, 256),
        "test_seed": 42,
        "test_timeout": 10,
        "max_generation_time": 2.0,
        "mock_llm_api": True,
    }


# ===== Generator Fixtures =====

@pytest.fixture
def test_image():
    """Create a small test image."""
    img = Image.new("RGBA", (64, 64), (255, 0, 0, 128))
    return img


@pytest.fixture
def sample_generator():
    """Create a test generator instance."""
    return default_factory.create_generator("sigil", width=256, height=256)


@pytest.fixture(params=["sigil", "enso", "parchment", "giraffe", "kangaroo"])
def generator_type(request):
    """Parameterized fixture for all generator types."""
    return request.param


@pytest.fixture
def all_generators():
    """Fixture providing all available generator instances."""
    generators = {}
    from generators import list_generators
    for gen_type in list_generators():
        try:
            generators[gen_type] = default_factory.create_generator(
                gen_type, width=256, height=256
            )
        except Exception as e:
            pytest.skip(f"Could not create generator {gen_type}: {e}")
    return generators


# ===== Cache Fixtures =====

@pytest.fixture
def test_cache():
    """Create a clean cache for testing."""
    cache = get_cache()
    cache.clear_all()
    yield cache
    # Clean up after test
    cache.clear_all()


@pytest.fixture
def populated_cache(test_cache, sample_generator):
    """Create a cache with some test data."""
    # Generate and cache some test assets
    for i in range(5):
        asset = sample_generator.generate()
        test_cache.set(f"test_asset_{i}", asset)
    return test_cache


# ===== API Testing Fixtures =====

@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    if not HAS_TEST_CLIENT:
        pytest.skip("FastAPI TestClient not available")
    
    # Set test environment
    os.environ["TESTING"] = "1"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
    
    # Create test client
    with TestClient(backend.app) as client:
        yield client
    
    # Clean up environment
    os.environ.pop("TESTING", None)


@pytest.fixture
async def async_test_client():
    """Create an async HTTP test client."""
    if not HAS_HTTPX:
        pytest.skip("httpx not available")
    
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_llm_response():
    """Mock LLM API response for testing."""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"color": "#FF5733", "complexity": 3, "chaos": 0.7}'
                }
            }
        ]
    }


# ===== Batch Job Fixtures =====

@pytest.fixture
def test_batch_request():
    """Create a test batch request."""
    requests = [
        GenerationRequest(type="sigil", count=2, parameters={}),
        GenerationRequest(type="enso", count=1, parameters={}),
    ]
    return BatchRequest(requests=requests)


@pytest.fixture
def job_manager():
    """Get the job manager instance."""
    manager = get_job_manager()
    yield manager
    # Clean up any test jobs
    for job in manager.get_all_jobs():
        if hasattr(job, 'job_id') and job.job_id.startswith('test_'):
            manager.cancel_job(job.job_id)


# ===== Image Comparison Utilities =====

def assert_images_similar(img1: Image.Image, img2: Image.Image, tolerance: float = 0.1):
    """Assert two images are similar within tolerance."""
    assert img1.size == img2.size, f"Image sizes differ: {img1.size} vs {img2.size}"
    assert img1.mode == img2.mode, f"Image modes differ: {img1.mode} vs {img2.mode}"
    
    # Convert to numpy arrays for comparison
    arr1 = np.array(img1).astype(float)
    arr2 = np.array(img2).astype(float)
    
    # Calculate mean absolute difference
    diff = np.abs(arr1 - arr2).mean()
    max_diff = arr1.size * 255  # Maximum possible difference
    
    relative_diff = diff / max_diff
    assert relative_diff <= tolerance, f"Images differ by {relative_diff:.3f} > {tolerance}"


def assert_image_has_content(img: Image.Image, min_pixels: int = 100):
    """Assert image has meaningful content (not solid color)."""
    arr = np.array(img)
    
    # Check if image has variation (not solid color)
    unique_colors = len(np.unique(arr.reshape(-1, arr.shape[-1]), axis=0))
    assert unique_colors > min_pixels, f"Image has insufficient variation: {unique_colors} unique colors"


# ===== Performance Testing Helpers =====

@pytest.fixture
def performance_monitor():
    """Monitor performance during tests."""
    start_time = time.time()
    start_memory = get_memory_usage()
    
    yield {
        "start_time": start_time,
        "start_memory": start_memory,
        "check": lambda: {
            "elapsed": time.time() - start_time,
            "memory_delta": get_memory_usage() - start_memory,
        }
    }
    
    # Check performance after test
    elapsed = time.time() - start_time
    memory_delta = get_memory_usage() - start_memory
    
    # Warn if test took too long (but don't fail)
    if elapsed > 5.0:
        pytest.warn(f"Test took {elapsed:.2f}s (longer than expected)")


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


# ===== Mocking Fixtures =====

@pytest.fixture
def mock_requests():
    """Mock HTTP requests for testing."""
    if not HAS_RESPONSES:
        pytest.skip("responses library not available")
    
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_generator():
    """Create a mock generator for testing."""
    mock = Mock(spec=BaseGenerator)
    mock.generate.return_value = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
    mock.get_generator_type.return_value = "mock"
    return mock


# ===== Temporary File Fixtures =====

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def temp_file():
    """Create a temporary file for tests."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        yield tmp_file.name
    # Clean up
    try:
        os.unlink(tmp_file.name)
    except FileNotFoundError:
        pass


# ===== Async Testing Helpers =====

@pytest.fixture
async def run_async_test():
    """Helper to run async tests with proper event loop."""
    def _run_async(coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    return _run_async


# ===== Test Data Factories =====

class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_batch_request(asset_types=None, counts=None):
        """Create a batch request with specified types and counts."""
        if asset_types is None:
            asset_types = ["sigil", "enso"]
        if counts is None:
            counts = [1, 1]
        
        requests = [
            GenerationRequest(type=asset_type, count=count, parameters={})
            for asset_type, count in zip(asset_types, counts)
        ]
        return BatchRequest(requests=requests)
    
    @staticmethod
    def create_test_image(size=(100, 100), color=(255, 0, 0, 255)):
        """Create a test image with specified size and color."""
        return Image.new("RGBA", size, color)
    
    @staticmethod
    def create_noise_image(size=(64, 64), seed=None):
        """Create a noise image for testing."""
        np.random.seed(seed)
        img_array = np.random.randint(0, 256, (*size, 4), dtype=np.uint8)
        return Image.fromarray(img_array, 'RGBA')


@pytest.fixture
def test_factory():
    """Provide test data factory."""
    return TestDataFactory()


# ===== Configuration Overrides =====

@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""
    # Store original values
    original_values = {}
    test_env = {
        "TESTING": "1",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000",
        "OPENAI_API_KEY": "test-key-placeholder",
        "LLM_BASE_URL": "https://test-api.example.com",
    }
    
    # Set test values
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# ===== Cleanup Fixtures =====

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    
    # Force garbage collection
    import gc
    gc.collect()
    
    # Clear any test caches
    try:
        cache = get_cache()
        # Only clear test-related keys
        test_keys = [key for key in cache._cache.keys() if key.startswith('test_')]
        for key in test_keys:
            cache._cache.pop(key, None)
    except Exception:
        pass


# ===== Skip Fixtures =====

@pytest.fixture
def skip_if_no_llm():
    """Skip test if LLM is not available."""
    try:
        import llm_director
        yield
    except ImportError:
        pytest.skip("LLM Director not available - skipping LLM-dependent test")


@pytest.fixture
def skip_if_slow():
    """Mark test as slow (can be skipped with -m 'not slow')."""
    return pytest.mark.slow


# ===== Custom Assertions =====

def assert_valid_png_image(img):
    """Assert that image is valid PNG format."""
    assert isinstance(img, Image.Image), f"Expected PIL Image, got {type(img)}"
    assert img.format == "PNG" or img.mode in ["RGBA", "RGB"], f"Invalid image format: {img.format} {img.mode}"
    assert img.size[0] > 0 and img.size[1] > 0, f"Invalid image size: {img.size}"


def assert_api_response_success(response, status_code=200):
    """Assert API response indicates success."""
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}"
    if hasattr(response, 'json'):
        data = response.json()
        if isinstance(data, dict):
            assert 'error' not in data or data['error'] is None, f"API returned error: {data}"


# Make custom assertions available globally
pytest.assert_valid_png_image = assert_valid_png_image
pytest.assert_api_response_success = assert_api_response_success