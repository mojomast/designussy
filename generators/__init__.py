"""
Generators Package

This package contains the modular asset generator system for NanoBanana.
It provides a plugin-based architecture for extensible asset generation.
"""

# Import all generator classes for easy access
from .base_generator import BaseGenerator
from .parchment_generator import ParchmentGenerator
from .enso_generator import EnsoGenerator
from .sigil_generator import SigilGenerator
from .giraffe_generator import GiraffeGenerator
from .kangaroo_generator import KangarooGenerator
from .directed_generator import DirectedGenerator

# Import registry and factory
from .registry import GeneratorRegistry
from .factory import GeneratorFactory
from .config import GeneratorConfig

# Version information
__version__ = "2.0.0"
__author__ = "NanoBanana Generator System"

# Default registry instance
default_registry = GeneratorRegistry()
default_config = GeneratorConfig()

# Register built-in generators BEFORE creating factory
default_registry.register("parchment", ParchmentGenerator)
default_registry.register("enso", EnsoGenerator)
default_registry.register("sigil", SigilGenerator)
default_registry.register("giraffe", GiraffeGenerator)
default_registry.register("kangaroo", KangarooGenerator)
default_registry.register("directed", DirectedGenerator)

# Factory uses the registered registry
default_factory = GeneratorFactory(registry=default_registry)

# Convenience functions
def get_generator(generator_type: str, **kwargs):
    """
    Get a generator instance by type name.
    
    Args:
        generator_type: Type of generator to create
        **kwargs: Generator initialization parameters
        
    Returns:
        Generator instance
        
    Raises:
        ValueError: If generator type is not found
    """
    return default_factory.create_generator(generator_type, **kwargs)

def list_generators():
    """
    List all available generator types.
    
    Returns:
        List of generator type names
    """
    return default_registry.list_generators()

def get_generator_info(generator_type: str):
    """
    Get information about a specific generator.
    
    Args:
        generator_type: Type of generator to get info about
        
    Returns:
        Dictionary with generator information
        
    Raises:
        ValueError: If generator type is not found
    """
    if generator_type not in default_registry._generators:
        raise ValueError(f"Unknown generator type: {generator_type}")
    
    generator_class = default_registry._generators[generator_type]
    config = default_config.get_defaults(generator_type)
    
    return {
        'type': generator_type,
        'class_name': generator_class.__name__,
        'module': generator_class.__module__,
        'description': getattr(generator_class, '__doc__', ''),
        'default_config': config
    }

# Main API exports
__all__ = [
    # Base classes
    'BaseGenerator',
    
    # Generator implementations
    'ParchmentGenerator',
    'EnsoGenerator', 
    'SigilGenerator',
    'GiraffeGenerator',
    'KangarooGenerator',
    'DirectedGenerator',
    
    # System components
    'GeneratorRegistry',
    'GeneratorFactory', 
    'GeneratorConfig',
    
    # Convenience functions
    'get_generator',
    'list_generators',
    'get_generator_info',
    
    # Default instances
    'default_registry',
    'default_factory',
    'default_config'
]