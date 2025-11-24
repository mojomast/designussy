"""
Sigil Generator

This module implements the Arcane Sigil generator,
creating mystical geometric runes and symbols with glow effects.
"""

import random
import math
from typing import Optional, Tuple
from PIL import Image, ImageDraw
from .base_generator import BaseGenerator


class SigilGenerator(BaseGenerator):
    """
    Generator for Arcane Sigils.
    
    Creates mystical geometric runes and symbols with outer circles,
    connecting lines, and ethereal glow effects.
    """
    
    def __init__(self, width: int = 500, height: int = 500,
                 color: Optional[Tuple[int, int, int, int]] = None,
                 point_count_range: Tuple[int, int] = (3, 7), **kwargs):
        """
        Initialize the sigil generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            color: RGBA color for the sigil lines
            point_count_range: Min/max number of points in the sigil
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
        
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate an arcane sigil.
        
        Args:
            **kwargs: Override parameters (color, point_count_range)
            
        Returns:
            PIL Image of the generated sigil
        """
        # Allow parameter overrides
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
            'point_count_range': (3, 7)
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