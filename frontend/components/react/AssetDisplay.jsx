/**
 * @fileoverview AssetDisplay React Component
 * @description Component for displaying and interacting with generated assets
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * Component for displaying generated assets with interaction features
 * @param {Object} props - Component props
 * @param {Object} props.asset - Asset object to display
 * @param {string} props.theme - Theme to apply
 * @param {Function} props.onDownload - Download callback
 * @param {Function} props.onShare - Share callback
 * @param {Function} props.onDelete - Delete callback
 * @param {boolean} props.showMetadata - Whether to show metadata
 * @param {boolean} props.allowDownload - Whether to allow download
 * @param {boolean} props.allowShare - Whether to allow sharing
 * @param {boolean} props.allowDelete - Whether to allow deletion
 * @returns {JSX.Element} AssetDisplay component
 */
const AssetDisplay = ({
  asset,
  theme = 'default',
  onDownload = () => {},
  onShare = () => {},
  onDelete = () => {},
  showMetadata = true,
  allowDownload = true,
  allowShare = true,
  allowDelete = false,
  className = '',
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [showFullMetadata, setShowFullMetadata] = useState(false);

  // Reset states when asset changes
  useEffect(() => {
    setIsLoading(true);
    setError(null);
    setImageLoaded(false);
    setShowFullMetadata(false);
  }, [asset]);

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
    setIsLoading(false);
  }, []);

  const handleImageError = useCallback(() => {
    setError('Failed to load image');
    setIsLoading(false);
  }, []);

  const handleDownload = useCallback(() => {
    if (!asset || !allowDownload) return;
    onDownload(asset);
  }, [asset, allowDownload, onDownload]);

  const handleShare = useCallback(() => {
    if (!asset || !allowShare) return;
    onShare(asset);
  }, [asset, allowShare, onShare]);

  const handleDelete = useCallback(() => {
    if (!asset || !allowDelete) return;
    if (window.confirm('Are you sure you want to delete this asset?')) {
      onDelete(asset);
    }
  }, [asset, allowDelete, onDelete]);

  if (!asset) {
    return (
      <div className={`uw-asset-display empty ${theme} ${className}`} {...props}>
        <div className="uw-empty-state">
          <div className="uw-empty-icon">🎨</div>
          <h3 className="uw-empty-title">No Asset Selected</h3>
          <p className="uw-empty-description">
            Generate an asset to see it displayed here
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`uw-asset-display error ${theme} ${className}`} {...props}>
        <div className="uw-error-state">
          <div className="uw-error-icon">⚠️</div>
          <h3 className="uw-error-title">Failed to Load Asset</h3>
          <p className="uw-error-message">{error}</p>
          <button
            type="button"
            className="uw-btn uw-btn-secondary"
            onClick={() => setError(null)}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`uw-asset-display ${theme} ${className}`} {...props}>
      {/* Image Container */}
      <div className="uw-image-container">
        {isLoading && (
          <div className="uw-loading-overlay" role="status" aria-live="polite">
            <div className="uw-spinner" aria-hidden="true"></div>
            <span className="uw-loading-text">Loading asset...</span>
          </div>
        )}
        
        <img
          src={asset.url}
          alt={asset.alt || `${asset.type || 'Asset'} - ${asset.metadata?.dimensions || ''}`}
          className={`uw-asset-image ${imageLoaded ? 'loaded' : ''}`}
          onLoad={handleImageLoad}
          onError={handleImageError}
          loading="lazy"
          style={{
            opacity: imageLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease'
          }}
        />
      </div>

      {/* Asset Actions */}
      <div className="uw-asset-actions">
        <div className="uw-action-buttons">
          {allowDownload && (
            <button
              type="button"
              className="uw-btn uw-btn-primary"
              onClick={handleDownload}
              aria-label="Download asset"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7,10 12,15 17,10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Download
            </button>
          )}

          {allowShare && (
            <button
              type="button"
              className="uw-btn uw-btn-secondary"
              onClick={handleShare}
              aria-label="Share asset"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <circle cx="18" cy="5" r="3" />
                <circle cx="6" cy="12" r="3" />
                <circle cx="18" cy="19" r="3" />
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
              </svg>
              Share
            </button>
          )}

          {allowDelete && (
            <button
              type="button"
              className="uw-btn uw-btn-danger"
              onClick={handleDelete}
              aria-label="Delete asset"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <polyline points="3,6 5,6 21,6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
              Delete
            </button>
          )}
        </div>
      </div>

      {/* Asset Metadata */}
      {showMetadata && asset.metadata && (
        <div className="uw-asset-metadata">
          <button
            type="button"
            className="uw-metadata-toggle"
            onClick={() => setShowFullMetadata(!showFullMetadata)}
            aria-expanded={showFullMetadata}
            aria-controls="uw-metadata-content"
          >
            <span className="uw-metadata-title">
              Asset Details
            </span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              style={{
                transform: showFullMetadata ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease'
              }}
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </button>

          <div
            id="uw-metadata-content"
            className={`uw-metadata-content ${showFullMetadata ? 'expanded' : 'collapsed'}`}
            aria-hidden={!showFullMetadata}
          >
            <dl className="uw-metadata-list">
              {asset.metadata.type && (
                <>
                  <dt>Type</dt>
                  <dd>{asset.metadata.type}</dd>
                </>
              )}
              
              {asset.metadata.dimensions && (
                <>
                  <dt>Dimensions</dt>
                  <dd>{asset.metadata.dimensions}</dd>
                </>
              )}
              
              {asset.metadata.size && (
                <>
                  <dt>Size</dt>
                  <dd>{asset.metadata.size}</dd>
                </>
              )}
              
              {asset.metadata.format && (
                <>
                  <dt>Format</dt>
                  <dd>{asset.metadata.format}</dd>
                </>
              )}
              
              {asset.metadata.generatedAt && (
                <>
                  <dt>Generated</dt>
                  <dd>{new Date(asset.metadata.generatedAt).toLocaleString()}</dd>
                </>
              )}
              
              {asset.metadata.prompt && (
                <>
                  <dt>Prompt</dt>
                  <dd className="uw-prompt-text">{asset.metadata.prompt}</dd>
                </>
              )}
              
              {asset.metadata.model && (
                <>
                  <dt>Model</dt>
                  <dd>{asset.metadata.model}</dd>
                </>
              )}
              
              {asset.tags && asset.tags.length > 0 && (
                <>
                  <dt>Tags</dt>
                  <dd className="uw-tags">
                    {asset.tags.map((tag, index) => (
                      <span key={index} className="uw-tag">
                        {tag}
                      </span>
                    ))}
                  </dd>
                </>
              )}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
};

// PropTypes definition
AssetDisplay.propTypes = {
  asset: PropTypes.shape({
    id: PropTypes.string,
    url: PropTypes.string.isRequired,
    type: PropTypes.string,
    alt: PropTypes.string,
    metadata: PropTypes.shape({
      type: PropTypes.string,
      dimensions: PropTypes.string,
      size: PropTypes.string,
      format: PropTypes.string,
      generatedAt: PropTypes.string,
      prompt: PropTypes.string,
      model: PropTypes.string
    }),
    tags: PropTypes.arrayOf(PropTypes.string)
  }),
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  onDownload: PropTypes.func,
  onShare: PropTypes.func,
  onDelete: PropTypes.func,
  showMetadata: PropTypes.bool,
  allowDownload: PropTypes.bool,
  allowShare: PropTypes.bool,
  allowDelete: PropTypes.bool,
  className: PropTypes.string
};

export default AssetDisplay;