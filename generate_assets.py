import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import math

OUTPUT_BASE = "assets/elements"
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

def create_void_parchment(index=None, base_color=(15, 15, 18), noise_scale=1.5):
    width, height = 1024, 1024
    img = Image.new('RGB', (width, height), base_color)
    
    # Layer 1: Heavy Grain
    noise = create_noise_layer(width, height, scale=noise_scale)
    img.paste(ImageOps.colorize(noise, (0,0,0), (40,40,45)), (0,0), mask=None)
    
    # Layer 2: Scratches
    scratches = create_noise_layer(width, height, scale=noise_scale + 0.5)
    scratches = scratches.resize((width, height // 10))
    scratches = scratches.resize((width, height), Image.BICUBIC)
    img = Image.blend(img, scratches.convert('RGB'), 0.1)
    
    # Vignette
    vignette = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(vignette)
    draw.ellipse((50, 50, width-50, height-50), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(150))
    
    dark_layer = Image.new('RGB', (width, height), (0,0,0))
    img = Image.composite(img, dark_layer, vignette)
    
    if index is not None:
        save_asset(img, CATEGORIES["backgrounds"], "void_parchment", index)
    return img

def create_ink_enso(index=None, color=(0,0,0), complexity=40, chaos=1.0):
    width, height = 800, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = width // 2, height // 2
    radius = 300
    
    for _ in range(complexity):
        points = []
        current_radius = radius + random.randint(int(-30 * chaos), int(30 * chaos))
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
            
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
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

from PIL import ImageOps

if __name__ == "__main__":
    print("Starting NanoBanana Generator...")
    for i in range(1, 4):
        create_void_parchment(i)
        create_ink_enso(i)
        create_sigil(i)
        create_giraffe(i)
        create_kangaroo(i)
        create_ink_divider(i)
        create_void_orb(i)
    print("Done! Assets generated in standardized structure.")
