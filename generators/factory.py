"""
Generator Factory

This module implements a factory pattern for creating generator instances
with proper configuration management and validation.
"""

import logging
from typing import Dict, Any, Optional, Type, Union
from .base_generator import BaseGenerator
from .registry import GeneratorRegistry


class GeneratorFactory:
    """
    Factory for creating generator instances with validation and configuration.
    
    Provides a clean interface for creating generators with proper error handling,
    configuration management, and dependency injection.
    """
    
    def __init__(self, registry: Optional[GeneratorRegistry] = None):
        """
        Initialize the generator factory.
        
        Args:
            registry: Optional registry to use. Uses default if not provided.
        """
        self.registry = registry or GeneratorRegistry()
        self.logger = logging.getLogger(__name__)
        self._generator_cache: Dict[str, BaseGenerator] = {}
        self._default_configs: Dict[str, Dict[str, Any]] = {}
        
    def create_generator(self, generator_type: str, **kwargs) -> BaseGenerator:
        """
        Create a generator instance with the specified type and configuration.
        
        Args:
            generator_type: Type of generator to create
            **kwargs: Generator initialization parameters
            
        Returns:
            Generator instance configured with provided parameters
            
        Raises:
            ValueError: If generator type is not found
            TypeError: If generator class is not valid
            Exception: If generator initialization fails
        """
        # Check cache first for singleton pattern
        cache_key = self._get_cache_key(generator_type, kwargs)
        if cache_key in self._generator_cache:
            self.logger.debug(f"Returning cached generator: {generator_type}")
            return self._generator_cache[cache_key]
        
        # Validate generator type exists
        generator_class = self.registry.get_generator_class(generator_type)
        if generator_class is None:
            available_types = self.registry.list_generators()
            raise ValueError(
                f"Unknown generator type: '{generator_type}'. "
                f"Available types: {available_types}"
            )
        
        # Merge configuration with defaults
        config = self._merge_config(generator_type, kwargs)
        
        # Validate configuration
        self._validate_config(generator_type, config)
        
        try:
            # Create generator instance
            generator = generator_class(**config)
            
            # Verify it's a valid BaseGenerator
            if not isinstance(generator, BaseGenerator):
                raise TypeError(f"Created object is not a BaseGenerator: {type(generator)}")
            
            # Cache the instance if it's meant to be shared
            if self._should_cache(config):
                self._generator_cache[cache_key] = generator
                self.logger.debug(f"Cached generator: {generator_type}")
            
            self.logger.info(f"Created generator: {generator_type}")
            return generator
            
        except Exception as e:
            self.logger.error(f"Failed to create generator '{generator_type}': {e}")
            raise Exception(f"Failed to initialize generator '{generator_type}': {e}")
    
    def create_generator_with_defaults(self, generator_type: str, 
                                     override_defaults: Optional[Dict[str, Any]] = None) -> BaseGenerator:
        """
        Create a generator using default configuration with optional overrides.
        
        Args:
            generator_type: Type of generator to create
            override_defaults: Dictionary of parameters to override from defaults
            
        Returns:
            Generator instance with default or overridden configuration
        """
        defaults = self.get_default_config(generator_type)
        config = defaults.copy()
        
        if override_defaults:
            config.update(override_defaults)
        
        return self.create_generator(generator_type, **config)
    
    def get_generator_info(self, generator_type: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a generator type.
        
        Args:
            generator_type: Type of generator to get info about
            
        Returns:
            Dictionary with generator information
        """
        if generator_type not in self.registry:
            raise ValueError(f"Unknown generator type: {generator_type}")
        
        generator_class = self.registry.get_generator_class(generator_type)
        
        return {
            'type': generator_type,
            'class_name': generator_class.__name__,
            'module': generator_class.__module__,
            'default_config': self.get_default_config(generator_type),
            'signature': self.registry.get_generator_signature(generator_type),
            'validation': self.registry.validate_generator(generator_type)
        }
    
    def get_default_config(self, generator_type: str) -> Dict[str, Any]:
        """
        Get default configuration for a generator type.
        
        Args:
            generator_type: Type of generator
            
        Returns:
            Dictionary with default configuration parameters
        """
        # Use cached defaults if available
        if generator_type in self._default_configs:
            return self._default_configs[generator_type]
        
        # Generate defaults from generator class
        generator_class = self.registry.get_generator_class(generator_type)
        if generator_class is None:
            raise ValueError(f"Unknown generator type: {generator_type}")
        
        try:
            # Try to get defaults from generator method
            if hasattr(generator_class, 'get_default_params'):
                defaults = generator_class.get_default_params()
            else:
                # Create instance with minimal config to get defaults
                temp_instance = generator_class()
                defaults = getattr(temp_instance, 'config', {})
            
            # Cache the defaults
            self._default_configs[generator_type] = defaults
            return defaults.copy()
            
        except Exception as e:
            self.logger.warning(f"Could not get defaults for {generator_type}: {e}")
            return {}
    
    def set_default_config(self, generator_type: str, config: Dict[str, Any]) -> None:
        """
        Set default configuration for a generator type.
        
        Args:
            generator_type: Type of generator
            config: Default configuration dictionary
        """
        self._default_configs[generator_type] = config.copy()
        self.logger.info(f"Set default config for {generator_type}: {config}")
    
    def validate_generator_config(self, generator_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration for a generator type.
        
        Args:
            generator_type: Type of generator
            config: Configuration to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if generator type exists
        if generator_type not in self.registry:
            result['valid'] = False
            result['errors'].append(f"Unknown generator type: {generator_type}")
            return result
        
        # Get expected signature
        signature = self.registry.get_generator_signature(generator_type)
        if not signature:
            result['warnings'].append("Could not determine expected parameters")
            return result
        
        # Validate parameter types
        for param_name, param_value in config.items():
            if param_name in signature:
                expected_type = signature[param_name]
                # Basic type checking (can be enhanced)
                if expected_type == 'int' and not isinstance(param_value, int):
                    result['warnings'].append(f"Parameter '{param_name}' should be int, got {type(param_value).__name__}")
                elif expected_type == 'float' and not isinstance(param_value, (int, float)):
                    result['warnings'].append(f"Parameter '{param_name}' should be float, got {type(param_value).__name__}")
                elif expected_type == 'str' and not isinstance(param_value, str):
                    result['warnings'].append(f"Parameter '{param_name}' should be str, got {type(param_value).__name__}")
        
        # Check for required parameters
        for param_name, param_type in signature.items():
            if param_name in ['width', 'height']:  # Required basic parameters
                if param_name not in config:
                    result['valid'] = False
                    result['errors'].append(f"Required parameter missing: {param_name}")
        
        return result
    
    def clear_cache(self) -> None:
        """Clear the generator instance cache."""
        self._generator_cache.clear()
        self.logger.info("Cleared generator cache")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the factory cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_generators': len(self._generator_cache),
            'default_configs': len(self._default_configs)
        }
    
    def _get_cache_key(self, generator_type: str, config: Dict[str, Any]) -> str:
        """Generate a cache key for generator configuration."""
        # Create a hashable representation
        config_items = sorted(config.items())
        return f"{generator_type}:{hash(tuple(config_items))}"
    
    def _merge_config(self, generator_type: str, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with defaults."""
        defaults = self.get_default_config(generator_type)
        
        # Start with defaults
        merged = defaults.copy()
        
        # Override with user config
        merged.update(user_config)
        
        return merged
    
    def _validate_config(self, generator_type: str, config: Dict[str, Any]) -> None:
        """Validate configuration before generator creation."""
        validation_result = self.validate_generator_config(generator_type, config)
        
        if not validation_result['valid']:
            error_msg = "; ".join(validation_result['errors'])
            raise ValueError(f"Invalid configuration for {generator_type}: {error_msg}")
        
        if validation_result['warnings']:
            self.logger.warning(f"Configuration warnings for {generator_type}: {validation_result['warnings']}")
    
    def _should_cache(self, config: Dict[str, Any]) -> bool:
        """Determine if a generator should be cached based on configuration."""
        # Don't cache if explicitly disabled
        if config.get('cache', True) is False:
            return False
        
        # Don't cache if it has a seed (makes it non-deterministic)
        if 'seed' in config:
            return False
        
        # Cache by default
        return True
    
    def __repr__(self) -> str:
        """String representation of the factory."""
        registered_types = list(self.registry.list_generators())
        return f"GeneratorFactory(generators={registered_types}, cached={len(self._generator_cache)})"