<template>
  <div :class="['uw-asset-generator', `theme-${theme}`, className]" v-bind="$attrs">
    <!-- Generation Controls -->
    <div class="uw-generator-controls">
      <h2 class="uw-title" id="uw-generator-title">
        Generate Asset
      </h2>
      
      <div class="uw-controls-grid">
        <!-- Asset Type Selection -->
        <div class="uw-form-group">
          <label for="uw-asset-type" class="uw-label">
            Asset Type
          </label>
          <select
            id="uw-asset-type"
            v-model="localParams.type"
            class="uw-select"
            aria-describedby="uw-asset-type-help"
          >
            <option value="parchment">Void Parchment</option>
            <option value="enso">Ink Enso</option>
            <option value="sigil">Eldritch Sigil</option>
            <option value="giraffe">Ink Giraffe</option>
            <option value="kangaroo">Eldritch Kangaroo</option>
          </select>
          <div id="uw-asset-type-help" class="uw-help-text">
            Select the type of asset to generate
          </div>
        </div>

        <!-- Dimensions -->
        <div class="uw-form-group">
          <label for="uw-width" class="uw-label">
            Width
          </label>
          <input
            type="number"
            id="uw-width"
            v-model="localParams.width"
            class="uw-input"
            min="100"
            max="2048"
            step="100"
            aria-describedby="uw-dimensions-help"
          />
        </div>

        <div class="uw-form-group">
          <label for="uw-height" class="uw-label">
            Height
          </label>
          <input
            type="number"
            id="uw-height"
            v-model="localParams.height"
            class="uw-input"
            min="100"
            max="2048"
            step="100"
          />
        </div>

        <div id="uw-dimensions-help" class="uw-help-text">
          Asset dimensions (100-2048 pixels)
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="uw-action-buttons">
        <button
          type="button"
          class="uw-btn uw-btn-primary"
          :disabled="isGenerating"
          @click="generateAsset"
          aria-describedby="uw-generate-help"
        >
          <span v-if="isGenerating" class="uw-spinner" aria-hidden="true"></span>
          {{ isGenerating ? 'Generating...' : 'Generate Asset' }}
        </button>
        
        <button
          type="button"
          class="uw-btn uw-btn-secondary"
          :disabled="isGenerating"
          @click="generateDirectedAsset"
          aria-describedby="uw-directed-help"
        >
          {{ isGenerating ? 'Generating...' : 'Directed Generation' }}
        </button>
      </div>

      <!-- Directed Generation Prompt -->
      <div v-if="showPrompt" class="uw-form-group">
        <label for="uw-prompt" class="uw-label">
          Generation Prompt
        </label>
        <textarea
          id="uw-prompt"
          v-model="prompt"
          class="uw-textarea"
          rows="3"
          placeholder="Describe the asset you want to generate..."
        ></textarea>
      </div>

      <div class="uw-help-text" id="uw-generate-help">
        Generate a random asset with current parameters
      </div>
      <div class="uw-help-text" id="uw-directed-help">
        Generate an asset with LLM guidance
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="uw-error" role="alert" aria-live="polite">
      <h3 class="uw-error-title">Generation Error</h3>
      <p class="uw-error-message">{{ error }}</p>
      <button
        type="button"
        class="uw-btn uw-btn-ghost"
        @click="clearError"
        aria-label="Dismiss error"
      >
        Dismiss
      </button>
    </div>

    <!-- Generated Asset Display -->
    <div v-if="currentAsset" class="uw-asset-display">
      <h3 class="uw-section-title">Generated Asset</h3>
      <div class="uw-asset-container">
        <img
          :src="currentAsset.url"
          :alt="`${formatAssetType(currentAsset.type)} - ${currentAsset.metadata.width} x ${currentAsset.metadata.height}`"
          class="uw-asset-image"
          loading="lazy"
        />
      </div>
      
      <div class="uw-asset-info">
        <div class="uw-asset-metadata">
          <p>
            <strong>Type:</strong> {{ formatAssetType(currentAsset.type) }}
          </p>
          <p>
            <strong>Dimensions:</strong> {{ currentAsset.metadata.width }} × {{ currentAsset.metadata.height }}
          </p>
          <p>
            <strong>Size:</strong> {{ formatFileSize(currentAsset.size) }}
          </p>
          <p>
            <strong>Generated:</strong> {{ formatRelativeTime(currentAsset.createdAt) }}
          </p>
          <p v-if="currentAsset.metadata.prompt">
            <strong>Prompt:</strong> {{ currentAsset.metadata.prompt }}
          </p>
        </div>
        
        <div class="uw-asset-actions">
          <button
            type="button"
            class="uw-btn uw-btn-primary"
            @click="downloadAsset"
            aria-label="Download generated asset"
          >
            Download
          </button>
          <button
            type="button"
            class="uw-btn uw-btn-ghost"
            @click="clearAsset"
            aria-label="Clear generated asset"
          >
            Clear
          </button>
        </div>
      </div>
    </div>

    <!-- Generation History -->
    <div v-if="generationHistory.length > 0" class="uw-history">
      <h3 class="uw-section-title">Recent Generations</h3>
      <div class="uw-history-grid">
        <div
          v-for="asset in generationHistory.slice(0, 5)"
          :key="asset.id"
          class="uw-history-item"
          @click="setCurrentAsset(asset)"
          @keydown.enter="setCurrentAsset(asset)"
          @keydown.space="setCurrentAsset(asset)"
          role="button"
          tabindex="0"
          :aria-label="`View ${formatAssetType(asset.type)} from ${formatRelativeTime(asset.createdAt)}`"
        >
          <img
            :src="asset.url"
            :alt="`${formatAssetType(asset.type)} thumbnail`"
            class="uw-history-thumbnail"
            loading="lazy"
          />
          <div class="uw-history-info">
            <span class="uw-history-type">
              {{ formatAssetType(asset.type) }}
            </span>
            <span class="uw-history-time">
              {{ formatRelativeTime(asset.createdAt) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Region for Accessibility -->
    <div
      class="uw-sr-only"
      aria-live="polite"
      aria-atomic="true"
      id="uw-live-region"
    >
      {{ liveMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { APIClient, APIError } from '../utils/api-client.js';
import { AssetFormatters } from '../utils/formatters.js';
import { AssetValidators } from '../utils/validators.js';

// Props
const props = defineProps({
  apiEndpoint: {
    type: String,
    default: 'http://localhost:8001'
  },
  apiKey: {
    type: String,
    default: ''
  },
  baseUrl: {
    type: String,
    default: 'https://router.requesty.ai/v1'
  },
  theme: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'dark', 'minimal', 'chaotic'].includes(value)
  },
  defaultParams: {
    type: Object,
    default: () => ({})
  },
  className: {
    type: String,
    default: ''
  }
});

// Emits
const emit = defineEmits(['generated', 'error']);

// Reactive state
const isGenerating = ref(false);
const currentAsset = ref(null);
const generationHistory = ref([]);
const error = ref(null);
const prompt = ref('');
const showPrompt = ref(false);
const liveMessage = ref('');

// Local parameters
const localParams = reactive({
  type: props.defaultParams.type || 'enso',
  width: props.defaultParams.width || 800,
  height: props.defaultParams.height || 800
});

// API client
const apiClient = new APIClient({
  endpoint: props.apiEndpoint,
  apiKey: props.apiKey,
  baseUrl: props.baseUrl
});

// Computed
const lastGenerationTime = computed(() => {
  return generationHistory.value.length > 0 ? generationHistory.value[0].createdAt : null;
});

// Methods
const formatAssetType = (type) => AssetFormatters.formatAssetType(type);
const formatFileSize = (bytes) => AssetFormatters.formatFileSize(bytes);
const formatRelativeTime = (date) => AssetFormatters.formatRelativeTime(date);

const validateParams = (params) => {
  return AssetValidators.validateObject(params, {
    type: (value) => AssetValidators.assetType(value, { fieldName: 'Type' }),
    width: (value) => AssetValidators.number(value, {
      fieldName: 'Width',
      min: 100,
      max: 2048,
      integer: true
    }),
    height: (value) => AssetValidators.number(value, {
      fieldName: 'Height',
      min: 100,
      max: 2048,
      integer: true
    })
  });
};

const generateAsset = async () => {
  if (isGenerating.value) return;

  isGenerating.value = true;
  error.value = null;
  liveMessage.value = 'Generating asset, please wait...';

  try {
    const validatedParams = validateParams({ ...localParams });
    const assetBlob = await apiClient.generateAsset(validatedParams.type);
    const assetUrl = APIClient.blobToURL(assetBlob);
    
    const assetData = {
      id: `asset_${Date.now()}`,
      type: validatedParams.type,
      url: assetUrl,
      blob: assetBlob,
      createdAt: new Date(),
      size: assetBlob.size,
      metadata: {
        width: validatedParams.width,
        height: validatedParams.height,
        type: validatedParams.type,
        generatedAt: new Date().toISOString(),
        filename: AssetFormatters.formatDownloadFilename({
          generator_type: validatedParams.type,
          width: validatedParams.width,
          height: validatedParams.height
        })
      }
    };

    currentAsset.value = assetData;
    generationHistory.value.unshift(assetData);
    generationHistory.value = generationHistory.value.slice(0, 10);
    liveMessage.value = `Asset generated: ${formatAssetType(assetData.type)}`;

    emit('generated', assetData);

  } catch (err) {
    const errorMessage = err instanceof APIError 
      ? `API Error: ${err.message}` 
      : `Generation failed: ${err.message}`;
    
    error.value = errorMessage;
    liveMessage.value = `Error: ${errorMessage}`;
    emit('error', err);
  } finally {
    isGenerating.value = false;
  }
};

const generateDirectedAsset = async () => {
  if (isGenerating.value || !prompt.value.trim()) return;

  isGenerating.value = true;
  error.value = null;
  liveMessage.value = 'Generating asset with LLM guidance...';

  try {
    const validatedPrompt = AssetValidators.prompt(prompt.value, { allowEmpty: false });
    const validatedParams = validateParams({ ...localParams });

    const assetBlob = await apiClient.generateDirectedAsset(
      validatedPrompt,
      validatedParams.type
    );
    
    const assetUrl = APIClient.blobToURL(assetBlob);
    
    const assetData = {
      id: `directed_asset_${Date.now()}`,
      type: validatedParams.type,
      url: assetUrl,
      blob: assetBlob,
      createdAt: new Date(),
      size: assetBlob.size,
      metadata: {
        width: validatedParams.width,
        height: validatedParams.height,
        type: validatedParams.type,
        prompt: validatedPrompt,
        generatedAt: new Date().toISOString(),
        filename: AssetFormatters.formatDownloadFilename({
          generator_type: validatedParams.type,
          width: validatedParams.width,
          height: validatedParams.height
        })
      }
    };

    currentAsset.value = assetData;
    generationHistory.value.unshift(assetData);
    generationHistory.value = generationHistory.value.slice(0, 10);
    liveMessage.value = `Asset generated: ${formatAssetType(assetData.type)}`;

    emit('generated', assetData);

  } catch (err) {
    const errorMessage = err instanceof APIError 
      ? `API Error: ${err.message}` 
      : `Directed generation failed: ${err.message}`;
    
    error.value = errorMessage;
    liveMessage.value = `Error: ${errorMessage}`;
    emit('error', err);
  } finally {
    isGenerating.value = false;
  }
};

const downloadAsset = () => {
  if (!currentAsset.value) return;

  const link = document.createElement('a');
  link.href = currentAsset.value.url;
  link.download = currentAsset.value.metadata.filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const clearAsset = () => {
  if (currentAsset.value?.url) {
    APIClient.revokeURL(currentAsset.value.url);
  }
  currentAsset.value = null;
  error.value = null;
};

const clearError = () => {
  error.value = null;
};

const setCurrentAsset = (asset) => {
  currentAsset.value = asset;
};

// Watch for directed generation toggle
const toggleDirectedGeneration = () => {
  showPrompt.value = !showPrompt.value;
  if (!showPrompt.value) {
    prompt.value = '';
  }
};

// Lifecycle
onMounted(() => {
  // Watch for parameter changes
  if (prompt.value.trim()) {
    showPrompt.value = true;
  }
});

onUnmounted(() => {
  // Cleanup object URLs
  if (currentAsset.value?.url) {
    APIClient.revokeURL(currentAsset.value.url);
  }
  generationHistory.value.forEach(asset => {
    if (asset.url) {
      APIClient.revokeURL(asset.url);
    }
  });
});

// Expose methods for parent components
defineExpose({
  generateAsset,
  generateDirectedAsset,
  downloadAsset,
  clearAsset,
  toggleDirectedGeneration
});
</script>

<style scoped>
/* Vue component styles would be scoped to this component */
.uw-asset-generator {
  @apply bg-gray-900 text-white p-6 rounded-lg;
}

.uw-generator-controls {
  @apply space-y-4;
}

.uw-controls-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
}

.uw-form-group {
  @apply space-y-2;
}

.uw-label {
  @apply block text-sm font-medium;
}

.uw-input,
.uw-select,
.uw-textarea {
  @apply w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-white;
}

.uw-input:focus,
.uw-select:focus,
.uw-textarea:focus {
  @apply outline-none border-blue-500 ring-1 ring-blue-500;
}

.uw-action-buttons {
  @apply flex gap-4;
}

.uw-btn {
  @apply px-4 py-2 rounded-md font-medium transition-colors;
}

.uw-btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.uw-btn-secondary {
  @apply bg-gray-600 text-white hover:bg-gray-700;
}

.uw-btn-ghost {
  @apply bg-transparent text-gray-300 hover:bg-gray-700;
}

.uw-error {
  @apply bg-red-900 border border-red-600 rounded-md p-4;
}

.uw-asset-display {
  @apply mt-8;
}

.uw-section-title {
  @apply text-lg font-semibold mb-4;
}

.uw-asset-container {
  @apply bg-gray-800 rounded-lg p-4 mb-4;
}

.uw-asset-image {
  @apply w-full h-auto max-w-md mx-auto;
}

.uw-asset-info {
  @apply flex flex-col sm:flex-row gap-4 justify-between;
}

.uw-asset-metadata {
  @apply text-sm space-y-1;
}

.uw-asset-actions {
  @apply flex gap-2;
}

.uw-history {
  @apply mt-8;
}

.uw-history-grid {
  @apply grid grid-cols-2 md:grid-cols-5 gap-4;
}

.uw-history-item {
  @apply cursor-pointer rounded-lg overflow-hidden border border-gray-600 hover:border-gray-400 transition-colors;
}

.uw-history-thumbnail {
  @apply w-full h-24 object-cover;
}

.uw-history-info {
  @apply p-2 text-xs;
}

.uw-history-type {
  @apply block font-medium;
}

.uw-history-time {
  @apply text-gray-400;
}

.uw-spinner {
  @apply inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2;
}

.uw-help-text {
  @apply text-xs text-gray-400;
}

.uw-sr-only {
  @apply sr-only;
}
</style>