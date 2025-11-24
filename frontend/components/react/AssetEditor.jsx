/**
 * @fileoverview AssetEditor React Component
 * @description Full-screen editing interface with real-time preview
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import ParameterControls from './ParameterControls.jsx';
import PreviewCanvas from './PreviewCanvas.jsx';
import { APIClient } from '../utils/api-client.js';
import LivePreviewManager from '../utils/LivePreviewManager.js';

/**
 * Full-screen asset editor with real-time preview
 * @param {Object} props - Component props
 * @param {string} props.generatorType - Type of generator to use
 * @param {Object} props.initialParameters - Initial generation parameters
 * @param {Object} props.schema - Parameter schema definition
 * @param {string} props.theme - Theme to apply
 * @param {boolean} props.enableLivePreview - Whether to enable live preview
 * @param {Function} props.onSave - Callback when asset is saved
 * @param {Function} props.onExport - Callback when asset is exported
 * @param {Function} props.onClose - Callback when editor is closed
 * @returns {JSX.Element} AssetEditor component
 */
const AssetEditor = ({
  generatorType = 'enso',
  initialParameters = {},
  schema = {},
  theme = 'default',
  enableLivePreview = true,
  onSave = () => {},
  onExport = () => {},
  onClose = () => {},
  className = '',
  ...props
}) => {
  const [parameters, setParameters] = useState(initialParameters);
  const [currentAsset, setCurrentAsset] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [livePreviewEnabled, setLivePreviewEnabled] = useState(enableLivePreview);
  const [connectionStatus, setConnectionStatus] = useState({ status: 'disconnected' });
  const [error, setError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const apiClientRef = useRef(null);
  const previewManagerRef = useRef(null);
  const containerRef = useRef(null);

  // Initialize API client and preview manager
  useEffect(() => {
    apiClientRef.current = new APIClient({
      endpoint: 'http://localhost:8001',
      timeout: 60000
    });

    if (enableLivePreview) {
      previewManagerRef.current = new LivePreviewManager({
        endpoint: 'ws://localhost:8001/ws/preview',
        onPreviewUpdate: handlePreviewUpdate,
        onStatusChange: setConnectionStatus
      });

      // Connect to WebSocket
      previewManagerRef.current.connect().catch(error => {
        console.error('Failed to connect to preview server:', error);
        setConnectionStatus({ status: 'error', error: error.message });
      });

      return () => {
        if (previewManagerRef.current) {
          previewManagerRef.current.disconnect();
        }
      };
    }
  }, [enableLivePreview]);

  // Load presets on mount
  useEffect(() => {
    loadPresets();
  }, [generatorType]);

  // Save parameters to history for undo/redo
  useEffect(() => {
    if (Object.keys(parameters).length > 0) {
      addToHistory(parameters);
    }
  }, [parameters]);

  // Handle preview updates from WebSocket
  const handlePreviewUpdate = useCallback((update) => {
    switch (update.type) {
      case 'update':
        // Preview update received
        if (update.assetUrl) {
          setCurrentAsset({
            url: update.assetUrl,
            metadata: {
              dimensions: '800x800',
              format: 'PNG'
            }
          });
        }
        break;
        
      case 'complete':
        // Preview generation complete
        setCurrentAsset({
          url: update.assetUrl,
          metadata: update.metadata || {
            dimensions: '800x800',
            format: 'PNG'
          }
        });
        setIsGenerating(false);
        break;
        
      case 'error':
        // Preview generation failed
        setError(update.error);
        setIsGenerating(false);
        break;
        
      case 'progress':
        // Preview generation in progress
        console.log(`Generation progress: ${update.progress}%`);
        break;
    }
  }, []);

  // Add parameters to history
  const addToHistory = useCallback((params) => {
    setGenerationHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(params);
      
      // Limit history size
      if (newHistory.length > 50) {
        newHistory.shift();
      } else {
        setHistoryIndex(newHistory.length - 1);
      }
      
      return newHistory;
    });
  }, [historyIndex]);

  // Load available presets
  const loadPresets = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8001/presets');
      const data = await response.json();
      
      if (data.status === 'success' && data.presets) {
        // Filter presets for current generator type
        const generatorPresets = [];
        Object.values(data.presets).forEach(category => {
          category.forEach(preset => {
            if (preset.generator_types && preset.generator_types.includes(generatorType)) {
              generatorPresets.push(preset);
            }
          });
        });
        
        setPresets(generatorPresets);
      }
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  }, [generatorType]);

  // Handle parameter changes
  const handleParameterChange = useCallback((newParameters, key, value, errors) => {
    setParameters(newParameters);
    setError(null);

    // Request live preview if enabled
    if (livePreviewEnabled && previewManagerRef.current && !errors || Object.keys(errors).length === 0) {
      previewManagerRef.current.requestPreview(newParameters, generatorType, {
        quality: 'preview',
        priority: 'high'
      });
    }
  }, [generatorType, livePreviewEnabled]);

  // Handle parameter reset
  const handleParameterReset = useCallback((defaultParameters) => {
    setParameters(defaultParameters);
    addToHistory(defaultParameters);
  }, [addToHistory]);

  // Generate asset
  const handleGenerate = useCallback(async (genParameters = null) => {
    const finalParameters = genParameters || parameters;
    
    setIsGenerating(true);
    setError(null);

    try {
      // Use WebSocket if live preview is enabled
      if (livePreviewEnabled && previewManagerRef.current) {
        previewManagerRef.current.requestPreview(finalParameters, generatorType, {
          quality: 'full',
          priority: 'high'
        });
      } else {
        // Fall back to HTTP API
        const response = await fetch(`${apiClientRef.current.endpoint}/generate/advanced/${generatorType}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            asset_type: generatorType,
            parameters: finalParameters
          })
        });

        if (!response.ok) {
          throw new Error(`Generation failed: ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        setCurrentAsset({
          url,
          metadata: {
            dimensions: '800x800',
            format: 'PNG'
          }
        });
        
        setIsGenerating(false);
      }
    } catch (err) {
      setError(err.message);
      setIsGenerating(false);
    }
  }, [generatorType, parameters, livePreviewEnabled]);

  // Undo parameter changes
  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setParameters(generationHistory[newIndex]);
    }
  }, [historyIndex, generationHistory]);

  // Redo parameter changes
  const handleRedo = useCallback(() => {
    if (historyIndex < generationHistory.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setParameters(generationHistory[newIndex]);
    }
  }, [historyIndex, generationHistory]);

  // Load preset
  const handleLoadPreset = useCallback(async (presetName) => {
    try {
      setSelectedPreset(presetName);
      
      const response = await fetch(`http://localhost:8001/generate/preset/${presetName}?asset_type=${generatorType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        throw new Error(`Failed to load preset: ${response.statusText}`);
      }

      // Get preset parameters (would need additional endpoint)
      // For now, just generate with preset
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      setCurrentAsset({
        url,
        metadata: {
          dimensions: '800x800',
          format: 'PNG'
        }
      });
    } catch (err) {
      setError(err.message);
    }
  }, [generatorType]);

  // Save current asset
  const handleSave = useCallback(() => {
    if (currentAsset) {
      onSave({
        asset: currentAsset,
        parameters,
        generatorType,
        timestamp: new Date().toISOString()
      });
    }
  }, [currentAsset, parameters, generatorType, onSave]);

  // Export asset
  const handleExport = useCallback(async (format = 'png') => {
    if (!currentAsset) return;

    try {
      // Create download link
      const link = document.createElement('a');
      link.href = currentAsset.url;
      link.download = `${generatorType}_${Date.now()}.${format}`;
      link.click();

      onExport({
        asset: currentAsset,
        format,
        parameters,
        generatorType
      });
    } catch (err) {
      setError(err.message);
    }
  }, [currentAsset, parameters, generatorType, onExport]);

  // Toggle fullscreen
  const handleToggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < generationHistory.length - 1;

  return (
    <div 
      className={`uw-asset-editor ${theme} ${className} ${isFullscreen ? 'fullscreen' : ''}`}
      ref={containerRef}
      {...props}
    >
      {/* Editor Header */}
      <div className="uw-editor-header">
        <div className="uw-header-left">
          <h2 className="uw-editor-title">
            Asset Editor
            {generatorType && (
              <span className="uw-generator-type"> - {generatorType}</span>
            )}
          </h2>
          
          {connectionStatus.status === 'connected' && (
            <div className="uw-connection-status connected" title="Live preview connected">
              <span className="uw-status-indicator"></span>
              Live Preview
            </div>
          )}
          
          {connectionStatus.status === 'reconnecting' && (
            <div className="uw-connection-status reconnecting" title="Reconnecting...">
              <span className="uw-status-indicator"></span>
              Reconnecting...
            </div>
          )}
        </div>

        <div className="uw-header-right">
          {/* History Controls */}
          <div className="uw-history-controls">
            <button
              type="button"
              className="uw-btn uw-btn-icon"
              onClick={handleUndo}
              disabled={!canUndo || isGenerating}
              title="Undo (Ctrl+Z)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 7v6h6" />
                <path d="M21 17a9 9 0 0 0-15-6.7L3 13" />
              </svg>
            </button>
            
            <button
              type="button"
              className="uw-btn uw-btn-icon"
              onClick={handleRedo}
              disabled={!canRedo || isGenerating}
              title="Redo (Ctrl+Y)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 7v6h-6" />
                <path d="M3 17a9 9 0 0 1 15-6.7L21 13" />
              </svg>
            </button>
          </div>

          {/* Live Preview Toggle */}
          {enableLivePreview && (
            <label className="uw-toggle-switch">
              <input
                type="checkbox"
                checked={livePreviewEnabled}
                onChange={(e) => setLivePreviewEnabled(e.target.checked)}
                disabled={connectionStatus.status !== 'connected'}
              />
              <span className="uw-toggle-slider"></span>
              Live Preview
            </label>
          )}

          {/* Fullscreen Toggle */}
          <button
            type="button"
            className="uw-btn uw-btn-icon"
            onClick={handleToggleFullscreen}
            title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {isFullscreen ? (
                <>
                  <polyline points="16,8 22,8 22,14" />
                  <polyline points="8,16 2,16 2,22" />
                  <polyline points="8,8 2,8 2,2" />
                  <polyline points="16,16 22,16 22,22" />
                </>
              ) : (
                <>
                  <polyline points="15,3 21,3 21,9" />
                  <polyline points="9,21 3,21 3,15" />
                  <polyline points="21,3 14,10" />
                  <polyline points="3,21 10,14" />
                </>
              )}
            </svg>
          </button>

          {/* Close Button */}
          <button
            type="button"
            className="uw-btn uw-btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="uw-editor-error" role="alert">
          <div className="uw-error-content">
            <strong>Error:</strong> {error}
          </div>
          <button
            type="button"
            className="uw-btn uw-btn-icon"
            onClick={() => setError(null)}
            title="Dismiss"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}

      {/* Editor Content */}
      <div className="uw-editor-content">
        {/* Parameter Controls Panel */}
        <div className="uw-parameters-panel">
          {/* Preset Selector */}
          {presets.length > 0 && (
            <div className="uw-preset-selector">
              <label className="uw-label">Presets</label>
              <select
                className="uw-select"
                value={selectedPreset || ''}
                onChange={(e) => {
                  if (e.target.value) {
                    handleLoadPreset(e.target.value);
                  }
                }}
                disabled={isGenerating}
              >
                <option value="">Select a preset...</option>
                {presets.map(preset => (
                  <option key={preset.name} value={preset.name}>
                    {preset.label || preset.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Parameter Controls */}
          <ParameterControls
            parameters={parameters}
            schema={schema}
            onChange={handleParameterChange}
            onReset={handleParameterReset}
            theme={theme}
            disabled={isGenerating}
          />
        </div>

        {/* Preview Panel */}
        <div className="uw-preview-panel">
          <PreviewCanvas
            asset={currentAsset}
            parameters={parameters}
            onGenerate={handleGenerate}
            autoGenerate={livePreviewEnabled}
            theme={theme}
            showControls={true}
          />

          {/* Action Buttons */}
          {currentAsset && (
            <div className="uw-action-buttons">
              <button
                type="button"
                className="uw-btn uw-btn-primary"
                onClick={handleSave}
                disabled={!currentAsset}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                  <polyline points="17,21 17,13 7,13 7,21" />
                  <polyline points="7,3 7,8 15,8" />
                </svg>
                Save Asset
              </button>

              <div className="uw-export-dropdown">
                <button
                  type="button"
                  className="uw-btn uw-btn-secondary"
                  disabled={!currentAsset}
                >
                  Export
                </button>
                <div className="uw-export-menu">
                  <button onClick={() => handleExport('png')}>PNG</button>
                  <button onClick={() => handleExport('jpg')}>JPG</button>
                  <button onClick={() => handleExport('svg')}>SVG</button>
                  <button onClick={() => handleExport('json')}>JSON</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Editor Footer */}
      <div className="uw-editor-footer">
        <div className="uw-footer-info">
          {generationHistory.length > 0 && (
            <span>History: {historyIndex + 1} / {generationHistory.length}</span>
          )}
          
          {currentAsset && (
            <span>Current: {generatorType} - {currentAsset.metadata?.dimensions || 'Unknown size'}</span>
          )}
        </div>

        <div className="uw-footer-actions">
          <button
            type="button"
            className="uw-btn uw-btn-link"
            onClick={() => setParameters(initialParameters)}
          >
            Reset to Initial
          </button>
        </div>
      </div>
    </div>
  );
};

// PropTypes definition
AssetEditor.propTypes = {
  generatorType: PropTypes.string.isRequired,
  initialParameters: PropTypes.object,
  schema: PropTypes.object.isRequired,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  enableLivePreview: PropTypes.bool,
  onSave: PropTypes.func,
  onExport: PropTypes.func,
  onClose: PropTypes.func.isRequired,
  className: PropTypes.string
};

export default AssetEditor;