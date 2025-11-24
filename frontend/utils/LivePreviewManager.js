/**
 * Unwritten Worlds - Live Preview Manager
 * WebSocket-based real-time preview updates
 * @version 1.0.0
 */

class LivePreviewManager {
  /**
   * Create a new Live Preview Manager
   * @param {Object} config - Configuration object
   * @param {string} config.endpoint - WebSocket endpoint URL
   * @param {string} config.apiKey - API key for authentication
   * @param {Function} config.onPreviewUpdate - Callback when preview updates
   * @param {Function} config.onStatusChange - Callback when connection status changes
   * @param {number} config.reconnectInterval - Reconnection interval in ms
   * @param {number} config.maxReconnectAttempts - Maximum reconnection attempts
   */
  constructor(config = {}) {
    this.endpoint = config.endpoint || 'ws://localhost:8001/ws/preview';
    this.apiKey = config.apiKey || '';
    this.onPreviewUpdate = config.onPreviewUpdate || (() => {});
    this.onStatusChange = config.onStatusChange || (() => {});
    this.reconnectInterval = config.reconnectInterval || 3000;
    this.maxReconnectAttempts = config.maxReconnectAttempts || 10;
    
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.reconnectTimeout = null;
    this.heartbeatInterval = null;
    this.lastHeartbeat = null;
    this.messageQueue = [];
    this.subscribers = new Map();
    this.currentPreviewId = null;
  }

  /**
   * Connect to the WebSocket server
   * @returns {Promise<void>}
   */
  async connect() {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        resolve();
        return;
      }

      try {
        // Build WebSocket URL with auth parameters
        const params = new URLSearchParams();
        if (this.apiKey) {
          params.append('api_key', this.apiKey);
        }

        const wsUrl = `${this.endpoint}?${params}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('🔗 WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.lastHeartbeat = Date.now();
          this.startHeartbeat();
          this.flushMessageQueue();
          this.onStatusChange({ status: 'connected', attempts: this.reconnectAttempts });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('WebSocket message parse error:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.stopHeartbeat();
          this.onStatusChange({ status: 'disconnected', code: event.code, reason: event.reason });
          
          // Attempt to reconnect if not explicitly closed
          if (event.code !== 1000 && event.code !== 1001) {
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.onStatusChange({ status: 'error', error: error.message });
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.messageQueue = [];
    this.onStatusChange({ status: 'disconnected', code: 1000 });
  }

  /**
   * Attempt to reconnect to the server
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.onStatusChange({ 
        status: 'failed', 
        attempts: this.reconnectAttempts,
        maxAttempts: this.maxReconnectAttempts 
      });
      return;
    }

    this.reconnectAttempts++;
    console.log(`🔄 Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.onStatusChange({ 
      status: 'reconnecting', 
      attempts: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts 
    });

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, this.reconnectInterval);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.stopHeartbeat();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
        const now = Date.now();
        
        // Send ping if no message received in last 30 seconds
        if (this.lastHeartbeat && now - this.lastHeartbeat > 30000) {
          this.send({ type: 'ping' });
        }
        
        this.send({ type: 'heartbeat', timestamp: now });
      }
    }, 10000); // Every 10 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Handle incoming WebSocket message
   * @param {Object} data - Message data
   */
  handleMessage(data) {
    this.lastHeartbeat = Date.now();

    switch (data.type) {
      case 'preview_update':
        this.handlePreviewUpdate(data);
        break;
        
      case 'preview_progress':
        this.handlePreviewProgress(data);
        break;
        
      case 'preview_complete':
        this.handlePreviewComplete(data);
        break;
        
      case 'preview_error':
        this.handlePreviewError(data);
        break;
        
      case 'pong':
        // Heartbeat response
        break;
        
      default:
        console.warn('Unknown message type:', data.type);
    }
  }

  /**
   * Handle preview update message
   * @param {Object} data - Preview update data
   */
  handlePreviewUpdate(data) {
    const { previewId, assetUrl, parameters, progress } = data;
    
    // Update current preview ID
    this.currentPreviewId = previewId;
    
    // Notify subscribers
    this.onPreviewUpdate({
      type: 'update',
      previewId,
      assetUrl,
      parameters,
      progress: progress || 0
    });
  }

  /**
   * Handle preview progress message
   * @param {Object} data - Progress data
   */
  handlePreviewProgress(data) {
    const { previewId, progress, stage, estimatedTime } = data;
    
    this.onPreviewUpdate({
      type: 'progress',
      previewId,
      progress,
      stage,
      estimatedTime
    });
  }

  /**
   * Handle preview complete message
   * @param {Object} data - Completion data
   */
  handlePreviewComplete(data) {
    const { previewId, assetUrl, metadata, parameters } = data;
    
    this.onPreviewUpdate({
      type: 'complete',
      previewId,
      assetUrl,
      metadata,
      parameters,
      progress: 100
    });
  }

  /**
   * Handle preview error message
   * @param {Object} data - Error data
   */
  handlePreviewError(data) {
    const { previewId, error, errorDetails } = data;
    
    this.onPreviewUpdate({
      type: 'error',
      previewId,
      error,
      errorDetails
    });
  }

  /**
   * Send message to WebSocket server
   * @param {Object} data - Message data
   */
  send(data) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
      } catch (error) {
        console.error('WebSocket send error:', error);
        this.messageQueue.push(data);
      }
    } else {
      // Queue message for when connection is established
      this.messageQueue.push(data);
    }
  }

  /**
   * Flush queued messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Request a preview update
   * @param {Object} parameters - Generation parameters
   * @param {string} generatorType - Type of generator
   * @param {Object} options - Preview options
   * @returns {string} Preview ID
   */
  requestPreview(parameters, generatorType, options = {}) {
    const previewId = this.generatePreviewId();
    
    const message = {
      type: 'preview_request',
      previewId,
      generatorType,
      parameters,
      options: {
        priority: options.priority || 'normal',
        quality: options.quality || 'preview',
        format: options.format || 'png',
        ...options
      }
    };
    
    this.send(message);
    return previewId;
  }

  /**
   * Cancel a preview request
   * @param {string} previewId - Preview ID to cancel
   */
  cancelPreview(previewId) {
    this.send({
      type: 'preview_cancel',
      previewId
    });
  }

  /**
   * Subscribe to preview updates
   * @param {string} previewId - Preview ID to subscribe to
   * @param {Function} callback - Callback function
   */
  subscribe(previewId, callback) {
    if (!this.subscribers.has(previewId)) {
      this.subscribers.set(previewId, new Set());
    }
    this.subscribers.get(previewId).add(callback);
  }

  /**
   * Unsubscribe from preview updates
   * @param {string} previewId - Preview ID to unsubscribe from
   * @param {Function} callback - Callback function to remove
   */
  unsubscribe(previewId, callback) {
    if (this.subscribers.has(previewId)) {
      this.subscribers.get(previewId).delete(callback);
      if (this.subscribers.get(previewId).size === 0) {
        this.subscribers.delete(previewId);
      }
    }
  }

  /**
   * Generate a unique preview ID
   * @returns {string} Unique preview ID
   */
  generatePreviewId() {
    return `preview_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current connection status
   * @returns {Object} Status information
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      lastHeartbeat: this.lastHeartbeat,
      queuedMessages: this.messageQueue.length,
      currentPreviewId: this.currentPreviewId
    };
  }

  /**
   * Update configuration
   * @param {Object} config - New configuration
   */
  updateConfig(config = {}) {
    if (config.endpoint !== undefined) {
      this.endpoint = config.endpoint;
    }
    if (config.apiKey !== undefined) {
      this.apiKey = config.apiKey;
    }
    if (config.reconnectInterval !== undefined) {
      this.reconnectInterval = config.reconnectInterval;
    }
    if (config.maxReconnectAttempts !== undefined) {
      this.maxReconnectAttempts = config.maxReconnectAttempts;
    }
  }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LivePreviewManager;
} else if (typeof window !== 'undefined') {
  window.LivePreviewManager = LivePreviewManager;
}

export default LivePreviewManager;