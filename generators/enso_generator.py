"""
Enso Generator

This module implements the Ink Enso circle generator,
creating organic circular brush strokes with chaos and complexity.

Updated to be type-aware and support ElementType-based generation.
"""

import math
import random
import numpy as np
from typing import Optional, Tuple, Union, Dict, Any
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from .base_generator import BaseGenerator
from .schemas import GenerationParameters
from .color_utils import apply_palette_to_parameters, hex_to_rgb
from .presets import get_preset_manager

# Import type system components
try:
    from enhanced_design.element_types import ElementType
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    ElementType = None


class EnsoGenerator(BaseGenerator):
    """
    Generator for Ink Enso circles.
    
    Creates organic circular brush strokes with variable complexity,
    chaos, and color for meditative and artistic effects.
    
    Updated to support type-aware generation from ElementType definitions.
    
    Supports advanced parameters including:
    - Quality controls and resolution settings
    - Custom color palettes and brush styles
    - Preset application for different enso styles
    - Enhanced organic flow and chaos parameters
    - Type-based parameter transformation
    """
    
    def __init__(self, width: int = 800, height: int = 800,
                 color: Optional[Tuple[int, int, int, int]] = None,
                 complexity: int = 40, chaos: float = 1.0,
                 element_type: Optional[ElementType] = None, **kwargs):
        """
        Initialize the enso generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            color: RGBA color for the enso strokes
            complexity: Number of brush strokes (higher = more detailed)
            chaos: Chaos factor for organic variation (0.1 = stable, 2.0 = very chaotic)
            element_type: Optional ElementType for type-aware generation
            **kwargs: Additional configuration options
        """
        if color is None:
            color = (0, 0, 0, 255)
            
        super().__init__(
            width=width,
            height=height,
            color=color,
            complexity=complexity,
            chaos=chaos,
            **kwargs
        )
        
        self.color = color
        self.complexity = complexity
        self.chaos = chaos
        self.preset_manager = get_preset_manager()
        self.element_type = element_type
        
    def set_element_type(self, element_type: ElementType) -> 'EnsoGenerator':
        """
        Set the ElementType for type-aware generation.
        
        Args:
            element_type: ElementType definition to use
            
        Returns:
            Self for method chaining
        """
        if HAS_TYPE_SYSTEM and isinstance(element_type, ElementType):
            self.element_type = element_type
            self.logger.info(f"Set ElementType: {element_type.id}")
        return self
        
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate an ink enso circle.
        
        Args:
            **kwargs: Generation parameters including:
                - GenerationParameters object
                - Legacy parameters (color, complexity, chaos)
                - ElementType-based parameters
                - Custom overrides
                
        Returns:
            PIL Image of the generated enso circle
        """
        # Handle type-aware generation first
        if self.element_type and HAS_TYPE_SYSTEM:
            return self._generate_from_element_type(**kwargs)
            
        # Handle advanced parameters
        if 'parameters' in kwargs and isinstance(kwargs['parameters'], GenerationParameters):
            parameters = kwargs['parameters']
            
            # Validate parameters
            validation_result = self.validate_parameters(parameters)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid parameters: {validation_result.errors}")
            
            # Apply preset if specified
            if hasattr(parameters, 'style_preset') and parameters.style_preset:
                preset_name = f"enso_{parameters.style_preset}"
                try:
                    parameters = self.preset_manager.apply_preset(parameters, preset_name)
                except ValueError:
                    pass
            
            # Apply to generator dimensions
            effective_width, effective_height = parameters.get_effective_dimensions()
            self.width = effective_width
            self.height = effective_height
            
            # Generate with advanced parameters
            img = self._generate_enso_advanced(parameters)
            
            # Apply advanced enhancements
            img = self.enhance_with_parameters(img, parameters)
            
        else:
            # Legacy generation mode
            color = kwargs.get('color', self.color)
            complexity = kwargs.get('complexity', self.complexity)
            chaos = kwargs.get('chaos', self.chaos)
            
            img = self._generate_enso_legacy(color, complexity, chaos)
        
        # Final validation
        img = self.validate_output_size(img)
        
        self.logger.info("Enso circle generation completed")
        return img
    
    def _generate_from_element_type(self, **kwargs) -> Image.Image:
        """
        Generate enso circle from ElementType definition.
        
        Args:
            **kwargs: Additional parameter overrides
            
        Returns:
            PIL Image of the generated enso circle
        """
        if not self.element_type:
            raise ValueError("No ElementType set for type-aware generation")
            
        # Get parameters from ElementType
        params = self.element_type.get_effective_params()
        
        # Apply any additional overrides from kwargs
        for key, value in kwargs.items():
            if key not in ['parameters']:  # Skip GenerationParameters in type mode
                params[key] = value
        
        # Set up generation parameters
        effective_width = params.get('width', self.width)
        effective_height = params.get('height', self.height)
        
        # Update dimensions
        self.width = effective_width
        self.height = effective_height
        
        # Convert color if needed
        if 'color' in params:
            if isinstance(params['color'], str):
                hex_color = params['color'].lstrip('#')
                rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                params['color'] = rgb_color + (255,)
        
        # Create GenerationParameters for consistency
        generation_params = GenerationParameters(
            width=effective_width,
            height=effective_height,
            base_color=params.get('color', '#000000'),  # Default to black
            complexity=params.get('complexity', 0.6),
            randomness=params.get('chaos', 1.0) / 2.0,  # Normalize chaos to 0-1 range
            quality=params.get('quality', 'medium'),
            style_preset=params.get('style_preset', 'detailed')
        )
        
        # Apply style preset if specified
        if generation_params.style_preset:
            preset_name = f"enso_{generation_params.style_preset}"
            try:
                generation_params = self.preset_manager.apply_preset(generation_params, preset_name)
            except ValueError:
                pass
        
        # Generate the enso
        img = self._generate_enso_advanced(generation_params)
        
        # Apply type-specific effects
        img = self._apply_type_specific_effects(img, params)
        
        self.logger.info(f"Generated enso from ElementType: {self.element_type.id}")
        return img
    
    def _apply_type_specific_effects(self, img: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """
        Apply effects specific to the ElementType configuration.
        
        Args:
            img: Base PIL Image
            params: Type-specific parameters
            
        Returns:
            PIL Image with type-specific effects applied
        """
        # Style-specific adjustments
        style = params.get('style', 'balanced')
        
        if style == 'meditative':
            # Add subtle blur for meditative effect
            img = img.filter(ImageFilter.GaussianBlur(radius=1))
        elif style == 'energetic':
            # Increase contrast for energetic look
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
        
        # Custom opacity based on type
        if 'opacity' in params:
            opacity = params['opacity']
            if opacity < 1.0:
                # Convert to RGBA and apply opacity
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img.putalpha(int(255 * opacity))
        
        # Brush characteristics
        if 'brush_thickness' in params:
            thickness = params['brush_thickness']
            # This would require re-generation with different thickness
            # For now, we can apply a scaling effect
            img = img.resize((int(self.width * thickness), int(self.height * thickness)), 
                           Image.Resampling.LANCZOS)
            # Center crop back to original size
            left = (img.width - self.width) // 2
            top = (img.height - self.height) // 2
            img = img.crop((left, top, left + self.width, top + self.height))
        
        return img
    
    def _generate_enso_advanced(self, parameters: GenerationParameters) -> Image.Image:
        """
        Generate enso circle with advanced parameters.
        
        Args:
            parameters: GenerationParameters object
            
        Returns:
            PIL Image of the generated enso circle
        """
        # Resolve color from parameters
        if parameters.base_color:
            hex_color = parameters.base_color.lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            base_color = rgb_color + (255,)
        else:
            base_color = self.color
        
        # Calculate effective parameters based on advanced settings
        effective_complexity = int(self.complexity * (0.5 + parameters.complexity))
        effective_chaos = self.chaos * (0.3 + parameters.randomness * 1.7)
        
        # Quality-based stroke settings
        quality_settings = parameters.get_quality_settings()
        max_thickness = int(15 * quality_settings.get('detail_level', 1.0))
        min_thickness = 2
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate center and radius based on style
        center_x, center_y = self.width // 2, self.height // 2
        
        if parameters.style_preset == "minimal":
            radius = min(self.width, self.height) // 4
            stroke_segments = 1
        elif parameters.style_preset == "chaotic":
            radius = min(self.width, self.height) // 3
            stroke_segments = int(effective_complexity * 1.5)
        else:
            radius = min(self.width, self.height) // 3
            stroke_segments = effective_complexity
        
        self.logger.info(f"Generating enso with complexity={effective_complexity}, chaos={effective_chaos}, style={parameters.style_preset}")
        
        # Generate brush strokes based on style preset
        if parameters.style_preset == "ordered":
            img = self._generate_ordered_enzo(draw, center_x, center_y, radius, base_color, 
                                            stroke_segments, max_thickness, min_thickness, effective_chaos, parameters)
        elif parameters.style_preset == "chaotic":
            img = self._generate_chaotic_enzo(draw, center_x, center_y, radius, base_color, 
                                           stroke_segments, max_thickness, min_thickness, effective_chaos, parameters)
        else:
            img = self._generate_standard_enzo(draw, center_x, center_y, radius, base_color, 
                                             stroke_segments, max_thickness, min_thickness, effective_chaos, parameters)
        
        # Apply ink blur based on quality
        blur_radius = quality_settings.get('blur_radius', 1.0)
        img = self.apply_ink_blur(img, radius=blur_radius)
        
        return img
    
    def _generate_standard_enzo(self, draw: ImageDraw.Draw, center_x: int, center_y: int, 
                               radius: int, color: Tuple[int, int, int, int], stroke_segments: int,
                               max_thickness: int, min_thickness: int, chaos: float, parameters: GenerationParameters) -> Image.Image:
        """
        Generate standard enso with balanced parameters.
        """
        img = draw._image
        
        for _ in range(stroke_segments):
            points = []
            
            # Vary radius with chaos
            current_radius = radius + random.randint(int(-30 * chaos), int(30 * chaos))
            thickness = random.randint(min_thickness, max_thickness)
            
            # Generate arc segment
            start_angle = random.uniform(0, 2 * math.pi)
            end_angle = start_angle + random.uniform(3, 5)
            
            # Create organic path
            for angle in np.arange(start_angle, end_angle, 0.05):
                r_wobble = (current_radius + 
                           math.sin(angle * 10) * 5 * chaos + 
                           random.randint(-2, 2))
                
                x = center_x + r_wobble * math.cos(angle)
                y = center_y + r_wobble * math.sin(angle)
                points.append((x, y))
            
            # Draw the stroke if we have enough points
            if len(points) > 1:
                stroke_color = color
                if len(color) == 3:  # RGB, add random alpha
                    stroke_color = color + (random.randint(50, 200),)
                
                draw.line(points, fill=stroke_color, width=thickness)
        
        return img
    
    def _generate_ordered_enzo(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
                              radius: int, color: Tuple[int, int, int, int], stroke_segments: int,
                              max_thickness: int, min_thickness: int, chaos: float, parameters: GenerationParameters) -> Image.Image:
        """
        Generate ordered, geometric enso with minimal chaos.
        """
        img = draw._image
        
        # More structured, circular paths
        for i in range(stroke_segments):
            points = []
            
            # Less radius variation for ordered look
            current_radius = radius + int((i % 2) * 10 * chaos) - int(5 * chaos)
            thickness = min_thickness + (i % 3) * 2
            
            # More regular arc segments
            start_angle = (i / stroke_segments) * 2 * math.pi
            end_angle = start_angle + (2 * math.pi / stroke_segments) * 0.8
            
            # Create precise circular path
            for angle in np.arange(start_angle, end_angle, 0.02):
                r_variation = math.sin(angle * 5) * 2 * chaos
                r_wobble = current_radius + r_variation
                
                x = center_x + r_wobble * math.cos(angle)
                y = center_y + r_wobble * math.sin(angle)
                points.append((x, y))
            
            # Draw precise stroke
            if len(points) > 1:
                stroke_color = color + (220,) if len(color) == 3 else color
                draw.line(points, fill=stroke_color, width=thickness)
        
        return img
    
    def _generate_chaotic_enzo(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
                              radius: int, color: Tuple[int, int, int, int], stroke_segments: int,
                              max_thickness: int, min_thickness: int, chaos: float, parameters: GenerationParameters) -> Image.Image:
        """
        Generate chaotic, organic enso with maximum variation.
        """
        img = draw._image
        
        for _ in range(stroke_segments):
            points = []
            
            # High radius variation
            current_radius = radius + random.randint(int(-50 * chaos), int(50 * chaos))
            thickness = random.randint(min_thickness, max_thickness)
            
            # More irregular arc segments
            start_angle = random.uniform(-math.pi, math.pi)
            end_angle = start_angle + random.uniform(1, 6)
            
            # Create highly irregular path
            for angle in np.arange(start_angle, end_angle, 0.03):
                # Multiple wobble factors for chaos
                r_wobble = (current_radius + 
                           math.sin(angle * 20) * 15 * chaos + 
                           math.cos(angle * 7) * 8 * chaos +
                           random.randint(-8, 8))
                
                x = center_x + r_wobble * math.cos(angle)
                y = center_y + r_wobble * math.sin(angle)
                points.append((x, y))
            
            # Draw chaotic stroke
            if len(points) > 1:
                # More transparent for chaotic look
                alpha = random.randint(30, 150)
                if len(color) == 3:
                    stroke_color = color + (alpha,)
                else:
                    stroke_color = color[:3] + (alpha,)
                
                draw.line(points, fill=stroke_color, width=thickness)
        
        return img
    
    def _generate_enso_legacy(self, color: Tuple[int, int, int, int], complexity: int, chaos: float) -> Image.Image:
        """
        Generate enso circle using legacy method for backward compatibility.
        """
        self.logger.info(f"Generating enso with complexity={complexity}, chaos={chaos}")
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate center and base radius
        center_x, center_y = self.width // 2, self.height // 2
        radius = min(self.width, self.height) // 3
        
        # Generate brush strokes
        for _ in range(complexity):
            points = []
            
            # Vary radius with chaos
            current_radius = radius + random.randint(int(-30 * chaos), int(30 * chaos))
            thickness = random.randint(2, 15)
            
            # Generate arc segment
            start_angle = random.uniform(0, 2 * math.pi)
            end_angle = start_angle + random.uniform(3, 5)
            
            # Create organic path
            for angle in np.arange(start_angle, end_angle, 0.05):
                # Add variation to radius with mathematical wobble and random noise
                r_wobble = (current_radius + 
                           math.sin(angle * 10) * 5 * chaos + 
                           random.randint(-2, 2))
                
                x = center_x + r_wobble * math.cos(angle)
                y = center_y + r_wobble * math.sin(angle)
                points.append((x, y))
            
            # Draw the stroke if we have enough points
            if len(points) > 1:
                stroke_color = color
                if len(color) == 3:  # RGB, add random alpha
                    stroke_color = color + (random.randint(50, 200),)
                
                draw.line(points, fill=stroke_color, width=thickness)
        
        # Apply ink blur for organic feel
        img = self.apply_ink_blur(img, radius=1)
        
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "enso"
    
    @staticmethod
    def get_default_params() -> dict:
        """
        Get default parameters for this generator type.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'width': 800,
            'height': 800,
            'color': (0, 0, 0, 255),
            'complexity': 40,
            'chaos': 1.0,
            'style_preset': 'detailed'
        }
    
    def get_type_aware_params(self) -> Dict[str, Any]:
        """
        Get parameters expected by ElementType schema.
        
        Returns:
            Dictionary of type-aware parameters
        """
        return {
            'width': {'type': 'int', 'default': 800, 'min': 64, 'max': 2048},
            'height': {'type': 'int', 'default': 800, 'min': 64, 'max': 2048},
            'color': {'type': 'str', 'default': '#000000', 'description': 'Hex color string'},
            'complexity': {'type': 'int', 'default': 40, 'min': 5, 'max': 200},
            'chaos': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 3.0},
            'quality': {'type': 'str', 'default': 'medium', 'choices': ['low', 'medium', 'high', 'ultra']},
            'style_preset': {'type': 'str', 'default': 'detailed', 'choices': ['minimal', 'detailed', 'chaotic', 'ordered']},
            'style': {'type': 'str', 'default': 'balanced', 'choices': ['meditative', 'energetic', 'balanced', 'minimal', 'chaotic', 'ordered']},
            'opacity': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 1.0},
            'brush_thickness': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 2.0}
        }
    
    def get_available_presets(self) -> Dict[str, str]:
        """
        Get available presets specific to enso generation.
        
        Returns:
            Dictionary mapping preset names to descriptions
        """
        return {
            "enso_meditative": "Simple, centered enso for meditation",
            "enso_energetic": "Dynamic, chaotic enso with high energy",
            "minimal": "Clean, minimalistic enso circle",
            "detailed": "Richly detailed enso with balanced chaos",
            "chaotic": "Highly irregular, expressive enso",
            "ordered": "Perfect geometric circle with precision"
        }
    
    def generate_with_preset(self, preset_name: str, **overrides) -> Image.Image:
        """
        Generate enso with a specific preset applied.
        
        Args:
            preset_name: Name of the preset to apply
            **overrides: Parameter overrides
            
        Returns:
            PIL Image of the generated enso
        """
        # Start with default parameters
        parameters = GenerationParameters()
        
        # Apply the preset
        parameters = self.preset_manager.apply_preset(parameters, preset_name, overrides)
        
        # Generate with parameters
        return self.generate(parameters=parameters)
    
    def generate_from_params(self, color_hex: str, complexity: int, chaos: float) -> Image.Image:
        """
        Generate an enso from specific parameters (for LLM-directed generation).
        
        Args:
            color_hex: Hex color string (e.g., '#FF0000')
            complexity: Number of brush strokes
            chaos: Chaos factor
            
        Returns:
            PIL Image of the generated enso
        """
        # Convert hex to RGB
        color_hex = color_hex.lstrip('#')
        rgb_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        rgba_color = rgb_color + (255,)
        
        return self.generate(color=rgba_color, complexity=complexity, chaos=chaos)
    
    def save_with_index(self, index: int) -> str:
        """
        Save an enso circle with the standard naming convention.
        
        Args:
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        img = self.generate()
        self.save_asset(img, self.category_map["glyphs"], "ink_enso", index)
        return f"{self.output_dir}/{self.category_map['glyphs']}/ink_enso_{index}.png"
    
    def generate_parameter_suggestions(self, style_hint: str = None) -> Dict[str, Any]:
        """
        Generate parameter suggestions based on style hints.
        
        Args:
            style_hint: Optional style hint ("meditative", "energetic", "chaotic", etc.)
            
        Returns:
            Dictionary of suggested parameters
        """
        suggestions = {
            "meditative": {
                "complexity": 20,
                "chaos": 0.3,
                "color": "#000000",
                "style_preset": "minimal",
                "style": "meditative"
            },
            "energetic": {
                "complexity": 60,
                "chaos": 1.5,
                "color": "#8b0000",
                "style_preset": "chaotic",
                "style": "energetic"
            },
            "balanced": {
                "complexity": 40,
                "chaos": 1.0,
                "style_preset": "detailed",
                "style": "balanced"
            },
            "minimal": {
                "complexity": 15,
                "chaos": 0.2,
                "style_preset": "minimal",
                "style": "minimal"
            },
            "chaotic": {
                "complexity": 80,
                "chaos": 2.0,
                "style_preset": "chaotic",
                "style": "chaotic"
            },
            "ordered": {
                "complexity": 30,
                "chaos": 0.1,
                "style_preset": "ordered",
                "style": "ordered"
            }
        }
        
        if style_hint and style_hint in suggestions:
            return suggestions[style_hint]
        
        return suggestions.get("balanced", {})