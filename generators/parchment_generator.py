"""
Parchment Generator

This module implements the Void Parchment texture generator, 
creating aged parchment backgrounds with realistic grain and weathering.
"""

from typing import Optional, Tuple, Union, Dict, Any
from PIL import Image, ImageOps
from .base_generator import BaseGenerator
from .schemas import GenerationParameters
from .color_utils import apply_palette_to_parameters
from .presets import get_preset_manager
import numpy as np


class ParchmentGenerator(BaseGenerator):
    """
    Generator for Void Parchment textures.
    
    Creates aged parchment backgrounds with heavy grain, scratches,
    and vignette effects for a weathered, ancient appearance.
    
    Supports advanced parameters including:
    - Quality controls and resolution settings
    - Custom color palettes and styling
    - Preset application
    - Enhanced weathering effects
    """
    
    def __init__(self, width: int = 1024, height: int = 1024, 
                 base_color: Optional[Tuple[int, int, int]] = None, 
                 noise_scale: float = 1.5, **kwargs):
        """
        Initialize the parchment generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels  
            base_color: RGB base color for parchment
            noise_scale: Intensity of grain texture
            **kwargs: Additional configuration options
        """
        if base_color is None:
            base_color = (15, 15, 18)
            
        super().__init__(
            width=width,
            height=height, 
            base_color=base_color,
            noise_scale=noise_scale,
            **kwargs
        )
        
        self.noise_scale = noise_scale
        self.preset_manager = get_preset_manager()
        
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate a void parchment texture.
        
        Args:
            **kwargs: Generation parameters including:
                - GenerationParameters object
                - Legacy parameters (width, height, seed, noise_scale)
                - Custom overrides
                
        Returns:
            PIL Image of the generated parchment texture
        """
        # Handle advanced parameters
        if 'parameters' in kwargs and isinstance(kwargs['parameters'], GenerationParameters):
            parameters = kwargs['parameters']
            
            # Validate parameters
            validation_result = self.validate_parameters(parameters)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid parameters: {validation_result.errors}")
            
            # Apply preset if specified
            if hasattr(parameters, 'style_preset') and parameters.style_preset:
                # Apply preset for parchment-specific styling
                preset_name = f"parchment_{parameters.style_preset}"
                try:
                    parameters = self.preset_manager.apply_preset(parameters, preset_name)
                except ValueError:
                    # Fall back to style preset only
                    pass
            
            # Apply to generator dimensions
            effective_width, effective_height = parameters.get_effective_dimensions()
            self.width = effective_width
            self.height = effective_height
            
            # Generate base texture
            img = self._generate_base_parchment(parameters)
            
            # Apply advanced enhancements
            img = self.enhance_with_parameters(img, parameters)
            
        else:
            # Legacy generation mode
            noise_scale = kwargs.get('noise_scale', self.noise_scale)
            self.logger.info(f"Generating parchment texture with noise scale: {noise_scale}")
            
            img = self._generate_base_parchment_legacy(noise_scale)
        
        # Final validation and resize
        img = self.validate_output_size(img)
        
        self.logger.info("Parchment texture generation completed")
        return img
    
    def _generate_base_parchment(self, parameters: GenerationParameters) -> Image.Image:
        """
        Generate base parchment texture with advanced parameters.
        
        Args:
            parameters: GenerationParameters object
            
        Returns:
            PIL Image of the base parchment texture
        """
        # Get effective noise scale based on complexity
        effective_noise_scale = self.noise_scale * (0.5 + parameters.complexity)
        
        # Create base image
        if parameters.base_color:
            hex_color = parameters.base_color.lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb_color = self.base_color
        
        img = Image.new('RGB', (self.width, self.height), rgb_color)
        
        # Layer 1: Enhanced Grain based on quality settings
        quality_settings = parameters.get_quality_settings()
        noise_opacity = int(128 * (0.5 + parameters.complexity * 0.5))
        
        noise = self.create_noise_layer(scale=effective_noise_scale, opacity=noise_opacity)
        if noise.mode != 'L':
            noise = noise.convert('L')
        
        # Enhanced colorization based on style
        if parameters.style_preset == "chaotic":
            # More extreme colorization for chaotic style
            dark_color = tuple(max(0, c - 20) for c in rgb_color)
            light_color = tuple(min(255, c + 30) for c in rgb_color)
        else:
            # Standard colorization
            dark_color = tuple(max(0, c - 15) for c in rgb_color)
            light_color = tuple(min(255, c + 20) for c in rgb_color)
        
        colorized_noise = ImageOps.colorize(noise, dark_color, light_color)
        img.paste(colorized_noise, (0, 0))
        
        # Layer 2: Enhanced weathering effects
        weathering_intensity = parameters.randomness * 2.0
        img = self._apply_enhanced_weathering(img, intensity=weathering_intensity, parameters=parameters)
        
        # Layer 3: Adaptive vignette based on style
        if parameters.style_preset == "minimal":
            vignette_intensity = 0.3
        elif parameters.style_preset == "chaotic":
            vignette_intensity = 0.8
        else:
            vignette_intensity = 0.6 + (parameters.complexity - 0.5) * 0.4
        
        img = self.apply_vignette(img, intensity=vignette_intensity)
        
        # Layer 4: Age-related effects based on quality
        if parameters.quality in ["high", "ultra"]:
            img = self._apply_age_effects(img, parameters)
        
        return img
    
    def _generate_base_parchment_legacy(self, noise_scale: float) -> Image.Image:
        """
        Generate parchment texture using legacy method for backward compatibility.
        
        Args:
            noise_scale: Noise intensity scale
            
        Returns:
            PIL Image of the generated parchment texture
        """
        self.logger.info(f"Generating parchment texture with noise scale: {noise_scale}")
        
        # Create base image
        img = Image.new('RGB', (self.width, self.height), self.base_color)
        
        # Layer 1: Heavy Grain (ensure L mode for colorize)
        noise = self.create_noise_layer(scale=noise_scale)
        if noise.mode != 'L':
            noise = noise.convert('L')
        colorized_noise = ImageOps.colorize(noise, (0, 0, 0), (40, 40, 45))
        img.paste(colorized_noise, (0, 0))
        
        # Layer 2: Add scratches for weathered look
        img = self.add_scratch_texture(img, scale=noise_scale)
        
        # Layer 3: Vignette for depth
        img = self.apply_vignette(img, intensity=0.6)
        
        return img
    
    def _apply_enhanced_weathering(self, img: Image.Image, intensity: float, 
                                 parameters: GenerationParameters) -> Image.Image:
        """
        Apply enhanced weathering effects based on parameters.
        
        Args:
            img: Base PIL Image
            intensity: Weathering intensity
            parameters: Generation parameters
            
        Returns:
            PIL Image with weathering effects applied
        """
        # Base scratch texture
        img = self.add_scratch_texture(img, scale=intensity)
        
        # Add stain effects based on randomness
        if parameters.randomness > 0.6:
            stain_intensity = (parameters.randomness - 0.6) * 1.5
            img = self._apply_stain_effects(img, intensity=stain_intensity)
        
        # Add crack effects for high complexity and chaos
        if parameters.complexity > 0.7 and parameters.randomness > 0.5:
            img = self._apply_crack_effects(img, intensity=parameters.complexity)
        
        return img
    
    def _apply_stain_effects(self, img: Image.Image, intensity: float) -> Image.Image:
        """
        Apply stain effects to simulate age and wear.
        
        Args:
            img: PIL Image to apply stains to
            intensity: Stain intensity
            
        Returns:
            PIL Image with stain effects
        """
        # Create stain pattern
        stain_noise = self.create_noise_layer(scale=intensity * 2.0, opacity=int(60 * intensity))
        
        # Convert to appropriate mode
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        if stain_noise.mode != 'RGBA':
            stain_noise = stain_noise.convert('RGBA')
        
        # Blend stains
        img = Image.alpha_composite(img, stain_noise)
        
        return img.convert('RGB')
    
    def _apply_crack_effects(self, img: Image.Image, intensity: float) -> Image.Image:
        """
        Apply subtle crack effects.
        
        Args:
            img: PIL Image to apply cracks to
            intensity: Crack intensity
            
        Returns:
            PIL Image with crack effects
        """
        # Create crack pattern using darker noise
        crack_noise = self.create_noise_layer(scale=intensity * 3.0, opacity=int(40 * intensity))
        
        # Darken the cracks
        crack_array = np.array(crack_noise)
        crack_array = np.clip(crack_array * 0.3, 0, 255).astype(np.uint8)
        crack_img = Image.fromarray(crack_array, 'L')
        
        # Apply as mask to darken areas
        dark_overlay = Image.new('RGB', img.size, (0, 0, 0))
        img = Image.composite(dark_overlay, img, crack_img)
        
        return img
    
    def _apply_age_effects(self, img: Image.Image, parameters: GenerationParameters) -> Image.Image:
        """
        Apply age-related effects for higher quality generations.
        
        Args:
            img: PIL Image to apply age effects to
            parameters: Generation parameters
            
        Returns:
            PIL Image with age effects applied
        """
        # Slight desaturation for aged look
        if parameters.saturation > 0.5:
            img = ImageEnhance.Color(img).enhance(0.9)
        
        # Add subtle yellowing
        if parameters.base_color and parameters.base_color.lower() in ['#d4c5b0', '#c4b5a0']:
            yellow_overlay = Image.new('RGB', img.size, (255, 240, 200))
            img = Image.blend(img, yellow_overlay, 0.1)
        
        # Apply subtle texture enhancement
        if parameters.quality == "ultra":
            # Add very fine grain
            fine_grain = self.create_noise_layer(scale=0.5, opacity=20)
            img = Image.composite(img, fine_grain, fine_grain)
        
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "parchment"
    
    @staticmethod
    def get_default_params() -> dict:
        """
        Get default parameters for this generator type.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'width': 1024,
            'height': 1024,
            'noise_scale': 1.5,
            'base_color': (15, 15, 18),
            'complexity': 0.6,
            'randomness': 0.5,
            'quality': 'medium',
            'style_preset': 'detailed'
        }
    
    def get_available_presets(self) -> Dict[str, str]:
        """
        Get available presets specific to parchment generation.
        
        Returns:
            Dictionary mapping preset names to descriptions
        """
        return {
            "parchment_ancient": "Ancient, weathered parchment with heavy aging",
            "parchment_pristine": "Clean, well-preserved parchment",
            "minimal": "Simple, clean parchment texture",
            "detailed": "Richly textured parchment with full weathering",
            "chaotic": "Highly irregular, damaged parchment",
            "ordered": "Uniform, perfectly aged parchment"
        }
    
    def generate_with_preset(self, preset_name: str, **overrides) -> Image.Image:
        """
        Generate parchment with a specific preset applied.
        
        Args:
            preset_name: Name of the preset to apply
            **overrides: Parameter overrides
            
        Returns:
            PIL Image of the generated parchment
        """
        # Start with default parameters
        parameters = GenerationParameters()
        
        # Apply the preset
        parameters = self.preset_manager.apply_preset(parameters, preset_name, overrides)
        
        # Generate with parameters
        return self.generate(parameters=parameters)
    
    def save_with_index(self, index: int) -> str:
        """
        Save a parchment texture with the standard naming convention.
        
        Args:
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        img = self.generate()
        self.save_asset(img, self.category_map["backgrounds"], "void_parchment", index)
        return f"{self.output_dir}/{self.category_map['backgrounds']}/void_parchment_{index}.png"
    
    def generate_parameter_suggestions(self, style_hint: str = None) -> Dict[str, Any]:
        """
        Generate parameter suggestions based on style hints.
        
        Args:
            style_hint: Optional style hint ("ancient", "pristine", "weathered", etc.)
            
        Returns:
            Dictionary of suggested parameters
        """
        suggestions = {
            "ancient": {
                "complexity": 0.8,
                "randomness": 0.7,
                "base_color": "#2a2520",
                "quality": "high"
            },
            "pristine": {
                "complexity": 0.3,
                "randomness": 0.2,
                "base_color": "#d4c5b0",
                "quality": "medium"
            },
            "weathered": {
                "complexity": 0.6,
                "randomness": 0.6,
                "quality": "high"
            },
            "minimal": {
                "complexity": 0.2,
                "randomness": 0.1,
                "quality": "low"
            }
        }
        
        if style_hint and style_hint in suggestions:
            return suggestions[style_hint]
        
        return suggestions.get("weathered", {})