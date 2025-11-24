"""
Performance Tests for NanoBanana Generators

Comprehensive performance testing suite to verify optimization targets
and detect performance regressions.
"""

import unittest
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

from generators.factory import GeneratorFactory
from generators.base_generator import BaseGenerator
from generators.sigil_generator import SigilGenerator
from generators.enso_generator import EnsoGenerator
from generators.parchment_generator import ParchmentGenerator
from generators.giraffe_generator import GiraffeGenerator
from generators.kangaroo_generator import KangarooGenerator
from generators.fast_generators import FastGeneratorFactory
from utils.cache import get_cache


class PerformanceTargets:
    """Performance target definitions."""
    
    SIMPLE_TARGET = 0.100  # 100ms for simple assets
    MEDIUM_TARGET = 0.200  # 200ms for medium assets
    COMPLEX_TARGET = 0.500  # 500ms for complex assets
    LLM_TARGET = 1.000     # 1000ms for LLM-directed assets
    
    # Memory targets in MB
    SIMPLE_MEMORY = 50
    MEDIUM_MEMORY = 100
    COMPLEX_MEMORY = 200


class GeneratorPerformanceTest(unittest.TestCase):
    """Performance tests for individual generators."""
    
    def setUp(self):
        """Set up performance test environment."""
        self.factory = GeneratorFactory()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024
        
    def _measure_generation_performance(self, generator: BaseGenerator, iterations: int = 3) -> Dict[str, float]:
        """Measure generation performance metrics."""
        times = []
        memory_usage = []
        
        for _ in range(iterations):
            # Force garbage collection
            import gc
            gc.collect()
            
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Generate asset
            result = generator.generate()
            
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            times.append(end_time - start_time)
            memory_usage.append(end_memory - start_memory)
        
        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_memory': sum(memory_usage) / len(memory_usage),
            'times': times,
            'memory_usage': memory_usage
        }
    
    def test_sigil_performance(self):
        """Test sigil generator meets performance targets."""
        generator = SigilGenerator(width=512, height=512)
        metrics = self._measure_generation_performance(generator, iterations=5)
        
        self.assertLess(metrics['avg_time'], PerformanceTargets.SIMPLE_TARGET,
                       f"Sigil generation too slow: {metrics['avg_time']*1000:.1f}ms > {PerformanceTargets.SIMPLE_TARGET*1000}ms")
        
        # Memory should be reasonable
        self.assertLess(metrics['avg_memory'], PerformanceTargets.SIMPLE_MEMORY,
                       f"Too much memory used: {metrics['avg_memory']:.1f}MB > {PerformanceTargets.SIMPLE_MEMORY}MB")
    
    def test_enso_performance(self):
        """Test enso generator meets performance targets."""
        generator = EnsoGenerator(width=512, height=512)
        metrics = self._measure_generation_performance(generator, iterations=5)
        
        self.assertLess(metrics['avg_time'], PerformanceTargets.MEDIUM_TARGET,
                       f"Enso generation too slow: {metrics['avg_time']*1000:.1f}ms > {PerformanceTargets.MEDIUM_TARGET*1000}ms")
        
        self.assertLess(metrics['avg_memory'], PerformanceTargets.MEDIUM_MEMORY,
                       f"Too much memory used: {metrics['avg_memory']:.1f}MB > {PerformanceTargets.MEDIUM_MEMORY}MB")
    
    def test_parchment_performance(self):
        """Test parchment generator meets performance targets."""
        generator = ParchmentGenerator(width=512, height=512)
        metrics = self._measure_generation_performance(generator, iterations=5)
        
        self.assertLess(metrics['avg_time'], PerformanceTargets.MEDIUM_TARGET,
                       f"Parchment generation too slow: {metrics['avg_time']*1000:.1f}ms > {PerformanceTargets.MEDIUM_TARGET*1000}ms")
    
    def test_creature_performance(self):
        """Test creature generators meet performance targets."""
        for generator_class, name in [(GiraffeGenerator, "giraffe"), (KangarooGenerator, "kangaroo")]:
            with self.subTest(generator=name):
                generator = generator_class(width=512, height=512)
                metrics = self._measure_generation_performance(generator, iterations=3)
                
                self.assertLess(metrics['avg_time'], PerformanceTargets.COMPLEX_TARGET,
                               f"{name} generation too slow: {metrics['avg_time']*1000:.1f}ms > {PerformanceTargets.COMPLEX_TARGET*1000}ms")
    
    def test_different_sizes(self):
        """Test performance across different image sizes."""
        sizes = [(256, 256), (512, 512), (1024, 1024)]
        generator = SigilGenerator()
        
        for width, height in sizes:
            with self.subTest(size=f"{width}x{height}"):
                generator.width = width
                generator.height = height
                
                metrics = self._measure_generation_performance(generator, iterations=3)
                
                # Performance should degrade gracefully with size
                self.assertLess(metrics['avg_time'], PerformanceTargets.SIMPLE_TARGET * 4,
                               f"Performance degradation too severe at {width}x{height}")


class FastPathPerformanceTest(unittest.TestCase):
    """Performance tests for fast-path generators."""
    
    def test_fast_vs_standard_comparison(self):
        """Test that fast-path generators are significantly faster than standard ones."""
        factory = GeneratorFactory()
        fast_factory = FastGeneratorFactory()
        
        generator_types = ['sigil', 'enso', 'parchment']
        
        for gen_type in generator_types:
            if not fast_factory.is_fast_path_available(gen_type):
                continue
                
            with self.subTest(generator=gen_type):
                # Test standard generator
                standard_gen = factory.create_generator(gen_type, width=512, height=512)
                standard_metrics = self._measure_fast_performance(standard_gen, iterations=3)
                
                # Test fast generator
                fast_gen = fast_factory.create_generator(gen_type, width=512, height=512)
                fast_metrics = self._measure_fast_performance(fast_gen, iterations=3)
                
                # Fast should be at least 2x faster
                speedup = standard_metrics['avg_time'] / fast_metrics['avg_time']
                self.assertGreater(speedup, 2.0,
                                 f"Fast-path {gen_type} not fast enough: {speedup:.1f}x speedup")
                
                # Memory usage should be less
                self.assertLess(fast_metrics['avg_memory'], standard_metrics['avg_memory'],
                               f"Fast-path {gen_type} using more memory")
    
    def _measure_fast_performance(self, generator: BaseGenerator, iterations: int = 3) -> Dict[str, float]:
        """Measure generation performance (optimized for fast-path testing)."""
        times = []
        memory_usage = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            result = generator.generate()
            
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            times.append(end_time - start_time)
            memory_usage.append(max(0, end_memory - start_memory))
        
        return {
            'avg_time': sum(times) / len(times),
            'avg_memory': sum(memory_usage) / len(memory_usage),
            'times': times
        }


class CachePerformanceTest(unittest.TestCase):
    """Performance tests for caching system."""
    
    def test_cache_hit_performance(self):
        """Test that cache hits are significantly faster than misses."""
        cache = get_cache()
        
        # Clear cache for clean test
        cache.clear_all()
        
        # Create test generator
        factory = GeneratorFactory()
        generator = factory.create_generator('sigil')
        
        # First generation (cache miss)
        start_time = time.perf_counter()
        result1 = generator.generate()
        first_time = time.perf_counter() - start_time
        
        # Cache the result
        cache.set('test', result1, 'sigil')
        
        # Second generation (cache hit)
        start_time = time.perf_counter()
        result2 = cache.get('test', 'sigil')
        second_time = time.perf_counter() - start_time
        
        # Cache hit should be much faster
        self.assertLess(second_time, first_time / 10,
                       f"Cache hit not fast enough: {second_time*1000:.1f}ms vs {first_time*1000:.1f}ms")
    
    def test_cache_statistics(self):
        """Test cache statistics accuracy."""
        cache = get_cache()
        cache.clear_all()
        
        # Generate and cache some items
        factory = GeneratorFactory()
        generator = factory.create_generator('sigil')
        
        for i in range(5):
            result = generator.generate()
            cache.set(f'test_{i}', result, 'sigil')
        
        # Test getting some items
        for i in range(3):
            cache.get(f'test_{i}', 'sigil')
        
        # Check statistics
        stats = cache.get_stats()
        
        self.assertEqual(stats['total_hits'], 3)
        self.assertEqual(stats['total_set'], 5)
        self.assertGreater(stats['overall_hit_rate'], 0.5)


class ParallelPerformanceTest(unittest.TestCase):
    """Performance tests for parallel generation."""
    
    def test_parallel_generation(self):
        """Test that parallel generation improves throughput."""
        factory = GeneratorFactory()
        
        # Single-threaded generation
        start_time = time.perf_counter()
        for _ in range(5):
            generator = factory.create_generator('sigil')
            generator.generate()
        single_time = time.perf_counter() - start_time
        
        # Multi-threaded generation
        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for _ in range(5):
                generator = factory.create_generator('sigil')
                future = executor.submit(generator.generate)
                futures.append(future)
            
            # Wait for all to complete
            for future in as_completed(futures):
                result = future.result()
        
        parallel_time = time.perf_counter() - start_time
        
        # Parallel should be faster (though not necessarily 4x due to overhead)
        self.assertLess(parallel_time, single_time * 0.8,
                       f"Parallel generation not faster: {parallel_time:.3f}s vs {single_time:.3f}s")
    
    def test_thread_safety(self):
        """Test that parallel generation doesn't cause crashes."""
        factory = GeneratorFactory()
        
        errors = []
        
        def generate_with_error_handling():
            try:
                generator = factory.create_generator('sigil')
                result = generator.generate()
                return True
            except Exception as e:
                errors.append(e)
                return False
        
        # Generate many assets in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(generate_with_error_handling) for _ in range(20)]
            
            results = [future.result() for future in as_completed(futures)]
        
        # All should succeed
        self.assertEqual(len(errors), 0, f"Parallel generation errors: {errors}")
        self.assertEqual(sum(results), 20)


class MemoryLeakTest(unittest.TestCase):
    """Tests for memory leaks during generation."""
    
    def test_memory_stability(self):
        """Test that memory usage doesn't grow indefinitely."""
        factory = GeneratorFactory()
        
        # Get initial memory
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Generate many assets
        for i in range(50):
            generator = factory.create_generator('sigil')
            result = generator.generate()
            
            # Periodic cleanup
            if i % 10 == 0:
                import gc
                gc.collect()
        
        # Final memory
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (< 50MB)
        self.assertLess(memory_growth, 50,
                       f"Excessive memory growth: {memory_growth:.1f}MB")


class PerformanceRegressionTest(unittest.TestCase):
    """Tests to detect performance regressions."""
    
    def test_baseline_performance(self):
        """Test that current performance meets baseline expectations."""
        factory = GeneratorFactory()
        generator = factory.create_generator('sigil', width=512, height=512)
        
        # Measure performance
        start_time = time.perf_counter()
        for _ in range(10):
            result = generator.generate()
        total_time = time.perf_counter() - start_time
        avg_time = total_time / 10
        
        # Should be significantly better than targets
        self.assertLess(avg_time, PerformanceTargets.SIMPLE_TARGET * 0.5,
                       f"Performance regression detected: {avg_time*1000:.1f}ms > {PerformanceTargets.SIMPLE_TARGET*500}ms")
    
    def test_performance_consistency(self):
        """Test that performance is consistent across runs."""
        factory = GeneratorFactory()
        generator = factory.create_generator('enso', width=512, height=512)
        
        times = []
        for _ in range(10):
            start_time = time.perf_counter()
            result = generator.generate()
            times.append(time.perf_counter() - start_time)
        
        # Calculate coefficient of variation
        avg_time = sum(times) / len(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        cv = std_dev / avg_time if avg_time > 0 else 0
        
        # Should be relatively consistent (CV < 30%)
        self.assertLess(cv, 0.3,
                       f"Inconsistent performance: CV = {cv:.2f}")


def create_performance_suite():
    """Create and return the complete performance test suite."""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        GeneratorPerformanceTest,
        FastPathPerformanceTest,
        CachePerformanceTest,
        ParallelPerformanceTest,
        MemoryLeakTest,
        PerformanceRegressionTest
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


if __name__ == '__main__':
    # Run performance tests
    suite = create_performance_suite()
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Exception:')[-1].strip()}")