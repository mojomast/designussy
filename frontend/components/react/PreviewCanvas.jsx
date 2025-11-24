/**
 * @fileoverview PreviewCanvas React Component
 * @description Real-time asset rendering with live preview capabilities
 * @version 1.0.0
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * Component for displaying real-time asset preview
 * @param {Object} props - Component props
 * @param {Object} props.asset - Current asset to display
 * @param {Object} props.parameters - Current generation parameters
 * @param {Function} props.onGenerate - Callback when generation is requested
 * @param {boolean} props.autoGenerate - Whether to auto-generate on parameter change
 * @param {string} props.theme - Theme to apply
 * @param {boolean} props.showControls - Whether to show preview controls
 * @returns {JSX.Element} PreviewCanvas component
 */
const PreviewCanvas = ({
  asset = null,
  parameters = {},
  onGenerate = () => {},
  autoGenerate = false,
  theme = 'default',
  showControls = true,
  className = '',
  ...props
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });
  const [error, setError] = useState(null);
  const [generationQueue, setGenerationQueue] = useState([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);
  
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const generationTimeoutRef = useRef(null);

  // Clean up preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Update preview when asset changes
  useEffect(() => {
    if (asset && asset.url) {
      // Revoke old URL
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      
      // Set new preview
      setPreviewUrl(asset.url);
      setError(null);
      
      // Reset zoom and pan for new asset
      setZoom(1);
      setPan({ x: 0, y: 0 });
    }
  }, [asset]);

  // Debounced parameter change handler for auto-generation
  useEffect(() => {
    if (autoGenerate && Object.keys(parameters).length > 0) {
      // Clear existing timeout
      if (generationTimeoutRef.current) {
        clearTimeout(generationTimeoutRef.current);
      }

      // Add to generation queue
      setGenerationQueue(prev => [...prev, { parameters, timestamp: Date.now() }]);

      // Set new timeout for debounced generation
      generationTimeoutRef.current = setTimeout(() => {
        handleGeneratePreview();
      }, 500); // 500ms debounce
    }

    return () => {
      if (generationTimeoutRef.current) {
        clearTimeout(generationTimeoutRef.current);
      }
    };
  }, [parameters, autoGenerate]);

  // Process generation queue
  const handleGeneratePreview = useCallback(async () => {
    if (isGenerating || isProcessingQueue) return;

    setIsProcessingQueue(true);
    const queue = [...generationQueue];
    setGenerationQueue([]);

    try {
      setIsGenerating(true);
      setError(null);
      
      // Get latest parameters from queue
      const latestParams = queue.length > 0 ? queue[queue.length - 1].parameters : parameters;
      
      await onGenerate(latestParams);
    } catch (err) {
      setError(err.message || 'Failed to generate preview');
      console.error('Preview generation error:', err);
    } finally {
      setIsGenerating(false);
      setIsProcessingQueue(false);
    }
  }, [isGenerating, isProcessingQueue, generationQueue, parameters, onGenerate]);

  // Mouse event handlers for pan and zoom
  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return; // Only left mouse button
    
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
    e.preventDefault();
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;

    const deltaX = e.clientX - lastMousePos.x;
    const deltaY = e.clientY - lastMousePos.y;

    setPan(prev => ({
      x: prev.x + deltaX,
      y: prev.y + deltaY
    }));

    setLastMousePos({ x: e.clientX, y: e.clientY });
    e.preventDefault();
  }, [isDragging, lastMousePos]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    
    const delta = e.deltaY > 0 ? 0.9 : 1.1; // Zoom out or in
    const newZoom = Math.max(0.1, Math.min(10, zoom * delta));
    
    setZoom(newZoom);
  }, [zoom]);

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(10, prev * 1.5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(0.1, prev / 1.5));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  const handleGenerateClick = useCallback(() => {
    handleGeneratePreview();
  }, [handleGeneratePreview]);

  return (
    <div 
      className={`uw-preview-canvas ${theme} ${className}`}
      ref={containerRef}
      {...props}
    >
      {/* Preview Controls */}
      {showControls && (
        <div className="uw-preview-controls">
          <div className="uw-control-group">
            <button
              type="button"
              className="uw-btn uw-btn-icon"
              onClick={handleZoomIn}
              title="Zoom In"
              disabled={isGenerating}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="16" />
                <line x1="8" y1="12" x2="16" y2="12" />
              </svg>
            </button>
            
            <button
              type="button"
              className="uw-btn uw-btn-icon"
              onClick={handleZoomOut}
              title="Zoom Out"
              disabled={isGenerating}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="8" y1="12" x2="16" y2="12" />
              </svg>
            </button>
            
            <button
              type="button"
              className="uw-btn uw-btn-icon"
              onClick={handleZoomReset}
              title="Reset Zoom"
              disabled={isGenerating}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6V12L16 14" />
              </svg>
            </button>
          </div>

          <div className="uw-control-group">
            <button
              type="button"
              className="uw-btn uw-btn-primary"
              onClick={handleGenerateClick}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <span className="uw-spinner" aria-hidden="true"></span>
                  Generating...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3" />
                    <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3" />
                    <path d="M7 12h10" />
                  </svg>
                  Generate Preview
                </>
              )}
            </button>
          </div>

          {autoGenerate && (
            <div className="uw-auto-gen-indicator" title="Auto-generate enabled">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3" />
                <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3" />
                <path d="M7 12h10" />
                <path d="M12 2v20" />
              </svg>
              Auto
            </div>
          )}
        </div>
      )}

      {/* Preview Area */}
      <div className="uw-preview-area">
        <div 
          className="uw-preview-container"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {error && (
            <div className="uw-preview-error" role="alert">
              <div className="uw-error-icon">⚠️</div>
              <div className="uw-error-content">
                <h4>Preview Error</h4>
                <p>{error}</p>
                <button
                  type="button"
                  className="uw-btn uw-btn-secondary"
                  onClick={handleGenerateClick}
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {isGenerating && !previewUrl && (
            <div className="uw-preview-loading">
              <div className="uw-spinner" aria-hidden="true"></div>
              <span>Generating preview...</span>
            </div>
          )}

          {previewUrl && (
            <div 
              className="uw-preview-image-container"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: 'center center'
              }}
            >
              <img
                src={previewUrl}
                alt="Asset preview"
                className="uw-preview-image"
                style={{
                  opacity: isGenerating ? 0.7 : 1,
                  transition: 'opacity 0.3s ease'
                }}
              />
              
              {isGenerating && (
                <div className="uw-preview-overlay">
                  <div className="uw-spinner" aria-hidden="true"></div>
                  <span>Updating...</span>
                </div>
              )}
            </div>
          )}

          {!previewUrl && !isGenerating && !error && (
            <div className="uw-preview-placeholder">
              <div className="uw-placeholder-icon">🎨</div>
              <h3>No Preview Available</h3>
              <p>
                {autoGenerate ? (
                  <>Adjust parameters to see live preview</>
                ) : (
                  <>Click "Generate Preview" to see your asset</>
                )}
              </p>
            </div>
          )}
        </div>

        {/* Preview Info */}
        {previewUrl && (
          <div className="uw-preview-info">
            <div className="uw-info-item">
              <span className="uw-info-label">Zoom:</span>
              <span className="uw-info-value">{Math.round(zoom * 100)}%</span>
            </div>
            
            {asset && asset.metadata && (
              <>
                {asset.metadata.dimensions && (
                  <div className="uw-info-item">
                    <span className="uw-info-label">Size:</span>
                    <span className="uw-info-value">{asset.metadata.dimensions}</span>
                  </div>
                )}
                
                {asset.metadata.format && (
                  <div className="uw-info-item">
                    <span className="uw-info-label">Format:</span>
                    <span className="uw-info-value">{asset.metadata.format}</span>
                  </div>
                )}
              </>
            )}

            {generationQueue.length > 0 && (
              <div className="uw-info-item">
                <span className="uw-info-label">Queue:</span>
                <span className="uw-info-value">{generationQueue.length}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="uw-preview-instructions">
        <details className="uw-instructions-details">
          <summary className="uw-instructions-summary">
            Preview Controls
          </summary>
          <ul className="uw-instructions-list">
            <li><strong>Zoom:</strong> Scroll wheel or use zoom buttons</li>
            <li><strong>Pan:</strong> Click and drag to move the preview</li>
            <li><strong>Reset:</strong> Click reset button to return to default view</li>
            <li><strong>Auto-generate:</strong> When enabled, preview updates automatically as you adjust parameters</li>
          </ul>
        </details>
      </div>
    </div>
  );
};

// PropTypes definition
PreviewCanvas.propTypes = {
  asset: PropTypes.shape({
    url: PropTypes.string,
    metadata: PropTypes.shape({
      dimensions: PropTypes.string,
      format: PropTypes.string
    })
  }),
  parameters: PropTypes.object,
  onGenerate: PropTypes.func,
  autoGenerate: PropTypes.bool,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  showControls: PropTypes.bool,
  className: PropTypes.string
};

export default PreviewCanvas;