"""
Unit tests for ParchmentGenerator class.

Tests the parchment texture generation including noise patterns,
aging effects, and texture validation.
"""

import pytest
import numpy as np
from PIL import Image

from generators.parchment_generator import ParchmentGenerator
from tests.conftest import assert_images_similar, assert_image_has_content


class TestParchmentGenerator:
    """Test suite for ParchmentGenerator functionality."""
    
    def test_generator_type(self):
        """Test that generator type is correctly identified."""
        generator = ParchmentGenerator()
        assert generator.get_generator_type() == "parchment"
    
    def test_default_parameters(self):
        """Test default parameter values."""
        generator = ParchmentGenerator()
        params = generator.get_default_params()
        
        assert 'width' in params
        assert 'height' in params
        assert 'grain_level' in params
        assert 'age_level' in params
        assert 'seed' in params
        assert params['width'] == 1024
        assert params['height'] == 1024
    
    def test_generate_basic_parchment(self):
        """Test basic parchment generation."""
        generator = ParchmentGenerator(width=256, height=256)
        img = generator.generate()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert img.mode in ["RGBA", "RGB"]
        assert_image_has_content(img, min_pixels=20)
    
    def test_different_sizes(self):
        """Test parchment generation at different sizes."""
        sizes = [(128, 128), (256, 256), (512, 512), (1024, 768)]
        
        for width, height in sizes:
            generator = ParchmentGenerator(width=width, height=height)
            img = generator.generate()
            
            assert img.size == (width, height)
            assert_image_has_content(img, min_pixels=5)
    
    def test_seed_consistency(self):
        """Test that same seed produces same parchment."""
        generator1 = ParchmentGenerator(width=256, height=256, seed=42)
        generator2 = ParchmentGenerator(width=256, height=256, seed=42)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        assert_images_similar(img1, img2, tolerance=0.01)
    
    def test_save_with_index(self):
        """Test saving parchment with index."""
        generator = ParchmentGenerator(output_dir="/tmp")
        filename = generator.save_with_index(1)
        
        assert filename.endswith("parchment_1.png")
        
        # Clean up
        import os
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass