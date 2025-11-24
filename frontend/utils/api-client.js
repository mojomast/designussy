/**
 * Unwritten Worlds - API Client Utility
 * Handles communication with the generation API
 */

class APIError extends Error {
  constructor(message, status, details = {}) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }
}

class APIClient {
  /**
   * Create a new API client
   * @param {Object} config - Configuration object
   * @param {string} config.endpoint - API endpoint URL
   * @param {string} config.apiKey - API key for authentication
   * @param {string} config.baseUrl - Base URL for LLM provider
   */
  constructor(config = {}) {
    this.endpoint = config.endpoint || 'http://localhost:8001';
    this.apiKey = config.apiKey || '';
    this.baseUrl = config.baseUrl || 'https://router.requesty.ai/v1';
    this.timeout = config.timeout || 30000;
  }

  /**
   * Get request headers
   * @returns {Object} Headers object
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    
    if (this.baseUrl && this.baseUrl !== 'https://router.requesty.ai/v1') {
      headers['X-Base-Url'] = this.baseUrl;
    }
    
    return headers;
  }

  /**
   * Make a fetch request with timeout and error handling
   * @param {string} url - Request URL
   * @param {Object} options - Fetch options
   * @returns {Promise<Response>}
   */
  async request(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.getHeaders(),
          ...options.headers,
        },
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails = {};
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.error || errorMessage;
          errorDetails = errorData;
        } catch {
          try {
            errorMessage = await response.text();
          } catch {}
        }
        
        throw new APIError(errorMessage, response.status, errorDetails);
      }
      
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new APIError('Request timeout', 408);
      }
      
      if (error instanceof APIError) {
        throw error;
      }
      
      throw new APIError(`Network error: ${error.message}`, 0);
    }
  }

  /**
   * Generate an asset
   * @param {string} type - Asset type (parchment/enso/sigil/giraffe/kangaroo)
   * @returns {Promise<Blob>}
   */
  async generateAsset(type) {
    const response = await this.request(`${this.endpoint}/generate/${type}`, {
      method: 'GET',
    });
    
    return await response.blob();
  }

  /**
   * Generate an asset with LLM guidance
   * @param {string} prompt - Description prompt
   * @param {string} type - Asset type (default: enso)
   * @param {Object} options - Generation options
   * @returns {Promise<Blob>}
   */
  async generateDirectedAsset(prompt, type = 'enso', options = {}) {
    const params = new URLSearchParams({
      prompt,
      model: options.model || '',
    });
    
    const url = `${this.endpoint}/generate/directed/${type}?${params}`;
    
    const response = await this.request(url, {
      method: 'GET',
    });
    
    return await response.blob();
  }

  /**
   * Load available models
   * @returns {Promise<Array>}
   */
  async loadModels() {
    const response = await this.request(`${this.endpoint}/models`);
    const data = await response.json();
    return data.data || [];
  }

  /**
   * Get health status
   * @returns {Promise<Object>}
   */
  async getHealth() {
    const response = await this.request(`${this.endpoint}/health`);
    return await response.json();
  }

  /**
   * Update configuration
   * @param {Object} config - New configuration
   */
  updateConfig(config = {}) {
    if (config.endpoint !== undefined) this.endpoint = config.endpoint;
    if (config.apiKey !== undefined) this.apiKey = config.apiKey;
    if (config.baseUrl !== undefined) this.baseUrl = config.baseUrl;
    if (config.timeout !== undefined) this.timeout = config.timeout;
  }

  /**
   * Convert blob to object URL
   * @param {Blob} blob - The blob to convert
   * @returns {string} Object URL
   */
  static blobToURL(blob) {
    return URL.createObjectURL(blob);
  }

  /**
   * Revoke object URL to free memory
   * @param {string} url - The object URL to revoke
   */
  static revokeURL(url) {
    URL.revokeObjectURL(url);
  }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { APIClient, APIError };
} else if (typeof window !== 'undefined') {
  window.UnwrittenAPI = { APIClient, APIError };
}