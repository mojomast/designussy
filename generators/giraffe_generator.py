"""
Giraffe Generator

This module implements the Ink Giraffe creature generator,
creating stylized giraffe silhouettes with spots and ink effects.

Updated to be type-aware and support ElementType-based generation.
"""

import random
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


class GiraffeGenerator(BaseGenerator):
    """
    Generator for Ink Giraffe creatures.
    
    Creates stylized giraffe silhouettes with elongated necks,
    spots, and ink-like appearance.
    
    Updated to support type-aware generation from ElementType definitions.
    
    Supports:
    - Stylized giraffe anatomy
    - Customizable body and spot colors
    - Configurable spot patterns
    - Baby and adult giraffe variants
    - Type-based parameter transformation
    """
    
    def __init__(self, width: int = 600, height: int = 800,
                 body_color: Optional[Tuple[int, int, int, int]] = None,
                 spot_color: Optional[Tuple[int, int, int, int]] = None,
                 spot_count: int = 20,
                 element_type: Optional[ElementType] = None, **kwargs):
        """
        Initialize the giraffe generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            body_color: RGBA color for the giraffe body
            spot_color: RGBA color for the giraffe spots
            spot_count: Number of spots to generate
            element_type: Optional ElementType for type-aware generation
            **kwargs: Additional configuration options
        """
        if body_color is None:
            body_color = (212, 197, 176, 255)  # Parchment color
        if spot_color is None:
            spot_color = (20, 20, 20, 220)    # Dark ink color
            
        super().__init__(
            width=width,
            height=height,
            body_color=body_color,
            spot_color=spot_color,
            spot_count=spot_count,
            **kwargs
        )
        
        self.body_color = body_color
        self.spot_color = spot_color
        self.spot_count = spot_count
        self.element_type = element_type
        
    def set_element_type(self, element_type: ElementType) -> 'GiraffeGenerator':
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
        Generate an ink giraffe.
        
        Args:
            **kwargs: Generation parameters including:
                - Legacy parameters (body_color, spot_color, spot_count)
                - ElementType-based parameters
                - Custom overrides
                
        Returns:
            PIL Image of the generated giraffe
        """
        # Handle type-aware generation first
        if self.element_type and HAS_TYPE_SYSTEM:
            return self._generate_from_element_type(**kwargs)
            
        # Legacy generation mode
        body_color = kwargs.get('body_color', self.body_color)
        spot_color = kwargs.get('spot_color', self.spot_color)
        spot_count = kwargs.get('spot_count', self.spot_count)
        
        self.logger.info(f"Generating giraffe with {spot_count} spots")
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Generate giraffe anatomy
        img = self._draw_giraffe_anatomy(draw, body_color, spot_color, spot_count)
        
        # Apply ink blur for organic feel
        img = self.apply_ink_blur(img, radius=1)
        
        # Final validation
        img = self.validate_output_size(img)
        
        self.logger.info("Giraffe generation completed")
        return img
    
    def _generate_from_element_type(self, **kwargs) -> Image.Image:
        """
        Generate giraffe from ElementType definition.
        
        Args:
            **kwargs: Additional parameter overrides
            
        Returns:
            PIL Image of the generated giraffe
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
        
        # Convert colors if needed
        if 'body_color' in params:
            if isinstance(params['body_color'], str):
                hex_color = params['body_color'].lstrip('#')
                rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                params['body_color'] = rgb_color + (255,)
        
        if 'spot_color' in params:
            if isinstance(params['spot_color'], str):
                hex_color = params['spot_color'].lstrip('#')
                rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                params['spot_color'] = rgb_color + (220,)
        
        # Get giraffe-specific parameters
        body_color = params.get('body_color', self.body_color)
        spot_color = params.get('spot_color', self.spot_color)
        spot_count = params.get('spot_count', self.spot_count)
        giraffe_type = params.get('type', 'adult')  # adult, baby, elongated
        neck_length = params.get('neck_length', 1.0)
        spot_pattern = params.get('spot_pattern', 'random')
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Generate giraffe anatomy based on type
        if giraffe_type == 'baby':
            img = self._draw_baby_giraffe(draw, body_color, spot_color, spot_count, params)
        elif giraffe_type == 'elongated':
            img = self._draw_elongated_giraffe(draw, body_color, spot_color, spot_count, neck_length, params)
        else:
            # Standard adult giraffe
            img = self._draw_giraffe_anatomy(draw, body_color, spot_color, spot_count, params)
        
        # Apply type-specific effects
        img = self._apply_type_specific_effects(img, params)
        
        self.logger.info(f"Generated giraffe from ElementType: {self.element_type.id}")
        return img
    
    def _draw_giraffe_anatomy(self, draw: ImageDraw.Draw, 
                            body_color: Tuple[int, int, int, int],
                            spot_color: Tuple[int, int, int, int],
                            spot_count: int,
                            params: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Draw the standard giraffe anatomy.
        
        Args:
            draw: ImageDraw object
            body_color: Body color
            spot_color: Spot color
            spot_count: Number of spots
            params: Additional parameters
            
        Returns:
            Image with giraffe anatomy drawn
        """
        img = draw._image
        
        # Define giraffe anatomy
        body_x = self.width // 2
        body_y = self.height - 200  # Body position
        
        # Neck - start from body, extend upward
        neck_start = (body_x - 50, body_y)
        neck_end = (body_x + 100, body_y - 400)  # Long giraffe neck
        
        # Draw neck
        neck_width = random.randint(20, 40)
        draw.line([neck_start, neck_end], fill=body_color, width=neck_width)
        
        # Head
        head_center = neck_end
        head_width = 80
        head_height = 60
        draw.ellipse(
            (head_center[0] - 30, head_center[1] - 20,
             head_center[0] + 50, head_center[1] + 40),
            fill=body_color
        )
        
        # Ears
        draw.line([head_center, (head_center[0], head_center[1] - 60)], fill=body_color, width=5)
        draw.line(
            [(head_center[0] + 20, head_center[1]),
             (head_center[0] + 20, head_center[1] - 60)],
            fill=body_color, width=5
        )
        
        # Body
        body_width = 200
        body_height = 100
        draw.rectangle(
            (body_x - body_width//2, body_y,
             body_x + body_width//2, body_y + body_height),
            fill=body_color
        )
        
        # Legs
        leg_width = 15
        leg_spacing = 80
        
        # Front legs
        draw.line(
            [(body_x - leg_spacing//2, body_y + body_height),
             (body_x - leg_spacing//2 - 10, self.height - 50)],
            fill=body_color, width=leg_width
        )
        draw.line(
            [(body_x + leg_spacing//2, body_y + body_height),
             (body_x + leg_spacing//2 + 10, self.height - 50)],
            fill=body_color, width=leg_width
        )
        
        # Generate spots
        img = self._draw_giraffe_spots(draw, spot_color, spot_count, params)
        
        return img
    
    def _draw_baby_giraffe(self, draw: ImageDraw.Draw,
                         body_color: Tuple[int, int, int, int],
                         spot_color: Tuple[int, int, int, int],
                         spot_count: int,
                         params: Dict[str, Any]) -> Image.Image:
        """
        Draw a baby giraffe with shorter neck and bigger features.
        
        Args:
            draw: ImageDraw object
            body_color: Body color
            spot_color: Spot color  
            spot_count: Number of spots
            params: Additional parameters
            
        Returns:
            Image with baby giraffe drawn
        """
        img = draw._image
        
        body_x = self.width // 2
        body_y = self.height - 150  # Lower body position
        
        # Shorter, thicker neck
        neck_start = (body_x - 40, body_y)
        neck_end = (body_x + 80, body_y - 250)  # Shorter neck
        draw.line([neck_start, neck_end], fill=body_color, width=30)
        
        # Bigger head
        head_center = neck_end
        draw.ellipse(
            (head_center[0] - 35, head_center[1] - 25,
             head_center[0] + 35, head_center[1] + 35),
            fill=body_color
        )
        
        # Rounder body
        draw.ellipse(
            (body_x - 80, body_y - 20,
             body_x + 80, body_y + 80),
            fill=body_color
        )
        
        # Thicker legs
        draw.line(
            [(body_x - 40, body_y + 80), (body_x - 50, self.height - 30)],
            fill=body_color, width=20
        )
        draw.line(
            [(body_x + 40, body_y + 80), (body_x + 50, self.height - 30)],
            fill=body_color, width=20
        )
        
        # Bigger, fewer spots
        baby_spot_count = max(8, spot_count // 2)
        for _ in range(baby_spot_count):
            spot_x = random.randint(body_x - 100, body_x + 100)
            spot_y = random.randint(body_y - 200, body_y + 60)
            spot_size = random.randint(10, 25)
            
            draw.ellipse(
                (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                fill=spot_color
            )
        
        return img
    
    def _draw_elongated_giraffe(self, draw: ImageDraw.Draw,
                              body_color: Tuple[int, int, int, int],
                              spot_color: Tuple[int, int, int, int],
                              spot_count: int,
                              neck_length: float,
                              params: Dict[str, Any]) -> Image.Image:
        """
        Draw an elongated giraffe with extended neck.
        
        Args:
            draw: ImageDraw object
            body_color: Body color
            spot_color: Spot color
            spot_count: Number of spots
            neck_length: Neck length multiplier
            params: Additional parameters
            
        Returns:
            Image with elongated giraffe drawn
        """
        img = draw._image
        
        body_x = self.width // 2
        body_y = self.height - 200
        
        # Extended neck based on neck_length parameter
        neck_start = (body_x - 50, body_y)
        neck_height = int(400 * neck_length)
        neck_end = (body_x + 100, body_y - neck_height)
        
        # Draw extended neck
        neck_width = random.randint(15, 35)  # Slightly thinner for elongated look
        draw.line([neck_start, neck_end], fill=body_color, width=neck_width)
        
        # Head (smaller relative to body for elongated effect)
        head_center = neck_end
        draw.ellipse(
            (head_center[0] - 25, head_center[1] - 15,
             head_center[0] + 35, head_center[1] + 25),
            fill=body_color
        )
        
        # Small ears
        draw.line([head_center, (head_center[0], head_center[1] - 40)], fill=body_color, width=4)
        
        # Normal body
        body_width = 180
        body_height = 90
        draw.rectangle(
            (body_x - body_width//2, body_y,
             body_x + body_width//2, body_y + body_height),
            fill=body_color
        )
        
        # Normal legs
        leg_width = 12
        leg_spacing = 70
        
        draw.line(
            [(body_x - leg_spacing//2, body_y + body_height),
             (body_x - leg_spacing//2 - 5, self.height - 50)],
            fill=body_color, width=leg_width
        )
        draw.line(
            [(body_x + leg_spacing//2, body_y + body_height),
             (body_x + leg_spacing//2 + 5, self.height - 50)],
            fill=body_color, width=leg_width
        )
        
        # Spots distributed along extended neck and body
        elongated_spot_count = spot_count + int(spot_count * 0.3)
        for _ in range(elongated_spot_count):
            # Focus on neck area for elongated giraffe
            spot_x = random.randint(body_x - 120, body_x + 150)
            spot_y = random.randint(body_y - neck_height + 50, self.height - 50)
            
            # Avoid ground and sky areas
            if spot_y > self.height - 100 or spot_y < head_center[1] - 30:
                continue
                
            spot_size = random.randint(5, 18)
            draw.ellipse(
                (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                fill=spot_color
            )
        
        return img
    
    def _draw_giraffe_spots(self, draw: ImageDraw.Draw,
                          spot_color: Tuple[int, int, int, int],
                          spot_count: int,
                          params: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Draw giraffe spots with various patterns.
        
        Args:
            draw: ImageDraw object
            spot_color: Spot color
            spot_count: Number of spots
            params: Additional parameters for spot customization
            
        Returns:
            Image with spots drawn
        """
        img = draw._image
        spot_pattern = params.get('spot_pattern', 'random') if params else 'random'
        
        body_x = self.width // 2
        body_y = self.height - 200
        
        if spot_pattern == 'clustered':
            # Generate spots in clusters
            cluster_count = max(3, spot_count // 5)
            for _ in range(cluster_count):
                cluster_center_x = random.randint(body_x - 100, body_x + 120)
                cluster_center_y = random.randint(body_y - 300, body_y + 50)
                cluster_spots = random.randint(3, 8)
                
                for _ in range(cluster_spots):
                    spot_x = cluster_center_x + random.randint(-30, 30)
                    spot_y = cluster_center_y + random.randint(-30, 30)
                    spot_size = random.randint(8, 22)
                    
                    draw.ellipse(
                        (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                        fill=spot_color
                    )
        
        else:  # random pattern
            for _ in range(spot_count):
                # Random spot position (focusing on neck and body area)
                spot_x = random.randint(body_x - 150, body_x + 200)
                spot_y = random.randint(body_y - 400, self.height - 50)
                
                # Skip spots that are too close to the ground or sky
                if spot_y > self.height - 100 or spot_y < body_y - 350:
                    continue
                    
                spot_size = random.randint(5, 20)
                draw.ellipse(
                    (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                    fill=spot_color
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
        # Adjust opacity based on type
        opacity = params.get('opacity', 1.0)
        if opacity < 1.0:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.putalpha(int(255 * opacity))
        
        # Add mystical/ink effects
        if params.get('ink_effects', False):
            img = self.apply_ink_blur(img, radius=2)
        
        # Add texture overlay
        if params.get('add_texture', False):
            texture = self.create_noise_layer(scale=0.5, opacity=30)
            img = Image.composite(img, texture, texture)
        
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "giraffe"
    
    @staticmethod
    def get_default_params() -> dict:
        """
        Get default parameters for this generator type.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'width': 600,
            'height': 800,
            'body_color': (212, 197, 176, 255),
            'spot_color': (20, 20, 20, 220),
            'spot_count': 20
        }
    
    def get_type_aware_params(self) -> Dict[str, Any]:
        """
        Get parameters expected by ElementType schema.
        
        Returns:
            Dictionary of type-aware parameters
        """
        return {
            'width': {'type': 'int', 'default': 600, 'min': 300, 'max': 1200},
            'height': {'type': 'int', 'default': 800, 'min': 400, 'max': 1600},
            'body_color': {'type': 'str', 'default': '#d4c5b0', 'description': 'Hex color string'},
            'spot_color': {'type': 'str', 'default': '#141414', 'description': 'Hex color string'},
            'spot_count': {'type': 'int', 'default': 20, 'min': 5, 'max': 50},
            'type': {'type': 'str', 'default': 'adult', 'choices': ['adult', 'baby', 'elongated']},
            'neck_length': {'type': 'float', 'default': 1.0, 'min': 0.5, 'max': 2.0},
            'spot_pattern': {'type': 'str', 'default': 'random', 'choices': ['random', 'clustered']},
            'opacity': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 1.0},
            'ink_effects': {'type': 'bool', 'default': False},
            'add_texture': {'type': 'bool', 'default': False}
        }
    
    def save_with_index(self, index: int) -> str:
        """
        Save a giraffe with the standard naming convention.
        
        Args:
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        img = self.generate()
        self.save_asset(img, self.category_map["creatures"], "giraffe", index)
        return f"{self.output_dir}/{self.category_map['creatures']}/giraffe_{index}.png"
    
    def generate_baby_giraffe(self) -> Image.Image:
        """
        Generate a baby giraffe with shorter neck and bigger spots.
        
        Returns:
            PIL Image of the baby giraffe
        """
        # Adjust parameters for baby giraffe
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        body_x = self.width // 2
        body_y = self.height - 150  # Lower body position
        
        # Shorter, thicker neck
        neck_start = (body_x - 40, body_y)
        neck_end = (body_x + 80, body_y - 250)  # Shorter neck
        draw.line([neck_start, neck_end], fill=self.body_color, width=30)
        
        # Bigger head
        head_center = neck_end
        draw.ellipse(
            (head_center[0] - 35, head_center[1] - 25,
             head_center[0] + 35, head_center[1] + 35),
            fill=self.body_color
        )
        
        # Rounder body
        draw.ellipse(
            (body_x - 80, body_y - 20,
             body_x + 80, body_y + 80),
            fill=self.body_color
        )
        
        # Thicker legs
        draw.line(
            [(body_x - 40, body_y + 80), (body_x - 50, self.height - 30)],
            fill=self.body_color, width=20
        )
        draw.line(
            [(body_x + 40, body_y + 80), (body_x + 50, self.height - 30)],
            fill=self.body_color, width=20
        )
        
        # Bigger, fewer spots
        for _ in range(12):
            spot_x = random.randint(body_x - 100, body_x + 100)
            spot_y = random.randint(body_y - 200, body_y + 60)
            spot_size = random.randint(10, 25)
            
            draw.ellipse(
                (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                fill=self.spot_color
            )
        
        img = self.apply_ink_blur(img, radius=1)
        return img
    
    def generate_parameter_suggestions(self, style_hint: str = None) -> Dict[str, Any]:
        """
        Generate parameter suggestions based on style hints.
        
        Args:
            style_hint: Optional style hint ("baby", "elongated", "clustered", etc.)
            
        Returns:
            Dictionary of suggested parameters
        """
        suggestions = {
            "baby": {
                "type": "baby",
                "spot_count": 12,
                "body_color": "#d4c5b0",
                "spot_color": "#1a1a1a"
            },
            "elongated": {
                "type": "elongated",
                "neck_length": 1.5,
                "spot_count": 25,
                "spot_pattern": "random"
            },
            "clustered": {
                "spot_pattern": "clustered",
                "spot_count": 30,
                "add_texture": True
            },
            "mystical": {
                "ink_effects": True,
                "opacity": 0.9,
                "body_color": "#b8a590",
                "spot_color": "#0a0a0a"
            },
            "minimal": {
                "spot_count": 8,
                "type": "baby",
                "opacity": 0.8
            }
        }
        
        if style_hint and style_hint in suggestions:
            return suggestions[style_hint]
        
        return suggestions.get("minimal", {})