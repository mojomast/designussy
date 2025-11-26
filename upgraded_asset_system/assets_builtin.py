
"""
assets_builtin.py

New, hand-authored assets in the same design language as your original generator.
Each asset is registered via @register_asset so the core generator can discover
and render them automatically.

These functions are designed to be mix-and-matchable with your original ones
from generate_assets.py if you choose to wrap those as well.
"""

from typing import Optional
import math
import random

from PIL import Image, ImageDraw, ImageFilter

try:
    from .upgraded_core import (
        StyleTheme,
        register_asset,
        create_noise_layer,
        draw_bleed_line,
        draw_dry_brush_line,
    )
except ImportError:
    from upgraded_core import (
        StyleTheme,
        register_asset,
        create_noise_layer,
        draw_bleed_line,
        draw_dry_brush_line,
    )


# Utility: soft glow compositing
def _add_glow(base: Image.Image, shape_fn, intensity: int = 8):
    w, h = base.size
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    shape_fn(gdraw)
    glow = glow.filter(ImageFilter.GaussianBlur(intensity))
    base.alpha_composite(glow)


# ---------------------------------------------------------------------------
# 20 new assets
# ---------------------------------------------------------------------------

@register_asset("ink_phoenix", "creatures")
def create_ink_phoenix(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 700, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2 + 50

    # Body
    body_height = 160
    d.ellipse(
        (cx - 40, cy - body_height, cx + 40, cy + 40),
        fill=theme.ink + (230,),
    )

    # Head
    d.ellipse(
        (cx - 25, cy - body_height - 40, cx + 25, cy - body_height + 10),
        fill=theme.ink + (240,),
    )

    # Beak
    d.polygon(
        [
            (cx + 25, cy - body_height - 15),
            (cx + 55, cy - body_height - 5),
            (cx + 25, cy - body_height + 5),
        ],
        fill=theme.accent + (255,),
    )

    # Flight feathers (wings)
    for side in (-1, 1):
        points = []
        for i in range(20):
            t = i / 19
            x = cx + side * (40 + t * 220 + math.sin(t * 6) * 20)
            y = cy - 40 - t * 200 + math.sin(t * 10) * 10
            points.append((x, y))
        draw_bleed_line(d, points, theme.ink + (255,), base_width=12)

    # Tail feathers
    for i in range(5):
        angle = math.radians(210 + i * 15)
        pts = []
        for t in range(0, 60):
            r = 40 + t * 5
            x = cx + math.cos(angle) * r + math.sin(t / 5) * 5
            y = cy + math.sin(angle) * r + math.cos(t / 5) * 5
            pts.append((x, y))
        draw_bleed_line(d, pts, theme.accent + (220,), base_width=8)

    # Eyes
    d.ellipse(
        (cx - 10, cy - body_height - 20, cx + 2, cy - body_height - 8),
        fill=theme.glow + (255,),
    )

    # Glowing embers
    for _ in range(80):
        ex = random.randint(cx - 260, cx + 260)
        ey = random.randint(cy - 260, cy + 60)
        r = random.randint(2, 6)
        col = theme.accent + (random.randint(120, 255),)
        d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=col)

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("astral_hourglass", "ui")
def create_astral_hourglass(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 700
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    # Frame
    d.rectangle((cx - 120, 100, cx + 120, 600), outline=theme.ink + (255,), width=4)

    # Top triangle
    d.polygon(
        [(cx - 80, 150), (cx + 80, 150), (cx, cy)],
        outline=theme.ink + (255,),
        width=3,
    )
    # Bottom triangle
    d.polygon(
        [(cx - 80, 550), (cx + 80, 550), (cx, cy)],
        outline=theme.ink + (255,),
        width=3,
    )

    # Sand stream
    for i in range(40):
        y = 270 + i * 6
        jitter = random.randint(-4, 4)
        d.ellipse((cx - 4 + jitter, y, cx + 4 + jitter, y + 4), fill=theme.glow + (200,))

    # Star halo
    for _ in range(50):
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(180, 230)
        x = cx + math.cos(ang) * rad
        y = cy + math.sin(ang) * rad
        r = random.randint(2, 4)
        d.ellipse((x - r, y - r, x + r, y + r), fill=theme.glow + (180,))

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("void_lotus", "glyphs")
def create_void_lotus(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    layers = 4
    petals_per_layer = 10
    base_radius = 40

    for layer in range(layers):
        radius = base_radius + layer * 22
        for i in range(petals_per_layer):
            ang = (2 * math.pi / petals_per_layer) * i + layer * 0.2
            x1 = cx + math.cos(ang) * radius
            y1 = cy + math.sin(ang) * radius
            x2 = cx + math.cos(ang + 0.3) * (radius + 25)
            y2 = cy + math.sin(ang + 0.3) * (radius + 25)
            x3 = cx + math.cos(ang - 0.3) * (radius + 25)
            y3 = cy + math.sin(ang - 0.3) * (radius + 25)

            d.polygon(
                [(x1, y1), (x2, y2), (x3, y3)],
                fill=theme.ink + (220,),
            )

    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=theme.glow + (255,))
    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("ink_compass_rose", "ui")
def create_ink_compass_rose(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    radius = 180
    for angle_deg in range(0, 360, 45):
        ang = math.radians(angle_deg)
        outer = (cx + math.cos(ang) * radius, cy + math.sin(ang) * radius)
        inner = (cx + math.cos(ang) * 60, cy + math.sin(ang) * 60)
        d.line([inner, outer], fill=theme.ink + (255,), width=4)

    for angle_deg in range(0, 360, 90):
        ang = math.radians(angle_deg)
        outer = (cx + math.cos(ang) * (radius + 20), cy + math.sin(ang) * (radius + 20))
        inner = (cx + math.cos(ang) * 80, cy + math.sin(ang) * 80)
        d.line([inner, outer], fill=theme.accent + (255,), width=4)

    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=theme.glow + (255,))
    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("shattered_glyph_tablet", "glyphs")
def create_shattered_glyph_tablet(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = 60
    rect = (margin, margin, w - margin, h - margin)
    d.rounded_rectangle(rect, radius=40, fill=theme.parchment + (255,))

    # Cracks
    cx, cy = w // 2, h // 2
    for _ in range(12):
        points = [(cx, cy)]
        length = random.randint(80, 180)
        ang = random.uniform(0, 2 * math.pi)
        for step in range(1, 10):
            t = step / 10
            r = length * t
            x = cx + math.cos(ang + math.sin(t * 10) * 0.2) * r
            y = cy + math.sin(ang + math.cos(t * 10) * 0.2) * r
            points.append((x, y))
        draw_dry_brush_line(d, points, theme.ink + (255,), base_width=3)

    # Glyph rows
    for row in range(6):
        y = margin + 40 + row * 60
        for _ in range(10):
            gx = random.randint(margin + 20, w - margin - 40)
            gy = y + random.randint(-6, 6)
            r = random.randint(4, 7)
            d.ellipse((gx, gy, gx + r, gy + r), fill=theme.ink + (220,))

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("abyss_leviathan", "creatures")
def create_abyss_leviathan(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 900, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    points = []
    for i in range(80):
        t = i / 79
        x = 100 + t * 700
        y = 300 + math.sin(t * 3 * math.pi) * 120
        y += math.sin(t * 15) * 15
        points.append((x, y))

    draw_bleed_line(d, points, theme.ink + (240,), base_width=26)

    hx, hy = points[-1]
    d.ellipse((hx - 35, hy - 30, hx + 40, hy + 35), fill=theme.ink + (255,))
    d.ellipse((hx + 10, hy - 10, hx + 20, hy), fill=theme.glow + (255,))

    # Back spines
    for i in range(10):
        t = i / 9
        idx = int(t * (len(points) - 20))
        x, y = points[idx]
        length = 40 + t * 30
        d.polygon(
            [(x, y - 10), (x + 10, y - length), (x - 10, y - length)],
            fill=theme.accent + (200,),
        )

    img = img.filter(ImageFilter.GaussianBlur(2))
    return img


@register_asset("runic_obelisk", "glyphs")
def create_runic_obelisk(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 400, 700
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    base = (w // 2 - 60, h - 80, w // 2 + 60, h - 40)
    d.rectangle(base, fill=theme.parchment + (255,))

    pts = [
        (w // 2 - 40, 120),
        (w // 2 + 40, 120),
        (w // 2 + 60, h - 80),
        (w // 2 - 60, h - 80),
    ]
    d.polygon(pts, fill=theme.parchment + (255,))

    # Vertical rune line
    for i in range(12):
        y = 160 + i * 35
        x = w // 2 + random.randint(-8, 8)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=theme.ink + (230,))

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("ink_mandala", "glyphs")
def create_ink_mandala(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 600, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    rings = 8
    for r_i in range(rings):
        radius = 40 + r_i * 30
        count = 8 + r_i * 2
        for i in range(count):
            ang = 2 * math.pi * i / count
            x = cx + math.cos(ang) * radius
            y = cy + math.sin(ang) * radius
            r = 4 + (r_i % 3)
            d.ellipse((x - r, y - r, x + r, y + r), fill=theme.ink + (220,))

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("spectral_lantern", "ui")
def create_spectral_lantern(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 400, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2

    d.line([(cx, 40), (cx, 120)], fill=theme.ink + (255,), width=3)
    d.rectangle((cx - 70, 120, cx + 70, 420), outline=theme.ink + (255,), width=4)

    for _ in range(60):
        x = random.randint(cx - 40, cx + 40)
        y = random.randint(170, 370)
        r = random.randint(4, 12)
        col = theme.glow + (random.randint(140, 255),)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    img = img.filter(ImageFilter.GaussianBlur(3))
    return img


@register_asset("gilded_cog", "ui")
def create_gilded_cog(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    teeth = 14
    outer_r = 180
    inner_r = 130

    for i in range(teeth):
        ang = 2 * math.pi * i / teeth
        mid = 2 * math.pi * (i + 0.5) / teeth
        p1 = (cx + math.cos(ang) * inner_r, cy + math.sin(ang) * inner_r)
        p2 = (cx + math.cos(mid) * outer_r, cy + math.sin(mid) * outer_r)
        p3 = (cx + math.cos(ang + 2 * math.pi / teeth) * inner_r, cy + math.sin(ang + 2 * math.pi / teeth) * inner_r)
        d.polygon([p1, p2, p3], fill=theme.accent + (240,))

    d.ellipse((cx - 60, cy - 60, cx + 60, cy + 60), fill=theme.parchment + (255,))
    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("void_raven", "creatures")
def create_void_raven(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 600, 400
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Perched raven body
    body = (220, 140, 360, 320)
    d.ellipse(body, fill=theme.ink + (255,))

    head = (300, 80, 360, 150)
    d.ellipse(head, fill=theme.ink + (255,))

    # Beak
    d.polygon([(360, 110), (410, 120), (360, 135)], fill=theme.parchment + (255,))

    # Wing silhouette
    pts = []
    for t in range(0, 60):
        x = 260 - t * 4
        y = 220 - math.sin(t / 6) * 60
        pts.append((x, y))
    draw_bleed_line(d, pts, theme.ink + (255,), base_width=14)

    d.ellipse((338, 102, 350, 114), fill=theme.glow + (255,))
    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("ink_octopus", "creatures")
def create_ink_octopus(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 600, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    d.ellipse((cx - 80, cy - 80, cx + 80, cy + 40), fill=theme.ink + (240,))

    for k in range(8):
        angle = math.radians(20 + k * 40)
        pts = []
        for t in range(40):
            r = 20 + t * 8
            x = cx + math.cos(angle + math.sin(t / 3) * 0.2) * r
            y = cy + 40 + math.sin(angle + math.cos(t / 3) * 0.2) * r
            pts.append((x, y))
        draw_dry_brush_line(d, pts, theme.ink + (230,), base_width=10)

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("arcane_mirror", "ui")
def create_arcane_mirror(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 700
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    d.rounded_rectangle((80, 80, w - 80, h - 80), radius=40, outline=theme.ink + (255,), width=4)
    d.rounded_rectangle((100, 120, w - 100, h - 100), radius=30, outline=theme.accent + (200,), width=2)

    for _ in range(40):
        x = random.randint(110, w - 110)
        y = random.randint(130, h - 110)
        r = random.randint(10, 40)
        col = (theme.glow[0], theme.glow[1], theme.glow[2], random.randint(40, 120))
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    img = img.filter(ImageFilter.GaussianBlur(4))
    return img


@register_asset("ethereal_tree", "backgrounds")
def create_ethereal_tree(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 700, 800
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h - 80

    d.rectangle((cx - 30, cy - 180, cx + 30, cy), fill=theme.ink + (240,))

    def branch(x, y, length, angle, depth):
        if depth <= 0 or length < 15:
            if random.random() < 0.6:
                r = random.randint(4, 8)
                col = theme.glow + (random.randint(150, 255),)
                d.ellipse((x - r, y - r, x + r, y + r), fill=col)
            return
        x2 = x + math.cos(angle) * length
        y2 = y - math.sin(angle) * length
        d.line((x, y, x2, y2), fill=theme.ink + (255,), width=max(1, int(length / 10)))
        for delta in (-0.5, 0, 0.5):
            if random.random() < 0.8:
                branch(x2, y2, length * (0.6 + random.random() * 0.2), angle + delta, depth - 1)

    branch(cx, cy - 180, 120, math.pi / 2, 4)
    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("shadow_puppet_mask", "ui")
def create_shadow_puppet_mask(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.ellipse((80, 80, w - 80, h - 80), fill=theme.parchment + (255,))
    # Eyes
    d.ellipse((150, 220, 210, 280), fill=theme.ink + (255,))
    d.ellipse((w - 210, 220, w - 150, 280), fill=theme.ink + (255,))

    # Mouth
    d.arc((150, 320, w - 150, 420), 200, 340, fill=theme.ink + (255,), width=5)

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("astral_portal_gate", "ui")
def create_astral_portal_gate(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 600, 700
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2

    d.rectangle((80, 150, 160, h - 80), fill=theme.ink + (230,))
    d.rectangle((w - 160, 150, w - 80, h - 80), fill=theme.ink + (230,))

    for y in range(200, h - 100, 40):
        r = random.randint(3, 6)
        d.ellipse((90, y, 90 + r, y + r), fill=theme.glow + (210,))
        d.ellipse((w - 90 - r, y, w - 90, y + r), fill=theme.glow + (210,))

    for _ in range(120):
        x = random.randint(180, w - 180)
        y = random.randint(200, h - 120)
        r = random.randint(4, 14)
        col = theme.glow + (random.randint(120, 255),)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    img = img.filter(ImageFilter.GaussianBlur(3))
    return img


@register_asset("ink_wolf", "creatures")
def create_ink_wolf(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 600, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    head = (160, 120, 360, 320)
    d.ellipse(head, fill=theme.ink + (255,))

    # Snout
    d.polygon([(300, 210), (420, 250), (300, 280)], fill=theme.ink + (255,))

    # Ear
    d.polygon([(210, 130), (250, 40), (290, 130)], fill=theme.ink + (255,))
    d.polygon([(310, 130), (350, 40), (390, 130)], fill=theme.ink + (255,))

    d.ellipse((310, 200, 330, 220), fill=theme.glow + (255,))

    # Scars
    for i in range(3):
        x0 = 220 + i * 40
        d.line((x0, 260, x0 + 50, 310), fill=theme.accent + (220,), width=3)

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("void_compass", "ui")
def create_void_compass(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    d.ellipse((cx - 190, cy - 190, cx + 190, cy + 190), outline=theme.ink + (255,), width=4)

    for r in (80, 120, 160):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=theme.accent + (150,), width=2)

    for i in range(8):
        ang = 2 * math.pi * i / 8
        x1 = cx + math.cos(ang) * 40
        y1 = cy + math.sin(ang) * 40
        x2 = cx + math.cos(ang) * 180
        y2 = cy + math.sin(ang) * 180
        d.line((x1, y1, x2, y2), fill=theme.ink + (200,), width=2)

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("ancient_sundial", "ui")
def create_ancient_sundial(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 500, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2 + 40

    d.ellipse((cx - 160, cy - 160, cx + 160, cy + 160), fill=theme.parchment + (255,))

    for ang_deg in range(0, 360, 15):
        ang = math.radians(ang_deg)
        r0 = 40 if ang_deg % 90 else 60
        r1 = 150
        x0 = cx + math.cos(ang) * r0
        y0 = cy + math.sin(ang) * r0
        x1 = cx + math.cos(ang) * r1
        y1 = cy + math.sin(ang) * r1
        d.line((x0, y0, x1, y1), fill=theme.ink + (200,), width=2)

    # Gnomon
    d.polygon([(cx, cy - 10), (cx + 20, cy - 180), (cx - 10, cy - 10)], fill=theme.ink + (255,))

    img = img.filter(ImageFilter.GaussianBlur(1))
    return img


@register_asset("fractured_moon", "backgrounds")
def create_fractured_moon(index: Optional[int] = None, theme: Optional[StyleTheme] = None):
    theme = theme or StyleTheme("tmp")
    w, h = 700, 500
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx, cy = w // 2, h // 2
    d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), fill=theme.glow + (230,))

    for _ in range(8):
        ang = random.uniform(0, 2 * math.pi)
        r0 = random.randint(10, 40)
        x0 = cx + math.cos(ang) * r0
        y0 = cy + math.sin(ang) * r0
        length = random.randint(50, 120)
        x1 = x0 + math.cos(ang) * length
        y1 = y0 + math.sin(ang) * length
        d.line((x0, y0, x1, y1), fill=theme.ink + (220,), width=3)

    img = img.filter(ImageFilter.GaussianBlur(2))
    return img
