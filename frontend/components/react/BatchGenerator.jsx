/**
 * @fileoverview BatchGenerator React Component
 * @description Component for generating multiple assets in batch
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { APIClient, APIError } from '../utils/api-client.js';
import { AssetFormatters } from '../utils/formatters.js';

/**
 * Component for generating multiple assets in batch
 * @param {Object} props - Component props
 * @param {string} props.apiEndpoint - API endpoint URL
 * @param {string} props.apiKey - API key for authentication
 * @param {string} props.baseUrl - Base URL for LLM provider
 * @param {string} props.theme - Theme to apply
 * @param {Function} props.onBatchComplete - Callback when batch is complete
 * @param {Function} props.onBatchProgress - Progress callback
 * @param {Object} props.defaultParams - Default generation parameters
 * @returns {JSX.Element} BatchGenerator component
 */
const BatchGenerator = ({
  apiEndpoint = 'http://localhost:8001',
  apiKey = '',
  baseUrl = 'https://router.requesty.ai/v1',
  theme = 'default',
  onBatchComplete = () => {},
  onBatchProgress = () => {},
  defaultParams = {},
  className = '',
  ...props
}) => {
  // State management
  const [isRunning, setIsRunning] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [batchErrors, setBatchErrors] = useState([]);
  const [progress, setProgress] = useState(0);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(null);
  const [startTime, setStartTime] = useState(null);

  // Form state
  const [jobConfig, setJobConfig] = useState({
    count: 10,
    assetType: 'enso',
    width: 800,
    height: 800,
    directed: false,
    prompt: '',
    model: '',
    delay: 1000
  });

  const [errors, setErrors] = useState({});
  const abortControllerRef = useRef(null);
  const apiClient = useRef(null);

  // Initialize API client
  useEffect(() => {
    apiClient.current = new APIClient({
      endpoint: apiEndpoint,
      apiKey,
      baseUrl
    });

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [apiEndpoint, apiKey, baseUrl]);

  /**
   * Validate job configuration
   */
  const validateJobConfig = useCallback(() => {
    const newErrors = {};

    if (!jobConfig.count || jobConfig.count < 1) {
      newErrors.count = 'Count must be at least 1';
    }
    if (jobConfig.count > 50) {
      newErrors.count = 'Count cannot exceed 50';
    }

    if (!jobConfig.assetType || !['parchment', 'enso', 'sigil', 'giraffe', 'kangaroo'].includes(jobConfig.assetType)) {
      newErrors.assetType = 'Invalid asset type';
    }

    if (jobConfig.width < 100 || jobConfig.width > 2048) {
      newErrors.width = 'Width must be between 100 and 2048';
    }

    if (jobConfig.height < 100 || jobConfig.height > 2048) {
      newErrors.height = 'Height must be between 100 and 2048';
    }

    if (jobConfig.directed && !jobConfig.prompt.trim()) {
      newErrors.prompt = 'Prompt is required for directed generation';
    }

    if (jobConfig.delay < 0 || jobConfig.delay > 10000) {
      newErrors.delay = 'Delay must be between 0 and 10000 milliseconds';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [jobConfig]);

  /**
   * Generate a single asset
   */
  const generateSingleAsset = useCallback(async (index, config) => {
    try {
      let assetBlob;
      
      if (config.directed && config.prompt) {
        assetBlob = await apiClient.current.generateDirectedAsset(
          config.prompt,
          config.assetType,
          { model: config.model }
        );
      } else {
        assetBlob = await apiClient.current.generateAsset(config.assetType);
      }

      const assetUrl = APIClient.blobToURL(assetBlob);
      
      return {
        id: `batch_asset_${Date.now()}_${index}`,
        index,
        type: config.assetType,
        url: assetUrl,
        blob: assetBlob,
        createdAt: new Date(),
        size: assetBlob.size,
        metadata: {
          width: config.width,
          height: config.height,
          type: config.assetType,
          prompt: config.directed ? config.prompt : null,
          model: config.model,
          generatedAt: new Date().toISOString(),
          filename: AssetFormatters.formatDownloadFilename({
            generator_type: config.assetType,
            width: config.width,
            height: config.height
          })
        }
      };
    } catch (error) {
      throw {
        index,
        error: error instanceof APIError ? error.message : error.message,
        config
      };
    }
  }, []);

  /**
   * Calculate estimated time remaining
   */
  const calculateETA = useCallback((completed, total, startTime) => {
    if (completed === 0 || !startTime) return null;
    
    const elapsed = Date.now() - startTime;
    const avgPerItem = elapsed / completed;
    const remaining = total - completed;
    
    return Math.round((remaining * avgPerItem) / 1000); // seconds
  }, []);

  /**
   * Run batch generation
   */
  const runBatch = useCallback(async () => {
    if (!validateJobConfig() || isRunning) return;

    setIsRunning(true);
    setCurrentProgress(0);
    setProgress(0);
    setBatchResults([]);
    setBatchErrors([]);
    setStartTime(Date.now());
    
    const newJob = {
      id: `batch_${Date.now()}`,
      config: { ...jobConfig },
      startTime: Date.now(),
      status: 'running'
    };
    setCurrentJob(newJob);

    abortControllerRef.current = new AbortController();
    const results = [];
    const errors = [];

    try {
      for (let i = 0; i < jobConfig.count; i++) {
        // Check if aborted
        if (abortControllerRef.current?.signal.aborted) {
          throw new Error('Batch generation cancelled');
        }

        setCurrentProgress(i);
        const progressPercent = (i / jobConfig.count) * 100;
        setProgress(progressPercent);

        // Calculate ETA
        const eta = calculateETA(i, jobConfig.count, startTime);
        setEstimatedTime(eta);

        // Progress callback
        onBatchProgress({
          current: i,
          total: jobConfig.count,
          progress: progressPercent,
          eta,
          currentAsset: {
            index: i,
            type: jobConfig.assetType,
            config: jobConfig
          }
        });

        try {
          // Generate asset
          const asset = await generateSingleAsset(i, jobConfig);
          results.push(asset);
          setBatchResults([...results]);
        } catch (error) {
          errors.push(error);
          setBatchErrors([...errors]);
        }

        // Add delay between generations (except for the last one)
        if (i < jobConfig.count - 1 && jobConfig.delay > 0) {
          await new Promise(resolve => setTimeout(resolve, jobConfig.delay));
        }
      }

      // Complete the batch
      setProgress(100);
      setCurrentProgress(jobConfig.count);
      
      newJob.status = 'completed';
      newJob.endTime = Date.now();
      newJob.results = results;
      newJob.errors = errors;

      setCurrentJob(newJob);
      setIsRunning(false);

      // Final callback
      onBatchComplete({
        job: newJob,
        results,
        errors,
        success: results.length,
        failed: errors.length,
        total: jobConfig.count
      });

    } catch (error) {
      newJob.status = 'failed';
      newJob.error = error.message;
      setCurrentJob(newJob);
      setIsRunning(false);

      onBatchComplete({
        job: newJob,
        results,
        errors: [...errors, { index: currentProgress, error: error.message }],
        success: results.length,
        failed: errors.length + 1,
        total: jobConfig.count
      });
    }
  }, [
    jobConfig, 
    isRunning, 
    validateJobConfig, 
    generateSingleAsset, 
    calculateETA, 
    onBatchProgress, 
    onBatchComplete, 
    currentProgress,
    startTime
  ]);

  /**
   * Cancel batch generation
   */
  const cancelBatch = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsRunning(false);
    setProgress(0);
    setCurrentProgress(0);
    setEstimatedTime(null);
    
    if (currentJob) {
      setCurrentJob({
        ...currentJob,
        status: 'cancelled',
        endTime: Date.now()
      });
    }
  }, [currentJob]);

  /**
   * Download all results as ZIP
   */
  const downloadAllResults = useCallback(async () => {
    if (batchResults.length === 0) return;

    try {
      // In a real implementation, you would use a library like JSZip
      // For now, we'll download each file individually
      for (const asset of batchResults) {
        const link = document.createElement('a');
        link.href = asset.url;
        link.download = asset.metadata.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Small delay between downloads
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
  }, [batchResults]);

  const isValid = Object.keys(errors).length === 0;
  const canStart = isValid && !isRunning;

  return (
    <div className={`uw-batch-generator ${theme} ${className}`} {...props}>
      <div className="uw-batch-header">
        <h2 className="uw-title">Batch Generation</h2>
        <p className="uw-description">
          Generate multiple assets with the same parameters
        </p>
      </div>

      <div className="uw-batch-form">
        <div className="uw-form-grid">
          {/* Asset Count */}
          <div className="uw-form-group">
            <label htmlFor="batch-count" className="uw-label">
              Number of Assets *
            </label>
            <input
              type="number"
              id="batch-count"
              className={`uw-input ${errors.count ? 'error' : ''}`}
              value={jobConfig.count}
              min="1"
              max="50"
              onChange={(e) => setJobConfig(prev => ({ ...prev, count: parseInt(e.target.value) }))}
              disabled={isRunning}
            />
            {errors.count && (
              <div className="uw-error-text" role="alert">{errors.count}</div>
            )}
          </div>

          {/* Asset Type */}
          <div className="uw-form-group">
            <label htmlFor="batch-asset-type" className="uw-label">
              Asset Type *
            </label>
            <select
              id="batch-asset-type"
              className={`uw-select ${errors.assetType ? 'error' : ''}`}
              value={jobConfig.assetType}
              onChange={(e) => setJobConfig(prev => ({ ...prev, assetType: e.target.value }))}
              disabled={isRunning}
            >
              <option value="parchment">Void Parchment</option>
              <option value="enso">Ink Enso</option>
              <option value="sigil">Eldritch Sigil</option>
              <option value="giraffe">Ink Giraffe</option>
              <option value="kangaroo">Eldritch Kangaroo</option>
            </select>
            {errors.assetType && (
              <div className="uw-error-text" role="alert">{errors.assetType}</div>
            )}
          </div>

          {/* Dimensions */}
          <div className="uw-form-group">
            <label htmlFor="batch-width" className="uw-label">
              Width *
            </label>
            <input
              type="number"
              id="batch-width"
              className={`uw-input ${errors.width ? 'error' : ''}`}
              value={jobConfig.width}
              min="100"
              max="2048"
              step="100"
              onChange={(e) => setJobConfig(prev => ({ ...prev, width: parseInt(e.target.value) }))}
              disabled={isRunning}
            />
            {errors.width && (
              <div className="uw-error-text" role="alert">{errors.width}</div>
            )}
          </div>

          <div className="uw-form-group">
            <label htmlFor="batch-height" className="uw-label">
              Height *
            </label>
            <input
              type="number"
              id="batch-height"
              className={`uw-input ${errors.height ? 'error' : ''}`}
              value={jobConfig.height}
              min="100"
              max="2048"
              step="100"
              onChange={(e) => setJobConfig(prev => ({ ...prev, height: parseInt(e.target.value) }))}
              disabled={isRunning}
            />
            {errors.height && (
              <div className="uw-error-text" role="alert">{errors.height}</div>
            )}
          </div>

          {/* Directed Generation */}
          <div className="uw-form-group">
            <label className="uw-checkbox-label">
              <input
                type="checkbox"
                checked={jobConfig.directed}
                onChange={(e) => setJobConfig(prev => ({ ...prev, directed: e.target.checked }))}
                disabled={isRunning}
              />
              Enable LLM-directed generation
            </label>
          </div>

          {jobConfig.directed && (
            <>
              <div className="uw-form-group">
                <label htmlFor="batch-prompt" className="uw-label">
                  Generation Prompt *
                </label>
                <textarea
                  id="batch-prompt"
                  className={`uw-textarea ${errors.prompt ? 'error' : ''}`}
                  value={jobConfig.prompt}
                  placeholder="Describe the assets you want to generate..."
                  rows="3"
                  onChange={(e) => setJobConfig(prev => ({ ...prev, prompt: e.target.value }))}
                  disabled={isRunning}
                />
                {errors.prompt && (
                  <div className="uw-error-text" role="alert">{errors.prompt}</div>
                )}
              </div>

              <div className="uw-form-group">
                <label htmlFor="batch-model" className="uw-label">
                  LLM Model
                </label>
                <input
                  type="text"
                  id="batch-model"
                  className="uw-input"
                  value={jobConfig.model}
                  placeholder="gpt-3.5-turbo"
                  onChange={(e) => setJobConfig(prev => ({ ...prev, model: e.target.value }))}
                  disabled={isRunning}
                />
              </div>
            </>
          )}

          {/* Delay */}
          <div className="uw-form-group">
            <label htmlFor="batch-delay" className="uw-label">
              Delay between generations (ms)
            </label>
            <input
              type="number"
              id="batch-delay"
              className={`uw-input ${errors.delay ? 'error' : ''}`}
              value={jobConfig.delay}
              min="0"
              max="10000"
              step="100"
              onChange={(e) => setJobConfig(prev => ({ ...prev, delay: parseInt(e.target.value) }))}
              disabled={isRunning}
            />
            {errors.delay && (
              <div className="uw-error-text" role="alert">{errors.delay}</div>
            )}
            <div className="uw-help-text">
              Add delay to avoid overwhelming the API
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="uw-form-actions">
          {!isRunning ? (
            <button
              type="button"
              className="uw-btn uw-btn-primary"
              onClick={runBatch}
              disabled={!canStart}
            >
              Start Batch Generation
            </button>
          ) : (
            <button
              type="button"
              className="uw-btn uw-btn-danger"
              onClick={cancelBatch}
            >
              Cancel Batch
            </button>
          )}
        </div>
      </div>

      {/* Progress Section */}
      {(isRunning || currentJob) && (
        <div className="uw-batch-progress">
          <h3 className="uw-section-title">Progress</h3>
          
          {/* Progress Bar */}
          <div className="uw-progress-container">
            <div className="uw-progress-bar" style={{ width: `${progress}%` }} />
            <div className="uw-progress-text">
              {currentProgress} / {jobConfig.count} ({Math.round(progress)}%)
            </div>
          </div>

          {/* ETA */}
          {estimatedTime && (
            <div className="uw-eta">
              Estimated time remaining: {estimatedTime}s
            </div>
          )}

          {/* Current Job Info */}
          {currentJob && (
            <div className="uw-job-info">
              <div className="uw-job-status">
                Status: <span className={`uw-status-${currentJob.status}`}>{currentJob.status}</span>
              </div>
              {currentJob.status === 'running' && (
                <div className="uw-current-asset">
                  Currently generating: {AssetFormatters.formatAssetType(jobConfig.assetType)} #{currentProgress + 1}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Results Section */}
      {batchResults.length > 0 && (
        <div className="uw-batch-results">
          <div className="uw-results-header">
            <h3 className="uw-section-title">Generated Assets</h3>
            <div className="uw-results-summary">
              <span className="uw-success-count">Success: {batchResults.length}</span>
              {batchErrors.length > 0 && (
                <span className="uw-error-count">Failed: {batchErrors.length}</span>
              )}
            </div>
            <button
              type="button"
              className="uw-btn uw-btn-secondary"
              onClick={downloadAllResults}
            >
              Download All
            </button>
          </div>

          <div className="uw-results-grid">
            {batchResults.map((asset, index) => (
              <div key={asset.id} className="uw-result-item">
                <img
                  src={asset.url}
                  alt={`Generated asset ${index + 1}`}
                  className="uw-result-thumbnail"
                  loading="lazy"
                />
                <div className="uw-result-info">
                  <div className="uw-result-title">#{index + 1}</div>
                  <div className="uw-result-meta">
                    {asset.metadata.width} × {asset.metadata.height}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Errors Section */}
      {batchErrors.length > 0 && (
        <div className="uw-batch-errors">
          <h3 className="uw-section-title">Errors</h3>
          <div className="uw-error-list">
            {batchErrors.map((error, index) => (
              <div key={index} className="uw-error-item">
                <div className="uw-error-index">Asset #{error.index + 1}</div>
                <div className="uw-error-message">{error.error}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// PropTypes definition
BatchGenerator.propTypes = {
  apiEndpoint: PropTypes.string,
  apiKey: PropTypes.string,
  baseUrl: PropTypes.string,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  onBatchComplete: PropTypes.func,
  onBatchProgress: PropTypes.func,
  defaultParams: PropTypes.object,
  className: PropTypes.string
};

export default BatchGenerator;