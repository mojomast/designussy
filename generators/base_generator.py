"""
Base Generator Class

This module provides the base class for all asset generators in the NanoBanana system.
It contains common functionality, utilities, and interfaces that all generators can inherit.
"""

import os
import math
import random
import logging
import time
import threading
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import colorsys
import re
from .schemas import GenerationParameters, ParameterValidationResult


class BaseGenerator(ABC):
    """
    Abstract base class for all asset generators.
    
    Provides common functionality including:
    - Image creation and manipulation
    - Noise generation utilities (optimized)
    - Color manipulation
    - Configuration management
    - Error handling
    - Logging infrastructure
    - Performance monitoring
    - Advanced parameter processing
    - Quality and style controls
    """
    
    def __init__(self, width: int = 1024, height: int = 1024, seed: Optional[int] = None, **kwargs):
        """
        Initialize the base generator.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            seed: Optional random seed for reproducible generation
            **kwargs: Additional generator-specific configuration
        """
        self.width = width
        self.height = height
        self.seed = seed
        self.config = kwargs
        
        # Performance configuration
        self.performance_config = {
            'level': os.getenv('PERFORMANCE_LEVEL', 'balanced'),
            'enable_precomputation': os.getenv('ENABLE_PRECOMPUTATION', 'true').lower() == 'true',
            'noise_cache_size': int(os.getenv('NOISE_CACHE_SIZE', '50')),
            'image_pool_size': int(os.getenv('IMAGE_POOL_SIZE', '10')),
            'parallel_generation': os.getenv('PARALLEL_GENERATION', 'true').lower() == 'true',
            'max_workers': int(os.getenv('MAX_WORKERS', '4')),
            'fast_path': os.getenv('ENABLE_FAST_PATH', 'false').lower() == 'true',
            'monitoring': os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
        }
        
        # Set up logging
        self._setup_logging()
        
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Initialize common image processing attributes
        self.base_color = kwargs.get('base_color', (15, 15, 18))
        self.output_dir = kwargs.get('output_dir', 'assets/elements')
        self.category_map = {
            "backgrounds": "backgrounds",
            "glyphs": "glyphs",
            "creatures": "creatures",
            "ui": "ui"
        }
        
        # Performance monitoring
        self._performance_data = {
            'generation_times': [],
            'memory_usage': [],
            'operation_counts': {}
        }
        self._perf_lock = threading.Lock()
        
        # Cache for expensive operations
        self._noise_cache = {}
        self._gradient_cache = {}
        self._image_pool = []
        
        # Ensure output directories exist
        self._ensure_directories()
        
        # Setup validation
        self._validate_config()
    
    def _setup_logging(self):
        """Set up logging for the generator."""
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _ensure_directories(self):
        """Ensure all output directories exist."""
        for category in self.category_map.values():
            dir_path = os.path.join(self.output_dir, category)
            os.makedirs(dir_path, exist_ok=True)
    
    def _validate_config(self):
        """Validate the generator configuration."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.width}x{self.height}")
        
        if not (1 <= self.base_color[0] <= 255 and 
                1 <= self.base_color[1] <= 255 and 
                1 <= self.base_color[2] <= 255):
            raise ValueError(f"Invalid base color: {self.base_color}")
    
    def validate_parameters(self, parameters: GenerationParameters) -> ParameterValidationResult:
        """
        Validate advanced generation parameters.
        
        Args:
            parameters: GenerationParameters object to validate
            
        Returns:
            ParameterValidationResult with validation results and suggestions
        """
        result = ParameterValidationResult(is_valid=True)
        
        # Check dimension constraints
        effective_width, effective_height = parameters.get_effective_dimensions()
        max_resolution = int(os.getenv('MAX_RESOLUTION', '2048'))
        min_resolution = int(os.getenv('MIN_RESOLUTION', '64'))
        
        if effective_width > max_resolution or effective_height > max_resolution:
            result.add_warning(f"High resolution {effective_width}x{effective_height} may impact performance")
            
        if effective_width < min_resolution or effective_height < min_resolution:
            result.add_error(f"Resolution too low: minimum {min_resolution}x{min_resolution}")
            result.is_valid = False
        
        # Check color palette constraints
        if parameters.color_palette:
            max_colors = int(os.getenv('MAX_COLORS_IN_PALETTE', '10'))
            if len(parameters.color_palette) > max_colors:
                result.add_warning(f"Large color palette ({len(parameters.color_palette)} colors) may impact generation speed")
        
        # Check quality vs performance implications
        if parameters.quality == "ultra" and self.performance_config.get('fast_path'):
            result.add_warning("Ultra quality may bypass fast path optimizations")
        
        # Validate quality parameters consistency
        quality_settings = parameters.get_quality_settings()
        if parameters.complexity > quality_settings.get('detail_level', 1.0):
            result.add_suggestion(f"High complexity ({parameters.complexity}) with {parameters.quality} quality may cause artifacts")
        
        # Set effective parameters in result
        result.effective_parameters = parameters
        
        return result
    
    def apply_color_palette(self, img: Image.Image, color_palette: List[str]) -> Image.Image:
        """
        Apply a custom color palette to the image.
        
        Args:
            img: PIL Image to apply palette to
            color_palette: List of hex color strings
            
        Returns:
            PIL Image with palette applied
        """
        if not color_palette or len(color_palette) == 0:
            return img
        
        # Convert hex colors to RGB tuples
        rgb_palette = []
        for hex_color in color_palette:
            hex_color = hex_color.lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            rgb_palette.append(rgb_color)
        
        # Convert image to palette mode if it's grayscale
        if img.mode == 'L':
            img = img.convert('RGB')
        
        # Create a color mapping
        img_array = np.array(img)
        
        # Apply simple color quantization to match palette
        for i, (r, g, b) in enumerate(img_array.reshape(-1, 3)):
            # Find closest color in palette
            distances = [((r - pr)**2 + (g - pg)**2 + (b - pb)**2)**0.5 
                        for pr, pg, pb in rgb_palette]
            closest_idx = distances.index(min(distances))
            img_array.flat[i*3:(i+1)*3] = rgb_palette[closest_idx]
        
        return Image.fromarray(img_array.astype(np.uint8), 'RGB')
    
    def apply_quality_rendering(self, img: Image.Image, quality: str, anti_aliasing: bool = True) -> Image.Image:
        """
        Apply quality-specific rendering settings to the image.
        
        Args:
            img: PIL Image to apply quality settings to
            quality: Quality level ("low", "medium", "high", "ultra")
            anti_aliasing: Whether to enable anti-aliasing
            
        Returns:
            PIL Image with quality settings applied
        """
        if quality == "low":
            # Minimal processing for speed
            return img.resize((self.width // 2, self.height // 2), Image.NEAREST).resize((self.width, self.height), Image.NEAREST)
        
        elif quality == "medium":
            # Balanced processing
            if anti_aliasing:
                img = img.filter(ImageFilter.SMOOTH_MORE)
            return img
        
        elif quality == "high":
            # Enhanced processing
            if anti_aliasing:
                img = img.filter(ImageFilter.SMOOTH_MORE)
            # Add slight sharpening
            img = ImageEnhance.Sharpness(img).enhance(1.1)
            return img
        
        elif quality == "ultra":
            # Maximum quality processing
            if anti_aliasing:
                img = img.filter(ImageFilter.SMOOTH_MORE)
            # Multiple enhancement passes
            img = ImageEnhance.Sharpness(img).enhance(1.2)
            img = ImageEnhance.Contrast(img).enhance(1.05)
            # Apply subtle unsharp mask
            img = self._apply_unsharp_mask(img, radius=1, amount=0.1)
            return img
        
        return img
    
    def _apply_unsharp_mask(self, img: Image.Image, radius: float = 1, amount: float = 0.1) -> Image.Image:
        """Apply an unsharp mask filter."""
        blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
        return Image.blend(img, blurred, amount)
    
    def apply_style_parameters(self, img: Image.Image, complexity: float, randomness: float, 
                             style_preset: Optional[str] = None) -> Image.Image:
        """
        Apply style-related parameters to modify the image appearance.
        
        Args:
            img: PIL Image to apply style to
            complexity: Detail complexity (0.0=simple, 1.0=complex)
            randomness: Random variation amount (0.0=deterministic, 1.0=very random)
            style_preset: Optional predefined style preset
            
        Returns:
            PIL Image with style parameters applied
        """
        # Apply complexity-based effects
        if complexity > 0.7:
            # Add fine detail enhancement
            img = ImageEnhance.Sharpness(img).enhance(1.0 + (complexity - 0.7) * 0.5)
        elif complexity < 0.3:
            # Smooth out details
            img = img.filter(ImageFilter.SMOOTH)
        
        # Apply randomness-based texture variation
        if randomness > 0.6:
            # Add noise for organic variation
            noise_scale = (randomness - 0.6) * 2.0
            noise_layer = self.create_noise_layer(scale=noise_scale, opacity=30)
            img = Image.composite(img, noise_layer, noise_layer)
        
        # Apply style preset effects
        if style_preset == "minimal":
            # Reduce texture intensity
            img = img.filter(ImageFilter.SMOOTH_MORE)
        elif style_preset == "chaotic":
            # Increase contrast and add noise
            img = ImageEnhance.Contrast(img).enhance(1.2)
            chaotic_noise = self.create_noise_layer(scale=2.0, opacity=40)
            img = Image.composite(img, chaotic_noise, chaotic_noise)
        elif style_preset == "ordered":
            # Enhance geometric precision
            img = ImageEnhance.Sharpness(img).enhance(1.3)
            img = img.filter(ImageFilter.SMOOTH_MORE)
        
        return img
    
    def resolve_parameters(self, legacy_params: Optional[Dict[str, Any]] = None) -> GenerationParameters:
        """
        Resolve and merge legacy parameters with default advanced parameters.
        
        Args:
            legacy_params: Legacy parameter dictionary (width, height, seed, etc.)
            
        Returns:
            Resolved GenerationParameters object
        """
        # Start with default parameters
        params = GenerationParameters()
        
        # Override with legacy parameters if provided
        if legacy_params:
            for key, value in legacy_params.items():
                if hasattr(params, key) and value is not None:
                    setattr(params, key, value)
        
        return params
    
    def enhance_with_parameters(self, img: Image.Image, parameters: GenerationParameters) -> Image.Image:
        """
        Apply all advanced parameters to enhance the generated image.
        
        Args:
            img: Base PIL Image to enhance
            parameters: GenerationParameters with all enhancement settings
            
        Returns:
            Enhanced PIL Image
        """
        self.logger.info(f"Applying advanced parameters: quality={parameters.quality}, style={parameters.style_preset}")
        
        # Apply color adjustments
        if parameters.contrast != 1.0 or parameters.brightness != 1.0 or parameters.saturation != 1.0:
            if parameters.contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(parameters.contrast)
            if parameters.brightness != 1.0:
                img = ImageEnhance.Brightness(img).enhance(parameters.brightness)
            if parameters.saturation != 1.0:
                img = ImageEnhance.Color(img).enhance(parameters.saturation)
        
        # Apply custom color palette
        if parameters.color_palette:
            img = self.apply_color_palette(img, parameters.color_palette)
        
        # Apply quality rendering
        img = self.apply_quality_rendering(img, parameters.quality, parameters.anti_aliasing)
        
        # Apply style parameters
        img = self.apply_style_parameters(img, parameters.complexity, parameters.randomness, parameters.style_preset)
        
        # Apply base color if specified
        if parameters.base_color:
            hex_color = parameters.base_color.lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # Tint the image with the base color
            tint = Image.new('RGB', img.size, rgb_color)
            img = Image.blend(img.convert('RGB'), tint, 0.1)
        
        return img
    
    @abstractmethod
    def generate(self, **kwargs) -> Image.Image:
        """
        Generate the asset.
        
        This method must be implemented by subclasses.
        
        Args:
            **kwargs: Generator-specific parameters or GenerationParameters object
            
        Returns:
            PIL Image of the generated asset
        """
        pass
    
    @abstractmethod 
    def get_generator_type(self) -> str:
        """
        Get the type of generator this is.
        
        Returns:
            String identifier for the generator type
        """
        pass
    
    def save_asset(self, img: Image.Image, category: str, name: str, index: int):
        """
        Save an asset to the file system.
        
        Args:
            img: PIL Image to save
            category: Category directory name
            name: Asset base name
            index: Asset index number
        """
        filename = os.path.join(self.output_dir, category, f"{name}_{index}.png")
        img.save(filename)
        self.logger.info(f"Generated {filename}")
    
    @lru_cache(maxsize=100)
    def _get_cached_noise_seed(self, scale: float, width: int, height: int) -> Optional[np.ndarray]:
        """Get cached noise pattern if available."""
        cache_key = (scale, width, height)
        return self._noise_cache.get(cache_key)
    
    def _store_cached_noise(self, scale: float, width: int, height: int, noise_data: np.ndarray):
        """Store noise pattern in cache."""
        if len(self._noise_cache) >= self.performance_config['noise_cache_size']:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._noise_cache))
            del self._noise_cache[oldest_key]
        
        cache_key = (scale, width, height)
        self._noise_cache[cache_key] = noise_data
    
    def create_noise_layer(self, scale: float = 1.0, opacity: int = 128) -> Image.Image:
        """
        Create a noise layer for texture generation (optimized).
        
        Args:
            scale: Noise intensity scale factor
            opacity: Alpha value for the noise
            
        Returns:
            PIL Image with noise
        """
        start_time = time.perf_counter()
        
        # Check for cached noise if precomputation is enabled
        if self.performance_config['enable_precomputation']:
            cached_noise = self._get_cached_noise_seed(scale, self.width, self.height)
            if cached_noise is not None:
                noise_img = Image.fromarray(cached_noise, mode='L')
            else:
                # Generate optimized noise
                noise_data = self._generate_optimized_noise(scale)
                self._store_cached_noise(scale, self.width, self.height, noise_data)
                noise_img = Image.fromarray(noise_data, mode='L')
        else:
            # Direct generation without caching
            noise_data = self._generate_optimized_noise(scale)
            noise_img = Image.fromarray(noise_data, mode='L')
        
        if opacity < 255:
            # Optimized opacity application
            noise_rgba = noise_img.convert('RGBA')
            alpha = noise_rgba.split()[-1]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 255.0)
            noise_rgba.putalpha(alpha)
            noise_img = noise_rgba
        
        # Performance tracking
        if self.performance_config['monitoring']:
            self._track_performance('create_noise_layer', time.perf_counter() - start_time)
            
        return noise_img
    
    def _generate_optimized_noise(self, scale: float) -> np.ndarray:
        """Generate noise using optimized NumPy operations."""
        # Use float32 for better performance and less memory
        noise_shape = (self.height, self.width)
        noise = np.random.normal(128, 50 * scale, noise_shape).astype(np.float32)
        
        # Apply scale and clamp for better performance
        if scale != 1.0:
            noise = noise * scale
        noise = np.clip(noise, 0, 255).astype(np.uint8)
        
        return noise
    
    def _track_performance(self, operation: str, duration: float, memory_mb: float = 0.0):
        """Track performance metrics for optimization monitoring."""
        if not self.performance_config['monitoring']:
            return
            
        with self._perf_lock:
            if operation not in self._performance_data['operation_counts']:
                self._performance_data['operation_counts'][operation] = 0
            self._performance_data['operation_counts'][operation] += 1
            self._performance_data['generation_times'].append(duration)
            
            if memory_mb > 0:
                self._performance_data['memory_usage'].append(memory_mb)
            
            # Keep only last 1000 measurements
            if len(self._performance_data['generation_times']) > 1000:
                self._performance_data['generation_times'] = self._performance_data['generation_times'][-1000:]
                if memory_mb > 0:
                    self._performance_data['memory_usage'] = self._performance_data['memory_usage'][-1000:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this generator instance."""
        if not self.performance_config['monitoring']:
            return {"monitoring_disabled": True}
            
        with self._perf_lock:
            times = self._performance_data['generation_times']
            memory = self._performance_data['memory_usage']
            operations = self._performance_data['operation_counts']
            
            if not times:
                return {"no_data": True}
            
            return {
                "avg_generation_time": sum(times) / len(times),
                "min_generation_time": min(times),
                "max_generation_time": max(times),
                "total_operations": sum(operations.values()),
                "operations_breakdown": operations.copy(),
                "avg_memory_usage": sum(memory) / len(memory) if memory else 0,
                "performance_level": self.performance_config['level'],
                "cache_enabled": self.performance_config['enable_precomputation'],
                "cache_size": len(self._noise_cache)
            }
    
    def clear_performance_cache(self):
        """Clear performance tracking data."""
        with self._perf_lock:
            self._performance_data = {
                'generation_times': [],
                'memory_usage': [],
                'operation_counts': {}
            }
        self._noise_cache.clear()
        self._gradient_cache.clear()
    
    def _get_preallocated_buffer(self, size: Tuple[int, int], mode: str = 'RGBA') -> Image.Image:
        """Get a pre-allocated image buffer from pool."""
        pool_size = self.performance_config['image_pool_size']
        
        # Simple pool implementation - can be enhanced
        if len(self._image_pool) < pool_size:
            return Image.new(mode, size, (0, 0, 0, 0))
        else:
            return Image.new(mode, size, (0, 0, 0, 0))
    
    def _optimize_pil_operations(self, img: Image.Image, operations: List[str]) -> Image.Image:
        """Apply PIL operations in optimized order."""
        result = img
        
        # Batch similar operations
        for operation in operations:
            if operation == 'blur':
                result = result.filter(ImageFilter.GaussianBlur(1.0))
            elif operation == 'enhance_contrast':
                result = ImageEnhance.Contrast(result).enhance(1.1)
            elif operation == 'slight_brightness':
                result = ImageEnhance.Brightness(result).enhance(1.05)
        
        return result
    
    def apply_vignette(self, img: Image.Image, intensity: float = 0.5) -> Image.Image:
        """
        Apply a vignette effect to the image (optimized).
        
        Args:
            img: PIL Image to apply vignette to
            intensity: Vignette intensity (0.0 to 1.0)
            
        Returns:
            PIL Image with vignette applied
        """
        start_time = time.perf_counter()
        
        # Use pre-allocated buffer
        vignette = self._get_preallocated_buffer((self.width, self.height), 'L')
        draw = ImageDraw.Draw(vignette)
        
        # Create elliptical vignette with optimized calculations
        margin = int(min(self.width, self.height) * 0.1 * (2 - intensity))
        draw.ellipse((margin, margin, self.width - margin, self.height - margin), fill=255)
        vignette = vignette.filter(ImageFilter.GaussianBlur(int(min(self.width, self.height) * 0.2)))
        
        # Apply vignette efficiently
        dark_layer = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        result = Image.composite(img, dark_layer, vignette)
        
        if self.performance_config['monitoring']:
            self._track_performance('apply_vignette', time.perf_counter() - start_time)
        
        return result
    
    def apply_ink_blur(self, img: Image.Image, radius: float = 1.0) -> Image.Image:
        """
        Apply a subtle ink blur effect to make drawings look more organic.
        
        Args:
            img: PIL Image to blur
            radius: Blur radius
            
        Returns:
            PIL Image with ink blur applied
        """
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    def apply_glow(self, img: Image.Image, glow_color: Tuple[int, int, int, int], blur_radius: int = 4) -> Image.Image:
        """
        Apply a glow effect to the image.
        
        Args:
            img: PIL Image to apply glow to
            glow_color: RGBA color for the glow
            blur_radius: Blur radius for the glow effect
            
        Returns:
            PIL Image with glow applied
        """
        glow = img.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Convert to RGBA if not already
        if glow.mode != 'RGBA':
            glow = glow.convert('RGBA')
        
        # Apply color to the glow
        glow_array = np.array(glow)
        height, width = glow_array.shape[:2]
        
        # Create colored glow channels
        red_channel = np.full((height, width), glow_color[0], dtype=np.uint8)
        green_channel = np.full((height, width), glow_color[1], dtype=np.uint8)
        blue_channel = np.full((height, width), glow_color[2], dtype=np.uint8)
        
        # Use alpha from original glow if available, otherwise use glow_color[3]
        if len(glow_array.shape) == 3 and glow_array.shape[2] == 4:
            alpha_channel = glow_array[:, :, 3]
        else:
            alpha_channel = np.full((height, width), glow_color[3], dtype=np.uint8)
        
        # Combine channels
        glow_rgba = np.stack([red_channel, green_channel, blue_channel, alpha_channel], axis=2)
        
        glow_colored = Image.fromarray(glow_rgba, 'RGBA')
        return Image.alpha_composite(glow_colored, img)
    
    def add_scratch_texture(self, img: Image.Image, scale: float = 1.5) -> Image.Image:
        """
        Add scratch texture to give parchment a weathered look.
        
        Args:
            img: PIL Image to add scratches to
            scale: Intensity of scratch texture
            
        Returns:
            PIL Image with scratch texture added
        """
        scratches = self.create_noise_layer(scale=scale + 0.5, opacity=100)
        scratches = scratches.resize((self.width, self.height // 10))
        scratches = scratches.resize((self.width, self.height), Image.BICUBIC)
        
        return Image.blend(img, scratches.convert('RGB'), 0.1)
    
    def validate_output_size(self, img: Image.Image) -> Image.Image:
        """
        Ensure the output image matches the expected dimensions.
        
        Args:
            img: PIL Image to validate and resize if needed
            
        Returns:
            PIL Image with correct dimensions
        """
        if img.size != (self.width, self.height):
            self.logger.warning(f"Resizing image from {img.size} to {(self.width, self.height)}")
            return img.resize((self.width, self.height), Image.LANCZOS)
        return img
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current generator configuration.
        
        Returns:
            Dictionary containing configuration details
        """
        return {
            'generator_type': self.get_generator_type(),
            'dimensions': (self.width, self.height),
            'seed': self.seed,
            'base_color': self.base_color,
            'output_dir': self.output_dir,
            'custom_config': self.config
        }
    
    def get_default_params(self) -> Dict[str, Any]:
        """
        Get default parameters for this generator type.
        This should be overridden by subclasses.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'width': 1024,
            'height': 1024,
            'seed': None,
            'base_color': (15, 15, 18)
        }
    
    def __str__(self) -> str:
        """String representation of the generator."""
        return f"{self.__class__.__name__}({self.width}x{self.height})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the generator."""
        return f"{self.__class__.__name__}(width={self.width}, height={self.height}, seed={self.seed})"