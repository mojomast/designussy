"""
Giraffe Generator

This module implements the Ink Giraffe creature generator,
creating stylized giraffe silhouettes with spots and ink effects.
"""

import random
from typing import Optional, Tuple
from PIL import Image, ImageDraw
from .base_generator import BaseGenerator


class GiraffeGenerator(BaseGenerator):
    """
    Generator for Ink Giraffe creatures.
    
    Creates stylized giraffe silhouettes with elongated necks,
    spots, and ink-like appearance.
    """
    
    def __init__(self, width: int = 600, height: int = 800,
                 body_color: Optional[Tuple[int, int, int, int]] = None,
                 spot_color: Optional[Tuple[int, int, int, int]] = None,
                 spot_count: int = 20, **kwargs):
        """
        Initialize the giraffe generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            body_color: RGBA color for the giraffe body
            spot_color: RGBA color for the giraffe spots
            spot_count: Number of spots to generate
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
        
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate an ink giraffe.
        
        Args:
            **kwargs: Override parameters (body_color, spot_color, spot_count)
            
        Returns:
            PIL Image of the generated giraffe
        """
        # Allow parameter overrides
        body_color = kwargs.get('body_color', self.body_color)
        spot_color = kwargs.get('spot_color', self.spot_color)
        spot_count = kwargs.get('spot_count', self.spot_count)
        
        self.logger.info(f"Generating giraffe with {spot_count} spots")
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
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
        
        # Generate spots throughout the giraffe
        for _ in range(spot_count):
            # Random spot position (focusing on neck and body area)
            spot_x = random.randint(body_x - 150, body_x + 200)
            spot_y = random.randint(body_y - 400, self.height - 50)
            
            # Skip spots that are too close to the ground or sky
            if spot_y > self.height - 100 or spot_y < head_center[1] - 50:
                continue
                
            spot_size = random.randint(5, 20)
            draw.ellipse(
                (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                fill=spot_color
            )
        
        # Apply ink blur for organic feel
        img = self.apply_ink_blur(img, radius=1)
        
        # Final validation
        img = self.validate_output_size(img)
        
        self.logger.info("Giraffe generation completed")
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