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

# Import cache and batch job utilities
from utils.cache import get_cache
from utils.batch_job import (
    get_job_manager, BatchRequest, GenerationRequest, BatchOptions,
    JobStatus, AssetResult
)

# Import rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import legacy generator functions for backward compatibility
from generate_assets import create_void_parchment, create_ink_enso, create_sigil, create_giraffe, create_kangaroo

# Import new modular generator system
from generators import get_generator, default_factory, list_generators

# Import advanced generation components
from generators.schemas import GenerationParameters, GenerationRequest, PresetRequest, ParameterValidationResult
from generators.presets import get_preset_manager
from generators.color_utils import ColorPaletteManager

# Import metadata system components
try:
    from storage.metadata_schema import AssetMetadata, AssetFormat, AssetCategory, MetadataQuery
    from storage.asset_storage import AssetStorage
    from storage.versioning import AssetVersioner
    from storage.search import AssetSearchEngine
    from storage.tag_manager import TagManager
    from storage.export_import import get_exporter, get_importer, create_full_backup
    
    # Initialize metadata system if enabled
    METADATA_ENABLED = os.getenv('METADATA_ENABLED', 'true').lower() == 'true'
    if METADATA_ENABLED:
        storage = AssetStorage()
        versioner = AssetVersioner(storage)
        search_engine = AssetSearchEngine(storage)
        tag_manager = TagManager(storage)
        print("🔗 Metadata system initialized")
    else:
        storage = versioner = search_engine = tag_manager = None
        print("📦 Metadata system disabled")
        
except ImportError as e:
    print(f"⚠️ Metadata system not available: {e}")
    storage = versioner = search_engine = tag_manager = None
    METADATA_ENABLED = False

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
            "validation_enabled": True,
            "metadata_system": "enabled" if METADATA_ENABLED else "disabled"
        }
    }
    
    # Add metadata system health check
    if METADATA_ENABLED and storage:
        try:
            stats = storage.get_stats()
            health_status["services"]["metadata_storage"] = "operational"
            health_status["metadata_stats"] = {
                "total_assets": stats.total_assets,
                "total_tags": stats.total_tags,
                "database_size_mb": round(stats.database_size_bytes / (1024 * 1024), 2)
            }
        except Exception as e:
            health_status["services"]["metadata_storage"] = f"error: {str(e)}"
    
    # Set start time if not already set
    if not hasattr(app, 'start_time'):
        app.start_time = time.time()
    
    return health_status

@app.get("/generators")
def get_available_generators():
    """
    List all available generator types in the modular system.
    
    Returns:
        Dictionary with available generator types and their information
    """
    try:
        generators = list_generators()
        generator_info = {}
        
        for gen_type in generators:
            try:
                info = default_factory.get_generator_info(gen_type)
                generator_info[gen_type] = info
            except Exception as e:
                generator_info[gen_type] = {"error": str(e)}
        
        return {
            "status": "success",
            "generators": generator_info,
            "total_generators": len(generators),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        print(f"❌ Generator List Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list generators: {str(e)}")

@app.get("/generate/modular/{generator_type}")
def generate_modular_asset(generator_type: str, width: int = None, height: int = None, **kwargs):
    """
    Generate an asset using the new modular generator system.
    
    Args:
        generator_type: Type of generator to use
        width: Optional width override
        height: Optional height override
        **kwargs: Additional generator-specific parameters
        
    Returns:
        PNG image of the generated asset
    """
    try:
        # Validate generator type exists
        available_generators = list_generators()
        if generator_type not in available_generators:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown generator type '{generator_type}'. Available: {available_generators}"
            )
        
        # Build configuration
        config = kwargs.copy()
        if width is not None:
            config['width'] = width
        if height is not None:
            config['height'] = height
            
        # Create generator using factory
        generator = default_factory.create_generator(generator_type, **config)
        
        # Generate asset
        img = generator.generate(**kwargs)
        
        # Return as image
        print(f"✨ Generated {generator_type} using modular system")
        return serve_pil_image(img)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Modular Generation Error for {generator_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate {generator_type}: {str(e)}")

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


# Asset generation function mapping for backward compatibility
LEGACY_GENERATION_FUNCTIONS = {
    'parchment': create_void_parchment,
    'enso': create_ink_enso,
    'sigil': create_sigil,
    'giraffe': create_giraffe,
    'kangaroo': create_kangaroo,
}

# Unified generation function mapping (supports both legacy and modern)
GENERATION_FUNCTIONS = {
    'parchment': 'parchment',
    'enso': 'enso',
    'sigil': 'sigil',
    'giraffe': 'giraffe',
    'kangaroo': 'kangaroo',
}


def generate_single_asset(asset_type: str, parameters: dict = None, use_modern: bool = True) -> Any:
    """
    Generate a single asset with error handling.
    
    Args:
        asset_type: Type of asset to generate
        parameters: Optional generation parameters
        use_modern: Whether to use the new modular system (default: True)
        
    Returns:
        Generated PIL image
        
    Raises:
        Exception: If generation fails
    """
    if asset_type not in GENERATION_FUNCTIONS:
        raise ValueError(f"Unknown asset type: {asset_type}")
    
    # Check cache first with system type in key
    cache_key = f"batch_{asset_type}_{'modern' if use_modern else 'legacy'}_{hash(str(parameters))}"
    cached_img = cache.get(asset_type, cache_key)
    if cached_img is not None:
        print(f"📦 Serving {asset_type} from cache ({'modern' if use_modern else 'legacy'} batch)")
        return cached_img
    
    img = None
    modern_system_used = False
    
    if use_modern:
        # Try new modular system first
        try:
            generator = default_factory.create_generator(asset_type, **(parameters or {}))
            img = generator.generate(**(parameters or {}))
            modern_system_used = True
            print(f"✨ Generated new {asset_type} using modern system (batch)")
        except Exception as e:
            print(f"⚠️ Modern system failed for {asset_type}, falling back to legacy: {e}")
    
    if img is None:
        # Fall back to legacy system
        img = _generate_legacy_asset(asset_type, parameters)
        print(f"✨ Generated new {asset_type} using legacy system (batch)")
    
    # Cache the result with system type in key
    cache_key = f"batch_{asset_type}_{'modern' if modern_system_used else 'legacy'}_{hash(str(parameters))}"
    cache.set(asset_type, img, cache_key)
    
    return img


def _generate_legacy_asset(asset_type: str, parameters: dict = None) -> Any:
    """
    Generate asset using legacy system for backward compatibility.
    
    Args:
        asset_type: Type of asset to generate
        parameters: Optional generation parameters
        
    Returns:
        Generated PIL image
    """
    if asset_type not in LEGACY_GENERATION_FUNCTIONS:
        raise ValueError(f"Unknown legacy asset type: {asset_type}")
    
    func = LEGACY_GENERATION_FUNCTIONS[asset_type]
    
    if parameters:
        return func(index=None, **parameters)
    else:
        return func(index=None)


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
async def generate_batch(
    batch_request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate multiple assets in a single batch request.
    
    Accepts an array of generation requests and processes them asynchronously.
    Returns a job ID for tracking progress.
    """
    try:
        # Create new job
        job = job_manager.create_job(batch_request)
        
        # Start processing in background
        background_tasks.add_task(process_batch_job, job.job_id, batch_request)
        
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


# ==================== Advanced Generation Endpoints ====================

@app.post("/generate/advanced/parchment")
@limiter.limit("10/minute")
async def generate_advanced_parchment(request: Request, generation_request: GenerationRequest):
    """
    Generate parchment with advanced parameters.
    
    Provides fine-grained control over quality, style, color palettes, and effects.
    """
    try:
        if generation_request.asset_type != "parchment":
            raise HTTPException(status_code=400, detail="Invalid asset type for this endpoint")
        
        # Get final parameters
        parameters = generation_request.get_final_parameters()
        
        # Create generator
        generator = default_factory.create_generator("parchment",
                                                   width=parameters.width,
                                                   height=parameters.height,
                                                   seed=parameters.seed)
        
        # Generate with advanced parameters
        img = generator.generate(parameters=parameters)
        
        print(f"✨ Generated advanced parchment with quality={parameters.quality}")
        return serve_pil_image(img)
        
    except Exception as e:
        print(f"❌ Advanced Parchment Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate advanced parchment: {str(e)}")


@app.post("/generate/advanced/enso")
@limiter.limit("10/minute")
async def generate_advanced_enso(request: Request, generation_request: GenerationRequest):
    """
    Generate enso with advanced parameters.
    
    Provides fine-grained control over brush style, chaos, and artistic effects.
    """
    try:
        if generation_request.asset_type != "enso":
            raise HTTPException(status_code=400, detail="Invalid asset type for this endpoint")
        
        # Get final parameters
        parameters = generation_request.get_final_parameters()
        
        # Create generator
        generator = default_factory.create_generator("enso",
                                                   width=parameters.width,
                                                   height=parameters.height,
                                                   seed=parameters.seed)
        
        # Generate with advanced parameters
        img = generator.generate(parameters=parameters)
        
        print(f"✨ Generated advanced enso with style={parameters.style_preset}")
        return serve_pil_image(img)
        
    except Exception as e:
        print(f"❌ Advanced Enso Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate advanced enso: {str(e)}")


@app.post("/generate/advanced/sigil")
@limiter.limit("10/minute")
async def generate_advanced_sigil(request: Request, generation_request: GenerationRequest):
    """
    Generate sigil with advanced parameters.
    
    Provides fine-grained control over geometric precision and mystical effects.
    """
    try:
        if generation_request.asset_type != "sigil":
            raise HTTPException(status_code=400, detail="Invalid asset type for this endpoint")
        
        # Get final parameters
        parameters = generation_request.get_final_parameters()
        
        # Create generator
        generator = default_factory.create_generator("sigil",
                                                   width=parameters.width,
                                                   height=parameters.height,
                                                   seed=parameters.seed)
        
        # Generate with advanced parameters
        img = generator.generate(parameters=parameters)
        
        print(f"✨ Generated advanced sigil with complexity={parameters.complexity}")
        return serve_pil_image(img)
        
    except Exception as e:
        print(f"❌ Advanced Sigil Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate advanced sigil: {str(e)}")


@app.post("/generate/advanced/{asset_type}")
@limiter.limit("10/minute")
async def generate_advanced_asset(request: Request, asset_type: str, generation_request: GenerationRequest):
    """
    Generate any asset with advanced parameters.
    
    Universal endpoint for advanced generation with full parameter support.
    """
    try:
        if generation_request.asset_type != asset_type:
            raise HTTPException(status_code=400, detail="Asset type mismatch between URL and request body")
        
        # Validate asset type
        available_generators = list_generators()
        if asset_type not in available_generators:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown generator type '{asset_type}'. Available: {available_generators}"
            )
        
        # Get final parameters
        parameters = generation_request.get_final_parameters()
        
        # Create generator
        generator = default_factory.create_generator(asset_type,
                                                   width=parameters.width,
                                                   height=parameters.height,
                                                   seed=parameters.seed)
        
        # Generate with advanced parameters
        img = generator.generate(parameters=parameters)
        
        print(f"✨ Generated advanced {asset_type} with preset={parameters.style_preset}")
        return serve_pil_image(img)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Advanced {asset_type} Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate advanced {asset_type}: {str(e)}")


@app.post("/generate/preset/{preset_name}")
@limiter.limit("20/minute")
async def generate_with_preset(request: Request, preset_name: str,
                              asset_type: str, overrides: dict = None):
    """
    Generate asset using a predefined preset.
    
    Args:
        preset_name: Name of the preset to apply
        asset_type: Type of asset to generate
        overrides: Optional parameter overrides
    """
    try:
        # Validate asset type
        available_generators = list_generators()
        if asset_type not in available_generators:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown generator type '{asset_type}'. Available: {available_generators}"
            )
        
        # Get preset manager
        preset_manager = get_preset_manager()
        
        # Start with default parameters
        parameters = GenerationParameters()
        
        # Apply preset
        parameters = preset_manager.apply_preset(parameters, preset_name, overrides)
        
        # Create generator
        generator = default_factory.create_generator(asset_type,
                                                   width=parameters.width,
                                                   height=parameters.height,
                                                   seed=parameters.seed)
        
        # Generate with preset
        img = generator.generate(parameters=parameters)
        
        print(f"✨ Generated {asset_type} with preset '{preset_name}'")
        return serve_pil_image(img)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Preset Generation Error for {preset_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate with preset '{preset_name}': {str(e)}")


@app.get("/presets")
async def get_available_presets():
    """
    Get all available presets organized by category.
    
    Returns:
        Dictionary with preset categories and names
    """
    try:
        preset_manager = get_preset_manager()
        categories = preset_manager.get_presets_by_category()
        
        # Get detailed info for each preset
        preset_info = {}
        for category, presets in categories.items():
            preset_info[category] = []
            for preset_name in presets:
                try:
                    info = preset_manager.get_preset_info(preset_name)
                    preset_info[category].append(info)
                except Exception as e:
                    preset_info[category].append({
                        "name": preset_name,
                        "error": str(e)
                    })
        
        return {
            "status": "success",
            "presets": preset_info,
            "total_presets": sum(len(presets) for presets in categories.values()),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Preset List Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get presets: {str(e)}")


@app.post("/validate/parameters")
async def validate_parameters(request_data: dict):
    """
    Validate generation parameters before use.
    
    Returns validation results and suggestions.
    """
    try:
        # Parse parameters
        parameters = GenerationParameters(**request_data)
        
        # Create dummy generator for validation
        generator = default_factory.create_generator("parchment",
                                                   width=parameters.width,
                                                   height=parameters.height)
        
        # Validate parameters
        validation_result = generator.validate_parameters(parameters)
        
        return {
            "status": "success",
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "suggestions": validation_result.suggestions,
            "effective_dimensions": parameters.get_effective_dimensions(),
            "quality_settings": parameters.get_quality_settings(),
            "style_settings": parameters.get_style_settings(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Parameter Validation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate parameters: {str(e)}")


@app.get("/color-palettes")
async def get_color_palettes():
    """
    Get available color palettes and utilities.
    
    Returns:
        Available color palettes and generation utilities
    """
    try:
        palette_manager = ColorPaletteManager()
        palette_manager.generate_preset_palettes()
        
        return {
            "status": "success",
            "presets": palette_manager.list_saved_palettes(),
            "utilities": {
                "complementary": "Generate complementary color palettes",
                "analogous": "Generate analogous color palettes",
                "monochromatic": "Generate monochromatic palettes",
                "triadic": "Generate triadic color schemes"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Color Palette Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get color palettes: {str(e)}")


# ==================== Metadata Collection Functions ====================

def collect_asset_metadata(img, generator_type: str, parameters: dict = None,
                          user_metadata: dict = None) -> Optional[AssetMetadata]:
    """
    Collect metadata from a generated asset.
    
    Args:
        img: Generated PIL image
        generator_type: Type of generator used
        parameters: Generation parameters
        user_metadata: User-provided metadata (tags, title, etc.)
        
    Returns:
        AssetMetadata object if metadata collection is enabled, None otherwise
    """
    if not METADATA_ENABLED or not storage:
        return None
    
    try:
        import hashlib
        import io
        
        # Calculate file size and hash
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        size_bytes = len(img_buffer.getvalue())
        
        # Calculate SHA256 hash
        img_buffer.seek(0)
        content_hash = hashlib.sha256(img_buffer.read()).hexdigest()
        
        # Create metadata
        metadata = AssetMetadata.create_new(
            generator_type=generator_type,
            width=img.width,
            height=img.height,
            format=AssetFormat.PNG,
            size_bytes=size_bytes,
            hash=content_hash,
            parameters=parameters or {},
            seed=parameters.get('seed') if parameters else None,
            quality=parameters.get('quality') if parameters else None,
            complexity=parameters.get('complexity') if parameters else None,
            randomness=parameters.get('randomness') if parameters else None,
            base_color=parameters.get('base_color') if parameters else None,
            color_palette=parameters.get('color_palette') if parameters else None,
            category=_get_category_for_generator(generator_type),
            tags=user_metadata.get('tags', []) if user_metadata else [],
            title=user_metadata.get('title') if user_metadata else None,
            description=user_metadata.get('description') if user_metadata else None,
            author=user_metadata.get('author') if user_metadata else None
        )
        
        return metadata
        
    except Exception as e:
        print(f"❌ Error collecting metadata: {e}")
        return None


def store_asset_metadata(metadata: AssetMetadata) -> bool:
    """
    Store asset metadata in the database.
    
    Args:
        metadata: AssetMetadata to store
        
    Returns:
        True if successful, False otherwise
    """
    if not METADATA_ENABLED or not storage:
        return False
    
    try:
        return storage.store_asset(metadata)
    except Exception as e:
        print(f"❌ Error storing metadata: {e}")
        return False


def _get_category_for_generator(generator_type: str) -> Optional[AssetCategory]:
    """Map generator types to asset categories."""
    category_mapping = {
        'parchment': AssetCategory.BACKGROUND,
        'enso': AssetCategory.GLYPH,
        'sigil': AssetCategory.GLYPH,
        'giraffe': AssetCategory.CREATURE,
        'kangaroo': AssetCategory.CREATURE,
        'divider': AssetCategory.UI,
        'orb': AssetCategory.UI
    }
    return category_mapping.get(generator_type)


# ==================== Metadata API Endpoints ====================

@app.get("/assets")
async def list_assets(
    search: Optional[str] = Query(None, description="Full-text search query"),
    tags: Optional[str] = Query(None, description="Comma-separated list of required tags"),
    category: Optional[str] = Query(None, description="Asset category filter"),
    generator_type: Optional[str] = Query(None, description="Generator type filter"),
    author: Optional[str] = Query(None, description="Author filter"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List assets with search and filtering capabilities.
    
    Provides comprehensive asset discovery with text search, tag filtering,
    and pagination support.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
        
        # Create query
        query = MetadataQuery(
            text=search,
            tags=tag_list,
            category=AssetCategory(category) if category else None,
            generator_type=generator_type,
            author=author,
            limit=limit,
            offset=offset
        )
        
        # Search assets
        search_results, total_count, facets = search_engine.search(query)
        
        # Convert results to response format
        assets_data = []
        for result in search_results:
            asset = result.asset
            assets_data.append({
                "asset_id": asset.asset_id,
                "title": asset.title or f"{asset.generator_type}_{asset.asset_id[:8]}",
                "generator_type": asset.generator_type,
                "category": asset.category.value if asset.category else None,
                "width": asset.width,
                "height": asset.height,
                "format": asset.format.value,
                "size_bytes": asset.size_bytes,
                "tags": asset.tags,
                "author": asset.author,
                "created_at": asset.created_at.isoformat() + "Z",
                "access_count": asset.access_count,
                "is_favorite": asset.is_favorite,
                "relevance_score": result.relevance_score
            })
        
        return {
            "status": "success",
            "assets": assets_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "facets": {name: {
                "name": facet.name,
                "values": facet.values,
                "total_count": facet.total_count
            } for name, facet in facets.items()},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Asset List Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list assets: {str(e)}")


@app.get("/assets/{asset_id}")
async def get_asset_metadata(asset_id: str):
    """
    Get metadata for a specific asset.
    
    Returns comprehensive asset information including metadata,
    version history, and related assets.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Get asset metadata
        asset = storage.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Increment access count
        storage.increment_access_count(asset_id)
        
        # Get version history
        version_history = versioner.get_version_history(asset_id)
        
        # Get similar assets
        similar_assets = search_engine.find_similar_assets(asset_id, limit=5)
        
        return {
            "status": "success",
            "asset": {
                "asset_id": asset.asset_id,
                "version": asset.version,
                "generator_type": asset.generator_type,
                "parameters": asset.parameters,
                "width": asset.width,
                "height": asset.height,
                "format": asset.format.value,
                "size_bytes": asset.size_bytes,
                "hash": asset.hash,
                "tags": asset.tags,
                "category": asset.category.value if asset.category else None,
                "description": asset.description,
                "author": asset.author,
                "title": asset.title,
                "quality": asset.quality,
                "complexity": asset.complexity,
                "randomness": asset.randomness,
                "base_color": asset.base_color,
                "color_palette": asset.color_palette,
                "created_at": asset.created_at.isoformat() + "Z",
                "updated_at": asset.updated_at.isoformat() + "Z",
                "access_count": asset.access_count,
                "download_count": asset.download_count,
                "is_favorite": asset.is_favorite,
                "status": asset.status.value
            },
            "version_history": [
                {
                    "version": v.version,
                    "created_at": v.created_at.isoformat() + "Z",
                    "description": getattr(v, 'description', None)
                }
                for v in version_history
            ],
            "similar_assets": [
                {
                    "asset_id": sa.asset.asset_id,
                    "title": sa.asset.title or f"{sa.asset.generator_type}_{sa.asset.asset_id[:8]}",
                    "generator_type": sa.asset.generator_type,
                    "relevance_score": sa.relevance_score
                }
                for sa in similar_assets
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Asset Metadata Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get asset metadata: {str(e)}")


@app.get("/assets/{asset_id}/versions")
async def get_asset_versions(asset_id: str):
    """
    Get version history for an asset.
    
    Returns complete version lineage with change tracking
    and rollback capabilities.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        version_history = versioner.get_version_history(asset_id)
        
        if not version_history:
            raise HTTPException(status_code=404, detail="No versions found for asset")
        
        # Get version statistics
        stats = versioner.get_version_statistics(asset_id)
        
        versions_data = []
        for i, version in enumerate(version_history):
            version_info = {
                "version": version.version,
                "created_at": version.created_at.isoformat() + "Z",
                "updated_at": version.updated_at.isoformat() + "Z",
                "description": version.description,
                "author": version.author,
                "quality": version.quality,
                "complexity": version.complexity,
                "width": version.width,
                "height": version.height,
                "size_bytes": version.size_bytes,
                "hash": version.hash,
                "status": version.status.value,
                "is_current": (i == 0)  # Most recent version
            }
            
            # Add change information if not the first version
            if i > 0:
                diff = versioner.get_version_diff(asset_id, version_history[i-1].version, version.version)
                if diff:
                    version_info["changes"] = {
                        "change_type": diff.change_type.value,
                        "summary": diff.get_change_summary(),
                        "significant_changes": diff.significant_changes
                    }
            
            versions_data.append(version_info)
        
        return {
            "status": "success",
            "asset_id": asset_id,
            "versions": versions_data,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Asset Versions Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get asset versions: {str(e)}")


@app.post("/assets/{asset_id}/tags")
async def add_asset_tags(asset_id: str, tags: List[str]):
    """
    Add tags to an asset.
    
    Validates tags and updates the asset's metadata.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Validate tags
        valid_tags, invalid_tags = tag_manager.validate_tags(tags)
        
        if invalid_tags:
            return {
                "status": "partial_success",
                "message": f"Some tags were invalid: {invalid_tags}",
                "valid_tags_added": len(valid_tags),
                "invalid_tags": invalid_tags,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Get current asset
        asset = storage.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Add new tags to existing ones
        new_tags = list(set(asset.tags + valid_tags))
        
        # Update asset
        success = storage.update_asset_metadata(asset_id, {"tags": new_tags})
        
        if success:
            return {
                "status": "success",
                "asset_id": asset_id,
                "tags_added": valid_tags,
                "total_tags": len(new_tags),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update asset tags")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Add Tags Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add tags: {str(e)}")


@app.put("/assets/{asset_id}/metadata")
async def update_asset_metadata(asset_id: str, metadata: dict):
    """
    Update asset metadata.
    
    Allows updating title, description, author, tags, and other metadata fields.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Validate asset exists
        asset = storage.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Update metadata
        success = storage.update_asset_metadata(asset_id, metadata)
        
        if success:
            return {
                "status": "success",
                "asset_id": asset_id,
                "fields_updated": list(metadata.keys()),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update metadata")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update Metadata Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update metadata: {str(e)}")


@app.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str, permanent: bool = Query(False, description="Permanently delete instead of soft delete")):
    """
    Delete an asset.
    
    Performs soft delete by default, can be made permanent.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        success = storage.delete_asset(asset_id, permanent=permanent)
        
        if success:
            return {
                "status": "success",
                "asset_id": asset_id,
                "deleted_permanently": permanent,
                "message": "Asset deleted successfully",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(status_code=404, detail="Asset not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete Asset Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete asset: {str(e)}")


@app.get("/tags")
async def get_popular_tags(
    limit: int = Query(50, ge=1, le=200, description="Number of tags to return"),
    category: Optional[str] = Query(None, description="Filter by tag category")
):
    """
    Get popular tags with filtering options.
    
    Returns most frequently used tags across all assets.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Parse category filter
        from storage.tag_manager import TagCategory
        category_filter = TagCategory(category) if category else None
        
        # Get popular tags
        popular_tags = tag_manager.get_popular_tags(limit=limit, category=category_filter)
        
        tags_data = []
        for tag_info in popular_tags:
            tags_data.append({
                "tag": tag_info.name,
                "category": tag_info.category.value,
                "usage_count": tag_info.usage_count,
                "popularity_score": tag_info.popularity_score,
                "synonyms": tag_info.synonyms,
                "related_tags": tag_info.related_tags,
                "description": tag_info.description
            })
        
        return {
            "status": "success",
            "tags": tags_data,
            "total_count": len(tags_data),
            "category_filter": category,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Popular Tags Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular tags: {str(e)}")


@app.get("/tags/search")
async def search_tags(
    query: str = Query(..., description="Tag search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return")
):
    """
    Search for tags by name.
    
    Provides intelligent tag discovery with autocomplete capabilities.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Search tags
        tag_results = tag_manager.search_tags(query, limit=limit)
        
        tags_data = []
        for tag_info in tag_results:
            tags_data.append({
                "tag": tag_info.name,
                "category": tag_info.category.value,
                "usage_count": tag_info.usage_count,
                "popularity_score": tag_info.popularity_score,
                "synonyms": tag_info.synonyms,
                "related_tags": tag_info.related_tags
            })
        
        return {
            "status": "success",
            "query": query,
            "tags": tags_data,
            "total_count": len(tags_data),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Tag Search Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search tags: {str(e)}")


@app.get("/metadata/stats")
async def get_metadata_stats():
    """
    Get comprehensive metadata system statistics.
    
    Returns system-wide statistics including asset counts, storage usage,
    and popular tags.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Get storage stats
        storage_stats = storage.get_stats()
        
        # Get tag stats
        tag_stats = tag_manager.get_tag_statistics()
        
        # Get search analytics
        search_analytics = search_engine.get_search_analytics()
        
        return {
            "status": "success",
            "storage": {
                "total_assets": storage_stats.total_assets,
                "total_versions": storage_stats.total_versions,
                "total_storage_bytes": storage_stats.total_storage_bytes,
                "average_file_size": storage_stats.average_file_size,
                "database_size_bytes": storage_stats.database_size_bytes,
                "assets_by_category": storage_stats.assets_by_category,
                "assets_by_generator": storage_stats.assets_by_generator
            },
            "tags": {
                "total_tags": tag_stats.get('total_tags', 0),
                "total_usage": tag_stats.get('total_usage', 0),
                "tagged_assets": tag_stats.get('tagged_assets', 0),
                "category_distribution": tag_stats.get('category_distribution', {})
            },
            "search": {
                "total_searches": search_analytics.total_searches,
                "unique_queries": search_analytics.unique_queries,
                "avg_results_per_query": search_analytics.avg_results_per_query
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Metadata Stats Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metadata stats: {str(e)}")


@app.post("/metadata/export")
async def export_metadata(
    format: str = Query("json", description="Export format (json, csv)"),
    include_deleted: bool = Query(False, description="Include deleted assets"),
    asset_ids: Optional[str] = Query(None, description="Comma-separated asset IDs to export")
):
    """
    Export asset metadata.
    
    Creates metadata export in specified format with filtering options.
    """
    if not METADATA_ENABLED:
        raise HTTPException(status_code=503, detail="Metadata system disabled")
    
    try:
        # Parse asset IDs
        id_list = [aid.strip() for aid in asset_ids.split(",")] if asset_ids else None
        
        # Get exporter
        from storage.export_import import get_exporter
        exporter = get_exporter(storage, tag_manager)
        
        # Generate export filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"metadata_export_{timestamp}.{format}"
        filepath = f"./exports/{filename}"
        
        # Ensure exports directory exists
        os.makedirs("./exports", exist_ok=True)
        
        # Perform export
        success = False
        if format.lower() == "json":
            success = exporter.export_to_json(filepath, include_deleted=include_deleted, asset_ids=id_list)
        elif format.lower() == "csv":
            success = exporter.export_to_csv(filepath, include_deleted=include_deleted)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
        
        if success:
            # Get file size
            file_size = os.path.getsize(filepath)
            
            return {
                "status": "success",
                "filename": filename,
                "filepath": filepath,
                "format": format,
                "file_size_bytes": file_size,
                "include_deleted": include_deleted,
                "asset_count": len(id_list) if id_list else "all",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(status_code=500, detail="Export failed")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Export Metadata Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export metadata: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("🍌 NanoBanana API starting up...")
    print(f"   - LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', 'Not Set (will use default)')}")
    key = os.environ.get('OPENAI_API_KEY', '')
    masked_key = f"{key[:8]}...{key[-4:]}" if key else "Not Set"
    print(f"   - OPENAI_API_KEY: {masked_key}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
