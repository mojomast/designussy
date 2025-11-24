"""
Unit tests for GiraffeGenerator class.

Tests the giraffe creature generation including body shapes,
patterns, and styling.
"""

import pytest
import numpy as np
from PIL import Image

from generators.giraffe_generator import GiraffeGenerator
from tests.conftest import assert_images_similar, assert_image_has_content


class TestGiraffeGenerator:
    """Test suite for GiraffeGenerator functionality."""
    
    def test_generator_type(self):
        """Test that generator type is correctly identified."""
        generator = GiraffeGenerator()
        assert generator.get_generator_type() == "giraffe"
    
    def test_default_parameters(self):
        """Test default parameter values."""
        generator = GiraffeGenerator()
        params = generator.get_default_params()
        
        assert 'width' in params
        assert 'height' in params
        assert 'pattern_style' in params
        assert 'size_factor' in params
        assert 'seed' in params
        assert params['width'] == 600
        assert params['height'] == 800
    
    def test_generate_basic_giraffe(self):
        """Test basic giraffe generation."""
        generator = GiraffeGenerator(width=256, height=256)
        img = generator.generate()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert img.mode in ["RGBA", "RGB"]
        assert_image_has_content(img, min_pixels=10)
    
    def test_generate_baby_giraffe(self):
        """Test baby giraffe generation."""
        generator = GiraffeGenerator(width=256, height=256)
        img = generator.generate_baby_giraffe()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert_image_has_content(img, min_pixels=5)
    
    def test_save_with_index(self):
        """Test saving giraffe with index."""
        generator = GiraffeGenerator(output_dir="/tmp")
        filename = generator.save_with_index(1)
        
        assert filename.endswith("giraffe_1.png")
        
        # Clean up
        import os
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass