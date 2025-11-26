"""
Element Type Schemas

This module defines the foundational Pydantic schemas for the dynamic
element type system in the NanoBanana project.

The schemas provide validation, serialization, and type safety for:
- ElementType: Core type definitions with metadata
- RenderStrategy: How types should be rendered/generated
- ElementVariant: Variations of a base type
- DiversityConfig: Configuration for variation strategies
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any
import json


class EngineType(str, Enum):
    """Supported rendering engines."""
    PIL = "pil"
    CAIRO = "cairo"
    SKIA = "skia"


class VariationStrategy(str, Enum):
    """Available variation strategies for element types."""
    JITTER = "jitter"
    STRATEGY_POOL = "strategy_pool"
    SEEDED = "seeded"
    PARAMETER_SAMPLING = "parameter_sampling"
    COMPOSITIONAL = "compositional"


class RenderStrategy(BaseModel):
    """
    Defines how an element type should be rendered.
    
    Specifies the engine and generator to use for creating assets
    of this type.
    """
    engine: EngineType = Field(..., description="Rendering engine to use")
    generator_name: str = Field(..., min_length=1, description="Name of the generator class")
    
    class Config:
        use_enum_values = True


class ElementVariant(BaseModel):
    """
    Represents a variation of an element type.
    
    Contains alternative parameters, styling, or configurations
    that can be applied to create diverse outputs from a single type.
    """
    variant_id: str = Field(..., description="Unique identifier for this variant")
    name: str = Field(..., min_length=1, description="Human-readable variant name")
    description: Optional[str] = Field(None, description="Description of this variant")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Variant-specific parameters")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Probability weight for this variant")
    
    @field_validator('variant_id')
    @classmethod
    def validate_variant_id(cls, v):
        """Ensure variant_id is alphanumeric with underscores."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Variant ID must be alphanumeric with optional underscores/hyphens")
        return v


class DiversityJitterConfig(BaseModel):
    """Configuration for jitter-based variation strategy."""
    jitter_amount: float = Field(0.1, ge=0.0, le=1.0, description="± percentage variation")
    affected_parameters: List[str] = Field(default_factory=list, description="Parameters to apply jitter to")


class DiversityStrategyPoolConfig(BaseModel):
    """Configuration for strategy pool variation strategy."""
    strategy_pool: List[Dict[str, Any]] = Field(..., description="Predefined parameter sets")
    
    @field_validator('strategy_pool')
    @classmethod
    def validate_strategy_pool(cls, v):
        """Ensure strategy pool has at least one strategy."""
        if not v or len(v) == 0:
            raise ValueError("Strategy pool must contain at least one strategy")
        return v


class DiversitySeededConfig(BaseModel):
    """Configuration for seeded variation strategy."""
    seed: int = Field(..., description="Base seed for deterministic variations")
    variation_strength: float = Field(0.05, ge=0.0, le=1.0, description="Strength of variations")


class DiversityParameterSamplingConfig(BaseModel):
    """Configuration for parameter sampling variation strategy."""
    distributions: Dict[str, Dict[str, Any]] = Field(..., description="Parameter distributions")
    
    @field_validator('distributions')
    @classmethod
    def validate_distributions(cls, v):
        """Validate distribution configurations."""
        for param_name, dist_config in v.items():
            if 'type' not in dist_config:
                raise ValueError(f"Distribution for {param_name} must specify a type")
            dist_type = dist_config['type']
            if dist_type not in ['normal', 'uniform', 'triangular', 'exponential']:
                raise ValueError(f"Unknown distribution type: {dist_type}")
        return v


class DiversityCompositionalConfig(BaseModel):
    """Configuration for compositional variation strategy."""
    composition: List[Dict[str, Any]] = Field(..., description="Ordered list of strategy compositions")


class DiversityConfig(BaseModel):
    """
    Configuration for diversity and variation strategies (Phase 4 Enhanced).
    
    Defines how an element type should create diverse outputs
    through various mathematical and probabilistic strategies.
    
    Phase 4 enhancements:
    - Enhanced sampling strategies (Latin Hypercube, Sobol, Halton)
    - Parameter diversity weights
    - Constraint validation
    - Target diversity scores
    """
    strategy: VariationStrategy = Field(..., description="Primary variation strategy")
    jitter: Optional[DiversityJitterConfig] = None
    strategy_pool: Optional[DiversityStrategyPoolConfig] = None
    seeded: Optional[DiversitySeededConfig] = None
    parameter_sampling: Optional[DiversityParameterSamplingConfig] = None
    compositional: Optional[DiversityCompositionalConfig] = None
    
    # Phase 4 enhancements - Diversity configuration
    target_diversity_score: float = Field(0.7, ge=0.0, le=1.0, description="Target diversity score (0-1)")
    diversity_weights: Dict[str, float] = Field(default_factory=dict, description="Per-parameter diversity importance weights")
    sampling_strategy: str = Field("random", description="Sampling strategy: 'random', 'latin_hypercube', 'sobol', 'halton'")
    constraints: List[str] = Field(default_factory=list, description="Constraints for valid parameter combinations")
    
    # Global settings (backward compatibility)
    diversity_target: float = Field(0.7, ge=0.0, le=1.0, description="Legacy: Target diversity score (deprecated)")
    max_variations: int = Field(100, ge=1, le=10000, description="Maximum number of variations to generate")
    
    @model_validator(mode='after')
    def validate_strategy_config(self):
        """Ensure strategy-specific config is provided."""
        strategy = self.strategy
        
        # Convert string to enum if needed
        if isinstance(strategy, str):
            try:
                self.strategy = VariationStrategy(strategy)
            except ValueError:
                raise ValueError(f"Unknown strategy: {strategy}")
        
        # Map enum to required config field
        strategy_configs = {
            VariationStrategy.JITTER: self.jitter,
            VariationStrategy.STRATEGY_POOL: self.strategy_pool,
            VariationStrategy.SEEDED: self.seeded,
            VariationStrategy.PARAMETER_SAMPLING: self.parameter_sampling,
            VariationStrategy.COMPOSITIONAL: self.compositional
        }
        
        required_config_map = {
            VariationStrategy.JITTER: 'jitter',
            VariationStrategy.STRATEGY_POOL: 'strategy_pool',
            VariationStrategy.SEEDED: 'seeded',
            VariationStrategy.PARAMETER_SAMPLING: 'parameter_sampling',
            VariationStrategy.COMPOSITIONAL: 'compositional'
        }
        
        required_config = required_config_map.get(self.strategy)
        if required_config:
            config_value = getattr(self, required_config)
            if not config_value:
                raise ValueError(f"Strategy '{self.strategy}' requires '{required_config}' configuration")
        
        return self


class ElementType(BaseModel):
    """
    Core element type definition schema.
    
    Represents a dynamic, LLM-definable type for asset generation.
    Contains all metadata, parameters, and configuration needed
    to create and manage element instances.
    """
    # Core identification
    id: str = Field(..., description="Unique type identifier")
    name: str = Field(..., min_length=1, description="Human-readable type name")
    description: str = Field("", description="Detailed description of this type")
    
    # Categorization
    category: str = Field(..., description="Type category (backgrounds/glyphs/creatures/ui)")
    tags: List[str] = Field(default_factory=list, description="Searchable tags for this type")
    
    # Rendering configuration
    render_strategy: RenderStrategy = Field(..., description="How this type should be rendered")
    
    # Parameter schema - flexible JSON schema for type parameters
    param_schema: Dict[str, Any] = Field(
        default_factory=dict, 
        description="JSON schema defining valid parameters for this type"
    )
    
    # Variations and diversity
    variants: List[ElementVariant] = Field(default_factory=list, description="Available type variants")
    diversity_config: Optional[DiversityConfig] = Field(None, description="Diversity strategy configuration")
    
    # Metadata
    created_by: str = Field("system", description="Creator identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # LLM integration
    llm_prompt: Optional[str] = Field(None, description="Original LLM prompt used to create this type")
    llm_model: Optional[str] = Field(None, description="LLM model used for creation")
    
    # Versioning
    version: str = Field("1.0.0", description="Semantic version of this type")
    parent_type_id: Optional[str] = Field(None, description="ID of parent type if derived")
    
    # Status and lifecycle
    is_active: bool = Field(True, description="Whether this type is currently active")
    is_template: bool = Field(False, description="Whether this is a template for type creation")
    usage_count: int = Field(0, description="Number of times this type has been used")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('id')
    @classmethod
    def validate_type_id(cls, v):
        """Ensure type ID follows naming conventions."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Type ID must be alphanumeric with optional underscores/hyphens")
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Ensure category is a valid option."""
        valid_categories = [
            'backgrounds', 'glyphs', 'creatures', 'ui', 'effects',
            'patterns', 'textures', 'decorations', 'symbols'
        ]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.dict()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElementType':
        """Create instance from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ElementType':
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls(**data)
    
    def get_default_params(self) -> Dict[str, Any]:
        """Get default parameters for this type based on param_schema."""
        # Extract defaults from param_schema if available
        defaults = {}
        if 'properties' in self.param_schema:
            for param_name, param_def in self.param_schema['properties'].items():
                if 'default' in param_def:
                    defaults[param_name] = param_def['default']
        
        # Add any variant-specific defaults if no variants or no params yet
        if not defaults and self.variants:
            # Use the first variant's parameters as defaults
            defaults = self.variants[0].parameters.copy()
        
        return defaults
    
    def add_variant(self, variant: ElementVariant) -> 'ElementType':
        """Add a new variant to this type."""
        # Check for duplicate variant IDs
        existing_ids = {v.variant_id for v in self.variants}
        if variant.variant_id in existing_ids:
            raise ValueError(f"Variant with ID '{variant.variant_id}' already exists")
        
        self.variants.append(variant)
        return self
    
    def remove_variant(self, variant_id: str) -> 'ElementType':
        """Remove a variant by ID."""
        self.variants = [v for v in self.variants if v.variant_id != variant_id]
        return self
    
    def get_variant(self, variant_id: str) -> Optional[ElementVariant]:
        """Get a variant by ID."""
        for variant in self.variants:
            if variant.variant_id == variant_id:
                return variant
        return None
    
    def get_effective_params(self, variant_id: Optional[str] = None, 
                           overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get effective parameters by merging defaults with variant and overrides."""
        params = self.get_default_params()
        
        # Apply variant parameters
        if variant_id:
            variant = self.get_variant(variant_id)
            if variant:
                params.update(variant.parameters)
        
        # Apply overrides
        if overrides:
            params.update(overrides)
        
        return params
    
    def increment_usage(self) -> 'ElementType':
        """Increment usage count for this type."""
        self.usage_count += 1
        return self
    
    def is_compatible_with(self, other: 'ElementType') -> bool:
        """Check if this type is compatible with another for composition."""
        return (self.render_strategy.engine == other.render_strategy.engine and
                self.category == other.category)
    
    def get_search_text(self) -> str:
        """Get searchable text for this type."""
        search_parts = [self.name, self.description, self.id]
        search_parts.extend(self.tags)
        
        # Add variant names and descriptions
        for variant in self.variants:
            search_parts.extend([variant.name, variant.description or ""])
        
        return " ".join(filter(None, search_parts)).lower()


# Utility functions for element type management

def validate_param_schema(schema: Dict[str, Any]) -> bool:
    """
    Validate a parameter schema structure.
    
    Args:
        schema: Parameter schema to validate
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not isinstance(schema, dict):
        raise ValueError("Parameter schema must be a dictionary")
    
    # Check for required JSON Schema fields
    if 'type' not in schema:
        schema['type'] = 'object'
    
    if schema.get('type') == 'object':
        if 'properties' not in schema:
            schema['properties'] = {}
    
    return True


def merge_type_configs(base_config: Dict[str, Any], 
                      override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two type configurations with override precedence.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration dictionary
    """
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_type_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged