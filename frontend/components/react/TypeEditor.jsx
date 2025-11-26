/**
 * @fileoverview TypeEditor React Component
 * @description Component for editing element type definitions with JSON schema validation
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { APIClient } from '../utils/api-client.js';

/**
 * Component for editing element type definitions with JSON schema validation
 * @param {Object} props - Component props
 * @param {Object} props.elementType - Element type to edit (null for new types)
 * @param {Function} props.onTypeSave - Callback when type is saved
 * @param {Function} props.onTypeValidate - Callback for validation results
 * @param {string} props.theme - Theme to apply
 * @param {boolean} props.readOnly - Whether the editor is read-only
 * @returns {JSX.Element} TypeEditor component
 */
const TypeEditor = ({
  elementType = null,
  onTypeSave = () => {},
  onTypeValidate = () => {},
  theme = 'dark',
  readOnly = false,
  className = '',
  ...props
}) => {
  const [typeDefinition, setTypeDefinition] = useState(null);
  const [originalType, setOriginalType] = useState(null);
  const [activeTab, setActiveTab] = useState('basic'); // 'basic', 'schema', 'variants', 'diversity', 'json'
  const [validationResults, setValidationResults] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [isValidating, setIsValidating] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [jsonEditorContent, setJsonEditorContent] = useState('');
  const [jsonParseError, setJsonParseError] = useState(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importContent, setImportContent] = useState('');
  const [changeHistory, setChangeHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [apiClient] = useState(() => new APIClient({ endpoint: 'http://localhost:8001' }));
  const jsonEditorRef = useRef(null);

  // Initialize type definition
  useEffect(() => {
    if (elementType) {
      setTypeDefinition({ ...elementType });
      setOriginalType({ ...elementType });
      setJsonEditorContent(JSON.stringify(elementType, null, 2));
      setHasUnsavedChanges(false);
    } else {
      const newType = {
        id: '',
        name: '',
        description: '',
        category: '',
        tags: [],
        render_strategy: {
          engine: 'pil',
          generator_name: ''
        },
        param_schema: {
          type: 'object',
          properties: {},
          required: []
        },
        variants: [],
        diversity_config: {
          strategy: 'jitter',
          target_diversity_score: 0.7,
          max_variations: 100
        },
        version: '1.0.0',
        is_active: true
      };
      setTypeDefinition(newType);
      setOriginalType(null);
      setJsonEditorContent(JSON.stringify(newType, null, 2));
      setHasUnsavedChanges(true);
    }
  }, [elementType]);

  // Track changes
  useEffect(() => {
    if (typeDefinition) {
      const currentStr = JSON.stringify(typeDefinition);
      const originalStr = JSON.stringify(originalType || {});
      setHasUnsavedChanges(currentStr !== originalStr);
    }
  }, [typeDefinition, originalType]);

  // Auto-validate on changes
  useEffect(() => {
    if (typeDefinition) {
      validateType();
    }
  }, [typeDefinition]);

  const validateType = useCallback(async () => {
    if (!typeDefinition) return;
    
    setIsValidating(true);
    try {
      const response = await fetch('http://localhost:8001/llm/validate-type', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(typeDefinition)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setValidationResults(data.validation);
        setValidationErrors(data.validation?.issues || []);
        onTypeValidate(data.validation);
      }
    } catch (err) {
      console.error('Validation failed:', err);
      setValidationErrors(['Validation request failed']);
    } finally {
      setIsValidating(false);
    }
  }, [typeDefinition, onTypeValidate]);

  const handleBasicFieldChange = useCallback((field, value) => {
    const newType = { ...typeDefinition, [field]: value };
    setTypeDefinition(newType);
    addToHistory(newType);
  }, [typeDefinition]);

  const handleNestedFieldChange = useCallback((section, field, value) => {
    const newType = {
      ...typeDefinition,
      [section]: {
        ...typeDefinition[section],
        [field]: value
      }
    };
    setTypeDefinition(newType);
    addToHistory(newType);
  }, [typeDefinition]);

  const handleParameterSchemaChange = useCallback((action, paramName, paramData = null) => {
    if (!typeDefinition.param_schema) return;
    
    const newSchema = { ...typeDefinition.param_schema };
    
    switch (action) {
      case 'add':
        newSchema.properties = {
          ...newSchema.properties,
          [paramName]: {
            type: 'string',
            default: '',
            description: '',
            ...paramData
          }
        };
        break;
      case 'remove':
        delete newSchema.properties[paramName];
        newSchema.required = newSchema.required.filter(req => req !== paramName);
        break;
      case 'update':
        newSchema.properties = {
          ...newSchema.properties,
          [paramName]: {
            ...newSchema.properties[paramName],
            ...paramData
          }
        };
        break;
      case 'toggle_required':
        if (newSchema.required.includes(paramName)) {
          newSchema.required = newSchema.required.filter(req => req !== paramName);
        } else {
          newSchema.required = [...newSchema.required, paramName];
        }
        break;
    }
    
    const newType = { ...typeDefinition, param_schema: newSchema };
    setTypeDefinition(newType);
    addToHistory(newType);
  }, [typeDefinition]);

  const addToHistory = useCallback((newType) => {
    setChangeHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(JSON.stringify(newType));
      return newHistory.slice(-20); // Keep last 20 changes
    });
    setHistoryIndex(prev => Math.min(prev + 1, 19));
  }, [historyIndex]);

  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      const typeStr = changeHistory[newIndex];
      setTypeDefinition(JSON.parse(typeStr));
    }
  }, [historyIndex, changeHistory]);

  const handleRedo = useCallback(() => {
    if (historyIndex < changeHistory.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      const typeStr = changeHistory[newIndex];
      setTypeDefinition(JSON.parse(typeStr));
    }
  }, [historyIndex, changeHistory]);

  const handleJsonEditorChange = useCallback((content) => {
    setJsonEditorContent(content);
    
    try {
      const parsed = JSON.parse(content);
      setJsonParseError(null);
      setTypeDefinition(parsed);
      addToHistory(parsed);
    } catch (err) {
      setJsonParseError(`JSON Parse Error: ${err.message}`);
    }
  }, [addToHistory]);

  const handleSave = useCallback(async () => {
    if (!typeDefinition) return;
    
    setSaveLoading(true);
    try {
      const endpoint = originalType ? `types/${typeDefinition.id}` : 'types';
      const method = originalType ? 'PUT' : 'POST';
      
      const response = await fetch(`http://localhost:8001/${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(typeDefinition)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setOriginalType(data.type);
        setHasUnsavedChanges(false);
        onTypeSave(data.type);
      } else {
        throw new Error(data.error || 'Save failed');
      }
    } catch (err) {
      setValidationErrors([err.message]);
    } finally {
      setSaveLoading(false);
    }
  }, [typeDefinition, originalType, onTypeSave]);

  const handleExport = useCallback(() => {
    if (!typeDefinition) return;
    
    const exportData = {
      type: typeDefinition,
      exported_at: new Date().toISOString(),
      version: '1.0.0'
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${typeDefinition.id || typeDefinition.name || 'element-type'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [typeDefinition]);

  const handleImport = useCallback(() => {
    try {
      const imported = JSON.parse(importContent);
      setTypeDefinition(imported);
      setJsonEditorContent(JSON.stringify(imported, null, 2));
      setImportDialogOpen(false);
      setImportContent('');
      addToHistory(imported);
    } catch (err) {
      setJsonParseError(`Import Error: ${err.message}`);
    }
  }, [importContent, addToHistory]);

  const handleReset = useCallback(() => {
    if (originalType) {
      setTypeDefinition({ ...originalType });
      setJsonEditorContent(JSON.stringify(originalType, null, 2));
    }
  }, [originalType]);

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < changeHistory.length - 1;

  if (!typeDefinition) {
    return (
      <div className={`uw-type-editor ${theme} ${className}`} {...props}>
        <div className="uw-loading-state">
          <p>Loading type editor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`uw-type-editor ${theme} ${className}`} {...props}>
      {/* Editor Header */}
      <div className="uw-editor-header">
        <div className="uw-header-left">
          <h2 className="uw-editor-title">
            {originalType ? 'Edit Type' : 'Create New Type'}
          </h2>
          <span className="uw-type-id">
            {typeDefinition.id && `ID: ${typeDefinition.id}`}
          </span>
          {hasUnsavedChanges && (
            <span className="uw-unsaved-indicator">Unsaved changes</span>
          )}
        </div>

        <div className="uw-header-right">
          {/* History Controls */}
          <div className="uw-history-controls">
            <button
              className="uw-btn uw-btn-icon"
              onClick={handleUndo}
              disabled={!canUndo}
              title="Undo (Ctrl+Z)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 7v6h6" />
                <path d="M21 17a9 9 0 0 0-15-6.7L3 13" />
              </svg>
            </button>
            
            <button
              className="uw-btn uw-btn-icon"
              onClick={handleRedo}
              disabled={!canRedo}
              title="Redo (Ctrl+Y)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 7v6h-6" />
                <path d="M3 17a9 9 0 0 1 15-6.7L21 13" />
              </svg>
            </button>
          </div>

          {/* Validation Status */}
          {isValidating ? (
            <div className="uw-validation-status validating">
              <div className="uw-spinner-small"></div>
              Validating...
            </div>
          ) : validationResults?.is_valid ? (
            <div className="uw-validation-status valid">
              ✓ Valid
            </div>
          ) : (
            <div className="uw-validation-status invalid">
              ✗ {validationErrors.length} issues
            </div>
          )}

          {/* Action Buttons */}
          <button
            className="uw-btn uw-btn-secondary"
            onClick={() => setImportDialogOpen(true)}
            disabled={readOnly}
          >
            Import
          </button>
          
          <button
            className="uw-btn uw-btn-secondary"
            onClick={handleExport}
          >
            Export
          </button>
          
          {originalType && (
            <button
              className="uw-btn uw-btn-secondary"
              onClick={handleReset}
              disabled={readOnly}
            >
              Reset
            </button>
          )}
          
          <button
            className="uw-btn uw-btn-primary"
            onClick={handleSave}
            disabled={readOnly || saveLoading || !hasUnsavedChanges}
          >
            {saveLoading ? 'Saving...' : 'Save Type'}
          </button>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="uw-validation-errors" role="alert">
          <h4 className="uw-error-title">Validation Issues:</h4>
          <ul className="uw-error-list">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* JSON Parse Error */}
      {jsonParseError && (
        <div className="uw-json-error" role="alert">
          {jsonParseError}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="uw-tab-navigation">
        <button
          className={`uw-tab ${activeTab === 'basic' ? 'active' : ''}`}
          onClick={() => setActiveTab('basic')}
        >
          Basic Info
        </button>
        <button
          className={`uw-tab ${activeTab === 'schema' ? 'active' : ''}`}
          onClick={() => setActiveTab('schema')}
        >
          Parameter Schema
        </button>
        <button
          className={`uw-tab ${activeTab === 'variants' ? 'active' : ''}`}
          onClick={() => setActiveTab('variants')}
        >
          Variants
        </button>
        <button
          className={`uw-tab ${activeTab === 'diversity' ? 'active' : ''}`}
          onClick={() => setActiveTab('diversity')}
        >
          Diversity Config
        </button>
        <button
          className={`uw-tab ${activeTab === 'json' ? 'active' : ''}`}
          onClick={() => setActiveTab('json')}
        >
          JSON Editor
        </button>
      </div>

      {/* Tab Content */}
      <div className="uw-tab-content">
        {/* Basic Information Tab */}
        {activeTab === 'basic' && (
          <div className="uw-tab-panel">
            <div className="uw-form-grid">
              <div className="uw-form-group">
                <label className="uw-label">Type ID</label>
                <input
                  type="text"
                  className="uw-input"
                  value={typeDefinition.id || ''}
                  onChange={(e) => handleBasicFieldChange('id', e.target.value)}
                  disabled={readOnly || !!originalType}
                />
                <div className="uw-help-text">Unique identifier for this type</div>
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Name</label>
                <input
                  type="text"
                  className="uw-input"
                  value={typeDefinition.name || ''}
                  onChange={(e) => handleBasicFieldChange('name', e.target.value)}
                  disabled={readOnly}
                />
              </div>

              <div className="uw-form-group full-width">
                <label className="uw-label">Description</label>
                <textarea
                  className="uw-textarea"
                  rows={3}
                  value={typeDefinition.description || ''}
                  onChange={(e) => handleBasicFieldChange('description', e.target.value)}
                  disabled={readOnly}
                />
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Category</label>
                <input
                  type="text"
                  className="uw-input"
                  value={typeDefinition.category || ''}
                  onChange={(e) => handleBasicFieldChange('category', e.target.value)}
                  disabled={readOnly}
                />
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Tags (comma-separated)</label>
                <input
                  type="text"
                  className="uw-input"
                  value={(typeDefinition.tags || []).join(', ')}
                  onChange={(e) => handleBasicFieldChange('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  disabled={readOnly}
                />
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Generator Name</label>
                <input
                  type="text"
                  className="uw-input"
                  value={typeDefinition.render_strategy?.generator_name || ''}
                  onChange={(e) => handleNestedFieldChange('render_strategy', 'generator_name', e.target.value)}
                  disabled={readOnly}
                />
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Engine</label>
                <select
                  className="uw-select"
                  value={typeDefinition.render_strategy?.engine || 'pil'}
                  onChange={(e) => handleNestedFieldChange('render_strategy', 'engine', e.target.value)}
                  disabled={readOnly}
                >
                  <option value="pil">PIL</option>
                  <option value="opencv">OpenCV</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div className="uw-form-group">
                <label className="uw-label">Version</label>
                <input
                  type="text"
                  className="uw-input"
                  value={typeDefinition.version || '1.0.0'}
                  onChange={(e) => handleBasicFieldChange('version', e.target.value)}
                  disabled={readOnly}
                />
              </div>

              <div className="uw-form-group">
                <label className="uw-checkbox">
                  <input
                    type="checkbox"
                    checked={typeDefinition.is_active || false}
                    onChange={(e) => handleBasicFieldChange('is_active', e.target.checked)}
                    disabled={readOnly}
                  />
                  <span className="uw-checkbox-label">Active</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Parameter Schema Tab */}
        {activeTab === 'schema' && (
          <div className="uw-tab-panel">
            <div className="uw-schema-editor">
              {/* Parameter List */}
              <div className="uw-parameter-list">
                <h3 className="uw-section-title">Parameters</h3>
                
                {Object.entries(typeDefinition.param_schema?.properties || {}).map(([paramName, paramSchema]) => (
                  <div key={paramName} className="uw-parameter-item">
                    <div className="uw-parameter-header">
                      <h4 className="uw-parameter-name">{paramName}</h4>
                      <div className="uw-parameter-actions">
                        <button
                          className="uw-btn uw-btn-small uw-btn-secondary"
                          onClick={() => handleParameterSchemaChange('toggle_required', paramName)}
                          disabled={readOnly}
                        >
                          {typeDefinition.param_schema.required?.includes(paramName) ? 'Required' : 'Optional'}
                        </button>
                        <button
                          className="uw-btn uw-btn-small uw-btn-secondary"
                          onClick={() => handleParameterSchemaChange('remove', paramName)}
                          disabled={readOnly}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    
                    <div className="uw-parameter-fields">
                      <div className="uw-form-row">
                        <div className="uw-form-group">
                          <label className="uw-label">Type</label>
                          <select
                            className="uw-select"
                            value={paramSchema.type}
                            onChange={(e) => handleParameterSchemaChange('update', paramName, { type: e.target.value })}
                            disabled={readOnly}
                          >
                            <option value="string">String</option>
                            <option value="number">Number</option>
                            <option value="integer">Integer</option>
                            <option value="boolean">Boolean</option>
                            <option value="color">Color</option>
                          </select>
                        </div>
                        
                        <div className="uw-form-group">
                          <label className="uw-label">Default</label>
                          <input
                            type="text"
                            className="uw-input"
                            value={paramSchema.default || ''}
                            onChange={(e) => handleParameterSchemaChange('update', paramName, { default: e.target.value })}
                            disabled={readOnly}
                          />
                        </div>
                      </div>
                      
                      <div className="uw-form-group">
                        <label className="uw-label">Description</label>
                        <input
                          type="text"
                          className="uw-input"
                          value={paramSchema.description || ''}
                          onChange={(e) => handleParameterSchemaChange('update', paramName, { description: e.target.value })}
                          disabled={readOnly}
                        />
                      </div>
                      
                      {/* Type-specific fields */}
                      {(paramSchema.type === 'number' || paramSchema.type === 'integer') && (
                        <div className="uw-form-row">
                          <div className="uw-form-group">
                            <label className="uw-label">Minimum</label>
                            <input
                              type="number"
                              className="uw-input"
                              value={paramSchema.minimum || ''}
                              onChange={(e) => handleParameterSchemaChange('update', paramName, { minimum: parseFloat(e.target.value) })}
                              disabled={readOnly}
                            />
                          </div>
                          
                          <div className="uw-form-group">
                            <label className="uw-label">Maximum</label>
                            <input
                              type="number"
                              className="uw-input"
                              value={paramSchema.maximum || ''}
                              onChange={(e) => handleParameterSchemaChange('update', paramName, { maximum: parseFloat(e.target.value) })}
                              disabled={readOnly}
                            />
                          </div>
                        </div>
                      )}
                      
                      {paramSchema.type === 'string' && (
                        <div className="uw-form-row">
                          <div className="uw-form-group">
                            <label className="uw-label">Min Length</label>
                            <input
                              type="number"
                              className="uw-input"
                              value={paramSchema.minLength || ''}
                              onChange={(e) => handleParameterSchemaChange('update', paramName, { minLength: parseInt(e.target.value) })}
                              disabled={readOnly}
                            />
                          </div>
                          
                          <div className="uw-form-group">
                            <label className="uw-label">Max Length</label>
                            <input
                              type="number"
                              className="uw-input"
                              value={paramSchema.maxLength || ''}
                              onChange={(e) => handleParameterSchemaChange('update', paramName, { maxLength: parseInt(e.target.value) })}
                              disabled={readOnly}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Add Parameter */}
                <div className="uw-add-parameter">
                  <input
                    type="text"
                    className="uw-input"
                    placeholder="New parameter name"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.target.value.trim()) {
                        handleParameterSchemaChange('add', e.target.value.trim());
                        e.target.value = '';
                      }
                    }}
                    disabled={readOnly}
                  />
                  <button
                    className="uw-btn uw-btn-secondary"
                    onClick={(e) => {
                      const input = e.target.previousElementSibling;
                      if (input.value.trim()) {
                        handleParameterSchemaChange('add', input.value.trim());
                        input.value = '';
                      }
                    }}
                    disabled={readOnly}
                  >
                    Add Parameter
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Variants Tab */}
        {activeTab === 'variants' && (
          <div className="uw-tab-panel">
            <div className="uw-variants-editor">
              <h3 className="uw-section-title">Type Variants</h3>
              <p className="uw-section-description">
                Define preset variations of this type with specific parameter combinations
              </p>
              
              {/* Variant List */}
              <div className="uw-variant-list">
                {typeDefinition.variants?.map((variant, index) => (
                  <div key={index} className="uw-variant-item">
                    <div className="uw-variant-header">
                      <h4 className="uw-variant-name">{variant.name}</h4>
                      <button
                        className="uw-btn uw-btn-small uw-btn-secondary"
                        onClick={() => {
                          const newVariants = typeDefinition.variants.filter((_, i) => i !== index);
                          handleBasicFieldChange('variants', newVariants);
                        }}
                        disabled={readOnly}
                      >
                        Remove
                      </button>
                    </div>
                    
                    <div className="uw-variant-fields">
                      <div className="uw-form-group">
                        <label className="uw-label">Name</label>
                        <input
                          type="text"
                          className="uw-input"
                          value={variant.name || ''}
                          onChange={(e) => {
                            const newVariants = [...(typeDefinition.variants || [])];
                            newVariants[index] = { ...newVariants[index], name: e.target.value };
                            handleBasicFieldChange('variants', newVariants);
                          }}
                          disabled={readOnly}
                        />
                      </div>
                      
                      <div className="uw-form-group">
                        <label className="uw-label">Description</label>
                        <input
                          type="text"
                          className="uw-input"
                          value={variant.description || ''}
                          onChange={(e) => {
                            const newVariants = [...(typeDefinition.variants || [])];
                            newVariants[index] = { ...newVariants[index], description: e.target.value };
                            handleBasicFieldChange('variants', newVariants);
                          }}
                          disabled={readOnly}
                        />
                      </div>
                      
                      <div className="uw-form-group">
                        <label className="uw-label">Weight</label>
                        <input
                          type="number"
                          step="0.01"
                          className="uw-input"
                          value={variant.weight || 1}
                          onChange={(e) => {
                            const newVariants = [...(typeDefinition.variants || [])];
                            newVariants[index] = { ...newVariants[index], weight: parseFloat(e.target.value) };
                            handleBasicFieldChange('variants', newVariants);
                          }}
                          disabled={readOnly}
                        />
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Add Variant */}
                <button
                  className="uw-btn uw-btn-secondary"
                  onClick={() => {
                    const newVariants = [...(typeDefinition.variants || []), {
                      variant_id: `variant_${Date.now()}`,
                      name: 'New Variant',
                      description: '',
                      parameters: {},
                      weight: 1.0
                    }];
                    handleBasicFieldChange('variants', newVariants);
                  }}
                  disabled={readOnly}
                >
                  Add Variant
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Diversity Config Tab */}
        {activeTab === 'diversity' && (
          <div className="uw-tab-panel">
            <div className="uw-diversity-editor">
              <h3 className="uw-section-title">Diversity Configuration</h3>
              
              <div className="uw-form-grid">
                <div className="uw-form-group">
                  <label className="uw-label">Strategy</label>
                  <select
                    className="uw-select"
                    value={typeDefinition.diversity_config?.strategy || 'jitter'}
                    onChange={(e) => handleNestedFieldChange('diversity_config', 'strategy', e.target.value)}
                    disabled={readOnly}
                  >
                    <option value="jitter">Jitter</option>
                    <option value="strategyPool">Strategy Pool</option>
                    <option value="seeded">Seeded</option>
                    <option value="compositional">Compositional</option>
                  </select>
                </div>
                
                <div className="uw-form-group">
                  <label className="uw-label">Target Diversity Score</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    className="uw-input"
                    value={typeDefinition.diversity_config?.target_diversity_score || 0.7}
                    onChange={(e) => handleNestedFieldChange('diversity_config', 'target_diversity_score', parseFloat(e.target.value))}
                    disabled={readOnly}
                  />
                </div>
                
                <div className="uw-form-group">
                  <label className="uw-label">Max Variations</label>
                  <input
                    type="number"
                    className="uw-input"
                    value={typeDefinition.diversity_config?.max_variations || 100}
                    onChange={(e) => handleNestedFieldChange('diversity_config', 'max_variations', parseInt(e.target.value))}
                    disabled={readOnly}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* JSON Editor Tab */}
        {activeTab === 'json' && (
          <div className="uw-tab-panel">
            <div className="uw-json-editor">
              <div className="uw-json-editor-header">
                <h3 className="uw-section-title">JSON Editor</h3>
                <div className="uw-json-editor-actions">
                  <button
                    className="uw-btn uw-btn-small"
                    onClick={() => setJsonEditorContent(JSON.stringify(typeDefinition, null, 2))}
                    disabled={readOnly}
                  >
                    Format
                  </button>
                  <button
                    className="uw-btn uw-btn-small uw-btn-secondary"
                    onClick={() => {
                      try {
                        const parsed = JSON.parse(jsonEditorContent);
                        setTypeDefinition(parsed);
                        addToHistory(parsed);
                      } catch (err) {
                        setJsonParseError(`Parse Error: ${err.message}`);
                      }
                    }}
                    disabled={readOnly}
                  >
                    Apply Changes
                  </button>
                </div>
              </div>
              
              <textarea
                ref={jsonEditorRef}
                className={`uw-json-textarea ${jsonParseError ? 'error' : ''}`}
                value={jsonEditorContent}
                onChange={(e) => handleJsonEditorChange(e.target.value)}
                disabled={readOnly}
                placeholder="Type definition JSON..."
              />
            </div>
          </div>
        )}
      </div>

      {/* Import Dialog */}
      {importDialogOpen && (
        <div className="uw-modal-overlay" onClick={() => setImportDialogOpen(false)}>
          <div className="uw-modal" onClick={(e) => e.stopPropagation()}>
            <div className="uw-modal-header">
              <h3>Import Type Definition</h3>
              <button
                className="uw-btn uw-btn-icon"
                onClick={() => setImportDialogOpen(false)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            
            <div className="uw-modal-content">
              <textarea
                className="uw-textarea"
                rows={10}
                value={importContent}
                onChange={(e) => setImportContent(e.target.value)}
                placeholder="Paste type definition JSON here..."
              />
            </div>
            
            <div className="uw-modal-actions">
              <button
                className="uw-btn uw-btn-secondary"
                onClick={() => setImportDialogOpen(false)}
              >
                Cancel
              </button>
              <button
                className="uw-btn uw-btn-primary"
                onClick={handleImport}
              >
                Import
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// PropTypes definition
TypeEditor.propTypes = {
  elementType: PropTypes.object,
  onTypeSave: PropTypes.func,
  onTypeValidate: PropTypes.func,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  readOnly: PropTypes.bool,
  className: PropTypes.string
};

export default TypeEditor;