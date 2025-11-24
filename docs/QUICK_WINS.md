# 🚀 Quick Wins - Implement Today

These are immediate improvements that can be implemented in minutes for instant impact.

---

## 1. Fix CORS Vulnerability ⚡ (5 minutes)

**Problem**: Wildcard CORS origins (`*`) is a security risk  
**Location**: [`backend.py:26-32`](backend.py:26)

### Implementation
```python
# Replace lines 26-32 in backend.py
import os

# Get comma-separated origins from env, default to localhost
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
origins_list = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,  # ✅ Configurable whitelist
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "X-Base-Url", "Content-Type"],
)
```

### Usage
```bash
# Development
export CORS_ORIGINS="http://localhost:3000,http://localhost:8000"

# Production
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

**Impact**: ✅ Eliminates critical security vulnerability

---

## 2. Add Health Check Endpoint ⚡ (5 minutes)

**Problem**: No way to monitor service health  
**Location**: Add to [`backend.py`](backend.py) after line 46

### Implementation
```python
import time
import os

STARTUP_TIME = time.time()

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "NanoBanana Generator API",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - STARTUP_TIME),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
```

### Usage
```bash
curl http://localhost:8001/health
# Returns: {"status": "healthy", "version": "1.0.0", ...}
```

**Impact**: ✅ Enables monitoring and deployment health checks

---

## 3. Create .env.example Template ⚡ (2 minutes)

**Problem**: No template for required environment variables  
**Location**: Create [``.env.example``](.env.example)

### Implementation
```bash
# .env.example
# NanoBanana Generator Configuration
# Copy this file to .env and fill in your values

# API Keys
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Override Base URL for LLM provider
# Default: https://router.requesty.ai/v1
LLM_BASE_URL=https://router.requesty.ai/v1

# CORS Configuration
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Server Configuration (optional)
PORT=8001
HOST=0.0.0.0
```

**Impact**: ✅ Documents configuration, prevents key exposure

---

## 4. Add Basic Error Handling ⚡ (10 minutes)

**Problem**: Unhandled exceptions crash server  
**Location**: [`backend.py`](backend.py) - wrap API endpoints

### Implementation
```python
from fastapi import HTTPException

@app.get("/generate/{asset_type}")
def generate_asset(asset_type: str):
    """Generate asset with error handling"""
    try:
        if asset_type == "parchment":
            img = create_void_parchment(index=None)
        elif asset_type == "enso":
            img = create_ink_enso(index=None)
        elif asset_type == "sigil":
            img = create_sigil(index=None)
        elif asset_type == "giraffe":
            img = create_giraffe(index=None)
        elif asset_type == "kangaroo":
            img = create_kangaroo(index=None)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown asset type: {asset_type}. Valid types: parchment, enso, sigil, giraffe, kangaroo"
            )
        
        return serve_pil_image(img)
        
    except Exception as e:
        print(f"Error generating {asset_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
```

**Impact**: ✅ Prevents server crashes, improves user experience

---

## 5. Add Request Logging ⚡ (5 minutes)

**Problem**: No visibility into API usage  
**Location**: [`backend.py`](backend.py) - add middleware

### Implementation
```python
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    print(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
    
    return response
```

**Impact**: ✅ Visibility into API performance and usage

---

## 6. Fix llm_director.py Corruption ⚡ (15 minutes)

**Problem**: Code corruption prevents LLM-directed generation  
**Location**: [`llm_director.py:68-85`](llm_director.py:68)

### Implementation
Replace corrupted section with:
```python
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the Art Director for 'Unwritten Worlds'. "
                    "Translate user moods into JSON parameters for the Ink Enso generator. "
                    "Output ONLY a valid JSON object with keys: color_hex (e.g. #FF0000), complexity (20-100), chaos (0.1-2.0), text_overlay (string)."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.8,
        "max_tokens": 150,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Extract content safely
        content = data["choices"][0]["message"]["content"]
        
        # Handle both string and object content
        if isinstance(content, dict):
            params_dict = content
        else:
            # Parse JSON from string
            params_dict = json.loads(content)
```

**Impact**: ✅ Restores LLM-directed generation functionality

---

## 7. Add Input Validation ⚡ (10 minutes)

**Problem**: No validation on API inputs  
**Location**: [`backend.py`](backend.py) - add validation

### Implementation
```python
from fastapi import Query, HTTPException

@app.get("/generate/directed/enso")
def get_directed_enso(
    prompt: str = Query(..., min_length=1, max_length=500),
    model: str = Query("gpt-4o", regex="^[a-zA-Z0-9-_.]+$"),
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
):
    """Generate directed enso with input validation"""
    # Validate prompt
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Validate model name
    valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06"]
    if model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Valid models: {', '.join(valid_models)}"
        )
    
    # Continue with existing logic...
```

**Impact**: ✅ Prevents invalid input, improves security

---

## 8. Create README.md ⚡ (15 minutes)

**Problem**: No project documentation  
**Location**: Create [`README.md`](README.md)

### Implementation
```markdown
# 🍌 NanoBanana Protocol

Procedural generation system for the "Unwritten Worlds" aesthetic.

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn pillow numpy python-dotenv

# Configure environment
cp .env.example .env
# Edit .env with your API key

# Run server
python backend.py
```

## API Endpoints

- `GET /health` - Health check
- `GET /generate/parchment` - Generate parchment texture
- `GET /generate/enso` - Generate ink enso
- `GET /generate/directed/enso?prompt=...` - LLM-directed generation

## Development

See [`docs/`](docs/) for full documentation.
```

**Impact**: ✅ Enables onboarding and adoption

---

## Summary

| Quick Win | Time | Impact | Priority |
|-----------|------|--------|----------|
| Fix CORS | 5 min | 🔴 Critical | 1 |
| Health Check | 5 min | 🟡 High | 2 |
| .env.example | 2 min | 🟢 Medium | 3 |
| Error Handling | 10 min | 🔴 Critical | 1 |
| Request Logging | 5 min | 🟢 Medium | 4 |
| Fix llm_director | 15 min | 🔴 Critical | 1 |
| Input Validation | 10 min | 🟡 High | 2 |
| README | 15 min | 🟢 Medium | 3 |

**Total Time**: ~67 minutes  
**Critical Issues Fixed**: 3  
**Security Improvements**: 2

---

## Next Steps

After implementing quick wins:
1. ✅ Run security audit
2. ✅ Test all endpoints
3. ✅ Update [`HANDOFF.md`](HANDOFF.md) with progress
4. ✅ Proceed to Phase 1 remaining tasks