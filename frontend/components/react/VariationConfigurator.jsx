/**
 * @fileoverview VariationConfigurator React Component
 * @description Component for configuring variation strategies and diversity settings
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { APIClient } from '../utils/api-client.js';

/**
 * Component for configuring variation strategies and diversity settings
 * @param {Object} props - Component props
 * @param {Object} props.elementType - Element type definition
 * @param {Function} props.onVariationConfigChange - Callback when config changes
 * @param {Function} props.onPreviewGenerate - Callback for diversity preview
 * @param {string} props.theme - Theme to apply
 * @param {Object} props.initialConfig - Initial variation configuration
 * @returns {JSX.Element} VariationConfigurator component
 */
const VariationConfigurator = ({
  elementType = null,
  onVariationConfigChange = () => {},
  onPreviewGenerate = () => {},
  theme = 'dark',
  initialConfig = {},
  className = '',
  ...props
}) => {
  const [config, setConfig] = useState({
    strategy: 'jitter',
    targetDiversityScore: 0.7,
    samplingStrategy: 'random',
    seed: '',
    batchCount: 1,
    outputFormat: 'json',
    parameterWeights: {},
    diversityWeights: {},
    jitter: {
      jitterAmount: 0.1,
      affectedParameters: []
    },
    strategyPool: {
      poolSize: 10,
      replacementStrategy: 'weighted'
    },
    seeded: {
      baseSeed: Date.now(),
      seedRange: 1000
    },
    ...initialConfig
  });
  
  const [diversityPreview, setDiversityPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [availableParameters, setAvailableParameters] = useState([]);
  const [validationErrors, setValidationErrors] = useState([]);
  const [apiClient] = useState(() => new APIClient({ endpoint: 'http://localhost:8001' }));

  // Extract available parameters from element type
  useEffect(() => {
    if (elementType?.param_schema?.properties) {
      const params = Object.keys(elementType.param_schema.properties);
      setAvailableParameters(params);
      
      // Set default parameter weights
      if (params.length > 0 && Object.keys(config.parameterWeights).length === 0) {
        const defaultWeights = {};
        params.forEach(param => {
          defaultWeights[param] = 1.0;
        });
        setConfig(prev => ({
          ...prev,
          parameterWeights: defaultWeights,
          diversityWeights: defaultWeights
        }));
      }
      
      // Set default affected parameters for jitter
      if (config.jitter.affectedParameters.length === 0) {
        setConfig(prev => ({
          ...prev,
          jitter: {
            ...prev.jitter,
            affectedParameters: params.slice(0, Math.min(3, params.length))
          }
        }));
      }
    }
  }, [elementType]);

  // Update configuration and notify parent
  useEffect(() => {
    onVariationConfigChange(config);
    validateConfig();
  }, [config, onVariationConfigChange]);

  const validateConfig = useCallback(() => {
    const errors = [];
    
    if (config.strategy === 'jitter' && config.jitter.jitterAmount <= 0) {
      errors.push('Jitter amount must be greater than 0');
    }
    
    if (config.strategy === 'strategyPool' && config.strategyPool.poolSize <= 1) {
      errors.push('Strategy pool size must be greater than 1');
    }
    
    if (config.batchCount < 1 || config.batchCount > 1000) {
      errors.push('Batch count must be between 1 and 1000');
    }
    
    if (config.targetDiversityScore < 0 || config.targetDiversityScore > 1) {
      errors.push('Target diversity score must be between 0 and 1');
    }
    
    // Validate parameter weights
    const weightSum = Object.values(config.diversityWeights).reduce((sum, weight) => sum + weight, 0);
    if (weightSum === 0) {
      errors.push('At least one parameter must have a non-zero weight');
    }
    
    setValidationErrors(errors);
  }, [config]);

  const handleConfigChange = useCallback((field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleNestedConfigChange = useCallback((section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  }, []);

  const handleParameterWeightChange = useCallback((param, weight) => {
    setConfig(prev => ({
      ...prev,
      diversityWeights: {
        ...prev.diversityWeights,
        [param]: parseFloat(weight) || 0
      }
    }));
  }, []);

  const handleJitterParameterToggle = useCallback((param) => {
    setConfig(prev => {
      const current = prev.jitter.affectedParameters;
      const updated = current.includes(param)
        ? current.filter(p => p !== param)
        : [...current, param];
        
      return {
        ...prev,
        jitter: {
          ...prev.jitter,
          affectedParameters: updated
        }
      };
    });
  }, []);

  const handlePreview = useCallback(async () => {
    if (!elementType) return;
    
    setPreviewLoading(true);
    
    try {
      const response = await fetch(`http://localhost:8001/diversity/preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          element_type_id: elementType.id,
          variation_config: config,
          sample_count: Math.min(config.batchCount, 20) // Limit preview size
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setDiversityPreview(data);
        onPreviewGenerate(data);
      }
    } catch (err) {
      console.error('Failed to generate diversity preview:', err);
    } finally {
      setPreviewLoading(false);
    }
  }, [elementType, config, onPreviewGenerate]);

  const handleExportConfig = useCallback(() => {
    const exportData = {
      elementType: elementType?.id,
      variationConfig: config,
      exportDate: new Date().toISOString(),
      version: '1.0.0'
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `variation-config-${elementType?.id || 'unknown'}-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [elementType, config]);

  const resetToDefaults = useCallback(() => {
    setConfig({
      strategy: 'jitter',
      targetDiversityScore: 0.7,
      samplingStrategy: 'random',
      seed: '',
      batchCount: 1,
      outputFormat: 'json',
      parameterWeights: availableParameters.reduce((acc, param) => {
        acc[param] = 1.0;
        return acc;
      }, {}),
      diversityWeights: availableParameters.reduce((acc, param) => {
        acc[param] = 1.0;
        return acc;
      }, {}),
      jitter: {
        jitterAmount: 0.1,
        affectedParameters: availableParameters.slice(0, Math.min(3, availableParameters.length))
      },
      strategyPool: {
        poolSize: 10,
        replacementStrategy: 'weighted'
      },
      seeded: {
        baseSeed: Date.now(),
        seedRange: 1000
      }
    });
  }, [availableParameters]);

  return (
    <div className={`uw-variation-configurator ${theme} ${className}`} {...props}>
      {/* Configurator Header */}
      <div className="uw-configurator-header">
        <h2 className="uw-configurator-title">Variation Configurator</h2>
        <p className="uw-configurator-description">
          Configure diversity strategies and variation parameters for this element type
        </p>
      </div>

      {/* Element Type Info */}
      {elementType && (
        <div className="uw-element-type-info">
          <h3 className="uw-element-title">{elementType.name}</h3>
          <p className="uw-element-description">{elementType.description}</p>
          <div className="uw-element-meta">
            <span className="uw-category">Category: {elementType.category}</span>
            <span className="uw-parameter-count">
              {availableParameters.length} parameters available
            </span>
          </div>
        </div>
      )}

      {/* Configuration Form */}
      <div className="uw-config-form">
        {/* Basic Settings */}
        <div className="uw-config-section">
          <h3 className="uw-section-title">Basic Settings</h3>
          
          <div className="uw-form-row">
            <div className="uw-form-group">
              <label className="uw-label">Variation Strategy</label>
              <select
                className="uw-select"
                value={config.strategy}
                onChange={(e) => handleConfigChange('strategy', e.target.value)}
              >
                <option value="jitter">Jitter - Random perturbations</option>
                <option value="strategyPool">Strategy Pool - Pre-defined variations</option>
                <option value="seeded">Seeded - Deterministic generation</option>
                <option value="compositional">Compositional - Parameter combinations</option>
                <option value="parameterSampling">Parameter Sampling - Statistical sampling</option>
              </select>
            </div>

            <div className="uw-form-group">
              <label className="uw-label">Sampling Strategy</label>
              <select
                className="uw-select"
                value={config.samplingStrategy}
                onChange={(e) => handleConfigChange('samplingStrategy', e.target.value)}
              >
                <option value="random">Random</option>
                <option value="latinHypercube">Latin Hypercube</option>
                <option value="halton">Halton Sequence</option>
                <option value="sobol">Sobol Sequence</option>
                <option value="monteCarlo">Monte Carlo</option>
              </select>
            </div>
          </div>

          <div className="uw-form-row">
            <div className="uw-form-group">
              <label className="uw-label">
                Target Diversity Score
                <span className="uw-range-indicator">
                  {config.targetDiversityScore}
                </span>
              </label>
              <input
                type="range"
                className="uw-range-input"
                min="0"
                max="1"
                step="0.05"
                value={config.targetDiversityScore}
                onChange={(e) => handleConfigChange('targetDiversityScore', parseFloat(e.target.value))}
              />
              <div className="uw-range-labels">
                <span>Low (0)</span>
                <span>Medium (0.5)</span>
                <span>High (1)</span>
              </div>
            </div>

            <div className="uw-form-group">
              <label className="uw-label">Seed (for reproducibility)</label>
              <input
                type="text"
                className="uw-input"
                value={config.seed}
                onChange={(e) => handleConfigChange('seed', e.target.value)}
                placeholder="Leave empty for random seed"
              />
              <div className="uw-help-text">
                Use the same seed to reproduce the same variations
              </div>
            </div>
          </div>
        </div>

        {/* Strategy-Specific Configuration */}
        {config.strategy === 'jitter' && (
          <div className="uw-config-section">
            <h3 className="uw-section-title">Jitter Configuration</h3>
            
            <div className="uw-form-row">
              <div className="uw-form-group">
                <label className="uw-label">
                  Jitter Amount
                  <span className="uw-range-indicator">
                    {config.jitter.jitterAmount}
                  </span>
                </label>
                <input
                  type="range"
                  className="uw-range-input"
                  min="0.01"
                  max="0.5"
                  step="0.01"
                  value={config.jitter.jitterAmount}
                  onChange={(e) => handleNestedConfigChange('jitter', 'jitterAmount', parseFloat(e.target.value))}
                />
                <div className="uw-range-labels">
                  <span>Subtle (0.01)</span>
                  <span>Moderate (0.1)</span>
                  <span>Dramatic (0.5)</span>
                </div>
              </div>
            </div>

            <div className="uw-form-group">
              <label className="uw-label">Affected Parameters</label>
              <div className="uw-parameter-checkboxes">
                {availableParameters.map(param => (
                  <label key={param} className="uw-checkbox">
                    <input
                      type="checkbox"
                      checked={config.jitter.affectedParameters.includes(param)}
                      onChange={() => handleJitterParameterToggle(param)}
                    />
                    <span className="uw-checkbox-label">{param}</span>
                  </label>
                ))}
              </div>
              <div className="uw-help-text">
                Select which parameters will be affected by jitter
              </div>
            </div>
          </div>
        )}

        {config.strategy === 'strategyPool' && (
          <div className="uw-config-section">
            <h3 className="uw-section-title">Strategy Pool Configuration</h3>
            
            <div className="uw-form-row">
              <div className="uw-form-group">
                <label className="uw-label">Pool Size</label>
                <input
                  type="number"
                  className="uw-input"
                  min="2"
                  max="100"
                  value={config.strategyPool.poolSize}
                  onChange={(e) => handleNestedConfigChange('strategyPool', 'poolSize', parseInt(e.target.value))}
                />
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Replacement Strategy</label>
                <select
                  className="uw-select"
                  value={config.strategyPool.replacementStrategy}
                  onChange={(e) => handleNestedConfigChange('strategyPool', 'replacementStrategy', e.target.value)}
                >
                  <option value="weighted">Weighted Random</option>
                  <option value="random">Pure Random</option>
                  <option value="sequential">Sequential</option>
                  <option value="roundRobin">Round Robin</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Diversity Weights */}
        <div className="uw-config-section">
          <h3 className="uw-section-title">Diversity Weights</h3>
          <p className="uw-section-description">
            Configure how much each parameter contributes to diversity
          </p>
          
          <div className="uw-weights-grid">
            {availableParameters.map(param => (
              <div key={param} className="uw-weight-control">
                <label className="uw-label">
                  {param}
                  <span className="uw-weight-indicator">
                    {config.diversityWeights[param] || 0}
                  </span>
                </label>
                <input
                  type="range"
                  className="uw-range-input"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.diversityWeights[param] || 0}
                  onChange={(e) => handleParameterWeightChange(param, parseFloat(e.target.value))}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Batch Generation */}
        <div className="uw-config-section">
          <h3 className="uw-section-title">Batch Generation</h3>
          
          <div className="uw-form-row">
            <div className="uw-form-group">
              <label className="uw-label">Batch Count</label>
              <input
                type="number"
                className="uw-input"
                min="1"
                max="1000"
                value={config.batchCount}
                onChange={(e) => handleConfigChange('batchCount', parseInt(e.target.value))}
              />
              <div className="uw-help-text">
                Number of variations to generate
              </div>
            </div>

            <div className="uw-form-group">
              <label className="uw-label">Output Format</label>
              <select
                className="uw-select"
                value={config.outputFormat}
                onChange={(e) => handleConfigChange('outputFormat', e.target.value)}
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="zip">ZIP Archive</option>
                <option value="images">Image Files</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="uw-validation-errors" role="alert">
          <h4 className="uw-error-title">Configuration Issues:</h4>
          <ul className="uw-error-list">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="uw-config-actions">
        <button
          className="uw-btn uw-btn-secondary"
          onClick={resetToDefaults}
        >
          Reset to Defaults
        </button>
        
        <button
          className="uw-btn uw-btn-secondary"
          onClick={handleExportConfig}
          disabled={!elementType}
        >
          Export Config
        </button>
        
        <button
          className="uw-btn uw-btn-primary"
          onClick={handlePreview}
          disabled={previewLoading || !elementType}
        >
          {previewLoading ? (
            <>
              <div className="uw-spinner-small"></div>
              Generating Preview...
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              Preview Diversity
            </>
          )}
        </button>
      </div>

      {/* Diversity Preview */}
      {diversityPreview && (
        <div className="uw-diversity-preview">
          <h3 className="uw-preview-title">Diversity Analysis</h3>
          
          <div className="uw-preview-metrics">
            <div className="uw-metric">
              <span className="uw-metric-label">Actual Diversity Score</span>
              <span className="uw-metric-value">
                {diversityPreview.actual_diversity_score?.toFixed(3) || 'N/A'}
              </span>
            </div>
            
            <div className="uw-metric">
              <span className="uw-metric-label">Target Diversity Score</span>
              <span className="uw-metric-value">
                {config.targetDiversityScore}
              </span>
            </div>
            
            <div className="uw-metric">
              <span className="uw-metric-label">Parameters Analyzed</span>
              <span className="uw-metric-value">
                {diversityPreview.parameters_analyzed || 0}
              </span>
            </div>
          </div>

          {diversityPreview.parameter_distributions && (
            <div className="uw-parameter-distributions">
              <h4 className="uw-distribution-title">Parameter Distributions</h4>
              <div className="uw-distributions-grid">
                {Object.entries(diversityPreview.parameter_distributions).map(([param, dist]) => (
                  <div key={param} className="uw-distribution">
                    <h5 className="uw-distribution-param">{param}</h5>
                    <div className="uw-distribution-stats">
                      <span>Min: {dist.min?.toFixed(3) || 'N/A'}</span>
                      <span>Max: {dist.max?.toFixed(3) || 'N/A'}</span>
                      <span>Mean: {dist.mean?.toFixed(3) || 'N/A'}</span>
                      <span>Std: {dist.std?.toFixed(3) || 'N/A'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// PropTypes definition
VariationConfigurator.propTypes = {
  elementType: PropTypes.object,
  onVariationConfigChange: PropTypes.func,
  onPreviewGenerate: PropTypes.func,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  initialConfig: PropTypes.object,
  className: PropTypes.string
};

export default VariationConfigurator;