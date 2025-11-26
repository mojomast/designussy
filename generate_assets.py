import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import random
import math

OUTPUT_BASE = "assets/static/elements"
CATEGORIES = {
    "backgrounds": "backgrounds",
    "glyphs": "glyphs",
    "creatures": "creatures",
    "ui": "ui"
}

for cat in CATEGORIES.values():
    os.makedirs(os.path.join(OUTPUT_BASE, cat), exist_ok=True)

def save_asset(img, category, name, index):
    filename = os.path.join(OUTPUT_BASE, category, f"{name}_{index}.png")
    img.save(filename)
    print(f"Generated {filename}")

def create_noise_layer(width, height, scale=1.0, opacity=128):
    # Generate random noise
    noise_data = np.random.normal(128, 50 * scale, (height, width)).astype(np.uint8)
    img = Image.fromarray(noise_data, mode='L')
    return img

# ===== DIVERSITY HELPER FUNCTIONS =====

def seed_from_index(index, asset_name):
    """Set random seed based on index and asset name for consistent variation"""
    if index is not None:
        # Ensure seed is within valid range (0 to 2^32 - 1)
        seed_value = (index * 1000 + abs(hash(asset_name))) % (2**32)
        random.seed(seed_value)
        np.random.seed(seed_value)

def get_color_variant(index, base_color, variation_range=30):
    """Get a color variant based on index"""
    if index is None:
        return base_color
    
    seed_from_index(index, "color")
    r = max(0, min(255, base_color[0] + random.randint(-variation_range, variation_range)))
    g = max(0, min(255, base_color[1] + random.randint(-variation_range, variation_range)))
    b = max(0, min(255, base_color[2] + random.randint(-variation_range, variation_range)))
    
    if len(base_color) == 4:
        a = base_color[3]
        return (r, g, b, a)
    return (r, g, b)

def get_size_variant(index, base_size, variation_percent=0.3):
    """Get a size multiplier based on index"""
    if index is None:
        return 1.0
    
    seed_from_index(index, "size")
    return 1.0 + random.uniform(-variation_percent, variation_percent)

def get_rotation_variant(index):
    """Get a rotation angle based on index"""
    if index is None:
        return 0
    
    seed_from_index(index, "rotation")
    return random.uniform(0, 360)

def get_complexity_variant(index, base_complexity, variation_percent=0.5):
    """Get a complexity value based on index"""
    if index is None:
        return base_complexity
    
    seed_from_index(index, "complexity")
    variation = int(base_complexity * variation_percent)
    return base_complexity + random.randint(-variation, variation)

def get_count_variant(index, base_count, min_count=None, max_count=None):
    """Get a count variant for elements like particles, segments, etc."""
    if index is None:
        return base_count
    
    seed_from_index(index, "count")
    variation = max(1, base_count // 3)
    result = base_count + random.randint(-variation, variation)
    
    if min_count is not None:
        result = max(min_count, result)
    if max_count is not None:
        result = min(max_count, result)
    
    return result


def create_void_parchment(index=None, base_color=(15, 15, 18), noise_scale=1.5):
    seed_from_index(index, "void_parchment")
    
    # Vary base color darkness
    varied_color = get_color_variant(index, base_color, variation_range=10)
    varied_noise_scale = noise_scale * get_size_variant(index, 1.0, 0.3)
    vignette_intensity = 100 + get_count_variant(index, 50, 20, 100)
    
    width, height = 1024, 1024
    img = Image.new('RGB', (width, height), varied_color)
    
    # Layer 1: Heavy Grain
    noise = create_noise_layer(width, height, scale=varied_noise_scale)
    img.paste(ImageOps.colorize(noise, (0,0,0), (40,40,45)), (0,0), mask=None)
    
    # Layer 2: Scratches
    scratches = create_noise_layer(width, height, scale=varied_noise_scale + 0.5)
    scratches = scratches.resize((width, height // 10))
    scratches = scratches.resize((width, height), Image.BICUBIC)
    img = Image.blend(img, scratches.convert('RGB'), 0.1)
    
    # Vignette with varied intensity
    vignette = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(vignette)
    draw.ellipse((50, 50, width-50, height-50), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(vignette_intensity))
    
    dark_layer = Image.new('RGB', (width, height), (0,0,0))
    img = Image.composite(img, dark_layer, vignette)
    
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "void_parchment", index)
    return img

def create_ink_enso(index=None, color=(0,0,0), complexity=40, chaos=1.0):
    seed_from_index(index, "ink_enso")
    
    # Vary complexity and chaos based on index
    varied_complexity = get_complexity_variant(index, complexity, 0.5)
    varied_chaos = chaos * get_size_variant(index, 1.0, 0.4)
    varied_radius = int(300 * get_size_variant(index, 1.0, 0.2))
    blur_amount = get_count_variant(index, 1, 0, 3)
    
    width, height = 800, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = width // 2, height // 2
    
    for _ in range(varied_complexity):
        points = []
        current_radius = varied_radius + random.randint(int(-30 * varied_chaos), int(30 * varied_chaos))
        thickness = random.randint(2, 15)
        
        start_angle = random.uniform(0, 2 * math.pi)
        end_angle = start_angle + random.uniform(3, 5)
        
        for angle in np.arange(start_angle, end_angle, 0.05):
            r_wobble = current_radius + math.sin(angle * 10) * 5 + random.randint(-2, 2)
            x = center_x + r_wobble * math.cos(angle)
            y = center_y + r_wobble * math.sin(angle)
            points.append((x, y))
            
        if len(points) > 1:
            stroke_color = color + (random.randint(50, 200),) if len(color) == 3 else color
            draw.line(points, fill=stroke_color, width=thickness)
            
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_amount))
    
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "ink_enso", index)
    return img

def create_sigil(index=None):
    width, height = 500, 500
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    color = (212, 197, 176, 255)
    
    if random.random() > 0.3:
        draw.ellipse((50, 50, 450, 450), outline=color, width=3)
    
    points = []
    num_points = random.randint(3, 7)
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        r = 180
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x,y))
    
    draw.polygon(points, outline=color, width=2)
    
    for p in points:
        draw.line((cx, cy, p[0], p[1]), fill=color, width=1)

    glow = img.filter(ImageFilter.GaussianBlur(4))
    final = Image.alpha_composite(glow, img)

    if index is not None:
        save_asset(final, CATEGORIES["glyphs"], "sigil", index)
    return final

def create_giraffe(index=None):
    width, height = 600, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    body_color = (212, 197, 176, 255)
    spot_color = (20, 20, 20, 220)
    
    body_x, body_y = width // 2, height - 200
    neck_start = (body_x - 50, body_y)
    neck_end = (body_x + 100, body_y - 400)
    
    draw.line([neck_start, neck_end], fill=body_color, width=random.randint(20, 40))
    
    head_center = neck_end
    draw.ellipse((head_center[0]-30, head_center[1]-20, head_center[0]+50, head_center[1]+40), fill=body_color)
    
    draw.line([head_center, (head_center[0], head_center[1]-60)], fill=body_color, width=5)
    draw.line([(head_center[0]+20, head_center[1]), (head_center[0]+20, head_center[1]-60)], fill=body_color, width=5)
    
    draw.rectangle((body_x - 100, body_y, body_x + 100, body_y + 100), fill=body_color)
    
    leg_width = 15
    draw.line([(body_x - 80, body_y+100), (body_x - 90, height-50)], fill=body_color, width=leg_width)
    draw.line([(body_x + 80, body_y+100), (body_x + 90, height-50)], fill=body_color, width=leg_width)
    
    for _ in range(20):
        spot_x = random.randint(body_x - 100, body_x + 150)
        spot_y = random.randint(body_y - 400, height - 50)
        s_size = random.randint(5, 20)
        draw.ellipse((spot_x, spot_y, spot_x+s_size, spot_y+s_size), fill=spot_color)
        
    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "giraffe", index)
    return img

def create_kangaroo(index=None):
    width, height = 600, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    ink = (10, 10, 12, 240)
    parchment = (212, 197, 176, 255)
    
    cx, cy = width // 2, height // 2
    
    # Pogo
    draw.line([(cx, cy - 50), (cx, cy + 250)], fill=ink, width=10)
    draw.line([(cx-40, cy-40), (cx+40, cy-40)], fill=ink, width=8)
    draw.line([(cx-30, cy+180), (cx+30, cy+180)], fill=ink, width=8)
    
    spring_pts = []
    for i in range(12):
        off = 15 if i % 2 == 0 else -15
        spring_pts.append((cx + off, cy + 180 + i*5))
    if len(spring_pts) > 1:
        draw.line(spring_pts, fill=ink, width=4)

    # Kangaroo
    tail_pts = [(cx-40, cy+50), (cx-150, cy+20), (cx-180, cy-50)]
    draw.line(tail_pts, fill=parchment, width=25)
    draw.ellipse((cx-50, cy-100, cx+50, cy+80), fill=parchment)
    draw.ellipse((cx-30, cy-160, cx+50, cy-90), fill=parchment)
    draw.polygon([(cx, cy-150), (cx-10, cy-220), (cx+10, cy-160)], fill=parchment)
    draw.polygon([(cx+25, cy-150), (cx+40, cy-210), (cx+35, cy-160)], fill=parchment)
    
    draw.line([(cx-20, cy+50), (cx-60, cy+80)], fill=parchment, width=15)
    draw.line([(cx+20, cy+50), (cx+60, cy+80)], fill=parchment, width=15)
    draw.line([(cx-60, cy+80), (cx-25, cy+180)], fill=parchment, width=12)
    draw.line([(cx+60, cy+80), (cx+25, cy+180)], fill=parchment, width=12)
    
    draw.line([(cx-30, cy-20), (cx-35, cy-40)], fill=parchment, width=10)
    draw.line([(cx+30, cy-20), (cx+35, cy-40)], fill=parchment, width=10)
    
    draw.ellipse((cx+10, cy-140, cx+20, cy-130), fill=ink)
    
    for _ in range(15):
        sx = random.randint(cx-100, cx+100)
        sy = random.randint(cy+200, cy+300)
        draw.ellipse((sx, sy, sx+random.randint(2,8), sy+random.randint(2,8)), fill=ink)

    img = img.filter(ImageFilter.GaussianBlur(1))

    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "kangaroo", index)
    return img

def create_ink_divider(index=None):
    width, height = 1000, 100
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cy = height // 2
    ink_color = (0, 0, 0, 255)
    
    # Main stroke
    points = []
    for x in range(50, width - 50, 5):
        y = cy + random.randint(-5, 5) + math.sin(x / 50) * 10
        points.append((x, y))
    
    draw.line(points, fill=ink_color, width=random.randint(2, 5))
    
    # Splatters along the line
    for _ in range(10):
        sx = random.randint(100, width - 100)
        sy = cy + random.randint(-20, 20)
        r = random.randint(2, 8)
        draw.ellipse((sx, sy, sx+r, sy+r), fill=ink_color)
        
    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "ink_divider", index)
    return img

def create_void_orb(index=None):
    width, height = 300, 300
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    
    # Outer Glow
    for r in range(100, 80, -2):
        alpha = int((r - 80) * 5)
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(200, 200, 255, alpha), width=1)
        
    # Core
    draw.ellipse((cx-80, cy-80, cx+80, cy+80), fill=(10, 10, 20, 240))
    
    # Inner Runes/Noise
    for _ in range(5):
        r = random.randint(20, 60)
        angle = random.uniform(0, 6.28)
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        draw.ellipse((x, y, x+5, y+5), fill=(200, 200, 255, 200))
        
    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "void_orb", index)
    return img

def create_void_manta(index=None):
    seed_from_index(index, "void_manta")
    
    # Vary manta properties
    ink_color = get_color_variant(index, (10, 10, 15, 230), 20)
    glow_color = get_color_variant(index, (180, 160, 255, 150), 40)
    body_width = get_count_variant(index, 180, 150, 220)
    body_height = get_count_variant(index, 150, 120, 180)
    wing_extension = get_count_variant(index, 220, 180, 260)
    tail_length = get_count_variant(index, 200, 150, 250)
    tail_width = get_count_variant(index, 5, 3, 8)
    
    width, height = 600, 600
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    
    # Body (Diamond/Kite shape) with varied size
    points = [(cx, cy-body_height), (cx+body_width, cy), (cx, cy+body_height), (cx-body_width, cy)]
    draw.polygon(points, fill=ink_color)
    
    # Tail with varied length and width
    draw.line([(cx, cy+body_height), (cx, cy+body_height+tail_length)], fill=ink_color, width=tail_width)
    
    # Wings/Fins details with varied extension
    draw.polygon([(cx, cy-body_height), (cx+wing_extension, cy-20), (cx+body_width, cy)], fill=ink_color)
    draw.polygon([(cx, cy-body_height), (cx-wing_extension, cy-20), (cx-body_width, cy)], fill=ink_color)

    # Eyes with varied color and position
    eye_offset = body_width // 4
    draw.ellipse((cx-eye_offset-20, cy-80, cx-eye_offset, cy-60), fill=glow_color)
    draw.ellipse((cx+eye_offset, cy-80, cx+eye_offset+20, cy-60), fill=glow_color)
    
    # Blur for ethereal effect
    img = img.filter(ImageFilter.GaussianBlur(2))
    
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "void_manta", index)
    return img

def create_ink_crab(index=None):
    width, height = 500, 400
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    ink_color = (20, 20, 25, 240)
    
    # Body
    draw.ellipse((cx-80, cy-60, cx+80, cy+60), fill=ink_color)
    
    # Legs
    for i in range(4):
        offset = i * 25
        # Left legs
        draw.arc((cx-160, cy-40+offset, cx-60, cy+offset), 180, 360, fill=ink_color, width=8)
        # Right legs
        draw.arc((cx+60, cy-40+offset, cx+160, cy+offset), 180, 360, fill=ink_color, width=8)
        
    # Claws
    draw.pieslice((cx-140, cy-100, cx-60, cy-20), 150, 330, fill=ink_color)
    draw.pieslice((cx+60, cy-100, cx+140, cy-20), 210, 30, fill=ink_color)
    
    # Splatter effect
    for _ in range(20):
        sx = random.randint(cx-100, cx+100)
        sy = random.randint(cy-80, cy+80)
        r = random.randint(2, 6)
        draw.ellipse((sx, sy, sx+r, sy+r), fill=ink_color)

    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "ink_crab", index)
    return img

def create_mystic_eye(index=None):
    seed_from_index(index, "mystic_eye")
    
    # Vary eye properties for diversity
    iris_color = get_color_variant(index, (100, 50, 150, 200), 60)
    pupil_shape = get_count_variant(index, 0, 0, 2)  # 0=circle, 1=vertical, 2=horizontal
    ray_count = get_count_variant(index, 18, 12, 24)
    ray_spacing = 360 // ray_count
    rotation = get_rotation_variant(index)
    
    width, height = 400, 400
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    
    # Eye shape
    draw.ellipse((cx-150, cy-100, cx+150, cy+100), fill=(20, 20, 20, 255))
    draw.ellipse((cx-120, cy-70, cx+120, cy+70), outline=(200, 200, 200, 255), width=3)
    
    # Iris with varied color
    iris_size = get_count_variant(index, 40, 30, 50)
    draw.ellipse((cx-iris_size, cy-iris_size, cx+iris_size, cy+iris_size), fill=iris_color)
    
    # Pupil with varied shape
    if pupil_shape == 0:
        draw.ellipse((cx-15, cy-15, cx+15, cy+15), fill=(255, 255, 255, 255))
    elif pupil_shape == 1:
        draw.ellipse((cx-8, cy-25, cx+8, cy+25), fill=(255, 255, 255, 255))
    else:
        draw.ellipse((cx-25, cy-8, cx+25, cy+8), fill=(255, 255, 255, 255))
    
    # Rays/Lashes with varied count and rotation
    for i in range(0, 360, ray_spacing):
        angle = math.radians(i + rotation)
        x1 = cx + math.cos(angle) * 80
        y1 = cy + math.sin(angle) * 50
        x2 = cx + math.cos(angle) * 140
        y2 = cy + math.sin(angle) * 90
        draw.line([(x1, y1), (x2, y2)], fill=(20, 20, 20, 200), width=2)

    img = img.filter(ImageFilter.GaussianBlur(1))

    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "mystic_eye", index)
    return img

def create_broken_chain(index=None):
    seed_from_index(index, "broken_chain")
    
    # Vary chain properties
    chain_color = get_color_variant(index, (30, 30, 35, 255), 30)
    num_links = get_count_variant(index, 5, 4, 7)
    broken_link = get_count_variant(index, num_links // 2, 1, num_links - 1)
    link_width = get_count_variant(index, 8, 6, 10)
    link_size = get_count_variant(index, 20, 15, 25)
    
    width, height = 200, 600
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx = width // 2
    link_spacing = (height - 200) // (num_links - 1)
    
    # Links with varied broken position
    for i in range(num_links):
        cy = 100 + i * link_spacing
        if i == broken_link: # Broken link
            angle_gap = random.randint(20, 60)
            draw.arc((cx-link_size, cy-30, cx+link_size, cy+30), 180+angle_gap, 360-angle_gap, fill=chain_color, width=link_width)
            draw.arc((cx-link_size, cy-30, cx+link_size, cy+30), angle_gap, 180-angle_gap, fill=chain_color, width=link_width)
        else:
            draw.ellipse((cx-link_size, cy-30, cx+link_size, cy+30), outline=chain_color, width=link_width)
            
    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "broken_chain", index)
    return img

def create_floating_island(index=None):
    width, height = 500, 500
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    rock_color = (40, 40, 45, 255)
    
    # Island Base (inverted triangle-ish)
    points = [
        (cx-100, cy), (cx+100, cy),
        (cx+60, cy+80), (cx+20, cy+150),
        (cx-40, cy+100), (cx-80, cy+60)
    ]
    draw.polygon(points, fill=rock_color)
    
    # Top vegetation/details
    draw.ellipse((cx-100, cy-20, cx+100, cy+20), fill=rock_color)
    
    # Floating debris
    for _ in range(5):
        dx = random.randint(cx-120, cx+120)
        dy = random.randint(cy+50, cy+200)
        s = random.randint(5, 15)
        draw.ellipse((dx, dy, dx+s, dy+s), fill=rock_color)

    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "floating_island", index)
    return img

def create_rune_stone(index=None):
    seed_from_index(index, "rune_stone")
    
    # Vary rune stone properties
    stone_color = get_color_variant(index, (180, 180, 200, 255), 40)
    line_color = get_color_variant(index, (100, 100, 150, 255), 50)
    num_lines = get_count_variant(index, 8, 5, 12)
    stone_radius = get_count_variant(index, 60, 50, 70)
    line_length = get_count_variant(index, 70, 60, 85)
    rotation = get_rotation_variant(index)
    
    width, height = 200, 200
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    draw.ellipse((cx-stone_radius, cy-stone_radius, cx+stone_radius, cy+stone_radius), fill=stone_color)
    
    for i in range(num_lines):
        angle = math.radians((360 / num_lines) * i + rotation)
        x = cx + math.cos(angle)*line_length
        y = cy + math.sin(angle)*line_length
        draw.line((cx, cy, x, y), fill=line_color, width=3)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "rune_stone", index)
    return img

def create_ink_splatter(index=None):
    width, height = 400, 400
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    ink_color = (20,20,25,200)
    for _ in range(150):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(1,4)
        draw.ellipse((x, y, x+r, y+r), fill=ink_color)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "ink_splatter", index)
    return img

def create_mystic_frame(index=None):
    seed_from_index(index, "mystic_frame")
    
    # Vary frame properties
    frame_color = get_color_variant(index, (150, 120, 200, 255), 50)
    num_layers = get_count_variant(index, 5, 3, 7)
    outer_width = get_count_variant(index, 8, 5, 12)
    corner_style = get_count_variant(index, 0, 0, 2)  # 0=square, 1=rounded, 2=ornate
    
    width, height = 500, 500
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Outer frame
    draw.rectangle((20,20,width-20,height-20), outline=frame_color, width=outer_width)
    
    # Inner layers
    layer_spacing = (width // 2 - 40) // num_layers
    for i in range(num_layers):
        offset = 20 + (i+1)*layer_spacing
        draw.rectangle((offset, offset, width-offset, height-offset), outline=frame_color, width=2)
    
    # Add corner decorations based on style
    if corner_style >= 1:
        corner_size = 30
        for cx, cy in [(40, 40), (width-40, 40), (40, height-40), (width-40, height-40)]:
            draw.ellipse((cx-corner_size//2, cy-corner_size//2, cx+corner_size//2, cy+corner_size//2), 
                        outline=frame_color, width=2)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "mystic_frame", index)
    return img

def create_void_crystal(index=None):
    seed_from_index(index, "void_crystal")
    
    # Vary crystal properties for diversity
    num_sides = get_count_variant(index, 6, 5, 8)
    crystal_color = get_color_variant(index, (100, 150, 255, 200), 50)
    radius = int(120 * get_size_variant(index, 1.0, 0.3))
    rotation = get_rotation_variant(index)
    line_width = get_count_variant(index, 3, 2, 5)
    
    width, height = 300, 300
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    points = []
    for i in range(num_sides):
        angle = math.radians((360 / num_sides) * i + rotation)
        r = radius + random.randint(-10, 10)
        x = cx + math.cos(angle)*r
        y = cy + math.sin(angle)*r
        points.append((x,y))
    draw.polygon(points, outline=crystal_color, width=line_width)
    
    # Add inner glow lines
    for i in range(num_sides):
        angle = math.radians((360 / num_sides) * i + rotation)
        draw.line([(cx, cy), (cx + math.cos(angle)*radius*0.7, cy + math.sin(angle)*radius*0.7)], 
                  fill=crystal_color, width=1)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "void_crystal", index)
    return img

def create_ancient_key(index=None):
    seed_from_index(index, "ancient_key")
    
    # Vary key properties
    key_color = get_color_variant(index, (180, 150, 100, 255), 40)
    num_teeth = get_count_variant(index, 3, 2, 5)
    shaft_width = get_count_variant(index, 10, 8, 14)
    head_size = get_count_variant(index, 30, 25, 40)
    
    width, height = 200, 400
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Shaft
    draw.rectangle((width//2-shaft_width//2, 100, width//2+shaft_width//2, height-20), fill=key_color)
    
    # Head (circular or square)
    if random.random() > 0.5:
        draw.ellipse((width//2-head_size, 60, width//2+head_size, 120), fill=key_color)
    else:
        draw.rectangle((width//2-head_size, 60, width//2+head_size, 120), fill=key_color)
    
    # Teeth with varied count and spacing
    tooth_spacing = (width - 40) // (num_teeth + 1)
    for i in range(num_teeth):
        x_pos = 20 + (i + 1) * tooth_spacing
        tooth_height = random.randint(15, 30)
        draw.rectangle((x_pos-5, height-tooth_height, x_pos+5, height), fill=key_color)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "ancient_key", index)
    return img

# ===== 20 NEW UNIQUE ASSETS =====

def create_void_rune(index=None):
    seed_from_index(index, "void_rune")
    
    # Vary rune properties
    line_count = get_count_variant(index, 8, 4, 12)
    glow_intensity = get_count_variant(index, 8, 4, 12)
    rotation = get_rotation_variant(index)
    rune_color = get_color_variant(index, (150, 100, 200, 255), 40)
    glow_color = get_color_variant(index, (200, 150, 255, 100), 30)
    
    width, height = 400, 400
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Central circle
    draw.ellipse((cx-80, cy-80, cx+80, cy+80), outline=rune_color, width=3)
    
    # Swirling void lines with varied count
    for i in range(line_count):
        angle_offset = (360 / line_count) * i + rotation
        angle = math.radians(angle_offset)
        x1 = cx + math.cos(angle) * 60
        y1 = cy + math.sin(angle) * 60
        x2 = cx + math.cos(angle + 0.5) * 120
        y2 = cy + math.sin(angle + 0.5) * 120
        draw.line([(x1, y1), (x2, y2)], fill=rune_color, width=2)
    
    # Glow effect with varied intensity
    for r in range(100, 100 + glow_intensity * 5, 5):
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=glow_color, width=1)
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "void_rune", index)
    return img

def create_ink_spiral(index=None):
    seed_from_index(index, "ink_spiral")
    
    # Vary spiral properties
    spiral_tightness = get_size_variant(index, 10, 0.4)  # Affects r = t / tightness
    splatter_count = get_count_variant(index, 15, 5, 30)
    line_thickness = get_count_variant(index, 4, 2, 8)
    rotations = get_count_variant(index, 3, 2, 5)
    
    width, height = 400, 400
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    ink_color = (20, 20, 25, 255)
    
    # Spiral path with varied tightness
    points = []
    for t in range(0, 360 * rotations, 5):
        angle = math.radians(t)
        r = t / spiral_tightness
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        points.append((x, y))
    
    draw.line(points, fill=ink_color, width=line_thickness)
    
    # Splatter accents with varied count
    for _ in range(splatter_count):
        sx = random.randint(cx-100, cx+100)
        sy = random.randint(cy-100, cy+100)
        r = random.randint(2, 6)
        draw.ellipse((sx, sy, sx+r, sy+r), fill=ink_color)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "ink_spiral", index)
    return img

def create_ethereal_feather(index=None):
    width, height = 300, 500
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = width//2
    feather_color = (180, 180, 200, 200)
    
    # Central shaft
    draw.line([(cx, 50), (cx, height-50)], fill=feather_color, width=3)
    
    # Barbs
    for y in range(80, height-50, 20):
        length = 40 + random.randint(-10, 10)
        draw.line([(cx, y), (cx-length, y-15)], fill=feather_color, width=2)
        draw.line([(cx, y), (cx+length, y-15)], fill=feather_color, width=2)
    
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "ethereal_feather", index)
    return img

def create_astral_eye(index=None):
    width, height = 400, 400
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Eye outline
    draw.ellipse((cx-120, cy-70, cx+120, cy+70), outline=(200, 200, 220, 255), width=3)
    
    # Nebula pupil
    for _ in range(50):
        px = random.randint(cx-30, cx+30)
        py = random.randint(cy-30, cy+30)
        color = (random.randint(100, 150), random.randint(50, 100), random.randint(150, 200), random.randint(100, 200))
        r = random.randint(2, 8)
        draw.ellipse((px, py, px+r, py+r), fill=color)
    
    # Central pupil
    draw.ellipse((cx-15, cy-15, cx+15, cy+15), fill=(255, 255, 255, 255))
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "astral_eye", index)
    return img

def create_void_circuit(index=None):
    width, height = 400, 400
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    circuit_color = (100, 80, 150, 255)
    glow_color = (150, 100, 200, 150)
    
    # Grid pattern
    for x in range(50, width-50, 60):
        for y in range(50, height-50, 60):
            draw.ellipse((x-5, y-5, x+5, y+5), fill=circuit_color)
            if random.random() > 0.5:
                draw.line([(x, y), (x+60, y)], fill=circuit_color, width=2)
            if random.random() > 0.5:
                draw.line([(x, y), (x, y+60)], fill=circuit_color, width=2)
    
    # Glow
    for x in range(50, width-50, 60):
        for y in range(50, height-50, 60):
            draw.ellipse((x-10, y-10, x+10, y+10), outline=glow_color, width=1)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "void_circuit", index)
    return img

def create_spectral_serpent(index=None):
    seed_from_index(index, "spectral_serpent")
    
    # Vary serpent properties
    segment_count = get_count_variant(index, 20, 15, 30)
    wave_amplitude = get_size_variant(index, 100, 0.5)
    body_width = get_count_variant(index, 25, 15, 35)
    serpent_color = get_color_variant(index, (180, 180, 200, 180), 30)
    eye_color = get_color_variant(index, (200, 100, 150, 255), 40)
    
    width, height = 600, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Serpentine body with varied segments and wave
    points = []
    for i in range(segment_count):
        x = width//2 + math.sin(i * 0.5) * wave_amplitude
        y = 100 + i * (600 / segment_count)
        points.append((x, y))
    
    draw.line(points, fill=serpent_color, width=body_width)
    
    # Head with varied position
    head_x, head_y = points[-1]
    head_size = int(body_width * 1.2)
    draw.ellipse((head_x-30, head_y-20, head_x+30, head_y+40), fill=serpent_color)
    
    # Eyes with varied color
    draw.ellipse((head_x-15, head_y+5, head_x-5, head_y+15), fill=eye_color)
    draw.ellipse((head_x+5, head_y+5, head_x+15, head_y+15), fill=eye_color)
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "spectral_serpent", index)
    return img

def create_void_hopper(index=None):
    seed_from_index(index, "void_hopper")
    
    # Vary hopper properties
    body_color = get_color_variant(index, (40, 40, 50, 255), 30)
    glow_color = get_color_variant(index, (150, 100, 200, 255), 50)
    body_width = get_count_variant(index, 60, 50, 75)
    body_height = get_count_variant(index, 120, 100, 140)
    leg_width = get_count_variant(index, 12, 8, 16)
    leg_spread = get_count_variant(index, 40, 30, 55)
    
    width, height = 400, 500
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Body with varied size
    draw.ellipse((cx-body_width, cy-body_height//2, cx+body_width, cy+body_height//2), fill=body_color)
    
    # Glowing core with varied color
    core_size = body_width // 3
    draw.ellipse((cx-core_size, cy-core_size//2, cx+core_size, cy+core_size//2), fill=glow_color)
    
    # Legs with varied spread and width
    draw.line([(cx-leg_spread, cy+30), (cx-leg_spread-20, cy+120)], fill=body_color, width=leg_width)
    draw.line([(cx+leg_spread, cy+30), (cx+leg_spread+20, cy+120)], fill=body_color, width=leg_width)
    
    # Feet
    foot_size = leg_width + 5
    draw.ellipse((cx-leg_spread-30, cy+110, cx-leg_spread-10, cy+130), fill=body_color)
    draw.ellipse((cx+leg_spread+10, cy+110, cx+leg_spread+30, cy+130), fill=body_color)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "void_hopper", index)
    return img

def create_abyssal_jelly(index=None):
    seed_from_index(index, "abyssal_jelly")
    
    # Vary jellyfish properties
    jelly_color = get_color_variant(index, (100, 120, 180, 150), 40)
    bell_size = get_count_variant(index, 100, 80, 130)
    num_tentacles = get_count_variant(index, 8, 6, 12)
    tentacle_length = get_count_variant(index, 10, 8, 14)
    tentacle_width = get_count_variant(index, 8, 5, 12)
    wave_frequency = get_size_variant(index, 0.5, 0.5)
    
    width, height = 500, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, 150
    
    # Bell/dome with varied size
    draw.pieslice((cx-bell_size, cy-bell_size*0.8, cx+bell_size, cy+bell_size*0.8), 0, 180, fill=jelly_color)
    
    # Tentacles with varied count, length, and wave
    tentacle_spacing = (bell_size * 2) // (num_tentacles - 1)
    for i in range(num_tentacles):
        x_start = cx - bell_size + i * tentacle_spacing
        points = []
        for j in range(tentacle_length):
            x = x_start + math.sin(j * wave_frequency) * 15
            y = cy + 80 + j * 40
            points.append((x, y))
        draw.line(points, fill=jelly_color, width=tentacle_width)
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "abyssal_jelly", index)
    return img

def create_ink_nebula(index=None):
    seed_from_index(index, "ink_nebula")
    
    # Vary nebula properties
    cloud_count = get_count_variant(index, 200, 100, 300)
    blur_radius = get_count_variant(index, 30, 15, 50)
    color_tint = get_count_variant(index, 20, 10, 40)
    
    width, height = 1024, 1024
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Swirling ink clouds with varied count and colors
    for _ in range(cloud_count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(20, 80)
        color = (random.randint(10, color_tint), random.randint(10, color_tint), random.randint(20, color_tint + 20), random.randint(50, 150))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
    
    img = img.filter(ImageFilter.GaussianBlur(blur_radius))
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "ink_nebula", index)
    return img

def create_ethereal_mist(index=None):
    width, height = 1024, 1024
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Soft mist layers
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(40, 120)
        alpha = random.randint(20, 80)
        color = (200, 200, 220, alpha)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
    
    img = img.filter(ImageFilter.GaussianBlur(40))
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "ethereal_mist", index)
    return img

from PIL import ImageOps

if __name__ == "__main__":
    print("Starting NanoBanana Generator...")
    for i in range(1, 21):
        create_void_parchment(i)
        create_ink_enso(i)
        create_sigil(i)
        create_giraffe(i)
        create_kangaroo(i)
        create_ink_divider(i)
        create_void_orb(i)
        create_void_manta(i)
        create_ink_crab(i)
        create_mystic_eye(i)
        create_broken_chain(i)
        create_floating_island(i)
        create_rune_stone(i)
        create_ink_splatter(i)
        create_mystic_frame(i)
        create_void_crystal(i)
        create_ancient_key(i)
        # New unique assets
        create_void_rune(i)
        create_ink_spiral(i)
        create_ethereal_feather(i)
        create_astral_eye(i)
        create_void_circuit(i)
        create_spectral_serpent(i)
        create_void_hopper(i)
        create_abyssal_jelly(i)
        create_ink_nebula(i)
        create_ethereal_mist(i)
    print("Done! Assets generated in standardized structure.")

# ===== 10 NEW HIGHLY DIVERSE ASSETS =====

def create_void_portal(index=None):
    seed_from_index(index, "void_portal")
    
    # Highly varied portal properties
    portal_color = get_color_variant(index, (120, 80, 180, 200), 60)
    num_rings = get_count_variant(index, 8, 5, 12)
    particle_count = get_count_variant(index, 50, 30, 80)
    swirl_intensity = get_size_variant(index, 1.0, 0.6)
    rotation = get_rotation_variant(index)
    portal_shape = get_count_variant(index, 0, 0, 2)  # 0=circle, 1=oval, 2=spiral
    
    width, height = 600, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Concentric rings with varied count and color
    for i in range(num_rings):
        radius = 50 + i * 25
        ring_color = get_color_variant(index + i, portal_color, 20)
        width_var = get_count_variant(index + i, 3, 2, 6)
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), 
                    outline=ring_color, width=width_var)
    
    # Swirling particles with varied count and pattern
    for _ in range(particle_count):
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(0, 250)
        px = cx + math.cos(angle + rotation) * dist * swirl_intensity
        py = cy + math.sin(angle + rotation) * dist * swirl_intensity
        p_size = random.randint(2, 8)
        p_color = get_color_variant(index, (200, 150, 255, random.randint(100, 255)), 40)
        draw.ellipse((px, py, px+p_size, py+p_size), fill=p_color)
    
    # Center vortex
    vortex_size = get_count_variant(index, 40, 25, 60)
    draw.ellipse((cx-vortex_size, cy-vortex_size, cx+vortex_size, cy+vortex_size), 
                fill=(10, 10, 20, 255))
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "void_portal", index)
    return img

def create_spectral_wisp(index=None):
    seed_from_index(index, "spectral_wisp")
    
    # Varied wisp properties
    wisp_color = get_color_variant(index, (180, 200, 220, 150), 50)
    num_trails = get_count_variant(index, 5, 3, 8)
    wisp_length = get_count_variant(index, 200, 150, 300)
    wisp_width = get_count_variant(index, 30, 20, 45)
    has_face = random.random() > 0.5
    
    width, height = 400, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = width//2
    
    # Main body - flowing ethereal shape
    for i in range(num_trails):
        points = []
        y_start = 100 + i * (wisp_length // num_trails)
        for j in range(20):
            x = cx + math.sin(j * 0.3 + i) * wisp_width
            y = y_start + j * 15
            points.append((x, y))
        trail_color = get_color_variant(index + i, wisp_color, 30)
        draw.line(points, fill=trail_color, width=get_count_variant(index+i, 15, 10, 25))
    
    # Wisp head/core
    head_size = get_count_variant(index, 50, 35, 70)
    draw.ellipse((cx-head_size, 50, cx+head_size, 50+head_size*2), fill=wisp_color)
    
    # Optional face features
    if has_face:
        eye_color = get_color_variant(index, (100, 150, 200, 255), 40)
        draw.ellipse((cx-20, 80, cx-10, 100), fill=eye_color)
        draw.ellipse((cx+10, 80, cx+20, 100), fill=eye_color)
    
    img = img.filter(ImageFilter.GaussianBlur(3))
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "spectral_wisp", index)
    return img

def create_ancient_scroll(index=None):
    seed_from_index(index, "ancient_scroll")
    
    # Varied scroll properties
    scroll_color = get_color_variant(index, (200, 180, 140, 255), 40)
    text_color = get_color_variant(index, (40, 30, 20, 200), 30)
    num_text_lines = get_count_variant(index, 8, 5, 12)
    num_runes = get_count_variant(index, 4, 2, 6)
    scroll_curl = get_size_variant(index, 1.0, 0.4)
    
    width, height = 500, 700
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = width//2
    
    # Scroll body with curl variation
    scroll_width = int(350 * scroll_curl)
    draw.rectangle((cx-scroll_width//2, 100, cx+scroll_width//2, height-100), 
                  fill=scroll_color)
    
    # Top and bottom rolls
    roll_height = get_count_variant(index, 30, 20, 45)
    draw.rectangle((cx-scroll_width//2, 80, cx+scroll_width//2, 100), fill=scroll_color)
    draw.rectangle((cx-scroll_width//2, height-100, cx+scroll_width//2, height-80), 
                  fill=scroll_color)
    
    # Mystical text lines
    line_spacing = (height - 250) // num_text_lines
    for i in range(num_text_lines):
        y = 130 + i * line_spacing
        line_length = random.randint(scroll_width-100, scroll_width-50)
        draw.line([(cx-line_length//2, y), (cx+line_length//2, y)], 
                 fill=text_color, width=2)
        
        # Add random "rune" marks
        for _ in range(random.randint(2, 5)):
            rx = random.randint(cx-line_length//2, cx+line_length//2)
            draw.ellipse((rx, y-3, rx+6, y+3), fill=text_color)
    
    # Decorative runes around edges
    for i in range(num_runes):
        angle = (360 / num_runes) * i
        radius = scroll_width // 2 + 20
        rx = cx + math.cos(math.radians(angle)) * radius
        ry = height // 2 + math.sin(math.radians(angle)) * 200
        rune_size = random.randint(15, 25)
        draw.polygon([(rx, ry-rune_size), (rx+rune_size, ry), (rx, ry+rune_size), 
                     (rx-rune_size, ry)], outline=text_color, width=2)
    
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "ancient_scroll", index)
    return img

def create_shadow_beast(index=None):
    seed_from_index(index, "shadow_beast")
    
    # Highly varied beast properties
    shadow_color = get_color_variant(index, (20, 15, 25, 220), 15)
    eye_color = get_color_variant(index, (200, 80, 100, 255), 60)
    num_limbs = get_count_variant(index, 6, 4, 10)
    beast_size = get_size_variant(index, 1.0, 0.4)
    has_horns = random.random() > 0.5
    has_wings = random.random() > 0.6
    
    width, height = 600, 700
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Main body - amorphous shadow shape
    body_width = int(150 * beast_size)
    body_height = int(180 * beast_size)
    draw.ellipse((cx-body_width, cy-body_height//2, cx+body_width, cy+body_height), 
                fill=shadow_color)
    
    # Limbs/tentacles radiating outward
    limb_spacing = 360 // num_limbs
    for i in range(num_limbs):
        angle = limb_spacing * i + get_rotation_variant(index + i)
        limb_length = random.randint(80, 180)
        limb_width = random.randint(12, 25)
        
        end_x = cx + math.cos(math.radians(angle)) * limb_length
        end_y = cy + math.sin(math.radians(angle)) * limb_length
        
        # Wavy limb
        points = []
        for j in range(10):
            t = j / 10
            x = cx + (end_x - cx) * t + math.sin(j) * 10
            y = cy + (end_y - cy) * t
            points.append((x, y))
        draw.line(points, fill=shadow_color, width=limb_width)
    
    # Glowing eyes
    num_eyes = get_count_variant(index, 2, 1, 4)
    eye_spacing = body_width // (num_eyes + 1)
    for i in range(num_eyes):
        eye_x = cx - body_width//2 + (i+1) * eye_spacing
        eye_y = cy - body_height//4
        eye_size = random.randint(12, 20)
        draw.ellipse((eye_x-eye_size, eye_y-eye_size, eye_x+eye_size, eye_y+eye_size), 
                    fill=eye_color)
    
    # Optional horns
    if has_horns:
        horn_count = random.randint(2, 4)
        for i in range(horn_count):
            hx = cx + random.randint(-body_width//2, body_width//2)
            hy = cy - body_height
            horn_height = random.randint(40, 80)
            draw.polygon([(hx, hy), (hx-10, hy-horn_height), (hx+10, hy-horn_height)], 
                        fill=shadow_color)
    
    # Optional wings
    if has_wings:
        wing_span = int(200 * beast_size)
        # Left wing
        draw.polygon([(cx-body_width, cy), (cx-wing_span, cy-100), (cx-body_width, cy+50)], 
                    fill=(shadow_color[0], shadow_color[1], shadow_color[2], 100))
        # Right wing
        draw.polygon([(cx+body_width, cy), (cx+wing_span, cy-100), (cx+body_width, cy+50)], 
                    fill=(shadow_color[0], shadow_color[1], shadow_color[2], 100))
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "shadow_beast", index)
    return img

def create_mystic_constellation(index=None):
    seed_from_index(index, "mystic_constellation")
    
    # Varied constellation properties
    star_color = get_color_variant(index, (200, 200, 255, 255), 50)
    line_color = get_color_variant(index, (150, 150, 200, 150), 40)
    num_stars = get_count_variant(index, 9, 6, 15)
    pattern_type = get_count_variant(index, 0, 0, 3)  # Different patterns
    rotation = get_rotation_variant(index)
    
    width, height = 500, 500
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Generate star positions based on pattern
    star_positions = []
    if pattern_type == 0:  # Circular
        for i in range(num_stars):
            angle = math.radians((360 / num_stars) * i + rotation)
            radius = random.randint(100, 180)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            star_positions.append((x, y))
    elif pattern_type == 1:  # Spiral
        for i in range(num_stars):
            angle = math.radians(i * 40 + rotation)
            radius = 40 + i * 15
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            star_positions.append((x, y))
    elif pattern_type == 2:  # Grid
        grid_size = int(math.sqrt(num_stars))
        spacing = 100
        for i in range(grid_size):
            for j in range(grid_size):
                if len(star_positions) < num_stars:
                    x = cx - spacing + j * (spacing * 2 // grid_size)
                    y = cy - spacing + i * (spacing * 2 // grid_size)
                    star_positions.append((x, y))
    else:  # Random
        for _ in range(num_stars):
            x = cx + random.randint(-180, 180)
            y = cy + random.randint(-180, 180)
            star_positions.append((x, y))
    
    # Connect stars with lines
    for i in range(len(star_positions) - 1):
        draw.line([star_positions[i], star_positions[i+1]], fill=line_color, width=2)
    if len(star_positions) > 2:
        draw.line([star_positions[-1], star_positions[0]], fill=line_color, width=2)
    
    # Draw stars
    for x, y in star_positions:
        star_size = random.randint(6, 14)
        # Four-pointed star
        points = [
            (x, y-star_size), (x+star_size//3, y-star_size//3),
            (x+star_size, y), (x+star_size//3, y+star_size//3),
            (x, y+star_size), (x-star_size//3, y+star_size//3),
            (x-star_size, y), (x-star_size//3, y-star_size//3)
        ]
        draw.polygon(points, fill=star_color)
        
        # Glow
        glow_color = (star_color[0], star_color[1], star_color[2], 80)
        draw.ellipse((x-star_size*2, y-star_size*2, x+star_size*2, y+star_size*2), 
                    fill=glow_color)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "mystic_constellation", index)
    return img

def create_ink_butterfly(index=None):
    seed_from_index(index, "ink_butterfly")
    
    # Varied butterfly properties
    wing_color = get_color_variant(index, (80, 60, 100, 200), 50)
    accent_color = get_color_variant(index, (180, 150, 200, 220), 60)
    wing_span = get_count_variant(index, 200, 150, 280)
    wing_pattern = get_count_variant(index, 0, 0, 3)
    num_spots = get_count_variant(index, 6, 3, 10)
    
    width, height = 600, 500
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Body
    body_length = get_count_variant(index, 120, 100, 150)
    draw.ellipse((cx-10, cy-body_length//2, cx+10, cy+body_length//2), 
                fill=(20, 20, 25, 255))
    
    # Antennae
    antenna_length = random.randint(40, 70)
    draw.line([(cx-5, cy-body_length//2), (cx-20, cy-body_length//2-antenna_length)], 
             fill=(20, 20, 25, 255), width=3)
    draw.line([(cx+5, cy-body_length//2), (cx+20, cy-body_length//2-antenna_length)], 
             fill=(20, 20, 25, 255), width=3)
    
    # Wings - upper
    wing_height = wing_span // 2
    # Left upper wing
    left_upper = [(cx-10, cy-20), (cx-wing_span//2, cy-wing_height), 
                  (cx-wing_span//3, cy+20)]
    draw.polygon(left_upper, fill=wing_color, outline=accent_color, width=3)
    
    # Right upper wing
    right_upper = [(cx+10, cy-20), (cx+wing_span//2, cy-wing_height), 
                   (cx+wing_span//3, cy+20)]
    draw.polygon(right_upper, fill=wing_color, outline=accent_color, width=3)
    
    # Lower wings
    # Left lower
    left_lower = [(cx-10, cy+20), (cx-wing_span//3, cy+wing_height), 
                  (cx-wing_span//4, cy+50)]
    draw.polygon(left_lower, fill=wing_color, outline=accent_color, width=3)
    
    # Right lower
    right_lower = [(cx+10, cy+20), (cx+wing_span//3, cy+wing_height), 
                   (cx+wing_span//4, cy+50)]
    draw.polygon(right_lower, fill=wing_color, outline=accent_color, width=3)
    
    # Wing patterns/spots
    for _ in range(num_spots//2):
        # Left wing spots
        sx = random.randint(cx-wing_span//2+30, cx-30)
        sy = random.randint(cy-wing_height+30, cy+30)
        spot_size = random.randint(8, 18)
        draw.ellipse((sx, sy, sx+spot_size, sy+spot_size), fill=accent_color)
        
        # Mirror to right wing
        sx_mirror = cx + (cx - sx)
        draw.ellipse((sx_mirror-spot_size, sy, sx_mirror, sy+spot_size), fill=accent_color)
    
    img = img.filter(ImageFilter.GaussianBlur(1))
    if index is not None:
        save_asset(img, CATEGORIES["creatures"], "ink_butterfly", index)
    return img

def create_void_anchor(index=None):
    seed_from_index(index, "void_anchor")
    
    # Varied anchor properties
    anchor_color = get_color_variant(index, (100, 100, 120, 255), 40)
    chain_color = get_color_variant(index, (80, 80, 100, 255), 30)
    num_chain_links = get_count_variant(index, 6, 4, 10)
    anchor_style = get_count_variant(index, 0, 0, 2)  # Different anchor designs
    has_runes = random.random() > 0.5
    
    width, height = 400, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = width//2
    
    # Chain links
    link_spacing = 40
    for i in range(num_chain_links):
        cy_link = 50 + i * link_spacing
        link_size = random.randint(15, 22)
        draw.ellipse((cx-link_size, cy_link-link_size//2, cx+link_size, cy_link+link_size//2), 
                    outline=chain_color, width=4)
    
    # Anchor top position
    anchor_top = 50 + num_chain_links * link_spacing
    
    # Anchor shank (vertical bar)
    shank_height = get_count_variant(index, 200, 150, 250)
    draw.rectangle((cx-10, anchor_top, cx+10, anchor_top+shank_height), 
                  fill=anchor_color)
    
    # Anchor crown (top horizontal)
    crown_width = get_count_variant(index, 60, 45, 80)
    draw.rectangle((cx-crown_width, anchor_top-8, cx+crown_width, anchor_top+8), 
                  fill=anchor_color)
    
    # Anchor flukes (bottom hooks)
    fluke_span = get_count_variant(index, 120, 90, 160)
    fluke_curve = get_count_variant(index, 40, 30, 60)
    
    if anchor_style == 0:  # Traditional
        # Left fluke
        draw.polygon([
            (cx-10, anchor_top+shank_height),
            (cx-fluke_span, anchor_top+shank_height-fluke_curve),
            (cx-fluke_span+20, anchor_top+shank_height-fluke_curve-30),
            (cx-30, anchor_top+shank_height-20)
        ], fill=anchor_color)
        
        # Right fluke
        draw.polygon([
            (cx+10, anchor_top+shank_height),
            (cx+fluke_span, anchor_top+shank_height-fluke_curve),
            (cx+fluke_span-20, anchor_top+shank_height-fluke_curve-30),
            (cx+30, anchor_top+shank_height-20)
        ], fill=anchor_color)
    elif anchor_style == 1:  # Modern
        # Straight flukes
        draw.polygon([
            (cx, anchor_top+shank_height),
            (cx-fluke_span//2, anchor_top+shank_height+40),
            (cx-fluke_span//2+15, anchor_top+shank_height+50)
        ], fill=anchor_color)
        draw.polygon([
            (cx, anchor_top+shank_height),
            (cx+fluke_span//2, anchor_top+shank_height+40),
            (cx+fluke_span//2-15, anchor_top+shank_height+50)
        ], fill=anchor_color)
    else:  # Mystical
        # Curved mystical flukes
        points_left = [
            (cx, anchor_top+shank_height),
            (cx-fluke_span//2, anchor_top+shank_height+20),
            (cx-fluke_span, anchor_top+shank_height-20),
            (cx-fluke_span+20, anchor_top+shank_height-40)
        ]
        draw.line(points_left, fill=anchor_color, width=20)
        
        points_right = [
            (cx, anchor_top+shank_height),
            (cx+fluke_span//2, anchor_top+shank_height+20),
            (cx+fluke_span, anchor_top+shank_height-20),
            (cx+fluke_span-20, anchor_top+shank_height-40)
        ]
        draw.line(points_right, fill=anchor_color, width=20)
    
    # Optional runes on shank
    if has_runes:
        num_runes = random.randint(3, 6)
        rune_spacing = shank_height // (num_runes + 1)
        for i in range(num_runes):
            ry = anchor_top + (i+1) * rune_spacing
            rune_type = random.randint(0, 3)
            rune_color = get_color_variant(index, (180, 160, 200, 200), 30)
            
            if rune_type == 0:
                draw.line([(cx-6, ry), (cx+6, ry)], fill=rune_color, width=2)
            elif rune_type == 1:
                draw.ellipse((cx-4, ry-4, cx+4, ry+4), outline=rune_color, width=2)
            elif rune_type == 2:
                draw.polygon([(cx, ry-6), (cx+6, ry+6), (cx-6, ry+6)], 
                           outline=rune_color, width=2)
            else:
                draw.line([(cx, ry-6), (cx, ry+6)], fill=rune_color, width=2)
    
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "void_anchor", index)
    return img

def create_ethereal_torch(index=None):
    seed_from_index(index, "ethereal_torch")
    
    # Varied torch properties
    flame_color = get_color_variant(index, (180, 120, 220, 200), 70)
    stick_color = get_color_variant(index, (80, 70, 60, 255), 30)
    flame_height = get_count_variant(index, 150, 100, 220)
    flame_width = get_count_variant(index, 80, 60, 120)
    num_particles = get_count_variant(index, 20, 10, 35)
    flame_style = get_count_variant(index, 0, 0, 2)
    
    width, height = 400, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = width//2
    
    # Torch stick
    stick_top = height - 200
    stick_width = get_count_variant(index, 15, 12, 20)
    draw.rectangle((cx-stick_width//2, stick_top, cx+stick_width//2, height-50), 
                  fill=stick_color)
    
    # Wrapping/texture on stick
    num_wraps = random.randint(3, 6)
    for i in range(num_wraps):
        wrap_y = stick_top + 20 + i * 30
        wrap_color = get_color_variant(index+i, (60, 50, 40, 255), 20)
        draw.line([(cx-stick_width//2, wrap_y), (cx+stick_width//2, wrap_y)], 
                 fill=wrap_color, width=6)
    
    # Flame base
    flame_base_y = stick_top - 20
    
    if flame_style == 0:  # Pointed flame
        flame_points = [
            (cx, flame_base_y - flame_height),
            (cx + flame_width//2, flame_base_y - flame_height//2),
            (cx + flame_width//3, flame_base_y),
            (cx - flame_width//3, flame_base_y),
            (cx - flame_width//2, flame_base_y - flame_height//2)
        ]
        draw.polygon(flame_points, fill=flame_color)
    elif flame_style == 1:  # Wispy flame
        # Multiple overlapping ellipses
        for i in range(5):
            offset_x = random.randint(-20, 20)
            offset_y = i * (flame_height // 6)
            ellipse_width = flame_width - i * 10
            ellipse_height = flame_height // 5
            draw.ellipse((cx+offset_x-ellipse_width//2, flame_base_y-offset_y-ellipse_height,
                         cx+offset_x+ellipse_width//2, flame_base_y-offset_y), 
                        fill=flame_color)
    else:  # Ethereal flame
        # Draw as wavy line
        points = []
        for i in range(20):
            y = flame_base_y - (i * flame_height // 20)
            x = cx + math.sin(i * 0.5) * (flame_width // 2)
            points.append((x, y))
        draw.line(points, fill=flame_color, width=flame_width//2)
    
    # Floating particles/sparks
    for _ in range(num_particles):
        px = cx + random.randint(-flame_width, flame_width)
        py = flame_base_y - random.randint(0, flame_height + 100)
        p_size = random.randint(3, 8)
        p_color = get_color_variant(index, (255, 200, 150, random.randint(150, 255)), 60)
        draw.ellipse((px, py, px+p_size, py+p_size), fill=p_color)
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    if index is not None:
        save_asset(img, CATEGORIES["ui"], "ethereal_torch", index)
    return img

def create_crystal_shard(index=None):
    seed_from_index(index, "crystal_shard")
    
    # Varied crystal properties
    crystal_color = get_color_variant(index, (120, 180, 255, 200), 60)
    glow_color = get_color_variant(index, (180, 220, 255, 150), 50)
    num_faces = get_count_variant(index, 6, 4, 10)
    shard_height = get_count_variant(index, 300, 200, 400)
    rotation = get_rotation_variant(index)
    num_inner_facets = get_count_variant(index, 4, 2, 7)
    
    width, height = 400, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = width//2
    cy_base = height - 100
    cy_tip = cy_base - shard_height
    
    # Main crystal outline
    shard_width = get_count_variant(index, 100, 70, 140)
    crystal_points = [(cx, cy_tip)]  # Tip
    
    # Generate faceted edges
    for i in range(num_faces):
        angle_offset = (i / num_faces) * 180 - 90 + rotation
        height_pos = cy_tip + (i / num_faces) * shard_height
        width_pos = cx + math.cos(math.radians(angle_offset)) * (shard_width * (i / num_faces))
        crystal_points.append((width_pos, height_pos))
    
    crystal_points.append((cx + shard_width//2, cy_base))
    crystal_points.append((cx - shard_width//2, cy_base))
    
    # Mirror the points for other side
    for i in range(num_faces-1, -1, -1):
        angle_offset = (i / num_faces) * 180 - 90 - rotation
        height_pos = cy_tip + (i / num_faces) * shard_height
        width_pos = cx + math.cos(math.radians(angle_offset)) * (shard_width * (i / num_faces))
        crystal_points.append((width_pos, height_pos))
    
    draw.polygon(crystal_points, fill=crystal_color, outline=glow_color, width=3)
    
    # Inner facet lines
    for i in range(num_inner_facets):
        y_pos = cy_tip + (i+1) * (shard_height // (num_inner_facets + 1))
        x_offset = (shard_width // 2) * ((num_inner_facets - i) / num_inner_facets)
        draw.line([(cx - x_offset, y_pos), (cx + x_offset, y_pos)], 
                 fill=glow_color, width=2)
        draw.line([(cx, cy_tip), (cx - x_offset, y_pos)], fill=glow_color, width=1)
        draw.line([(cx, cy_tip), (cx + x_offset, y_pos)], fill=glow_color, width=1)
    
    # Glow effect
    for r in range(5):
        glow_alpha = int(100 / (r+1))
        glow = (glow_color[0], glow_color[1], glow_color[2], glow_alpha)
        draw.ellipse((cx-shard_width-r*10, cy_tip-r*10, 
                     cx+shard_width+r*10, cy_base+r*10), 
                    outline=glow, width=2)
    
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "crystal_shard", index)
    return img

def create_runic_circle(index=None):
    seed_from_index(index, "runic_circle")
    
    # Highly varied circle properties
    circle_color = get_color_variant(index, (160, 140, 180, 255), 50)
    rune_color = get_color_variant(index, (200, 180, 220, 255), 40)
    num_rings = get_count_variant(index, 4, 2, 6)
    num_runes = get_count_variant(index, 8, 6, 12)
    num_symbols = get_count_variant(index, 16, 10, 24)
    rotation = get_rotation_variant(index)
    has_center_glyph = random.random() > 0.5
    
    width, height = 600, 600
    img = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx, cy = width//2, height//2
    
    # Concentric circles
    base_radius = 250
    for i in range(num_rings):
        radius = base_radius - (i * (base_radius // (num_rings + 1)))
        line_width = get_count_variant(index+i, 3, 2, 5)
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), 
                    outline=circle_color, width=line_width)
    
    # Radial lines
    num_lines = get_count_variant(index, 12, 8, 16)
    for i in range(num_lines):
        angle = math.radians((360 / num_lines) * i + rotation)
        inner_radius = base_radius // num_rings
        x1 = cx + math.cos(angle) * inner_radius
        y1 = cy + math.sin(angle) * inner_radius
        x2 = cx + math.cos(angle) * base_radius
        y2 = cy + math.sin(angle) * base_radius
        draw.line([(x1, y1), (x2, y2)], fill=circle_color, width=2)
    
    # Runes around outer edge
    rune_radius = base_radius + 20
    rune_spacing = 360 / num_runes
    for i in range(num_runes):
        angle = math.radians(i * rune_spacing + rotation)
        rx = cx + math.cos(angle) * rune_radius
        ry = cy + math.sin(angle) * rune_radius
        
        # Different rune types
        rune_type = random.randint(0, 5)
        rune_size = random.randint(15, 25)
        
        if rune_type == 0:  # Triangle
            draw.polygon([
                (rx, ry-rune_size), 
                (rx+rune_size, ry+rune_size), 
                (rx-rune_size, ry+rune_size)
            ], outline=rune_color, width=2)
        elif rune_type == 1:  # Circle
            draw.ellipse((rx-rune_size//2, ry-rune_size//2, 
                         rx+rune_size//2, ry+rune_size//2), 
                        outline=rune_color, width=2)
        elif rune_type == 2:  # Cross
            draw.line([(rx-rune_size, ry), (rx+rune_size, ry)], 
                     fill=rune_color, width=2)
            draw.line([(rx, ry-rune_size), (rx, ry+rune_size)], 
                     fill=rune_color, width=2)
        elif rune_type == 3:  # Diamond
            draw.polygon([
                (rx, ry-rune_size), 
                (rx+rune_size, ry), 
                (rx, ry+rune_size), 
                (rx-rune_size, ry)
            ], outline=rune_color, width=2)
        elif rune_type == 4:  # Star
            draw.polygon([
                (rx, ry-rune_size),
                (rx+rune_size//3, ry-rune_size//3),
                (rx+rune_size, ry),
                (rx+rune_size//3, ry+rune_size//3),
                (rx, ry+rune_size),
                (rx-rune_size//3, ry+rune_size//3),
                (rx-rune_size, ry),
                (rx-rune_size//3, ry-rune_size//3)
            ], outline=rune_color, width=2)
        else:  # Line
            angle2 = angle + math.radians(random.randint(-30, 30))
            lx = rx + math.cos(angle2) * rune_size
            ly = ry + math.sin(angle2) * rune_size
            draw.line([(rx, ry), (lx, ly)], fill=rune_color, width=3)
    
    # Small symbols in between rings
    symbol_ring_radius = base_radius - (base_radius // num_rings) // 2
    symbol_spacing = 360 / num_symbols
    for i in range(num_symbols):
        angle = math.radians(i * symbol_spacing + rotation + 180/num_symbols)
        sx = cx + math.cos(angle) * symbol_ring_radius
        sy = cy + math.sin(angle) * symbol_ring_radius
        symbol_size = random.randint(5, 10)
        draw.ellipse((sx-symbol_size, sy-symbol_size, sx+symbol_size, sy+symbol_size), 
                    fill=rune_color)
    
    # Central glyph
    if has_center_glyph:
        glyph_size = base_radius // (num_rings + 1)
        # Complex central pattern
        for i in range(6):
            angle = math.radians(i * 60 + rotation)
            gx = cx + math.cos(angle) * glyph_size
            gy = cy + math.sin(angle) * glyph_size
            draw.line([(cx, cy), (gx, gy)], fill=rune_color, width=3)
            draw.ellipse((gx-5, gy-5, gx+5, gy+5), fill=rune_color)
        
        # Center point
        draw.ellipse((cx-10, cy-10, cx+10, cy+10), fill=rune_color)
    
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    if index is not None:
        save_asset(img, CATEGORIES["glyphs"], "runic_circle", index)
    return img
