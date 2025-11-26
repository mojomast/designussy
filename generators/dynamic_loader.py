"""
Dynamic Generator Loader

This module implements the DynamicGeneratorLoader class that bridges
the TypeRegistry system with generators, enabling dynamic, type-aware
asset generation based on ElementType definitions.

The loader handles:
- Mapping ElementType to appropriate generator classes
- Parameter transformation from ElementType.param_schema
- Integration with variation strategies from DiversityConfig
- Type validation and error handling
"""

from typing import Dict, Any, Optional, List, Union, Tuple
from PIL import Image
import logging
import copy

# Import type system components
try:
    from enhanced_design.type_registry import get_type_registry, TypeRegistry
    from enhanced_design.element_types import ElementType, RenderStrategy, DiversityConfig, ElementVariant
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    # Create mock classes for fallback
    class ElementType:
        pass
    class RenderStrategy:
        pass
    class DiversityConfig:
        pass
    class ElementVariant:
        pass

# Import generator components
from .base_generator import BaseGenerator
from .registry import GeneratorRegistry
from .variation_strategies import VariationEngine


class DynamicGeneratorLoader:
    """
    Dynamic generator loader that bridges ElementType definitions with generators.
    
    This class provides the core functionality for:
    - Loading generator classes based on ElementType.render_strategy
    - Transforming ElementType parameters to generator parameters
    - Applying diversity and variation strategies
    - Maintaining backward compatibility with existing generators
    """
    
    def __init__(self, 
                 generator_registry: Optional[GeneratorRegistry] = None,
                 type_registry: Optional[TypeRegistry] = None,
                 variation_engine: Optional[VariationEngine] = None):
        """
        Initialize the dynamic generator loader.
        
        Args:
            generator_registry: Generator registry instance
            type_registry: Type registry instance (optional)
            variation_engine: Variation engine for diversity strategies (optional)
        """
        self.generator_registry = generator_registry or GeneratorRegistry()
        self.type_registry = type_registry if HAS_TYPE_SYSTEM else None
        self.variation_engine = variation_engine or VariationEngine()
        self.logger = logging.getLogger(__name__)
        
        # ElementType to generator class mappings
        self._type_to_generator_map: Dict[str, str] = {}
        self._generator_to_types_map: Dict[str, List[str]] = {}
        
        # Build initial mappings from existing generators
        self._build_initial_mappings()
        
    def load_generator_from_type(self, 
                                element_type: ElementType,
                                variant_id: Optional[str] = None,
                                parameter_overrides: Optional[Dict[str, Any]] = None,
                                diversity_config: Optional[DiversityConfig] = None,
                                seed: Optional[int] = None) -> BaseGenerator:
        """
        Create a generator instance from an ElementType definition.
        
        Args:
            element_type: ElementType definition to load generator from
            variant_id: Optional variant ID to use
            parameter_overrides: Optional parameter overrides
            diversity_config: Optional diversity configuration
            seed: Optional seed for reproducible randomness
            
        Returns:
            Generator instance configured according to the ElementType
            
        Raises:
            ValueError: If generator type is not supported or parameters are invalid
            RuntimeError: If generator creation fails
        """
        if not HAS_TYPE_SYSTEM:
            raise RuntimeError("Type system not available - cannot load generator from type")
            
        # Validate element type
        if not isinstance(element_type, ElementType):
            raise ValueError(f"Expected ElementType, got {type(element_type)}")
        
        try:
            # Get render strategy
            render_strategy = element_type.render_strategy
            generator_name = render_strategy.generator_name
            
            # Validate generator exists
            if not self.generator_registry.is_registered(generator_name):
                available_generators = self.generator_registry.list_generators()
                raise ValueError(
                    f"Generator '{generator_name}' not found. "
                    f"Available generators: {available_generators}"
                )
            
            # Build parameter set
            parameters = self._build_generator_parameters(
                element_type=element_type,
                variant_id=variant_id,
                parameter_overrides=parameter_overrides,
                diversity_config=diversity_config,
                seed=seed
            )
            
            # Create generator instance
            generator = self.generator_registry.create_generator(
                generator_name, 
                **parameters
            )
            
            # Set type metadata if generator supports it
            if hasattr(generator, 'set_element_type'):
                generator.set_element_type(element_type)
            
            self.logger.info(
                f"Loaded generator '{generator_name}' from type '{element_type.id}'"
            )
            return generator
            
        except Exception as e:
            self.logger.error(f"Failed to load generator from type {element_type.id}: {e}")
            raise RuntimeError(f"Failed to load generator from type: {e}")
    
    def _build_generator_parameters(self,
                                  element_type: ElementType,
                                  variant_id: Optional[str] = None,
                                  parameter_overrides: Optional[Dict[str, Any]] = None,
                                  diversity_config: Optional[DiversityConfig] = None,
                                  seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Build parameter dictionary for generator from ElementType.
        
        Args:
            element_type: ElementType definition
            variant_id: Optional variant ID
            parameter_overrides: Optional parameter overrides
            diversity_config: Optional diversity configuration
            seed: Optional seed
            
        Returns:
            Dictionary of parameters for generator initialization
        """
        # Start with defaults from param_schema
        parameters = element_type.get_effective_params(
            variant_id=variant_id,
            overrides=parameter_overrides
        )
        
        # Apply diversity/variation strategies if provided
        if diversity_config or element_type.diversity_config:
            effective_diversity = diversity_config or element_type.diversity_config
            if effective_diversity and seed is not None:
                # Apply variation strategy
                parameters = self.variation_engine.apply_variations(
                    element_type=element_type,
                    base_params=parameters,
                    diversity_config=effective_diversity,
                    seed=seed
                )
        
        # Add seed if provided
        if seed is not None:
            parameters['seed'] = seed
            
        return parameters
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of ElementType IDs that can be loaded as generators.
        
        Returns:
            List of supported type IDs
        """
        if not self.type_registry:
            return []
        
        try:
            types = self.type_registry.list(active_only=True)
            supported_types = []
            
            for element_type in types:
                if self.is_type_supported(element_type):
                    supported_types.append(element_type.id)
                    
            return supported_types
        except Exception as e:
            self.logger.warning(f"Failed to get supported types: {e}")
            return []
    
    def is_type_supported(self, element_type: ElementType) -> bool:
        """
        Check if an ElementType is supported by any registered generator.
        
        Args:
            element_type: ElementType to check
            
        Returns:
            True if the type can be loaded by a generator
        """
        if not isinstance(element_type, ElementType):
            return False
            
        generator_name = element_type.render_strategy.generator_name
        return self.generator_registry.is_registered(generator_name)
    
    def get_type_info(self, type_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a type and its generator mapping.
        
        Args:
            type_id: ElementType ID to get info for
            
        Returns:
            Dictionary with type and generator information, or None
        """
        if not self.type_registry:
            return None
        
        try:
            element_type = self.type_registry.get(type_id)
            if not element_type:
                return None
                
            # Get basic type info
            info = {
                'type_id': element_type.id,
                'type_name': element_type.name,
                'category': element_type.category,
                'description': element_type.description,
                'supported': self.is_type_supported(element_type),
                'has_variants': len(element_type.variants) > 0,
                'has_diversity': element_type.diversity_config is not None,
                'variants_count': len(element_type.variants),
                'usage_count': element_type.usage_count,
                'generator_name': element_type.render_strategy.generator_name
            }
            
            # Add generator info if supported
            if info['supported']:
                generator_name = element_type.render_strategy.generator_name
                info['generator_info'] = self.generator_registry.get_generator_info(generator_name)
            
            # Add variation strategies info
            if element_type.diversity_config:
                info['diversity_strategy'] = element_type.diversity_config.strategy.value
                info['max_variations'] = element_type.diversity_config.max_variations
                info['diversity_target'] = element_type.diversity_config.diversity_target
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get type info for {type_id}: {e}")
            return None
    
    def create_generator_from_type_id(self,
                                    type_id: str,
                                    variant_id: Optional[str] = None,
                                    parameter_overrides: Optional[Dict[str, Any]] = None,
                                    diversity_config: Optional[DiversityConfig] = None,
                                    seed: Optional[int] = None) -> Optional[BaseGenerator]:
        """
        Convenience method to create generator from type ID.
        
        Args:
            type_id: ElementType ID
            variant_id: Optional variant ID
            parameter_overrides: Optional parameter overrides
            diversity_config: Optional diversity configuration
            seed: Optional seed
            
        Returns:
            Generator instance or None if type not found
        """
        if not self.type_registry:
            return None
            
        try:
            element_type = self.type_registry.get(type_id)
            if not element_type:
                return None
                
            return self.load_generator_from_type(
                element_type=element_type,
                variant_id=variant_id,
                parameter_overrides=parameter_overrides,
                diversity_config=diversity_config,
                seed=seed
            )
        except Exception as e:
            self.logger.error(f"Failed to create generator from type ID {type_id}: {e}")
            return None
    
    def _build_initial_mappings(self):
        """Build initial mappings between types and generators."""
        if not self.generator_registry:
            return
            
        # Get all registered generators
        generator_names = self.generator_registry.list_generators()
        
        # Build mapping from generator names to inferred type patterns
        for generator_name in generator_names:
            # Infer type ID from generator name (simple convention)
            type_id = f"{generator_name}_v1"
            
            self._type_to_generator_map[type_id] = generator_name
            
            if generator_name not in self._generator_to_types_map:
                self._generator_to_types_map[generator_name] = []
            self._generator_to_types_map[generator_name].append(type_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loader's state.
        
        Returns:
            Dictionary with loader statistics
        """
        stats = {
            'total_generators': len(self.generator_registry),
            'type_mappings': len(self._type_to_generator_map),
            'generator_mappings': len(self._generator_to_types_map),
            'type_system_available': HAS_TYPE_SYSTEM,
            'type_registry_connected': self.type_registry is not None,
            'variation_engine_available': self.variation_engine is not None
        }
        
        if self.type_registry:
            try:
                stats['available_types'] = len(self.get_supported_types())
                stats['total_types'] = len(self.type_registry.list(active_only=True))
            except:
                stats['available_types'] = 0
                stats['total_types'] = 0
        
        return stats
    
    def refresh_mappings(self):
        """Refresh type-to-generator mappings."""
        self._type_to_generator_map.clear()
        self._generator_to_types_map.clear()
        self._build_initial_mappings()
        self.logger.info("Refreshed type-to-generator mappings")
    
    def __repr__(self) -> str:
        """String representation of the loader."""
        return (f"DynamicGeneratorLoader("
                f"generators={len(self.generator_registry)}, "
                f"mappings={len(self._type_to_generator_map)}, "
                f"type_system={HAS_TYPE_SYSTEM})")