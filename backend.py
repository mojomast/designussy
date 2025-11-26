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
# Import Phase 2 type-aware generation components
try:
    from generators.dynamic_loader import DynamicGeneratorLoader
    from generators.type_batch_generator import TypeBatchGenerator
    from generators.variation_strategies import VariationEngine
    HAS_TYPE_AWARE_SYSTEM = True
except ImportError as e:
    print(f"⚠️ Type-aware generation system not available: {e}")
    HAS_TYPE_AWARE_SYSTEM = False

# Import Type System components
try:
    from enhanced_design.type_registry import get_type_registry, TypeRegistry
    from enhanced_design.element_types import ElementType
    HAS_TYPE_SYSTEM = True
except ImportError as e:
    print(f"⚠️ Type system not available: {e}")
    HAS_TYPE_SYSTEM = False

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
# Initialize type-aware generation system if available
if HAS_TYPE_AWARE_SYSTEM:
    type_aware_loader = DynamicGeneratorLoader()
    type_batch_generator = TypeBatchGenerator()
    variation_engine = VariationEngine()
    print("🎯 Type-aware generation system initialized")
else:
    type_aware_loader = None
    type_batch_generator = None
    variation_engine = None
    print("📦 Type-aware generation system disabled")

# Initialize type registry if available
if HAS_TYPE_SYSTEM:
    type_registry = get_type_registry()
    print("🔧 Type system initialized")
else:
    type_registry = None
    print("📦 Type system disabled")

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


# ==================== Type System API Endpoints ====================

@app.get("/types")
async def list_types(
    category: Optional[str] = Query(None, description="Filter by type category"),
    search: Optional[str] = Query(None, description="Search in type names and descriptions"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all available element types with optional filtering.
    
    Provides comprehensive type discovery with search and pagination.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Get tags from query parameter
        tags = None
        if search:
            # Simple search implementation
            pass
        
        # List types from registry
        types = type_registry.list(
            category=category,
            search=search,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        types_data = []
        for element_type in types:
            types_data.append({
                "id": element_type.id,
                "name": element_type.name,
                "description": element_type.description,
                "category": element_type.category,
                "tags": element_type.tags,
                "version": element_type.version,
                "created_at": element_type.created_at.isoformat() + "Z",
                "usage_count": element_type.usage_count,
                "variants_count": len(element_type.variants),
                "has_diversity_config": element_type.diversity_config is not None
            })
        
        return {
            "status": "success",
            "types": types_data,
            "total_count": len(types_data),
            "category_filter": category,
            "search_query": search,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ List Types Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list types: {str(e)}")


@app.get("/types/{type_id}")
async def get_type(type_id: str):
    """
    Get detailed information about a specific element type.
    
    Returns comprehensive type information including variants,
    diversity configuration, and parameter schema.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Get type from registry
        element_type = type_registry.get(type_id)
        if not element_type:
            raise HTTPException(status_code=404, detail=f"Type '{type_id}' not found")
        
        # Convert to response format
        type_data = {
            "id": element_type.id,
            "name": element_type.name,
            "description": element_type.description,
            "category": element_type.category,
            "tags": element_type.tags,
            "version": element_type.version,
            "created_by": element_type.created_by,
            "created_at": element_type.created_at.isoformat() + "Z",
            "updated_at": element_type.updated_at.isoformat() + "Z" if element_type.updated_at else None,
            "usage_count": element_type.usage_count,
            "is_active": element_type.is_active,
            "is_template": element_type.is_template,
            "render_strategy": {
                "engine": element_type.render_strategy.engine,
                "generator_name": element_type.render_strategy.generator_name
            },
            "param_schema": element_type.param_schema,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "description": v.description,
                    "parameters": v.parameters,
                    "weight": v.weight
                }
                for v in element_type.variants
            ],
            "diversity_config": element_type.diversity_config.dict() if element_type.diversity_config else None,
            "default_params": element_type.get_default_params(),
            "search_text": element_type.get_search_text()
        }
        
        return {
            "status": "success",
            "type": type_data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get Type Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get type: {str(e)}")


@app.post("/types")
async def create_type(type_data: dict):
    """
    Create a new element type.
    
    Validates the type data and adds it to the registry.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Create ElementType from data
        element_type = ElementType(**type_data)
        
        # Add to registry
        success = type_registry.add(element_type)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create type (may already exist)")
        
        return {
            "status": "success",
            "type_id": element_type.id,
            "message": "Type created successfully",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid type data: {str(e)}")
    except Exception as e:
        print(f"❌ Create Type Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create type: {str(e)}")


@app.put("/types/{type_id}")
async def update_type(type_id: str, type_data: dict):
    """
    Update an existing element type.
    
    Updates type information in the registry.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Add type_id to data
        type_data['id'] = type_id
        
        # Create ElementType from data
        element_type = ElementType(**type_data)
        
        # Update in registry
        success = type_registry.update(element_type)
        if not success:
            raise HTTPException(status_code=404, detail=f"Type '{type_id}' not found")
        
        return {
            "status": "success",
            "type_id": type_id,
            "message": "Type updated successfully",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid type data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update Type Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update type: {str(e)}")


@app.delete("/types/{type_id}")
async def delete_type(type_id: str, soft_delete: bool = Query(True, description="Whether to use soft delete")):
    """
    Delete an element type from the registry.
    
    Performs soft delete by default, can be made permanent.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Delete from registry
        success = type_registry.delete(type_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail=f"Type '{type_id}' not found")
        
        return {
            "status": "success",
            "type_id": type_id,
            "deleted_permanently": not soft_delete,
            "message": "Type deleted successfully",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete Type Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete type: {str(e)}")


@app.get("/types/categories")
async def get_type_categories():
    """
    Get all available type categories.
    
    Returns list of categories with type counts.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        categories = type_registry.get_categories()
        
        return {
            "status": "success",
            "categories": categories,
            "total_count": len(categories),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Get Categories Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@app.get("/types/tags")
async def get_type_tags(limit: int = Query(50, ge=1, le=200, description="Maximum number of tags")):
    """
    Get all available type tags.
    
    Returns list of unique tags used across all types.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        tags = type_registry.get_tags(limit=limit)
        
        return {
            "status": "success",
            "tags": tags,
            "total_count": len(tags),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Get Tags Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {str(e)}")

@app.get("/types/stats")
async def get_type_stats():
    """
    Get comprehensive type system statistics.
    
    Returns system-wide statistics including type counts, categories, and usage.
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        stats = type_registry.get_statistics()
        usage_stats = type_registry.get_usage_stats()
        
        return {
            "status": "success",
            "statistics": stats,
            "usage": usage_stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Type Stats Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get type stats: {str(e)}")


# ==================== Type-Based Generation Endpoints ====================

@app.post("/generate/from-type")
async def generate_from_type(request_data: dict):
    """
    Generate asset from ElementType definition with optional variations.
    
    Body: {
        "type_id": "string",           # ElementType ID
        "params": { ... },             # Optional parameter overrides
        "variations": { ... },         # Optional diversity configuration
        "seed": 123                    # Optional seed for reproducible results
    }
    
    Returns:
        PNG image of the generated asset
    """
    if not HAS_TYPE_AWARE_SYSTEM or not type_aware_loader:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        type_id = request_data.get('type_id')
        if not type_id:
            raise HTTPException(status_code=400, detail="type_id is required")
        
        # Get parameter overrides and variations
        params = request_data.get('params', {})
        variations = request_data.get('variations')
        seed = request_data.get('seed')
        
        # Create generator from type
        generator = type_aware_loader.create_generator_from_type_id(
            type_id=type_id,
            parameter_overrides=params,
            diversity_config=variations,
            seed=seed
        )
        
        if generator is None:
            available_types = type_aware_loader.get_supported_types()
            raise HTTPException(
                status_code=400,
                detail=f"Type '{type_id}' not found or not supported. Available: {available_types}"
            )
        
        # Generate the asset
        img = generator.generate(**params)
        
        print(f"✨ Generated asset from type {type_id} using type-aware system")
        return serve_pil_image(img)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type-based Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate from type: {str(e)}")


@app.get("/generate/types")
async def list_generatable_types():
    """
    Get list of ElementTypes that can be used for generation.
    
    Returns:
        List of supported type IDs and their basic information
    """
    if not HAS_TYPE_AWARE_SYSTEM or not type_aware_loader:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        supported_types = type_aware_loader.get_supported_types()
        
        # Get detailed info for each type
        types_info = []
        for type_id in supported_types:
            type_info = type_aware_loader.get_type_info(type_id)
            if type_info:
                types_info.append({
                    "id": type_id,
                    "name": type_info.get('type_name', type_id),
                    "category": type_info.get('category'),
                    "description": type_info.get('description'),
                    "generator_name": type_info.get('generator_name'),
                    "supported": type_info.get('supported', False),
                    "has_variants": type_info.get('has_variants', False),
                    "has_diversity": type_info.get('has_diversity', False)
                })
        
        return {
            "status": "success",
            "types": types_info,
            "total_count": len(types_info),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ List Generatable Types Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list generatable types: {str(e)}")


@app.post("/generate/type-batch")
async def generate_type_batch(request_data: dict, background_tasks: BackgroundTasks):
    """
    Generate multiple variations from ElementType definitions.
    
    Body: {
        "type_ids": ["type1", "type2"],        # List of ElementType IDs
        "count_per_type": 5,                   # Number of variations per type
        "parameter_overrides": {               # Optional parameter overrides per type
            "type1": { "width": 512 },
            "type2": { "color": "#ff0000" }
        },
        "seeds": {                             # Optional seeds per type
            "type1": 123,
            "type2": 456
        },
        "output_format": "image"               # "image", "metadata", or "both"
    }
    
    Returns:
        Batch job ID for tracking progress
    """
    if not HAS_TYPE_AWARE_SYSTEM or not type_batch_generator:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        type_ids = request_data.get('type_ids', [])
        count_per_type = request_data.get('count_per_type', 5)
        parameter_overrides = request_data.get('parameter_overrides', {})
        seeds = request_data.get('seeds', {})
        output_format = request_data.get('output_format', 'image')
        
        if not type_ids:
            raise HTTPException(status_code=400, detail="type_ids cannot be empty")
        
        # Create batch job
        batch_id = type_batch_generator.generate_batch_from_types(
            type_ids=type_ids,
            count_per_type=count_per_type,
            parameter_overrides=parameter_overrides,
            seeds=seeds,
            output_format=output_format
        )
        
        return {
            "batch_id": batch_id,
            "status": "created",
            "total_items": len(type_ids) * count_per_type,
            "type_ids": type_ids,
            "count_per_type": count_per_type,
            "output_format": output_format,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Type Batch Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create type batch: {str(e)}")


@app.get("/generate/type-batch/{batch_id}/status")
async def get_type_batch_status(batch_id: str):
    """
    Get status of a type-based batch generation job.
    
    Args:
        batch_id: Batch job ID
        
    Returns:
        Current batch status and progress
    """
    if not HAS_TYPE_AWARE_SYSTEM or not type_batch_generator:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        status_info = type_batch_generator.get_batch_status(batch_id)
        if not status_info:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        return {
            "status": "success",
            "batch_status": status_info,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type Batch Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@app.get("/generate/type-batch/{batch_id}/results")
async def get_type_batch_results(batch_id: str):
    """
    Get results from a completed type-based batch generation job.
    
    Args:
        batch_id: Batch job ID
        
    Returns:
        List of generation results
    """
    if not HAS_TYPE_AWARE_SYSTEM or not type_batch_generator:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        results = type_batch_generator.get_batch_results(batch_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Batch job not found or not completed")
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "results_count": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type Batch Results Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch results: {str(e)}")


@app.get("/generate/variation-strategies")
async def get_variation_strategies():
    """
    Get available variation strategies for type-based generation.
    
    Returns:
        List of available variation strategies and their descriptions
    """
    if not HAS_TYPE_AWARE_SYSTEM or not variation_engine:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        strategies = variation_engine.get_available_strategies()
        strategy_info = {}
        
        for strategy_name in strategies:
            info = variation_engine.get_strategy_info(strategy_name)
            if info:
                strategy_info[strategy_name] = info
        
        return {
            "status": "success",
            "strategies": strategy_info,
            "total_count": len(strategies),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Variation Strategies Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get variation strategies: {str(e)}")


@app.get("/generate/type-stats")
async def get_type_generation_stats():
    """
    Get comprehensive statistics about type-based generation system.
    
    Returns:
        System statistics including types, generators, and batch processing
    """
    if not HAS_TYPE_AWARE_SYSTEM:
        raise HTTPException(status_code=503, detail="Type-aware generation system disabled")
    
    try:
        stats = {
            "type_aware_system": {
                "available": HAS_TYPE_AWARE_SYSTEM,
                "supported_types": len(type_aware_loader.get_supported_types()) if type_aware_loader else 0,
                "loader_stats": type_aware_loader.get_statistics() if type_aware_loader else {}
            },
            "batch_system": {
                "available": type_batch_generator is not None,
                "batch_stats": type_batch_generator.get_statistics() if type_batch_generator else {}
            },
            "variation_system": {
                "available": variation_engine is not None,
                "strategies": variation_engine.get_available_strategies() if variation_engine else []
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Type Generation Stats Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get type generation stats: {str(e)}")



# ==================== LLM Type Creation Endpoints ====================

@app.post("/llm/create-type")
async def create_type_from_llm(
    request_data: dict,
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    base_url_header: str | None = Header(default=None, alias="X-Base-Url"),
    model: str = Query("gpt-4o-2024-08-06", description="LLM model to use")
):
    """
    Create a new ElementType from natural language description using LLM.
    
    Body: {
        "description": "A mystical glyph with ancient symbols and glowing properties",
        "context": { ... }  # Optional context information
    }
    
    Headers:
        X-API-Key: API key for LLM service
        X-Base-Url: Optional base URL for LLM API
    """
    try:
        # Import LLM functions
        from llm_director import create_element_type_from_prompt
        
        description = request_data.get('description', '').strip()
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")
        
        if len(description) > 1000:
            raise HTTPException(status_code=400, detail="Description too long (max 1000 characters)")
        
        context = request_data.get('context', {})
        
        # Get API key
        api_key = api_key_header or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="No API key provided. Pass X-API-Key header or configure .env")
        
        base_url = base_url_header or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")
        
        # Create type using LLM
        result = create_element_type_from_prompt(
            description=description,
            api_key=api_key,
            context=context,
            model=model,
            base_url=base_url
        )
        
        if result.get('success'):
            # Try to add to registry if available
            if HAS_TYPE_SYSTEM and type_registry and 'type_data' in result:
                try:
                    from enhanced_design.element_types import ElementType
                    element_type = ElementType(**result['type_data'])
                    type_registry.add(element_type)
                    result['persisted'] = True
                except Exception as e:
                    result['persisted'] = False
                    result['registry_error'] = str(e)
            
            return {
                "status": "success",
                "type_id": result.get('type_id'),
                "type_data": result.get('type_data'),
                "validation_result": result.get('validation_result'),
                "llm_model": result.get('llm_model'),
                "persisted": result.get('persisted', False),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Type creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ LLM Type Creation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create type: {str(e)}")


@app.post("/llm/refine-type/{type_id}")
async def refine_type_with_llm(
    type_id: str,
    request_data: dict,
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    base_url_header: str | None = Header(default=None, alias="X-Base-Url"),
    model: str = Query("gpt-4o-2024-08-06", description="LLM model to use")
):
    """
    Refine an existing ElementType based on user feedback using LLM.
    
    Body: {
        "feedback": "Make it more mystical and add parameters for color intensity"
    }
    
    Headers:
        X-API-Key: API key for LLM service
        X-Base-Url: Optional base URL for LLM API
    """
    try:
        # Import LLM functions
        from llm_director import refine_element_type
        
        feedback = request_data.get('feedback', '').strip()
        if not feedback:
            raise HTTPException(status_code=400, detail="Feedback is required")
        
        if len(feedback) > 1000:
            raise HTTPException(status_code=400, detail="Feedback too long (max 1000 characters)")
        
        # Get API key
        api_key = api_key_header or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="No API key provided. Pass X-API-Key header or configure .env")
        
        base_url = base_url_header or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")
        
        # Check if type exists
        if HAS_TYPE_SYSTEM and type_registry:
            existing_type = type_registry.get(type_id)
            if not existing_type:
                raise HTTPException(status_code=404, detail=f"Type '{type_id}' not found")
        
        # Refine type using LLM
        result = refine_element_type(
            type_id=type_id,
            feedback=feedback,
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        
        if result.get('success'):
            # Try to update in registry if available
            updated = False
            if HAS_TYPE_SYSTEM and type_registry and 'type_data' in result:
                try:
                    from enhanced_design.element_types import ElementType
                    element_type = ElementType(**result['type_data'])
                    updated = type_registry.update(element_type)
                except Exception as e:
                    print(f"⚠️ Failed to update registry: {e}")
            
            return {
                "status": "success",
                "type_id": result.get('type_id'),
                "type_data": result.get('type_data'),
                "validation_result": result.get('validation_result'),
                "refinement_feedback": feedback,
                "updated_in_registry": updated,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Type refinement failed: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ LLM Type Refinement Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refine type: {str(e)}")


@app.post("/llm/validate-type")
async def validate_type_with_llm(request_data: dict):
    """
    Validate an ElementType definition using the comprehensive validator.
    
    Body: {
        "type_data": { ... }  # ElementType definition to validate
    }
    
    Returns:
        Detailed validation results with errors, warnings, and suggestions
    """
    try:
        # Import validation functions
        from llm_director import validate_element_type_schema
        
        type_data = request_data.get('type_data')
        if not type_data:
            raise HTTPException(status_code=400, detail="type_data is required")
        
        # Validate type using validator
        result = validate_element_type_schema(type_data)
        
        return {
            "status": "success",
            "validation_result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type Validation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate type: {str(e)}")


@app.get("/llm/type-templates")
async def get_type_templates():
    """
    Get available type templates for common categories.
    
    Returns:
        List of template information for glyphs, creatures, backgrounds, effects
    """
    try:
        # Import template functions
        from llm_director import list_available_templates
        
        templates = list_available_templates()
        
        return {
            "status": "success",
            "templates": templates,
            "total_count": len(templates),
            "categories": list(set(t['category'] for t in templates)),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Type Templates Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@app.get("/llm/type-examples")
async def get_type_examples():
    """
    Get example ElementType definitions for reference and learning.
    
    Returns:
        List of example type definitions showing best practices
    """
    try:
        # Import example functions
        from llm_director import get_example_type_definitions
        
        examples = get_example_type_definitions()
        
        return {
            "status": "success",
            "examples": examples,
            "total_count": len(examples),
            "categories": list(set(ex.get('category') for ex in examples)),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Type Examples Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get examples: {str(e)}")


@app.get("/llm/templates/{template_id}")
async def get_template_details(template_id: str):
    """
    Get detailed information about a specific template.
    
    Args:
        template_id: ID of the template (glyph_template, creature_part_template, etc.)
        
    Returns:
        Complete template definition with parameters and examples
    """
    try:
        # Try to load from file system first
        template_path = f"storage/types/templates/{template_id}.json"
        
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template_data = json.load(f)
            
            return {
                "status": "success",
                "template": template_data,
                "source": "file_system",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Template Details Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template details: {str(e)}")


@app.get("/llm/stats")
async def get_llm_type_creation_stats():
    """
    Get comprehensive statistics for LLM type creation system.
    
    Returns:
        System statistics including performance metrics and usage data
    """
    try:
        # Import stats functions
        from llm_director import get_type_creation_stats
        
        # Get LLM director stats
        llm_stats = get_type_creation_stats()
        
        # Get type registry stats if available
        registry_stats = {}
        if HAS_TYPE_SYSTEM and type_registry:
            try:
                registry_stats = type_registry.get_statistics()
            except Exception as e:
                registry_stats = {"error": str(e)}
        
        return {
            "status": "success",
            "llm_director": llm_stats,
            "type_registry": registry_stats,
            "system_capabilities": {
                "type_creation_enabled": llm_stats.get("type_creation_enabled", False),
                "type_system_available": HAS_TYPE_SYSTEM,
                "llm_available": HAS_LLM,
                "templates_available": True,
                "improvement_system": True
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ LLM Type Creation Stats Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ==================== Type Improvement Endpoints ====================

@app.post("/types/{type_id}/analyze-usage")
async def analyze_type_usage(type_id: str, days: int = Query(30, description="Number of days to analyze")):
    """
    Analyze usage patterns for a specific type.
    
    Args:
        type_id: Type identifier to analyze
        days: Number of days to analyze (default: 30)
        
    Returns:
        Comprehensive usage analysis with patterns and recommendations
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Import Type Improver
        from llm.type_improver import TypeImprover
        
        improver = TypeImprover()
        analysis = improver.analyze_type_usage(type_id, days)
        
        return {
            "status": "success",
            "type_id": type_id,
            "analysis": {
                "usage_count": analysis.usage_count,
                "success_rate": analysis.success_rate,
                "avg_generation_time": analysis.avg_generation_time,
                "error_rate": analysis.error_rate,
                "pattern": analysis.pattern.value,
                "usage_frequency": analysis.usage_frequency,
                "performance_score": analysis.performance_score,
                "last_used": analysis.last_used.isoformat() + "Z" if analysis.last_used else None,
                "recommendations": analysis.get_recommendations()
            },
            "analysis_window_days": days,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type Usage Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze type usage: {str(e)}")


@app.post("/types/{type_id}/suggest-improvements")
async def suggest_type_improvements(
    type_id: str,
    analysis_data: dict | None = None,
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get improvement suggestions for a type based on usage and best practices.
    
    Args:
        type_id: Type identifier to improve
        analysis_data: Optional pre-computed usage analysis
        days: Number of days to analyze if no analysis provided
        
    Returns:
        List of improvement suggestions with priorities and impact estimates
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Import Type Improver
        from llm.type_improver import TypeImprover
        
        improver = TypeImprover()
        
        # Get analysis if not provided
        analysis = None
        if analysis_data:
            # Convert analysis_data back to UsageAnalysis (simplified)
            pass
        else:
            analysis = improver.analyze_type_usage(type_id, days)
        
        # Get suggestions
        suggestions = improver.suggest_improvements(type_id, analysis)
        
        return {
            "status": "success",
            "type_id": type_id,
            "suggestions": [s.to_dict() for s in suggestions],
            "suggestions_count": len(suggestions),
            "high_priority_count": len([s for s in suggestions if s.priority >= 8]),
            "analysis_window_days": days if not analysis_data else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type Improvement Suggestions Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get improvement suggestions: {str(e)}")


@app.post("/types/{type_id}/auto-optimize")
async def auto_optimize_type(type_id: str, max_changes: int = Query(5, description="Maximum changes to apply")):
    """
    Automatically apply safe optimizations to a type.
    
    Args:
        type_id: Type identifier to optimize
        max_changes: Maximum number of changes to apply (default: 5)
        
    Returns:
        Optimized type definition and applied changes
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Import Type Improver
        from llm.type_improver import TypeImprover
        
        improver = TypeImprover()
        optimized_type = improver.auto_optimize_type(type_id, max_changes)
        
        # Update in registry
        updated = type_registry.update(optimized_type)
        
        return {
            "status": "success",
            "type_id": type_id,
            "optimized_type": optimized_type.to_dict(),
            "updated_in_registry": updated,
            "max_changes_requested": max_changes,
            "optimization_applied": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Type Auto-Optimization Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to auto-optimize type: {str(e)}")


@app.get("/improvement/metrics")
async def get_improvement_metrics():
    """
    Get comprehensive improvement metrics across all types.
    
    Returns:
        System-wide improvement analytics and recommendations
    """
    if not HAS_TYPE_SYSTEM or not type_registry:
        raise HTTPException(status_code=503, detail="Type system disabled")
    
    try:
        # Import Type Improver
        from llm.type_improver import TypeImprover
        
        improver = TypeImprover()
        metrics = improver.get_improvement_metrics()
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Improvement Metrics Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get improvement metrics: {str(e)}")


# ==================== Diversity System API Endpoints ====================

try:
    from utils.diversity_metrics import DiversityMetrics
    from storage.diversity_tracker import DiversityTracker
    from utils.diversity_viz import DiversityViz
    from generators.diversity_optimizer import DiversityOptimizer
    HAS_DIVERSITY_SYSTEM = True
except ImportError as e:
    print(f"⚠️ Diversity system not available: {e}")
    HAS_DIVERSITY_SYSTEM = False

# Initialize diversity system components if available
if HAS_DIVERSITY_SYSTEM:
    diversity_metrics = DiversityMetrics()
    diversity_tracker = DiversityTracker()
    diversity_viz = DiversityViz()
    diversity_optimizer = DiversityOptimizer()
    print("🔄 Diversity system initialized")
else:
    diversity_metrics = diversity_tracker = diversity_viz = diversity_optimizer = None
    print("📦 Diversity system disabled")


@app.post("/diversity/analyze-parameters")
async def analyze_parameter_diversity(request_data: dict):
    """
    Analyze parameter diversity for a set of generation parameters.
    
    Body: {
        "params_list": [
            {"width": 512, "height": 512, "complexity": 0.7},
            {"width": 256, "height": 256, "complexity": 0.3}
        ],
        "type_id": "optional_type_id"
    }
    
    Returns:
        Comprehensive diversity analysis with scores and recommendations
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_metrics:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        params_list = request_data.get('params_list', [])
        type_id = request_data.get('type_id')
        
        if not params_list:
            raise HTTPException(status_code=400, detail="params_list cannot be empty")
        
        # Analyze parameter diversity
        diversity_score = diversity_metrics.calculate_parameter_diversity(params_list)
        
        # Get detailed analysis
        analysis = {
            "diversity_score": diversity_score,
            "total_parameters": len(params_list),
            "parameter_count": len(params_list[0].keys()) if params_list else 0,
            "entropy_breakdown": diversity_metrics.get_entropy_breakdown(params_list),
            "coverage_analysis": diversity_metrics.analyze_parameter_coverage(params_list)
        }
        
        # Add type-specific analysis if type_id provided
        if type_id:
            analysis["type_specific"] = {
                "type_id": type_id,
                "expected_score": 0.8,  # Would get from ElementType diversity_config
                "meets_target": diversity_score >= 0.8,
                "recommendations": diversity_metrics.get_improvement_recommendations(params_list, target_score=0.8)
            }
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Parameter Diversity Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze parameter diversity: {str(e)}")


@app.post("/diversity/analyze-outputs")
async def analyze_output_diversity(request_data: dict):
    """
    Analyze output asset diversity for generated assets.
    
    Body: {
        "assets_list": [
            {"asset_id": "asset1", "image_data": "base64_data"},
            {"asset_id": "asset2", "image_data": "base64_data"}
        ],
        "analysis_type": "visual"  # "visual", "metadata", or "both"
    }
    
    Returns:
        Output diversity analysis with visual and metadata diversity scores
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_metrics:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        assets_list = request_data.get('assets_list', [])
        analysis_type = request_data.get('analysis_type', 'both')
        
        if not assets_list:
            raise HTTPException(status_code=400, detail="assets_list cannot be empty")
        
        # Analyze output diversity
        diversity_analysis = diversity_metrics.calculate_output_diversity(assets_list, analysis_type)
        
        return {
            "status": "success",
            "analysis": diversity_analysis,
            "assets_count": len(assets_list),
            "analysis_type": analysis_type,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Output Diversity Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze output diversity: {str(e)}")


@app.get("/diversity/type/{type_id}/history")
async def get_type_diversity_history(
    type_id: str,
    days: int = Query(30, description="Number of days to look back"),
    format: str = Query("json", description="Response format: json or chart")
):
    """
    Get diversity history for a specific ElementType.
    
    Args:
        type_id: ElementType identifier
        days: Number of days to analyze (default: 30)
        format: Response format (json, chart, or both)
        
    Returns:
        Historical diversity metrics and trends for the type
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_tracker:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        # Get diversity history
        history_data = diversity_tracker.get_type_diversity_history(type_id, days=days)
        
        # Get trend analysis
        trend_analysis = diversity_tracker.analyze_diversity_trend(type_id, days=days)
        
        # Generate chart if requested
        chart_data = None
        if format in ['chart', 'both']:
            chart_data = diversity_viz.plot_diversity_timeline(type_id, days=days)
        
        response_data = {
            "status": "success",
            "type_id": type_id,
            "history": history_data,
            "trend_analysis": trend_analysis,
            "days_analyzed": days,
            "format": format,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if chart_data:
            response_data["chart"] = chart_data
        
        return response_data
        
    except Exception as e:
        print(f"❌ Type Diversity History Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diversity history: {str(e)}")


@app.get("/diversity/overview")
async def get_diversity_overview():
    """
    Get system-wide diversity overview.
    
    Returns:
        Comprehensive overview of diversity across all types and systems
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_tracker:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        # Get overall diversity metrics
        overview = diversity_tracker.get_overall_diversity_overview()
        
        # Get type rankings
        type_rankings = diversity_tracker.get_type_diversity_rankings(limit=10)
        
        # Get system health metrics
        health_metrics = diversity_tracker.get_diversity_health_metrics()
        
        return {
            "status": "success",
            "overview": overview,
            "type_rankings": type_rankings,
            "health_metrics": health_metrics,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Diversity Overview Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diversity overview: {str(e)}")


@app.post("/diversity/generate-report")
async def generate_diversity_report(request_data: dict):
    """
    Generate comprehensive diversity report.
    
    Body: {
        "type_ids": ["type1", "type2"],  # Optional, defaults to all types
        "days": 30,                      # Analysis window
        "include_charts": true,          # Include visualization charts
        "include_recommendations": true  # Include improvement recommendations
    }
    
    Returns:
        Comprehensive diversity report with metrics, analysis, and recommendations
    """
    if not HAS_DIVERSITY_SYSTEM:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        type_ids = request_data.get('type_ids')
        days = request_data.get('days', 30)
        include_charts = request_data.get('include_charts', True)
        include_recommendations = request_data.get('include_recommendations', True)
        
        # Generate comprehensive report
        report = diversity_tracker.generate_comprehensive_report(
            type_ids=type_ids,
            days=days,
            include_charts=include_charts,
            include_recommendations=include_recommendations
        )
        
        return {
            "status": "success",
            "report": report,
            "report_id": report.get('report_id'),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Diversity Report Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate diversity report: {str(e)}")


@app.post("/diversity/optimize/{type_id}")
async def optimize_type_diversity(
    type_id: str,
    request_data: dict
):
    """
    Optimize diversity configuration for a specific type.
    
    Args:
        type_id: ElementType identifier to optimize
        
    Body: {
        "optimization_goals": ["maximize_variety", "ensure_quality"],  # Optimization priorities
        "max_changes": 5,                                             # Maximum changes to apply
        "preserve_existing": true                                     # Whether to preserve current settings
    }
    
    Returns:
        Optimized diversity configuration with applied changes and recommendations
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_optimizer:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        optimization_goals = request_data.get('optimization_goals', ['maximize_variety'])
        max_changes = request_data.get('max_changes', 5)
        preserve_existing = request_data.get('preserve_existing', True)
        
        # Check if type exists
        if HAS_TYPE_SYSTEM and type_registry:
            element_type = type_registry.get(type_id)
            if not element_type:
                raise HTTPException(status_code=404, detail=f"Type '{type_id}' not found")
        
        # Optimize diversity
        optimized_config = diversity_optimizer.optimize_type_diversity(
            type_id=type_id,
            optimization_goals=optimization_goals,
            max_changes=max_changes,
            preserve_existing=preserve_existing
        )
        
        # Get improvement suggestions
        suggestions = diversity_optimizer.suggest_diversity_improvements(type_id)
        
        return {
            "status": "success",
            "type_id": type_id,
            "optimized_config": optimized_config,
            "applied_changes": optimized_config.get('applied_changes', []),
            "suggestions": suggestions,
            "optimization_goals": optimization_goals,
            "max_changes_requested": max_changes,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Diversity Optimization Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize diversity: {str(e)}")


@app.post("/diversity/generate-diverse-batch")
async def generate_diverse_batch(request_data: dict):
    """
    Generate a batch of diverse parameter sets for efficient multi-asset generation.
    
    Body: {
        "type_id": "type_id",           # ElementType to generate for
        "count": 20,                     # Number of parameter sets to generate
        "target_diversity": 0.8,         # Target diversity score
        "sampling_strategy": "latin_hypercube"  # Sampling strategy
    }
    
    Returns:
        List of diverse parameter sets ready for batch generation
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_optimizer:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        type_id = request_data.get('type_id')
        count = request_data.get('count', 10)
        target_diversity = request_data.get('target_diversity', 0.8)
        sampling_strategy = request_data.get('sampling_strategy', 'latin_hypercube')
        
        if not type_id:
            raise HTTPException(status_code=400, detail="type_id is required")
        
        # Generate diverse parameter sets
        diverse_params = diversity_optimizer.generate_diverse_batch(
            element_type=type_id,
            count=count,
            target_diversity=target_diversity,
            sampling_strategy=sampling_strategy
        )
        
        # Analyze the diversity of generated parameters
        diversity_analysis = diversity_metrics.calculate_parameter_diversity(diverse_params)
        
        return {
            "status": "success",
            "type_id": type_id,
            "parameter_sets": diverse_params,
            "count_generated": len(diverse_params),
            "diversity_analysis": {
                "diversity_score": diversity_analysis,
                "target_achieved": diversity_analysis >= target_diversity,
                "sampling_strategy": sampling_strategy
            },
            "target_diversity": target_diversity,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Diverse Batch Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate diverse batch: {str(e)}")


@app.get("/diversity/visualization/{type_id}")
async def get_diversity_visualization(
    type_id: str,
    chart_type: str = Query("timeline", description="Chart type: timeline, distribution, or dashboard"),
    days: int = Query(30, description="Number of days for timeline charts")
):
    """
    Get diversity visualization for a type.
    
    Args:
        type_id: ElementType identifier
        chart_type: Type of chart to generate
        days: Analysis window for timeline charts
        
    Returns:
        Base64-encoded chart image and metadata
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_viz:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        # Generate appropriate visualization
        if chart_type == "timeline":
            chart_data = diversity_viz.plot_diversity_timeline(type_id, days=days)
        elif chart_type == "distribution":
            chart_data = diversity_viz.plot_parameter_distribution_for_type(type_id)
        elif chart_type == "dashboard":
            chart_data = diversity_viz.create_diversity_dashboard(type_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")
        
        return {
            "status": "success",
            "type_id": type_id,
            "chart_type": chart_type,
            "chart_data": chart_data,
            "days": days if chart_type == "timeline" else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Diversity Visualization Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate diversity visualization: {str(e)}")


@app.post("/diversity/record-generation")
async def record_diversity_generation(request_data: dict):
    """
    Record a generation event for diversity tracking.
    
    Body: {
        "type_id": "type_id",
        "generation_params": {...},
        "diversity_score": 0.8,
        "asset_metadata": {...}  # Optional asset metadata
    }
    
    Returns:
        Confirmation of recording with updated diversity metrics
    """
    if not HAS_DIVERSITY_SYSTEM or not diversity_tracker:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        type_id = request_data.get('type_id')
        generation_params = request_data.get('generation_params', {})
        diversity_score = request_data.get('diversity_score')
        asset_metadata = request_data.get('asset_metadata', {})
        
        if not type_id:
            raise HTTPException(status_code=400, detail="type_id is required")
        
        # Record generation
        success = diversity_tracker.record_generation(
            type_id=type_id,
            generation_params=generation_params,
            diversity_score=diversity_score,
            asset_metadata=asset_metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to record generation")
        
        # Get updated metrics
        updated_metrics = diversity_tracker.get_current_diversity_metrics(type_id)
        
        return {
            "status": "success",
            "recorded": True,
            "type_id": type_id,
            "updated_metrics": updated_metrics,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Diversity Recording Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record diversity generation: {str(e)}")


@app.get("/diversity/stats")
async def get_diversity_system_stats():
    """
    Get comprehensive diversity system statistics.
    
    Returns:
        System-wide diversity metrics, performance, and health indicators
    """
    if not HAS_DIVERSITY_SYSTEM:
        raise HTTPException(status_code=503, detail="Diversity system disabled")
    
    try:
        # Get system statistics
        stats = {
            "diversity_system": {
                "available": HAS_DIVERSITY_SYSTEM,
                "components": {
                    "metrics": diversity_metrics is not None,
                    "tracking": diversity_tracker is not None,
                    "visualization": diversity_viz is not None,
                    "optimization": diversity_optimizer is not None
                }
            },
            "tracking_stats": diversity_tracker.get_system_statistics() if diversity_tracker else {},
            "performance_metrics": diversity_metrics.get_performance_metrics() if diversity_metrics else {},
            "optimization_stats": diversity_optimizer.get_optimization_stats() if diversity_optimizer else {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"❌ Diversity System Stats Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diversity system stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🍌 NanoBanana API starting up...")
    print(f"   - LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', 'Not Set (will use default)')}")
    key = os.environ.get('OPENAI_API_KEY', '')
    masked_key = f"{key[:8]}...{key[-4:]}" if key else "Not Set"
    print(f"   - OPENAI_API_KEY: {masked_key}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
