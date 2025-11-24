# Testing Documentation

## Overview

This document describes the comprehensive test suite for the NanoBanana Generator project. The test suite provides >80% code coverage across all major components including generators, API endpoints, caching, batch processing, and integration workflows, plus comprehensive end-to-end testing with Playwright.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_generators/         # Generator unit tests
│   ├── test_base_generator.py
│   ├── test_sigil_generator.py
│   ├── test_enso_generator.py
│   ├── test_parchment_generator.py
│   ├── test_giraffe_generator.py
│   ├── test_kangaroo_generator.py
│   └── test_factory.py
├── test_api/               # API integration tests
│   └── test_endpoints.py
├── test_cache/            # Cache system tests
│   └── test_lru_cache.py
├── test_batch/            # Batch job tests
│   └── test_batch_job.py
├── test_utils/            # Utility tests
├── test_integration/      # Integration tests
│   └── test_workflows.py
└── e2e/                   # End-to-End Tests (Playwright)
    ├── __init__.py
    ├── conftest.py        # Playwright fixtures and configuration
    ├── utils.py           # E2E test utilities
    ├── global-setup.js    # Global test setup
    ├── global-teardown.js # Global test cleanup
    ├── test_generation_workflows.py
    ├── test_batch_workflows.py
    ├── test_cache_workflows.py
    ├── test_ui_interactions.py
    └── test_error_handling.py
```

## Running Tests

### Basic Test Run
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test category
pytest tests/test_generators/
pytest tests/test_api/
pytest tests/test_integration/

# Run E2E tests only
pytest tests/e2e/
```

### Performance Tests
```bash
# Run performance tests only
pytest -m performance

# Run slow tests (can be skipped)
pytest -m "not slow"

# Run E2E slow tests
pytest tests/e2e/ -m slow
```

### Coverage Reports
```bash
# Run with coverage
pytest --cov=generators --cov=utils --cov=backend --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run E2E tests in parallel
npx playwright test --workers=2
```

## End-to-End Testing (E2E)

### Overview
E2E tests validate complete user workflows through browser automation using Playwright. These tests ensure the entire system works as expected from a user perspective.

### Prerequisites
```bash
# Install Node.js dependencies for E2E tests
npm install

# Install Playwright browsers
npx playwright install

# Start backend server (in separate terminal)
python backend.py
```

### Running E2E Tests
```bash
# Run all E2E tests
npx playwright test

# Run specific E2E test file
npx playwright test tests/e2e/test_generation_workflows.py

# Run E2E tests in UI mode (watch mode)
npx playwright test --ui

# Run E2E tests with headed browser
npx playwright test --headed

# Run E2E tests on specific browser
npx playwright test --project=chromium
npx playwright test --project=webkit
npx playwright test --project=mobile-chrome

# Run E2E tests with specific viewport
npx playwright test --project="mobile-chrome"

# Debug E2E tests
npx playwright test --debug

# Generate E2E test report
npx playwright show-report
```

### E2E Test Categories

#### 1. Generation Workflow Tests (`test_generation_workflows.py`)
- **Basic Generation**: Test asset generation through UI and API
- **Multiple Asset Types**: Test all generator types (parchment, enso, sigil, giraffe, kangaroo)
- **Parameter Testing**: Test generation with custom parameters
- **Performance Validation**: Ensure generation completes within time limits
- **Image Display**: Verify generated images are properly displayed

#### 2. Batch Workflow Tests (`test_batch_workflows.py`)
- **Job Creation**: Test batch job creation and configuration
- **Progress Monitoring**: Test real-time job progress tracking
- **Job Cancellation**: Test canceling running batch jobs
- **Results Retrieval**: Test downloading batch results
- **Multi-Asset Batches**: Test batches with multiple asset types

#### 3. Cache Workflow Tests (`test_cache_workflows.py`)
- **Cache Hits**: Verify cache hits on repeated requests
- **Cache Statistics**: Test cache stats display and accuracy
- **Cache Clearing**: Test manual cache clearing functionality
- **Performance Impact**: Verify cache improves performance
- **Memory Efficiency**: Test cache memory management

#### 4. UI Interaction Tests (`test_ui_interactions.py`)
- **Navigation**: Test page navigation and routing
- **Form Interactions**: Test form submissions and input validation
- **Responsive Design**: Test mobile, tablet, and desktop layouts
- **Accessibility**: Test keyboard navigation and screen reader compatibility
- **Visual Elements**: Test buttons, hover states, and visual feedback

#### 5. Error Handling Tests (`test_error_handling.py`)
- **API Errors**: Test handling of invalid API requests
- **Network Issues**: Test behavior during network interruptions
- **Input Validation**: Test client-side input validation
- **Error Messages**: Test error message display and accessibility
- **Recovery**: Test system recovery after errors

### E2E Test Configuration

#### Playwright Configuration (`playwright.config.js`)
- **Browser Support**: Chromium, WebKit, mobile browsers
- **Test Timeouts**: 30s test timeout, 5s expectation timeout
- **Screenshots**: Automatic screenshots on failure
- **Videos**: Video recording on failure for debugging
- **Parallel Execution**: Configurable worker count
- **Reporting**: HTML, JSON, and custom reporters

#### Test Markers for E2E
- `@pytest.mark.e2e`: Mark test as E2E test
- `@pytest.mark.ui`: Mark test as UI interaction test
- `@pytest.mark.generation`: Mark test as asset generation test
- `@pytest.mark.batch`: Mark test as batch processing test
- `@pytest.mark.cache`: Mark test as cache behavior test
- `@pytest.mark.slow`: Mark test as slow-running test

#### E2E Test Utilities (`tests/e2e/utils.py`)
- **TestUtils**: Common E2E testing utilities
- **APIHelper**: Helper for API interactions
- **UIHelper**: Helper for UI element interactions
- **AssetGenerationHelper**: Helper for asset generation workflows

### E2E Best Practices

#### Page Object Model
```python
class GenerationPage:
    def __init__(self, page):
        self.page = page
        self.parchment_button = page.locator('[data-asset-type="parchment"]')
        self.result_image = page.locator('.generated-image')
    
    async def generate_parchment(self):
        await self.parchment_button.click()
        await self.result_image.wait_for()
        return self.result_image
```

#### Explicit Waits
```python
# ❌ Don't use hard-coded sleeps
await asyncio.sleep(3)

# ✅ Use proper waiting
await page.wait_for_selector('.result')
await page.wait_for_load_state('networkidle')
await expect(element).to_be_visible()
```

#### Test Isolation
```python
@pytest.mark.asyncio
async def test_generation_should_be_isolated(page):
    # Each test starts with fresh page and context
    await page.goto('http://localhost:8000')
    # Test isolated from other tests
```

## Test Categories

### 1. Generator Tests (`test_generators/`)
- **Base Generator**: Tests abstract base class functionality
- **Concrete Generators**: Sigil, Enso, Parchment, Giraffe, Kangaroo
- **Factory Tests**: Generator creation and registry functionality

### 2. API Tests (`test_api/`)
- **Basic Endpoints**: Health checks, root endpoint, generator listing
- **Generator Endpoints**: Individual asset generation
- **Modular Endpoints**: New modular generator system
- **Cache Endpoints**: Cache statistics and management
- **Batch Endpoints**: Batch job creation and management
- **Error Handling**: Invalid requests and error responses

### 3. Cache Tests (`test_cache/`)
- **LRU Cache**: Basic cache operations
- **TTL Expiration**: Time-based cache expiration
- **Thread Safety**: Concurrent access testing
- **Statistics**: Cache hit rates and metrics

### 4. Batch Tests (`test_batch/`)
- **Job Creation**: Batch request processing
- **Progress Tracking**: Job status monitoring
- **Cancellation**: Job cancellation functionality
- **Error Handling**: Failed job recovery

### 5. Integration Tests (`test_integration/`)
- **Complete Workflows**: End-to-end generation
- **Cross-System Integration**: Generator + API + Cache
- **Performance Validation**: System-wide performance checks

## Test Fixtures

### Environment Setup
- **Test Environment**: Automatic environment variable configuration
- **Clean State**: Each test starts with clean cache and generators
- **Resource Cleanup**: Automatic cleanup after each test

### Data Factories
- **Image Generation**: Standard test images
- **Generator Creation**: Pre-configured generator instances
- **Batch Requests**: Standardized batch job data

### Mocking and Stubs
- **API Mocking**: Mocked external dependencies
- **Generator Mocks**: Simplified generator implementations
- **Cache Mocks**: Isolated cache testing

### E2E Fixtures
- **Browser Management**: Automatic browser lifecycle management
- **Page Contexts**: Isolated page contexts for tests
- **API Client**: Pre-configured API client for E2E tests
- **Screenshots**: Automatic screenshots on test failures

## Performance Testing

### Performance Targets
- **Simple Assets**: <100ms generation time
- **Medium Assets**: <200ms generation time
- **Complex Assets**: <500ms generation time
- **Memory Usage**: <200MB per generation
- **Cache Hit Performance**: <10ms retrieval
- **E2E Tests**: <5s per UI interaction

### Performance Monitoring
- **Generation Time Tracking**: Automatic performance measurement
- **Memory Usage Monitoring**: Memory leak detection
- **Concurrency Testing**: Thread safety validation
- **E2E Performance**: Browser automation performance tracking

## Coverage Requirements

### Target Coverage
- **Overall Coverage**: >80%
- **Generators**: >90%
- **API Endpoints**: >85%
- **Cache System**: >80%
- **Batch System**: >80%
- **E2E Coverage**: All user workflows covered

### Coverage Configuration
Configured in `pyproject.toml` and `.coveragerc`:
- Source paths: `generators`, `utils`, `backend`
- Excluded paths: `tests/`, `scripts/`, `.venv/`
- HTML reports: `htmlcov/` directory
- E2E artifacts: `test-results/` directory

## Writing New Tests

### Test Structure
```python
class TestFeature:
    """Test suite for feature functionality."""
    
    def test_basic_functionality(self):
        """Test basic feature behavior."""
        # Arrange
        setup_data = create_test_data()
        
        # Act
        result = feature_function(setup_data)
        
        # Assert
        assert result.expected_behavior
    
    def test_error_conditions(self):
        """Test error handling."""
        with pytest.raises(ExpectedError):
            feature_function(invalid_input)
    
    @pytest.mark.performance
    def test_performance(self):
        """Test performance requirements."""
        start_time = time.perf_counter()
        result = feature_function(test_data)
        duration = time.perf_counter() - start_time
        
        assert duration < PERFORMANCE_TARGET
```

### E2E Test Structure
```python
@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.asyncio
class TestUserWorkflow:
    async def test_complete_workflow(self, page):
        """Test complete user workflow."""
        # Test implementation
        await page.goto('http://localhost:8000')
        # ... test steps
        assert await page.locator('.success-message').is_visible()
```

### Best Practices
1. **One Assert Per Test**: Focus on single behavior
2. **Descriptive Names**: Clear test method names
3. **Arrange-Act-Assert**: Clear test structure
4. **Test Doubles**: Use mocks for external dependencies
5. **Parameterization**: Test multiple inputs efficiently
6. **E2E Specific**: Use Page Object Model, explicit waits, test isolation

### Test Markers
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.ui`: UI interaction tests
- `@pytest.mark.generation`: Asset generation tests
- `@pytest.mark.batch`: Batch processing tests
- `@pytest.mark.cache`: Cache behavior tests

## CI/CD Integration

### GitHub Actions
Automated testing on pull requests and main branch:
- **Unit Tests**: Python version matrix (3.8, 3.9, 3.10, 3.11)
- **E2E Tests**: Playwright tests with browser matrix
- **Coverage Reporting**: Failure on <80% coverage
- **Performance Regression Detection**: Performance test validation
- **Linting and Type Checking**: Code quality validation
- **Artifacts**: Test reports and screenshots uploaded on failures

### Local Development
```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests with coverage
pytest --cov=generators --cov=utils --cov=backend

# Run performance tests
pytest -m performance

# Check coverage locally
pytest --cov=generators --cov-report=html
open htmlcov/index.html

# Setup E2E testing
npm install
npx playwright install

# Run E2E tests
npx playwright test

# Debug E2E tests
npx playwright test --ui
```

### E2E CI/CD Workflow
```yaml
e2e-tests:
  runs-on: ubuntu-latest
  steps:
  - uses: actions/checkout@v4
  - name: Setup Node.js and Python
    uses: actions/setup-node@v4
    uses: actions/setup-python@v4
  - name: Install dependencies
    run: |
      npm install
      pip install -e .[dev]
      npx playwright install --with-deps
  - name: Start backend server
    run: python backend.py &
  - name: Run E2E tests
    run: npx playwright test --reporter=html,json
  - name: Upload test artifacts
    uses: actions/upload-artifact@v3
    if: always()
    with:
      name: playwright-report
      path: playwright-report/
```

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Test Timeouts**: Increase timeout for slow generators
3. **Memory Issues**: Reduce image sizes in tests
4. **Cache Conflicts**: Use isolated test cache
5. **E2E Browser Issues**: Ensure Playwright browsers are installed
6. **E2E Connection Errors**: Verify backend server is running

### Debug Mode
```bash
# Run with debug output
pytest -v -s --tb=long

# Run single test
pytest tests/test_generators/test_sigil_generator.py::TestSigilGenerator::test_generator_type -v

# Debug E2E tests
npx playwright test --ui
npx playwright test --debug

# View E2E test traces
npx playwright show-trace trace.zip
```

### E2E Debugging
```bash
# Run E2E tests with headed browser
npx playwright test --headed

# Record test trace
npx playwright test --trace=on

# Run specific E2E test with debugging
npx playwright test tests/e2e/test_generation_workflows.py::TestGenerationWorkflows::test_generate_parchment_texture --headed --debug
```

## E2E Test Results and Artifacts

### Test Reports
- **HTML Report**: `playwright-report/index.html`
- **JSON Report**: `test-results/results.json`
- **Test Artifacts**: `test-results/screenshots/`, `test-results/videos/`

### Artifact Management
- **Screenshots**: Automatic on test failures
- **Videos**: Recorded test executions for debugging
- **Traces**: Detailed execution traces for investigation
- **Coverage Reports**: HTML coverage reports for unit tests

### Performance Tracking
- **Generation Times**: Tracked for all asset types
- **Cache Performance**: Cache hit/miss ratios
- **Batch Processing**: Job completion times
- **UI Response Times**: Browser automation performance