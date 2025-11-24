"""
Unit tests for KangarooGenerator class.

Tests the kangaroo creature generation including body shapes,
pogo stick functionality, and styling.
"""

import pytest
import numpy as np
from PIL import Image

from generators.kangaroo_generator import KangarooGenerator
from tests.conftest import assert_images_similar, assert_image_has_content


class TestKangarooGenerator:
    """Test suite for KangarooGenerator functionality."""
    
    def test_generator_type(self):
        """Test that generator type is correctly identified."""
        generator = KangarooGenerator()
        assert generator.get_generator_type() == "kangaroo"
    
    def test_default_parameters(self):
        """Test default parameter values."""
        generator = KangarooGenerator()
        params = generator.get_default_params()
        
        assert 'width' in params
        assert 'height' in params
        assert 'bounciness' in params
        assert 'has_pogo_stick' in params
        assert 'seed' in params
        assert params['width'] == 600
        assert params['height'] == 800
    
    def test_generate_basic_kangaroo(self):
        """Test basic kangaroo generation."""
        generator = KangarooGenerator(width=256, height=256)
        img = generator.generate()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert img.mode in ["RGBA", "RGB"]
        assert_image_has_content(img, min_pixels=10)
    
    def test_generate_super_bouncy_kangaroo(self):
        """Test super bouncy kangaroo generation."""
        generator = KangarooGenerator(width=256, height=256)
        img = generator.generate_super_bouncy_kangaroo()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert_image_has_content(img, min_pixels=5)
    
    def test_save_with_index(self):
        """Test saving kangaroo with index."""
        generator = KangarooGenerator(output_dir="/tmp")
        filename = generator.save_with_index(1)
        
        assert filename.endswith("kangaroo_1.png")
        
        # Clean up
        import os
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass