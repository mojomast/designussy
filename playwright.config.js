/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: './tests/e2e',
  
  // Test execution timeout (30 seconds)
  timeout: 30000,
  
  // Test expectations timeout (5 seconds)
  expect: {
    timeout: 5000,
  },
  
  // Parallel test execution
  fullyParallel: true,
  
  // Forbid test.only and test.skip
  forbidOnly: !!process.env.CI,
  
  // Retry failed tests
  retries: process.env.CI ? 2 : 0,
  
  // Number of test workers
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  
  // Global test settings
  use: {
    // Action timeout
    actionTimeout: 0,
    
    // Base URL for the application
    baseURL: 'http://localhost:8000',
    
    // Trace recording
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure  
    video: 'retain-on-failure',
    
    // Common HTTP headers
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },
  },
  
  // Browser projects configuration
  projects: [
    {
      name: 'chromium',
      use: { 
        browserName: 'chromium',
        viewport: { width: 1280, height: 720 },
      },
    },
    
    // Mobile testing
    {
      name: 'mobile-chrome',
      use: { 
        browserName: 'chromium',
        deviceName: 'Pixel 5',
        viewport: { width: 393, height: 851 },
        hasTouch: true,
      },
    },
    
    // Tablet testing
    {
      name: 'tablet-chrome',
      use: { 
        browserName: 'chromium', 
        deviceName: 'iPad Pro',
        viewport: { width: 1024, height: 768 },
        hasTouch: true,
      },
    },
    
    // Desktop Safari (if available)
    {
      name: 'webkit',
      use: { 
        browserName: 'webkit',
        viewport: { width: 1280, height: 720 },
      },
    },
  ],
  
  // Web server configuration for CI/CD
  webServer: {
    command: 'python backend.py',
    port: 8000,
    timeout: 120000, // 2 minutes
    reuseExistingServer: !process.env.CI,
    env: {
      PYTHONPATH: '.',
      PYTHONIOENCODING: 'utf-8',
    },
  },
  
  // Global test hooks
  globalSetup: './tests/e2e/global-setup.js',
  globalTeardown: './tests/e2e/global-teardown.js',
  
  // Test output directories
  outputDir: './test-results',
  
  // TypeScript configuration
  tsconfig: './tsconfig.json',
  
  // Ignore test files pattern
  testIgnore: [
    '**/node_modules/**',
    '**/dist/**',
    '**/build/**',
    '**/.*/**',
    '**/__pycache__/**',
    '**/.pytest_cache/**',
    '**/*.config.js',
  ],
  
  // Test match pattern
  testMatch: [
    '**/tests/e2e/**/*.spec.js',
    '**/tests/e2e/**/*.test.js',
  ],
  
  // Maximum number of test failures before stopping
  maxFailures: process.env.CI ? 5 : undefined,
  
  // Fully parallel mode for CI
  workers: process.env.CI ? 2 : undefined,
};

export default config;