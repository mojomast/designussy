"""End-to-end tests for the NanoBanana Generator system."""

# Test markers for categorization
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