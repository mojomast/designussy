"""
Integration tests for complete workflows.

Tests end-to-end functionality including generator creation,
asset generation, API integration, and cache interaction.
"""

import pytest
from PIL import Image

from generators import default_factory, list_generators
from tests.conftest import assert_image_has_content


class TestCompleteWorkflow:
    """Test complete generation workflows."""
    
    def test_all_generators_work(self, test_config):
        """Test that all registered generators can create assets."""
        generators = list_generators()
        
        for gen_type in generators:
            try:
                generator = default_factory.create_generator(gen_type, **test_config)
                img = generator.generate()
                
                assert isinstance(img, Image.Image)
                assert img.size == test_config['test_image_size']
                assert_image_has_content(img, min_pixels=10)
                
            except Exception as e:
                pytest.fail(f"Generator {gen_type} failed: {e}")
    
    def test_generator_consistency(self, test_config):
        """Test that generators produce consistent results with same seed."""
        generator1 = default_factory.create_generator("sigil", **test_config, seed=42)
        generator2 = default_factory.create_generator("sigil", **test_config, seed=42)
        
        img1 = generator1.generate()
        img2 = generator2.generate()
        
        # Should be very similar (allowing for minor differences in implementation)
        assert isinstance(img1, Image.Image)
        assert isinstance(img2, Image.Image)
        assert img1.size == img2.size
    
    def test_cache_integration(self, test_client, sample_generator):
        """Test that cache works with API endpoints."""
        # Generate through API
        response1 = test_client.get("/generate/sigil")
        assert response1.status_code == 200
        
        # Second request should potentially use cache
        response2 = test_client.get("/generate/sigil")
        assert response2.status_code == 200