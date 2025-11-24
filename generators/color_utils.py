"""
Color Palette Utilities

This module provides comprehensive utilities for color palette processing,
including validation, interpolation, generation, and manipulation.
"""

import colorsys
import random
import math
from typing import List, Tuple, Optional, Union
from .schemas import GenerationParameters


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color string to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')
        
    Returns:
        RGB tuple (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB tuple to hex color string.
    
    Args:
        rgb: RGB tuple (r, g, b)
        
    Returns:
        Hex color string
    """
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def validate_hex_color(color: str) -> bool:
    """
    Validate if a string is a valid hex color.
    
    Args:
        color: Color string to validate
        
    Returns:
        True if valid hex color, False otherwise
    """
    if not isinstance(color, str):
        return False
    
    color = color.lstrip('#')
    
    # Check length and character validity
    return len(color) == 6 and all(c in '0123456789ABCDEFabcdef' for c in color)


def generate_complementary_palette(base_color: Union[str, Tuple[int, int, int]], 
                                 count: int = 5) -> List[str]:
    """
    Generate a complementary color palette based on a base color.
    
    Args:
        base_color: Base color as hex string or RGB tuple
        count: Number of colors to generate (including base)
        
    Returns:
        List of hex color strings
    """
    if isinstance(base_color, str):
        rgb = hex_to_rgb(base_color)
    else:
        rgb = base_color
    
    # Convert to HSV for easier manipulation
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    palette = []
    
    # Generate complementary colors
    for i in range(count):
        # Alternate between complementary hues
        hue_offset = (i % 2) * 0.5
        new_h = (h + hue_offset) % 1.0
        
        # Vary saturation and value for palette diversity
        s_variation = 0.2 * (1 + random.random())
        v_variation = 0.3 * (1 + random.random())
        
        new_s = max(0.0, min(1.0, s * (1 + s_variation * (0.5 - i / count))))
        new_v = max(0.0, min(1.0, v * (1 + v_variation * (0.5 - i / count))))
        
        # Convert back to RGB
        new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        palette.append(rgb_to_hex((int(new_r * 255), int(new_g * 255), int(new_b * 255))))
    
    return palette


def generate_analogous_palette(base_color: Union[str, Tuple[int, int, int]], 
                             count: int = 5, angle_span: float = 0.3) -> List[str]:
    """
    Generate an analogous color palette based on a base color.
    
    Args:
        base_color: Base color as hex string or RGB tuple
        count: Number of colors to generate
        angle_span: Span of hue variation (0.0 to 1.0)
        
    Returns:
        List of hex color strings
    """
    if isinstance(base_color, str):
        rgb = hex_to_rgb(base_color)
    else:
        rgb = base_color
    
    # Convert to HSV
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    palette = []
    
    # Generate analogous colors
    for i in range(count):
        # Spread colors around the base hue
        offset = ((i / (count - 1)) - 0.5) * angle_span
        new_h = (h + offset) % 1.0
        
        # Add slight variations in saturation and value
        s_variation = random.uniform(-0.1, 0.1)
        v_variation = random.uniform(-0.1, 0.1)
        
        new_s = max(0.0, min(1.0, s + s_variation))
        new_v = max(0.0, min(1.0, v + v_variation))
        
        # Convert back to RGB
        new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        palette.append(rgb_to_hex((int(new_r * 255), int(new_g * 255), int(new_b * 255))))
    
    return palette


def generate_monochromatic_palette(base_color: Union[str, Tuple[int, int, int]], 
                                 count: int = 5) -> List[str]:
    """
    Generate a monochromatic color palette based on a base color.
    
    Args:
        base_color: Base color as hex string or RGB tuple
        count: Number of colors to generate
        
    Returns:
        List of hex color strings
    """
    if isinstance(base_color, str):
        rgb = hex_to_rgb(base_color)
    else:
        rgb = base_color
    
    # Convert to HSV
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    palette = []
    
    # Generate variations by adjusting value (brightness) and saturation
    for i in range(count):
        # Distribute colors across the value spectrum
        v_factor = 0.3 + (0.6 * i / (count - 1))
        s_factor = 0.5 + (0.4 * random.random())
        
        new_s = max(0.0, min(1.0, s * s_factor))
        new_v = max(0.0, min(1.0, v * v_factor))
        
        # Convert back to RGB
        new_r, new_g, new_b = colorsys.hsv_to_rgb(h, new_s, new_v)
        palette.append(rgb_to_hex((int(new_r * 255), int(new_g * 255), int(new_b * 255))))
    
    return palette


def generate_triadic_palette(base_color: Union[str, Tuple[int, int, int]]) -> List[str]:
    """
    Generate a triadic color palette based on a base color.
    
    Args:
        base_color: Base color as hex string or RGB tuple
        
    Returns:
        List of 3 hex color strings (120 degrees apart in hue)
    """
    if isinstance(base_color, str):
        rgb = hex_to_rgb(base_color)
    else:
        rgb = base_color
    
    # Convert to HSV
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    palette = []
    
    # Generate three colors 120 degrees apart
    for i in range(3):
        new_h = (h + i * (1.0 / 3.0)) % 1.0
        
        # Slight variations in saturation and value
        s_variation = 0.1 * random.random()
        v_variation = 0.1 * random.random()
        
        new_s = max(0.0, min(1.0, s + s_variation * (1 if i == 0 else -1)))
        new_v = max(0.0, min(1.0, v + v_variation * (1 if i == 1 else -1)))
        
        # Convert back to RGB
        new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        palette.append(rgb_to_hex((int(new_r * 255), int(new_g * 255), int(new_b * 255))))
    
    return palette


def interpolate_colors(colors: List[str], steps: int = 10) -> List[str]:
    """
    Interpolate between colors to create smooth transitions.
    
    Args:
        colors: List of hex color strings
        steps: Number of intermediate colors to generate
        
    Returns:
        List of interpolated hex color strings
    """
    if len(colors) < 2:
        return colors
    
    # Convert all colors to RGB
    rgb_colors = [hex_to_rgb(color) for color in colors]
    
    interpolated = []
    
    for i in range(len(rgb_colors) - 1):
        start_color = rgb_colors[i]
        end_color = rgb_colors[i + 1]
        
        # Add intermediate colors between start and end
        for step in range(steps):
            ratio = step / (steps - 1)
            
            # Linear interpolation
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            
            interpolated.append(rgb_to_hex((r, g, b)))
        
        # Add the end color (except for the last segment)
        if i < len(rgb_colors) - 2:
            interpolated.append(colors[i + 1])
    
    return interpolated


def adjust_contrast(color: Union[str, Tuple[int, int, int]], factor: float) -> str:
    """
    Adjust the contrast of a color.
    
    Args:
        color: Color as hex string or RGB tuple
        factor: Contrast factor (0.0 = grayscale, 1.0 = original, >1.0 = increased contrast)
        
    Returns:
        Hex color string with adjusted contrast
    """
    if isinstance(color, str):
        rgb = hex_to_rgb(color)
    else:
        rgb = color
    
    # Convert to float for calculations
    r, g, b = [x / 255.0 for x in rgb]
    
    # Apply contrast formula
    factor = max(0.0, min(3.0, factor))  # Clamp factor
    
    # Shift away from middle gray (0.5)
    r = 0.5 + (r - 0.5) * factor
    g = 0.5 + (g - 0.5) * factor
    b = 0.5 + (b - 0.5) * factor
    
    # Clamp to valid range
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    
    return rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))


def adjust_brightness(color: Union[str, Tuple[int, int, int]], factor: float) -> str:
    """
    Adjust the brightness of a color.
    
    Args:
        color: Color as hex string or RGB tuple
        factor: Brightness factor (0.0 = black, 1.0 = original, >1.0 = brighter)
        
    Returns:
        Hex color string with adjusted brightness
    """
    if isinstance(color, str):
        rgb = hex_to_rgb(color)
    else:
        rgb = color
    
    # Apply brightness adjustment
    factor = max(0.0, min(3.0, factor))  # Clamp factor
    
    r = int(rgb[0] * factor)
    g = int(rgb[1] * factor)
    b = int(rgb[2] * factor)
    
    # Clamp to valid range
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    return rgb_to_hex((r, g, b))


def adjust_saturation(color: Union[str, Tuple[int, int, int]], factor: float) -> str:
    """
    Adjust the saturation of a color.
    
    Args:
        color: Color as hex string or RGB tuple
        factor: Saturation factor (0.0 = grayscale, 1.0 = original, >1.0 = more saturated)
        
    Returns:
        Hex color string with adjusted saturation
    """
    if isinstance(color, str):
        rgb = hex_to_rgb(color)
    else:
        rgb = color
    
    # Convert to HSV for saturation adjustment
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Apply saturation adjustment
    factor = max(0.0, min(3.0, factor))  # Clamp factor
    s = max(0.0, min(1.0, s * factor))
    
    # Convert back to RGB
    new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, v)
    
    return rgb_to_hex((int(new_r * 255), int(new_g * 255), int(new_b * 255)))


def generate_color_from_palette_selection(palette: List[str], selection: float = 0.5) -> str:
    """
    Select a color from a palette using a selection factor.
    
    Args:
        palette: List of hex color strings
        selection: Selection factor (0.0 to 1.0)
        
    Returns:
        Selected hex color string
    """
    if not palette:
        raise ValueError("Palette cannot be empty")
    
    selection = max(0.0, min(1.0, selection))
    
    # Interpolate between palette colors
    if len(palette) == 1:
        return palette[0]
    
    # Map selection to palette indices
    index = selection * (len(palette) - 1)
    lower_idx = int(index)
    upper_idx = min(lower_idx + 1, len(palette) - 1)
    
    # Interpolate between the two closest colors
    factor = index - lower_idx
    
    lower_rgb = hex_to_rgb(palette[lower_idx])
    upper_rgb = hex_to_rgb(palette[upper_idx])
    
    r = int(lower_rgb[0] + (upper_rgb[0] - lower_rgb[0]) * factor)
    g = int(lower_rgb[1] + (upper_rgb[1] - lower_rgb[1]) * factor)
    b = int(lower_rgb[2] + (upper_rgb[2] - lower_rgb[2]) * factor)
    
    return rgb_to_hex((r, g, b))


def apply_palette_to_parameters(parameters: GenerationParameters) -> List[str]:
    """
    Apply color palette generation based on advanced parameters.
    
    Args:
        parameters: GenerationParameters object
        
    Returns:
        Generated color palette as list of hex strings
    """
    palette = []
    
    # If custom palette is provided, use it
    if parameters.color_palette:
        return parameters.color_palette
    
    # If base color is provided, generate palette around it
    if parameters.base_color:
        base = parameters.base_color
    else:
        # Use default void black theme
        base = "#0a0a0a"
    
    # Generate palette based on style preset
    if parameters.style_preset == "minimal":
        palette = generate_monochromatic_palette(base, count=3)
    elif parameters.style_preset == "detailed":
        palette = generate_complementary_palette(base, count=5)
    elif parameters.style_preset == "chaotic":
        palette = generate_triadic_palette(base)
        palette.extend(generate_analogous_palette(base, count=3, angle_span=0.5))
    elif parameters.style_preset == "ordered":
        palette = generate_monochromatic_palette(base, count=4)
    else:
        # Default generation based on complexity
        count = 3 + int(parameters.complexity * 4)
        palette = generate_analogous_palette(base, count=count)
    
    # Apply color adjustments to the entire palette
    if parameters.contrast != 1.0:
        palette = [adjust_contrast(color, parameters.contrast) for color in palette]
    
    if parameters.brightness != 1.0:
        palette = [adjust_brightness(color, parameters.brightness) for color in palette]
    
    if parameters.saturation != 1.0:
        palette = [adjust_saturation(color, parameters.saturation) for color in palette]
    
    return palette


class ColorPaletteManager:
    """
    Manager class for handling color palette operations.
    """
    
    def __init__(self):
        self.saved_palettes = {}
    
    def save_palette(self, name: str, colors: List[str]):
        """
        Save a color palette for future use.
        
        Args:
            name: Name for the palette
            colors: List of hex color strings
        """
        self.saved_palettes[name] = colors.copy()
    
    def load_palette(self, name: str) -> List[str]:
        """
        Load a saved color palette.
        
        Args:
            name: Name of the saved palette
            
        Returns:
            List of hex color strings
        """
        if name not in self.saved_palettes:
            raise ValueError(f"Palette '{name}' not found")
        
        return self.saved_palettes[name].copy()
    
    def list_saved_palettes(self) -> List[str]:
        """
        Get list of saved palette names.
        
        Returns:
            List of palette names
        """
        return list(self.saved_palettes.keys())
    
    def generate_preset_palettes(self):
        """Generate and save common preset palettes."""
        # Void Black theme
        self.save_palette("void_black", ["#0a0a0a", "#1a1a1a", "#2a2a2a", "#3a3a3a"])
        
        # Eldritch theme
        self.save_palette("eldritch", ["#2d1b69", "#1a0f4c", "#4a2d82", "#6b3fa0"])
        
        # Ink theme
        self.save_palette("ink", ["#000000", "#2c2c2c", "#1a1a1a", "#404040"])
        
        # Parchment theme
        self.save_palette("parchment", ["#d4c5b0", "#c4b5a0", "#b4a590", "#a49580"])
        
        # Blood theme
        self.save_palette("blood", ["#8b0000", "#a52a2a", "#cd5c5c", "#dc143c"])
        
        # Sacred geometry theme
        self.save_palette("sacred", ["#ffd700", "#ffed4e", "#ffbf00", "#e6ac00"])