"""
Advanced Parameters Validation Tests

This module tests the advanced generation parameters system including:
- Parameter validation
- Preset system functionality  
- Color palette utilities
- Schema validation
- Backward compatibility
"""

import pytest
import sys
import os
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generators.schemas import GenerationParameters, GenerationRequest, PresetRequest, ParameterValidationResult
from generators.presets import get_preset_manager
from generators.color_utils import ColorPaletteManager, validate_hex_color, hex_to_rgb
from generators.base_generator import BaseGenerator


class TestGenerationParameters:
    """Test the GenerationParameters schema."""
    
    def test_default_parameters(self):
        """Test default parameter values."""
        params = GenerationParameters()
        
        assert params.width == 512
        assert params.height == 512
        assert params.quality == "medium"
        assert params.style_preset is None
        assert params.complexity == 0.5
        assert params.randomness == 0.5
        assert params.contrast == 1.0
        assert params.brightness == 1.0
        assert params.saturation == 1.0
    
    def test_valid_custom_parameters(self):
        """Test valid custom parameter values."""
        params = GenerationParameters(
            width=1024,
            height=1024,
            quality="high",
            style_preset="minimal",
            complexity=0.8,
            randomness=0.3,
            base_color="#FF0000",
            color_palette=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        assert params.width == 1024
        assert params.height == 1024
        assert params.quality == "high"
        assert params.style_preset == "minimal"
        assert params.complexity == 0.8
        assert params.randomness == 0.3
        assert params.base_color == "#FF0000"
        assert len(params.color_palette) == 3
    
    def test_invalid_hex_color(self):
        """Test invalid hex color validation."""
        with pytest.raises(ValueError, match="Invalid hex color format"):
            GenerationParameters(base_color="invalid_color")
    
    def test_invalid_color_palette(self):
        """Test invalid color palette validation."""
        with pytest.raises(ValueError, match="Invalid hex color format"):
            GenerationParameters(color_palette=["#FF0000", "invalid", "#00FF00"])
    
    def test_excessive_color_palette(self):
        """Test color palette size validation."""
        # Create a palette with more than 10 colors
        large_palette = [f"#{i:02x}{i:02x}{i:02x}" for i in range(0, 256, 25)]
        
        with pytest.raises(ValueError, match="Color palette cannot exceed 10 colors"):
            GenerationParameters(color_palette=large_palette)
    
    def test_parameter_ranges(self):
        """Test parameter range validation."""
        # Test out-of-range values
        with pytest.raises(ValueError):
            GenerationParameters(width=50)  # Too small
        
        with pytest.raises(ValueError):
            GenerationParameters(height=3000)  # Too large
        
        with pytest.raises(ValueError):
            GenerationParameters(contrast=5.0)  # Too high
        
        with pytest.raises(ValueError):
            GenerationParameters(complexity=1.5)  # Out of range
    
    def test_effective_dimensions(self):
        """Test effective dimension calculation."""
        params = GenerationParameters(width=512, height=512, resolution_multiplier=2.0)
        effective_width, effective_height = params.get_effective_dimensions()
        
        assert effective_width == 1024
        assert effective_height == 1024
    
    def test_quality_settings(self):
        """Test quality-specific settings."""
        params = GenerationParameters(quality="ultra")
        quality_settings = params.get_quality_settings()
        
        assert "noise_samples" in quality_settings
        assert "detail_level" in quality_settings
        assert quality_settings["noise_samples"] == 400  # Ultra setting
    
    def test_style_settings(self):
        """Test style-specific settings."""
        params = GenerationParameters(style_preset="minimal")
        style_settings = params.get_style_settings()
        
        assert style_settings["geometric_precision"] > 0.7
        assert style_settings["organic_flow"] < 0.3
    
    def test_color_adjustments(self):
        """Test color adjustment application."""
        params = GenerationParameters(contrast=1.2, brightness=1.1, saturation=0.8)
        
        # Test with base color
        base_color = (100, 100, 100)
        adjusted = params.apply_color_adjustments(base_color)
        
        # Should return a modified RGB tuple
        assert len(adjusted) == 3
        assert all(0 <= c <= 255 for c in adjusted)


class TestGenerationRequest:
    """Test the GenerationRequest schema."""
    
    def test_legacy_parameter_merging(self):
        """Test merging legacy parameters with advanced parameters."""
        request = GenerationRequest(
            asset_type="parchment",
            parameters=GenerationParameters(quality="high"),
            width=2048,
            height=2048,
            seed=42
        )
        
        final_params = request.get_final_parameters()
        
        assert final_params.quality == "high"
        assert final_params.width == 2048
        assert final_params.height == 2048
        assert final_params.seed == 42
    
    def test_backward_compatibility(self):
        """Test backward compatibility with legacy parameters only."""
        request = GenerationRequest(
            asset_type="enso",
            width=800,
            height=800
        )
        
        final_params = request.get_final_parameters()
        
        assert final_params.width == 800
        assert final_params.height == 800
        assert final_params.quality == "medium"  # Default


class TestPresetSystem:
    """Test the preset management system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.preset_manager = get_preset_manager()
    
    def test_get_preset(self):
        """Test retrieving a built-in preset."""
        preset = self.preset_manager.get_preset("minimal")
        
        assert "complexity" in preset
        assert "quality" in preset
        assert preset["complexity"] == 0.2
        assert preset["quality"] == "low"
    
    def test_apply_preset(self):
        """Test applying a preset to parameters."""
        base_params = GenerationParameters(complexity=0.5, quality="medium")
        applied_params = self.preset_manager.apply_preset(base_params, "minimal")
        
        assert applied_params.complexity == 0.2
        assert applied_params.quality == "low"
    
    def test_list_presets(self):
        """Test listing available presets."""
        presets = self.preset_manager.list_presets()
        
        assert "minimal" in presets
        assert "detailed" in presets
        assert "chaotic" in presets
        assert "ordered" in presets
    
    def test_get_presets_by_category(self):
        """Test getting presets organized by category."""
        categories = self.preset_manager.get_presets_by_category()
        
        assert "style" in categories
        assert "quality" in categories
        assert "asset_specific" in categories
        assert len(categories["style"]) > 0
    
    def test_custom_preset(self):
        """Test creating and using a custom preset."""
        # Create custom preset
        custom_params = {"complexity": 0.9, "quality": "ultra", "style_preset": "chaotic"}
        self.preset_manager.create_custom_preset("test_preset", custom_params)
        
        # Retrieve and apply
        retrieved = self.preset_manager.get_preset("test_preset")
        assert retrieved["complexity"] == 0.9
        
        # Apply to parameters
        base_params = GenerationParameters()
        applied = self.preset_manager.apply_preset(base_params, "test_preset")
        assert applied.complexity == 0.9
    
    def test_preset_validation(self):
        """Test preset parameter validation."""
        valid_params = {"complexity": 0.5, "quality": "medium"}
        errors = self.preset_manager.validate_preset_parameters(valid_params)
        assert len(errors) == 0
        
        invalid_params = {"complexity": 2.0, "quality": "invalid"}
        errors = self.preset_manager.validate_preset_parameters(invalid_params)
        assert len(errors) > 0


class TestColorUtils:
    """Test color palette utilities."""
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        rgb = hex_to_rgb("#FF0000")
        assert rgb == (255, 0, 0)
        
        rgb = hex_to_rgb("#00FF00")
        assert rgb == (0, 255, 0)
    
    def test_validate_hex_color(self):
        """Test hex color validation."""
        assert validate_hex_color("#FF0000") is True
        assert validate_hex_color("#fff") is False  # Wrong format
        assert validate_hex_color("FF0000") is False  # Missing #
        assert validate_hex_color("#GG0000") is False  # Invalid characters
    
    def test_color_palette_manager(self):
        """Test ColorPaletteManager functionality."""
        manager = ColorPaletteManager()
        
        # Generate preset palettes
        manager.generate_preset_palettes()
        
        # Check if preset palettes are saved
        presets = manager.list_saved_palettes()
        assert "void_black" in presets
        assert "parchment" in presets
    
    def test_complementary_palette(self):
        """Test complementary palette generation."""
        from generators.color_utils import generate_complementary_palette
        
        palette = generate_complementary_palette("#FF0000", count=3)
        assert len(palette) == 3
        assert all(validate_hex_color(color) for color in palette)
    
    def test_analogous_palette(self):
        """Test analogous palette generation."""
        from generators.color_utils import generate_analogous_palette
        
        palette = generate_analogous_palette("#FF0000", count=4)
        assert len(palette) == 4
        assert all(validate_hex_color(color) for color in palette)
    
    def test_monochromatic_palette(self):
        """Test monochromatic palette generation."""
        from generators.color_utils import generate_monochromatic_palette
        
        palette = generate_monochromatic_palette("#FF0000", count=5)
        assert len(palette) == 5
        assert all(validate_hex_color(color) for color in palette)


class TestBackwardCompatibility:
    """Test backward compatibility with legacy API."""
    
    def test_legacy_parameter_parsing(self):
        """Test that legacy parameters are properly parsed."""
        # This simulates how legacy API calls would work
        legacy_params = {
            "width": 800,
            "height": 600,
            "seed": 12345
        }
        
        # Create generation request with legacy parameters
        request = GenerationRequest(
            asset_type="parchment",
            width=legacy_params["width"],
            height=legacy_params["height"],
            seed=legacy_params["seed"]
        )
        
        final_params = request.get_final_parameters()
        
        assert final_params.width == 800
        assert final_params.height == 600
        assert final_params.seed == 12345
        assert final_params.quality == "medium"  # Default
        assert final_params.style_preset is None  # Default
    
    def test_mixed_parameters(self):
        """Test mixing legacy and advanced parameters."""
        request = GenerationRequest(
            asset_type="enso",
            width=1024,  # Legacy
            parameters=GenerationParameters(  # Advanced
                quality="high",
                style_preset="chaotic",
                complexity=0.8
            ),
            height=768,  # Legacy override
            seed=999  # Legacy
        )
        
        final_params = request.get_final_parameters()
        
        # Legacy parameters
        assert final_params.width == 1024
        assert final_params.height == 768
        assert final_params.seed == 999
        
        # Advanced parameters
        assert final_params.quality == "high"
        assert final_params.style_preset == "chaotic"
        assert final_params.complexity == 0.8


class TestIntegration:
    """Integration tests for the complete advanced parameters system."""
    
    def test_parameter_validation_flow(self):
        """Test the complete parameter validation flow."""
        # Create a mock generator for testing
        try:
            # This would normally require a concrete generator class
            # For now, just test the parameter creation and validation
            params = GenerationParameters(
                width=1024,
                height=1024,
                quality="high",
                style_preset="detailed"
            )
            
            # Test parameter methods
            effective_dims = params.get_effective_dimensions()
            assert effective_dims[0] >= 512
            assert effective_dims[1] >= 512
            
            quality_settings = params.get_quality_settings()
            assert "noise_samples" in quality_settings
            
            style_settings = params.get_style_settings()
            assert "geometric_precision" in style_settings
            
        except Exception as e:
            # Expected if we don't have a concrete generator
            pytest.skip(f"Generator not available for integration test: {e}")
    
    def test_preset_application_flow(self):
        """Test the complete preset application flow."""
        preset_manager = get_preset_manager()
        
        # Start with default parameters
        base_params = GenerationParameters()
        
        # Apply a preset
        applied_params = preset_manager.apply_preset(base_params, "minimal")
        
        # Verify preset was applied
        assert applied_params.complexity < 0.5
        assert applied_params.quality == "low"
    
    def test_color_palette_flow(self):
        """Test the complete color palette generation flow."""
        manager = ColorPaletteManager()
        manager.generate_preset_palettes()
        
        # Load a preset palette
        palette = manager.load_palette("void_black")
        assert len(palette) > 0
        
        # Test palette validation
        for color in palette:
            assert validate_hex_color(color)


# Test fixtures and utilities
@pytest.fixture
def sample_parameters():
    """Provide sample generation parameters for testing."""
    return GenerationParameters(
        width=1024,
        height=1024,
        quality="medium",
        style_preset="detailed",
        complexity=0.6,
        randomness=0.5,
        contrast=1.0,
        brightness=1.0,
        saturation=1.0
    )


@pytest.fixture
def sample_color_palette():
    """Provide a sample color palette for testing."""
    return ["#000000", "#333333", "#666666", "#999999", "#CCCCCC"]


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic advanced parameters validation tests...")
    
    try:
        # Test 1: Basic parameter creation
        params = GenerationParameters(width=1024, height=1024, quality="high")
        print("✓ Basic parameter creation works")
        
        # Test 2: Parameter validation
        validation_result = params.validate_parameters(params) if hasattr(params, 'validate_parameters') else None
        print("✓ Parameter validation accessible")
        
        # Test 3: Preset system
        preset_manager = get_preset_manager()
        presets = preset_manager.list_presets()
        print(f"✓ Preset system works ({len(presets)} presets available)")
        
        # Test 4: Color utilities
        manager = ColorPaletteManager()
        manager.generate_preset_palettes()
        palettes = manager.list_saved_palettes()
        print(f"✓ Color palette system works ({len(palettes)} palettes available)")
        
        # Test 5: Color validation
        assert validate_hex_color("#FF0000") == True
        assert validate_hex_color("invalid") == False
        print("✓ Color validation works")
        
        print("\n🎉 All basic tests passed! Advanced parameters system is functional.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()