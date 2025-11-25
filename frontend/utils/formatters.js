/**
 * voidussy - Data Formatters
 * Utilities for formatting data for display
 */

class AssetFormatters {
  /**
   * Format file size in human readable format
   * @param {number} bytes - File size in bytes
   * @returns {string} Formatted size string
   */
  static formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }

  /**
   * Format dimensions as readable string
   * @param {number} width - Width in pixels
   * @param {number} height - Height in pixels
   * @returns {string} Formatted dimensions
   */
  static formatDimensions(width, height) {
    return `${width} × ${height}`;
  }

  /**
   * Format date in readable format
   * @param {Date|string} date - Date object or ISO string
   * @param {Object} options - Formatting options
   * @returns {string} Formatted date
   */
  static formatDate(date, options = {}) {
    const d = new Date(date);
    
    const defaults = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    };
    
    return d.toLocaleDateString('en-US', { ...defaults, ...options });
  }

  /**
   * Format relative time (e.g., "2 hours ago")
   * @param {Date|string} date - Date object or ISO string
   * @returns {string} Relative time string
   */
  static formatRelativeTime(date) {
    const now = new Date();
    const target = new Date(date);
    const diffMs = now - target;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);
    
    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
    if (diffHr < 24) return `${diffHr} hour${diffHr === 1 ? '' : 's'} ago`;
    if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`;
    
    return this.formatDate(date, { month: 'short', day: 'numeric', year: 'numeric' });
  }

  /**
   * Format asset type for display
   * @param {string} type - Asset type
   * @returns {string} Display name
   */
  static formatAssetType(type) {
    const typeMap = {
      parchment: 'Void Parchment',
      enso: 'Ink Enso',
      sigil: 'Eldritch Sigil',
      giraffe: 'Ink Giraffe',
      kangaroo: 'Eldritch Kangaroo',
    };
    
    return typeMap[type] || type.charAt(0).toUpperCase() + type.slice(1);
  }

  /**
   * Format generator type for display
   * @param {string} generator - Generator type
   * @returns {string} Display name
   */
  static formatGeneratorType(generator) {
    const generatorMap = {
      'void_parchment': 'Void Parchment',
      'ink_enso': 'Ink Enso',
      'eldritch_sigil': 'Eldritch Sigil',
      'ink_giraffe': 'Ink Giraffe',
      'eldritch_kangaroo': 'Eldritch Kangaroo',
    };
    
    return generatorMap[generator] || generator.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Format tags as comma-separated string
   * @param {Array<string>} tags - Array of tags
   * @param {number} maxTags - Maximum number of tags to show
   * @returns {string} Formatted tags
   */
  static formatTags(tags, maxTags = 5) {
    if (!Array.isArray(tags) || tags.length === 0) return '';
    
    const shownTags = tags.slice(0, maxTags);
    const remaining = tags.length - shownTags.length;
    
    if (remaining > 0) {
      return `${shownTags.join(', ')} +${remaining} more`;
    }
    
    return shownTags.join(', ');
  }

  /**
   * Format download filename
   * @param {Object} asset - Asset object
   * @returns {string} Filename
   */
  static formatDownloadFilename(asset) {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
    const extension = 'png';
    const type = this.formatAssetType(asset.generator_type || asset.type).replace(/\s+/g, '_').toLowerCase();
    
    return `voidussy_${type}_${timestamp}.${extension}`;
  }

  /**
   * Format asset metadata for display
   * @param {Object} asset - Asset object
   * @returns {Object} Formatted metadata
   */
  static formatAssetMetadata(asset) {
    return {
      id: asset.asset_id || asset.id || 'N/A',
      title: asset.title || 'Untitled Asset',
      type: this.formatAssetType(asset.generator_type || asset.type),
      dimensions: this.formatDimensions(asset.width, asset.height),
      size: this.formatFileSize(asset.size_bytes || asset.size || 0),
      format: (asset.format || 'PNG').toUpperCase(),
      created: this.formatRelativeTime(asset.created_at || asset.created),
      tags: this.formatTags(asset.tags || []),
      generator: this.formatGeneratorType(asset.generator_type || asset.generator || 'Unknown'),
    };
  }

  /**
   * Format parameter value for display
   * @param {*} value - Parameter value
   * @param {string} type - Parameter type
   * @returns {string} Formatted value
   */
  static formatParameterValue(value, type = 'string') {
    switch (type) {
      case 'number':
        return typeof value === 'number' ? value.toFixed(2) : value;
      case 'boolean':
        return value ? 'Yes' : 'No';
      case 'array':
        return Array.isArray(value) ? value.join(', ') : String(value);
      case 'color':
        return typeof value === 'string' ? value.toUpperCase() : value;
      default:
        return String(value);
    }
  }

  /**
   * Truncate text to specified length
   * @param {string} text - Text to truncate
   * @param {number} maxLength - Maximum length
   * @param {string} suffix - Suffix to append
   * @returns {string} Truncated text
   */
  static truncateText(text, maxLength = 100, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    return text.slice(0, maxLength - suffix.length) + suffix;
  }

  /**
   * Format progress percentage
   * @param {number} current - Current progress
   * @param {number} total - Total amount
   * @returns {string} Progress string
   */
  static formatProgress(current, total) {
    if (total === 0) return '0%';
    const percentage = Math.round((current / total) * 100);
    return `${percentage}% (${current}/${total})`;
  }

  /**
   * Format duration in seconds to human readable
   * @param {number} seconds - Duration in seconds
   * @returns {string} Formatted duration
   */
  static formatDuration(seconds) {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    
    if (minutes < 60) {
      return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  }

  /**
   * Format validation error message
   * @param {string} field - Field name
   * @param {string} message - Error message
   * @returns {string} Formatted error
   */
  static formatValidationError(field, message) {
    const fieldName = field.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
    return `${fieldName}: ${message}`;
  }

  /**
   * Format search query for highlighting
   * @param {string} text - Text to process
   * @param {string} query - Search query
   * @returns {string} Text with highlighted matches
   */
  static highlightSearchMatches(text, query) {
    if (!query || !text) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  /**
   * Format API endpoint path
   * @param {string} basePath - Base API path
   * @param {string} endpoint - Endpoint
   * @param {Object} params - Query parameters
   * @returns {string} Full URL
   */
  static formatAPIEndpoint(basePath, endpoint, params = {}) {
    const url = new URL(`${basePath}/${endpoint}`.replace(/\/+/g, '/'), window.location.origin);
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, value);
      }
    });
    
    return url.toString();
  }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AssetFormatters };
} else if (typeof window !== 'undefined') {
  window.VoidussyFormatters = { AssetFormatters };
}