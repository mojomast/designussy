"""
Generator Configuration

This module implements a comprehensive configuration system for managing
generator settings, defaults, and environment overrides.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path


class GeneratorConfig:
    """
    Configuration manager for generator settings.
    
    Handles default configurations, environment variable overrides,
    and validation schemas for all generator types.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file or "generators_config.json"
        
        # Configuration storage
        self._defaults: Dict[str, Dict[str, Any]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._overrides: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default configurations
        self._init_default_configs()
        self._init_validation_schemas()
        
        # Load configuration file if exists
        self._load_config_file()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
    def _init_default_configs(self) -> None:
        """Initialize default configurations for all generator types."""
        self._defaults = {
            "parchment": {
                "width": 1024,
                "height": 1024,
                "base_color": [15, 15, 18],
                "noise_scale": 1.5,
                "output_dir": "assets/elements",
                "category": "backgrounds"
            },
            
            "enso": {
                "width": 800,
                "height": 800,
                "color": [0, 0, 0, 255],
                "complexity": 40,
                "chaos": 1.0,
                "output_dir": "assets/elements",
                "category": "glyphs"
            },
            
            "sigil": {
                "width": 500,
                "height": 500,
                "color": [212, 197, 176, 255],
                "point_count_range": [3, 7],
                "output_dir": "assets/elements",
                "category": "glyphs"
            },
            
            "giraffe": {
                "width": 600,
                "height": 800,
                "body_color": [212, 197, 176, 255],
                "spot_color": [20, 20, 20, 220],
                "spot_count": 20,
                "output_dir": "assets/elements",
                "category": "creatures"
            },
            
            "kangaroo": {
                "width": 600,
                "height": 800,
                "ink_color": [10, 10, 12, 240],
                "parchment_color": [212, 197, 176, 255],
                "spot_count": 15,
                "output_dir": "assets/elements",
                "category": "creatures"
            },
            
            "directed": {
                "generator_type": "enso",
                "output_dir": "assets/elements",
                "category": "glyphs",
                "timeout": 30,
                "max_retries": 3
            },
            
            # Global configuration
            "_global": {
                "default_width": 1024,
                "default_height": 1024,
                "default_output_dir": "assets/elements",
                "enable_caching": True,
                "cache_timeout": 3600,
                "max_concurrent_generations": 4,
                "quality": "high"
            }
        }
    
    def _init_validation_schemas(self) -> None:
        """Initialize validation schemas for each generator type."""
        self._schemas = {
            "parchment": {
                "width": {"type": int, "min": 64, "max": 4096},
                "height": {"type": int, "min": 64, "max": 4096},
                "base_color": {"type": list, "length": 3, "item_type": int},
                "noise_scale": {"type": (int, float), "min": 0.1, "max": 5.0},
                "output_dir": {"type": str, "min_length": 1}
            },
            
            "enso": {
                "width": {"type": int, "min": 100, "max": 2000},
                "height": {"type": int, "min": 100, "max": 2000},
                "color": {"type": list, "length": 4, "item_type": int},
                "complexity": {"type": int, "min": 5, "max": 200},
                "chaos": {"type": (int, float), "min": 0.1, "max": 3.0},
                "output_dir": {"type": str, "min_length": 1}
            },
            
            "sigil": {
                "width": {"type": int, "min": 100, "max": 2000},
                "height": {"type": int, "min": 100, "max": 2000},
                "color": {"type": list, "length": 4, "item_type": int},
                "point_count_range": {"type": list, "length": 2, "item_type": int},
                "output_dir": {"type": str, "min_length": 1}
            },
            
            "giraffe": {
                "width": {"type": int, "min": 200, "max": 2000},
                "height": {"type": int, "min": 200, "max": 3000},
                "body_color": {"type": list, "length": 4, "item_type": int},
                "spot_color": {"type": list, "length": 4, "item_type": int},
                "spot_count": {"type": int, "min": 1, "max": 100},
                "output_dir": {"type": str, "min_length": 1}
            },
            
            "kangaroo": {
                "width": {"type": int, "min": 200, "max": 2000},
                "height": {"type": int, "min": 200, "max": 3000},
                "ink_color": {"type": list, "length": 4, "item_type": int},
                "parchment_color": {"type": list, "length": 4, "item_type": int},
                "spot_count": {"type": int, "min": 1, "max": 100},
                "output_dir": {"type": str, "min_length": 1}
            },
            
            "directed": {
                "generator_type": {"type": str, "choices": ["enso", "sigil"]},
                "output_dir": {"type": str, "min_length": 1},
                "timeout": {"type": int, "min": 1, "max": 300},
                "max_retries": {"type": int, "min": 0, "max": 10}
            }
        }
    
    def get_defaults(self, generator_type: str) -> Dict[str, Any]:
        """
        Get default configuration for a generator type.
        
        Args:
            generator_type: Type of generator
            
        Returns:
            Dictionary with default configuration
        """
        # Get generator defaults
        defaults = self._defaults.get(generator_type, {}).copy()
        
        # Apply global defaults for missing values
        global_defaults = self._defaults.get("_global", {})
        for key, value in global_defaults.items():
            if key not in defaults:
                defaults[key] = value
        
        # Apply any environment overrides
        if generator_type in self._overrides:
            defaults.update(self._overrides[generator_type])
        
        return defaults
    
    def get_all_defaults(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all default configurations.
        
        Returns:
            Dictionary mapping generator types to their default configurations
        """
        return {k: v.copy() for k, v in self._defaults.items() if k != "_global"}
    
    def set_default(self, generator_type: str, config: Dict[str, Any]) -> None:
        """
        Set default configuration for a generator type.
        
        Args:
            generator_type: Type of generator
            config: Configuration dictionary to set as default
        """
        self._defaults[generator_type] = config.copy()
        self.logger.info(f"Set default config for {generator_type}")
    
    def validate_config(self, generator_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration against the schema.
        
        Args:
            generator_type: Type of generator
            config: Configuration to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "sanitized": config.copy()
        }
        
        schema = self._schemas.get(generator_type, {})
        
        for param_name, param_value in config.items():
            if param_name not in schema:
                result["warnings"].append(f"Unknown parameter: {param_name}")
                continue
            
            param_schema = schema[param_name]
            validation_error = self._validate_parameter(param_name, param_value, param_schema)
            
            if validation_error:
                result["valid"] = False
                result["errors"].append(validation_error)
            else:
                # Sanitize the value if needed
                sanitized_value = self._sanitize_parameter(param_value, param_schema)
                result["sanitized"][param_name] = sanitized_value
        
        return result
    
    def _validate_parameter(self, name: str, value: Any, schema: Dict[str, Any]) -> Optional[str]:
        """Validate a single parameter against its schema."""
        # Type validation
        expected_type = schema.get("type")
        if expected_type and not self._check_type(value, expected_type):
            return f"Parameter '{name}': expected {expected_type.__name__ if hasattr(expected_type, '__name__') else expected_type}, got {type(value).__name__}"
        
        # Value range validation
        if "min" in schema and value < schema["min"]:
            return f"Parameter '{name}': value {value} is below minimum {schema['min']}"
        
        if "max" in schema and value > schema["max"]:
            return f"Parameter '{name}': value {value} is above maximum {schema['max']}"
        
        # String length validation
        if "min_length" in schema and hasattr(value, '__len__') and len(value) < schema["min_length"]:
            return f"Parameter '{name}': length {len(value)} is below minimum {schema['min_length']}"
        
        if "max_length" in schema and hasattr(value, '__len__') and len(value) > schema["max_length"]:
            return f"Parameter '{name}': length {len(value)} is above maximum {schema['max_length']}"
        
        # Choice validation
        if "choices" in schema and value not in schema["choices"]:
            return f"Parameter '{name}': value '{value}' not in allowed choices: {schema['choices']}"
        
        # List-specific validation
        if "length" in schema and isinstance(value, (list, tuple)):
            if len(value) != schema["length"]:
                return f"Parameter '{name}': expected length {schema['length']}, got {len(value)}"
            
            # Item type validation
            item_type = schema.get("item_type")
            if item_type:
                for i, item in enumerate(value):
                    if not self._check_type(item, item_type):
                        return f"Parameter '{name}': item {i} expected {item_type.__name__ if hasattr(item_type, '__name__') else item_type}, got {type(item).__name__}"
        
        return None
    
    def _check_type(self, value: Any, expected_type) -> bool:
        """Check if value matches expected type(s)."""
        if isinstance(expected_type, tuple):
            return any(self._check_type(value, t) for t in expected_type)
        return isinstance(value, expected_type)
    
    def _sanitize_parameter(self, value: Any, schema: Dict[str, Any]) -> Any:
        """Sanitize a parameter value."""
        # Convert strings to appropriate types if needed
        if "type" in schema and isinstance(value, str):
            target_type = schema["type"]
            if target_type == int:
                try:
                    return int(value)
                except ValueError:
                    pass
            elif target_type == float:
                try:
                    return float(value)
                except ValueError:
                    pass
        
        return value
    
    def _load_config_file(self) -> None:
        """Load configuration from file if it exists."""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Apply file configurations
                for generator_type, config in file_config.get("defaults", {}).items():
                    self.set_default(generator_type, config)
                
                self.logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration file: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Look for environment variables that match pattern: GENERATOR_TYPE_PARAM
        for key, value in os.environ.items():
            if key.startswith("GENERATOR_"):
                # Parse environment variable name
                parts = key[10:].split("_")  # Remove "GENERATOR_" prefix
                if len(parts) >= 2:
                    generator_type = parts[0].lower()
                    param_name = "_".join(parts[1:]).lower()
                    
                    # Try to parse the value
                    try:
                        # Try as JSON first
                        override_value = json.loads(value)
                    except json.JSONDecodeError:
                        # Fall back to string
                        override_value = value
                    
                    # Store override
                    if generator_type not in self._overrides:
                        self._overrides[generator_type] = {}
                    self._overrides[generator_type][param_name] = override_value
                    
                    self.logger.debug(f"Applied env override: {generator_type}.{param_name} = {override_value}")
    
    def save_config_file(self) -> None:
        """Save current configuration to file."""
        config_data = {
            "defaults": {k: v for k, v in self._defaults.items() if k != "_global"},
            "version": "2.0.0"
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration file: {e}")
    
    def get_schema(self, generator_type: str) -> Dict[str, Any]:
        """
        Get validation schema for a generator type.
        
        Args:
            generator_type: Type of generator
            
        Returns:
            Validation schema dictionary
        """
        return self._schemas.get(generator_type, {})
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all validation schemas.
        
        Returns:
            Dictionary mapping generator types to their schemas
        """
        return self._schemas.copy()
    
    def __repr__(self) -> str:
        """String representation of the configuration."""
        return f"GeneratorConfig(defaults={len(self._defaults)}, schemas={len(self._schemas)})"