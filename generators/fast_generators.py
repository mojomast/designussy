"""
Fast-Path Generators - Optimized Simple Asset Generation

Provides ultra-fast versions of generators for simple asset types
when performance is prioritized over visual complexity.
"""

import random
import math
import time
from typing import Optional, Tuple
from PIL import Image, ImageDraw

from .base_generator import BaseGenerator


class FastSigilGenerator(BaseGenerator):
    """
    Fast-path version of SigilGenerator for ultra-fast generation.
    
    Simplifies geometry and reduces processing steps for speed.
    """
    
    def __init__(self, width: int = 256, height: int = 256, **kwargs):
        """Initialize fast-path sigil generator."""
        super().__init__(width=width, height=height, fast_path=True, **kwargs)
        self.color = kwargs.get('color', (200, 180, 160, 255))
    
    def generate(self, **kwargs) -> Image.Image:
        """Generate a simplified sigil very quickly."""
        start_time = time.perf_counter()
        
        # Create transparent base image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate center
        cx, cy = self.width // 2, self.height // 2
        
        # Simple circle (no conditional logic for speed)
        margin = min(self.width, self.height) // 8
        radius = min(self.width, self.height) // 3
        
        # Fast point generation (fixed number for consistency)
        num_points = 6  # Fixed for speed
        points = []
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        
        # Draw simple polygon
        if len(points) >= 3:
            draw.polygon(points, outline=self.color, width=2)
        
        # Minimal center connections (only 3 lines for speed)
        for i in range(0, len(points), 2):
            draw.line((cx, cy, points[i][0], points[i][1]), fill=self.color, width=1)
        
        # Performance tracking
        if self.performance_config['monitoring']:
            self._track_performance('fast_generate', time.perf_counter() - start_time)
        
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "fast_sigil"


class FastEnsoGenerator(BaseGenerator):
    """
    Fast-path version of EnsoGenerator for ultra-fast generation.
    
    Uses simplified circle drawing with minimal complexity.
    """
    
    def __init__(self, width: int = 256, height: int = 256, **kwargs):
        """Initialize fast-path enso generator."""
        super().__init__(width=width, height=height, fast_path=True, **kwargs)
        self.color = kwargs.get('color', (212, 197, 176, 255))
    
    def generate(self, **kwargs) -> Image.Image:
        """Generate a simplified enso circle very quickly."""
        start_time = time.perf_counter()
        
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate center and radius
        cx, cy = self.width // 2, self.height // 2
        radius = min(self.width, self.height) // 3
        
        # Simple circle with fixed parameters for speed
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=self.color,
            width=3
        )
        
        # Simple arc for visual interest
        start_angle = 0
        end_angle = math.pi * 1.5
        
        # Convert to ellipse coordinates
        left = cx - radius
        top = cy - radius
        right = cx + radius
        bottom = cy + radius
        
        # Draw arc
        draw.arc(
            (left, top, right, bottom),
            start=int(math.degrees(start_angle)),
            end=int(math.degrees(end_angle)),
            fill=self.color,
            width=2
        )
        
        # Performance tracking
        if self.performance_config['monitoring']:
            self._track_performance('fast_generate', time.perf_counter() - start_time)
        
        return img
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "fast_enso"


class FastParchmentGenerator(BaseGenerator):
    """
    Fast-path version of ParchmentGenerator for ultra-fast generation.
    
    Uses pre-generated noise patterns and simplified processing.
    """
    
    def __init__(self, width: int = 512, height: int = 512, **kwargs):
        """Initialize fast-path parchment generator."""
        super().__init__(width=width, height=height, fast_path=True, **kwargs)
        self.base_color = kwargs.get('base_color', (212, 197, 176))
        
        # Pre-generate basic noise patterns for fast access
        self._pregenerated_noise = None
        if self.performance_config['enable_precomputation']:
            self._pregenerated_noise = self._generate_fast_noise()
    
    def _generate_fast_noise(self) -> Image.Image:
        """Generate basic noise pattern quickly."""
        # Use smaller noise array and scale up for speed
        small_width, small_height = 64, 64
        noise_data = [[random.randint(200, 240) for _ in range(small_width)] 
                     for _ in range(small_height)]
        
        noise_img = Image.new('L', (small_width, small_height))
        noise_img.putdata([pixel for row in noise_data for pixel in row])
        
        # Scale up to target size
        return noise_img.resize((self.width, self.height), Image.LANCZOS)
    
    def generate(self, **kwargs) -> Image.Image:
        """Generate simplified parchment very quickly."""
        start_time = time.perf_counter()
        
        # Use pre-generated noise if available
        if self._pregenerated_noise is not None:
            noise_layer = self._pregenerated_noise.copy()
        else:
            noise_layer = self.create_noise_layer(scale=0.5, opacity=128)
        
        # Create base parchment color
        parchment = Image.new('RGB', (self.width, self.height), self.base_color)
        
        # Simple blend (no multiple noise layers for speed)
        result = Image.blend(parchment, noise_layer.convert('RGB'), 0.3)
        
        # Minimal vignette for speed
        vignette = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        vignette_draw = ImageDraw.Draw(vignette)
        
        # Simple corner darkening
        corner_size = min(self.width, self.height) // 6
        vignette_draw.ellipse(
            (self.width - corner_size, self.height - corner_size,
             self.width + corner_size, self.height + corner_size),
            fill=(50, 50, 50)
        )
        
        result = Image.blend(result, vignette, 0.1)
        
        # Performance tracking
        if self.performance_config['monitoring']:
            self._track_performance('fast_generate', time.perf_counter() - start_time)
        
        return result
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return "fast_parchment"


class FastGeneratorFactory:
    """Factory for creating fast-path generators."""
    
    _generators = {
        'sigil': FastSigilGenerator,
        'enso': FastEnsoGenerator,
        'parchment': FastParchmentGenerator,
    }
    
    @classmethod
    def create_generator(cls, generator_type: str, **kwargs) -> Optional[BaseGenerator]:
        """Create a fast-path generator if available."""
        if generator_type in cls._generators:
            return cls._generators[generator_type](**kwargs)
        return None
    
    @classmethod
    def is_fast_path_available(cls, generator_type: str) -> bool:
        """Check if fast-path version is available for generator type."""
        return generator_type in cls._generators
    
    @classmethod
    def list_fast_generators(cls) -> list:
        """List available fast-path generators."""
        return list(cls._generators.keys())


# Performance comparison utilities
def compare_fast_vs_standard(generator_type: str, iterations: int = 5) -> dict:
    """Compare fast-path vs standard generator performance."""
    from .factory import GeneratorFactory
    
    factory = GeneratorFactory()
    fast_factory = FastGeneratorFactory()
    
    # Test standard generator
    standard_times = []
    try:
        standard_gen = factory.create_generator(generator_type)
        for _ in range(iterations):
            start = time.perf_counter()
            standard_gen.generate()
            standard_times.append(time.perf_counter() - start)
    except:
        standard_times = [float('inf')] * iterations
    
    # Test fast generator
    fast_times = []
    try:
        fast_gen = fast_factory.create_generator(generator_type)
        for _ in range(iterations):
            start = time.perf_counter()
            fast_gen.generate()
            fast_times.append(time.perf_counter() - start)
    except:
        fast_times = [float('inf')] * iterations
    
    return {
        'generator_type': generator_type,
        'standard_avg_time': sum(standard_times) / len(standard_times),
        'fast_avg_time': sum(fast_times) / len(fast_times),
        'speedup': (sum(standard_times) / len(standard_times)) / (sum(fast_times) / len(fast_times)) if sum(fast_times) > 0 else 0,
        'standard_times': standard_times,
        'fast_times': fast_times
    }