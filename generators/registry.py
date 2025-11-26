"""
Generator Registry

This module implements a registry system for dynamically registering
and managing generator classes in the NanoBanana system.
"""

import logging
from typing import Dict, Type, Optional, List, Any
from .base_generator import BaseGenerator

# Import Type System components for integration
try:
    from enhanced_design.type_registry import get_type_registry, TypeRegistry
    from enhanced_design.element_types import ElementType
    HAS_TYPE_SYSTEM = True
except ImportError as e:
    HAS_TYPE_SYSTEM = False

# Import Dynamic Generator Loader for Phase 2 integration
try:
    from .dynamic_loader import DynamicGeneratorLoader
    HAS_DYNAMIC_LOADER = True
except ImportError as e:
    HAS_DYNAMIC_LOADER = False


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
        # Initialize TypeRegistry integration if available
        if HAS_TYPE_SYSTEM:
            self._type_registry = get_type_registry()
            self.logger.info("TypeRegistry integration enabled")
        else:
            self._type_registry = None
            self.logger.info("TypeRegistry integration disabled")
        
        # Initialize DynamicGeneratorLoader integration if available
        if HAS_DYNAMIC_LOADER and HAS_TYPE_SYSTEM:
            self._dynamic_loader = DynamicGeneratorLoader()
            self.logger.info("DynamicGeneratorLoader integration enabled")
        else:
            self._dynamic_loader = None
            if not HAS_DYNAMIC_LOADER:
                self.logger.info("DynamicGeneratorLoader integration disabled")
            elif not HAS_TYPE_SYSTEM:
                self.logger.info("DynamicGeneratorLoader disabled (TypeSystem required)")
        
        
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
    
    # ==================== TypeRegistry Integration Methods ====================
    
    def get_available_types(self) -> List[str]:
        """
        Get list of available types from the TypeRegistry.
        
        Returns:
            List of type IDs from the type registry
        """
        if not self._type_registry:
            return []
        
        try:
            types = self._type_registry.list(active_only=True)
            return [element_type.id for element_type in types]
        except Exception as e:
            self.logger.warning(f"Failed to get types from registry: {e}")
            return []
    
    def get_type_registry(self) -> Optional[TypeRegistry]:
        """
        Get the TypeRegistry instance.
        
        Returns:
            TypeRegistry instance if available, None otherwise
        """
        return self._type_registry
    
    def get_types_by_category(self, category: str) -> List[ElementType]:
        """
        Get all types in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of ElementType instances in the category
        """
        if not self._type_registry:
            return []
        
        try:
            return self._type_registry.list(category=category, active_only=True)
        except Exception as e:
            self.logger.warning(f"Failed to get types by category {category}: {e}")
            return []
    
    def sync_with_type_registry(self) -> Dict[str, bool]:
        """
        Synchronize generator registry with TypeRegistry.
        
        Ensures all generators have corresponding types and vice versa.
        
        Returns:
            Dictionary with sync results for each generator
        """
        if not self._type_registry:
            return {}
        
        sync_results = {}
        available_generators = set(self.list_generators())
        available_types = set(self.get_available_types())
        
        # Check for generators without types
        generators_without_types = available_generators - available_types
        for generator_name in generators_without_types:
            try:
                # Try to create a basic type definition for this generator
                generator_class = self.get_generator_class(generator_name)
                if generator_class:
                    # Create basic type definition
                    type_data = {
                        "id": f"{generator_name}_v1",
                        "name": generator_name.replace("_", " ").title(),
                        "description": f"Auto-generated type for {generator_name} generator",
                        "category": self._get_category_for_generator(generator_name),
                        "tags": [generator_name],
                        "render_strategy": {
                            "engine": "pil",
                            "generator_name": generator_name
                        },
                        "param_schema": {},
                        "version": "1.0.0"
                    }
                    
                    # Try to add to registry
                    element_type = ElementType(**type_data)
                    success = self._type_registry.add(element_type)
                    sync_results[generator_name] = success
                    
                    if success:
                        self.logger.info(f"Created type for generator: {generator_name}")
                    else:
                        self.logger.warning(f"Failed to create type for generator: {generator_name}")
                        
            except Exception as e:
                self.logger.error(f"Error creating type for generator {generator_name}: {e}")
                sync_results[generator_name] = False
        
        # Check for types without generators (informational only)
        types_without_generators = available_types - available_generators
        for type_id in types_without_generators:
            self.logger.info(f"Type '{type_id}' exists but no corresponding generator found")
            sync_results[type_id] = True  # This is informational
        
        return sync_results
    
    def get_generator_from_type(self, type_id: str) -> Optional[BaseGenerator]:
        """
        Create a generator instance from a type definition.
        
        Args:
            type_id: Type ID to create generator for
            
        Returns:
            Generator instance if successful, None otherwise
        """
        if not self._type_registry:
            return None
        
        try:
            # Get type definition
            element_type = self._type_registry.get(type_id)
            if not element_type:
                return None
            
            # Get generator class
            generator_name = element_type.render_strategy.generator_name
            generator_class = self.get_generator_class(generator_name)
            if not generator_class:
                return None
            
            # Get default parameters
            params = element_type.get_default_params()
            
            # Create generator instance
            generator = generator_class(**params)
            return generator
            
        except Exception as e:
            self.logger.error(f"Failed to create generator from type {type_id}: {e}")
            return None
    
    def _get_category_for_generator(self, generator_name: str) -> str:
        """
        Map generator names to type categories.
        
        Args:
            generator_name: Name of the generator
            
        Returns:
            Category string
        """
        category_mapping = {
            'parchment': 'backgrounds',
            'enso': 'glyphs',
            'sigil': 'glyphs',
            'giraffe': 'creatures',
            'kangaroo': 'creatures',
            'divider': 'ui',
            'orb': 'ui'
        }
        return category_mapping.get(generator_name, 'backgrounds')
    
    def get_type_info(self, type_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a type.
        
        Args:
            type_id: Type ID to get info for
            
        Returns:
            Dictionary with type information or None
        """
        if not self._type_registry:
            return None
        
        try:
            element_type = self._type_registry.get(type_id)
            if not element_type:
                return None
            
            # Check if corresponding generator exists
            generator_name = element_type.render_strategy.generator_name
            has_generator = self.is_registered(generator_name)
            
            return {
                'id': element_type.id,
                'name': element_type.name,
                'description': element_type.description,
                'category': element_type.category,
                'tags': element_type.tags,
                'version': element_type.version,
                'has_generator': has_generator,
                'generator_name': generator_name,
                'usage_count': element_type.usage_count,
                'variants_count': len(element_type.variants),
                'has_diversity_config': element_type.diversity_config is not None,
                'created_at': element_type.created_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get type info for {type_id}: {e}")
            return None
    
    # ==================== DynamicGeneratorLoader Integration Methods ====================
    
    def get_dynamic_loader(self) -> Optional["DynamicGeneratorLoader"]:
        """
        Get the DynamicGeneratorLoader instance.
        
        Returns:
            DynamicGeneratorLoader instance if available, None otherwise
        """
        return self._dynamic_loader
    
    def create_generator_from_type_id(self, type_id: str, **kwargs) -> Optional[BaseGenerator]:
        """
        Create a generator instance from a type ID using DynamicGeneratorLoader.
        
        Args:
            type_id: Type ID to create generator for
            **kwargs: Additional parameters for generator creation
            
        Returns:
            Generator instance if successful, None otherwise
        """
        if not self._dynamic_loader:
            self.logger.warning("DynamicGeneratorLoader not available")
            return None
        
        try:
            return self._dynamic_loader.create_generator_from_type_id(type_id, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create generator from type {type_id}: {e}")
            return None
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of types supported by the DynamicGeneratorLoader.
        
        Returns:
            List of supported type IDs
        """
        if not self._dynamic_loader:
            return []
        
        try:
            return self._dynamic_loader.get_supported_types()
        except Exception as e:
            self.logger.error(f"Failed to get supported types: {e}")
            return []
    
    def get_type_info_from_loader(self, type_id: str) -> Optional[Dict[str, Any]]:
        """
        Get type information from DynamicGeneratorLoader.
        
        Args:
            type_id: Type ID to get info for
            
        Returns:
            Dictionary with type information or None
        """
        if not self._dynamic_loader:
            return None
        
        try:
            return self._dynamic_loader.get_type_info(type_id)
        except Exception as e:
            self.logger.error(f"Failed to get type info from loader for {type_id}: {e}")
            return None
    
    def validate_type_support(self, type_id: str) -> Dict[str, bool]:
        """
        Validate if a type is supported by the system.
        
        Args:
            type_id: Type ID to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'exists_in_registry': False,
            'has_generator_class': False,
            'supported_by_loader': False,
            'has_type_definition': False
        }
        
        try:
            # Check if type exists in registry
            available_types = self.get_available_types()
            result['exists_in_registry'] = type_id in available_types
            
            # Check if corresponding generator class exists
            if result['exists_in_registry']:
                element_type = self._type_registry.get(type_id)
                if element_type:
                    result['has_type_definition'] = True
                    generator_name = element_type.render_strategy.generator_name
                    result['has_generator_class'] = self.is_registered(generator_name)
            
            # Check if supported by DynamicGeneratorLoader
            if self._dynamic_loader:
                supported_types = self.get_supported_types()
                result['supported_by_loader'] = type_id in supported_types
            
        except Exception as e:
            self.logger.error(f"Error validating type support for {type_id}: {e}")
        
        return result
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive integration statistics.
        
        Returns:
            Dictionary with integration statistics
        """
        stats = {
            'type_system_available': HAS_TYPE_SYSTEM,
            'dynamic_loader_available': HAS_DYNAMIC_LOADER,
            'total_generators': len(self._generators),
            'total_types': len(self.get_available_types()) if self._type_registry else 0,
            'supported_types': len(self.get_supported_types()),
            'integration_status': 'fully_integrated'
        }
        
        if not HAS_TYPE_SYSTEM:
            stats['integration_status'] = 'type_system_disabled'
        elif not HAS_DYNAMIC_LOADER:
            stats['integration_status'] = 'dynamic_loader_disabled'
        elif not self._dynamic_loader:
            stats['integration_status'] = 'loader_initialization_failed'
        
        return stats