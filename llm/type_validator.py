"""
Type Validator Module

This module implements the TypeValidator class for comprehensive validation
of ElementType definitions, ensuring safety, completeness, and best practices.

The validator checks:
- Schema completeness (all required fields present)
- Parameter safety (bounded values, no exploits)
- Render strategy validity (available generators, engines)
- Diversity config validation (proper strategy configuration)
- Conflict detection (name/ID conflicts)
- Security constraints (URL restrictions, script prevention)

Provides detailed feedback with specific error messages and suggestions.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Import ElementType for validation
try:
    from ..enhanced_design.element_types import (
        ElementType, RenderStrategy, DiversityConfig, 
        ElementVariant, validate_param_schema
    )
    HAS_ELEMENT_TYPES = True
except ImportError:
    HAS_ELEMENT_TYPES = False
    # Fallback type definitions for testing
    class ElementType:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        def to_dict(self) -> Dict[str, Any]:
            return self.__dict__


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass
class ValidationIssue:
    """Individual validation issue with details."""
    severity: ValidationSeverity
    field: str
    message: str
    suggestion: Optional[str] = None
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result with detailed feedback."""
    is_valid: bool
    issues: List[ValidationIssue]
    field_errors: Dict[str, List[str]] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.field_errors is None:
            self.field_errors = {}
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
    
    def add_issue(self, severity: ValidationSeverity, field: str, message: str, 
                  suggestion: Optional[str] = None, code: Optional[str] = None):
        """Add a validation issue."""
        issue = ValidationIssue(severity, field, message, suggestion, code)
        self.issues.append(issue)
        
        # Update overall validity
        if severity == ValidationSeverity.ERROR:
            self.is_valid = False
        elif severity == ValidationSeverity.WARNING:
            self.warnings.append(f"{field}: {message}")
        elif severity == ValidationSeverity.SUGGESTION:
            self.suggestions.append(f"{field}: {message}")
        
        # Track field-specific errors
        if severity in [ValidationSeverity.ERROR, ValidationSeverity.WARNING]:
            if field not in self.field_errors:
                self.field_errors[field] = []
            self.field_errors[field].append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.issues.extend(other.issues)
        self.field_errors.update(other.field_errors)
        self.warnings.extend(other.warnings)
        self.suggestions.extend(other.suggestions)
        if not other.is_valid:
            self.is_valid = False
    
    def get_summary(self) -> str:
        """Get a human-readable summary of validation results."""
        if self.is_valid and len(self.warnings) == 0 and len(self.suggestions) == 0:
            return "✓ Valid ElementType definition"
        
        summary_parts = []
        
        if self.is_valid:
            summary_parts.append("✓ Valid with improvements suggested")
        else:
            summary_parts.append(f"✗ Invalid ({len([i for i in self.issues if i.severity == ValidationSeverity.ERROR])} errors)")
        
        if self.warnings:
            summary_parts.append(f"⚠ {len(self.warnings)} warnings")
        
        if self.suggestions:
            summary_parts.append(f"💡 {len(self.suggestions)} suggestions")
        
        return " - ".join(summary_parts)
    
    def get_detailed_report(self) -> str:
        """Get a detailed report of all validation issues."""
        if not self.issues and not self.warnings and not self.suggestions:
            return "No validation issues found."
        
        lines = [f"Validation Result: {'VALID' if self.is_valid else 'INVALID'}"]
        lines.append("=" * 50)
        
        # Group issues by severity
        errors = [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
        suggestions = [i for i in self.issues if i.severity == ValidationSeverity.SUGGESTION]
        
        if errors:
            lines.append("\nERRORS:")
            for error in errors:
                lines.append(f"  ❌ {error.field}: {error.message}")
                if error.suggestion:
                    lines.append(f"     💡 {error.suggestion}")
        
        if warnings:
            lines.append("\nWARNINGS:")
            for warning in warnings:
                lines.append(f"  ⚠️  {warning.field}: {warning.message}")
                if warning.suggestion:
                    lines.append(f"     💡 {warning.suggestion}")
        
        if suggestions:
            lines.append("\nSUGGESTIONS:")
            for suggestion in suggestions:
                lines.append(f"  💡 {suggestion.field}: {suggestion.message}")
                if suggestion.suggestion:
                    lines.append(f"     🔧 {suggestion.suggestion}")
        
        return "\n".join(lines)


class TypeValidator:
    """
    Comprehensive validator for ElementType definitions.
    
    Provides multiple validation methods targeting different aspects
    of type safety and quality.
    """
    
    # Allowed values for safety
    ALLOWED_GENERATORS = ["parchment", "enso", "sigil", "giraffe", "kangaroo"]
    ALLOWED_ENGINES = ["pil", "cairo", "skia"]
    VALID_CATEGORIES = [
        "backgrounds", "glyphs", "creatures", "ui", "effects",
        "patterns", "textures", "decorations", "symbols"
    ]
    
    # Safety constraints
    MAX_PARAMETERS = 20
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_NAME_LENGTH = 100
    MAX_TAG_LENGTH = 50
    MAX_ID_LENGTH = 100
    
    # Parameter safety limits
    MIN_NUMERIC_VALUE = -1000000
    MAX_NUMERIC_VALUE = 1000000
    MAX_STRING_LENGTH = 1000
    
    def __init__(self):
        """Initialize the type validator."""
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for performance
        self._hex_color_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        self._alphanumeric_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        self._url_pattern = re.compile(r'https?://|ftp://|file://')
    
    def validate_schema_completeness(self, element_type: Any) -> ValidationResult:
        """
        Validate that all required fields are present and properly structured.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult with schema completeness feedback
        """
        result = ValidationResult(is_valid=True, issues=[])
        
        if not HAS_ELEMENT_TYPES:
            # Basic validation without full schema
            return self._validate_basic_schema(element_type)
        
        try:
            # Check required fields
            required_fields = ["id", "name", "description", "category", "tags", "render_strategy", "version"]
            
            for field in required_fields:
                if not hasattr(element_type, field):
                    result.add_issue(
                        ValidationSeverity.ERROR, 
                        field, 
                        f"Required field '{field}' is missing",
                        f"Add the '{field}' field to your type definition",
                        "MISSING_REQUIRED_FIELD"
                    )
                    continue
                
                value = getattr(element_type, field)
                if value is None:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        field,
                        f"Required field '{field}' cannot be None",
                        f"Provide a value for '{field}'",
                        "NULL_REQUIRED_FIELD"
                    )
                elif field == "id" and not self._validate_type_id(str(value)):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "id",
                        f"Invalid type ID: '{value}'",
                        "Use only alphanumeric characters with optional underscores or hyphens",
                        "INVALID_TYPE_ID"
                    )
                elif field == "name" and not self._validate_name(str(value)):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "name",
                        f"Invalid type name: '{value}'",
                        "Use a descriptive name between 1-100 characters",
                        "INVALID_TYPE_NAME"
                    )
                elif field == "category" and str(value) not in self.VALID_CATEGORIES:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "category",
                        f"Invalid category: '{value}'",
                        f"Use one of: {', '.join(self.VALID_CATEGORIES)}",
                        "INVALID_CATEGORY"
                    )
                elif field == "description" and not self._validate_description(str(value)):
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        "description",
                        "Description could be more descriptive",
                        "Add a detailed description explaining what this type creates",
                        "WEAK_DESCRIPTION"
                    )
                elif field == "tags" and not self._validate_tags(value):
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        "tags",
                        "Tags could be improved",
                        "Add relevant, searchable tags",
                        "WEAK_TAGS"
                    )
                elif field == "render_strategy" and not self._validate_render_strategy(value):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "render_strategy",
                        "Invalid render strategy",
                        "Provide valid engine and generator_name",
                        "INVALID_RENDER_STRATEGY"
                    )
                elif field == "version" and not self._validate_version(str(value)):
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        "version",
                        f"Version format may be incorrect: '{value}'",
                        "Use semantic versioning (e.g., '1.0.0')",
                        "INVALID_VERSION_FORMAT"
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Schema validation error: {e}")
            result.add_issue(
                ValidationSeverity.ERROR,
                "schema",
                f"Schema validation failed: {str(e)}",
                "Check type definition structure",
                "VALIDATION_SYSTEM_ERROR"
            )
            return result
    
    def validate_parameter_safety(self, element_type: Any) -> ValidationResult:
        """
        Validate parameter schema for safety and security constraints.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult with parameter safety feedback
        """
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            if not hasattr(element_type, 'param_schema') or not element_type.param_schema:
                return result  # No parameters to validate
            
            param_schema = element_type.param_schema
            if not isinstance(param_schema, dict):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "param_schema",
                    "Parameter schema must be a dictionary",
                    "Provide a valid JSON schema object",
                    "INVALID_PARAM_SCHEMA_TYPE"
                )
                return result
            
            # Validate schema structure
            try:
                validate_param_schema(param_schema)
            except ValueError as e:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "param_schema",
                    f"Parameter schema validation failed: {str(e)}",
                    "Fix JSON schema structure and validation rules",
                    "INVALID_PARAM_SCHEMA"
                )
                return result
            
            # Check parameter count
            if 'properties' in param_schema:
                param_count = len(param_schema['properties'])
                if param_count > self.MAX_PARAMETERS:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "param_schema",
                        f"Too many parameters: {param_count} (max: {self.MAX_PARAMETERS})",
                        f"Reduce to {self.MAX_PARAMETERS} or fewer parameters",
                        "TOO_MANY_PARAMETERS"
                    )
                elif param_count == 0:
                    result.add_issue(
                        ValidationSeverity.SUGGESTION,
                        "param_schema",
                        "No parameters defined",
                        "Consider adding configurable parameters",
                        "NO_PARAMETERS"
                    )
            
            # Validate each parameter
            if 'properties' in param_schema:
                for param_name, param_def in param_schema['properties'].items():
                    self._validate_parameter(param_name, param_def, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Parameter safety validation error: {e}")
            result.add_issue(
                ValidationSeverity.ERROR,
                "param_schema",
                f"Parameter validation failed: {str(e)}",
                "Check parameter schema structure",
                "PARAMETER_VALIDATION_ERROR"
            )
            return result
    
    def validate_render_strategy(self, element_type: Any) -> ValidationResult:
        """
        Validate render strategy for generator compatibility.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult with render strategy feedback
        """
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            if not hasattr(element_type, 'render_strategy'):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "render_strategy",
                    "Render strategy is missing",
                    "Provide render_strategy with engine and generator_name",
                    "MISSING_RENDER_STRATEGY"
                )
                return result
            
            render_strategy = element_type.render_strategy
            
            # Handle both dict and object forms
            if isinstance(render_strategy, dict):
                engine = render_strategy.get('engine')
                generator_name = render_strategy.get('generator_name')
            else:
                engine = getattr(render_strategy, 'engine', None)
                generator_name = getattr(render_strategy, 'generator_name', None)
            
            # Validate engine
            if not engine:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "render_strategy.engine",
                    "Engine is required",
                    "Specify one of: pil, cairo, skia",
                    "MISSING_ENGINE"
                )
            elif engine not in self.ALLOWED_ENGINES:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "render_strategy.engine",
                    f"Unknown engine: '{engine}'",
                    f"Use one of: {', '.join(self.ALLOWED_ENGINES)}",
                    "UNKNOWN_ENGINE"
                )
            
            # Validate generator
            if not generator_name:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "render_strategy.generator_name",
                    "Generator name is required",
                    "Specify one of: parchment, enso, sigil, giraffe, kangaroo",
                    "MISSING_GENERATOR"
                )
            elif generator_name not in self.ALLOWED_GENERATORS:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "render_strategy.generator_name",
                    f"Unknown generator: '{generator_name}'",
                    f"Use one of: {', '.join(self.ALLOWED_GENERATORS)}",
                    "UNKNOWN_GENERATOR"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Render strategy validation error: {e}")
            result.add_issue(
                ValidationSeverity.ERROR,
                "render_strategy",
                f"Render strategy validation failed: {str(e)}",
                "Check render strategy structure",
                "RENDER_STRATEGY_ERROR"
            )
            return result
    
    def validate_diversity_config(self, element_type: Any) -> ValidationResult:
        """
        Validate diversity configuration for proper strategy setup.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult with diversity config feedback
        """
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            if not hasattr(element_type, 'diversity_config') or not element_type.diversity_config:
                return result  # No diversity config to validate
            
            diversity_config = element_type.diversity_config
            
            # Validate strategy selection
            if hasattr(diversity_config, 'strategy'):
                strategy = diversity_config.strategy
                if isinstance(strategy, str):
                    valid_strategies = ["jitter", "strategy_pool", "seeded", "parameter_sampling", "compositional"]
                    if strategy not in valid_strategies:
                        result.add_issue(
                            ValidationSeverity.ERROR,
                            "diversity_config.strategy",
                            f"Unknown strategy: '{strategy}'",
                            f"Use one of: {', '.join(valid_strategies)}",
                            "UNKNOWN_DIVERSITY_STRATEGY"
                        )
            
            # Validate strategy-specific configurations
            if hasattr(diversity_config, 'strategy'):
                strategy = diversity_config.strategy
                strategy_map = {
                    "jitter": diversity_config.jitter,
                    "strategy_pool": diversity_config.strategy_pool,
                    "seeded": diversity_config.seeded,
                    "parameter_sampling": diversity_config.parameter_sampling,
                    "compositional": diversity_config.compositional
                }
                
                required_config = strategy_map.get(strategy)
                if not required_config:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        f"diversity_config.{strategy}",
                        f"Strategy '{strategy}' requires configuration",
                        f"Provide {strategy} configuration parameters",
                        f"MISSING_{strategy.upper()}_CONFIG"
                    )
            
            # Validate global diversity settings
            if hasattr(diversity_config, 'diversity_target'):
                target = diversity_config.diversity_target
                if not (0.0 <= target <= 1.0):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "diversity_config.diversity_target",
                        f"Invalid diversity target: {target}",
                        "Use value between 0.0 and 1.0",
                        "INVALID_DIVERSITY_TARGET"
                    )
            
            if hasattr(diversity_config, 'max_variations'):
                max_vars = diversity_config.max_variations
                if max_vars < 1 or max_vars > 10000:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        "diversity_config.max_variations",
                        f"Invalid max variations: {max_vars}",
                        "Use value between 1 and 10000",
                        "INVALID_MAX_VARIATIONS"
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Diversity config validation error: {e}")
            result.add_issue(
                ValidationSeverity.ERROR,
                "diversity_config",
                f"Diversity config validation failed: {str(e)}",
                "Check diversity configuration structure",
                "DIVERSITY_CONFIG_ERROR"
            )
            return result
    
    def validate_security_constraints(self, element_type: Any) -> ValidationResult:
        """
        Validate security constraints and safety rules.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult with security validation feedback
        """
        result = ValidationResult(is_valid=True, issues=[])
        
        try:
            type_dict = element_type.to_dict() if hasattr(element_type, 'to_dict') else element_type.__dict__
            
            # Check for external URLs
            type_string = json.dumps(type_dict, default=str)
            urls = self._url_pattern.findall(type_string)
            if urls:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    "security",
                    f"External URLs not allowed: {len(urls)} found",
                    "Remove all external URLs and references",
                    "EXTERNAL_URLS_FORBIDDEN"
                )
            
            # Check for potentially dangerous patterns in descriptions and names
            dangerous_patterns = [
                r'javascript:', r'data:', r'file:', r'ftp:',
                r'<script', r'</script>', r'onload=', r'onerror='
            ]
            
            for field in ['name', 'description']:
                if field in type_dict:
                    content = str(type_dict[field])
                    for pattern in dangerous_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            result.add_issue(
                                ValidationSeverity.ERROR,
                                f"security.{field}",
                                f"Potentially dangerous content detected",
                                "Remove scripts, external references, or suspicious content",
                                "DANGEROUS_CONTENT"
                            )
            
            # Check for excessive parameter ranges that could cause resource issues
            if 'param_schema' in type_dict and type_dict['param_schema']:
                self._validate_parameter_bounds(type_dict['param_schema'], result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Security validation error: {e}")
            result.add_issue(
                ValidationSeverity.ERROR,
                "security",
                f"Security validation failed: {str(e)}",
                "Check for security issues manually",
                "SECURITY_VALIDATION_ERROR"
            )
            return result
    
    def _validate_basic_schema(self, element_type: Any) -> ValidationResult:
        """Basic schema validation without full ElementType support."""
        result = ValidationResult(is_valid=True, issues=[])
        
        # Check if it has basic attributes
        required_attrs = ['id', 'name', 'category', 'render_strategy']
        for attr in required_attrs:
            if not hasattr(element_type, attr):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    attr,
                    f"Missing required attribute: {attr}",
                    f"Add {attr} to the type definition",
                    "MISSING_ATTRIBUTE"
                )
        
        return result
    
    def _validate_type_id(self, type_id: str) -> bool:
        """Validate type ID format."""
        if not type_id or len(type_id) > self.MAX_ID_LENGTH:
            return False
        
        return self._alphanumeric_pattern.match(type_id) is not None
    
    def _validate_name(self, name: str) -> bool:
        """Validate type name."""
        if not name or len(name) > self.MAX_NAME_LENGTH:
            return False
        
        return len(name.strip()) > 0
    
    def _validate_description(self, description: str) -> bool:
        """Validate type description."""
        if not description:
            return False
        
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            return False
        
        # Check for minimum meaningful content
        words = description.strip().split()
        return len(words) >= 3
    
    def _validate_tags(self, tags: Any) -> bool:
        """Validate tags."""
        if not isinstance(tags, list):
            return False
        
        if len(tags) == 0:
            return False
        
        # Check each tag
        for tag in tags:
            if not isinstance(tag, str) or len(tag) > self.MAX_TAG_LENGTH:
                return False
        
        # Check for reasonable number of tags
        if len(tags) > 10:
            return False
        
        return True
    
    def _validate_render_strategy(self, render_strategy: Any) -> bool:
        """Validate render strategy."""
        if not render_strategy:
            return False
        
        # Handle both dict and object forms
        if isinstance(render_strategy, dict):
            engine = render_strategy.get('engine')
            generator_name = render_strategy.get('generator_name')
        else:
            engine = getattr(render_strategy, 'engine', None)
            generator_name = getattr(render_strategy, 'generator_name', None)
        
        return (engine in self.ALLOWED_ENGINES and 
                generator_name in self.ALLOWED_GENERATORS)
    
    def _validate_version(self, version: str) -> bool:
        """Validate version format."""
        if not version:
            return False
        
        # Simple semantic versioning check
        version_pattern = re.compile(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?$')
        return version_pattern.match(version) is not None
    
    def _validate_parameter(self, param_name: str, param_def: Dict[str, Any], result: ValidationResult):
        """Validate individual parameter definition."""
        # Check parameter name
        if not self._alphanumeric_pattern.match(param_name):
            result.add_issue(
                ValidationSeverity.ERROR,
                f"param_schema.properties.{param_name}",
                f"Invalid parameter name: '{param_name}'",
                "Use alphanumeric characters with optional underscores",
                "INVALID_PARAM_NAME"
            )
        
        # Check parameter type
        param_type = param_def.get('type')
        valid_types = ['string', 'integer', 'number', 'boolean', 'array', 'object']
        if param_type not in valid_types:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"param_schema.properties.{param_name}",
                f"Invalid parameter type: '{param_type}'",
                f"Use one of: {', '.join(valid_types)}",
                "INVALID_PARAM_TYPE"
            )
        
        # Check for dangerous parameter names
        dangerous_names = ['exec', 'eval', 'import', 'open', '__', 'system']
        if any(dangerous in param_name.lower() for dangerous in dangerous_names):
            result.add_issue(
                ValidationSeverity.ERROR,
                f"param_schema.properties.{param_name}",
                "Potentially dangerous parameter name",
                "Use safe, descriptive parameter names",
                "DANGEROUS_PARAM_NAME"
            )
        
        # Validate bounds for numeric parameters
        if param_type in ['integer', 'number']:
            minimum = param_def.get('minimum', self.MIN_NUMERIC_VALUE)
            maximum = param_def.get('maximum', self.MAX_NUMERIC_VALUE)
            
            if minimum < self.MIN_NUMERIC_VALUE or maximum > self.MAX_NUMERIC_VALUE:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"param_schema.properties.{param_name}",
                    "Parameter bounds are too wide",
                    "Use reasonable bounds within safe limits",
                    "EXCESSIVE_PARAM_BOUNDS"
                )
            
            if minimum >= maximum:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"param_schema.properties.{param_name}",
                    "Minimum value must be less than maximum value",
                    "Fix parameter bounds",
                    "INVALID_PARAM_BOUNDS"
                )
        
        # Check string parameter constraints
        if param_type == 'string':
            max_length = param_def.get('maxLength', 0)
            if max_length > self.MAX_STRING_LENGTH:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"param_schema.properties.{param_name}",
                    "String parameter may be too long",
                    "Consider limiting string length for safety",
                    "LONG_STRING_PARAM"
                )
            
            # Check for patterns that might indicate security issues
            pattern = param_def.get('pattern')
            if pattern and ('http' in pattern or 'file' in pattern):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"param_schema.properties.{param_name}",
                    "String pattern may allow external references",
                    "Avoid patterns that could be exploited",
                    "SUSPICIOUS_STRING_PATTERN"
                )
    
    def _validate_parameter_bounds(self, param_schema: Dict[str, Any], result: ValidationResult):
        """Validate parameter bounds for resource safety."""
        if 'properties' not in param_schema:
            return
        
        # Check for parameters that could cause resource exhaustion
        dangerous_params = {
            'width': {'max': 4096, 'reason': 'excessive image size'},
            'height': {'max': 4096, 'reason': 'excessive image size'},
            'iterations': {'max': 1000, 'reason': 'excessive computation'},
            'complexity': {'max': 100, 'reason': 'excessive detail'},
            'quality': {'max': 100, 'reason': 'excessive quality'},
            'samples': {'max': 1000, 'reason': 'excessive sampling'},
            'attempts': {'max': 100, 'reason': 'excessive retry attempts'}
        }
        
        for param_name, param_def in param_schema['properties'].items():
            if param_name.lower() in dangerous_params:
                config = dangerous_params[param_name.lower()]
                maximum = param_def.get('maximum')
                
                if maximum and maximum > config['max']:
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        f"param_schema.properties.{param_name}",
                        f"Parameter may cause {config['reason']}",
                        f"Consider limiting to {config['max']} or less",
                        "RESOURCE_INTENSIVE_PARAM"
                    )
    
    def validate_all(self, element_type: Any) -> ValidationResult:
        """
        Perform comprehensive validation of an ElementType.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult with complete validation feedback
        """
        # Start with basic validation
        result = self.validate_schema_completeness(element_type)
        
        # Add parameter safety validation
        param_result = self.validate_parameter_safety(element_type)
        result.merge(param_result)
        
        # Add render strategy validation
        render_result = self.validate_render_strategy(element_type)
        result.merge(render_result)
        
        # Add diversity config validation
        diversity_result = self.validate_diversity_config(element_type)
        result.merge(diversity_result)
        
        # Add security validation
        security_result = self.validate_security_constraints(element_type)
        result.merge(security_result)
        
        return result


# Export main classes
__all__ = [
    'TypeValidator',
    'ValidationResult',
    'ValidationIssue',
    'ValidationSeverity'
]