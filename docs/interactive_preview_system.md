# Interactive Preview System - Implementation Guide

## Overview

The Interactive Preview System (P3-T4) provides real-time asset generation with live parameter adjustment, enabling users to see instant visual feedback as they modify generation parameters. This system dramatically improves the creative workflow and user experience.

## Components Implemented

### 1. PreviewCanvas Component
**Location**: `frontend/components/react/PreviewCanvas.jsx`

A React component that provides real-time asset rendering with the following features:

- **Live Preview Rendering**: Displays generated assets with smooth loading states
- **Interactive Navigation**: 
  - Zoom in/out with mouse wheel or buttons
  - Pan by clicking and dragging
  - Reset to default view
- **Auto-generation Queue**: Debounced parameter updates prevent overwhelming the server
- **Loading States**: Visual feedback during generation
- **Error Handling**: Clear error messages with retry options
- **Responsive Design**: Works on all screen sizes

**Key Features**:
```javascript
// Auto-generate mode
<PreviewCanvas
  asset={currentAsset}
  parameters={parameters}
  onGenerate={handleGenerate}
  autoGenerate={true}  // Enables live preview
/>

// Manual mode
<PreviewCanvas
  asset={currentAsset}
  parameters={parameters}
  onGenerate={handleGenerate}
  autoGenerate={false}  // Manual generation only
/>
```

### 2. LivePreviewManager
**Location**: `frontend/utils/LivePreviewManager.js`

A WebSocket-based manager that handles real-time preview updates:

- **WebSocket Connection**: Maintains persistent connection to backend
- **Automatic Reconnection**: Exponential backoff with configurable retry limits
- **Heartbeat Monitoring**: Keeps connection alive and detects failures
- **Message Queuing**: Reliable message delivery even during disconnection
- **Preview Request Management**: Handles multiple concurrent preview requests
- **Progress Tracking**: Real-time generation progress updates

**Usage Example**:
```javascript
const previewManager = new LivePreviewManager({
  endpoint: 'ws://localhost:8001/ws/preview',
  onPreviewUpdate: (update) => {
    switch (update.type) {
      case 'complete':
        setCurrentAsset(update.assetUrl);
        break;
      case 'progress':
        console.log(`Progress: ${update.progress}%`);
        break;
      case 'error':
        setError(update.error);
        break;
    }
  },
  onStatusChange: (status) => {
    console.log('Connection status:', status);
  }
});

// Connect
await previewManager.connect();

// Request preview
previewManager.requestPreview(parameters, 'enso', {
  quality: 'preview',
  priority: 'high'
});

// Disconnect when done
previewManager.disconnect();
```

### 3. AssetEditor Component
**Location**: `frontend/components/react/AssetEditor.jsx`

A full-screen editing interface that brings everything together:

- **Full-screen Editing**: Distraction-free workspace
- **Parameter Controls**: Integrated parameter adjustment panel
- **History Management**: Unlimited undo/redo functionality
- **Preset System**: Save and load parameter configurations
- **Live Preview Toggle**: Enable/disable real-time updates
- **Export Options**: Multiple format support (PNG, JPG, SVG, JSON)
- **Theme Support**: All four aesthetic themes
- **Responsive Layout**: Adapts to different screen sizes

**Features**:
- Real-time parameter validation
- Parameter history tracking (undo/redo)
- Preset loading and management
- Fullscreen mode
- Connection status indicators
- Error handling and display
- Keyboard shortcuts support

**Usage Example**:
```javascript
<AssetEditor
  generatorType="enso"
  initialParameters={{ chaos: 0.5, complexity: 3 }}
  schema={parameterSchema}
  enableLivePreview={true}
  theme="dark"
  onSave={(asset) => {
    console.log('Asset saved:', asset);
  }}
  onExport={(exportData) => {
    console.log('Exporting:', exportData);
  }}
  onClose={() => {
    console.log('Editor closed');
  }}
/>
```

### 4. Preview System Styles
**Location**: `frontend/styles/preview-system.css`

Comprehensive CSS for the entire preview system:

- **CSS Variables**: Theme-based styling system
- **Component Styles**: All interactive elements styled
- **Animation System**: Smooth transitions and loading states
- **Responsive Design**: Mobile-first approach
- **Theme Variants**: Default, Dark, Minimal, Chaotic
- **Accessibility**: High contrast and keyboard navigation

## Architecture

### Frontend Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AssetEditor                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Editor Header                        │  │
│  │  - Title, Connection Status, Controls            │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌──────────────────────┬─────────────────────────────┐ │
│  │ Parameters Panel     │    Preview Panel            │ │
│  │ ┌──────────────────┐ │ ┌─────────────────────────┐ │ │
│  │ │ ParameterControls│ │ │   PreviewCanvas         │ │ │
│  │ │ - Inputs         │ │ │   - Live Preview        │ │ │
│  │ │ - Sliders        │ │ │   - Zoom/Pan            │ │ │
│  │ │ - Color Pickers  │ │ │   - Controls            │ │ │
│  │ └──────────────────┘ │ └─────────────────────────┘ │ │
│  │                      │ ┌─────────────────────────┐ │ │
│  │ Preset Selector      │ │   Action Buttons        │ │ │
│  │                      │ │   - Save, Export        │ │ │
│  │                      │ └─────────────────────────┘ │ │
│  └──────────────────────┴─────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Editor Footer                        │  │
│  │  - History Info, Quick Actions                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### WebSocket Communication Flow

```
Frontend                          Backend
   │                                │
   │  connect()                     │
   ├───────────────────────────────>│
   │                                │
   │  requestPreview(params)        │
   ├───────────────────────────────>│
   │                                │  Generate Asset
   │  preview_progress(10%)         │
   │<───────────────────────────────┤
   │                                │
   │  preview_progress(50%)         │
   │<───────────────────────────────┤
   │                                │
   │  preview_complete(url)         │
   │<───────────────────────────────┤
   │                                │
```

## Key Features

### 1. Real-time Parameter Updates
- Debounced updates prevent server overload
- Queue management for handling rapid changes
- Priority-based request handling
- Automatic cancellation of outdated requests

### 2. Interactive Canvas
- **Zoom**: Mouse wheel or button controls (0.1x - 10x)
- **Pan**: Click and drag to navigate
- **Reset**: One-click return to default view
- **Touch Support**: Mobile-friendly gestures

### 3. History Management
- Unlimited undo/redo (up to 50 states)
- Visual history indicator
- Keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- Parameter diff tracking

### 4. Live Preview Modes
- **Auto-generate**: Instant updates on parameter change
- **Manual**: User-controlled generation
- **Quality Modes**: Preview vs. Full quality
- **Priority Levels**: High, Normal, Low

### 5. Connection Management
- Automatic reconnection on failure
- Exponential backoff strategy
- Connection status indicators
- Heartbeat monitoring
- Graceful degradation to HTTP

## Implementation Details

### Performance Optimizations

1. **Debouncing**: 500ms debounce on parameter changes
2. **Request Cancellation**: Old requests cancelled when parameters change
3. **Queue Management**: Intelligent request queuing
4. **Memory Management**: Proper cleanup of object URLs
5. **Lazy Loading**: Components load on demand

### Error Handling

1. **Connection Errors**: Automatic reconnection with user notification
2. **Generation Errors**: Clear error messages with retry options
3. **Validation Errors**: Real-time parameter validation
4. **Network Errors**: Graceful fallback to HTTP API

### State Management

1. **Parameter State**: React state with validation
2. **Asset State**: Current preview asset management
3. **History State**: Undo/redo stack
4. **Connection State**: WebSocket status tracking
5. **UI State**: Loading, error, and interaction states

## Usage Examples

### Basic Usage

```javascript
import AssetEditor from './components/react/AssetEditor.jsx';
import { parameterSchema } from './schemas/enso-schema.js';

function App() {
  const handleSave = (asset) => {
    // Save asset to database
    console.log('Saving:', asset);
  };

  return (
    <AssetEditor
      generatorType="enso"
      initialParameters={{ chaos: 0.5 }}
      schema={parameterSchema}
      enableLivePreview={true}
      onSave={handleSave}
    />
  );
}
```

### Advanced Usage with Custom Preview

```javascript
import PreviewCanvas from './components/react/PreviewCanvas.jsx';
import LivePreviewManager from './utils/LivePreviewManager.js';

function CustomEditor() {
  const [asset, setAsset] = useState(null);
  const [parameters, setParameters] = useState({});
  const previewManager = useRef(null);

  useEffect(() => {
    previewManager.current = new LivePreviewManager({
      endpoint: 'ws://localhost:8001/ws/preview',
      onPreviewUpdate: (update) => {
        if (update.type === 'complete') {
          setAsset({ url: update.assetUrl });
        }
      }
    });

    previewManager.current.connect();

    return () => {
      previewManager.current.disconnect();
    };
  }, []);

  const handleGenerate = async (params) => {
    previewManager.current.requestPreview(params, 'enso');
  };

  return (
    <div>
      {/* Custom parameter controls */}
      <ParameterControls
        parameters={parameters}
        schema={schema}
        onChange={setParameters}
      />
      
      {/* Preview canvas */}
      <PreviewCanvas
        asset={asset}
        parameters={parameters}
        onGenerate={handleGenerate}
        autoGenerate={true}
      />
    </div>
  );
}
```

## Testing

### Component Testing

```javascript
// PreviewCanvas.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import PreviewCanvas from './PreviewCanvas.jsx';

test('renders preview canvas with controls', () => {
  render(<PreviewCanvas />);
  
  expect(screen.getByText(/generate preview/i)).toBeInTheDocument();
  expect(screen.getByTitle(/zoom in/i)).toBeInTheDocument();
  expect(screen.getByTitle(/zoom out/i)).toBeInTheDocument();
});

test('handles zoom controls', () => {
  render(<PreviewCanvas />);
  
  const zoomInBtn = screen.getByTitle(/zoom in/i);
  fireEvent.click(zoomInBtn);
  
  // Assert zoom level changed
});
```

### WebSocket Testing

```javascript
// LivePreviewManager.test.js
import LivePreviewManager from './LivePreviewManager.js';

test('connects to WebSocket server', async () => {
  const manager = new LivePreviewManager({
    endpoint: 'ws://localhost:8001/ws/preview'
  });
  
  await manager.connect();
  expect(manager.isConnected).toBe(true);
});

test('handles reconnection on failure', () => {
  const manager = new LivePreviewManager({
    endpoint: 'ws://invalid-url'
  });
  
  // Test reconnection logic
});
```

## Integration Points

### Backend Integration

The preview system integrates with the existing backend through:

1. **WebSocket Endpoint**: `/ws/preview` for real-time updates
2. **HTTP API**: `/generate/advanced/{type}` for fallback generation
3. **Preset API**: `/generate/preset/{name}` for preset loading
4. **Metadata API**: For saving generated assets

### Database Integration

- Asset metadata storage
- Parameter preset storage
- Generation history tracking
- User preference storage

## Future Enhancements

1. **Collaborative Editing**: Multi-user real-time editing
2. **Version Comparison**: Side-by-side version comparison
3. **Advanced Filters**: Real-time filter application
4. **Layer System**: Multi-layer asset composition
5. **Animation Support**: Animated asset preview
6. **Mobile App**: Native mobile applications
7. **Offline Mode**: Local generation without server

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check server is running on port 8001
   - Verify CORS settings
   - Check firewall rules

2. **Preview Not Updating**
   - Verify autoGenerate is enabled
   - Check WebSocket connection status
   - Review browser console for errors

3. **High Memory Usage**
   - Check for memory leaks in component cleanup
   - Verify object URLs are properly revoked
   - Reduce preview queue size

4. **Slow Performance**
   - Reduce preview quality for faster updates
   - Increase debounce delay
   - Check network latency

## Documentation

- **Component API**: See component JSDoc comments
- **WebSocket Protocol**: See LivePreviewManager documentation
- **Styling Guide**: See preview-system.css
- **Testing Guide**: See test files in `tests/`

## Summary

The Interactive Preview System successfully implements all requirements for P3-T4:

✅ Live preview of generation parameters  
✅ Real-time parameter adjustment  
✅ Undo/redo functionality  
✅ Save/load preset configurations  
✅ WebSocket-based real-time updates  
✅ Comprehensive error handling  
✅ Responsive design  
✅ Theme support  

This system provides a professional-grade editing experience that dramatically improves user productivity and creative exploration.