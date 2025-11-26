
"""
asset_dsl.py

Lightweight DSL for describing new assets in JSON so an LLM (or user) can define
new types without writing Python.

The DSL is intentionally simple: it covers a small set of drawing primitives that
match your aesthetic (ink strokes, glows, splatters, rings, etc.)

A spec looks like:

{
  "name": "phoenix_sigils",
  "category": "creatures",
  "width": 600,
  "height": 600,
  "layers": [
    {
      "type": "background_noise",
      "parchment": true,
      "intensity": 1.2
    },
    {
      "type": "ring",
      "radius": 200,
      "thickness": 4,
      "glow": true
    },
    {
      "type": "splatter",
      "count": 40,
      "max_radius": 12
    }
  ]
}

You can then call register_spec(spec_dict) to dynamically create an asset type
registered into the asset registry from upgraded_core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from PIL import Image, ImageDraw, ImageFilter
import random
import math

try:
    from .upgraded_core import (
        StyleTheme,
        register_asset,
        create_noise_layer,
        choose_theme,
    )
except ImportError:
    from upgraded_core import (
        StyleTheme,
        register_asset,
        create_noise_layer,
        choose_theme,
    )

# ---------------------------------------------------------------------------
# Spec model
# ---------------------------------------------------------------------------

@dataclass
class LayerSpec:
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssetSpec:
    name: str
    category: str
    width: int = 512
    height: int = 512
    layers: List[LayerSpec] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Rendering primitives for the DSL
# ---------------------------------------------------------------------------

def _render_background_noise(draw, img, theme: StyleTheme, params: Dict[str, Any]):
    try:
        from .upgraded_core import ImageOps  # local import to avoid cycles
    except ImportError:
        from upgraded_core import ImageOps
    intensity = float(params.get("intensity", 1.0))
    parchment_bias = params.get("parchment", True)
    w, h = img.size
    noise = create_noise_layer(w, h, scale=1.0 * intensity)
    dark = theme.parchment if parchment_bias else (10, 10, 15)
    light = tuple(min(255, c + 40) for c in theme.parchment)
    colored = ImageOps.colorize(noise, dark, light)
    img.paste(colored, (0, 0), colored.convert("L"))


def _render_ring(draw, img, theme: StyleTheme, params: Dict[str, Any]):
    w, h = img.size
    cx, cy = w // 2, h // 2
    radius = int(params.get("radius", min(w, h) // 3))
    thickness = int(params.get("thickness", 4))
    glow = bool(params.get("glow", False))

    bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.ellipse(bbox, outline=theme.ink + (255,), width=thickness)

    if glow:
        glow_radius = radius + 10
        glow_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow_img)
        gbbox = (cx - glow_radius, cy - glow_radius, cx + glow_radius, cy + glow_radius)
        gdraw.ellipse(gbbox, outline=theme.glow + (120,), width=2)
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(8))
        img.alpha_composite(glow_img)


def _render_splatter(draw, img, theme: StyleTheme, params: Dict[str, Any]):
    count = int(params.get("count", 40))
    max_radius = int(params.get("max_radius", 8))
    area = params.get("area", "full")
    w, h = img.size

    for _ in range(count):
        if area == "center":
            x = random.randint(w // 4, 3 * w // 4)
            y = random.randint(h // 4, 3 * h // 4)
        else:
            x = random.randint(0, w)
            y = random.randint(0, h)
        r = random.randint(1, max_radius)
        color = theme.ink + (200,)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _render_spiral(draw, img, theme: StyleTheme, params: Dict[str, Any]):
    turns = float(params.get("turns", 3.0))
    thickness = int(params.get("thickness", 4))
    spacing = float(params.get("spacing", 6.0))
    w, h = img.size
    cx, cy = w // 2, h // 2
    points = []
    for t_deg in range(0, int(360 * turns), 4):
        ang = math.radians(t_deg)
        r = t_deg / spacing
        x = cx + math.cos(ang) * r
        y = cy + math.sin(ang) * r
        points.append((x, y))
    try:
        from .upgraded_core import draw_bleed_line
    except ImportError:
        from upgraded_core import draw_bleed_line
    draw_bleed_line(draw, points, theme.ink + (255,), thickness)


def _render_starfield(draw, img, theme: StyleTheme, params: Dict[str, Any]):
    count = int(params.get("count", 80))
    w, h = img.size
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.randint(1, 3)
        color = theme.glow + (random.randint(120, 255),)
        draw.ellipse((x, y, x + size, y + size), fill=color)


LAYER_RENDERERS = {
    "background_noise": _render_background_noise,
    "ring": _render_ring,
    "splatter": _render_splatter,
    "spiral": _render_spiral,
    "starfield": _render_starfield,
}


# ---------------------------------------------------------------------------
# Spec registration
# ---------------------------------------------------------------------------

def render_spec(spec: AssetSpec, index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    try:
        from .upgraded_core import choose_theme as _choose_theme
    except ImportError:
        from upgraded_core import choose_theme as _choose_theme
    if theme is None:
        theme = _choose_theme(index)

    img = Image.new("RGBA", (spec.width, spec.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for layer in spec.layers:
        renderer = LAYER_RENDERERS.get(layer.type)
        if renderer is None:
            continue
        renderer(draw, img, theme, layer.params)

    return img


def _coerce_spec(d: Dict[str, Any]) -> AssetSpec:
    layers = [LayerSpec(type=ld["type"], params=ld.get("params", {})) for ld in d.get("layers", [])]
    return AssetSpec(
        name=d["name"],
        category=d.get("category", "glyphs"),
        width=int(d.get("width", 512)),
        height=int(d.get("height", 512)),
        layers=layers,
    )


def register_spec(d: Dict[str, Any]):
    """
    Register a new asset type from a raw dict (e.g. loaded from JSON).
    Returns the created AssetSpec.
    """
    spec = _coerce_spec(d)

    @register_asset(spec.name, spec.category, from_dsl=True)
    def _asset_fn(index=None, theme: Optional[StyleTheme] = None):
        return render_spec(spec, index=index, theme=theme)

    return spec
