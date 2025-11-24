# 🍌 NanoBanana Protocol - Unwritten Worlds

> *To the Agents who follow: Welcome to the Void. Here we do not write code; we unwrite reality.*

[![Status](https://img.shields.io/badge/Phase-P3%20Features%20%26%20UX-orange)](docs/phases/phase3.yaml)
[![Progress](https://img.shields.io/badge/Progress-70%25%20Complete-brightgreen)](HANDOFF.md)
[![Tests](https://img.shields.io/badge/Tests-87%25%20Passing-green)](tests/)
[![License](https://img.shields.io/badge/License-MIT-black)](LICENSE)

A procedural generation engine for creating eldritch, ink-stained assets through pure code. No external images required—just mathematics, chaos, and the void.

## 🌑 The Aesthetic

**Unwritten Worlds** embraces a specific design language:

- **Keywords**: Eldritch, Ink-stained, Ouroboros, Parchment, Void, Decay, Ephemeral
- **Colors**: Void Black (#0a0a0a), Bone Parchment (#d4c5b0), Deep Ink (#000000), Ghost Grey (#333333)
- **Typography**: Cinzel (headers), Cormorant Garamond (body), Special Elite (code)

## ✨ Features

### 🎨 Asset Generation
- **Procedural Assets**: Generate unique textures, glyphs, and creatures from pure code
- **Modular Generators**: Plugin-based architecture with 5+ generator types
- **Advanced Parameters**: Fine-grained control over quality, complexity, and chaos
- **Preset System**: 23+ predefined configurations for quick generation

### 🔄 Interactive Preview System
- **Real-time Editing**: See instant visual feedback as you adjust parameters
- **Live Preview**: WebSocket-based updates with auto-generation queue
- **Zoom & Pan**: Interactive canvas navigation with mouse and touch support
- **Undo/Redo**: Unlimited history tracking (50 states)
- **Full-screen Editor**: Distraction-free creative workspace

### 📦 Asset Management
- **Metadata System**: SQLite-backed asset tracking with full search capabilities
- **Version Control**: Track asset evolution with complete version history
- **Tagging System**: Organize assets with intelligent tag suggestions
- **Export Options**: PNG, JPG, SVG, and JSON formats with resolution presets

### 🎭 Theme System
- **Default (Eldritch)**: Classic void and parchment aesthetic
- **Dark**: High-contrast dark mode
- **Minimal**: Clean, distraction-free interface
- **Chaotic**: Wild, unpredictable styling

### ⚡ Performance
- **Caching Layer**: LRU cache with <50ms response times
- **Batch Processing**: Generate multiple assets simultaneously
- **Optimized Generators**: Fast-path implementations for high-performance
- **WebSocket Support**: Real-time communication for live previews

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend development)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nanobanana.git
cd nanobanana

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (if developing frontend)
npm install
```

### Running the Backend

```bash
# Start the API server
python backend.py

# Server runs on http://localhost:8001
# API documentation available at http://localhost:8001/docs
```

### Using the Interactive Editor

```bash
# Open the interactive demo
open unwritten_worlds_interactive_demo.html

# Or use the full editor
open unwritten_worlds_editor.html
```

### Basic Usage

```javascript
// Import the AssetEditor component
import AssetEditor from './frontend/components/react/AssetEditor.jsx';

// Create an editor instance
function MyEditor() {
  return (
    <AssetEditor
      generatorType="enso"
      initialParameters={{ chaos: 0.5, complexity: 3 }}
      enableLivePreview={true}
      theme="dark"
      onSave={(asset) => {
        console.log('Asset saved:', asset);
      }}
    />
  );
}
```

## 📚 Documentation

- **[Interactive Preview System](docs/interactive_preview_system.md)** - Complete guide to the real-time editing system
- **[Asset Structure](docs/asset_structure.md)** - Understanding generated assets
- **[Generator Development](docs/generators.md)** - Creating custom generators
- **[API Reference](docs/batch_api.md)** - Complete API documentation
- **[Phase Progress](docs/phases/)** - Development roadmap and status
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project

## 🎯 Current Status

### Phase 3: Features & UX Enhancement (70% Complete)

| Task | Description | Status |
|------|-------------|--------|
| P3-T1 | Advanced generation parameters | ✅ Completed |
| P3-T2 | Asset versioning and metadata | ✅ Completed |
| P3-T3 | Frontend component library | ✅ Completed |
| P3-T4 | Interactive preview and editing | ✅ Completed |
| P3-T5 | Multi-format export | 🔄 In Progress |
| P3-T6 | Production deployment | ⏳ Pending |
| P3-T7 | Monitoring and analytics | ⏳ Pending |
| P3-T8 | Comprehensive documentation | 🔄 In Progress |

**Latest Achievement**: Interactive preview system with real-time WebSocket updates, unlimited undo/redo, and full-screen editing interface.

## 🏗️ Architecture

### Backend (Python)
- **FastAPI**: High-performance async API framework
- **Pillow + Numpy**: Image generation and manipulation
- **SQLite**: Metadata storage and versioning
- **WebSocket**: Real-time communication for live previews

### Frontend (React/JavaScript)
- **React Components**: Modular, reusable UI components
- **WebSocket Client**: Real-time preview updates
- **CSS Variables**: Theme-based styling system
- **Responsive Design**: Mobile-first approach

### Key Components

```
┌─────────────────────────────────────────────────────┐
│                   AssetEditor                       │
│  ┌───────────────────────────────────────────────┐  │
│  │  PreviewCanvas (Real-time rendering)          │  │
│  │  - Zoom/Pan controls                          │  │
│  │  - Auto-generation queue                      │  │
│  │  - Loading states                             │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │  ParameterControls (Interactive inputs)       │  │
│  │  - Real-time validation                       │  │
│  │  - Category grouping                          │  │
│  │  - Error handling                             │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │  LivePreviewManager (WebSocket client)        │  │
│  │  - Connection management                      │  │
│  │  - Message queuing                            │  │
│  │  - Automatic reconnection                     │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 🎨 Available Generators

### Core Generators
- **Parchment**: Void parchment textures with heavy grain
- **Enso**: Ink enso circles with chaotic brush strokes
- **Sigil**: Arcane geometric sigils with glow effects
- **Giraffe**: Eldritch ink giraffe entities
- **Kangaroo**: Ink kangaroo on pogo stick

### Advanced Features
- **Directed Generation**: LLM-guided parameter selection
- **Batch Processing**: Generate multiple assets at once
- **Preset Configurations**: 23+ predefined parameter sets
- **Custom Color Palettes**: Advanced color scheme support

## 🔧 Development

### Project Structure

```
nanobanana/
├── backend.py                 # Main API server
├── generators/                # Modular generator system
│   ├── enso_generator.py
│   ├── sigil_generator.py
│   ├── parchment_generator.py
│   └── factory.py
├── frontend/                  # React components
│   ├── components/
│   │   └── react/
│   │       ├── AssetEditor.jsx
│   │       ├── PreviewCanvas.jsx
│   │       └── ParameterControls.jsx
│   ├── utils/
│   │   └── LivePreviewManager.js
│   └── styles/
│       └── preview-system.css
├── storage/                   # Metadata and versioning
│   ├── asset_storage.py
│   ├── metadata_schema.py
│   └── versioning.py
├── tests/                     # Comprehensive test suite
├── docs/                      # Documentation
└── assets/                    # Generated assets
```

### Adding a New Generator

1. Create generator class in `generators/`
2. Implement `BaseGenerator` interface
3. Register in `generators/factory.py`
4. Add parameter schema
5. Write tests in `tests/test_generators/`

Example:
```python
from generators.base_generator import BaseGenerator

class MyGenerator(BaseGenerator):
    def generate(self, **parameters):
        # Your generation logic here
        return image
    
    def validate_parameters(self, parameters):
        # Validation logic
        return validation_result
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_generators/
pytest tests/e2e/

# Run with coverage
pytest --cov=generators --cov=storage
```

## 🌐 API Endpoints

### Core Generation
- `GET /generate/{type}` - Generate single asset
- `POST /generate/advanced/{type}` - Advanced generation with parameters
- `POST /generate/batch` - Batch generation
- `GET /generate/batch/{job_id}/status` - Batch job status

### Interactive Preview
- `WS /ws/preview` - WebSocket for real-time previews
- `POST /generate/preset/{name}` - Generate with preset

### Asset Management
- `GET /assets` - List assets with search
- `GET /assets/{id}` - Get asset metadata
- `POST /assets/{id}/tags` - Add tags to asset
- `PUT /assets/{id}/metadata` - Update metadata

### System
- `GET /health` - Health check
- `GET /generators` - List available generators
- `GET /presets` - List available presets
- `GET /cache/stats` - Cache statistics

## 🎯 Performance Metrics

- **Cache Hit Rate**: >90%
- **Response Time**: <50ms (cached), <2s (generation)
- **Batch Processing**: Up to 100 assets/minute
- **WebSocket Latency**: <100ms
- **Memory Usage**: <500MB (typical)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style

- Python: Black formatting, PEP 8 guidelines
- JavaScript: ESLint with Prettier
- React: Functional components with hooks
- Documentation: Markdown with clear examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Pillow**: Python imaging library
- **FastAPI**: Modern Python web framework
- **React**: JavaScript UI library
- **Numpy**: Numerical computing
- **Cinzel & Cormorant Garamond**: Beautiful typography from Google Fonts

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/nanobanana/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/nanobanana/discussions)
- **Documentation**: [docs/](docs/)

## 🗺️ Roadmap

### Phase 3 (Current)
- ✅ Advanced parameters and presets
- ✅ Asset versioning and metadata
- ✅ Frontend component library
- ✅ Interactive preview system
- 🔄 Multi-format export
- ⏳ Production deployment
- ⏳ Monitoring and analytics

### Future Phases
- Phase 4: Advanced features (AI integration, advanced filters)
- Phase 5: Scaling and optimization
- Phase 6: Community features and marketplace

---

**Made with 🍌 and void magic**

*"In the beginning, there was nothing. And then we added parameters."*