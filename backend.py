from fastapi import FastAPI, Query, Header, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import re
import requests
import time
import json
import asyncio
from typing import Any
from datetime import datetime
from dotenv import load_dotenv
from generate_assets import create_void_parchment, create_ink_enso, create_sigil, create_giraffe, create_kangaroo
from utils.cache import get_cache
from utils.batch_job import (
    get_job_manager, BatchRequest, GenerationRequest, BatchOptions,
    JobStatus, AssetResult
)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from .env
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import the Director (Wrap in try/except in case dependencies/keys are missing)
try:
    from llm_director import get_enso_params_from_prompt
    HAS_LLM = True
except Exception as e:
    print(f"⚠️ LLM Director not available: {e}")
    HAS_LLM = False

app = FastAPI(title="NanoBanana Generator API")

# Initialize cache
cache = get_cache()

# Initialize job manager
job_manager = get_job_manager()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Secure CORS configuration with configurable whitelist
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
origins_list = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,  # Configurable whitelist
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "X-Base-Url", "Content-Type"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Log request
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": request.method,
        "url": str(request.url),
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent", "unknown"),
        "status": "started"
    }
    print(f"📥 Request: {json.dumps(log_entry)}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        log_entry["status"] = "completed"
        log_entry["status_code"] = response.status_code
        log_entry["process_time"] = round(process_time, 3)
        
        print(f"📤 Response: {json.dumps(log_entry)}")
        
        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        log_entry["status"] = "error"
        log_entry["error"] = str(e)
        log_entry["process_time"] = round(process_time, 3)
        
        print(f"❌ Error: {json.dumps(log_entry)}")
        raise

def serve_pil_image(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@app.get("/")
def read_root():
    return {"message": "NanoBanana Generator API is running. Go to /docs for more."}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and deployment."""
    import time
    from datetime import datetime
    
    # Basic health check
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "uptime_seconds": time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        "services": {
            "api": "operational",
            "asset_generation": "operational",
            "llm_director": "operational" if HAS_LLM else "disabled"
        },
        "checks": {
            "cors_configured": True,
            "error_handling_enabled": True,
            "validation_enabled": True
        }
    }
    
    # Set start time if not already set
    if not hasattr(app, 'start_time'):
        app.start_time = time.time()
    
    return health_status

@app.get("/models")
def get_models(
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    base_url_header: str | None = Header(default=None, alias="X-Base-Url"),
):
    """Fetches available models from the LLM provider (Requesty/OpenAI-compatible).
    Prefers API Key and Base URL from headers; falls back to .env. Defaults base to Requesty router.
    """
    api_key = api_key_header or os.environ.get("OPENAI_API_KEY")
    base_url = (base_url_header or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")).rstrip('/')

    if not api_key or "placeholder" in str(api_key):
        return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]}

    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/models", headers=headers, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching models: {e}")
        return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}, {"id": "error-fetching-models"}]}

@app.get("/generate/parchment")
def get_parchment():
    """Generates a new unique Void Parchment texture."""
    try:
        # Try to get from cache first
        cached_img = cache.get('parchment')
        if cached_img is not None:
            print("📦 Serving parchment from cache")
            return serve_pil_image(cached_img)
        
        # Generate new asset
        img = create_void_parchment(index=None)
        
        # Cache the result
        cache.set('parchment', img)
        print("✨ Generated new parchment and cached it")
        
        return serve_pil_image(img)
    except Exception as e:
        print(f"❌ Parchment Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate parchment: {str(e)}")

@app.get("/generate/enso")
def get_enso():
    """Generates a new unique Ink Enso circle."""
    try:
        # Try to get from cache first
        cached_img = cache.get('enso')
        if cached_img is not None:
            print("📦 Serving enso from cache")
            return serve_pil_image(cached_img)
        
        # Generate new asset
        img = create_ink_enso(index=None)
        
        # Cache the result
        cache.set('enso', img)
        print("✨ Generated new enso and cached it")
        
        return serve_pil_image(img)
    except Exception as e:
        print(f"❌ Enso Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate enso: {str(e)}")

@app.get("/generate/directed/enso")
def get_directed_enso(
    prompt: str = Query(..., description="Describe the vibe (e.g. 'Burning Rage')"),
    model: str = Query("gpt-4o", description="The LLM model to use"),
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    base_url_header: str | None = Header(default=None, alias="X-Base-Url"),
):
    # Input validation
    if not prompt or len(prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    if len(prompt) > 500:
        raise HTTPException(status_code=400, detail="Prompt too long (max 500 characters)")
    
    # Sanitize prompt - remove potentially harmful characters
    prompt = prompt.strip()
    
    # Validate API key format if provided via header
    if api_key_header:
        if not api_key_header.startswith("sk-"):
            raise HTTPException(status_code=400, detail="Invalid API key format")
        if len(api_key_header) < 20 or len(api_key_header) > 200:
            raise HTTPException(status_code=400, detail="Invalid API key length")
    
    # Validate model name
    valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
    if model not in valid_models:
        # Allow custom models but validate format
        if not re.match(r'^[a-zA-Z0-9\.\-_]+$', model):
            raise HTTPException(status_code=400, detail="Invalid model name format")
    """
    Uses LLM (Requesty/OpenAI-compatible) to generate an Enso from a text prompt.
    Prefers API Key and Base URL from headers; falls back to .env. Defaults base to Requesty router.
    """
    if not HAS_LLM:
        raise HTTPException(status_code=503, detail="LLM Director not available.")

    api_key = api_key_header or os.environ.get("OPENAI_API_KEY")
    base_url = base_url_header or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")

    if not api_key or "placeholder" in str(api_key):
        raise HTTPException(status_code=401, detail="No API Key provided. Pass X-API-Key header or configure .env")

    try:
        # Create cache key from prompt and model
        cache_key = f"directed_enso:{prompt}:{model}"
        
        # Try to get from cache first
        cached_img = cache.get('directed_enso', prompt, model)
        if cached_img is not None:
            print(f"📦 Serving directed enso from cache (prompt: {prompt[:50]}...)")
            return serve_pil_image(cached_img)
        
        params = get_enso_params_from_prompt(prompt, api_key=api_key, model=model, base_url=base_url)
        print(f"🎨 Director ({model}) ordered: {params}")

        rgb_color = hex_to_rgb(params.color_hex)
        img = create_ink_enso(
            index=None,
            color=rgb_color,
            complexity=params.complexity,
            chaos=params.chaos,
        )
        
        # Cache the result
        cache.set('directed_enso', img, prompt, model)
        print("✨ Generated new directed enso and cached it")

        return serve_pil_image(img)

    except Exception as e:
        print(f"❌ Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate/sigil")
def get_sigil():
    """Generates a new unique Arcane Sigil."""
    try:
        # Try to get from cache first
        cached_img = cache.get('sigil')
        if cached_img is not None:
            print("📦 Serving sigil from cache")
            return serve_pil_image(cached_img)
        
        # Generate new asset
        img = create_sigil(index=None)
        
        # Cache the result
        cache.set('sigil', img)
        print("✨ Generated new sigil and cached it")
        
        return serve_pil_image(img)
    except Exception as e:
        print(f"❌ Sigil Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate sigil: {str(e)}")

@app.get("/generate/giraffe")
def get_giraffe():
    """Generates a new unique Ink Giraffe entity."""
    try:
        # Try to get from cache first
        cached_img = cache.get('giraffe')
        if cached_img is not None:
            print("📦 Serving giraffe from cache")
            return serve_pil_image(cached_img)
        
        # Generate new asset
        img = create_giraffe(index=None)
        
        # Cache the result
        cache.set('giraffe', img)
        print("✨ Generated new giraffe and cached it")
        
        return serve_pil_image(img)
    except Exception as e:
        print(f"❌ Giraffe Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate giraffe: {str(e)}")

@app.get("/generate/kangaroo")
def get_kangaroo():
    """Generates a new unique Ink Kangaroo on a Pogo Stick."""
    try:
        # Try to get from cache first
        cached_img = cache.get('kangaroo')
        if cached_img is not None:
            print("📦 Serving kangaroo from cache")
            return serve_pil_image(cached_img)
        
        # Generate new asset
        img = create_kangaroo(index=None)
        
        # Cache the result
        cache.set('kangaroo', img)
        print("✨ Generated new kangaroo and cached it")
        
        return serve_pil_image(img)
    except Exception as e:
        print(f"❌ Kangaroo Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate kangaroo: {str(e)}")

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics and metrics."""
    try:
        stats = cache.get_stats()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "cache_stats": stats
        }
    except Exception as e:
        print(f"❌ Cache Stats Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")
@app.get("/cache/clear")
async def clear_cache():
    """Clear all cached assets."""
    try:
        cache.clear_all()
        return {
            "status": "success",
            "message": "Cache cleared",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        print(f"❌ Cache Clear Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# Asset generation function mapping
GENERATION_FUNCTIONS = {
    'parchment': create_void_parchment,
    'enso': create_ink_enso,
    'sigil': create_sigil,
    'giraffe': create_giraffe,
    'kangaroo': create_kangaroo,
}


def generate_single_asset(asset_type: str, parameters: dict = None) -> Any:
    """
    Generate a single asset with error handling.
    
    Args:
        asset_type: Type of asset to generate
        parameters: Optional generation parameters
        
    Returns:
        Generated PIL image
        
    Raises:
        Exception: If generation fails
    """
    if asset_type not in GENERATION_FUNCTIONS:
        raise ValueError(f"Unknown asset type: {asset_type}")
    
    func = GENERATION_FUNCTIONS[asset_type]
    
    # Check cache first
    cache_key = f"batch_{asset_type}_{hash(str(parameters))}"
    cached_img = cache.get(asset_type, cache_key)
    if cached_img is not None:
        print(f"📦 Serving {asset_type} from cache (batch)")
        return cached_img
    
    # Generate new asset
    if parameters:
        img = func(index=None, **parameters)
    else:
        img = func(index=None)
    
    # Cache the result
    cache.set(asset_type, img, cache_key)
    print(f"✨ Generated new {asset_type} and cached it (batch)")
    
    return img


async def process_batch_job(job_id: str, batch_request: BatchRequest):
    """
    Process a batch generation job asynchronously.
    
    Args:
        job_id: Job identifier
        batch_request: Batch generation request
    """
    job_manager.update_job_status(job_id, JobStatus.PROCESSING, started_at=datetime.utcnow())
    
    try:
        total_generated = 0
        request_index = 0
        
        for gen_request in batch_request.requests:
            if job_manager.get_job(job_id).cancelled:
                break
            
            # Process each request
            for i in range(gen_request.count):
                if job_manager.get_job(job_id).cancelled:
                    break
                
                try:
                    # Generate asset
                    img = await asyncio.get_event_loop().run_in_executor(
                        None,
                        generate_single_asset,
                        gen_request.type,
                        gen_request.parameters or {}
                    )
                    
                    # Store result
                    result = AssetResult(
                        request_index=request_index,
                        asset_index=i,
                        asset_type=gen_request.type,
                        success=True,
                        data=img
                    )
                    job_manager.add_asset_result(job_id, result)
                    total_generated += 1
                    
                    print(f"✅ Generated {gen_request.type} #{i+1}/{gen_request.count} for job {job_id}")
                    
                except Exception as e:
                    print(f"❌ Failed to generate {gen_request.type} #{i+1}: {e}")
                    result = AssetResult(
                        request_index=request_index,
                        asset_index=i,
                        asset_type=gen_request.type,
                        success=False,
                        error=str(e)
                    )
                    job_manager.add_asset_result(job_id, result)
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.01)
            
            request_index += 1
        
        # Mark job as completed
        job = job_manager.get_job(job_id)
        if job.cancelled:
            job_manager.update_job_status(job_id, JobStatus.CANCELLED, completed_at=datetime.utcnow())
        elif job.failed_items > 0 and job.completed_items == 0:
            job_manager.update_job_status(job_id, JobStatus.FAILED, completed_at=datetime.utcnow())
        else:
            job_manager.update_job_status(job_id, JobStatus.COMPLETED, completed_at=datetime.utcnow())
        
        print(f"🎉 Batch job {job_id} completed: {job.completed_items} successful, {job.failed_items} failed")
        
    except Exception as e:
        print(f"❌ Batch job {job_id} failed: {e}")
        job_manager.update_job_status(job_id, JobStatus.FAILED, error=str(e), completed_at=datetime.utcnow())


@app.post("/generate/batch")
@limiter.limit("10/minute")
async def generate_batch(
    request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate multiple assets in a single batch request.
    
    Accepts an array of generation requests and processes them asynchronously.
    Returns a job ID for tracking progress.
    """
    try:
        # Create new job
        job = job_manager.create_job(request)
        
        # Start processing in background
        background_tasks.add_task(process_batch_job, job.job_id, request)
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "created_at": job.created_at.isoformat() + "Z",
            "message": "Batch job created and processing started"
        }
        
    except Exception as e:
        print(f"❌ Batch Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create batch job: {str(e)}")


@app.get("/generate/batch/{job_id}/status")
@limiter.limit("60/minute")
async def get_batch_status(job_id: str):
    """
    Get the status of a batch generation job.
    
    Returns current progress, completed items, and any errors.
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Prepare asset data (convert PIL images to base64 for response)
        assets_data = []
        for asset in job.assets:
            asset_dict = {
                "request_index": asset.request_index,
                "asset_index": asset.asset_index,
                "asset_type": asset.asset_type,
                "success": asset.success,
                "timestamp": asset.timestamp.isoformat() + "Z"
            }
            if asset.error:
                asset_dict["error"] = asset.error
            assets_data.append(asset_dict)
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "assets": assets_data,
            "created_at": job.created_at.isoformat() + "Z",
            "started_at": job.started_at.isoformat() + "Z" if job.started_at else None,
            "completed_at": job.completed_at.isoformat() + "Z" if job.completed_at else None,
            "error": job.error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Batch Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@app.post("/generate/batch/{job_id}/cancel")
@limiter.limit("30/minute")
async def cancel_batch_job(job_id: str):
    """
    Cancel a running batch generation job.
    
    Attempts to stop processing and marks the job as cancelled.
    """
    try:
        success = job_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or already completed")
        
        return {
            "status": "success",
            "message": "Job cancelled successfully",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Batch Cancel Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel batch job: {str(e)}")


@app.get("/jobs")
@limiter.limit("30/minute")
async def list_jobs():
    """
    List all batch jobs with their current status.
    
    Useful for monitoring and debugging.
    """
    try:
        jobs = job_manager.get_all_jobs()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "job_id": job.job_id,
                "status": job.status,
                "total_items": job.total_items,
                "completed_items": job.completed_items,
                "failed_items": job.failed_items,
                "created_at": job.created_at.isoformat() + "Z",
                "started_at": job.started_at.isoformat() + "Z" if job.started_at else None,
                "completed_at": job.completed_at.isoformat() + "Z" if job.completed_at else None,
                "error": job.error
            })
        
        return {
            "jobs": jobs_data,
            "total_jobs": len(jobs_data),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ List Jobs Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("🍌 NanoBanana API starting up...")
    print(f"   - LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', 'Not Set (will use default)')}")
    key = os.environ.get('OPENAI_API_KEY', '')
    masked_key = f"{key[:8]}...{key[-4:]}" if key else "Not Set"
    print(f"   - OPENAI_API_KEY: {masked_key}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
