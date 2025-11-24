#!/usr/bin/env python3
"""
Performance Profiling Script for NanoBanana Generators

Profiles generation time, CPU usage, memory allocations, and identifies
performance bottlenecks across all generator types.
"""

import os
import sys
import time
import psutil
import cProfile
import pstats
import tracemalloc
import gc
from typing import Dict, List, Any, Callable
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the generators module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from generators.factory import GeneratorFactory
from generators.base_generator import BaseGenerator
from generators.sigil_generator import SigilGenerator
from generators.enso_generator import EnsoGenerator
from generators.parchment_generator import ParchmentGenerator
from generators.giraffe_generator import GiraffeGenerator
from generators.kangaroo_generator import KangarooGenerator


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single generation run."""
    generator_type: str
    width: int
    height: int
    generation_time: float
    peak_memory_mb: float
    cpu_percent: float
    iterations: int
    avg_time: float
    min_time: float
    max_time: float
    memory_per_gen_mb: float


class PerformanceProfiler:
    """Performance profiler for generator operations."""
    
    def __init__(self):
        self.results: List[PerformanceMetrics] = []
        self.memory_snapshots: Dict[str, int] = {}
        self.detailed_stats = {}
    
    @contextmanager
    def measure_performance(self, generator_type: str, width: int = 500, height: int = 500):
        """Context manager to measure performance metrics."""
        
        # Start memory tracking
        tracemalloc.start()
        gc.collect()  # Clean up before measurement
        
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Start CPU monitoring
        cpu_samples = []
        
        def sample_cpu():
            return psutil.cpu_percent(interval=0.1)
        
        # Run generation with profiling
        start_time = time.perf_counter()
        
        yield self
        
        end_time = time.perf_counter()
        
        # Get memory snapshot
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Final CPU sample
        final_cpu = psutil.cpu_percent(interval=None)
        peak_memory = initial_memory + (peak / 1024 / 1024)
        
        # Calculate metrics
        generation_time = end_time - start_time
        
        return PerformanceMetrics(
            generator_type=generator_type,
            width=width,
            height=height,
            generation_time=generation_time,
            peak_memory_mb=peak_memory,
            cpu_percent=final_cpu,
            iterations=1,
            avg_time=generation_time,
            min_time=generation_time,
            max_time=generation_time,
            memory_per_gen_mb=peak_memory
        )
    
    def profile_generator(self, generator_class: type, test_configs: List[Dict[str, Any]], 
                         iterations: int = 5) -> Dict[str, PerformanceMetrics]:
        """Profile a generator with multiple configurations."""
        
        results = {}
        
        for config in test_configs:
            config_key = f"{config.get('width', 500)}x{config.get('height', 500)}"
            
            try:
                generator = generator_class(**config)
                
                times = []
                memory_usages = []
                
                for i in range(iterations):
                    # Memory tracking
                    gc.collect()
                    tracemalloc.start()
                    
                    # CPU tracking
                    cpu_start = psutil.cpu_percent(interval=None)
                    
                    # Generate
                    start_time = time.perf_counter()
                    result = generator.generate()
                    end_time = time.perf_counter()
                    
                    # Get memory usage
                    current, peak = tracemalloc.get_traced_memory()
                    memory_usage = peak / 1024 / 1024
                    tracemalloc.stop()
                    
                    times.append(end_time - start_time)
                    memory_usages.append(memory_usage)
                
                # Calculate metrics
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                avg_memory = sum(memory_usages) / len(memory_usages)
                
                metrics = PerformanceMetrics(
                    generator_type=generator.get_generator_type(),
                    width=config.get('width', 500),
                    height=config.get('height', 500),
                    generation_time=avg_time,
                    peak_memory_mb=avg_memory,
                    cpu_percent=psutil.cpu_percent(interval=None),
                    iterations=iterations,
                    avg_time=avg_time,
                    min_time=min_time,
                    max_time=max_time,
                    memory_per_gen_mb=avg_memory
                )
                
                results[config_key] = metrics
                
            except Exception as e:
                print(f"Error profiling {generator_class.__name__} with config {config}: {e}")
                continue
        
        return results
    
    def profile_with_cprofile(self, generator_func: Callable, iterations: int = 1):
        """Profile a generator function with cProfile."""
        
        profiler = cProfile.Profile()
        
        for _ in range(iterations):
            profiler.enable()
            result = generator_func()
            profiler.disable()
        
        return profiler
    
    def generate_performance_report(self, output_file: str = "performance_report.txt"):
        """Generate a comprehensive performance report."""
        
        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("NANOBANANA GENERATORS - PERFORMANCE PROFILING REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {psutil.cpu_count()} cores, {psutil.virtual_memory().total / 1024**3:.1f}GB RAM\n\n")
            
            if not self.results:
                f.write("No performance data available.\n")
                return
            
            # Summary statistics
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-" * 40 + "\n")
            
            total_tests = len(self.results)
            avg_generation_time = sum(r.avg_time for r in self.results) / total_tests
            avg_memory = sum(r.memory_per_gen_mb for r in self.results) / total_tests
            
            f.write(f"Total tests: {total_tests}\n")
            f.write(f"Average generation time: {avg_generation_time*1000:.2f}ms\n")
            f.write(f"Average memory usage: {avg_memory:.2f}MB\n")
            f.write(f"Target < 200ms: {'PASS' if avg_generation_time < 0.2 else 'FAIL'}\n\n")
            
            # Detailed results
            f.write("DETAILED RESULTS\n")
            f.write("-" * 40 + "\n")
            
            for result in sorted(self.results, key=lambda x: x.avg_time):
                f.write(f"Generator: {result.generator_type}\n")
                f.write(f"  Size: {result.width}x{result.height}\n")
                f.write(f"  Time: {result.avg_time*1000:.2f}ms avg ({result.min_time*1000:.2f}ms - {result.max_time*1000:.2f}ms)\n")
                f.write(f"  Memory: {result.memory_per_gen_mb:.2f}MB\n")
                f.write(f"  CPU: {result.cpu_percent:.1f}%\n")
                
                # Performance assessment
                target_time = 0.5 if result.generator_type in ['giraffe', 'kangaroo'] else 0.2
                status = "PASS" if result.avg_time < target_time else "FAIL"
                f.write(f"  Target < {target_time*1000}ms: {status}\n\n")
            
            # Bottleneck analysis
            f.write("BOTTLENECK ANALYSIS\n")
            f.write("-" * 40 + "\n")
            
            slow_generators = [r for r in self.results if r.avg_time > 0.5]
            memory_intensive = [r for r in self.results if r.memory_per_gen_mb > 100]
            
            if slow_generators:
                f.write("Slow generators (>500ms):\n")
                for gen in slow_generators:
                    f.write(f"  {gen.generator_type}: {gen.avg_time*1000:.1f}ms\n")
                f.write("\n")
            
            if memory_intensive:
                f.write("Memory intensive (>100MB):\n")
                for gen in memory_intensive:
                    f.write(f"  {gen.generator_type}: {gen.memory_per_gen_mb:.1f}MB\n")
                f.write("\n")
            
            # Recommendations
            f.write("OPTIMIZATION RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            
            if avg_generation_time > 0.2:
                f.write("1. Generation time >200ms target\n")
                f.write("   - Implement vectorized numpy operations\n")
                f.write("   - Add caching for expensive computations\n")
                f.write("   - Use lazy evaluation for non-critical operations\n")
            
            if avg_memory > 50:
                f.write("2. High memory usage detected\n")
                f.write("   - Implement image buffer pooling\n")
                f.write("   - Optimize noise generation algorithms\n")
                f.write("   - Reduce unnecessary image copies\n")
            
            if any(r.avg_time > 1.0 for r in self.results):
                f.write("3. Some operations taking >1s\n")
                f.write("   - Profile individual method calls\n")
                f.write("   - Consider algorithmic optimizations\n")
                f.write("   - Add progress indicators for long operations\n")
            
            f.write("\nRecommendations based on bottlenecks detected.\n")


def main():
    """Main profiling function."""
    
    print("Starting performance profiling...")
    profiler = PerformanceProfiler()
    
    # Define test configurations
    test_configs = [
        {"width": 256, "height": 256},
        {"width": 512, "height": 512},
        {"width": 1024, "height": 1024},
    ]
    
    generators_to_test = [
        (SigilGenerator, "SigilGenerator"),
        (EnsoGenerator, "EnsoGenerator"),
        (ParchmentGenerator, "ParchmentGenerator"),
        (GiraffeGenerator, "GiraffeGenerator"),
        (KangarooGenerator, "KangarooGenerator"),
    ]
    
    factory = GeneratorFactory()
    all_results = []
    
    for generator_class, name in generators_to_test:
        print(f"\nProfiling {name}...")
        
        try:
            results = profiler.profile_generator(generator_class, test_configs, iterations=3)
            all_results.extend(results.values())
            
            for config_key, metrics in results.items():
                print(f"  {config_key}: {metrics.avg_time*1000:.1f}ms, {metrics.memory_per_gen_mb:.1f}MB")
                
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    # Generate report
    profiler.results = all_results
    profiler.generate_performance_report()
    
    print(f"\nPerformance report generated: performance_report.txt")
    print(f"Total tests completed: {len(all_results)}")


if __name__ == "__main__":
    main()