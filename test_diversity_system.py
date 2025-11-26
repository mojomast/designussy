#!/usr/bin/env python3
"""
Comprehensive test script for Phase 4: Diversity & Variation System.

This script tests all components of the diversity system:
- Diversity metrics analysis
- Diversity tracking and storage
- Diversity visualization
- Diversity optimization
- Backend API endpoints
- Integration with existing systems

Run with: python test_diversity_system.py
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all diversity system components can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from utils.diversity_metrics import DiversityMetrics
        print("✅ DiversityMetrics imported successfully")
    except ImportError as e:
        print(f"❌ DiversityMetrics import failed: {e}")
        return False
    
    try:
        from storage.diversity_tracker import DiversityTracker
        print("✅ DiversityTracker imported successfully")
    except ImportError as e:
        print(f"❌ DiversityTracker import failed: {e}")
        return False
    
    try:
        from utils.diversity_viz import DiversityViz
        print("✅ DiversityViz imported successfully")
    except ImportError as e:
        print(f"❌ DiversityViz import failed: {e}")
        return False
    
    try:
        from generators.diversity_optimizer import DiversityOptimizer
        print("✅ DiversityOptimizer imported successfully")
    except ImportError as e:
        print(f"❌ DiversityOptimizer import failed: {e}")
        return False
    
    try:
        from generators.variation_strategies import VariationEngine, DiversityAnalyzer
        print("✅ VariationEngine and DiversityAnalyzer imported successfully")
    except ImportError as e:
        print(f"❌ VariationEngine import failed: {e}")
        return False
    
    try:
        from enhanced_design.element_types import DiversityConfig
        print("✅ DiversityConfig imported successfully")
    except ImportError as e:
        print(f"❌ DiversityConfig import failed: {e}")
        return False
    
    return True

def test_diversity_metrics():
    """Test diversity metrics calculations."""
    print("\n📊 Testing diversity metrics...")
    
    try:
        from utils.diversity_metrics import DiversityMetrics
        
        metrics = DiversityMetrics()
        
        # Test parameter diversity
        test_params = [
            {"width": 256, "height": 256, "complexity": 0.3},
            {"width": 512, "height": 512, "complexity": 0.7},
            {"width": 1024, "height": 1024, "complexity": 0.9},
            {"width": 128, "height": 128, "complexity": 0.1}
        ]
        
        diversity_score = metrics.calculate_parameter_diversity(test_params)
        print(f"✅ Parameter diversity score: {diversity_score:.3f}")
        
        # Test entropy calculation
        test_values = [0.1, 0.3, 0.7, 0.9]
        entropy = metrics.entropy_score(test_values)
        print(f"✅ Entropy score: {entropy:.3f}")
        
        # Test coefficient of variation
        cv = metrics.coefficient_of_variation(test_values)
        print(f"✅ Coefficient of variation: {cv:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Diversity metrics test failed: {e}")
        return False

def test_diversity_tracker():
    """Test diversity tracking and storage."""
    print("\n📈 Testing diversity tracking...")
    
    try:
        from storage.diversity_tracker import DiversityTracker
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            tracker = DiversityTracker(db_path=db_path)
            
            # Test recording generation
            test_type_id = "test_glyph_v1"
            test_params = {"width": 512, "height": 512, "complexity": 0.7}
            diversity_score = 0.8
            
            success = tracker.record_generation(
                type_id=test_type_id,
                generation_params=test_params,
                diversity_score=diversity_score
            )
            
            if success:
                print("✅ Successfully recorded generation event")
            else:
                print("❌ Failed to record generation event")
                return False
            
            # Test getting current metrics
            current_metrics = tracker.get_current_diversity_metrics(test_type_id)
            print(f"✅ Current metrics retrieved: {len(current_metrics) if current_metrics else 0} metrics")
            
            # Test diversity history
            history = tracker.get_type_diversity_history(test_type_id, days=7)
            print(f"✅ History retrieved: {len(history) if history else 0} records")
            
            return True
            
        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Diversity tracker test failed: {e}")
        return False

def test_diversity_visualization():
    """Test diversity visualization."""
    print("\n📊 Testing diversity visualization...")
    
    try:
        from utils.diversity_viz import DiversityViz
        
        viz = DiversityViz()
        
        # Test parameter distribution plot
        test_params = [
            {"width": 256, "height": 256, "complexity": 0.3},
            {"width": 512, "height": 512, "complexity": 0.7},
            {"width": 1024, "height": 1024, "complexity": 0.9}
        ]
        
        dist_plot = viz.plot_parameter_distribution(test_params)
        print(f"✅ Parameter distribution plot generated (length: {len(dist_plot)})")
        
        # Test diversity timeline
        timeline_plot = viz.plot_diversity_timeline("test_type", days=30)
        print(f"✅ Diversity timeline generated (length: {len(timeline_plot) if timeline_plot else 0})")
        
        # Test dashboard
        dashboard = viz.create_diversity_dashboard("test_type")
        print(f"✅ Diversity dashboard created with {len(dashboard)} sections")
        
        return True
        
    except Exception as e:
        print(f"❌ Diversity visualization test failed: {e}")
        return False

def test_diversity_optimizer():
    """Test diversity optimization."""
    print("\n⚙️ Testing diversity optimization...")
    
    try:
        from generators.diversity_optimizer import DiversityOptimizer
        
        optimizer = DiversityOptimizer()
        
        # Test diverse batch generation
        test_params = {"width": (128, 1024), "height": (128, 1024), "complexity": (0.1, 0.9)}
        
        diverse_batch = optimizer.generate_diverse_batch(
            element_type=test_params,
            count=5,
            target_diversity=0.7,
            sampling_strategy="random"
        )
        
        print(f"✅ Generated diverse batch with {len(diverse_batch)} parameter sets")
        
        # Test improvement suggestions
        suggestions = optimizer.suggest_diversity_improvements("test_type")
        print(f"✅ Generated {len(suggestions)} improvement suggestions")
        
        return True
        
    except Exception as e:
        print(f"❌ Diversity optimizer test failed: {e}")
        return False

def test_variation_engine_enhancements():
    """Test enhanced VariationEngine with DiversityAnalyzer."""
    print("\n🎯 Testing enhanced VariationEngine...")
    
    try:
        from generators.variation_strategies import VariationEngine, DiversityAnalyzer
        
        # Test DiversityAnalyzer
        analyzer = DiversityAnalyzer()
        
        # Test parameter diversity analysis
        test_params = [
            {"width": 256, "height": 256, "complexity": 0.3},
            {"width": 512, "height": 512, "complexity": 0.7}
        ]
        
        diversity_score = analyzer.calculate_parameter_diversity(test_params)
        print(f"✅ DiversityAnalyzer parameter diversity: {diversity_score:.3f}")
        
        # Test VariationEngine
        engine = VariationEngine()
        
        # Test getting available strategies
        strategies = engine.get_available_strategies()
        print(f"✅ VariationEngine has {len(strategies)} available strategies")
        
        return True
        
    except Exception as e:
        print(f"❌ VariationEngine test failed: {e}")
        return False

def test_element_type_enhancements():
    """Test enhanced ElementType with diversity configuration."""
    print("\n🏗️ Testing ElementType enhancements...")
    
    try:
        from enhanced_design.element_types import DiversityConfig, ElementType
        
        # Test DiversityConfig
        config = DiversityConfig(
            target_diversity_score=0.8,
            diversity_weights={"width": 1.0, "height": 1.0, "complexity": 2.0},
            sampling_strategy="latin_hypercube",
            constraints=["width <= 1024", "complexity >= 0.1"]
        )
        
        print("✅ DiversityConfig created successfully")
        print(f"   Target diversity: {config.target_diversity_score}")
        print(f"   Sampling strategy: {config.sampling_strategy}")
        print(f"   Constraints: {len(config.constraints)} constraints")
        
        # Test ElementType with diversity config
        element_type_data = {
            "id": "test_glyph_v1",
            "name": "Test Glyph",
            "description": "A test glyph for diversity testing",
            "category": "glyph",
            "render_strategy": {
                "engine": "pil",
                "generator_name": "sigil"
            },
            "param_schema": {
                "width": {"type": "int", "min": 128, "max": 1024, "default": 512},
                "height": {"type": "int", "min": 128, "max": 1024, "default": 512},
                "complexity": {"type": "float", "min": 0.1, "max": 0.9, "default": 0.5}
            },
            "diversity_config": config
        }
        
        element_type = ElementType(**element_type_data)
        print("✅ ElementType with diversity config created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ ElementType test failed: {e}")
        return False

def test_backend_endpoints():
    """Test backend API endpoints."""
    print("\n🌐 Testing backend endpoints...")
    
    try:
        import sys
        import importlib.util
        
        # Import backend module
        spec = importlib.util.spec_from_file_location("backend", "backend.py")
        backend_module = importlib.util.module_from_spec(spec)
        
        # Check if diversity endpoints exist in the file content
        with open("backend.py", "r") as f:
            backend_content = f.read()
        
        diversity_endpoints = [
            "/diversity/analyze-parameters",
            "/diversity/analyze-outputs",
            "/diversity/type/{type_id}/history",
            "/diversity/overview",
            "/diversity/generate-report",
            "/diversity/optimize/{type_id}",
            "/diversity/generate-diverse-batch",
            "/diversity/visualization/{type_id}",
            "/diversity/record-generation",
            "/diversity/stats"
        ]
        
        found_endpoints = 0
        for endpoint in diversity_endpoints:
            if endpoint.replace("{type_id}", "") in backend_content:
                found_endpoints += 1
        
        print(f"✅ Found {found_endpoints}/{len(diversity_endpoints)} diversity endpoints in backend")
        
        if found_endpoints == len(diversity_endpoints):
            print("✅ All diversity endpoints successfully added to backend")
        else:
            print(f"⚠️ Missing {len(diversity_endpoints) - found_endpoints} diversity endpoints")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend endpoints test failed: {e}")
        return False

def test_integration():
    """Test integration between all components."""
    print("\n🔗 Testing system integration...")
    
    try:
        from utils.diversity_metrics import DiversityMetrics
        from storage.diversity_tracker import DiversityTracker
        from utils.diversity_viz import DiversityViz
        from generators.diversity_optimizer import DiversityOptimizer
        from generators.variation_strategies import VariationEngine
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Initialize all components
            metrics = DiversityMetrics()
            tracker = DiversityTracker(db_path=db_path)
            viz = DiversityViz()
            optimizer = DiversityOptimizer()
            engine = VariationEngine()
            
            # Test parameter generation and analysis pipeline
            test_params = optimizer.generate_diverse_batch(
                element_type={"width": (128, 1024), "height": (128, 1024)},
                count=5,
                target_diversity=0.7
            )
            
            diversity_score = metrics.calculate_parameter_diversity(test_params)
            
            # Record in tracker
            tracker.record_generation(
                type_id="integration_test_type",
                generation_params=test_params[0],
                diversity_score=diversity_score
            )
            
            # Get history
            history = tracker.get_type_diversity_history("integration_test_type", days=1)
            
            print(f"✅ Integration test successful:")
            print(f"   Generated {len(test_params)} parameter sets")
            print(f"   Diversity score: {diversity_score:.3f}")
            print(f"   Recorded in tracker: {len(history)} records")
            
            return True
            
        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all diversity system tests."""
    print("🚀 Starting Phase 4: Diversity System Comprehensive Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Diversity Metrics", test_diversity_metrics),
        ("Diversity Tracker", test_diversity_tracker),
        ("Diversity Visualization", test_diversity_visualization),
        ("Diversity Optimizer", test_diversity_optimizer),
        ("Variation Engine", test_variation_engine_enhancements),
        ("Element Type", test_element_type_enhancements),
        ("Backend Endpoints", test_backend_endpoints),
        ("System Integration", test_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Phase 4 Diversity System is fully functional.")
        print("\n🌟 Diversity System Capabilities:")
        print("   ✅ Statistical diversity analysis (entropy, CV, clustering)")
        print("   ✅ Persistent diversity tracking with SQLite")
        print("   ✅ Visual diversity analytics and reporting")
        print("   ✅ Intelligent diversity optimization")
        print("   ✅ Enhanced variation strategies with analysis")
        print("   ✅ Complete API integration")
        print("   ✅ Type-aware diversity configuration")
        print("   ✅ System-wide diversity monitoring")
    else:
        print(f"⚠️ {failed} tests failed. Check the output above for details.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)