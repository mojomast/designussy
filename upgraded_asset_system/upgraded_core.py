
"""
upgraded_core.py

Core utilities for the upgraded procedural asset system:

- Output directory + categories
- Seeded randomness helpers
- Style themes
- Variation helpers (color/size/count/etc.)
- Asset registry (dynamic plugin-based)
- Simple brush utilities
- High-level generation entrypoint

This is designed so that:
- Existing "create_..." functions from your original generate_assets.py can be
  wrapped and registered.
- New assets can be plugged in via the @register_asset decorator.
"""

import os
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_BASE = "assets/static/elements"

CATEGORIES = {
    "backgrounds": "backgrounds",
    "glyphs": "glyphs",
    "creatures": "creatures",
    "ui": "ui",
}

for cat in CATEGORIES.values():
    os.makedirs(os.path.join(OUTPUT_BASE, cat), exist_ok=True)


# ---------------------------------------------------------------------------
# Seeding & variation helpers
# ---------------------------------------------------------------------------

def seed_from_index(index: Optional[int], asset_name: str) -> None:
    """
    Set random seed based on index and asset name for consistent variation.
    """
    if index is not None:
        seed_value = (index * 1000 + abs(hash(asset_name))) % (2 ** 32)
        random.seed(seed_value)
        np.random.seed(seed_value)


def get_color_variant(
    index: Optional[int],
    base_color: Tuple[int, ...],
    variation_range: int = 30,
    salt: str = "color",
) -> Tuple[int, ...]:
    """
    Get a color variant based on index + salt.
    """
    if index is None:
        return base_color

    seed_from_index(index, salt)
    r = max(0, min(255, base_color[0] + random.randint(-variation_range, variation_range)))
    g = max(0, min(255, base_color[1] + random.randint(-variation_range, variation_range)))
    b = max(0, min(255, base_color[2] + random.randint(-variation_range, variation_range)))
    if len(base_color) == 4:
        a = base_color[3]
        return (r, g, b, a)
    return (r, g, b)


def get_size_variant(
    index: Optional[int],
    base_multiplier: float = 1.0,
    variation_percent: float = 0.3,
    salt: str = "size",
) -> float:
    if index is None:
        return base_multiplier
    seed_from_index(index, salt)
    return base_multiplier * (1.0 + random.uniform(-variation_percent, variation_percent))


def get_rotation_variant(index: Optional[int], salt: str = "rotation") -> float:
    if index is None:
        return 0
    seed_from_index(index, salt)
    return random.uniform(0, 360)


def get_complexity_variant(
    index: Optional[int],
    base_complexity: int,
    variation_percent: float = 0.5,
    salt: str = "complexity",
) -> int:
    if index is None:
        return base_complexity
    seed_from_index(index, salt)
    variation = int(base_complexity * variation_percent)
    return max(1, base_complexity + random.randint(-variation, variation))


def get_count_variant(
    index: Optional[int],
    base_count: int,
    min_count: Optional[int] = None,
    max_count: Optional[int] = None,
    salt: str = "count",
) -> int:
    if index is None:
        return base_count
    seed_from_index(index, salt)
    variation = max(1, base_count // 3)
    result = base_count + random.randint(-variation, variation)
    if min_count is not None:
        result = max(min_count, result)
    if max_count is not None:
        result = min(max_count, result)
    return result


# ---------------------------------------------------------------------------
# Noise / texture helpers
# ---------------------------------------------------------------------------

def create_noise_layer(width: int, height: int, scale: float = 1.0) -> Image.Image:
    noise_data = np.random.normal(128, 50 * scale, (height, width)).astype(np.uint8)
    img = Image.fromarray(noise_data, mode="L")
    return img


# ---------------------------------------------------------------------------
# Style themes
# ---------------------------------------------------------------------------

@dataclass
class StyleTheme:
    name: str
    ink: Tuple[int, int, int] = (20, 20, 25)
    glow: Tuple[int, int, int] = (200, 200, 255)
    parchment: Tuple[int, int, int] = (20, 18, 18)
    accent: Tuple[int, int, int] = (180, 150, 200)
    saturation_boost: float = 1.0
    contrast_boost: float = 1.0


STYLE_THEMES: Dict[str, StyleTheme] = {
    "void_purple": StyleTheme(
        name="void_purple",
        ink=(30, 20, 45),
        glow=(210, 140, 255),
        parchment=(15, 10, 18),
        accent=(180, 120, 220),
        saturation_boost=1.2,
        contrast_boost=1.1,
    ),
    "astral_blue": StyleTheme(
        name="astral_blue",
        ink=(10, 15, 40),
        glow=(160, 200, 255),
        parchment=(10, 12, 20),
        accent=(100, 160, 240),
    ),
    "sepia_ancient": StyleTheme(
        name="sepia_ancient",
        ink=(40, 30, 20),
        glow=(220, 200, 160),
        parchment=(60, 50, 40),
        accent=(190, 150, 90),
        saturation_boost=0.9,
    ),
    "fungal_green": StyleTheme(
        name="fungal_green",
        ink=(10, 25, 15),
        glow=(180, 255, 190),
        parchment=(18, 22, 18),
        accent=(90, 190, 120),
    ),
}


def choose_theme(index: Optional[int], explicit: Optional[str] = None) -> StyleTheme:
    if explicit and explicit in STYLE_THEMES:
        return STYLE_THEMES[explicit]
    if index is None:
        return list(STYLE_THEMES.values())[0]
    seed_from_index(index, "style_theme")
    themes = list(STYLE_THEMES.values())
    return themes[index % len(themes)]


# ---------------------------------------------------------------------------
# Brush utilities
# ---------------------------------------------------------------------------

def draw_bleed_line(draw: ImageDraw.ImageDraw, points, color, base_width: int, jitter: int = 2):
    """
    Slightly wobbly line that feels like bleeding ink.
    """
    if len(points) < 2:
        return
    noisy_points = []
    for (x, y) in points:
        dx = random.randint(-jitter, jitter)
        dy = random.randint(-jitter, jitter)
        noisy_points.append((x + dx, y + dy))
    draw.line(noisy_points, fill=color, width=base_width)


def draw_dry_brush_line(draw: ImageDraw.ImageDraw, points, color, base_width: int):
    """
    Line whose width fluctuates, emulating a drier brush.
    """
    if len(points) < 2:
        return
    for i in range(len(points) - 1):
        w = max(1, base_width + random.randint(-base_width // 2, base_width // 2))
        draw.line([points[i], points[i + 1]], fill=color, width=w)


# ---------------------------------------------------------------------------
# Asset registry
# ---------------------------------------------------------------------------

@dataclass
class AssetInfo:
    name: str
    category: str
    fn: Callable[[Optional[int], Optional[StyleTheme]], Image.Image]
    tags: List[str] = field(default_factory=list)
    from_dsl: bool = False


ASSET_REGISTRY: Dict[str, AssetInfo] = {}


def register_asset(name: str, category: str, tags: Optional[List[str]] = None, from_dsl: bool = False):
    """
    Decorator used by all asset generator functions. Asset functions should have signature:
        fn(index: Optional[int], theme: Optional[StyleTheme] = None) -> PIL.Image
    """
    def wrapper(fn):
        info = AssetInfo(
            name=name,
            category=category,
            fn=fn,
            tags=tags or [],
            from_dsl=from_dsl,
        )
        ASSET_REGISTRY[name] = info
        return fn
    return wrapper


def save_asset(img: Image.Image, category: str, name: str, index: int) -> str:
    """
    Save asset to disk with consistent path.
    """
    filename = os.path.join(OUTPUT_BASE, category, f"{name}_{index}.png")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)
    return filename


def generate_all_assets(
    indices: range,
    categories: Optional[List[str]] = None,
    themes: Optional[List[str]] = None,
    verbose: bool = True,
) -> None:
    """
    High-level generator:
    - iterates over all indices
    - for each registered asset, generates and saves the PNG
    - optional category filter
    - optional theme cycling
    """
    if categories:
        allowed_cats = set(categories)
        assets = [a for a in ASSET_REGISTRY.values() if a.category in allowed_cats]
    else:
        assets = list(ASSET_REGISTRY.values())

    if verbose:
        print(f"[core] Generating {len(assets)} asset types for indices {indices.start}..{indices.stop-1}")

    for idx in indices:
        theme = None
        if themes:
            theme_name = themes[(idx - indices.start) % len(themes)]
            theme = STYLE_THEMES.get(theme_name, choose_theme(idx))
        else:
            theme = choose_theme(idx)

        for info in assets:
            img = info.fn(idx, theme)
            path = save_asset(img, info.category, info.name, idx)
            if verbose:
                print(f"  - {info.name}@{idx} -> {path}")
