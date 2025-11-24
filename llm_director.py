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