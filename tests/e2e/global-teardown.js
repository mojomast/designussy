/**
 * Global teardown for Playwright E2E tests
 */

/**
 * Teardown function that runs once after all tests
 */
async function globalTeardown() {
  console.log('🧹 Starting Playwright E2E test teardown...');
  
  // Clean up test data
  const fs = require('fs');
  const path = require('path');
  
  // Archive test results for CI/CD
  if (process.env.CI) {
    const testResultsDir = path.join(process.cwd(), 'test-results');
    
    if (fs.existsSync(testResultsDir)) {
      // Archive test results
      const archiveName = `test-results-${Date.now()}.tar.gz`;
      const archivePath = path.join(process.cwd(), archiveName);
      
      try {
        const { execSync } = require('child_process');
        execSync(`cd "${testResultsDir}" && tar -czf "${archivePath}" .`);
        console.log(`📦 Test results archived: ${archiveName}`);
      } catch (error) {
        console.warn('⚠️ Failed to archive test results:', error.message);
      }
    }
  }
  
  // Clean up any temporary files
  const tempDirs = [
    path.join(process.cwd(), '.playwright'),
    path.join(process.cwd(), 'test-results', 'temp')
  ];
  
  tempDirs.forEach(dir => {
    if (fs.existsSync(dir)) {
      try {
        fs.rmSync(dir, { recursive: true, force: true });
        console.log(`🗑️ Cleaned up temp directory: ${dir}`);
      } catch (error) {
        console.warn(`⚠️ Failed to clean up ${dir}:`, error.message);
      }
    }
  });
  
  console.log('🎭 Playwright E2E teardown completed successfully');
}

module.exports = globalTeardown;