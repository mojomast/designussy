/**
 * Unwritten Worlds - Input Validators
 * Comprehensive validation utilities for component inputs
 */

class ValidationError extends Error {
  constructor(message, field = null, code = null) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.code = code;
  }
}

class AssetValidators {
  /**
   * Validate required field
   * @param {*} value - Value to check
   * @param {string} fieldName - Field name for error message
   * @returns {*} Validated value
   */
  static required(value, fieldName = 'Field') {
    if (value === null || value === undefined || value === '') {
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }
    return value;
  }

  /**
   * Validate string value
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated string
   */
  static string(value, options = {}) {
    const { 
      fieldName = 'Field', 
      minLength = 0, 
      maxLength = Infinity, 
      pattern = null,
      allowEmpty = false 
    } = options;

    if (value === null || value === undefined) {
      if (allowEmpty) return '';
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    const strValue = String(value);

    if (!allowEmpty && strValue.length === 0) {
      throw new ValidationError(`${fieldName} cannot be empty`, fieldName, 'empty');
    }

    if (strValue.length < minLength) {
      throw new ValidationError(
        `${fieldName} must be at least ${minLength} characters long`, 
        fieldName, 
        'minLength'
      );
    }

    if (strValue.length > maxLength) {
      throw new ValidationError(
        `${fieldName} must be no more than ${maxLength} characters long`, 
        fieldName, 
        'maxLength'
      );
    }

    if (pattern && !pattern.test(strValue)) {
      throw new ValidationError(`${fieldName} format is invalid`, fieldName, 'pattern');
    }

    return strValue;
  }

  /**
   * Validate number value
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {number} Validated number
   */
  static number(value, options = {}) {
    const { 
      fieldName = 'Field', 
      min = -Infinity, 
      max = Infinity, 
      integer = false,
      allowEmpty = false 
    } = options;

    if (value === null || value === undefined || value === '') {
      if (allowEmpty) return null;
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    const numValue = Number(value);

    if (Number.isNaN(numValue)) {
      throw new ValidationError(`${fieldName} must be a valid number`, fieldName, 'nan');
    }

    if (integer && !Number.isInteger(numValue)) {
      throw new ValidationError(`${fieldName} must be an integer`, fieldName, 'integer');
    }

    if (numValue < min) {
      throw new ValidationError(
        `${fieldName} must be at least ${min}`, 
        fieldName, 
        'min'
      );
    }

    if (numValue > max) {
      throw new ValidationError(
        `${fieldName} must be no more than ${max}`, 
        fieldName, 
        'max'
      );
    }

    return numValue;
  }

  /**
   * Validate URL
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated URL
   */
  static url(value, options = {}) {
    const { fieldName = 'URL', allowEmpty = false } = options;
    
    if (!value) {
      if (allowEmpty) return '';
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    try {
      const url = new URL(value);
      return url.toString();
    } catch {
      throw new ValidationError(`${fieldName} must be a valid URL`, fieldName, 'url');
    }
  }

  /**
   * Validate email address
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated email
   */
  static email(value, options = {}) {
    const { fieldName = 'Email', allowEmpty = false } = options;
    
    if (!value) {
      if (allowEmpty) return '';
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailPattern.test(String(value))) {
      throw new ValidationError(`${fieldName} must be a valid email address`, fieldName, 'email');
    }

    return String(value).toLowerCase();
  }

  /**
   * Validate color value
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated color
   */
  static color(value, options = {}) {
    const { fieldName = 'Color', allowEmpty = false } = options;
    
    if (!value) {
      if (allowEmpty) return '';
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    // Check for hex color
    const hexPattern = /^#[0-9A-Fa-f]{6}$/;
    // Check for rgb/rgba color
    const rgbPattern = /^rgba?\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})(?:,\s*(0|1|0?\.\d+))?\)$/;
    // Check for hsl/hsla color
    const hslPattern = /^hsla?\((\d+),\s*(\d+)%,\s*(\d+)%?(?:,\s*(0|1|0?\.\d+))?\)$/;

    const colorStr = String(value).toLowerCase();
    
    if (!hexPattern.test(colorStr) && !rgbPattern.test(colorStr) && !hslPattern.test(colorStr)) {
      throw new ValidationError(
        `${fieldName} must be a valid color (hex, rgb, or hsl)`, 
        fieldName, 
        'color'
      );
    }

    return colorStr;
  }

  /**
   * Validate asset type
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated asset type
   */
  static assetType(value, options = {}) {
    const { fieldName = 'Asset type', allowEmpty = false } = options;
    
    const validTypes = ['parchment', 'enso', 'sigil', 'giraffe', 'kangaroo'];
    
    if (!value) {
      if (allowEmpty) return '';
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    const strValue = String(value).toLowerCase();
    
    if (!validTypes.includes(strValue)) {
      throw new ValidationError(
        `${fieldName} must be one of: ${validTypes.join(', ')}`, 
        fieldName, 
        'assetType'
      );
    }

    return strValue;
  }

  /**
   * Validate dimensions
   * @param {*} width - Width value
   * @param {*} height - Height value
   * @param {Object} options - Validation options
   * @returns {Object} Validated dimensions
   */
  static dimensions(width, height, options = {}) {
    const { 
      fieldName = 'Dimensions', 
      minDimension = 100, 
      maxDimension = 2048,
      allowEmpty = false 
    } = options;

    if (!width || !height) {
      if (allowEmpty) return { width: null, height: null };
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    const widthValue = this.number(width, { 
      fieldName: 'Width', 
      min: minDimension, 
      max: maxDimension,
      integer: true 
    });

    const heightValue = this.number(height, { 
      fieldName: 'Height', 
      min: minDimension, 
      max: maxDimension,
      integer: true 
    });

    return { width: widthValue, height: heightValue };
  }

  /**
   * Validate array
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {Array} Validated array
   */
  static array(value, options = {}) {
    const { 
      fieldName = 'Field', 
      minItems = 0, 
      maxItems = Infinity,
      itemValidator = null,
      allowEmpty = false 
    } = options;

    if (!value) {
      if (allowEmpty) return [];
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    if (!Array.isArray(value)) {
      throw new ValidationError(`${fieldName} must be an array`, fieldName, 'array');
    }

    if (value.length < minItems) {
      throw new ValidationError(
        `${fieldName} must contain at least ${minItems} item(s)`, 
        fieldName, 
        'minItems'
      );
    }

    if (value.length > maxItems) {
      throw new ValidationError(
        `${fieldName} must contain no more than ${maxItems} item(s)`, 
        fieldName, 
        'maxItems'
      );
    }

    // Validate array items if validator provided
    if (itemValidator) {
      value.forEach((item, index) => {
        try {
          itemValidator(item);
        } catch (error) {
          throw new ValidationError(
            `${fieldName}[${index}]: ${error.message}`, 
            fieldName, 
            'itemValidation'
          );
        }
      });
    }

    return value;
  }

  /**
   * Validate tags array
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {Array} Validated tags
   */
  static tags(value, options = {}) {
    const { fieldName = 'Tags', maxTags = 10 } = options;

    return this.array(value, {
      ...options,
      fieldName,
      maxItems: maxTags,
      itemValidator: (item) => this.string(item, {
        fieldName: 'Tag',
        minLength: 1,
        maxLength: 30,
        pattern: /^[a-zA-Z0-9_-]+$/
      })
    });
  }

  /**
   * Validate prompt for LLM generation
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated prompt
   */
  static prompt(value, options = {}) {
    const { fieldName = 'Prompt', allowEmpty = false } = options;

    return this.string(value, {
      ...options,
      fieldName,
      minLength: 10,
      maxLength: 500,
      allowEmpty
    });
  }

  /**
   * Validate API key
   * @param {*} value - Value to check
   * @param {Object} options - Validation options
   * @returns {string} Validated API key
   */
  static apiKey(value, options = {}) {
    const { fieldName = 'API key', allowEmpty = false } = options;

    if (!value) {
      if (allowEmpty) return '';
      throw new ValidationError(`${fieldName} is required`, fieldName, 'required');
    }

    const strValue = String(value).trim();
    
    // API keys should be reasonable length (10-200 characters)
    if (strValue.length < 10) {
      throw new ValidationError(`${fieldName} is too short`, fieldName, 'minLength');
    }

    if (strValue.length > 200) {
      throw new ValidationError(`${fieldName} is too long`, fieldName, 'maxLength');
    }

    // Basic pattern check - alphanumerics and some special characters
    const apiKeyPattern = /^[a-zA-Z0-9._-]+$/;
    
    if (!apiKeyPattern.test(strValue)) {
      throw new ValidationError(
        `${fieldName} contains invalid characters`, 
        fieldName, 
        'pattern'
      );
    }

    return strValue;
  }

  /**
   * Run multiple validations
   * @param {Object} data - Data object to validate
   * @param {Object} schema - Validation schema
   * @returns {Object} Validated data
   */
  static validateObject(data, schema) {
    const errors = {};
    const validated = {};

    for (const [fieldName, validator] of Object.entries(schema)) {
      try {
        validated[fieldName] = validator(data[fieldName]);
      } catch (error) {
        errors[fieldName] = error.message;
      }
    }

    if (Object.keys(errors).length > 0) {
      throw new ValidationError('Validation failed', null, 'object');
    }

    return validated;
  }

  /**
   * Create a composable validator
   * @param {...Function} validators - Validator functions
   * @returns {Function} Composed validator
   */
  static compose(...validators) {
    return (value) => {
      let result = value;
      for (const validator of validators) {
        result = validator(result);
      }
      return result;
    };
  }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AssetValidators, ValidationError };
} else if (typeof window !== 'undefined') {
  window.UnwrittenValidators = { AssetValidators, ValidationError };
}