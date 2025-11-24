"""
Preset System for Advanced Generation Parameters

This module provides predefined parameter sets for consistent asset generation
across different types with various styles and quality levels.
"""

from typing import Dict, Any, Optional, List
from .schemas import GenerationParameters
import copy


# Preset definitions for different styles and use cases
PRESETS = {
    "minimal": {
        "complexity": 0.2,
        "quality": "low",
        "style_preset": "minimal",
        "randomness": 0.1,
        "contrast": 0.8,
        "brightness": 1.1,
        "saturation": 0.7,
        "resolution_multiplier": 1.0,
        "anti_aliasing": False
    },
    "detailed": {
        "complexity": 0.9,
        "quality": "high",
        "style_preset": "detailed",
        "randomness": 0.6,
        "contrast": 1.2,
        "brightness": 1.0,
        "saturation": 1.3,
        "resolution_multiplier": 2.0,
        "anti_aliasing": True
    },
    "chaotic": {
        "complexity": 0.8,
        "quality": "medium",
        "style_preset": "chaotic",
        "randomness": 0.9,
        "contrast": 1.5,
        "brightness": 0.9,
        "saturation": 1.8,
        "resolution_multiplier": 1.0,
        "anti_aliasing": True
    },
    "ordered": {
        "complexity": 0.7,
        "quality": "ultra",
        "style_preset": "ordered",
        "randomness": 0.1,
        "contrast": 1.3,
        "brightness": 1.1,
        "saturation": 0.8,
        "resolution_multiplier": 1.5,
        "anti_aliasing": True
    },
    # Asset-specific presets
    "parchment_ancient": {
        "base_color": "#2a2520",
        "complexity": 0.6,
        "quality": "high",
        "style_preset": "minimal",
        "randomness": 0.4,
        "contrast": 0.9,
        "brightness": 0.8,
        "saturation": 0.5,
        "color_palette": ["#1a1510", "#3a2f25", "#2a2520", "#4a3f35"]
    },
    "parchment_pristine": {
        "base_color": "#d4c5b0",
        "complexity": 0.3,
        "quality": "medium",
        "style_preset": "minimal",
        "randomness": 0.2,
        "contrast": 0.95,
        "brightness": 1.2,
        "saturation": 0.6,
        "color_palette": ["#e4d5c0", "#d4c5b0", "#c4b5a0", "#b4a590"]
    },
    "enso_meditative": {
        "base_color": "#000000",
        "complexity": 0.4,
        "quality": "medium",
        "style_preset": "minimal",
        "randomness": 0.3,
        "contrast": 1.0,
        "brightness": 1.0,
        "saturation": 0.0,
        "color_palette": ["#000000", "#1a1a1a", "#333333", "#666666"]
    },
    "enso_energetic": {
        "base_color": "#8b0000",
        "complexity": 0.8,
        "quality": "high",
        "style_preset": "chaotic",
        "randomness": 0.8,
        "contrast": 1.4,
        "brightness": 1.1,
        "saturation": 1.5,
        "color_palette": ["#8b0000", "#a52a2a", "#cd5c5c", "#dc143c"]
    },
    "sigil_geometric": {
        "base_color": "#ffd700",
        "complexity": 0.85,
        "quality": "ultra",
        "style_preset": "ordered",
        "randomness": 0.2,
        "contrast": 1.6,
        "brightness": 1.0,
        "saturation": 1.2,
        "resolution_multiplier": 2.5,
        "anti_aliasing": True,
        "color_palette": ["#ffd700", "#ffed4e", "#ffbf00", "#e6ac00"]
    },
    "sigil_chaotic": {
        "base_color": "#4a2d82",
        "complexity": 0.9,
        "quality": "high",
        "style_preset": "chaotic",
        "randomness": 0.95,
        "contrast": 1.8,
        "brightness": 0.9,
        "saturation": 2.0,
        "color_palette": ["#2d1b69", "#1a0f4c", "#4a2d82", "#6b3fa0"]
    },
    "giraffe_playful": {
        "base_color": "#000000",
        "complexity": 0.7,
        "quality": "high",
        "style_preset": "detailed",
        "randomness": 0.7,
        "contrast": 1.1,
        "brightness": 1.0,
        "saturation": 1.0,
        "color_palette": ["#000000", "#2c2c2c", "#1a1a1a", "#404040"]
    },
    "giraffe_majestic": {
        "base_color": "#ffbf00",
        "complexity": 0.8,
        "quality": "ultra",
        "style_preset": "detailed",
        "randomness": 0.5,
        "contrast": 1.3,
        "brightness": 1.2,
        "saturation": 1.4,
        "resolution_multiplier": 1.8,
        "color_palette": ["#ffbf00", "#e6ac00", "#cc9900", "#b38600"]
    },
    "kangaroo_bouncy": {
        "base_color": "#8b4513",
        "complexity": 0.6,
        "quality": "medium",
        "style_preset": "chaotic",
        "randomness": 0.8,
        "contrast": 1.2,
        "brightness": 1.1,
        "saturation": 1.1,
        "color_palette": ["#8b4513", "#a0522d", "#cd853f", "#daa520"]
    },
    "kangaroo_steady": {
        "base_color": "#654321",
        "complexity": 0.5,
        "quality": "high",
        "style_preset": "ordered",
        "randomness": 0.3,
        "contrast": 1.1,
        "brightness": 1.0,
        "saturation": 0.9,
        "color_palette": ["#654321", "#8b7355", "#a0826d", "#b89373"]
    },
    # Quality-focused presets
    "ultra_hd": {
        "quality": "ultra",
        "resolution_multiplier": 4.0,
        "anti_aliasing": True,
        "complexity": 0.9,
        "contrast": 1.1,
        "brightness": 1.0,
        "saturation": 1.1
    },
    "fast_generation": {
        "quality": "low",
        "resolution_multiplier": 0.75,
        "anti_aliasing": False,
        "complexity": 0.4,
        "randomness": 0.3
    },
    "balanced": {
        "quality": "medium",
        "resolution_multiplier": 1.0,
        "anti_aliasing": True,
        "complexity": 0.6,
        "randomness": 0.5,
        "contrast": 1.0,
        "brightness": 1.0,
        "saturation": 1.0
    },
    # Style-focused presets
    "noir": {
        "style_preset": "minimal",
        "contrast": 2.0,
        "brightness": 0.7,
        "saturation": 0.0,
        "complexity": 0.3,
        "randomness": 0.2,
        "quality": "medium"
    },
    "vibrant": {
        "style_preset": "chaotic",
        "contrast": 1.3,
        "brightness": 1.2,
        "saturation": 2.0,
        "complexity": 0.8,
        "randomness": 0.7,
        "quality": "high"
    },
    "soft": {
        "style_preset": "minimal",
        "contrast": 0.7,
        "brightness": 1.3,
        "saturation": 0.5,
        "complexity": 0.4,
        "randomness": 0.3,
        "quality": "medium",
        "anti_aliasing": True
    },
    # Resolution presets
    "web_optimized": {
        "width": 512,
        "height": 512,
        "quality": "medium",
        "resolution_multiplier": 0.5,
        "compression": 90,
        "format": "webp"
    },
    "print_ready": {
        "width": 2048,
        "height": 2048,
        "quality": "ultra",
        "resolution_multiplier": 2.0,
        "format": "png",
        "compression": 100
    },
    "mobile_friendly": {
        "width": 256,
        "height": 256,
        "quality": "low",
        "resolution_multiplier": 0.25,
        "compression": 80,
        "format": "jpg"
    }
}


class PresetManager:
    """
    Manager class for handling preset operations and application.
    """
    
    def __init__(self):
        self.presets = copy.deepcopy(PRESETS)
        self.custom_presets = {}
    
    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Get a preset by name.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            Dictionary containing preset parameters
        """
        # Check custom presets first
        if preset_name in self.custom_presets:
            return copy.deepcopy(self.custom_presets[preset_name])
        
        # Check built-in presets
        if preset_name not in self.presets:
            raise ValueError(f"Preset '{preset_name}' not found")
        
        return copy.deepcopy(self.presets[preset_name])
    
    def apply_preset(self, base_parameters: GenerationParameters, preset_name: str, 
                    custom_overrides: Optional[Dict[str, Any]] = None) -> GenerationParameters:
        """
        Apply a preset to base parameters.
        
        Args:
            base_parameters: Base GenerationParameters object
            preset_name: Name of the preset to apply
            custom_overrides: Optional custom parameter overrides
            
        Returns:
            New GenerationParameters object with preset applied
        """
        # Get preset parameters
        preset_params = self.get_preset(preset_name)
        
        # Create a copy of base parameters
        result = copy.deepcopy(base_parameters)
        
        # Apply preset parameters
        for key, value in preset_params.items():
            if hasattr(result, key):
                setattr(result, key, value)
        
        # Apply custom overrides if provided
        if custom_overrides:
            for key, value in custom_overrides.items():
                if hasattr(result, key):
                    setattr(result, key, value)
        
        return result
    
    def create_custom_preset(self, name: str, parameters: Dict[str, Any]):
        """
        Create a custom preset.
        
        Args:
            name: Name for the custom preset
            parameters: Dictionary of preset parameters
        """
        if not name or not name.strip():
            raise ValueError("Preset name cannot be empty")
        
        # Validate name format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name.strip()):
            raise ValueError("Preset name can only contain letters, numbers, hyphens, and underscores")
        
        self.custom_presets[name.strip()] = copy.deepcopy(parameters)
    
    def delete_custom_preset(self, name: str):
        """
        Delete a custom preset.
        
        Args:
            name: Name of the custom preset to delete
        """
        if name not in self.custom_presets:
            raise ValueError(f"Custom preset '{name}' not found")
        
        del self.custom_presets[name]
    
    def list_presets(self, include_custom: bool = True) -> List[str]:
        """
        List all available preset names.
        
        Args:
            include_custom: Whether to include custom presets
            
        Returns:
            List of preset names
        """
        presets = list(self.presets.keys())
        
        if include_custom:
            presets.extend(list(self.custom_presets.keys()))
        
        return sorted(presets)
    
    def get_presets_by_category(self) -> Dict[str, List[str]]:
        """
        Get presets organized by category.
        
        Returns:
            Dictionary mapping categories to preset names
        """
        categories = {
            "style": ["minimal", "detailed", "chaotic", "ordered"],
            "quality": ["balanced", "fast_generation", "ultra_hd"],
            "asset_specific": [
                "parchment_ancient", "parchment_pristine",
                "enso_meditative", "enso_energetic",
                "sigil_geometric", "sigil_chaotic",
                "giraffe_playful", "giraffe_majestic",
                "kangaroo_bouncy", "kangaroo_steady"
            ],
            "resolution": ["web_optimized", "print_ready", "mobile_friendly"],
            "mood": ["noir", "vibrant", "soft"]
        }
        
        # Add custom presets to a separate category
        if self.custom_presets:
            categories["custom"] = list(self.custom_presets.keys())
        
        return categories
    
    def get_preset_info(self, preset_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            Dictionary containing preset information
        """
        preset_params = self.get_preset(preset_name)
        
        # Determine preset category
        categories = self.get_presets_by_category()
        category = "unknown"
        
        for cat_name, presets in categories.items():
            if preset_name in presets:
                category = cat_name
                break
        
        # Generate description based on parameters
        style = preset_params.get("style_preset", "custom")
        quality = preset_params.get("quality", "medium")
        complexity = preset_params.get("complexity", 0.5)
        randomness = preset_params.get("randomness", 0.5)
        
        description = f"{style.title()} style with {quality} quality"
        if complexity > 0.7:
            description += ", high complexity"
        elif complexity < 0.3:
            description += ", low complexity"
        
        if randomness > 0.7:
            description += ", very random"
        elif randomness < 0.3:
            description += ", deterministic"
        
        return {
            "name": preset_name,
            "category": category,
            "description": description,
            "parameters": preset_params,
            "is_custom": preset_name in self.custom_presets
        }
    
    def validate_preset_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate preset parameters.
        
        Args:
            parameters: Dictionary of preset parameters to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check valid parameter names
        valid_params = {
            'width', 'height', 'seed', 'quality', 'resolution_multiplier', 'anti_aliasing',
            'color_palette', 'base_color', 'contrast', 'brightness', 'saturation',
            'style_preset', 'complexity', 'randomness', 'format', 'compression'
        }
        
        for param in parameters:
            if param not in valid_params:
                errors.append(f"Unknown parameter: {param}")
        
        # Check parameter values
        if 'width' in parameters:
            width = parameters['width']
            if not isinstance(width, int) or not (64 <= width <= 2048):
                errors.append(f"Width must be an integer between 64 and 2048, got {width}")
        
        if 'height' in parameters:
            height = parameters['height']
            if not isinstance(height, int) or not (64 <= height <= 2048):
                errors.append(f"Height must be an integer between 64 and 2048, got {height}")
        
        if 'quality' in parameters:
            valid_qualities = ['low', 'medium', 'high', 'ultra']
            if parameters['quality'] not in valid_qualities:
                errors.append(f"Quality must be one of {valid_qualities}, got {parameters['quality']}")
        
        if 'style_preset' in parameters:
            valid_styles = ['minimal', 'detailed', 'chaotic', 'ordered']
            if parameters['style_preset'] not in valid_styles:
                errors.append(f"Style preset must be one of {valid_styles}, got {parameters['style_preset']}")
        
        if 'contrast' in parameters:
            contrast = parameters['contrast']
            if not isinstance(contrast, (int, float)) or not (0.1 <= contrast <= 3.0):
                errors.append(f"Contrast must be between 0.1 and 3.0, got {contrast}")
        
        if 'brightness' in parameters:
            brightness = parameters['brightness']
            if not isinstance(brightness, (int, float)) or not (0.1 <= brightness <= 3.0):
                errors.append(f"Brightness must be between 0.1 and 3.0, got {brightness}")
        
        if 'saturation' in parameters:
            saturation = parameters['saturation']
            if not isinstance(saturation, (int, float)) or not (0.0 <= saturation <= 3.0):
                errors.append(f"Saturation must be between 0.0 and 3.0, got {saturation}")
        
        if 'complexity' in parameters:
            complexity = parameters['complexity']
            if not isinstance(complexity, (int, float)) or not (0.0 <= complexity <= 1.0):
                errors.append(f"Complexity must be between 0.0 and 1.0, got {complexity}")
        
        if 'randomness' in parameters:
            randomness = parameters['randomness']
            if not isinstance(randomness, (int, float)) or not (0.0 <= randomness <= 1.0):
                errors.append(f"Randomness must be between 0.0 and 1.0, got {randomness}")
        
        return errors
    
    def export_presets(self) -> Dict[str, Any]:
        """
        Export all presets to a dictionary.
        
        Returns:
            Dictionary containing all presets
        """
        return {
            "built_in": self.presets,
            "custom": self.custom_presets
        }
    
    def import_presets(self, preset_data: Dict[str, Any]):
        """
        Import presets from a dictionary.
        
        Args:
            preset_data: Dictionary containing preset definitions
        """
        if "custom" in preset_data:
            for name, params in preset_data["custom"].items():
                errors = self.validate_preset_parameters(params)
                if errors:
                    raise ValueError(f"Invalid parameters for preset '{name}': {errors}")
                self.create_custom_preset(name, params)


# Global preset manager instance
preset_manager = PresetManager()


def get_preset_manager() -> PresetManager:
    """
    Get the global preset manager instance.
    
    Returns:
        PresetManager instance
    """
    return preset_manager


def apply_preset_to_parameters(base_params: GenerationParameters, preset_name: str, 
                             custom_overrides: Optional[Dict[str, Any]] = None) -> GenerationParameters:
    """
    Convenience function to apply a preset to parameters.
    
    Args:
        base_params: Base GenerationParameters object
        preset_name: Name of the preset to apply
        custom_overrides: Optional custom parameter overrides
        
    Returns:
        New GenerationParameters object with preset applied
    """
    return preset_manager.apply_preset(base_params, preset_name, custom_overrides)