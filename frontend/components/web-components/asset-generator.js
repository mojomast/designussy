/**
 * @fileoverview Asset Generator Web Component
 * @description Framework-agnostic web component for generating assets
 * @version 1.0.0
 */

class AssetGenerator extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.isGenerating = false;
    this.generatedAsset = null;
    this.error = null;
    
    // Default configuration
    this.config = {
      apiEndpoint: 'http://localhost:8001',
      apiKey: '',
      baseUrl: 'https://router.requesty.ai/v1',
      theme: 'default',
      defaultParams: {
        type: 'enso',
        width: 800,
        height: 800
      }
    };
  }

  static get observedAttributes() {
    return ['api-endpoint', 'api-key', 'base-url', 'theme', 'asset-type', 'width', 'height'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      this.updateConfig(name, newValue);
    }
  }

  connectedCallback() {
    this.render();
    this.attachEventListeners();
  }

  disconnectedCallback() {
    this.cleanup();
  }

  updateConfig(name, value) {
    const configMap = {
      'api-endpoint': 'apiEndpoint',
      'api-key': 'apiKey',
      'base-url': 'baseUrl',
      'theme': 'theme',
      'asset-type': 'assetType',
      'width': 'width',
      'height': 'height'
    };

    const configKey = configMap[name];
    if (configKey) {
      if (configKey === 'width' || configKey === 'height') {
        this.config.defaultParams[configKey] = parseInt(value) || this.config.defaultParams[configKey];
      } else if (configKey === 'assetType') {
        this.config.defaultParams.type = value;
      } else {
        this.config[configKey] = value;
      }
    }
  }

  render() {
    const styles = this.getStyles();
    const template = this.getTemplate();
    
    this.shadowRoot.innerHTML = `
      <style>${styles}</style>
      ${template}
    `;
  }

  getStyles() {
    return `
      :host {
        display: block;
        font-family: var(--uw-font-body, 'Cormorant Garamond', serif);
        background: var(--uw-bg-color, #0a0a0a);
        color: var(--uw-text-color, #e0e0e0);
        border-radius: var(--uw-radius-md, 8px);
        padding: 1.5rem;
        box-shadow: var(--uw-shadow-md, 0 4px 8px rgba(0,0,0,0.2));
      }

      .uw-generator {
        max-width: 600px;
        margin: 0 auto;
      }

      .uw-title {
        font-family: var(--uw-font-header, 'Cinzel', serif);
        font-size: 1.5rem;
        letter-spacing: 0.2em;
        text-align: center;
        margin-bottom: 1.5rem;
        color: var(--uw-accent-color, #d4c5b0);
      }

      .uw-form-group {
        margin-bottom: 1rem;
      }

      .uw-label {
        display: block;
        margin-bottom: 0.5rem;
        font-family: var(--uw-font-header, 'Cinzel', serif);
        font-size: 0.9rem;
        font-weight: 400;
        color: var(--uw-text-color, #e0e0e0);
      }

      .uw-input,
      .uw-select,
      .uw-textarea {
        width: 100%;
        padding: 0.5rem 0.75rem;
        background: var(--uw-void-dark, #1a1a1a);
        border: 1px solid var(--uw-ghost-grey, #333);
        border-radius: var(--uw-radius-sm, 4px);
        color: var(--uw-text-color, #e0e0e0);
        font-family: var(--uw-font-body, 'Cormorant Garamond', serif);
        transition: all 0.3s ease;
      }

      .uw-input:focus,
      .uw-select:focus,
      .uw-textarea:focus {
        outline: none;
        border-color: var(--uw-accent-color, #d4c5b0);
        box-shadow: 0 0 0 2px rgba(212, 197, 176, 0.2);
      }

      .uw-controls-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
      }

      .uw-action-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-bottom: 1.5rem;
      }

      .uw-btn {
        background: transparent;
        border: 1px solid var(--uw-ghost-grey, #333);
        color: var(--uw-accent-color, #d4c5b0);
        padding: 0.5rem 1rem;
        border-radius: var(--uw-radius-sm, 4px);
        cursor: pointer;
        font-family: var(--uw-font-header, 'Cinzel', serif);
        font-size: 0.9rem;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        white-space: nowrap;
      }

      .uw-btn:hover:not(:disabled) {
        background: var(--uw-ghost-grey, #333);
        border-color: var(--uw-accent-color, #d4c5b0);
        transform: translateY(-1px);
      }

      .uw-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      .uw-btn-primary {
        background: var(--uw-accent-color, #d4c5b0);
        color: var(--uw-void-black, #0a0a0a);
        border-color: var(--uw-accent-color, #d4c5b0);
      }

      .uw-btn-primary:hover:not(:disabled) {
        background: transparent;
        color: var(--uw-accent-color, #d4c5b0);
      }

      .uw-spinner {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        border: 2px solid currentColor;
        border-top: 2px solid transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .uw-error {
        background: rgba(139, 0, 0, 0.2);
        border: 1px solid rgba(139, 0, 0, 0.5);
        border-radius: var(--uw-radius-md, 8px);
        padding: 1rem;
        margin-bottom: 1rem;
        color: #ff6b6b;
      }

      .uw-asset-display {
        text-align: center;
        margin-top: 2rem;
      }

      .uw-asset-image {
        max-width: 100%;
        max-height: 400px;
        border-radius: var(--uw-radius-md, 8px);
        box-shadow: var(--uw-shadow-lg, 0 8px 16px rgba(0,0,0,0.3));
        margin-bottom: 1rem;
      }

      .uw-asset-info {
        font-size: 0.9rem;
        color: var(--uw-ghost-grey, #666);
      }

      .uw-help-text {
        font-size: 0.8rem;
        color: var(--uw-ghost-grey, #666);
        margin-top: 0.5rem;
        text-align: center;
      }

      /* Theme variations */
      :host([theme="dark"]) {
        --uw-bg-color: #000000;
        --uw-void-dark: #0a0a0a;
        --uw-text-color: #f0f0f0;
        --uw-accent-color: #ffd700;
      }

      :host([theme="minimal"]) {
        --uw-bg-color: #0f0f0f;
        --uw-void-dark: #1a1a1a;
        --uw-text-color: #f0f0f0;
        --uw-accent-color: #b8941f;
        --uw-font-body: 'Inter', sans-serif;
      }

      :host([theme="chaotic"]) {
        --uw-bg-color: #000000;
        --uw-void-dark: #0a0a0a;
        --uw-text-color: #ffffff;
        --uw-accent-color: #ff6b35;
        animation: chaosBackground 20s ease-in-out infinite;
      }

      @keyframes chaosBackground {
        0%, 100% { background: linear-gradient(135deg, #000000 0%, #0a0a0a 100%); }
        50% { background: linear-gradient(45deg, #1a0a0a 0%, #000000 100%); }
      }
    `;
  }

  getTemplate() {
    return `
      <div class="uw-generator">
        <h2 class="uw-title">Generate Asset</h2>
        
        <div class="uw-controls-grid">
          <div class="uw-form-group">
            <label for="uw-asset-type" class="uw-label">Asset Type</label>
            <select id="uw-asset-type" class="uw-select">
              <option value="parchment">Void Parchment</option>
              <option value="enso">Ink Enso</option>
              <option value="sigil">Eldritch Sigil</option>
              <option value="giraffe">Ink Giraffe</option>
              <option value="kangaroo">Eldritch Kangaroo</option>
            </select>
          </div>

          <div class="uw-form-group">
            <label for="uw-width" class="uw-label">Width</label>
            <input type="number" id="uw-width" class="uw-input" min="100" max="2048" step="100" value="${this.config.defaultParams.width}">
          </div>

          <div class="uw-form-group">
            <label for="uw-height" class="uw-label">Height</label>
            <input type="number" id="uw-height" class="uw-input" min="100" max="2048" step="100" value="${this.config.defaultParams.height}">
          </div>
        </div>

        <div class="uw-action-buttons">
          <button type="button" class="uw-btn uw-btn-primary" id="uw-generate-btn">
            Generate Asset
          </button>
          <button type="button" class="uw-btn" id="uw-directed-btn">
            Directed Generation
          </button>
        </div>

        <div class="uw-form-group" id="uw-prompt-group" style="display: none;">
          <label for="uw-prompt" class="uw-label">Generation Prompt</label>
          <textarea id="uw-prompt" class="uw-textarea" rows="3" placeholder="Describe the asset you want to generate..."></textarea>
          <div class="uw-help-text">Provide a detailed description for LLM-guided generation</div>
        </div>

        <div id="uw-error" class="uw-error" style="display: none;"></div>

        <div id="uw-asset-display" class="uw-asset-display" style="display: none;">
          <img id="uw-asset-image" class="uw-asset-image" alt="Generated asset">
          <div id="uw-asset-info" class="uw-asset-info"></div>
          <button type="button" class="uw-btn uw-btn-primary" id="uw-download-btn">Download</button>
        </div>
      </div>
    `;
  }

  attachEventListeners() {
    const generateBtn = this.shadowRoot.getElementById('uw-generate-btn');
    const directedBtn = this.shadowRoot.getElementById('uw-directed-btn');
    const downloadBtn = this.shadowRoot.getElementById('uw-download-btn');

    if (generateBtn) {
      generateBtn.addEventListener('click', () => this.generateAsset());
    }

    if (directedBtn) {
      directedBtn.addEventListener('click', () => this.toggleDirectedGeneration());
    }

    if (downloadBtn) {
      downloadBtn.addEventListener('click', () => this.downloadAsset());
    }

    // Initialize form values
    this.initializeFormValues();
  }

  initializeFormValues() {
    const assetTypeSelect = this.shadowRoot.getElementById('uw-asset-type');
    if (assetTypeSelect && this.config.defaultParams.type) {
      assetTypeSelect.value = this.config.defaultParams.type;
    }
  }

  async generateAsset() {
    if (this.isGenerating) return;

    this.isGenerating = true;
    this.clearError();
    this.updateButtonState();

    try {
      const params = this.getGenerationParams();
      const assetBlob = await this.fetchAsset(params.type);
      
      if (!assetBlob) {
        throw new Error('No asset data received');
      }

      const assetUrl = URL.createObjectURL(assetBlob);
      const assetData = {
        url: assetUrl,
        blob: assetBlob,
        type: params.type,
        width: params.width,
        height: params.height,
        metadata: {
          dimensions: `${params.width} × ${params.height}`,
          type: params.type,
          generatedAt: new Date().toISOString()
        }
      };

      this.displayAsset(assetData);
      this.dispatchEvent(new CustomEvent('asset-generated', {
        detail: assetData
      }));

    } catch (error) {
      this.showError(`Generation failed: ${error.message}`);
      this.dispatchEvent(new CustomEvent('asset-generation-error', {
        detail: { error: error.message }
      }));
    } finally {
      this.isGenerating = false;
      this.updateButtonState();
    }
  }

  async fetchAsset(type) {
    const response = await fetch(`${this.config.apiEndpoint}/generate/${type}`);
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.error || errorMessage;
      } catch {
        try {
          errorMessage = await response.text();
        } catch {}
      }
      throw new Error(errorMessage);
    }

    return await response.blob();
  }

  getGenerationParams() {
    const assetType = this.shadowRoot.getElementById('uw-asset-type').value;
    const width = parseInt(this.shadowRoot.getElementById('uw-width').value) || 800;
    const height = parseInt(this.shadowRoot.getElementById('uw-height').value) || 800;

    return { type: assetType, width, height };
  }

  displayAsset(assetData) {
    const assetDisplay = this.shadowRoot.getElementById('uw-asset-display');
    const assetImage = this.shadowRoot.getElementById('uw-asset-image');
    const assetInfo = this.shadowRoot.getElementById('uw-asset-info');

    if (assetDisplay && assetImage && assetInfo) {
      assetImage.src = assetData.url;
      assetImage.alt = `${assetData.type} - ${assetData.metadata.dimensions}`;
      
      assetInfo.innerHTML = `
        <strong>Type:</strong> ${this.formatAssetType(assetData.type)}<br>
        <strong>Dimensions:</strong> ${assetData.metadata.dimensions}<br>
        <strong>Generated:</strong> ${new Date().toLocaleString()}
      `;

      assetDisplay.style.display = 'block';
      this.generatedAsset = assetData;
    }
  }

  formatAssetType(type) {
    const typeMap = {
      parchment: 'Void Parchment',
      enso: 'Ink Enso',
      sigil: 'Eldritch Sigil',
      giraffe: 'Ink Giraffe',
      kangaroo: 'Eldritch Kangaroo'
    };
    return typeMap[type] || type.charAt(0).toUpperCase() + type.slice(1);
  }

  downloadAsset() {
    if (!this.generatedAsset) return;

    const link = document.createElement('a');
    link.href = this.generatedAsset.url;
    link.download = `voidussy_${this.generatedAsset.type}_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  toggleDirectedGeneration() {
    const promptGroup = this.shadowRoot.getElementById('uw-prompt-group');
    if (promptGroup) {
      const isVisible = promptGroup.style.display !== 'none';
      promptGroup.style.display = isVisible ? 'none' : 'block';
    }
  }

  updateButtonState() {
    const generateBtn = this.shadowRoot.getElementById('uw-generate-btn');
    const directedBtn = this.shadowRoot.getElementById('uw-directed-btn');
    
    if (generateBtn && directedBtn) {
      generateBtn.innerHTML = this.isGenerating ? 
        '<span class="uw-spinner" aria-hidden="true"></span> Generating...' : 
        'Generate Asset';
      
      directedBtn.disabled = this.isGenerating;
      generateBtn.disabled = this.isGenerating;
    }
  }

  showError(message) {
    const errorDiv = this.shadowRoot.getElementById('uw-error');
    if (errorDiv) {
      errorDiv.textContent = message;
      errorDiv.style.display = 'block';
    }
    this.error = message;
  }

  clearError() {
    const errorDiv = this.shadowRoot.getElementById('uw-error');
    if (errorDiv) {
      errorDiv.style.display = 'none';
      errorDiv.textContent = '';
    }
    this.error = null;
  }

  cleanup() {
    if (this.generatedAsset && this.generatedAsset.url) {
      URL.revokeObjectURL(this.generatedAsset.url);
    }
  }

  // Public API methods
  generate() {
    return this.generateAsset();
  }

  clear() {
    const assetDisplay = this.shadowRoot.getElementById('uw-asset-display');
    if (assetDisplay) {
      assetDisplay.style.display = 'none';
    }
    this.clearError();
    this.cleanup();
    this.generatedAsset = null;
  }

  setConfig(config) {
    this.config = { ...this.config, ...config };
  }
}

// Register the custom element
if (!customElements.get('uw-asset-generator')) {
  customElements.define('uw-asset-generator', AssetGenerator);
}