# Performance Optimization Documentation

## Overview

This document describes the performance optimizations implemented in the NanoBanana asset generation system. The optimizations focus on reducing generation time, memory usage, and improving overall system efficiency while maintaining image quality.

## Performance Targets

The system targets the following performance benchmarks:

| Asset Type | Target Time | Complexity Level |
|------------|-------------|------------------|
| Simple (sigils) | <100ms | Basic geometric shapes |
| Medium (enso, parchment) | <200ms | Moderate complexity |
| Complex (creatures) | <500ms | High detail illustrations |
| LLM-directed | <1000ms | Including LLM latency |

## Optimization Techniques Implemented

### 1. Algorithm Optimizations

#### Noise Generation
- **Vectorized Operations**: Replaced Python loops with NumPy vectorized operations
- **Precomputation Cache**: Cache frequently used noise patterns
- **Memory-efficient Data Types**: Use `float32` instead of `float64` for intermediate calculations
- **Batch Processing**: Generate multiple noise patterns in a single operation

```python
# Before: Slow Python loop
noise = np.zeros((height, width))
for i in range(height):
    for j in range(width):
        noise[i, j] = np.random.normal(128, 50)

# After: Fast vectorized operation
noise = np.random.normal(128, 50, (height, width)).astype(np.float32)
```

#### PIL Operations
- **Batch Similar Operations**: Apply filters and enhancements together
- **Pre-allocated Buffers**: Reuse image buffers from a pool
- **Mode Conversion Optimization**: Minimize unnecessary image mode conversions
- **Lazy Evaluation**: Defer expensive operations until needed

### 2. Memory Optimizations

#### Image Buffer Pooling
- **Pre-allocated Buffers**: Maintain a pool of reusable image buffers
- **Memory Tracking**: Monitor memory usage per generation
- **Efficient Cleanup**: Clear caches and reset state properly

#### Cache Management
- **LRU Cache**: Least Recently Used eviction policy
- **TTL Support**: Time-to-live for cached items
- **Memory Estimation**: Track approximate memory usage per cached item

### 3. Performance Monitoring

#### Metrics Collection
- **Generation Time**: Track time per operation and overall generation
- **Memory Usage**: Monitor peak and average memory consumption
- **Cache Effectiveness**: Measure hit/miss ratios and cache performance
- **Operation Breakdown**: Track time spent in different generation phases

#### Performance Configuration
The system supports configurable performance settings via environment variables:

```bash
# Performance level: balanced, fast, quality
PERFORMANCE_LEVEL=balanced

# Enable precomputation of expensive patterns
ENABLE_PRECOMPUTATION=true

# Cache size for noise patterns
NOISE_CACHE_SIZE=50

# Pre-allocated image buffer pool size
IMAGE_POOL_SIZE=10

# Enable parallel generation
PARALLEL_GENERATION=true

# Maximum parallel workers
MAX_WORKERS=4

# Fast-path mode for simple assets
ENABLE_FAST_PATH=false

# Memory usage threshold
MEMORY_THRESHOLD=100

# Performance monitoring
PERFORMANCE_MONITORING=true
```

### 4. Fast-Path Generators

#### Optimized Simple Assets
For scenarios where speed is critical, fast-path generators provide simplified versions:

- **FastSigilGenerator**: Simplified geometric patterns
- **FastEnsoGenerator**: Basic circle drawing with minimal complexity
- **FastParchmentGenerator**: Pre-generated noise patterns with simplified processing

#### Performance Comparison
Fast-path generators typically achieve:
- 3-5x speed improvement over standard generators
- 50-70% memory reduction
- Slight quality reduction but acceptable for most use cases

## Performance Testing

### Benchmark Suite

The performance testing suite (`tests/performance_tests.py`) includes:

1. **Generation Benchmarks**: Test each generator type with various parameters
2. **Memory Profiling**: Track memory usage patterns
3. **Cache Effectiveness**: Measure cache hit rates and performance
4. **Parallel Processing**: Test multi-threaded generation efficiency
5. **Regression Testing**: Ensure optimizations don't break functionality

### Profiling Tools

The `scripts/profile_generators.py` script provides:

- **CPU Profiling**: Detailed function-level performance analysis
- **Memory Tracking**: Peak and average memory usage measurement
- **Statistical Analysis**: Mean, min, max generation times
- **Bottleneck Identification**: Automatic detection of slow operations

## Configuration Guide

### Performance Levels

#### Balanced (Default)
- Good quality with reasonable speed
- Precomputation enabled
- Moderate cache sizes
- Performance monitoring active

#### Fast
- Prioritize speed over quality
- Maximum precomputation
- Large cache sizes
- Simplified algorithms where possible
- Fast-path generators preferred

#### Quality
- Prioritize quality over speed
- Minimal precomputation
- Smaller cache sizes
- Full detail algorithms
- Enhanced post-processing

### Tuning Guidelines

#### For High-Throughput Applications
```bash
PERFORMANCE_LEVEL=fast
ENABLE_FAST_PATH=true
NOISE_CACHE_SIZE=100
IMAGE_POOL_SIZE=20
PARALLEL_GENERATION=true
MAX_WORKERS=8
```

#### for Quality-Critical Applications
```bash
PERFORMANCE_LEVEL=quality
ENABLE_PRECOMPUTATION=false
NOISE_CACHE_SIZE=20
IMAGE_POOL_SIZE=5
PARALLEL_GENERATION=false
```

#### for Resource-Constrained Environments
```bash
PERFORMANCE_LEVEL=balanced
MEMORY_THRESHOLD=50
NOISE_CACHE_SIZE=25
IMAGE_POOL_SIZE=3
```

## Monitoring and Debugging

### Performance Metrics API

Generators expose performance metrics via:

```python
# Get performance metrics
metrics = generator.get_performance_metrics()
print(f"Average generation time: {metrics['avg_generation_time']:.3f}s")
print(f"Cache hit rate: {metrics.get('cache_hit_rate', 'N/A')}")
```

### Cache Performance

Monitor cache performance through the cache statistics:

```python
from utils.cache import get_cache

cache = get_cache()
stats = cache.get_stats()
print(f"Overall hit rate: {stats['overall_hit_rate']:.2%}")
```

### Performance Report Generation

Generate comprehensive performance reports:

```bash
python scripts/profile_generators.py
# Creates performance_report.txt with detailed analysis
```

## Troubleshooting

### Common Performance Issues

#### Slow Generation Times
1. Check performance level setting
2. Enable precomputation if not active
3. Increase cache sizes
4. Consider using fast-path generators
5. Profile specific slow operations

#### High Memory Usage
1. Reduce cache sizes
2. Enable performance monitoring
3. Check for memory leaks in custom generators
4. Use smaller image sizes where possible
5. Clear caches periodically

#### Poor Cache Hit Rates
1. Increase cache TTL values
2. Adjust cache sizes based on usage patterns
3. Review key generation logic
4. Consider different caching strategies

### Performance Regression Detection

Run performance tests regularly to detect regressions:

```bash
python -m pytest tests/performance_tests.py -v
```

Compare against baseline performance metrics and investigate significant deviations.

## Future Optimizations

### Planned Improvements

1. **GPU Acceleration**: CUDA/OpenCL support for noise generation
2. **Advanced Caching**: Multi-level caching strategies
3. **Streaming Processing**: Process large images in chunks
4. **Distributed Generation**: Multi-node generation capabilities
5. **ML-Based Optimization**: Use machine learning to predict optimal parameters

### Performance Targets

Future versions aim to achieve:
- Simple assets: <50ms
- Medium assets: <100ms  
- Complex assets: <250ms
- 10x memory efficiency improvement
- Sub-millisecond cache operations

## Conclusion

The performance optimization implementation provides a solid foundation for efficient asset generation while maintaining the artistic quality and flexibility of the NanoBanana system. The configurable performance settings and comprehensive monitoring capabilities allow for optimization across different use cases and deployment scenarios.