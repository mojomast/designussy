/**
 * @fileoverview ParameterControls React Component
 * @description Component for controlling generation parameters
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { AssetValidators, ValidationError } from '../utils/validators.js';

/**
 * Component for controlling generation parameters
 * @param {Object} props - Component props
 * @param {Object} props.parameters - Current parameter values
 * @param {Object} props.schema - Parameter schema definition
 * @param {Function} props.onChange - Callback when parameters change
 * @param {Function} props.onReset - Callback to reset parameters
 * @param {string} props.theme - Theme to apply
 * @param {boolean} props.disabled - Whether controls are disabled
 * @returns {JSX.Element} ParameterControls component
 */
const ParameterControls = ({
  parameters = {},
  schema = {},
  onChange = () => {},
  onReset = () => {},
  theme = 'default',
  disabled = false,
  className = '',
  ...props
}) => {
  const [localParameters, setLocalParameters] = useState(parameters);
  const [errors, setErrors] = useState({});
  const [validationResults, setValidationResults] = useState({});

  // Update local parameters when props change
  useEffect(() => {
    setLocalParameters(parameters);
  }, [parameters]);

  /**
   * Validate a parameter value
   * @param {string} key - Parameter key
   * @param {*} value - Parameter value
   * @returns {Object} Validation result
   */
  const validateParameter = useCallback((key, value) => {
    const paramSchema = schema[key];
    if (!paramSchema) return { valid: true, error: null };

    try {
      // Apply validators based on schema type
      switch (paramSchema.type) {
        case 'string':
          AssetValidators.string(value, {
            fieldName: paramSchema.label || key,
            minLength: paramSchema.minLength,
            maxLength: paramSchema.maxLength,
            pattern: paramSchema.pattern,
            allowEmpty: !paramSchema.required
          });
          break;
        case 'number':
          AssetValidators.number(value, {
            fieldName: paramSchema.label || key,
            min: paramSchema.min,
            max: paramSchema.max,
            integer: paramSchema.integer,
            allowEmpty: !paramSchema.required
          });
          break;
        case 'boolean':
          if (paramSchema.required && value === undefined) {
            throw new ValidationError(`${paramSchema.label || key} is required`, key, 'required');
          }
          break;
        case 'color':
          AssetValidators.color(value, {
            fieldName: paramSchema.label || key,
            allowEmpty: !paramSchema.required
          });
          break;
        case 'select':
          if (paramSchema.required && !paramSchema.options.includes(value)) {
            throw new ValidationError(`${paramSchema.label || key} is required`, key, 'required');
          }
          break;
      }
      return { valid: true, error: null };
    } catch (error) {
      return { valid: false, error: error.message };
    }
  }, [schema]);

  /**
   * Handle parameter value change
   * @param {string} key - Parameter key
   * @param {*} value - New parameter value
   */
  const handleParameterChange = useCallback((key, value) => {
    if (disabled) return;

    const newParameters = { ...localParameters, [key]: value };
    
    // Validate the new value
    const validation = validateParameter(key, value);
    const newErrors = { ...errors };
    const newValidationResults = { ...validationResults };

    if (validation.valid) {
      delete newErrors[key];
    } else {
      newErrors[key] = validation.error;
    }

    newValidationResults[key] = validation;

    setLocalParameters(newParameters);
    setErrors(newErrors);
    setValidationResults(newValidationResults);

    // Notify parent component
    onChange(newParameters, key, value, newErrors);
  }, [localParameters, errors, validationResults, disabled, validateParameter, onChange]);

  /**
   * Handle reset to default values
   */
  const handleReset = useCallback(() => {
    const defaultParameters = {};
    
    // Get default values from schema
    Object.keys(schema).forEach(key => {
      defaultParameters[key] = schema[key].default !== undefined ? schema[key].default : '';
    });

    setLocalParameters(defaultParameters);
    setErrors({});
    setValidationResults({});
    onReset(defaultParameters);
  }, [schema, onReset]);

  /**
   * Render parameter control based on schema type
   * @param {string} key - Parameter key
   * @param {Object} paramSchema - Parameter schema
   * @returns {JSX.Element} Control element
   */
  const renderParameterControl = (key, paramSchema) => {
    const value = localParameters[key];
    const hasError = errors[key];
    const isDisabled = disabled || paramSchema.disabled;

    const controlProps = {
      key,
      id: `param-${key}`,
      className: `uw-input ${hasError ? 'error' : ''}`,
      disabled: isDisabled,
      'aria-describedby': hasError ? `param-${key}-error` : undefined,
      'aria-invalid': hasError ? 'true' : 'false'
    };

    switch (paramSchema.type) {
      case 'string':
        if (paramSchema.multiline) {
          return (
            <div className="uw-form-group" key={key}>
              <label htmlFor={controlProps.id} className="uw-label">
                {paramSchema.label}
                {paramSchema.required && <span className="uw-required" aria-label="required">*</span>}
              </label>
              <textarea
                {...controlProps}
                rows={paramSchema.rows || 3}
                value={value || ''}
                placeholder={paramSchema.placeholder}
                onChange={(e) => handleParameterChange(key, e.target.value)}
              />
              {paramSchema.help && (
                <div className="uw-help-text">{paramSchema.help}</div>
              )}
              {hasError && (
                <div id={controlProps['aria-describedby']} className="uw-error-text" role="alert">
                  {errors[key]}
                </div>
              )}
            </div>
          );
        }
        
        return (
          <div className="uw-form-group" key={key}>
            <label htmlFor={controlProps.id} className="uw-label">
              {paramSchema.label}
              {paramSchema.required && <span className="uw-required" aria-label="required">*</span>}
            </label>
            <input
              {...controlProps}
              type="text"
              value={value || ''}
              placeholder={paramSchema.placeholder}
              onChange={(e) => handleParameterChange(key, e.target.value)}
            />
            {paramSchema.help && (
              <div className="uw-help-text">{paramSchema.help}</div>
            )}
            {hasError && (
              <div id={controlProps['aria-describedby']} className="uw-error-text" role="alert">
                {errors[key]}
              </div>
            )}
          </div>
        );

      case 'number':
        return (
          <div className="uw-form-group" key={key}>
            <label htmlFor={controlProps.id} className="uw-label">
              {paramSchema.label}
              {paramSchema.required && <span className="uw-required" aria-label="required">*</span>}
            </label>
            <input
              {...controlProps}
              type="number"
              value={value !== undefined ? value : ''}
              min={paramSchema.min}
              max={paramSchema.max}
              step={paramSchema.step || 1}
              placeholder={paramSchema.placeholder}
              onChange={(e) => handleParameterChange(key, parseFloat(e.target.value))}
            />
            {paramSchema.help && (
              <div className="uw-help-text">{paramSchema.help}</div>
            )}
            {hasError && (
              <div id={controlProps['aria-describedby']} className="uw-error-text" role="alert">
                {errors[key]}
              </div>
            )}
          </div>
        );

      case 'boolean':
        return (
          <div className="uw-form-group" key={key}>
            <div className="uw-checkbox-group">
              <input
                {...controlProps}
                type="checkbox"
                checked={value || false}
                onChange={(e) => handleParameterChange(key, e.target.checked)}
              />
              <label htmlFor={controlProps.id} className="uw-checkbox-label">
                {paramSchema.label}
                {paramSchema.required && <span className="uw-required" aria-label="required">*</span>}
              </label>
            </div>
            {paramSchema.help && (
              <div className="uw-help-text">{paramSchema.help}</div>
            )}
            {hasError && (
              <div id={controlProps['aria-describedby']} className="uw-error-text" role="alert">
                {errors[key]}
              </div>
            )}
          </div>
        );

      case 'color':
        return (
          <div className="uw-form-group" key={key}>
            <label htmlFor={controlProps.id} className="uw-label">
              {paramSchema.label}
              {paramSchema.required && <span className="uw-required" aria-label="required">*</span>}
            </label>
            <div className="uw-color-input-group">
              <input
                {...controlProps}
                type="color"
                value={value || '#000000'}
                onChange={(e) => handleParameterChange(key, e.target.value)}
              />
              <input
                type="text"
                className="uw-color-text-input"
                value={value || ''}
                placeholder="#000000"
                onChange={(e) => handleParameterChange(key, e.target.value)}
                disabled={isDisabled}
              />
            </div>
            {paramSchema.help && (
              <div className="uw-help-text">{paramSchema.help}</div>
            )}
            {hasError && (
              <div id={controlProps['aria-describedby']} className="uw-error-text" role="alert">
                {errors[key]}
              </div>
            )}
          </div>
        );

      case 'select':
        return (
          <div className="uw-form-group" key={key}>
            <label htmlFor={controlProps.id} className="uw-label">
              {paramSchema.label}
              {paramSchema.required && <span className="uw-required" aria-label="required">*</span>}
            </label>
            <select
              {...controlProps}
              value={value || ''}
              onChange={(e) => handleParameterChange(key, e.target.value)}
            >
              <option value="">Select {paramSchema.label.toLowerCase()}</option>
              {paramSchema.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {paramSchema.help && (
              <div className="uw-help-text">{paramSchema.help}</div>
            )}
            {hasError && (
              <div id={controlProps['aria-describedby']} className="uw-error-text" role="alert">
                {errors[key]}
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="uw-form-group" key={key}>
            <label htmlFor={controlProps.id} className="uw-label">
              {paramSchema.label}
            </label>
            <input
              {...controlProps}
              type="text"
              value={value || ''}
              onChange={(e) => handleParameterChange(key, e.target.value)}
            />
            <div className="uw-help-text">
              Unsupported parameter type: {paramSchema.type}
            </div>
          </div>
        );
    }
  };

  // Group parameters by category if specified
  const groupedParameters = Object.entries(schema).reduce((groups, [key, paramSchema]) => {
    const category = paramSchema.category || 'General';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push([key, paramSchema]);
    return groups;
  }, {});

  const hasErrors = Object.keys(errors).length > 0;

  return (
    <div className={`uw-parameter-controls ${theme} ${className}`} {...props}>
      <div className="uw-controls-header">
        <h3 className="uw-controls-title">Parameters</h3>
        <div className="uw-controls-actions">
          <button
            type="button"
            className="uw-btn uw-btn-secondary"
            onClick={handleReset}
            disabled={disabled}
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      <div className="uw-controls-content">
        {hasErrors && (
          <div className="uw-validation-summary" role="alert" aria-live="polite">
            <h4 className="uw-validation-title">Please correct the following errors:</h4>
            <ul className="uw-validation-list">
              {Object.entries(errors).map(([key, error]) => (
                <li key={key}>
                  <a href={`#param-${key}`} onClick={(e) => {
                    e.preventDefault();
                    document.getElementById(`param-${key}`)?.focus();
                  }}>
                    {schema[key]?.label || key}: {error}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        {Object.entries(groupedParameters).map(([category, parameters]) => (
          <div key={category} className="uw-parameter-group">
            <h4 className="uw-group-title">{category}</h4>
            <div className="uw-group-content">
              {parameters.map(([key, paramSchema]) => 
                renderParameterControl(key, paramSchema)
              )}
            </div>
          </div>
        ))}

        {Object.keys(schema).length === 0 && (
          <div className="uw-empty-state">
            <p>No parameters available for this asset type.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// PropTypes definition
ParameterControls.propTypes = {
  parameters: PropTypes.object,
  schema: PropTypes.object,
  onChange: PropTypes.func,
  onReset: PropTypes.func,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  disabled: PropTypes.bool,
  className: PropTypes.string
};

export default ParameterControls;