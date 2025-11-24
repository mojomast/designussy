"""
Unit tests for BaseGenerator class.

Tests the abstract base class functionality that all generators inherit.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch
import numpy as np
from PIL import Image

from generators.base_generator import BaseGenerator
from tests.conftest import assert_images_similar, get_memory_usage


class ConcreteTestGenerator(BaseGenerator):
    """Concrete test implementation of BaseGenerator for testing."""
    
    def generate(self, **kwargs) -> Image.Image:
        """Generate a simple test image."""
        img = Image.new("RGBA", (self.width, self.height), (255, 0, 0, 255))
        # Add some noise to make it more realistic
        img = self.create_noise_layer(opacity=50)
        return img
    
    def get_generator_type(self) -> str:
        """Return test generator type."""
        return "test"


class TestBaseGenerator:
    """Test suite for BaseGenerator base functionality."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        generator = ConcreteTestGenerator()
        
        assert generator.width == 1024
        assert generator.height == 1024
        assert generator.seed is None
        assert generator.base_color == (15, 15, 18)
        assert generator.output_dir == "assets/elements"
        assert "backgrounds" in generator.category_map.values()
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        generator = ConcreteTestGenerator(
            width=512,
            height=768,
            seed=42,
            base_color=(100, 150, 200),
            output_dir="/custom/output"
        )
        
        assert generator.width == 512
        assert generator.height == 768
        assert generator.seed == 42
        assert generator.base_color == (100, 150, 200)
        assert generator.output_dir == "/custom/output"
    
    def test_init_invalid_dimensions(self):
        """Test that invalid dimensions raise ValueError."""
        with pytest.raises(ValueError, match="Invalid dimensions"):
            ConcreteTestGenerator(width=-100, height=200)
        
        with pytest.raises(ValueError, match="Invalid dimensions"):
            ConcreteTestGenerator(width=100, height=0)
    
    def test_init_invalid_base_color(self):
        """Test that invalid base color raises ValueError."""
        with pytest.raises(ValueError, match="Invalid base color"):
            ConcreteTestGenerator(base_color=(0, 150, 200))
        
        with pytest.raises(ValueError, match="Invalid base color"):
            ConcreteTestGenerator(base_color=(100, 150, 256))
    
    def test_seed_consistency(self):
        """Test that same seed produces same results."""
        generator1 = ConcreteTestGenerator(seed=42)
        generator2 = ConcreteTestGenerator(seed=42)
        
        # Generate images
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Convert to numpy arrays for comparison
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Images should be identical
        assert np.array_equal(arr1, arr2)
    
    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        generator1 = ConcreteTestGenerator(seed=42)
        generator2 = ConcreteTestGenerator(seed=43)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Images should be different
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        assert not np.array_equal(arr1, arr2)
    
    def test_create_noise_layer(self):
        """Test noise layer creation."""
        generator = ConcreteTestGenerator(width=64, height=64)
        noise = generator.create_noise_layer(scale=1.0, opacity=128)
        
        assert isinstance(noise, Image.Image)
        assert noise.size == (64, 64)
        assert noise.mode in ["L", "RGBA"]  # Depends on opacity
    
    def test_create_noise_layer_caching(self):
        """Test noise layer caching behavior."""
        generator = ConcreteTestGenerator(width=64, height=64)
        
        # First call should generate noise
        noise1 = generator.create_noise_layer(scale=1.0)
        
        # Second call should use cached version
        noise2 = generator.create_noise_layer(scale=1.0)
        
        # Should be identical due to caching
        assert_images_similar(noise1, noise2, tolerance=0.01)
    
    def test_apply_vignette(self):
        """Test vignette effect application."""
        generator = ConcreteTestGenerator(width=100, height=100)
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        
        vignetted = generator.apply_vignette(img, intensity=0.5)
        
        assert isinstance(vignetted, Image.Image)
        assert vignetted.size == (100, 100)
    
    def test_apply_ink_blur(self):
        """Test ink blur effect."""
        generator = ConcreteTestGenerator(width=100, height=100)
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        
        blurred = generator.apply_ink_blur(img, radius=1.0)
        
        assert isinstance(blurred, Image.Image)
        assert blurred.size == (100, 100)
    
    def test_apply_glow(self):
        """Test glow effect application."""
        generator = ConcreteTestGenerator(width=100, height=100)
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        
        glow_color = (0, 255, 0, 128)  # Green glow
        glowing = generator.apply_glow(img, glow_color, blur_radius=2)
        
        assert isinstance(glowing, Image.Image)
        assert glowing.size == (100, 100)
        assert glowing.mode == "RGBA"
    
    def test_add_scratch_texture(self):
        """Test scratch texture addition."""
        generator = ConcreteTestGenerator(width=100, height=100)
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        
        scratched = generator.add_scratch_texture(img, scale=1.0)
        
        assert isinstance(scratched, Image.Image)
        assert scratched.size == (100, 100)
    
    def test_validate_output_size(self):
        """Test output size validation."""
        generator = ConcreteTestGenerator(width=100, height=100)
        
        # Correct size
        correct_img = Image.new("RGB", (100, 100), (128, 128, 128))
        validated = generator.validate_output_size(correct_img)
        assert validated.size == (100, 100)
        
        # Incorrect size - should be resized
        wrong_img = Image.new("RGB", (50, 50), (128, 128, 128))
        validated = generator.validate_output_size(wrong_img)
        assert validated.size == (100, 100)
    
    def test_get_config_summary(self):
        """Test configuration summary generation."""
        generator = ConcreteTestGenerator(
            width=512,
            height=768,
            seed=42,
            base_color=(100, 150, 200),
            custom_param="test_value"
        )
        
        summary = generator.get_config_summary()
        
        assert summary['generator_type'] == "test"
        assert summary['dimensions'] == (512, 768)
        assert summary['seed'] == 42
        assert summary['base_color'] == (100, 150, 200)
        assert summary['custom_config']['custom_param'] == "test_value"
    
    def test_get_default_params(self):
        """Test default parameters retrieval."""
        generator = ConcreteTestGenerator()
        params = generator.get_default_params()
        
        assert 'width' in params
        assert 'height' in params
        assert 'seed' in params
        assert 'base_color' in params
        assert params['width'] == 1024
        assert params['height'] == 1024
        assert params['seed'] is None
        assert params['base_color'] == (15, 15, 18)
    
    def test_performance_tracking(self):
        """Test performance tracking functionality."""
        generator = ConcreteTestGenerator(width=100, height=100)
        
        # Clear any existing data
        generator.clear_performance_cache()
        
        # Track some operations
        generator._track_performance("test_operation", 0.1, 5.0)
        generator._track_performance("test_operation", 0.2, 6.0)
        generator._track_performance("other_operation", 0.15, 4.0)
        
        metrics = generator.get_performance_metrics()
        
        assert 'avg_generation_time' in metrics
        assert 'total_operations' in metrics
        assert 'operations_breakdown' in metrics
        assert metrics['total_operations'] == 3
        assert metrics['operations_breakdown']['test_operation'] == 2
        assert metrics['operations_breakdown']['other_operation'] == 1
    
    def test_performance_tracking_disabled(self):
        """Test behavior when performance tracking is disabled."""
        with patch.dict('os.environ', {'PERFORMANCE_MONITORING': 'false'}):
            generator = ConcreteTestGenerator(width=100, height=100)
            generator._track_performance("test", 0.1)
            
            metrics = generator.get_performance_metrics()
            assert metrics == {"monitoring_disabled": True}
    
    def test_clear_performance_cache(self):
        """Test clearing performance cache."""
        generator = ConcreteTestGenerator(width=100, height=100)
        
        # Add some data
        generator._track_performance("test", 0.1)
        
        # Clear cache
        generator.clear_performance_cache()
        
        metrics = generator.get_performance_metrics()
        assert metrics == {"no_data": True}
    
    def test_noise_cache_management(self):
        """Test noise cache size management."""
        generator = ConcreteTestGenerator(width=50, height=50)
        
        # Set small cache size
        generator.performance_config['noise_cache_size'] = 2
        
        # Add noise with different parameters
        generator.create_noise_layer(scale=1.0)
        generator.create_noise_layer(scale=2.0)
        generator.create_noise_layer(scale=3.0)
        
        # Should have only 2 items (cache limit)
        assert len(generator._noise_cache) <= 2
    
    def test_optimized_pil_operations(self):
        """Test optimized PIL operations."""
        generator = ConcreteTestGenerator(width=100, height=100)
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        
        operations = ['blur', 'enhance_contrast', 'slight_brightness']
        result = generator._optimize_pil_operations(img, operations)
        
        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)
    
    def test_preallocated_buffer(self):
        """Test pre-allocated buffer functionality."""
        generator = ConcreteTestGenerator(width=100, height=100)
        
        buffer1 = generator._get_preallocated_buffer((50, 50), 'RGB')
        buffer2 = generator._get_preallocated_buffer((50, 50), 'RGBA')
        
        assert buffer1.size == (50, 50)
        assert buffer1.mode == 'RGB'
        assert buffer2.mode == 'RGBA'
    
    def test_str_representation(self):
        """Test string representations."""
        generator = ConcreteTestGenerator(width=512, height=768)
        
        str_repr = str(generator)
        repr_repr = repr(generator)
        
        assert str_repr == "ConcreteTestGenerator(512x768)"
        assert "ConcreteTestGenerator(" in repr_repr
        assert "width=512" in repr_repr
        assert "height=768" in repr_repr
    
    def test_thread_safety(self):
        """Test thread safety of performance tracking."""
        generator = ConcreteTestGenerator(width=50, height=50)
        
        def track_operation():
            for _ in range(10):
                generator._track_performance("thread_test", 0.01)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=track_operation)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        metrics = generator.get_performance_metrics()
        # Should have 50 operations tracked
        assert metrics['total_operations'] == 50
    
    @pytest.mark.performance
    def test_generation_performance(self):
        """Test that generation meets performance targets."""
        generator = ConcreteTestGenerator(width=256, height=256)
        
        start_time = time.perf_counter()
        img = generator.generate()
        end_time = time.perf_counter()
        
        generation_time = end_time - start_time
        
        # Should generate within 1 second
        assert generation_time < 1.0, f"Generation took {generation_time:.2f}s (too slow)"
        
        # Should produce valid image
        assert isinstance(img, Image.Image)
        assert img.size == (256, 256)
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test memory usage during generation."""
        generator = ConcreteTestGenerator(width=256, height=256)
        
        initial_memory = get_memory_usage()
        
        # Generate multiple images
        for _ in range(10):
            img = generator.generate()
        
        final_memory = get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.1f}MB"
    
    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented."""
        # Creating a class that doesn't implement abstract methods should fail
        class IncompleteGenerator(BaseGenerator):
            pass
        
        with pytest.raises(TypeError):
            IncompleteGenerator()
    
    def test_directory_creation(self):
        """Test that output directories are created."""
        with patch('os.makedirs') as mock_makedirs:
            generator = ConcreteTestGenerator(output_dir="/test/output")
            
            # Should call makedirs for each category directory
            expected_calls = 0
            for category in generator.category_map.values():
                expected_path = f"/test/output/{category}"
                mock_makedirs.assert_any_call(expected_path, exist_ok=True)
                expected_calls += 1
            
            assert mock_makedirs.call_count >= expected_calls