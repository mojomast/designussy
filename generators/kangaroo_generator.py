"""
Kangaroo Generator

This module implements the Ink Kangaroo creature generator,
creating stylized kangaroo silhouettes on pogo sticks with ink effects.
"""

import random
import math
from typing import Optional, Tuple
from PIL import Image, ImageDraw
from .base_generator import BaseGenerator


class KangarooGenerator(BaseGenerator):
    """
    Generator for Ink Kangaroo on Pogo Stick creatures.
    
    Creates stylized kangaroo silhouettes with pogo stick and
    bouncy spring effects, maintaining the ink aesthetic.
    """
    
    def __init__(self, width: int = 600, height: int = 800,
                 ink_color: Optional[Tuple[int, int, int, int]] = None,
                 parchment_color: Optional[Tuple[int, int, int, int]] = None,
                 spot_count: int = 15, **kwargs):
        """
        Initialize the kangaroo generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            ink_color: RGBA color for shadows and details
            parchment_color: RGBA color for main kangaroo body
            spot_count: Number of ink spots to generate
            **kwargs: Additional configuration options
        """
        if ink_color is None:
            ink_color = (10, 10, 12, 240)      # Dark ink
        if parchment_color is None:
            parchment_color = (212, 197, 176, 255)  # Parchment color
            
        super().__init__(
            width=width,
            height=height,
            ink_color=ink_color,
            parchment_color=parchment_color,
            spot_count=spot_count,
            **kwargs
        )
        
        self.ink_color = ink_color
        self.parchment_color = parchment_color
        self.spot_count = spot_count
        
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate an ink kangaroo on pogo stick.
        
        Args:
            **kwargs: Override parameters (ink_color, parchment_color, spot_count)
            
        Returns:
            PIL Image of the generated kangaroo
        """
        # Allow parameter overrides
        ink_color = kwargs.get('ink_color', self.ink_color)
        parchment_color = kwargs.get('parchment_color', self.parchment_color)
        spot_count = kwargs.get('spot_count', self.spot_count)
        
        self.logger.info(f"Generating kangaroo with {spot_count} ink spots")
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Define center position
        cx, cy = self.width // 2, self.height // 2
        
        # POGO STICK COMPONENTS
        # Main pogo stick shaft
        draw.line([(cx, cy - 50), (cx, cy + 250)], fill=ink_color, width=10)
        
        # Handle bars
        draw.line([(cx - 40, cy - 40), (cx + 40, cy - 40)], fill=ink_color, width=8)
        draw.line([(cx - 30, cy + 180), (cx + 30, cy + 180)], fill=ink_color, width=8)
        
        # Spring/pogo mechanism
        spring_points = []
        for i in range(12):
            offset = 15 if i % 2 == 0 else -15
            spring_points.append((cx + offset, cy + 180 + i * 5))
        
        if len(spring_points) > 1:
            draw.line(spring_points, fill=ink_color, width=4)
        
        # KANGAROO BODY
        # Tail (distinctive kangaroo feature)
        tail_points = [
            (cx - 40, cy + 50),
            (cx - 150, cy + 20),
            (cx - 180, cy - 50)
        ]
        draw.line(tail_points, fill=parchment_color, width=25)
        
        # Body (torso)
        body_center_x = cx
        body_center_y = cy - 10
        body_width = 100
        body_height = 180
        draw.ellipse(
            (body_center_x - body_width//2, body_center_y - body_height//2,
             body_center_x + body_width//2, body_center_y + body_height//2),
            fill=parchment_color
        )
        
        # Head
        head_center_x = cx
        head_center_y = cy - 130
        head_width = 80
        head_height = 70
        draw.ellipse(
            (head_center_x - head_width//2, head_center_y - head_height//2,
             head_center_x + head_width//2, head_center_y + head_height//2),
            fill=parchment_color
        )
        
        # Ears
        # Left ear
        left_ear_points = [
            (head_center_x, head_center_y - 50),
            (head_center_x - 10, head_center_y - 120),
            (head_center_x + 10, head_center_y - 60)
        ]
        draw.polygon(left_ear_points, fill=parchment_color)
        
        # Right ear
        right_ear_points = [
            (head_center_x + 25, head_center_y - 50),
            (head_center_x + 40, head_center_y - 110),
            (head_center_x + 35, head_center_y - 60)
        ]
        draw.polygon(right_ear_points, fill=parchment_color)
        
        # Arms
        draw.line(
            [(head_center_x - 20, head_center_y + 50),
             (head_center_x - 60, head_center_y + 80)],
            fill=parchment_color, width=15
        )
        draw.line(
            [(head_center_x + 20, head_center_y + 50),
             (head_center_x + 60, head_center_y + 80)],
            fill=parchment_color, width=15
        )
        
        # Legs connecting to pogo
        draw.line(
            [(body_center_x - 30, body_center_y + 70),
             (body_center_x - 25, body_center_y + 150)],
            fill=parchment_color, width=12
        )
        draw.line(
            [(body_center_x + 30, body_center_y + 70),
             (body_center_x + 25, body_center_y + 150)],
            fill=parchment_color, width=12
        )
        
        # Connection to pogo stick
        draw.line(
            [(body_center_x - 30, head_center_y + 20),
             (head_center_x - 35, head_center_y + 40)],
            fill=parchment_color, width=10
        )
        draw.line(
            [(body_center_x + 30, head_center_y + 20),
             (head_center_x + 35, head_center_y + 40)],
            fill=parchment_color, width=10
        )
        
        # Eyes
        eye_x = head_center_x + 10
        eye_y = head_center_y - 10
        draw.ellipse(
            (eye_x, eye_y, eye_x + 10, eye_y + 10),
            fill=ink_color
        )
        
        # Generate ink spots around the kangaroo (debris effect)
        for _ in range(spot_count):
            spot_x = random.randint(cx - 100, cx + 100)
            spot_y = random.randint(cy + 200, cy + 300)
            spot_size = random.randint(2, 8)
            
            draw.ellipse(
                (spot_x, spot_y, spot_x + spot_size, spot_y + spot_size),
                fill=ink_color
            )
        
        # Apply ink blur for organic feel
        img = self.apply_ink_blur(img, radius=1)
        
        # Final validation
        img = self.validate_output_size(img)
        
        self.logger.info("Kangaroo generation completed")
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "kangaroo"
    
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
            'ink_color': (10, 10, 12, 240),
            'parchment_color': (212, 197, 176, 255),
            'spot_count': 15
        }
    
    def save_with_index(self, index: int) -> str:
        """
        Save a kangaroo with the standard naming convention.
        
        Args:
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        img = self.generate()
        self.save_asset(img, self.category_map["creatures"], "kangaroo", index)
        return f"{self.output_dir}/{self.category_map['creatures']}/kangaroo_{index}.png"
    
    def generate_super_bouncy_kangaroo(self) -> Image.Image:
        """
        Generate a kangaroo with exaggerated spring/bounce effects.
        
        Returns:
            PIL Image of the super bouncy kangaroo
        """
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = self.width // 2, self.height // 2
        
        # Extra long pogo stick
        draw.line([(cx, cy - 80), (cx, cy + 300)], fill=self.ink_color, width=12)
        
        # Multiple handle bars for bouncing effect
        for y_offset in [-40, -20, 0, 20, 40]:
            draw.line(
                [(cx - 40, cy + y_offset), (cx + 40, cy + y_offset)],
                fill=self.ink_color, width=6
            )
        
        # Compressed spring with more coils
        spring_points = []
        for i in range(20):  # More coils
            offset = 20 if i % 2 == 0 else -20
            spring_points.append((cx + offset, cy + 200 + i * 4))
        
        if len(spring_points) > 1:
            draw.line(spring_points, fill=self.ink_color, width=5)
        
        # Kangaroo in "compressed" bounce pose
        body_y = cy - 30  # Lower body position
        draw.ellipse(
            (cx - 50, body_y - 60, cx + 50, body_y + 60),
            fill=self.parchment_color
        )
        
        # Compressed head
        head_y = body_y - 80
        draw.ellipse(
            (cx - 30, head_y - 40, cx + 30, head_y + 40),
            fill=self.parchment_color
        )
        
        # Ears in wind-blown position
        left_ear = [(cx - 10, head_y - 40), (cx - 25, head_y - 80), (cx - 5, head_y - 50)]
        draw.polygon(left_ear, fill=self.parchment_color)
        
        right_ear = [(cx + 10, head_y - 40), (cx + 25, head_y - 80), (cx + 5, head_y - 50)]
        draw.polygon(right_ear, fill=self.parchment_color)
        
        # Arms raised in bounce
        draw.line(
            [(cx - 25, body_y), (cx - 60, body_y - 40)],
            fill=self.parchment_color, width=18
        )
        draw.line(
            [(cx + 25, body_y), (cx + 60, body_y - 40)],
            fill=self.parchment_color, width=18
        )
        
        # Motion lines (ink streaks)
        for i in range(5):
            motion_y = cy + 250 + i * 15
            draw.ellipse(
                (cx - 15 - i * 5, motion_y, cx - 10 - i * 5, motion_y + 8),
                fill=self.ink_color
            )
        
        img = self.apply_ink_blur(img, radius=1)
        return img