# NanoBanana Protocol - System Design

## Goals

Transform the NanoBanana Protocol into a production-ready procedural generation system while maintaining the "Unwritten Worlds" aesthetic vision. The system will serve as a scalable backend for generating eldritch/ink-themed assets with LLM-directed creative control.

## Non-Goals

- Building a full-fledged CMS or user management system
- Real-time collaborative editing features
- Mobile-first responsive design (desktop-focused aesthetic)
- Multi-tenant architecture (single-tenant with API key auth)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   HTML/CSS   │  │  JavaScript  │  │   Browser    │      │
│  │   Templates  │  │   (Core.js)  │  │     APIs     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ▼                                 │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼─────────────────────────────────┐
│                    BACKEND LAYER                            │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │         FastAPI Server            │              │
│         │         (backend.py)              │              │
│         │  Port: 8001                       │              │
│         └─────────────────┬─────────────────┘              │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │    Asset Generator Engine         │              │
│         │    (generate_assets.py)           │              │
│         │    Pillow + NumPy                 │              │
│         └─────────────────┬─────────────────┘              │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │      LLM Director Service         │              │
│         │      (llm_director.py)            │              │
│         │      OpenAI/Requesty API          │              │
│         └───────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼─────────────────────────────────┐
│                    DATA LAYER                               │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │   Asset Storage (File System)     │              │
│         │   assets/generated/               │              │
│         │   assets/elements/                │              │
│         └─────────────────┬─────────────────┘              │
│                           │                                 │
│         ┌─────────────────▼─────────────────┐              │
│         │   Configuration (.env)            │              │
│         │   API Keys, Base URLs             │              │
│         └───────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Key Flows

### Flow 1: Asset Generation (Simple)
1. Client requests `/generate/{type}` (parchment/enso/sigil/giraffe/kangaroo)
2. FastAPI routes to appropriate generator function
3. PIL creates image in memory with procedural algorithms
4. Image streamed directly to client as PNG
5. Client displays generated asset

### Flow 2: LLM-Directed Generation
1. Client sends prompt to `/generate/directed/enso?prompt="Burning Rage"`
2. Backend passes prompt to LLM Director with API key
3. Director calls OpenAI/Requesty API for structured JSON response
4. Director parses and validates parameters (color_hex, complexity, chaos)
5. Generator creates enso with LLM-specified parameters
6. Image streamed to client

### Flow 3: Model Discovery
1. Client requests `/models` with API key headers
2. Backend proxies request to configured LLM provider
3. Returns available models to client
4. Client populates model selector dropdown

## Data Model

### Storage
- **File-based storage** for generated assets
- Organized in hierarchical directories:
  - `assets/generated/` - Runtime-generated assets
  - `assets/elements/` - Pre-generated template assets
  - `assets/effects/` - Static overlay textures

### Schema Notes
- No database required (stateless generation)
- Asset metadata stored in filenames: `{type}_{index}.png`
- Configuration in `.env` file (API keys, base URLs)

## Security

### Authentication
- API key-based authentication via headers (`X-API-Key`)
- Fallback to `.env` configuration
- No user accounts or sessions

### Secrets Management
- `.env` file for local development (excluded from git)
- Environment variables in production
- API keys never logged or exposed in responses

### CORS Policy
- **CURRENT**: Overly permissive (`allow_origins=["*"]`)
- **PLANNED**: Configurable whitelist with environment variable

## Testing Strategy

### Levels
1. **Unit Tests**: Individual generator functions (PIL operations)
2. **Integration Tests**: API endpoints with mocked LLM responses
3. **E2E Tests**: Full generation flow with browser automation

### Tools
- `pytest` for Python unit/integration tests
- `Playwright` for frontend E2E tests
- Coverage reporting with `pytest-cov`

## Deployment

### Environments
- **Development**: Localhost (Python venv, hot reload)
- **Production**: Containerized deployment (Docker)

### Target Platform
- Docker containers on cloud provider (AWS ECS, Railway, Render)
- No serverless (requires persistent PIL dependencies)

## Constraints

### Performance
- Target: <500ms for simple asset generation
- Target: <3s for LLM-directed generation (includes API call)
- Concurrent generation supported via async FastAPI

### Cost
- LLM API costs: ~$0.01-0.05 per directed generation
- Hosting: ~$5-20/month for containerized deployment
- Bandwidth: Minimal (small PNG files)

### Latency
- Image generation: <200ms (PIL operations)
- LLM API call: 500-2000ms (network dependent)
- Total end-to-end: <3000ms

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API downtime | Directed generation fails | Graceful fallback to random generation |
| CORS misconfiguration | Frontend cannot fetch assets | Configurable origins, health checks |
| Memory leaks in PIL | Server crashes | Periodic restart strategy, memory monitoring |
| API key exposure | Unauthorized usage | Environment variables, key rotation |
| Code corruption | Broken functionality | Version control, automated testing |
| Asset duplication | Storage bloat | Deduplication, cache invalidation |

## Technology Stack

### Languages
- Python 3.10+ (backend generation)
- JavaScript ES6+ (frontend orchestration)
- HTML5/CSS3 (presentation)

### Frameworks
- FastAPI (Python web framework)
- Uvicorn (ASGI server)
- Pillow + NumPy (image processing)

### APIs
- OpenAI Compatible (Requesty router, OpenAI direct)
- Custom REST API for asset generation

### Runtime
- **Frontend**: Modern browsers (Chrome 90+, Firefox 88+)
- **Backend**: Python 3.10+ with venv
- **Infrastructure**: Docker containers, cloud hosting