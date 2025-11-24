"""
Example Custom Generator

This module demonstrates how to create a custom generator that inherits
from BaseGenerator and integrates with the plugin system.
"""

import random
import math
from typing import Optional, Tuple
from PIL import Image, ImageDraw
from .base_generator import BaseGenerator


class StarFieldGenerator(BaseGenerator):
    """
    Example custom generator for creating star field backgrounds.
    
    This demonstrates:
    - How to inherit from BaseGenerator
    - How to implement required methods
    - How to add custom functionality
    - How to integrate with the plugin system
    """
    
    def __init__(self, width: int = 1024, height: int = 1024,
                 star_count: int = 200,
                 star_colors: Optional[Tuple[Tuple[int, int, int, int], ...]] = None,
                 nebula_colors: Optional[Tuple[int, int, int]] = None,
                 **kwargs):
        """
        Initialize the star field generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            star_count: Number of stars to generate
            star_colors: Tuple of possible star colors (RGBA)
            nebula_colors: RGB tuple for nebula background color
            **kwargs: Additional configuration options
        """
        # Default star colors (white, blue, yellow, red stars)
        if star_colors is None:
            star_colors = (
                (255, 255, 255, 255),    # White
                (200, 220, 255, 240),    # Blue-white
                (255, 255, 200, 235),    # Yellow-white
                (255, 200, 200, 220),    # Red-white
                (180, 180, 255, 200),    # Pale blue
            )
        
        # Default nebula color (dark space)
        if nebula_colors is None:
            nebula_colors = (10, 15, 25)
        
        super().__init__(
            width=width,
            height=height,
            star_count=star_count,
            star_colors=star_colors,
            nebula_colors=nebula_colors,
            **kwargs
        )
        
        self.star_count = star_count
        self.star_colors = star_colors
        self.nebula_colors = nebula_colors
        
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate a star field background.
        
        Args:
            **kwargs: Override parameters (star_count, star_colors, nebula_colors)
            
        Returns:
            PIL Image of the generated star field
        """
        # Allow parameter overrides
        star_count = kwargs.get('star_count', self.star_count)
        star_colors = kwargs.get('star_colors', self.star_colors)
        nebula_colors = kwargs.get('nebula_colors', self.nebula_colors)
        
        self.logger.info(f"Generating star field with {star_count} stars")
        
        # Create base image with nebula background
        img = Image.new('RGB', (self.width, self.height), nebula_colors)
        
        # Add some nebula texture with noise
        nebula_noise = self.create_noise_layer(scale=0.3, opacity=30)
        
        # Apply subtle color to the noise
        from PIL import ImageOps
        colorized_noise = ImageOps.colorize(nebula_noise, (0, 0, 0), nebula_colors)
        img = Image.blend(img, colorized_noise, 0.3)
        
        # Generate stars
        draw = ImageDraw.Draw(img)
        
        for _ in range(star_count):
            # Random position
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            
            # Random star properties
            star_color = random.choice(star_colors)
            star_size = random.choice([1, 1, 1, 1, 2, 2, 3])  # Mostly small stars
            
            # Draw star
            if star_size == 1:
                # Single pixel star
                if 0 <= x < self.width and 0 <= y < self.height:
                    img.putpixel((x, y), star_color[:3])
            else:
                # Multi-pixel star
                for dx in range(-star_size//2, star_size//2 + 1):
                    for dy in range(-star_size//2, star_size//2 + 1):
                        px, py = x + dx, y + dy
                        if (0 <= px < self.width and 0 <= py < self.height and
                            dx*dx + dy*dy <= star_size*star_size):
                            # Create gradient effect for larger stars
                            distance = math.sqrt(dx*dx + dy*dy)
                            alpha = max(0, 255 - int(distance * 60))
                            star_rgb = star_color[:3]
                            
                            # Blend with existing pixel
                            existing = img.getpixel((px, py))
                            blend_r = int((star_rgb[0] * alpha + existing[0] * (255 - alpha)) / 255)
                            blend_g = int((star_rgb[1] * alpha + existing[1] * (255 - alpha)) / 255)
                            blend_b = int((star_rgb[2] * alpha + existing[2] * (255 - alpha)) / 255)
                            
                            img.putpixel((px, py), (blend_r, blend_g, blend_b))
        
        # Add some shooting stars
        self._add_shooting_stars(img, count=max(1, star_count // 100))
        
        # Apply subtle blur for depth
        img = self.apply_ink_blur(img, radius=0.5)
        
        # Final validation
        img = self.validate_output_size(img)
        
        self.logger.info("Star field generation completed")
        return img
    
    def _add_shooting_stars(self, img: Image.Image, count: int = 2) -> None:
        """
        Add shooting stars to the image.
        
        Args:
            img: PIL Image to add shooting stars to
            count: Number of shooting stars to add
        """
        draw = ImageDraw.Draw(img)
        
        for _ in range(count):
            # Random start and end points
            start_x = random.randint(-100, self.width // 2)
            start_y = random.randint(0, self.height // 3)
            end_x = start_x + random.randint(50, 200)
            end_y = start_y + random.randint(20, 100)
            
            # Create shooting star path
            points = []
            steps = 20
            for i in range(steps):
                t = i / (steps - 1)
                x = int(start_x + (end_x - start_x) * t)
                y = int(start_y + (end_y - start_y) * t)
                points.append((x, y))
            
            # Draw shooting star with gradient effect
            for i, (x, y) in enumerate(points):
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Fade out towards the end
                    alpha = max(0, 255 - i * 10)
                    color = (255, 255, 255, alpha)
                    
                    # Draw main streak
                    if i > 0:
                        prev_x, prev_y = points[i-1]
                        draw.line([(prev_x, prev_y), (x, y)], fill=(255, 255, 255), width=2)
                    
                    # Draw bright head
                    if i == len(points) - 1:
                        draw.ellipse((x-3, y-3, x+3, y+3), fill=(255, 255, 255))
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "starfield"
    
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
            'star_count': 200,
            'star_colors': (
                (255, 255, 255, 255),
                (200, 220, 255, 240),
                (255, 255, 200, 235),
                (255, 200, 200, 220),
                (180, 180, 255, 200),
            ),
            'nebula_colors': (10, 15, 25)
        }
    
    def save_with_index(self, index: int) -> str:
        """
        Save a star field with the standard naming convention.
        
        Args:
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        img = self.generate()
        self.save_asset(img, self.category_map["backgrounds"], "starfield", index)
        return f"{self.output_dir}/{self.category_map['backgrounds']}/starfield_{index}.png"
    
    def generate_constellation(self, constellation_name: str = "Orion") -> Image.Image:
        """
        Generate a star field with a specific constellation pattern.
        
        Args:
            constellation_name: Name of constellation to include
            
        Returns:
            PIL Image with constellation pattern
        """
        # Base star field
        img = self.generate()
        draw = ImageDraw.Draw(img)
        
        # Orion constellation pattern (simplified)
        if constellation_name.lower() == "orion":
            orion_stars = [
                (200, 100),  # Betelgeuse
                (350, 120),  # Bellatrix
                (280, 300),  # Alnilam
                (320, 320),  # Alnitak
                (240, 330),  # Mintaka
                (180, 450),  # Saiph
                (380, 470),  # Rigel
            ]
            
            # Draw constellation stars (brighter)
            for x, y in orion_stars:
                if 0 <= x < self.width and 0 <= y < self.height:
                    draw.ellipse((x-4, y-4, x+4, y+4), fill=(255, 255, 255))
                    # Add outer glow
                    draw.ellipse((x-6, y-6, x+6, y+6), outline=(200, 200, 255), width=1)
            
            # Draw constellation lines
            lines = [
                ((200, 100), (280, 300)),  # Betelgeuse to Alnilam
                ((350, 120), (320, 320)),  # Bellatrix to Alnitak
                ((240, 330), (320, 320)),  # Mintaka to Alnitak
                ((280, 300), (180, 450)),  # Alnilam to Saiph
                ((320, 320), (380, 470)),  # Alnitak to Rigel
            ]
            
            for start, end in lines:
                draw.line([start, end], fill=(150, 150, 255), width=1)
        
        return img


# To register this generator with the plugin system, add this to your __init__.py:
# from .example_generator import StarFieldGenerator
# default_registry.register("starfield", StarFieldGenerator)


if __name__ == "__main__":
    # Example usage
    print("Creating StarFieldGenerator...")
    
    generator = StarFieldGenerator(width=800, height=600, star_count=150)
    
    print(f"Generator type: {generator.get_generator_type()}")
    print(f"Default params: {generator.get_default_params()}")
    
    # Generate and save
    img = generator.generate()
    filename = generator.save_with_index(1)
    print(f"Saved star field to: {filename}")
    
    # Generate constellation variant
    constellation_img = generator.generate_constellation("Orion")
    print("Generated Orion constellation variant")
    
    print("StarFieldGenerator example completed!")