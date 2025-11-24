"""
Advanced Generation Parameter Schemas

This module defines comprehensive Pydantic models for advanced generation parameters
including quality controls, color palettes, style presets, and validation rules.
"""

from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field, validator
import re


class GenerationParameters(BaseModel):
    """
    Comprehensive generation parameters with validation and defaults.
    
    This model provides fine-grained control over asset generation including:
    - Basic dimensions and seed control
    - Quality and resolution settings
    - Color palette and styling options
    - Output format and compression controls
    """
    
    # Basic parameters
    width: int = Field(512, ge=64, le=2048, description="Image width in pixels")
    height: int = Field(512, ge=64, le=2048, description="Image height in pixels")
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    
    # Quality parameters
    quality: Literal["low", "medium", "high", "ultra"] = Field(
        "medium", 
        description="Generation quality level affecting detail and processing time"
    )
    resolution_multiplier: float = Field(
        1.0, 
        ge=0.5, 
        le=4.0, 
        description="Multiplier for base resolution (affects detail level)"
    )
    anti_aliasing: bool = Field(True, description="Enable anti-aliasing for smoother edges")
    
    # Color parameters
    color_palette: Optional[List[str]] = Field(
        None, 
        description="Custom color palette as list of hex colors (e.g., ['#FF0000', '#00FF00'])"
    )
    base_color: Optional[str] = Field(
        None, 
        description="Base color as hex string (e.g., '#FF0000')"
    )
    contrast: float = Field(1.0, ge=0.1, le=3.0, description="Contrast adjustment factor")
    brightness: float = Field(1.0, ge=0.1, le=3.0, description="Brightness adjustment factor")
    saturation: float = Field(1.0, ge=0.0, le=3.0, description="Saturation adjustment factor")
    
    # Style parameters
    style_preset: Optional[Literal["minimal", "detailed", "chaotic", "ordered"]] = Field(
        None, 
        description="Predefined style preset for consistent appearance"
    )
    complexity: float = Field(0.5, ge=0.0, le=1.0, description="Detail complexity (0.0=simple, 1.0=complex)")
    randomness: float = Field(0.5, ge=0.0, le=1.0, description="Random variation amount (0.0=deterministic, 1.0=very random)")
    
    # Output parameters
    format: Literal["png", "jpg", "webp"] = Field("png", description="Output image format")
    compression: int = Field(95, ge=1, le=100, description="Compression quality (1-100)")
    
    @validator('color_palette')
    def validate_color_palette(cls, v):
        """Validate color palette format."""
        if v is None:
            return v
            
        if len(v) == 0:
            raise ValueError("Color palette cannot be empty")
            
        if len(v) > 10:
            raise ValueError("Color palette cannot exceed 10 colors")
            
        # Validate hex color format
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for color in v:
            if not hex_pattern.match(color):
                raise ValueError(f"Invalid hex color format: {color}. Expected format: #RRGGBB")
                
        return v
    
    @validator('base_color')
    def validate_base_color(cls, v):
        """Validate base color format."""
        if v is None:
            return v
            
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        if not hex_pattern.match(v):
            raise ValueError(f"Invalid hex color format: {v}. Expected format: #RRGGBB")
            
        return v
    
    def get_effective_dimensions(self) -> tuple[int, int]:
        """
        Get effective dimensions after applying resolution multiplier.
        
        Returns:
            Tuple of (effective_width, effective_height)
        """
        effective_width = int(self.width * self.resolution_multiplier)
        effective_height = int(self.height * self.resolution_multiplier)
        
        # Ensure dimensions don't exceed limits
        effective_width = max(64, min(2048, effective_width))
        effective_height = max(64, min(2048, effective_height))
        
        return (effective_width, effective_height)
    
    def get_quality_settings(self) -> dict:
        """
        Get quality-specific settings based on quality level.
        
        Returns:
            Dictionary with quality-related settings
        """
        quality_settings = {
            "low": {
                "noise_samples": 50,
                "blur_radius": 0.5,
                "detail_level": 0.3,
                "render_passes": 1
            },
            "medium": {
                "noise_samples": 100,
                "blur_radius": 1.0,
                "detail_level": 0.6,
                "render_passes": 1
            },
            "high": {
                "noise_samples": 200,
                "blur_radius": 1.2,
                "detail_level": 0.8,
                "render_passes": 2
            },
            "ultra": {
                "noise_samples": 400,
                "blur_radius": 1.5,
                "detail_level": 1.0,
                "render_passes": 3
            }
        }
        
        return quality_settings.get(self.quality, quality_settings["medium"])
    
    def get_style_settings(self) -> dict:
        """
        Get style-specific settings based on style preset.
        
        Returns:
            Dictionary with style-related settings
        """
        if self.style_preset is None:
            return {
                "geometric_precision": 0.5,
                "organic_flow": 0.5,
                "edge_smoothness": 0.5,
                "texture_intensity": 0.5
            }
        
        style_settings = {
            "minimal": {
                "geometric_precision": 0.9,
                "organic_flow": 0.1,
                "edge_smoothness": 0.9,
                "texture_intensity": 0.2
            },
            "detailed": {
                "geometric_precision": 0.7,
                "organic_flow": 0.6,
                "edge_smoothness": 0.7,
                "texture_intensity": 0.8
            },
            "chaotic": {
                "geometric_precision": 0.2,
                "organic_flow": 0.9,
                "edge_smoothness": 0.3,
                "texture_intensity": 0.9
            },
            "ordered": {
                "geometric_precision": 0.95,
                "organic_flow": 0.2,
                "edge_smoothness": 0.95,
                "texture_intensity": 0.4
            }
        }
        
        return style_settings.get(self.style_preset, style_settings["detailed"])
    
    def apply_color_adjustments(self, base_color: tuple) -> tuple:
        """
        Apply color adjustments to a base color.
        
        Args:
            base_color: Base RGB color tuple
            
        Returns:
            Adjusted RGB color tuple
        """
        import colorsys
        
        # Convert RGB to HSV
        r, g, b = [x / 255.0 for x in base_color]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        # Apply adjustments
        s = max(0.0, min(1.0, s * self.saturation))
        v = max(0.0, min(1.0, v * self.brightness))
        
        # Apply contrast by shifting away from middle gray
        contrast_factor = self.contrast
        if contrast_factor != 1.0:
            # Shift values away from 0.5 (middle gray)
            v = 0.5 + (v - 0.5) * contrast_factor
            s = 0.5 + (s - 0.5) * contrast_factor
            
            # Clamp to valid ranges
            v = max(0.0, min(1.0, v))
            s = max(0.0, min(1.0, s))
        
        # Convert back to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Don't allow extra fields


class GenerationRequest(BaseModel):
    """
    API request model for generation with advanced parameters.
    
    Supports both individual asset generation and batch requests
    with proper validation and backward compatibility.
    """
    
    # Required fields
    asset_type: Literal["parchment", "enso", "sigil", "giraffe", "kangaroo"]
    
    # Advanced parameters
    parameters: Optional[GenerationParameters] = Field(
        default_factory=GenerationParameters,
        description="Advanced generation parameters"
    )
    
    # Legacy compatibility
    width: Optional[int] = Field(None, description="Legacy width parameter")
    height: Optional[int] = Field(None, description="Legacy height parameter")
    seed: Optional[int] = Field(None, description="Legacy seed parameter")
    
    @validator('width')
    def validate_width(cls, v):
        if v is not None and not (64 <= v <= 2048):
            raise ValueError("Width must be between 64 and 2048 pixels")
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if v is not None and not (64 <= v <= 2048):
            raise ValueError("Height must be between 64 and 2048 pixels")
        return v
    
    def get_final_parameters(self) -> GenerationParameters:
        """
        Merge legacy parameters with advanced parameters.
        
        Returns:
            Final GenerationParameters object with all values resolved
        """
        # Start with default parameters
        final_params = GenerationParameters()
        
        # Override with legacy parameters if provided
        if self.parameters:
            # Update with advanced parameters
            for field, value in self.parameters.dict().items():
                if value is not None:
                    setattr(final_params, field, value)
        
        # Override with legacy parameters (for backward compatibility)
        if self.width is not None:
            final_params.width = self.width
        if self.height is not None:
            final_params.height = self.height
        if self.seed is not None:
            final_params.seed = self.seed
            
        return final_params
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class PresetRequest(BaseModel):
    """
    Request model for applying predefined presets.
    
    Allows users to apply pre-configured parameter sets for
    consistent results across different generation types.
    """
    
    preset_name: str = Field(..., description="Name of the preset to apply")
    asset_type: Optional[Literal["parchment", "enso", "sigil", "giraffe", "kangaroo"]] = Field(
        None, 
        description="Asset type (some presets are asset-specific)"
    )
    custom_overrides: Optional[dict] = Field(
        None, 
        description="Custom parameter overrides to apply after preset"
    )
    
    @validator('preset_name')
    def validate_preset_name(cls, v):
        """Validate preset name format."""
        if not v or not v.strip():
            raise ValueError("Preset name cannot be empty")
        
        # Allow alphanumeric characters, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Preset name can only contain letters, numbers, hyphens, and underscores")
        
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class ParameterValidationResult(BaseModel):
    """
    Result model for parameter validation.
    
    Provides detailed feedback about parameter validation including
    warnings, errors, and suggested corrections.
    """
    
    is_valid: bool = Field(..., description="Whether the parameters are valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Suggested improvements")
    effective_parameters: Optional[GenerationParameters] = Field(
        None, 
        description="Final validated and resolved parameters"
    )
    
    def add_error(self, error: str):
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str):
        """Add a suggested improvement."""
        self.suggestions.append(suggestion)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True