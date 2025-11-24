"""
Generator Registry

This module implements a registry system for dynamically registering
and managing generator classes in the NanoBanana system.
"""

import logging
from typing import Dict, Type, Optional, List
from .base_generator import BaseGenerator


class GeneratorRegistry:
    """
    Registry for managing generator classes.
    
    Provides dynamic registration and discovery of generator types,
    enabling a plugin-based architecture for the generator system.
    """
    
    def __init__(self):
        """Initialize an empty generator registry."""
        self._generators: Dict[str, Type[BaseGenerator]] = {}
        self.logger = logging.getLogger(__name__)
        
    def register(self, name: str, generator_class: Type[BaseGenerator]) -> bool:
        """
        Register a generator class with the registry.
        
        Args:
            name: Unique name for the generator type
            generator_class: Class that inherits from BaseGenerator
            
        Returns:
            True if registration was successful
            
        Raises:
            TypeError: If generator_class doesn't inherit from BaseGenerator
            ValueError: If name is empty or already exists
        """
        # Validation
        if not name or not isinstance(name, str):
            raise ValueError("Generator name must be a non-empty string")
            
        if not issubclass(generator_class, BaseGenerator):
            raise TypeError(f"Generator class must inherit from BaseGenerator")
            
        if name in self._generators:
            raise ValueError(f"Generator '{name}' is already registered")
        
        # Register the generator
        self._generators[name] = generator_class
        self.logger.info(f"Registered generator: {name} -> {generator_class.__name__}")
        
        return True
    
    def unregister(self, name: str) -> bool:
        """
        Remove a generator from the registry.
        
        Args:
            name: Name of the generator to remove
            
        Returns:
            True if removal was successful
        """
        if name in self._generators:
            generator_class = self._generators.pop(name)
            self.logger.info(f"Unregistered generator: {name} -> {generator_class.__name__}")
            return True
        return False
    
    def get_generator_class(self, name: str) -> Optional[Type[BaseGenerator]]:
        """
        Get a generator class by name.
        
        Args:
            name: Name of the generator to retrieve
            
        Returns:
            Generator class if found, None otherwise
        """
        return self._generators.get(name)
    
    def create_generator(self, name: str, **kwargs) -> Optional[BaseGenerator]:
        """
        Create a generator instance by name.
        
        Args:
            name: Name of the generator to create
            **kwargs: Initialization parameters for the generator
            
        Returns:
            Generator instance if found, None otherwise
        """
        generator_class = self.get_generator_class(name)
        if generator_class is None:
            return None
            
        try:
            return generator_class(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create generator '{name}': {e}")
            raise
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a generator name is registered.
        
        Args:
            name: Name to check
            
        Returns:
            True if the generator is registered
        """
        return name in self._generators
    
    def list_generators(self) -> List[str]:
        """
        List all registered generator names.
        
        Returns:
            List of generator type names
        """
        return list(self._generators.keys())
    
    def list_generator_info(self) -> List[Dict[str, str]]:
        """
        Get detailed information about all registered generators.
        
        Returns:
            List of dictionaries with generator information
        """
        info_list = []
        for name, generator_class in self._generators.items():
            info_list.append({
                'name': name,
                'class_name': generator_class.__name__,
                'module': generator_class.__module__,
                'description': getattr(generator_class, '__doc__', '').strip() if getattr(generator_class, '__doc__') else ''
            })
        return info_list
    
    def get_generator_signature(self, name: str) -> Optional[Dict[str, str]]:
        """
        Get the initialization signature for a generator.
        
        Args:
            name: Name of the generator to inspect
            
        Returns:
            Dictionary mapping parameter names to their types, or None if not found
        """
        generator_class = self.get_generator_class(name)
        if generator_class is None:
            return None
            
        try:
            import inspect
            sig = inspect.signature(generator_class.__init__)
            signature = {}
            for param_name, param in sig.parameters.items():
                if param_name != 'self':
                    param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
                    signature[param_name] = param_type
            return signature
        except Exception as e:
            self.logger.warning(f"Could not inspect signature for generator '{name}': {e}")
            return {}
    
    def validate_generator(self, name: str) -> Dict[str, bool]:
        """
        Validate that a generator meets all requirements.
        
        Args:
            name: Name of the generator to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'exists': False,
            'is_base_generator': False,
            'has_generate_method': False,
            'has_type_method': False,
            'can_instantiate': False
        }
        
        generator_class = self.get_generator_class(name)
        if generator_class is None:
            return result
            
        result['exists'] = True
        
        # Check inheritance
        if issubclass(generator_class, BaseGenerator):
            result['is_base_generator'] = True
        
        # Check required methods
        if hasattr(generator_class, 'generate') and callable(getattr(generator_class, 'generate')):
            result['has_generate_method'] = True
            
        if hasattr(generator_class, 'get_generator_type') and callable(getattr(generator_class, 'get_generator_type')):
            result['has_type_method'] = True
        
        # Try to instantiate
        try:
            instance = generator_class()
            result['can_instantiate'] = True
        except Exception:
            pass
            
        return result
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the registry.
        
        Returns:
            Dictionary with registry statistics
        """
        return {
            'total_generators': len(self._generators),
            'registered_names': len(set(self._generators.keys()))
        }
    
    def clear(self) -> None:
        """Clear all registrations from the registry."""
        count = len(self._generators)
        self._generators.clear()
        self.logger.info(f"Cleared {count} generators from registry")
    
    def __len__(self) -> int:
        """Return the number of registered generators."""
        return len(self._generators)
    
    def __contains__(self, name: str) -> bool:
        """Check if a generator name is registered."""
        return name in self._generators
    
    def __iter__(self):
        """Iterate over registered generator names."""
        return iter(self._generators.keys())
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"GeneratorRegistry(generators={list(self._generators.keys())})"