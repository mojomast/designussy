# Generator System Architecture

This document describes the modular architecture of the NanoBanana Generator System, designed in Phase 2 (P2-T5) to replace the monolithic `generate_assets.py` with a clean, extensible plugin-based system.

## Overview

The new architecture transforms the monolithic generator functions into a modular, object-oriented system with the following key benefits:

- **Extensibility**: Easy to add new generator types
- **Maintainability**: Clean separation of concerns
- **Testability**: Individual components can be tested independently
- **Configuration**: Centralized configuration management
- **Plugin System**: Dynamic registration and discovery of generators

## Architecture Components

### 1. Base Generator (`base_generator.py`)

The abstract base class that all generators inherit from. Provides:

- **Common initialization** (width, height, seed, configuration)
- **Image utilities** (noise generation, color manipulation, effects)
- **Common methods** (vignette, ink blur, glow, validation)
- **Configuration management** and validation
- **Logging infrastructure** for debugging

```python
class BaseGenerator(ABC):
    def __init__(self, width: int, height: int, seed: Optional[int] = None, **kwargs)
    def generate(self, **kwargs) -> Image.Image  # Abstract
    def get_generator_type(self) -> str  # Abstract
    def save_asset(self, img, category, name, index)
    def create_noise_layer(self, scale: float, opacity: int) -> Image.Image
    def apply_vignette(self, img, intensity: float) -> Image.Image
    # ... more utility methods
```

### 2. Individual Generator Classes

Each generator is now a separate class:

- **`ParchmentGenerator`** - Void parchment textures
- **`EnsoGenerator`** - Ink enso circles  
- **`SigilGenerator`** - Arcane sigils and runes
- **`GiraffeGenerator`** - Ink giraffe creatures
- **`KangarooGenerator`** - Kangaroo on pogo stick
- **`DirectedGenerator`** - LLM-directed asset generation

### 3. Plugin System (`registry.py`)

Dynamic registration and discovery of generators:

```python
class GeneratorRegistry:
    def register(self, name: str, generator_class: Type[BaseGenerator])
    def get_generator_class(self, name: str) -> Optional[Type[BaseGenerator]]
    def create_generator(self, name: str, **kwargs) -> Optional[BaseGenerator]
    def list_generators(self) -> List[str]
```

### 4. Factory Pattern (`factory.py`)

Clean interface for creating generators with validation:

```python
class GeneratorFactory:
    def create_generator(self, generator_type: str, **kwargs) -> BaseGenerator
    def get_default_config(self, generator_type: str) -> Dict[str, Any]
    def validate_generator_config(self, generator_type: str, config: Dict[str, Any])
```

### 5. Configuration System (`config.py`)

Centralized configuration management with validation:

```python
class GeneratorConfig:
    def get_defaults(self, generator_type: str) -> Dict[str, Any]
    def validate_config(self, generator_type: str, config: Dict[str, Any])
    def set_default(self, generator_type: str, config: Dict[str, Any])
```

## How to Create a New Generator

### Step 1: Inherit from BaseGenerator

```python
from generators import BaseGenerator
from PIL import Image, ImageDraw

class MyCustomGenerator(BaseGenerator):
    def __init__(self, width=512, height=512, **kwargs):
        super().__init__(width=width, height=height, **kwargs)
        # Custom initialization
    
    def generate(self, **kwargs) -> Image.Image:
        # Create your asset here
        img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Your generation logic here
        draw.rectangle([10, 10, 100, 100], fill=(255, 0, 0))
        
        return img
    
    def get_generator_type(self) -> str:
        return "my_custom_generator"
```

### Step 2: Add Default Parameters

```python
    def get_default_params(self) -> dict:
        return {
            'width': 512,
            'height': 512,
            'custom_parameter': 'default_value'
        }
```

### Step 3: Register with Plugin System

Update `generators/__init__.py`:

```python
from .my_custom_generator import MyCustomGenerator

# Register your generator
default_registry.register("my_custom", MyCustomGenerator)
```

## Configuration Management

### Default Configuration

Each generator has default parameters defined in the configuration system:

```python
from generators import default_config

# Get defaults for a generator
defaults = default_config.get_defaults("enso")
print(defaults)  # {'width': 800, 'height': 800, 'color': [0, 0, 0, 255], ...}
```

### Environment Variable Overrides

You can override configuration using environment variables:

```bash
# Override enso complexity
export GENERATOR_ENSO_COMPLEXITY=60

# Override parchment noise scale
export GENERATOR_PARCHMENT_NOISE_SCALE=2.0
```

### Custom Configuration

```python
from generators import default_factory

# Create with custom config
generator = default_factory.create_generator(
    "enso", 
    width=1024, 
    height=1024, 
    complexity=50,
    chaos=1.5
)
```

## Usage Examples

### Basic Usage

```python
from generators import get_generator

# Create generator instance
generator = get_generator("enso", width=800, height=800)

# Generate asset
img = generator.generate()

# Save asset
generator.save_with_index(1)
```

### Using the Factory

```python
from generators import default_factory

# Create with factory
generator = default_factory.create_generator_with_defaults(
    "parchment",
    override_defaults={"noise_scale": 2.0, "width": 2048}
)

img = generator.generate()
```

### Batch Generation

```python
# Generate multiple variations
for i in range(5):
    generator = get_generator("sigil", seed=i)  # Deterministic with seed
    img = generator.generate()
    generator.save_with_index(i)
```

### LLM-Directed Generation

```python
from generators import default_factory

# Create directed generator
directed_gen = default_factory.create_generator("directed", generator_type="enso")

# Generate from prompt
img = directed_gen.generate(
    prompt="Burning rage and chaos",
    model="gpt-4o",
    api_key="your-api-key"
)
```

## Migration Guide

### From Old Functions

Old way:
```python
from generate_assets import create_ink_enso, create_sigil

img = create_ink_enso(index=None)
img = create_sigil(index=None)
```

New way:
```python
from generators import get_generator

# Option 1: Direct replacement
enso_gen = get_generator("enso")
sigil_gen = get_generator("sigil")
img = enso_gen.generate()
img = sigil_gen.generate()

# Option 2: Factory with defaults
from generators import default_factory
enso_gen = default_factory.create_generator_with_defaults("enso")
img = enso_gen.generate()
```

### Backend API Compatibility

The new system maintains full backward compatibility. Existing API endpoints continue to work:

```python
# This still works exactly the same
@app.get("/generate/enso")
def get_enso():
    img = create_ink_enso(index=None)  # Still uses old function
    return serve_pil_image(img)
```

But you can also use the new modular system:

```python
from generators import get_generator

@app.get("/generate/enso") 
def get_enso():
    generator = get_generator("enso")
    img = generator.generate()
    return serve_pil_image(img)
```

## Performance Considerations

### Caching

The factory includes built-in caching for generator instances:

```python
from generators import default_factory

# First call - creates instance
gen1 = default_factory.create_generator("enso")

# Second call - may return cached instance (if config allows)
gen2 = default_factory.create_generator("enso")  

# Cache stats
stats = default_factory.get_cache_stats()
print(f"Cached generators: {stats['cached_generators']}")
```

### Generator Instance Reuse

Reuse generator instances when generating multiple assets:

```python
# Efficient - reuses same generator instance
generator = get_generator("enso", width=1024, height=1024)

for i in range(10):
    img = generator.generate()  # No new instance needed
    generator.save_asset(img, "glyphs", "enso", i)

# Inefficient - creates new instance each time
for i in range(10):
    generator = get_generator("enso", width=1024, height=1024)  # New instance!
    img = generator.generate()
```

## Testing

The modular architecture makes testing much easier:

```python
import unittest
from generators import ParchmentGenerator

class TestParchmentGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ParchmentGenerator(width=100, height=100)
    
    def test_generation(self):
        img = self.generator.generate()
        self.assertEqual(img.size, (100, 100))
        self.assertEqual(img.mode, 'RGB')
    
    def test_saving(self):
        filepath = self.generator.save_with_index(1)
        self.assertTrue(os.path.exists(filepath))
    
    def test_config_validation(self):
        from generators import default_factory
        config = {"width": 100, "height": 100, "invalid_param": "value"}
        validation = default_factory.validate_generator_config("parchment", config)
        self.assertTrue(len(validation['warnings']) > 0)

if __name__ == '__main__':
    unittest.main()
```

## Best Practices

### 1. Always Use the Factory

```python
# Good
from generators import default_factory
generator = default_factory.create_generator_with_defaults("enso")

# Avoid
from generators import EnsoGenerator
generator = EnsoGenerator()  # Bypasses validation and config
```

### 2. Validate Configuration

```python
from generators import default_factory

config = {"width": 5000, "height": 5000}  # Too large!
validation = default_factory.validate_generator_config("enso", config)

if not validation['valid']:
    print("Config errors:", validation['errors'])
```

### 3. Use Seeds for Reproducibility

```python
# Reproducible generation
for i in range(5):
    generator = get_generator("giraffe", seed=42)  # Same results each time
    img = generator.generate()
```

### 4. Leverage Configuration System

```python
# Set custom defaults
from generators import default_config

custom_defaults = {
    "width": 2048,
    "height": 2048,
    "quality": "high"
}
default_config.set_default("parchment", custom_defaults)
```

## Troubleshooting

### Common Issues

**Generator not found:**
```python
from generators import list_generators
print("Available generators:", list_generators())
```

**Configuration validation errors:**
```python
from generators import default_factory
validation = default_factory.validate_generator_config("unknown_gen", {})
print(validation['errors'])
```

**LLM Director not available:**
```python
from generators import DirectedGenerator
try:
    directed_gen = DirectedGenerator()
    print("LLM Director available")
except RuntimeError as e:
    print(f"LLM Director not available: {e}")
```

## Future Extensions

The modular architecture supports several future enhancements:

### 1. Generator Categories
Group generators by type (backgrounds, creatures, etc.)

### 2. Generator Pipelines  
Combine multiple generators in sequence

### 3. Real-time Configuration
Update generator parameters during generation

### 4. Distributed Generation
Split generation across multiple processes/machines

### 5. Custom Post-Processing
Add custom filter chains to generators

### 6. Generator Dependencies
Allow generators to depend on other generators

## Conclusion

The new modular architecture provides a solid foundation for the NanoBanana Generator System's future growth. It maintains full backward compatibility while introducing modern software engineering practices that make the system more maintainable, testable, and extensible.

The plugin system allows developers to easily add new generator types, while the factory and configuration systems provide clean interfaces for managing generator instances and their settings. This architecture will serve the system well as it evolves and grows more complex.