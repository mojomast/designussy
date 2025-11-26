"""
Sigil Generator

This module implements the Arcane Sigil generator,
creating mystical geometric runes and symbols with glow effects.

Updated to be type-aware and support ElementType-based generation.
"""

import random
import math
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFilter
from .base_generator import BaseGenerator
from .schemas import GenerationParameters

# Import type system components
try:
    from enhanced_design.element_types import ElementType
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    ElementType = None


class SigilGenerator(BaseGenerator):
    """
    Generator for Arcane Sigils.
    
    Creates mystical geometric runes and symbols with outer circles,
    connecting lines, and ethereal glow effects.
    
    Updated to support type-aware generation from ElementType definitions.
    
    Supports:
    - Mystical geometric patterns
    - Custom point counts and complexity
    - Color variations and glow effects
    - Type-based parameter transformation
    """
    
    def __init__(self, width: int = 500, height: int = 500,
                 color: Optional[Tuple[int, int, int, int]] = None,
                 point_count_range: Tuple[int, int] = (3, 7),
                 element_type: Optional[ElementType] = None, **kwargs):
        """
        Initialize the sigil generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            color: RGBA color for the sigil lines
            point_count_range: Min/max number of points in the sigil
            element_type: Optional ElementType for type-aware generation
            **kwargs: Additional configuration options
        """
        if color is None:
            color = (212, 197, 176, 255)  # Parchment color
            
        super().__init__(
            width=width,
            height=height,
            color=color,
            point_count_range=point_count_range,
            **kwargs
        )
        
        self.color = color
        self.point_count_range = point_count_range
        self.element_type = element_type
        
    def set_element_type(self, element_type: ElementType) -> 'SigilGenerator':
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
        Generate an arcane sigil.
        
        Args:
            **kwargs: Generation parameters including:
                - Legacy parameters (color, point_count_range)
                - ElementType-based parameters
                - Custom overrides
                
        Returns:
            PIL Image of the generated sigil
        """
        # Handle type-aware generation first
        if self.element_type and HAS_TYPE_SYSTEM:
            return self._generate_from_element_type(**kwargs)
            
        # Legacy generation mode
        color = kwargs.get('color', self.color)
        min_points, max_points = kwargs.get('point_count_range', self.point_count_range)
        
        self.logger.info(f"Generating sigil with {min_points}-{max_points} points")
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate center
        cx, cy = self.width // 2, self.height // 2
        
        # Optionally draw outer circle (70% chance)
        if random.random() > 0.3:
            margin = max(self.width, self.height) // 10
            draw.ellipse(
                (margin, margin, self.width - margin, self.height - margin),
                outline=color,
                width=3
            )
        
        # Generate points for the sigil
        num_points = random.randint(min_points, max_points)
        points = []
        radius = min(self.width, self.height) // 3
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        
        # Draw connecting polygon
        if len(points) > 2:
            draw.polygon(points, outline=color, width=2)
        
        # Draw lines from center to each point
        for point in points:
            draw.line((cx, cy, point[0], point[1]), fill=color, width=1)
        
        # Apply glow effect
        glow_color = color  # Use same color for glow
        img = self.apply_glow(img, glow_color, blur_radius=4)
        
        # Final validation
        img = self.validate_output_size(img)
        
        self.logger.info("Sigil generation completed")
        return img
    
    def _generate_from_element_type(self, **kwargs) -> Image.Image:
        """
        Generate sigil from ElementType definition.
        
        Args:
            **kwargs: Additional parameter overrides
            
        Returns:
            PIL Image of the generated sigil
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
        
        # Get sigil-specific parameters
        min_points = params.get('min_points', 3)
        max_points = params.get('max_points', 7)
        has_outer_circle = params.get('has_outer_circle', True)
        glow_intensity = params.get('glow_intensity', 4)
        style = params.get('style', 'geometric')
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate center
        cx, cy = self.width // 2, self.height // 2
        
        # Draw outer circle if enabled
        if has_outer_circle:
            margin = max(self.width, self.height) // 10
            draw.ellipse(
                (margin, margin, self.width - margin, self.height - margin),
                outline=params['color'],
                width=3
            )
        
        # Generate points for the sigil
        num_points = random.randint(min_points, max_points)
        points = []
        radius = min(self.width, self.height) // 3
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        
        # Draw based on style
        if style == 'complex':
            img = self._generate_complex_sigil(draw, cx, cy, points, params, num_points)
        else:
            # Standard geometric style
            if len(points) > 2:
                draw.polygon(points, outline=params['color'], width=2)
            
            # Draw lines from center to each point
            for point in points:
                draw.line((cx, cy, point[0], point[1]), fill=params['color'], width=1)
        
        # Apply glow effect with type-specific intensity
        img = self.apply_glow(img, params['color'], blur_radius=glow_intensity)
        
        # Apply type-specific enhancements
        img = self._apply_type_specific_effects(img, params)
        
        self.logger.info(f"Generated sigil from ElementType: {self.element_type.id}")
        return img
    
    def _generate_complex_sigil(self, draw: ImageDraw.Draw, cx: int, cy: int, 
                               points: list, params: Dict[str, Any], num_points: int) -> Image.Image:
        """
        Generate a complex sigil with multiple layers.
        
        Args:
            draw: ImageDraw object
            cx, cy: Center coordinates
            points: List of sigil points
            params: ElementType parameters
            num_points: Number of points
            
        Returns:
            Image with complex sigil drawn
        """
        img = draw._image
        color = params['color']
        
        # Primary polygon
        if len(points) > 2:
            draw.polygon(points, outline=color, width=3)
        
        # Center connections
        for point in points:
            draw.line((cx, cy, point[0], point[1]), fill=color, width=2)
        
        # Add secondary layer for complexity
        if num_points >= 4:
            secondary_radius = min(self.width, self.height) // 5
            secondary_points = []
            
            for i in range(num_points):
                angle = (i / num_points) * 2 * math.pi + math.pi / num_points
                x = cx + secondary_radius * math.cos(angle)
                y = cy + secondary_radius * math.sin(angle)
                secondary_points.append((x, y))
            
            # Draw secondary polygon (dashed effect with thinner lines)
            for i in range(len(secondary_points)):
                next_i = (i + 1) % len(secondary_points)
                draw.line(
                    (secondary_points[i][0], secondary_points[i][1], 
                     secondary_points[next_i][0], secondary_points[next_i][1]),
                    fill=color,
                    width=1
                )
        
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
        # Add complexity layers
        complexity = params.get('complexity', 0.5)
        
        if complexity > 0.7:
            # Add additional geometric elements
            img = self._add_geometric_elements(img, complexity)
        
        # Adjust opacity based on type
        opacity = params.get('opacity', 1.0)
        if opacity < 1.0:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.putalpha(int(255 * opacity))
        
        # Add mystical aura
        if params.get('mystical_aura', False):
            img = self._add_mystical_aura(img, params)
        
        return img
    
    def _add_geometric_elements(self, img: Image.Image, complexity: float) -> Image.Image:
        """
        Add additional geometric elements based on complexity.
        
        Args:
            img: Base image
            complexity: Complexity level (0-1)
            
        Returns:
            Image with additional geometric elements
        """
        draw = ImageDraw.Draw(img)
        cx, cy = self.width // 2, self.height // 2
        color = self.color
        
        # Add concentric circles for high complexity
        if complexity > 0.8:
            circle_count = int((complexity - 0.8) * 5) + 1
            for i in range(circle_count):
                radius = min(self.width, self.height) // 4 + (i * 20)
                draw.ellipse(
                    (cx - radius, cy - radius, cx + radius, cy + radius),
                    outline=color,
                    width=1
                )
        
        return img
    
    def _add_mystical_aura(self, img: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """
        Add mystical aura effects to the sigil.
        
        Args:
            img: Base image
            params: ElementType parameters
            
        Returns:
            Image with mystical aura applied
        """
        # Create a soft glow around the sigil
        aura_color = params.get('color', self.color)
        aura_radius = int(min(self.width, self.height) * 0.1)
        
        # Apply multiple blur passes for ethereal effect
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        self.logger.info("Applied mystical aura effects")
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "sigil"
    
    @staticmethod
    def get_default_params() -> dict:
        """
        Get default parameters for this generator type.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'width': 500,
            'height': 500,
            'color': (212, 197, 176, 255),
            'point_count_range': (3, 7),
            'has_outer_circle': True,
            'glow_intensity': 4
        }
    
    def get_type_aware_params(self) -> Dict[str, Any]:
        """
        Get parameters expected by ElementType schema.
        
        Returns:
            Dictionary of type-aware parameters
        """
        return {
            'width': {'type': 'int', 'default': 500, 'min': 64, 'max': 1024},
            'height': {'type': 'int', 'default': 500, 'min': 64, 'max': 1024},
            'color': {'type': 'str', 'default': '#d4c5b0', 'description': 'Hex color string'},
            'min_points': {'type': 'int', 'default': 3, 'min': 3, 'max': 12},
            'max_points': {'type': 'int', 'default': 7, 'min': 4, 'max': 15},
            'has_outer_circle': {'type': 'bool', 'default': True},
            'glow_intensity': {'type': 'float', 'default': 4.0, 'min': 1.0, 'max': 10.0},
            'style': {'type': 'str', 'default': 'geometric', 'choices': ['geometric', 'complex', 'mystical']},
            'complexity': {'type': 'float', 'default': 0.5, 'min': 0.0, 'max': 1.0},
            'opacity': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 1.0},
            'mystical_aura': {'type': 'bool', 'default': False}
        }
    
    def save_with_index(self, index: int) -> str:
        """
        Save a sigil with the standard naming convention.
        
        Args:
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        img = self.generate()
        self.save_asset(img, self.category_map["glyphs"], "sigil", index)
        return f"{self.output_dir}/{self.category_map['glyphs']}/sigil_{index}.png"
    
    def generate_complex_sigil(self, point_count: int = 6, add_secondary_layer: bool = True) -> Image.Image:
        """
        Generate a more complex sigil with specific parameters.
        
        Args:
            point_count: Exact number of points to use
            add_secondary_layer: Whether to add a secondary geometric layer
            
        Returns:
            PIL Image of the complex sigil
        """
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = self.width // 2, self.height // 2
        
        # Primary sigil
        radius = min(self.width, self.height) // 3
        primary_points = []
        
        for i in range(point_count):
            angle = (i / point_count) * 2 * math.pi
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            primary_points.append((x, y))
        
        # Draw primary polygon
        draw.polygon(primary_points, outline=self.color, width=3)
        
        # Draw center connections
        for point in primary_points:
            draw.line((cx, cy, point[0], point[1]), fill=self.color, width=2)
        
        # Optional secondary layer for more complexity
        if add_secondary_layer and point_count >= 4:
            secondary_radius = radius * 0.6
            secondary_points = []
            
            for i in range(point_count):
                angle = (i / point_count) * 2 * math.pi + math.pi / point_count
                x = cx + secondary_radius * math.cos(angle)
                y = cy + secondary_radius * math.sin(angle)
                secondary_points.append((x, y))
            
            # Draw secondary polygon (dashed effect with thinner lines)
            for i in range(len(secondary_points)):
                next_i = (i + 1) % len(secondary_points)
                draw.line(
                    (secondary_points[i][0], secondary_points[i][1], 
                     secondary_points[next_i][0], secondary_points[next_i][1]),
                    fill=self.color,
                    width=1
                )
        
        # Apply glow
        img = self.apply_glow(img, self.color, blur_radius=3)
        return img
    
    def generate_parameter_suggestions(self, style_hint: str = None) -> Dict[str, Any]:
        """
        Generate parameter suggestions based on style hints.
        
        Args:
            style_hint: Optional style hint ("simple", "complex", "mystical", etc.)
            
        Returns:
            Dictionary of suggested parameters
        """
        suggestions = {
            "simple": {
                "min_points": 3,
                "max_points": 4,
                "complexity": 0.3,
                "glow_intensity": 2.0,
                "style": "geometric"
            },
            "complex": {
                "min_points": 5,
                "max_points": 8,
                "complexity": 0.8,
                "glow_intensity": 6.0,
                "style": "complex"
            },
            "mystical": {
                "min_points": 4,
                "max_points": 6,
                "mystical_aura": True,
                "glow_intensity": 8.0,
                "style": "mystical",
                "opacity": 0.9
            },
            "geometric": {
                "min_points": 4,
                "max_points": 6,
                "has_outer_circle": True,
                "complexity": 0.5,
                "style": "geometric"
            }
        }
        
        if style_hint and style_hint in suggestions:
            return suggestions[style_hint]
        
        return suggestions.get("geometric", {})