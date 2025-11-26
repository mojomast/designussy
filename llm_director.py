import os
import json
import time
import hashlib
import threading
import requests
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import Type Creation components
try:
    from .llm.type_creator import LLMTypeCreator
    from .llm.type_validator import TypeValidator, ValidationResult
    from .enhanced_design.element_types import ElementType
    from .enhanced_design.type_registry import get_type_registry
    HAS_TYPE_SYSTEM = True
except ImportError as e:
    HAS_TYPE_SYSTEM = False
    print(f"Type system not available: {e}")

# Performance monitoring
class PerformanceTracker:
    """Track LLM Director performance metrics."""
    
    def __init__(self):
        self.stats = {
            'llm_calls': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'errors': 0
        }
        self._lock = threading.Lock()
    
    def record_call(self, duration: float, success: bool):
        """Record performance metrics for an LLM call."""
        with self._lock:
            self.stats['llm_calls'] += 1
            self.stats['total_time'] += duration
            if not success:
                self.stats['errors'] += 1
    
    def record_cache_hit(self):
        """Record a cache hit."""
        with self._lock:
            self.stats['cache_hits'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            stats = self.stats.copy()
            if stats['llm_calls'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['llm_calls']
                stats['error_rate'] = stats['errors'] / stats['llm_calls']
                stats['cache_hit_rate'] = stats['cache_hits'] / stats['llm_calls']
            return stats

# Global performance tracker
_performance_tracker = PerformanceTracker()

# Session with connection pooling and retry strategy
def _create_optimized_session() -> requests.Session:
    """Create an optimized requests session with connection pooling and retry logic."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(
        pool_connections=20,
        pool_maxsize=20,
        max_retries=retry_strategy
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Global optimized session
_session = _create_optimized_session()

# 1. Define the Structure (Pydantic used for validation after receiving JSON)
class EnsoParams(BaseModel):
    color_hex: str = Field(description="The hex color of the ink, e.g., #FF0000")
    complexity: int = Field(description="Number of brush strokes (20-100)")
    chaos: float = Field(description="How messy/wobbly the circle is (0.1-2.0)")
    text_overlay: str = Field(description="A short, cryptic loading message (e.g., 'ENTERING VOID')")

def get_enso_params_from_prompt(prompt: str, api_key: str, model: str = "gpt-4o-2024-08-06", base_url: str | None = None, use_cache: bool = True) -> EnsoParams:
    """
    Uses requests to call the LLM Provider (Requesty/OpenAI-compatible) and translate a vibe.
    Optimized with caching, connection pooling, and performance monitoring.
    
    Args:
        prompt: The prompt to send to the LLM
        api_key: API key for authentication
        model: Model to use
        base_url: Base URL for the API (defaults to environment variable)
        use_cache: Whether to use response caching
        
    Returns:
        EnsoParams: Parsed response from LLM
    """
    start_time = time.perf_counter()
    
    if not api_key:
        print("⚠️ No API Key provided.")
        return EnsoParams(color_hex="#FF0000", complexity=50, chaos=1.5, text_overlay="NO KEY")

    # Generate cache key
    cache_key = None
    if use_cache:
        cache_key = _generate_cache_key(prompt, model, base_url)
        cached_result = _get_cached_response(cache_key)
        if cached_result:
            _performance_tracker.record_cache_hit()
            return cached_result

    print(f"🧠 Director ({model}) thinking about: '{prompt[:50]}...'...")
    
    try:
        result = _make_llm_request(prompt, api_key, model, base_url)
        
        # Cache the result if caching is enabled
        if use_cache and cache_key:
            _cache_response(cache_key, result)
        
        # Record successful call
        duration = time.perf_counter() - start_time
        _performance_tracker.record_call(duration, success=True)
        
        return result
        
    except Exception as e:
        # Record failed call
        duration = time.perf_counter() - start_time
        _performance_tracker.record_call(duration, success=False)
        print(f"❌ Director Error: {e}")
        raise

def _generate_cache_key(prompt: str, model: str, base_url: Optional[str]) -> str:
    """Generate cache key for LLM request."""
    data = f"{prompt}|{model}|{base_url or ''}"
    return hashlib.md5(data.encode()).hexdigest()

# Simple in-memory cache with TTL
_llm_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 300  # 5 minutes

def _get_cached_response(cache_key: str) -> Optional[EnsoParams]:
    """Get cached response if available and not expired."""
    with _cache_lock:
        if cache_key in _llm_cache:
            response, timestamp = _llm_cache[cache_key]
            if time.time() - timestamp < _CACHE_TTL:
                return response
            else:
                # Remove expired entry
                del _llm_cache[cache_key]
    return None

def _cache_response(cache_key: str, result: EnsoParams):
    """Cache LLM response."""
    with _cache_lock:
        # Simple cache size limit
        if len(_llm_cache) > 100:
            # Remove oldest entry
            oldest_key = min(_llm_cache.keys(), key=lambda k: _llm_cache[k][1])
            del _llm_cache[oldest_key]
        
        _llm_cache[cache_key] = (result, time.time())

def _make_llm_request(prompt: str, api_key: str, model: str, base_url: Optional[str]) -> EnsoParams:
    """Make the actual LLM API request with optimizations."""
    
    # JSON Schema for Structured Outputs
    json_schema = {
        "name": "enso_params",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "color_hex": {"type": "string", "description": "Hex color e.g. #FF0000"},
                "complexity": {"type": "integer", "description": "Number of brush strokes (20-100)"},
                "chaos": {"type": "number", "description": "Chaos factor (0.1-2.0)"},
                "text_overlay": {"type": "string", "description": "Cryptic loading message"}
            },
            "required": ["color_hex", "complexity", "chaos", "text_overlay"],
            "additionalProperties": False
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mojomast/designussy", 
        "X-Title": "Unwritten Worlds"
    }

    # Resolve endpoint
    base = (base_url or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")).rstrip('/')
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    
    payload = {
        "model": model,
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
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": json_schema
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": "enso_params"}},
    }

    # Use optimized session with reduced timeout for faster failure detection
    response = _session.post(url, headers=headers, json=payload, timeout=(10, 20))
    response.raise_for_status()
    result = response.json()

    tool_call = result["choices"][0]["message"].get("tool_calls", [{}])[0]
    function_args = tool_call.get("function", {}).get("arguments", "{}")

    params_dict = json.loads(function_args)

    # Sanitize and clamp values
    color_hex = str(params_dict.get('color_hex', '#000000')).strip()
    if not color_hex.startswith('#'):
        color_hex = f"#{color_hex.lstrip('#')}"
    hex_part = color_hex.lstrip('#')
    if len(hex_part) == 3:
        hex_part = ''.join([c*2 for c in hex_part])
    if len(hex_part) != 6:
        hex_part = '000000'
    color_hex = f"#{hex_part}"

    try:
        complexity = int(params_dict.get('complexity', 40))
    except Exception:
        complexity = 40
    complexity = max(20, min(100, complexity))

    try:
        chaos = float(params_dict.get('chaos', 1.0))
    except Exception:
        chaos = 1.0
    chaos = max(0.1, min(2.0, chaos))

    text_overlay = str(params_dict.get('text_overlay', 'ENTERING VOID'))

    return EnsoParams(color_hex=color_hex, complexity=complexity, chaos=chaos, text_overlay=text_overlay)

def batch_get_enso_params(prompts: List[str], api_key: str, model: str = "gpt-4o-2024-08-06", 
                         base_url: Optional[str] = None, max_workers: int = 4) -> List[EnsoParams]:
    """
    Process multiple prompts in parallel for better performance.
    
    Args:
        prompts: List of prompts to process
        api_key: API key for authentication
        model: Model to use
        base_url: Base URL for the API
        max_workers: Maximum number of parallel workers
        
    Returns:
        List of EnsoParams results
    """
    results = [None] * len(prompts)
    
    def process_prompt(idx: int, prompt: str):
        try:
            result = get_enso_params_from_prompt(prompt, api_key, model, base_url, use_cache=True)
            results[idx] = result
            return result
        except Exception as e:
            print(f"❌ Batch processing error for prompt {idx}: {e}")
            # Return default parameters on error
            results[idx] = EnsoParams(color_hex="#FF0000", complexity=50, chaos=1.5, text_overlay="ERROR")
            return results[idx]
    
    # Process in parallel with limited workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_prompt, i, prompt) for i, prompt in enumerate(prompts)]
        
        # Wait for all to complete
        for future in as_completed(futures):
            future.result()  # Ensure any exceptions are raised
    
    return results

def get_llm_performance_stats() -> Dict[str, Any]:
    """Get LLM Director performance statistics."""
    return _performance_tracker.get_stats()

def clear_llm_cache():
    """Clear the LLM response cache."""
    with _cache_lock:
        _llm_cache.clear()


# ==================== LLM Type Creation Functions ====================

def create_element_type_from_prompt(description: str, api_key: str, context: Optional[Dict[str, Any]] = None, 
                                  model: str = "gpt-4o-2024-08-06", base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new ElementType from natural language description using LLM.
    
    Args:
        description: Natural language description of the desired element type
        api_key: API key for LLM authentication
        context: Additional context information
        model: LLM model to use
        base_url: Base URL for the API
        
    Returns:
        Dictionary with type data and validation results
    """
    if not HAS_TYPE_SYSTEM:
        return {
            "success": False,
            "error": "Type system not available",
            "type_data": None,
            "validation_result": None
        }
    
    try:
        # Initialize Type Creator
        type_creator = LLMTypeCreator(api_key=api_key, model=model, base_url=base_url)
        
        # Create the element type
        element_type = type_creator.propose_element_type(description, context)
        
        return {
            "success": True,
            "type_data": element_type.to_dict(),
            "type_id": element_type.id,
            "validation_result": "Valid",
            "llm_prompt": element_type.llm_prompt,
            "llm_model": element_type.llm_model
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type_data": None,
            "validation_result": None
        }


def refine_element_type(type_id: str, feedback: str, api_key: str, 
                       model: str = "gpt-4o-2024-08-06", base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Refine an existing element type based on user feedback.
    
    Args:
        type_id: ID of the element type to refine
        feedback: Natural language feedback for improvement
        api_key: API key for LLM authentication
        model: LLM model to use
        base_url: Base URL for the API
        
    Returns:
        Dictionary with refined type data and validation results
    """
    if not HAS_TYPE_SYSTEM:
        return {
            "success": False,
            "error": "Type system not available",
            "type_data": None,
            "validation_result": None
        }
    
    try:
        # Initialize Type Creator
        type_creator = LLMTypeCreator(api_key=api_key, model=model, base_url=base_url)
        
        # Refine the element type
        element_type = type_creator.refine_element_type(type_id, feedback)
        
        return {
            "success": True,
            "type_data": element_type.to_dict(),
            "type_id": element_type.id,
            "validation_result": "Valid",
            "refinement_feedback": feedback
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type_data": None,
            "validation_result": None
        }


def validate_element_type_schema(type_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an element type definition using the TypeValidator.
    
    Args:
        type_data: Dictionary containing element type definition
        
    Returns:
        Dictionary with validation results
    """
    if not HAS_TYPE_SYSTEM:
        return {
            "is_valid": False,
            "errors": ["Type system not available"],
            "warnings": [],
            "suggestions": [],
            "summary": "Validation unavailable"
        }
    
    try:
        # Create ElementType instance for validation
        element_type = ElementType(**type_data)
        
        # Initialize validator
        validator = TypeValidator()
        
        # Perform validation
        validation_result = validator.validate_all(element_type)
        
        return {
            "is_valid": validation_result.is_valid,
            "errors": [issue.message for issue in validation_result.issues if issue.severity.value == "error"],
            "warnings": [issue.message for issue in validation_result.issues if issue.severity.value == "warning"],
            "suggestions": [issue.message for issue in validation_result.issues if issue.severity.value == "suggestion"],
            "summary": validation_result.get_summary(),
            "detailed_report": validation_result.get_detailed_report()
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "suggestions": [],
            "summary": "Validation failed"
        }


def get_type_creation_stats() -> Dict[str, Any]:
    """
    Get performance statistics for LLM type creation operations.
    
    Returns:
        Dictionary with performance metrics
    """
    base_stats = get_llm_performance_stats()
    
    if HAS_TYPE_SYSTEM:
        # Add type-specific stats if available
        try:
            # This would be populated by the LLMTypeCreator instances
            return {
                **base_stats,
                "type_creation_enabled": True,
                "type_system_available": True
            }
        except:
            pass
    
    return {
        **base_stats,
        "type_creation_enabled": False,
        "type_system_available": HAS_TYPE_SYSTEM
    }


# ==================== Type Creation Helper Functions ====================

def list_available_templates() -> List[Dict[str, str]]:
    """
    List available type templates for common categories.
    
    Returns:
        List of template information dictionaries
    """
    templates = [
        {
            "id": "glyph_template",
            "name": "Glyph Template",
            "description": "Template for creating symbol/glyph types",
            "category": "glyphs",
            "parameters": ["complexity", "style", "ink_density"]
        },
        {
            "id": "creature_part_template", 
            "name": "Creature Part Template",
            "description": "Template for creating creature components",
            "category": "creatures",
            "parameters": ["size", "mood", "species_type", "detail_level"]
        },
        {
            "id": "background_template",
            "name": "Background Template", 
            "description": "Template for creating background/texture types",
            "category": "backgrounds",
            "parameters": ["darkness", "texture", "atmosphere", "color_palette"]
        },
        {
            "id": "effect_template",
            "name": "Effect Template",
            "description": "Template for creating visual effects",
            "category": "effects", 
            "parameters": ["intensity", "duration", "color", "size"]
        }
    ]
    
    return templates


def get_example_type_definitions() -> List[Dict[str, Any]]:
    """
    Get example element type definitions for reference.
    
    Returns:
        List of example type definitions
    """
    examples = [
        {
            "id": "mystical_glyph_example",
            "name": "Mystical Glyph",
            "description": "Ancient symbols with mystical properties, featuring complex geometric patterns",
            "category": "glyphs",
            "tags": ["mystical", "ancient", "symbol", "geometric", "complex"],
            "render_strategy": {"engine": "pil", "generator_name": "sigil"},
            "param_schema": {
                "type": "object",
                "properties": {
                    "complexity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                        "description": "Geometric complexity of the symbol"
                    },
                    "mysticism_level": {
                        "type": "float",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.7,
                        "description": "Intensity of mystical properties"
                    }
                }
            },
            "version": "1.0.0"
        },
        {
            "id": "void_parchment_example",
            "name": "Void Parchment",
            "description": "Dark parchment textures for mystical backgrounds, featuring aged paper with void-like properties",
            "category": "backgrounds",
            "tags": ["void", "parchment", "dark", "background", "aged", "textured"],
            "render_strategy": {"engine": "pil", "generator_name": "parchment"},
            "param_schema": {
                "type": "object",
                "properties": {
                    "darkness": {
                        "type": "float",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.8,
                        "description": "Overall darkness of the background"
                    },
                    "texture_intensity": {
                        "type": "float",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.6,
                        "description": "Intensity of aged paper texture"
                    }
                }
            },
            "version": "1.0.0"
        }
    ]
    
    return examples