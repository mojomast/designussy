"""
Unit tests for SigilGenerator class.

Tests the sigil generation functionality including geometric patterns,
styling, and validation.
"""

import pytest
import numpy as np
from PIL import Image

from generators.sigil_generator import SigilGenerator
from tests.conftest import assert_images_similar, assert_image_has_content


class TestSigilGenerator:
    """Test suite for SigilGenerator functionality."""
    
    def test_generator_type(self):
        """Test that generator type is correctly identified."""
        generator = SigilGenerator()
        assert generator.get_generator_type() == "sigil"
    
    def test_default_parameters(self):
        """Test default parameter values."""
        generator = SigilGenerator()
        params = generator.get_default_params()
        
        assert 'width' in params
        assert 'height' in params
        assert 'complexity' in params
        assert 'seed' in params
        assert params['width'] == 500
        assert params['height'] == 500
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        generator = SigilGenerator()
        
        assert generator.width == 500
        assert generator.height == 500
        assert generator.complexity == 6
        assert generator.chaos_level == 0.3
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        generator = SigilGenerator(
            width=800,
            height=600,
            complexity=8,
            chaos_level=0.5,
            seed=42
        )
        
        assert generator.width == 800
        assert generator.height == 600
        assert generator.complexity == 8
        assert generator.chaos_level == 0.5
        assert generator.seed == 42
    
    def test_generate_basic_sigil(self):
        """Test basic sigil generation."""
        generator = SigilGenerator(width=256, height=256)
        img = generator.generate()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert img.mode in ["RGBA", "RGB"]
        assert_image_has_content(img, min_pixels=20)
    
    def test_generate_with_complexity(self):
        """Test sigil generation with different complexity levels."""
        for complexity in [3, 6, 9, 12]:
            generator = SigilGenerator(width=256, height=256, complexity=complexity)
            img = generator.generate()
            
            assert isinstance(img, Image.Image)
            assert img.size == (256, 256)
            assert_image_has_content(img, min_pixels=10)
    
    def test_generate_with_chaos_levels(self):
        """Test sigil generation with different chaos levels."""
        for chaos_level in [0.0, 0.3, 0.7, 1.0]:
            generator = SigilGenerator(width=256, height=256, chaos_level=chaos_level)
            img = generator.generate()
            
            assert isinstance(img, Image.Image)
            assert img.size == (256, 256)
            assert_image_has_content(img, min_pixels=10)
    
    def test_generate_complex_sigil(self):
        """Test complex sigil generation."""
        generator = SigilGenerator(width=256, height=256)
        img = generator.generate_complex_sigil(point_count=8, add_secondary_layer=True)
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert_image_has_content(img, min_pixels=20)
    
    def test_generate_complex_sigil_different_points(self):
        """Test complex sigil with different point counts."""
        for point_count in [4, 6, 8, 10, 12]:
            generator = SigilGenerator(width=256, height=256)
            img = generator.generate_complex_sigil(point_count=point_count, add_secondary_layer=False)
            
            assert isinstance(img, Image.Image)
            assert img.size == (256, 256)
    
    def test_seed_consistency(self):
        """Test that same seed produces same sigil."""
        generator1 = SigilGenerator(width=256, height=256, seed=42, complexity=6)
        generator2 = SigilGenerator(width=256, height=256, seed=42, complexity=6)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Should be identical
        assert_images_similar(img1, img2, tolerance=0.01)
    
    def test_different_seeds_different_sigil(self):
        """Test that different seeds produce different sigils."""
        generator1 = SigilGenerator(width=256, height=256, seed=42, complexity=6)
        generator2 = SigilGenerator(width=256, height=256, seed=43, complexity=6)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Images should be different
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        assert not np.array_equal(arr1, arr2)
    
    def test_complexity_affects_sigil(self):
        """Test that different complexity levels produce different sigils."""
        generator1 = SigilGenerator(width=256, height=256, seed=42, complexity=3)
        generator2 = SigilGenerator(width=256, height=256, seed=42, complexity=12)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Should be different due to complexity
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        assert not np.array_equal(arr1, arr2)
    
    def test_chaos_affects_sigil(self):
        """Test that different chaos levels affect sigil generation."""
        generator1 = SigilGenerator(width=256, height=256, seed=42, chaos_level=0.0)
        generator2 = SigilGenerator(width=256, height=256, seed=42, chaos_level=1.0)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Should be different due to chaos level
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        assert not np.array_equal(arr1, arr2)
    
    def test_different_sizes(self):
        """Test sigil generation at different sizes."""
        sizes = [(128, 128), (256, 256), (512, 512), (800, 600)]
        
        for width, height in sizes:
            generator = SigilGenerator(width=width, height=height)
            img = generator.generate()
            
            assert img.size == (width, height)
            assert_image_has_content(img, min_pixels=5)
    
    def test_save_with_index(self):
        """Test saving sigil with index."""
        generator = SigilGenerator(output_dir="/tmp")
        filename = generator.save_with_index(1)
        
        assert filename.endswith("sigil_1.png")
        assert "sigil_1.png" in filename
        
        # Clean up
        import os
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
    
    def test_minimal_complexity(self):
        """Test generation with minimal complexity."""
        generator = SigilGenerator(width=256, height=256, complexity=1)
        img = generator.generate()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert_image_has_content(img, min_pixels=1)
    
    def test_maximum_complexity(self):
        """Test generation with maximum complexity."""
        generator = SigilGenerator(width=256, height=256, complexity=20)
        img = generator.generate()
        
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
        assert_image_has_content(img, min_pixels=5)
    
    def test_chaos_level_bounds(self):
        """Test chaos level within bounds."""
        for chaos_level in [-0.1, 1.1]:  # Out of bounds
            generator = SigilGenerator(width=256, height=256, chaos_level=chaos_level)
            # Should handle gracefully or adjust bounds
            img = generator.generate()
            
            assert isinstance(img, Image.Image)
            assert img.size == (256, 256)
    
    @pytest.mark.performance
    def test_generation_performance(self):
        """Test that sigil generation meets performance targets."""
        generator = SigilGenerator(width=512, height=512)
        
        import time
        start_time = time.perf_counter()
        img = generator.generate()
        end_time = time.perf_counter()
        
        generation_time = end_time - start_time
        
        # Should generate within 2 seconds
        assert generation_time < 2.0, f"Generation took {generation_time:.2f}s (too slow)"
    
    @pytest.mark.performance
    def test_complex_sigil_performance(self):
        """Test complex sigil generation performance."""
        generator = SigilGenerator(width=512, height=512)
        
        import time
        start_time = time.perf_counter()
        img = generator.generate_complex_sigil(point_count=10, add_secondary_layer=True)
        end_time = time.perf_counter()
        
        generation_time = end_time - start_time
        
        # Complex sigil should generate within 3 seconds
        assert generation_time < 3.0, f"Complex generation took {generation_time:.2f}s (too slow)"
    
    def test_secondary_layer_option(self):
        """Test add_secondary_layer parameter."""
        generator = SigilGenerator(width=256, height=256, seed=42)
        
        img1 = generator.generate_complex_sigil(point_count=6, add_secondary_layer=False)
        img2 = generator.generate_complex_sigil(point_count=6, add_secondary_layer=True)
        
        # Should produce different images
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        assert not np.array_equal(arr1, arr2)
    
    def test_point_count_affects_complexity(self):
        """Test that point count affects sigil complexity."""
        generator = SigilGenerator(width=256, height=256, seed=42)
        
        img_few_points = generator.generate_complex_sigil(point_count=4, add_secondary_layer=False)
        img_many_points = generator.generate_complex_sigil(point_count=12, add_secondary_layer=False)
        
        # Should produce different images
        arr1 = np.array(img_few_points)
        arr2 = np.array(img_many_points)
        assert not np.array_equal(arr1, arr2)
        
        # Both should have content
        assert_image_has_content(img_few_points, min_pixels=5)
        assert_image_has_content(img_many_points, min_pixels=5)