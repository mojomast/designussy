/**
 * @fileoverview LLMTypeCreator React Component
 * @description Component for creating element types using natural language descriptions
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { APIClient } from '../utils/api-client.js';

/**
 * Component for creating element types using LLM assistance
 * @param {Object} props - Component props
 * @param {Function} props.onTypeCreated - Callback when a type is successfully created
 * @param {Function} props.onTypeValidation - Callback for type validation results
 * @param {string} props.theme - Theme to apply
 * @param {boolean} props.autoValidate - Whether to auto-validate generated types
 * @returns {JSX.Element} LLMTypeCreator component
 */
const LLMTypeCreator = ({
  onTypeCreated = () => {},
  onTypeValidation = () => {},
  theme = 'dark',
  autoValidate = true,
  className = '',
  ...props
}) => {
  const [description, setDescription] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('glyph');
  const [templates, setTemplates] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedType, setGeneratedType] = useState(null);
  const [validationResults, setValidationResults] = useState(null);
  const [errors, setErrors] = useState([]);
  const [editableType, setEditableType] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [generationLog, setGenerationLog] = useState([]);
  const [apiClient] = useState(() => new APIClient({ endpoint: 'http://localhost:8001' }));

  // Load available templates
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8001/llm/type-templates');
      const data = await response.json();
      
      if (data.status === 'success' && data.templates) {
        setTemplates(data.templates);
      }
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!description.trim()) {
      setErrors(['Please provide a description for the type']);
      return;
    }

    setIsGenerating(true);
    setErrors([]);
    setGenerationLog([]);

    try {
      // Add log entry
      setGenerationLog(prev => [...prev, {
        timestamp: new Date(),
        message: 'Starting type generation...'
      }]);

      const response = await fetch('http://localhost:8001/llm/create-type', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          description: description.trim(),
          template: selectedTemplate,
          auto_validate: autoValidate
        })
      });

      if (!response.ok) {
        throw new Error(`Generation failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status === 'success') {
        setGeneratedType(data.type);
        setEditableType({ ...data.type });
        setValidationResults(data.validation || null);
        setErrors(data.errors || []);
        
        setGenerationLog(prev => [...prev, {
          timestamp: new Date(),
          message: 'Type generation completed successfully'
        }]);

        if (data.validation && !data.validation.is_valid) {
          setGenerationLog(prev => [...prev, {
            timestamp: new Date(),
            message: `Validation issues found: ${data.validation.issues.length} issues`
          }]);
        }

        // Notify parent components
        if (onTypeValidation && data.validation) {
          onTypeValidation(data.validation);
        }
      } else {
        throw new Error(data.error || 'Generation failed');
      }
    } catch (err) {
      setErrors([err.message]);
      setGenerationLog(prev => [...prev, {
        timestamp: new Date(),
        message: `Generation failed: ${err.message}`
      }]);
    } finally {
      setIsGenerating(false);
    }
  }, [description, selectedTemplate, autoValidate, onTypeValidation]);

  const handleSave = useCallback(async () => {
    if (!editableType) return;

    try {
      setIsGenerating(true);
      
      const response = await fetch('http://localhost:8001/types', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editableType)
      });

      if (!response.ok) {
        throw new Error(`Save failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.status === 'success') {
        setGeneratedType(data.type);
        setEditableType(null);
        setIsEditing(false);
        
        setGenerationLog(prev => [...prev, {
          timestamp: new Date(),
          message: 'Type saved to registry successfully'
        }]);

        onTypeCreated(data.type);
      } else {
        throw new Error(data.error || 'Save failed');
      }
    } catch (err) {
      setErrors([err.message]);
    } finally {
      setIsGenerating(false);
    }
  }, [editableType, onTypeCreated]);

  const handleEditChange = useCallback((field, value) => {
    if (!editableType) return;
    
    setEditableType(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleParameterSchemaChange = useCallback((paramKey, paramValue) => {
    if (!editableType?.param_schema?.properties) return;
    
    setEditableType(prev => ({
      ...prev,
      param_schema: {
        ...prev.param_schema,
        properties: {
          ...prev.param_schema.properties,
          [paramKey]: paramValue
        }
      }
    }));
  }, []);

  const handleValidateCurrent = useCallback(async () => {
    if (!editableType) return;

    try {
      const response = await fetch('http://localhost:8001/llm/validate-type', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editableType)
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setValidationResults(data.validation);
        setErrors(data.validation?.issues || []);
      }
    } catch (err) {
      console.error('Validation failed:', err);
    }
  }, [editableType]);

  const resetForm = useCallback(() => {
    setDescription('');
    setGeneratedType(null);
    setEditableType(null);
    setValidationResults(null);
    setErrors([]);
    setIsEditing(false);
    setGenerationLog([]);
  }, []);

  return (
    <div className={`uw-llm-type-creator ${theme} ${className}`} {...props}>
      {/* Creator Header */}
      <div className="uw-creator-header">
        <h2 className="uw-creator-title">AI Type Creator</h2>
        <p className="uw-creator-description">
          Describe your element type in natural language and let AI create the configuration
        </p>
      </div>

      {/* Input Form */}
      <div className="uw-creator-form">
        <div className="uw-form-section">
          <label className="uw-label">
            Element Type Description
            <span className="uw-required" aria-label="required">*</span>
          </label>
          <textarea
            className="uw-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the element type you want to create. Be as detailed as possible about appearance, behavior, and properties..."
            rows={6}
            disabled={isGenerating}
          />
          <div className="uw-help-text">
            Examples: "A mystical ink blot with swirling patterns", "Ancient parchment with weathered texture", "Geometric sigil with glowing runes"
          </div>
        </div>

        <div className="uw-form-row">
          <div className="uw-form-group">
            <label className="uw-label">Template Type</label>
            <select
              className="uw-select"
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              disabled={isGenerating}
            >
              {templates.map(template => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
            <div className="uw-help-text">
              Choose a base template to start with
            </div>
          </div>

          <div className="uw-form-group">
            <label className="uw-label">
              <input
                type="checkbox"
                checked={autoValidate}
                onChange={(e) => setAutoValidate(e.target.checked)}
                disabled={isGenerating}
              />
              Auto-validate during generation
            </label>
          </div>
        </div>

        <div className="uw-form-actions">
          <button
            className="uw-btn uw-btn-primary"
            onClick={handleGenerate}
            disabled={!description.trim() || isGenerating}
          >
            {isGenerating ? (
              <>
                <div className="uw-spinner-small"></div>
                Generating...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 12l2 2 4-4"/>
                  <path d="M21 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1"/>
                  <path d="M3 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1"/>
                </svg>
                Generate Type
              </>
            )}
          </button>

          <button
            className="uw-btn uw-btn-secondary"
            onClick={resetForm}
            disabled={isGenerating}
          >
            Reset Form
          </button>
        </div>
      </div>

      {/* Error Display */}
      {errors.length > 0 && (
        <div className="uw-error-summary" role="alert">
          <h4 className="uw-error-title">Errors:</h4>
          <ul className="uw-error-list">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Generation Log */}
      {generationLog.length > 0 && (
        <div className="uw-generation-log">
          <h4 className="uw-log-title">Generation Log</h4>
          <div className="uw-log-entries">
            {generationLog.map((entry, index) => (
              <div key={index} className="uw-log-entry">
                <span className="uw-log-time">
                  {entry.timestamp.toLocaleTimeString()}
                </span>
                <span className="uw-log-message">{entry.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated Type Display */}
      {generatedType && (
        <div className="uw-generated-type">
          <div className="uw-type-header">
            <h3 className="uw-type-title">
              Generated Type: {generatedType.name || 'Unnamed'}
            </h3>
            <div className="uw-type-actions">
              {!isEditing ? (
                <>
                  <button
                    className="uw-btn uw-btn-primary"
                    onClick={() => {
                      setEditableType({ ...generatedType });
                      setIsEditing(true);
                    }}
                  >
                    Edit Type
                  </button>
                  <button
                    className="uw-btn uw-btn-secondary"
                    onClick={handleSave}
                    disabled={isGenerating}
                  >
                    Save to Registry
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="uw-btn uw-btn-primary"
                    onClick={handleValidateCurrent}
                    disabled={isGenerating}
                  >
                    Validate
                  </button>
                  <button
                    className="uw-btn uw-btn-secondary"
                    onClick={() => {
                      setIsEditing(false);
                      setEditableType(null);
                    }}
                  >
                    Cancel Edit
                  </button>
                  <button
                    className="uw-btn uw-btn-primary"
                    onClick={handleSave}
                    disabled={isGenerating}
                  >
                    Save Changes
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Validation Results */}
          {validationResults && (
            <div className={`uw-validation-results ${validationResults.is_valid ? 'valid' : 'invalid'}`}>
              <h4 className="uw-validation-title">
                Validation Results
                {validationResults.is_valid ? '✅ Valid' : '❌ Issues Found'}
              </h4>
              
              {validationResults.issues && validationResults.issues.length > 0 && (
                <ul className="uw-validation-issues">
                  {validationResults.issues.map((issue, index) => (
                    <li key={index} className={`uw-issue ${issue.severity || 'warning'}`}>
                      <strong>{issue.field || 'General'}:</strong> {issue.message}
                    </li>
                  ))}
                </ul>
              )}

              {validationResults.suggestions && validationResults.suggestions.length > 0 && (
                <div className="uw-validation-suggestions">
                  <h5>Suggestions:</h5>
                  <ul>
                    {validationResults.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Type Definition Display */}
          <div className="uw-type-definition">
            {isEditing ? (
              <div className="uw-type-editor">
                {/* Basic Info Editor */}
                <div className="uw-editor-section">
                  <h4 className="uw-section-title">Basic Information</h4>
                  
                  <div className="uw-form-group">
                    <label className="uw-label">Name</label>
                    <input
                      type="text"
                      className="uw-input"
                      value={editableType.name || ''}
                      onChange={(e) => handleEditChange('name', e.target.value)}
                    />
                  </div>

                  <div className="uw-form-group">
                    <label className="uw-label">Description</label>
                    <textarea
                      className="uw-textarea"
                      value={editableType.description || ''}
                      onChange={(e) => handleEditChange('description', e.target.value)}
                      rows={3}
                    />
                  </div>

                  <div className="uw-form-group">
                    <label className="uw-label">Category</label>
                    <input
                      type="text"
                      className="uw-input"
                      value={editableType.category || ''}
                      onChange={(e) => handleEditChange('category', e.target.value)}
                    />
                  </div>

                  <div className="uw-form-group">
                    <label className="uw-label">Tags (comma-separated)</label>
                    <input
                      type="text"
                      className="uw-input"
                      value={(editableType.tags || []).join(', ')}
                      onChange={(e) => handleEditChange('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                    />
                  </div>
                </div>

                {/* Parameter Schema Editor */}
                {editableType.param_schema && (
                  <div className="uw-editor-section">
                    <h4 className="uw-section-title">Parameter Schema</h4>
                    <div className="uw-schema-editor">
                      {Object.entries(editableType.param_schema.properties || {}).map(([key, schema]) => (
                        <div key={key} className="uw-param-editor">
                          <h5 className="uw-param-title">{key}</h5>
                          <div className="uw-param-fields">
                            <div className="uw-form-group">
                              <label className="uw-label">Type</label>
                              <select
                                className="uw-select"
                                value={schema.type}
                                onChange={(e) => handleParameterSchemaChange(key, { ...schema, type: e.target.value })}
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
                                value={schema.default || ''}
                                onChange={(e) => handleParameterSchemaChange(key, { ...schema, default: e.target.value })}
                              />
                            </div>

                            <div className="uw-form-group">
                              <label className="uw-label">Description</label>
                              <input
                                type="text"
                                className="uw-input"
                                value={schema.description || ''}
                                onChange={(e) => handleParameterSchemaChange(key, { ...schema, description: e.target.value })}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="uw-type-preview">
                <pre className="uw-type-json">
                  {JSON.stringify(generatedType, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// PropTypes definition
LLMTypeCreator.propTypes = {
  onTypeCreated: PropTypes.func,
  onTypeValidation: PropTypes.func,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  autoValidate: PropTypes.bool,
  className: PropTypes.string
};

export default LLMTypeCreator;