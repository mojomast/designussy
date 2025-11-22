import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import math

OUTPUT_DIR = "assets/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_noise_layer(width, height, scale=1.0, opacity=128):
    # Generate random noise
    noise_data = np.random.normal(128, 50 * scale, (height, width)).astype(np.uint8)
    img = Image.fromarray(noise_data, mode='L')
    return img

def create_void_parchment(index):
    width, height = 1024, 1024
    base_color = (15, 15, 18) # Dark charcoal/black
    
    img = Image.new('RGB', (width, height), base_color)
    
    # Layer 1: Heavy Grain
    noise = create_noise_layer(width, height, scale=1.5)
    img.paste(ImageOps.colorize(noise, (0,0,0), (40,40,45)), (0,0), mask=None)
    
    # Layer 2: Scratches/Texture (simulated by stretching noise)
    scratches = create_noise_layer(width, height, scale=2.0)
    scratches = scratches.resize((width, height // 10))
    scratches = scratches.resize((width, height), Image.BICUBIC)
    img = Image.blend(img, scratches.convert('RGB'), 0.1)
    
    # Vignette
    vignette = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(vignette)
    draw.ellipse((50, 50, width-50, height-50), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(150))
    
    # Apply Vignette (darken edges)
    dark_layer = Image.new('RGB', (width, height), (0,0,0))
    img = Image.composite(img, dark_layer, vignette)
    
    if index is not None:
        filename = os.path.join(OUTPUT_DIR, f"void_parchment_{index}.png")
        img.save(filename)
        print(f"Generated {filename}")
    return img

def create_ink_enso(index=None):
    width, height = 800, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = width // 2, height // 2
    radius = 300
    
    # Draw multiple irregular rings to simulate brush bristles
    for _ in range(40):
        points = []
        current_radius = radius + random.randint(-30, 30)
        thickness = random.randint(2, 15)
        
        # Random start and end angle for the "stroke"
        start_angle = random.uniform(0, 2 * math.pi)
        end_angle = start_angle + random.uniform(3, 5) # almost full circle
        
        for angle in np.arange(start_angle, end_angle, 0.05):
            # Add wobble
            r_wobble = current_radius + math.sin(angle * 10) * 5 + random.randint(-2, 2)
            x = center_x + r_wobble * math.cos(angle)
            y = center_y + r_wobble * math.sin(angle)
            points.append((x, y))
            
        if len(points) > 1:
            draw.line(points, fill=(0, 0, 0, random.randint(50, 200)), width=thickness)
            
    # Blur to simulate ink bleed
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    if index is not None:
        filename = os.path.join(OUTPUT_DIR, f"ink_enso_{index}.png")
        img.save(filename)
        print(f"Generated {filename}")
    return img

def create_sigil(index=None):
    width, height = 500, 500
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2
    
    # Random geometric shapes
    color = (212, 197, 176, 255) # Parchment color
    
    # Outer Circle
    if random.random() > 0.3:
        draw.ellipse((50, 50, 450, 450), outline=color, width=3)
    
    # Inner shape (Triangle, Square, Pentagram ish)
    points = []
    num_points = random.randint(3, 7)
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        r = 180
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x,y))
    
    draw.polygon(points, outline=color, width=2)
    
    # Connecting lines
    for p in points:
        draw.line((cx, cy, p[0], p[1]), fill=color, width=1)

    # Random runes/text around
    
    # Add glow effect (manual blur copy)
    glow = img.filter(ImageFilter.GaussianBlur(4))
    final = Image.alpha_composite(glow, img)

    if index is not None:
        filename = os.path.join(OUTPUT_DIR, f"sigil_{index}.png")
        final.save(filename)
        print(f"Generated {filename}")
    return final

def create_giraffe(index=None):
    width, height = 600, 800
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Ink/Parchment colors
    body_color = (212, 197, 176, 255)
    spot_color = (20, 20, 20, 220)
    
    # Coordinates for a stylized giraffe
    # Using lines/polygons to draw a stick-figure-ish but artistic giraffe
    
    # Body
    body_x, body_y = width // 2, height - 200
    
    # Neck (long chaotic line)
    neck_start = (body_x - 50, body_y)
    neck_end = (body_x + 100, body_y - 400)
    
    # Draw Neck
    draw.line([neck_start, neck_end], fill=body_color, width=random.randint(20, 40))
    
    # Head
    head_center = neck_end
    draw.ellipse((head_center[0]-30, head_center[1]-20, head_center[0]+50, head_center[1]+40), fill=body_color)
    
    # Ossicones (Horns)
    draw.line([head_center, (head_center[0], head_center[1]-60)], fill=body_color, width=5)
    draw.line([(head_center[0]+20, head_center[1]), (head_center[0]+20, head_center[1]-60)], fill=body_color, width=5)
    
    # Body block
    draw.rectangle((body_x - 100, body_y, body_x + 100, body_y + 100), fill=body_color)
    
    # Legs (Long)
    leg_width = 15
    draw.line([(body_x - 80, body_y+100), (body_x - 90, height-50)], fill=body_color, width=leg_width)
    draw.line([(body_x + 80, body_y+100), (body_x + 90, height-50)], fill=body_color, width=leg_width)
    
    # Procedural Spots (Ink splatters on the giraffe)
    for _ in range(20):
        spot_x = random.randint(body_x - 100, body_x + 150)
        spot_y = random.randint(body_y - 400, height - 50)
        
        # Only draw if roughly near the "giraffe" (simplified bounding check not perfect, but chaotic is good)
        s_size = random.randint(5, 20)
        draw.ellipse((spot_x, spot_y, spot_x+s_size, spot_y+s_size), fill=spot_color)
        
    # Apply ink bleed effect
    img = img.filter(ImageFilter.GaussianBlur(1))
    
    if index is not None:
        filename = os.path.join(OUTPUT_DIR, f"giraffe_{index}.png")
        img.save(filename)
        print(f"Generated {filename}")
    return img
# Need to import ImageOps which I missed
from PIL import ImageOps

if __name__ == "__main__":
    print("Starting NanoBanana Generator...")
    for i in range(1, 6):
        # create_void_parchment(i)
        # create_ink_enso(i)
        # create_sigil(i)
        create_giraffe(i)
    print("Done! Generator went brrr.")
