/**
 * Global setup for Playwright E2E tests
 */

const { chromium } = require('@playwright/test');

/**
 * Setup function that runs once before all tests
 */
async function globalSetup() {
  console.log('🚀 Starting Playwright E2E test setup...');
  
  // Check if backend server is running
  const backendUrl = 'http://localhost:8001';
  const maxRetries = 30;
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const response = await fetch(`${backendUrl}/health`);
      if (response.ok) {
        console.log('✅ Backend server is running');
        break;
      }
    } catch (error) {
      console.log(`⏳ Waiting for backend server... (attempt ${retries + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      retries++;
    }
  }
  
  if (retries >= maxRetries) {
    throw new Error('Backend server did not start in time');
  }
  
  // Create test results directory
  const fs = require('fs');
  const path = require('path');
  
  const testResultsDir = path.join(process.cwd(), 'test-results');
  const screenshotsDir = path.join(testResultsDir, 'screenshots');
  const videosDir = path.join(testResultsDir, 'videos');
  
  [testResultsDir, screenshotsDir, videosDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
  
  console.log('✅ Test directories created');
  console.log('🎭 Playwright E2E setup completed successfully');
}

module.exports = globalSetup;