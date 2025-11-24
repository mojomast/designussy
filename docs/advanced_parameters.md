# Advanced Generation Parameters API Documentation

## Overview

The Advanced Generation Parameters API extends the NanoBanana Generator system with fine-grained control over asset generation. This system provides users with unprecedented creative control through quality controls, color palettes, style presets, and comprehensive parameter validation.

## Key Features

### 🎯 Fine-Grained Control
- **Quality Levels**: `low`, `medium`, `high`, `ultra`
- **Resolution Multipliers**: 0.5x to 4.0x
- **Style Presets**: `minimal`, `detailed`, `chaotic`, `ordered`
- **Color Management**: Custom palettes, contrast, brightness, saturation

### 🎨 Creative Tools
- **Color Palettes**: Custom hex color arrays
- **Style Transfer**: Preset-based consistent styling
- **Parameter Validation**: Comprehensive validation with suggestions
- **Backward Compatibility**: Legacy parameters still work

### ⚡ Performance Optimization
- **Progressive Enhancement**: Quality affects processing appropriately
- **Caching**: Advanced parameter combinations cached
- **Rate Limiting**: Configurable limits per endpoint
- **Resource Management**: Memory and CPU efficient

## API Endpoints

### Advanced Generation Endpoints

#### POST `/generate/advanced/parchment`
Generate parchment with advanced parameters.

**Request Body:**
```json
{
    "asset_type": "parchment",
    "parameters": {
        "width": 1024,
        "height": 1024,
        "quality": "high",
        "style_preset": "minimal",
        "complexity": 0.8,
        "randomness": 0.3,
        "color_palette": ["#2a2520", "#3a2f25", "#2a2520"],
        "contrast": 1.2,
        "brightness": 1.0,
        "saturation": 0.8
    }
}
```

#### POST `/generate/advanced/enso`
Generate enso circles with advanced brush and style parameters.

**Request Body:**
```json
{
    "asset_type": "enso",
    "parameters": {
        "width": 800,
        "height": 800,
        "quality": "ultra",
        "style_preset": "chaotic",
        "complexity": 0.9,
        "randomness": 0.95,
        "base_color": "#8b0000",
        "resolution_multiplier": 2.0
    }
}
```

#### POST `/generate/advanced/{asset_type}`
Universal endpoint for advanced generation of any asset type.

**Available Asset Types:**
- `parchment` - Void parchment textures
- `enso` - Ink enso circles  
- `sigil` - Arcane sigils
- `giraffe` - Ink giraffe entities
- `kangaroo` - Kangaroo on pogo stick

### Preset System Endpoints

#### POST `/generate/preset/{preset_name}`
Generate assets using predefined parameter sets.

**Example Request:**
```bash
POST /generate/preset/parchment_ancient?asset_type=parchment
```

**Available Presets:**
- **Style Presets**: `minimal`, `detailed`, `chaotic`, `ordered`
- **Quality Presets**: `ultra_hd`, `fast_generation`, `balanced`
- **Asset-Specific**: `parchment_ancient`, `enso_meditative`, `sigil_geometric`
- **Resolution**: `web_optimized`, `print_ready`, `mobile_friendly`
- **Mood**: `noir`, `vibrant`, `soft`

#### GET `/presets`
Get all available presets organized by category.

**Response:**
```json
{
    "status": "success",
    "presets": {
        "style": [
            {
                "name": "minimal",
                "category": "style",
                "description": "Minimal style with low quality",
                "parameters": {
                    "complexity": 0.2,
                    "quality": "low"
                }
            }
        ],
        "asset_specific": [...]
    },
    "total_presets": 25,
    "timestamp": "2025-11-24T21:54:30.000Z"
}
```

### Utility Endpoints

#### POST `/validate/parameters`
Validate generation parameters before use.

**Request Body:**
```json
{
    "width": 2048,
    "height": 2048,
    "quality": "ultra",
    "complexity": 1.5,
    "color_palette": ["#FF0000", "#00FF00", "#0000FF"]
}
```

**Response:**
```json
{
    "status": "success",
    "is_valid": false,
    "errors": ["Complexity must be between 0.0 and 1.0"],
    "warnings": ["High resolution may impact performance"],
    "suggestions": ["Consider using resolution_multiplier instead of direct dimensions"],
    "effective_dimensions": [2048, 2048],
    "quality_settings": {...},
    "style_settings": {...}
}
```

#### GET `/color-palettes`
Get available color palettes and utilities.

**Response:**
```json
{
    "status": "success",
    "presets": ["void_black", "eldritch", "ink", "parchment"],
    "utilities": {
        "complementary": "Generate complementary color palettes",
        "analogous": "Generate analogous color palettes",
        "monochromatic": "Generate monochromatic palettes",
        "triadic": "Generate triadic color schemes"
    }
}
```

## Parameter Reference

### GenerationParameters Schema

```python
class GenerationParameters(BaseModel):
    # Basic Parameters
    width: int = Field(512, ge=64, le=2048)
    height: int = Field(512, ge=64, le=2048)
    seed: Optional[int] = None
    
    # Quality Parameters
    quality: Literal["low", "medium", "high", "ultra"] = "medium"
    resolution_multiplier: float = Field(1.0, ge=0.5, le=4.0)
    anti_aliasing: bool = True
    
    # Color Parameters
    color_palette: Optional[List[str]] = None
    base_color: Optional[str] = None
    contrast: float = Field(1.0, ge=0.1, le=3.0)
    brightness: float = Field(1.0, ge=0.1, le=3.0)
    saturation: float = Field(1.0, ge=0.0, le=3.0)
    
    # Style Parameters
    style_preset: Optional[Literal["minimal", "detailed", "chaotic", "ordered"]] = None
    complexity: float = Field(0.5, ge=0.0, le=1.0)
    randomness: float = Field(0.5, ge=0.0, le=1.0)
    
    # Output Parameters
    format: Literal["png", "jpg", "webp"] = "png"
    compression: int = Field(95, ge=1, le=100)
```

### Parameter Details

#### Quality Levels

| Level | Description | Processing Time | Use Case |
|-------|-------------|----------------|----------|
| `low` | Basic generation with minimal processing | ~1x | Preview, Web thumbnails |
| `medium` | Balanced quality and speed | ~1.5x | General purpose |
| `high` | Enhanced detail and processing | ~2x | High-quality assets |
| `ultra` | Maximum quality with multiple passes | ~3x | Print-ready, detailed work |

#### Style Presets

| Preset | Characteristics | Best For |
|--------|----------------|----------|
| `minimal` | Clean, simple, low detail | Clean UI, minimal design |
| `detailed` | Rich textures, balanced complexity | General artistic assets |
| `chaotic` | High randomness, organic variation | Creative, expressive assets |
| `ordered` | Geometric precision, low randomness | Technical diagrams, logos |

#### Color Parameters

- **color_palette**: Array of hex colors for themed generation
- **base_color**: Single hex color as base for generation
- **contrast**: 0.1-3.0, affects color contrast
- **brightness**: 0.1-3.0, affects overall brightness
- **saturation**: 0.0-3.0, affects color saturation

#### Resolution Control

- **width/height**: Direct pixel dimensions (64-2048)
- **resolution_multiplier**: 0.5-4.0, scales base resolution
- **Effective Resolution**: `min(2048, base_resolution * multiplier)`

## Usage Examples

### Basic Advanced Generation

```javascript
// Generate high-quality parchment with custom styling
const response = await fetch('/generate/advanced/parchment', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        asset_type: 'parchment',
        parameters: {
            width: 1024,
            height: 1024,
            quality: 'high',
            style_preset: 'minimal',
            complexity: 0.3,
            randomness: 0.2,
            base_color: '#d4c5b0',
            contrast: 0.9,
            brightness: 1.1
        }
    })
});

const blob = await response.blob();
const img = URL.createObjectURL(blob);
```

### Preset-Based Generation

```javascript
// Generate enso using a predefined preset
const response = await fetch('/generate/preset/enso_meditative?asset_type=enso');
const blob = await response.blob();
```

### Parameter Validation

```javascript
// Validate parameters before generation
const validationResponse = await fetch('/validate/parameters', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        width: 2048,
        height: 2048,
        quality: 'ultra',
        complexity: 0.8,
        color_palette: ['#FF0000', '#00FF00']
    })
});

const validation = await validationResponse.json();
if (!validation.is_valid) {
    console.error('Parameter errors:', validation.errors);
    console.warn('Warnings:', validation.warnings);
}
```

### Custom Color Palette

```javascript
// Generate with custom color scheme
const response = await fetch('/generate/advanced/enso', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        asset_type: 'enso',
        parameters: {
            quality: 'high',
            style_preset: 'chaotic',
            color_palette: ['#8b0000', '#a52a2a', '#cd5c5c', '#dc143c'],
            complexity: 0.8,
            randomness: 0.9,
            saturation: 1.5
        }
    })
});
```

## Best Practices

### Performance Optimization

1. **Choose Appropriate Quality Levels**
   - Use `low` for previews and web thumbnails
   - Use `medium` for general purpose generation
   - Use `high` or `ultra` only when needed

2. **Efficient Resolution Usage**
   - Use `resolution_multiplier` instead of direct dimensions when possible
   - Consider 512x512 for web use, 1024x1024 for general use

3. **Caching Strategy**
   - Advanced parameter combinations are automatically cached
   - Use consistent parameters for batch generation

### Creative Guidelines

1. **Color Palette Design**
   - Use 3-5 colors for best results
   - Ensure good contrast between palette colors
   - Consider color harmony when selecting palettes

2. **Style Preset Selection**
   - `minimal`: Clean, professional assets
   - `detailed`: Rich, textured results
   - `chaotic`: Organic, expressive styles
   - `ordered`: Geometric, precise outputs

3. **Parameter Balance**
   - High complexity + low randomness = detailed but controlled
   - Low complexity + high randomness = simple but organic
   - Medium settings provide balanced results

### Error Handling

Always handle the validation response:

```javascript
const validation = await response.json();
if (!validation.is_valid) {
    // Handle errors
    validation.errors.forEach(error => console.error(error));
    
    // Consider warnings
    validation.warnings.forEach(warning => console.warn(warning));
    
    // Apply suggestions if desired
    validation.suggestions.forEach(suggestion => {
        console.info('Suggestion:', suggestion);
    });
}
```

## Rate Limits and Security

### Rate Limits
- Advanced generation endpoints: 10 requests/minute
- Preset generation: 20 requests/minute  
- Parameter validation: 60 requests/minute
- Preset listing: 60 requests/minute

### Parameter Limits
- Maximum resolution: 2048x2048 pixels
- Maximum color palette: 10 colors
- Complexity range: 0.0 to 1.0
- Randomness range: 0.0 to 1.0
- Adjustment factors: 0.1 to 3.0

## Configuration

Environment variables for advanced parameters (see `.env.example`):

```bash
# Resolution limits
MAX_RESOLUTION=2048
MIN_RESOLUTION=64

# Quality defaults
DEFAULT_QUALITY=medium
DEFAULT_STYLE_PRESET=detailed

# Palette settings
MAX_COLORS_IN_PALETTE=10
ALLOW_CUSTOM_PALETTES=true

# Rate limiting
ADVANCED_GENERATION_RATE_LIMIT=10
PRESET_RATE_LIMIT=20
VALIDATION_RATE_LIMIT=60

# Caching
ENABLE_ADVANCED_CACHING=true
ADVANCED_CACHE_SIZE=1000
```

## Migration from Legacy API

The advanced parameters API maintains full backward compatibility:

```javascript
// Legacy approach still works
const response = await fetch('/generate/parchment');

// New advanced approach
const response = await fetch('/generate/advanced/parchment', {
    method: 'POST',
    body: JSON.stringify({
        asset_type: 'parchment',
        // Legacy parameters can be passed as overrides
        width: 512,
        height: 512,
        seed: 42
    })
});
```

## Troubleshooting

### Common Issues

1. **"Invalid hex color format"**
   - Ensure colors are in format `#RRGGBB`
   - Use full 6-character hex codes

2. **"High resolution may impact performance"**
   - Consider using `resolution_multiplier` instead
   - Use lower quality settings for large resolutions

3. **"Preset not found"**
   - Check available presets with `/presets` endpoint
   - Verify preset name spelling

4. **"Parameter validation failed"**
   - Check parameter ranges in schema
   - Use `/validate/parameters` endpoint for debugging

### Performance Tips

1. **Batch Generation**: Use the batch endpoints for multiple assets
2. **Parameter Consistency**: Cache frequently used parameter combinations
3. **Quality Selection**: Start with medium quality, upgrade as needed
4. **Progressive Enhancement**: Use lower settings for previews, higher for final assets

## API Reference Summary

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/generate/advanced/{asset}` | POST | Advanced generation | 10/min |
| `/generate/preset/{name}` | POST | Preset-based generation | 20/min |
| `/presets` | GET | List available presets | 60/min |
| `/validate/parameters` | POST | Validate parameters | 60/min |
| `/color-palettes` | GET | List color utilities | 60/min |

For complete API documentation, visit `/docs` when the server is running.