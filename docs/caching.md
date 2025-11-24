# NanoBanana Asset Caching System

## Overview

The NanoBanana Generator implements a comprehensive in-memory caching system to optimize asset generation performance. This system reduces redundant computation by storing frequently accessed generated assets in memory with configurable expiration policies.

## Architecture

### Cache Hierarchy

```
GenerationalCache (Manager)
├── LRUCache (Parchment Assets)
│   ├── Cache Item 1
│   ├── Cache Item 2
│   └── ... (up to 50 items)
├── LRUCache (Enso Assets)
│   ├── Cache Item 1
│   └── ... (up to 100 items)
├── LRUCache (Sigil Assets)
│   └── ... (up to 100 items)
├── LRUCache (Giraffe Assets)
│   └── ... (up to 100 items)
├── LRUCache (Kangaroo Assets)
│   └── ... (up to 100 items)
└── LRUCache (Directed Enso Assets)
    └── ... (up to 200 items)
```

### Key Components

#### 1. LRUCache Class
- **Purpose**: Thread-safe Least Recently Used cache implementation
- **Features**:
  - TTL (Time To Live) support with automatic expiration
  - LRU eviction policy when capacity is reached
  - Comprehensive statistics tracking
  - Thread-safe operations using RLock

#### 2. GenerationalCache Class
- **Purpose**: Manages separate caches for different asset types
- **Features**:
  - Per-asset-type configuration (size, TTL)
  - Automatic cache creation on demand
  - Aggregated statistics across all caches
  - Bulk operations (clear all, configure all)

#### 3. Cache Decorator
- **Purpose**: Simplifies caching integration with functions
- **Usage**: `@cache_asset('asset_type')` decorator

## Cache Behavior

### Cache Keys

Cache keys are automatically generated using SHA-256 hashing of function arguments:

```python
# For simple assets (no parameters)
cache_key = hash(('parchment',))

# For directed enso (with parameters)
cache_key = hash(('directed_enso', prompt, model))
```

### Cache Workflow

```
Request → Check Cache → [HIT] → Return Cached Asset
         ↓
      [MISS] → Generate Asset → Store in Cache → Return Asset
```

### Cache Invalidation

The cache uses three invalidation strategies:

1. **TTL Expiration**: Automatic removal after time-to-live expires
2. **LRU Eviction**: Least recently used items evicted when capacity reached
3. **Manual Clear**: Manual invalidation via `/cache/clear` endpoint

## Configuration

### Environment Variables

Add these to your `.env` file to customize cache behavior:

```bash
# Maximum number of items to store in cache (default: 100)
CACHE_SIZE=100

# Time To Live for cached parchment assets (seconds, default: 3600)
CACHE_TTL_PARCHMENT=3600

# Time To Live for cached enso assets (seconds, default: 3600)
CACHE_TTL_ENSO=3600

# Time To Live for cached sigil assets (seconds, default: 3600)
CACHE_TTL_SIGIL=3600

# Time To Live for cached creature assets (seconds, default: 3600)
CACHE_TTL_CREATURE=3600

# Enable cache metrics collection (default: true)
CACHE_METRICS=true
```

### Default Cache Configuration

| Asset Type | Cache Size | TTL (seconds) | Rationale |
|------------|-----------|---------------|-----------|
| Parchment | 50 | 3600 | Large memory footprint, fewer variations |
| Enso | 100 | 3600 | Moderate variations, high reuse |
| Sigil | 100 | 3600 | High randomness, moderate reuse |
| Giraffe | 100 | 3600 | High randomness, moderate reuse |
| Kangaroo | 100 | 3600 | High randomness, moderate reuse |
| Directed Enso | 200 | 1800 | Many unique prompts, shorter TTL |

## API Endpoints

### Cache Statistics

**Endpoint**: `GET /cache/stats`

**Response**:
```json
{
  "status": "success",
  "timestamp": "2025-11-24T19:41:05.865Z",
  "cache_stats": {
    "total_hits": 150,
    "total_misses": 50,
    "total_evictions": 10,
    "total_expired": 5,
    "total_set": 60,
    "total_size": 45,
    "overall_hit_rate": 0.75,
    "caches": {
      "parchment": {
        "hits": 30,
        "misses": 5,
        "evictions": 2,
        "expired": 1,
        "total_set": 8,
        "size": 5,
        "max_size": 50,
        "default_ttl": 3600,
        "hit_rate": 0.857
      }
    }
  }
}
```

### Clear Cache

**Endpoint**: `GET /cache/clear`

**Response**:
```json
{
  "status": "success",
  "message": "Cache cleared",
  "timestamp": "2025-11-24T19:41:05.865Z"
}
```

## Performance Impact

### Expected Performance Improvements

| Metric | Without Cache | With Cache | Improvement |
|--------|--------------|------------|-------------|
| Cache Hit Response Time | N/A | <50ms | N/A |
| Cache Miss Response Time | 100-500ms | 100-500ms | No change |
| Hit Rate (repeated requests) | 0% | >70% | +70% |
| Memory Usage | ~10MB | <500MB | +490MB |

### Memory Usage

Memory usage scales with:
- Number of cached assets
- Image dimensions (1024x1024 for parchment, 800x800 for enso, etc.)
- Image format (RGBA vs RGB)

**Approximate memory per asset**:
- Parchment (1024x1024 RGB): ~3MB
- Enso (800x800 RGBA): ~2.5MB
- Sigil (500x500 RGBA): ~1MB
- Creatures (600x800 RGBA): ~1.9MB

**Maximum memory usage** (all caches full):
- Parchment: 50 × 3MB = 150MB
- Enso: 100 × 2.5MB = 250MB
- Sigil: 100 × 1MB = 100MB
- Giraffe: 100 × 1.9MB = 190MB
- Kangaroo: 100 × 1.9MB = 190MB
- Directed Enso: 200 × 2.5MB = 500MB
- **Total**: ~1.38GB (worst case)

**Note**: Actual memory usage is typically much lower due to:
- Cache rarely reaching maximum capacity
- LRU eviction keeping only active items
- TTL expiration removing old entries

## Monitoring and Metrics

### Key Metrics to Monitor

1. **Hit Rate**: Percentage of requests served from cache
   - Target: >70% for optimal performance
   - Action if low: Increase cache size or TTL

2. **Eviction Rate**: Frequency of cache evictions
   - High rate indicates cache too small
   - Action: Increase cache size

3. **Expiration Rate**: Frequency of TTL expirations
   - High rate with low hit rate suggests TTL too short
   - Action: Increase TTL

4. **Memory Usage**: Total memory consumed by cache
   - Monitor to prevent memory exhaustion
   - Action if high: Reduce cache size or TTL

### Logging

Cache operations are logged with emojis for easy monitoring:

```
📦 Serving parchment from cache
✨ Generated new enso and cached it
❌ Cache Stats Error: ...
```

## Best Practices

### 1. Cache Sizing

- **Small caches** (<50 items): Suitable for assets with low variation
- **Medium caches** (50-200 items): Good for moderate variation
- **Large caches** (>200 items): Required for high variation (e.g., directed enso)

### 2. TTL Configuration

- **Short TTL** (1800s): For frequently changing or user-specific content
- **Medium TTL** (3600s): For standard assets with moderate reuse
- **Long TTL** (7200s+): For very stable, frequently accessed assets

### 3. Cache Warming

Pre-populate cache on startup for critical assets:

```python
# In backend.py startup
cache.set('parchment', create_void_parchment(index=None))
cache.set('enso', create_ink_enso(index=None))
```

### 4. Monitoring

- Monitor hit rates regularly
- Set up alerts for hit rates <50%
- Track memory usage trends
- Review eviction patterns

## Troubleshooting

### Low Hit Rate

**Symptoms**: Hit rate <50%

**Possible Causes**:
1. Cache size too small
2. TTL too short
3. High asset variation
4. Insufficient request volume

**Solutions**:
- Increase cache size
- Increase TTL
- Analyze request patterns
- Consider cache warming

### High Memory Usage

**Symptoms**: Memory usage approaching system limits

**Possible Causes**:
1. Cache sizes too large
2. Memory leaks
3. Too many cached asset types

**Solutions**:
- Reduce cache sizes
- Decrease TTL
- Implement memory limits
- Monitor for leaks

### Cache Not Working

**Symptoms**: No cache hits, all requests generating assets

**Possible Causes**:
1. Cache not initialized
2. Cache disabled
3. Key generation issues

**Solutions**:
- Check cache initialization in logs
- Verify cache configuration
- Test cache manually via `/cache/stats`

## Future Enhancements

### Potential Improvements

1. **Disk-backed Cache**: Persist cache to disk for restart resilience
2. **Redis Integration**: Distributed caching for multi-instance deployments
3. **Cache Tiering**: L1 (memory) + L2 (disk) hierarchy
4. **Adaptive TTL**: Dynamic TTL based on access patterns
5. **Cache Analytics**: Detailed usage analytics and recommendations
6. **Selective Caching**: Cache only high-value assets
7. **Compression**: Reduce memory footprint with image compression

## Integration Example

### Using the Cache Decorator

```python
from utils.cache import cache_asset

@cache_asset('parchment')
def generate_parchment():
    return create_void_parchment(index=None)

# First call - generates and caches
img1 = generate_parchment()

# Second call - returns cached version
img2 = generate_parchment()  # Same as img1
```

### Manual Cache Usage

```python
from utils.cache import get_cache

cache = get_cache()

# Check cache
cached = cache.get('enso')
if cached:
    return cached

# Generate and cache
img = create_ink_enso(index=None)
cache.set('enso', img)
return img
```

## References

- [`utils/cache.py`](../utils/cache.py): Cache implementation
- [`backend.py`](../backend.py): Cache integration
- [`.env.example`](../.env.example): Configuration options
- [Asset Structure](asset_structure.md): Asset generation details