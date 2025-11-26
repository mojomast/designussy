# Voidussy Assets - Quick Start Guide

## 📦 What's Available

**200+ visual assets** across 4 categories:
- **Backgrounds** (5 types × 20 variants = 100 files)
- **Glyphs** (9 types × 20 variants = 180 files)  
- **Creatures** (8 types, 141 files total)
- **UI Elements** (6 types × 20 variants = 120 files)

## 🚀 How to Use

### 1. Include the Asset Registry

```html
<script src="assets/js/unwritten_worlds_assets.js"></script>
```

### 2. Access Assets

```javascript
// Get a specific asset
const path = UnwrittenAssets.getPath('glyphs', 'void_rune', 5);
// Returns: "assets/static/elements/glyphs/void_rune_5.png"

// Get a random variant
const randomPath = UnwrittenAssets.getRandom('creatures', 'void_hopper');

// Get all variants
const allPaths = UnwrittenAssets.getAllVariants('backgrounds', 'ink_nebula');
// Returns array of 20 paths

// Preload an asset
const img = await UnwrittenAssets.preload('ui', 'void_orb', 3);
```

### 3. Browse Available Assets

Open `new_assets_demo.html` in your browser to see all assets with:
- Interactive preview of all 200+ assets
- Randomize button to cycle through variants
- Preload functionality for performance

## 📁 File Structure

```
assets/static/elements/
├── backgrounds/
│   ├── void_parchment_1.png ... void_parchment_20.png
│   ├── ink_nebula_1.png ... ink_nebula_20.png
│   ├── ethereal_mist_1.png ... ethereal_mist_20.png
│   ├── floating_island_1.png ... floating_island_20.png
│   └── void_crystal_1.png ... void_crystal_20.png
├── glyphs/
│   ├── void_rune_1.png ... void_rune_20.png
│   ├── ink_spiral_1.png ... ink_spiral_20.png
│   ├── ethereal_feather_1.png ... ethereal_feather_20.png
│   ├── astral_eye_1.png ... astral_eye_20.png
│   ├── void_circuit_1.png ... void_circuit_20.png
│   ├── ink_enso_1.png ... ink_enso_20.png
│   ├── sigil_1.png ... sigil_20.png
│   ├── mystic_eye_1.png ... mystic_eye_20.png
│   └── rune_stone_1.png ... rune_stone_20.png
├── creatures/
│   ├── void_manta_1.png ... void_manta_20.png
│   ├── spectral_serpent_1.png ... spectral_serpent_20.png
│   ├── void_hopper_1.png ... void_hopper_20.png
│   ├── abyssal_jelly_1.png ... abyssal_jelly_20.png
│   ├── ink_crab_1.png ... ink_crab_20.png
│   ├── giraffe_1.png ... giraffe_20.png
│   ├── kangaroo_1.png ... kangaroo_20.png
│   └── void_serpent_1.png (AI-generated)
└── ui/
    ├── void_orb_1.png ... void_orb_20.png
    ├── broken_chain_1.png ... broken_chain_20.png
    ├── ink_splatter_1.png ... ink_splatter_20.png
    ├── mystic_frame_1.png ... mystic_frame_20.png
    ├── ancient_key_1.png ... ancient_key_20.png
    └── ink_divider_1.png ... ink_divider_20.png
```

## 🎇 Effects & Sprite Sheets

Located in `assets/static/effects/`:
- `void_runes_sheet.png`: Sprite sheet of 9 ancient magical runes.
- `ink_creatures_sheet.png`: Sprite sheet of 6 void creatures.
- `mystic_ui_sheet.png`: Sprite sheet of dark fantasy UI elements.

## 🎨 New Asset Types

### Glyphs
- **Void Rune** - Glowing sigil with purple void-energy swirls
- **Ink Spiral** - Tight spiral with splatter accents
- **Ethereal Feather** - Translucent feather made of ink strokes
- **Astral Eye** - Mystic eye with nebula pupil
- **Void Circuit** - Circuit pattern with dark-purple glow

### Creatures
- **Spectral Serpent** - Vapor-like serpentine form
- **Void Hopper** - Small hopper with glowing core
- **Abyssal Jelly** - Floating jellyfish with tentacles

### Backgrounds
- **Ink Nebula** - Swirling ink clouds
- **Ethereal Mist** - Soft mist overlay

## 💡 Usage Examples

### As Background
```html
<div style="background-image: url('assets/static/elements/backgrounds/ink_nebula_1.png');">
    Content here
</div>
```

### As Overlay
```javascript
const overlay = document.createElement('img');
overlay.src = UnwrittenAssets.getRandom('ui', 'ink_splatter');
overlay.style.position = 'absolute';
overlay.style.mixBlendMode = 'multiply';
document.body.appendChild(overlay);
```

### Dynamic Loading
```javascript
// Cycle through variants
let index = 1;
setInterval(() => {
    img.src = UnwrittenAssets.getPath('glyphs', 'void_rune', index);
    index = (index % 20) + 1;
}, 1000);
```

## 📝 Notes

- All assets follow the Voidussy design language (deep purples, ethereal effects, dark fantasy)
- Assets are PNG format with transparency where applicable
- File sizes range from 3KB (simple UI) to 1.5MB (high-res textures)
- 5 AI-generated assets have been restored: void_parchment_3, ink_enso_3, void_serpent_1, ink_divider_3, void_orb_2
