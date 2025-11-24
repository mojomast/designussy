/**
 * Unwritten Worlds - Shared JavaScript Library
 * Common functionality extracted from all HTML files
 * Maintains consistent behavior across all pages
 */

(function() {
  'use strict';

  // ============================================================================
  // SVG FILTER INJECTION
  // ============================================================================
  
  const svgFilters = `
    <svg width="0" height="0" style="position: absolute; pointer-events: none;">
      <defs>
        <!-- Filter for rough, ink-like edges -->
        <filter id="brush-stroke" x="-20%" y="-20%" width="140%" height="140%">
          <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="4" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="8" />
          <feGaussianBlur stdDeviation="0.5" result="blurred" />
          <feComposite operator="in" in="SourceGraphic" in2="blurred" result="composite" />
        </filter>

        <!-- Filter for paper texture/grit on text -->
        <filter id="rough-paper">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" result="noise" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" in="noise" result="coloredNoise" />
          <feComposite operator="in" in="SourceGraphic" in2="coloredNoise" result="composite" />
        </filter>
        
        <!-- Ink Spread / Bleed Effect -->
        <filter id="ink-spread">
          <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="4" />
        </filter>

        <!-- Rough Edge Filter -->
        <filter id="rough-edge">
          <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="4" />
        </filter>

        <!-- Ink Bleed Filter (Color Channel Shift) -->
        <filter id="ink-bleed">
          <feTurbulence type="turbulence" baseFrequency="0.05" numOctaves="2" result="turbulence"/>
          <feDisplacementMap in2="turbulence" in="SourceGraphic" scale="3" xChannelSelector="R" yChannelSelector="G"/>
          <feGaussianBlur stdDeviation="0.5" />
        </filter>

        <!-- Eroded/Decayed Filter -->
        <filter id="eroded">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="1" result="noise" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 6 -3" in="noise" result="coloredNoise" />
          <feComposite operator="out" in="SourceGraphic" in2="coloredNoise" result="composite" />
        </filter>
        
        <!-- Glow effect -->
        <filter id="glow">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
    </svg>
  `;

  // Inject SVG filters into DOM
  const injectSVGFilters = () => {
    if (!document.getElementById('unwritten-svg-filters')) {
      const div = document.createElement('div');
      div.innerHTML = svgFilters;
      div.id = 'unwritten-svg-filters';
      document.body.insertBefore(div, document.body.firstChild);
      console.log("Unwritten Worlds: SVG Filters Injected.");
    }
  };

  // ============================================================================
  // EXAMPLE/NAVIGATION MANAGEMENT
  // ============================================================================
  
  const ExampleManager = {
    /**
     * Show a specific example and hide others
     * @param {string|number} exampleId - The ID or number of the example to show
     */
    showExample: (exampleId) => {
      const id = typeof exampleId === 'number' ? 'ex' + exampleId : exampleId;
      
      // Hide all example containers
      document.querySelectorAll('.example-container').forEach(el => {
        el.classList.remove('active');
      });
      
      // Remove active class from all nav buttons
      document.querySelectorAll('.nav-btn').forEach(el => {
        el.classList.remove('active');
      });
      
      // Show selected example
      const target = document.getElementById(id);
      if (target) {
        target.classList.add('active');
      }
      
      // Update nav button
      const btns = document.querySelectorAll('.nav-btn');
      if (btns[id.replace('ex', '') - 1]) {
        btns[id.replace('ex', '') - 1].classList.add('active');
      }
    },
    
    /**
     * Initialize example navigation
     */
    init: () => {
      // Add click handlers to nav buttons
      document.querySelectorAll('.nav-btn').forEach(btn => {
        const onclick = btn.getAttribute('onclick');
        if (onclick && onclick.includes('showExample')) {
          btn.addEventListener('click', (e) => {
            const match = onclick.match(/showExample\((\d+)\)/);
            if (match) {
              ExampleManager.showExample(parseInt(match[1]));
            }
          });
        }
      });
    }
  };

  // ============================================================================
  // API INTERACTION HELPERS
  // ============================================================================
  
  const API = {
    /**
     * Fetch an asset from the generation API
     * @param {string} type - Asset type (parchment/enso/sigil/giraffe/kangaroo)
     * @param {string} endpoint - API endpoint (default: http://localhost:8001)
     * @returns {Promise<Blob>}
     */
    fetchAsset: async (type, endpoint = 'http://localhost:8001') => {
      try {
        const response = await fetch(`${endpoint}/generate/${type}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.blob();
      } catch (error) {
        console.error('API fetchAsset error:', error);
        throw error;
      }
    },
    
    /**
     * Fetch a directed asset using LLM guidance
     * @param {string} prompt - Description of desired asset
     * @param {string} type - Asset type (default: enso)
     * @param {string} model - LLM model to use
     * @param {string} endpoint - API endpoint
     * @param {string} apiKey - API key for authentication
     * @param {string} baseUrl - Base URL for LLM provider
     * @returns {Promise<Blob>}
     */
    fetchDirectedAsset: async (prompt, type = 'enso', model, endpoint = 'http://localhost:8001', apiKey, baseUrl) => {
      try {
        const url = `${endpoint}/generate/directed/${type}?prompt=${encodeURIComponent(prompt)}&model=${encodeURIComponent(model)}`;
        const headers = {};
        if (apiKey) headers['X-API-Key'] = apiKey;
        if (baseUrl) headers['X-Base-Url'] = baseUrl;
        
        const response = await fetch(url, { headers });
        if (!response.ok) {
          let msg = `HTTP ${response.status}`;
          try {
            const err = await response.json();
            msg = err.detail || err.error || JSON.stringify(err);
          } catch (_) {
            try { msg = await response.text(); } catch {}
          }
          throw new Error(msg);
        }
        return await response.blob();
      } catch (error) {
        console.error('API fetchDirectedAsset error:', error);
        throw error;
      }
    },
    
    /**
     * Load available models from API
     * @param {string} endpoint - API endpoint
     * @param {string} apiKey - API key for authentication
     * @param {string} baseUrl - Base URL for LLM provider
     * @returns {Promise<Array>}
     */
    loadModels: async (endpoint = 'http://localhost:8001', apiKey, baseUrl) => {
      try {
        const headers = {};
        if (apiKey) headers['X-API-Key'] = apiKey;
        if (baseUrl) headers['X-Base-Url'] = baseUrl;
        
        const response = await fetch(`${endpoint}/models`, { headers });
        const json = await response.json();
        return json.data || [];
      } catch (error) {
        console.error('API loadModels error:', error);
        return [];
      }
    },
    
    /**
     * Convert blob to object URL
     * @param {Blob} blob - The blob to convert
     * @returns {string} Object URL
     */
    blobToURL: (blob) => {
      return URL.createObjectURL(blob);
    },
    
    /**
     * Revoke object URL to free memory
     * @param {string} url - The object URL to revoke
     */
    revokeURL: (url) => {
      URL.revokeObjectURL(url);
    }
  };

  // ============================================================================
  // ASSET LOADING UTILITIES
  // ============================================================================
  
  const AssetLoader = {
    /**
     * Load and display an asset in a container
     * @param {string} type - Asset type
     * @param {HTMLElement} container - Container to display asset in
     * @param {string} endpoint - API endpoint
     */
    loadAsset: async (type, container, endpoint = 'http://localhost:8001') => {
      if (!container) return;
      
      container.innerHTML = '<div style="color:#d4c5b0; animation: pulseText 1s infinite">GENERATING...</div>';
      
      try {
        const blob = await API.fetchAsset(type, endpoint);
        const url = API.blobToURL(blob);
        container.innerHTML = `<img src="${url}" style="width:100%; height:100%; object-fit:contain; animation: fadeIn 0.5s">`;
      } catch (error) {
        container.innerHTML = `<div style="color:red; padding:20px; text-align:center;">API ERROR: ${error.message}<br><br>Check backend logs/keys.</div>`;
      }
    },
    
    /**
     * Load and display a directed asset
     * @param {string} prompt - Description prompt
     * @param {HTMLElement} container - Container to display asset in
     * @param {string} type - Asset type
     * @param {string} model - LLM model
     * @param {object} settings - API settings
     */
    loadDirectedAsset: async (prompt, container, type = 'enso', model, settings = {}) => {
      if (!container || !prompt) return;
      
      container.innerHTML = '<div style="color:#d4c5b0; animation: pulseText 1s infinite">CONSULTING THE DIRECTOR...</div>';
      
      try {
        const blob = await API.fetchDirectedAsset(
          prompt,
          type,
          model,
          settings.endpoint,
          settings.apiKey,
          settings.baseUrl
        );
        const url = API.blobToURL(blob);
        container.innerHTML = `<img src="${url}" style="width:100%; height:100%; object-fit:contain; animation: fadeIn 0.5s">`;
      } catch (error) {
        container.innerHTML = `<div style="color:red; padding:20px; text-align:center;">API ERROR: ${error.message}<br><br>Check backend logs/keys.</div>`;
      }
    },
    
    /**
     * Load multiple assets into a gallery
     * @param {Array} assets - Array of asset paths
     * @param {HTMLElement} container - Gallery container
     * @param {Function} itemRenderer - Function to render each item
     */
    loadGallery: (assets, container, itemRenderer) => {
      if (!container) return;
      
      container.innerHTML = assets.map(asset => {
        if (itemRenderer) {
          return itemRenderer(asset);
        }
        return `
          <div class="gallery-item">
            <img src="${asset.path}" alt="${asset.label}">
            <div class="gallery-label">${asset.label}</div>
          </div>
        `;
      }).join('');
    }
  };

  // ============================================================================
  // SETTINGS MANAGEMENT (LocalStorage)
  // ============================================================================
  
  const Settings = {
    KEY: 'unwritten_worlds_settings_v1',
    
    /**
     * Get stored settings
     * @returns {object} Settings object
     */
    get: () => {
      try {
        return JSON.parse(localStorage.getItem(Settings.KEY) || '{}');
      } catch {
        return {};
      }
    },
    
    /**
     * Save settings
     * @param {object} settings - Settings to save
     */
    save: (settings) => {
      try {
        localStorage.setItem(Settings.KEY, JSON.stringify(settings));
      } catch (error) {
        console.error('Failed to save settings:', error);
      }
    },
    
    /**
     * Get API settings
     * @returns {object} API settings
     */
    getAPI: () => {
      const settings = Settings.get();
      return {
        apiKey: settings.apiKey || '',
        baseUrl: settings.baseUrl || 'https://router.requesty.ai/v1',
        endpoint: settings.endpoint || 'http://localhost:8001'
      };
    },
    
    /**
     * Save API settings
     * @param {string} apiKey - API key
     * @param {string} baseUrl - Base URL
     * @param {string} endpoint - API endpoint
     */
    saveAPI: (apiKey, baseUrl, endpoint) => {
      const settings = Settings.get();
      settings.apiKey = apiKey;
      settings.baseUrl = baseUrl;
      settings.endpoint = endpoint;
      Settings.save(settings);
    }
  };

  // ============================================================================
  // MODAL MANAGEMENT
  // ============================================================================
  
  const Modal = {
    /**
     * Show a modal dialog
     * @param {string} id - Modal ID
     */
    show: (id) => {
      const modal = document.getElementById(id);
      if (modal) {
        modal.style.display = 'flex';
      }
    },
    
    /**
     * Hide a modal dialog
     * @param {string} id - Modal ID
     */
    hide: (id) => {
      const modal = document.getElementById(id);
      if (modal) {
        modal.style.display = 'none';
      }
    },
    
    /**
     * Initialize API settings modal
     */
    initAPISettings: () => {
      const settings = Settings.getAPI();
      const apiKeyInput = document.getElementById('api-key-input');
      const baseUrlInput = document.getElementById('base-url-input');
      const endpointInput = document.getElementById('endpoint-input');
      
      if (apiKeyInput) apiKeyInput.value = settings.apiKey || '';
      if (baseUrlInput) baseUrlInput.value = settings.baseUrl || 'https://router.requesty.ai/v1';
      if (endpointInput) endpointInput.value = settings.endpoint || 'http://localhost:8001';
    },
    
    /**
     * Save API settings from modal
     */
    saveAPISettings: () => {
      const apiKey = document.getElementById('api-key-input')?.value.trim() || '';
      const baseUrl = document.getElementById('base-url-input')?.value.trim() || 'https://router.requesty.ai/v1';
      const endpoint = document.getElementById('endpoint-input')?.value.trim() || 'http://localhost:8001';
      
      if (!apiKey) {
        alert('Please enter your API key');
        return;
      }
      
      Settings.saveAPI(apiKey, baseUrl, endpoint);
      Modal.hide('api-backdrop');
      
      // Trigger model loading if available
      const loadModels = window.loadModels;
      if (loadModels) loadModels();
    }
  };

  // ============================================================================
  // DOM MANIPULATION HELPERS
  // ============================================================================
  
  const DOM = {
    /**
     * Create an element with attributes
     * @param {string} tag - HTML tag name
     * @param {object} attrs - Attributes to set
     * @param {string|HTMLElement} content - Inner content
     * @returns {HTMLElement}
     */
    create: (tag, attrs = {}, content = '') => {
      const el = document.createElement(tag);
      Object.keys(attrs).forEach(key => {
        el.setAttribute(key, attrs[key]);
      });
      if (typeof content === 'string') {
        el.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        el.appendChild(content);
      }
      return el;
    },
    
    /**
     * Remove all children from an element
     * @param {HTMLElement} el - Parent element
     */
    clear: (el) => {
      if (el) {
        while (el.firstChild) {
          el.removeChild(el.firstChild);
        }
      }
    },
    
    /**
     * Add CSS class to element
     * @param {HTMLElement} el - Element
     * @param {string} className - Class to add
     */
    addClass: (el, className) => {
      if (el && className) {
        el.classList.add(className);
      }
    },
    
    /**
     * Remove CSS class from element
     * @param {HTMLElement} el - Element
     * @param {string} className - Class to remove
     */
    removeClass: (el, className) => {
      if (el && className) {
        el.classList.remove(className);
      }
    },
    
    /**
     * Toggle CSS class on element
     * @param {HTMLElement} el - Element
     * @param {string} className - Class to toggle
     */
    toggleClass: (el, className) => {
      if (el && className) {
        el.classList.toggle(className);
      }
    }
  };

  // ============================================================================
  // ANIMATION UTILITIES
  // ============================================================================
  
  const Animations = {
    /**
     * Wait for specified milliseconds
     * @param {number} ms - Milliseconds to wait
     * @returns {Promise}
     */
    wait: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
    
    /**
     * Randomly flicker an element
     * @param {HTMLElement} element - Element to flicker
     * @param {number} duration - Duration in milliseconds
     */
    glitch: async (element, duration = 500) => {
      if (!element) return;
      const originalOpacity = element.style.opacity;
      const startTime = Date.now();
      
      while (Date.now() - startTime < duration) {
        element.style.opacity = Math.random();
        await Animations.wait(50 + Math.random() * 100);
      }
      element.style.opacity = originalOpacity;
    },
    
    /**
     * Fade in an element
     * @param {HTMLElement} element - Element to fade in
     * @param {number} duration - Duration in milliseconds
     */
    fadeIn: async (element, duration = 500) => {
      if (!element) return;
      element.style.opacity = '0';
      element.style.display = 'block';
      
      await Animations.wait(10);
      element.style.transition = `opacity ${duration}ms ease-in-out`;
      element.style.opacity = '1';
      
      await Animations.wait(duration);
      element.style.transition = '';
    },
    
    /**
     * Fade out an element
     * @param {HTMLElement} element - Element to fade out
     * @param {number} duration - Duration in milliseconds
     */
    fadeOut: async (element, duration = 500) => {
      if (!element) return;
      element.style.transition = `opacity ${duration}ms ease-in-out`;
      element.style.opacity = '0';
      
      await Animations.wait(duration);
      element.style.display = 'none';
      element.style.transition = '';
    }
  };

  // ============================================================================
  // EVENT HANDLING UTILITIES
  // ============================================================================
  
  const Events = {
    /**
     * Add event listener with cleanup
     * @param {HTMLElement} element - Element to listen on
     * @param {string} event - Event type
     * @param {Function} handler - Event handler
     * @returns {Function} Cleanup function
     */
    on: (element, event, handler) => {
      if (!element) return () => {};
      element.addEventListener(event, handler);
      return () => element.removeEventListener(event, handler);
    },
    
    /**
     * Debounce a function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce: (func, wait) => {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },
    
    /**
     * Throttle a function
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in milliseconds
     * @returns {Function} Throttled function
     */
    throttle: (func, limit) => {
      let inThrottle;
      return function(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    }
  };

  // ============================================================================
  // INITIALIZATION
  // ============================================================================
  
  const init = () => {
    // Inject SVG filters
    injectSVGFilters();
    
    // Initialize example manager
    if (document.querySelector('.example-container')) {
      ExampleManager.init();
    }
    
    // Initialize API settings modal if present
    if (document.getElementById('api-backdrop')) {
      Modal.initAPISettings();
    }
    
    console.log('Unwritten Worlds Common JS initialized');
  };

  // ============================================================================
  // EXPORT TO GLOBAL SCOPE
  // ============================================================================
  
  window.Unwritten = {
    API,
    AssetLoader,
    Settings,
    Modal,
    DOM,
    Animations,
    Events,
    ExampleManager,
    init
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();