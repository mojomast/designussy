#!/usr/bin/env python3
"""
Test script for the new modular generator system.

This script tests the modular architecture to ensure everything is working correctly.
"""

import sys
from generators import get_generator, list_generators, default_factory
from PIL import Image
import io

def test_generator_listing():
    """Test that we can list all available generators."""
    print("Testing generator listing...")
    generators = list_generators()
    print(f"Available generators: {generators}")
    assert len(generators) > 0, "No generators found"
    assert "parchment" in generators, "parchment generator not found"
    assert "enso" in generators, "enso generator not found"
    print("✅ Generator listing test passed")

def test_generator_creation():
    """Test that we can create generator instances."""
    print("Testing generator creation...")
    generators_to_test = ["parchment", "enso", "sigil", "giraffe", "kangaroo"]
    
    for gen_type in generators_to_test:
        try:
            gen = get_generator(gen_type)
            print(f"Created {gen_type} generator: {gen}")
            assert gen.get_generator_type() == gen_type, f"Generator type mismatch for {gen_type}"
        except Exception as e:
            print(f"❌ Failed to create {gen_type} generator: {e}")
            raise
    
    print("✅ Generator creation test passed")

def test_asset_generation():
    """Test that generators can create assets."""
    print("Testing asset generation...")
    
    # Test parchment generation
    try:
        gen = get_generator("parchment", width=512, height=512)
        img = gen.generate()
        assert isinstance(img, Image.Image), "Generated asset is not a PIL Image"
        assert img.size == (512, 512), f"Wrong image size: {img.size}"
        print(f"✅ Generated parchment: {img.size}")
    except Exception as e:
        print(f"❌ Parchment generation failed: {e}")
        raise
    
    # Test enso generation
    try:
        gen = get_generator("enso", width=400, height=400)
        img = gen.generate()
        assert isinstance(img, Image.Image), "Generated enso is not a PIL Image"
        assert img.size == (400, 400), f"Wrong enso size: {img.size}"
        print(f"✅ Generated enso: {img.size}")
    except Exception as e:
        print(f"❌ Enso generation failed: {e}")
        raise
    
    # Test sigil generation
    try:
        gen = get_generator("sigil", width=300, height=300)
        img = gen.generate()
        assert isinstance(img, Image.Image), "Generated sigil is not a PIL Image"
        assert img.size == (300, 300), f"Wrong sigil size: {img.size}"
        print(f"✅ Generated sigil: {img.size}")
    except Exception as e:
        print(f"❌ Sigil generation failed: {e}")
        raise

def test_factory_functionality():
    """Test the factory system."""
    print("Testing factory functionality...")
    
    # Test getting generator info
    info = default_factory.get_generator_info("parchment")
    print(f"Parchment generator info: {info['type']}")
    assert info['type'] == "parchment", "Generator info type mismatch"
    
    # Test configuration validation
    config = {"width": 1024, "height": 1024, "noise_scale": 2.0}
    validation = default_factory.validate_generator_config("parchment", config)
    print(f"Config validation result: {validation['valid']}")
    assert validation['valid'], f"Config validation failed: {validation['errors']}"
    
    print("✅ Factory functionality test passed")

def test_backward_compatibility():
    """Test that old API endpoints still work."""
    print("Testing backward compatibility...")
    
    try:
        # Import the old functions to ensure they still exist
        from generate_assets import create_void_parchment, create_ink_enso
        
        # Test that they still work (even if they use the legacy system)
        img1 = create_void_parchment(index=None)
        assert isinstance(img1, Image.Image), "Legacy parchment generation failed"
        
        img2 = create_ink_enso(index=None)
        assert isinstance(img2, Image.Image), "Legacy enso generation failed"
        
        print("✅ Backward compatibility test passed")
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        raise

def test_image_serialization():
    """Test that generated images can be serialized."""
    print("Testing image serialization...")
    
    gen = get_generator("enso", width=200, height=200)
    img = gen.generate()
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    # Verify we can read it back
    img2 = Image.open(buf)
    assert img2.size == (200, 200), "Serialized image has wrong size"
    print(f"✅ Image serialization test passed")

def main():
    """Run all tests."""
    print("🧪 Testing Modular Generator Architecture")
    print("=" * 50)
    
    try:
        test_generator_listing()
        test_generator_creation()
        test_asset_generation()
        test_factory_functionality()
        test_backward_compatibility()
        test_image_serialization()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Modular architecture is working correctly.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())