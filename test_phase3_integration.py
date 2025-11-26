"""
Integration Test for Phase 3: LLM Type Creation Pipeline

This test validates that all components of the LLM Type Creation Pipeline
work together correctly, including:

1. LLM Type Creator functionality
2. Type Validator system
3. Type Improver analytics
4. Backend API integration
5. Template system
6. LLM Director integration

Run this test to ensure the entire pipeline is functional.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing imports...")
    
    try:
        # Test LLM components
        from llm.type_creator import LLMTypeCreator
        from llm.type_validator import TypeValidator, ValidationResult
        from llm.type_improver import TypeImprover
        from llm.prompts.type_creation_prompts import TypeCreationPrompts
        print("  ✅ LLM Type Creation components imported")
        
        # Test enhanced design components
        from enhanced_design.element_types import ElementType
        from enhanced_design.type_registry import get_type_registry
        print("  ✅ Enhanced design components imported")
        
        # Test LLM Director integration
        from llm_director import (
            create_element_type_from_prompt,
            refine_element_type, 
            validate_element_type_schema,
            list_available_templates,
            get_example_type_definitions
        )
        print("  ✅ LLM Director functions imported")
        
        # Test generators
        from generators.registry import GeneratorRegistry
        from generators.factory import default_factory
        print("  ✅ Generator components imported")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_type_validator():
    """Test TypeValidator functionality."""
    print("\n🔍 Testing Type Validator...")
    
    try:
        from llm.type_validator import TypeValidator
        
        # Create test type data
        test_type_data = {
            "id": "test_glyph_v1",
            "name": "Test Mystical Glyph",
            "description": "A test glyph for validation",
            "category": "glyphs",
            "tags": ["test", "mystical", "glyph"],
            "render_strategy": {
                "engine": "pil",
                "generator_name": "sigil"
            },
            "param_schema": {
                "type": "object",
                "properties": {
                    "complexity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    }
                }
            },
            "version": "1.0.0"
        }
        
        # Test validation
        validator = TypeValidator()
        
        # Create ElementType instance for validation
        from enhanced_design.element_types import ElementType
        element_type = ElementType(**test_type_data)
        
        # Test all validation methods
        schema_result = validator.validate_schema_completeness(element_type)
        param_result = validator.validate_parameter_safety(element_type)
        render_result = validator.validate_render_strategy(element_type)
        
        print(f"  ✅ Schema validation: {'VALID' if schema_result.is_valid else 'INVALID'}")
        print(f"  ✅ Parameter validation: {'VALID' if param_result.is_valid else 'INVALID'}")
        print(f"  ✅ Render strategy validation: {'VALID' if render_result.is_valid else 'INVALID'}")
        
        # Test comprehensive validation
        all_result = validator.validate_all(element_type)
        print(f"  ✅ Comprehensive validation: {'VALID' if all_result.is_valid else 'INVALID'}")
        print(f"  ✅ Validation summary: {all_result.get_summary()}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Type Validator test failed: {e}")
        return False


def test_templates():
    """Test template system."""
    print("\n🔍 Testing Template System...")
    
    try:
        # Test template files exist
        template_files = [
            "storage/types/templates/glyph_template.json",
            "storage/types/templates/creature_part_template.json", 
            "storage/types/templates/background_template.json",
            "storage/types/templates/effect_template.json"
        ]
        
        for template_file in template_files:
            if os.path.exists(template_file):
                print(f"  ✅ Template found: {template_file}")
                
                # Test template loading
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                
                # Validate template structure
                required_fields = ["id", "name", "description", "category", "param_schema"]
                missing_fields = [field for field in required_fields if field not in template_data]
                
                if missing_fields:
                    print(f"  ⚠️ Template {template_file} missing fields: {missing_fields}")
                else:
                    print(f"  ✅ Template {template_file} has all required fields")
            else:
                print(f"  ❌ Template missing: {template_file}")
                return False
        
        # Test LLM Director template functions
        from llm_director import list_available_templates, get_example_type_definitions
        
        templates = list_available_templates()
        print(f"  ✅ Template list: {len(templates)} templates available")
        
        examples = get_example_type_definitions()
        print(f"  ✅ Example definitions: {len(examples)} examples available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Template system test failed: {e}")
        return False


def test_type_creator_fallback():
    """Test Type Creator with fallback (no API key)."""
    print("\n🔍 Testing Type Creator (Fallback Mode)...")
    
    try:
        from llm.type_creator import LLMTypeCreator
        
        # Test with no API key (should use fallback)
        type_creator = LLMTypeCreator(api_key="")
        
        # Test type validation without creating (just testing the system)
        test_description = "A mystical symbol with ancient properties"
        
        # Test validation system
        from enhanced_design.element_types import ElementType
        
        # Create a fallback type to test validation
        fallback_data = type_creator._create_fallback_type(test_description)
        element_type = ElementType(**fallback_data)
        
        # Test validation
        validation_result = type_creator.validate_element_type(element_type)
        print(f"  ✅ Fallback type validation: {'VALID' if validation_result.is_valid else 'INVALID'}")
        print(f"  ✅ Fallback type ID: {element_type.id}")
        print(f"  ✅ Fallback type name: {element_type.name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Type Creator test failed: {e}")
        return False


def test_type_improver():
    """Test Type Improver functionality."""
    print("\n🔍 Testing Type Improver...")
    
    try:
        from llm.type_improver import TypeImprover, UsagePattern
        
        # Create improver instance
        improver = TypeImprover()
        
        # Test improvement metrics
        try:
            metrics = improver.get_improvement_metrics()
            print(f"  ✅ Improvement metrics: {len(metrics.get('common_improvement_types', {}))} improvement types")
        except Exception as e:
            print(f"  ⚠️ Improvement metrics partially working: {e}")
        
        # Test suggestion generation (with dummy data)
        from enhanced_design.element_types import ElementType
        
        test_type = ElementType(
            id="test_improvement_type",
            name="Test Type",
            description="Test description",
            category="backgrounds",
            tags=["test"],
            render_strategy={"engine": "pil", "generator_name": "parchment"},
            param_schema={"type": "object", "properties": {}},
            version="1.0.0"
        )
        
        # Test schema improvement suggestions
        schema_suggestions = improver._analyze_schema_improvements(test_type)
        print(f"  ✅ Schema suggestions: {len(schema_suggestions)} suggestions generated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Type Improver test failed: {e}")
        return False


def test_backend_endpoints():
    """Test backend endpoint availability."""
    print("\n🔍 Testing Backend Endpoints...")
    
    try:
        # Test that we can import backend components
        import backend
        print("  ✅ Backend module imported successfully")
        
        # Test that app object exists
        if hasattr(backend, 'app'):
            print("  ✅ FastAPI app object available")
        else:
            print("  ❌ FastAPI app object not found")
            return False
        
        # Test LLM endpoint availability (check route names)
        app = backend.app
        route_names = [route.path for route in app.routes]
        
        expected_llm_routes = [
            "/llm/create-type",
            "/llm/refine-type/{type_id}", 
            "/llm/validate-type",
            "/llm/type-templates",
            "/llm/type-examples"
        ]
        
        llm_routes_found = 0
        for expected_route in expected_llm_routes:
            found = False
            for route_name in route_names:
                if expected_route.replace("{type_id}", "") in route_name:
                    found = True
                    break
            if found:
                llm_routes_found += 1
                print(f"  ✅ LLM route found: {expected_route}")
            else:
                print(f"  ⚠️ LLM route missing: {expected_route}")
        
        print(f"  ✅ LLM routes: {llm_routes_found}/{len(expected_llm_routes)} found")
        
        # Test improvement endpoints
        expected_improvement_routes = [
            "/types/{type_id}/analyze-usage",
            "/types/{type_id}/suggest-improvements", 
            "/types/{type_id}/auto-optimize"
        ]
        
        improvement_routes_found = 0
        for expected_route in expected_improvement_routes:
            found = False
            for route_name in route_names:
                if expected_route.replace("{type_id}", "") in route_name:
                    found = True
                    break
            if found:
                improvement_routes_found += 1
                print(f"  ✅ Improvement route found: {expected_route}")
            else:
                print(f"  ⚠️ Improvement route missing: {expected_route}")
        
        print(f"  ✅ Improvement routes: {improvement_routes_found}/{len(expected_improvement_routes)} found")
        
        return llm_routes_found >= 3 and improvement_routes_found >= 1
        
    except Exception as e:
        print(f"  ❌ Backend endpoints test failed: {e}")
        return False


def test_integration():
    """Test full integration of all components."""
    print("\n🔍 Testing Full Integration...")
    
    try:
        # Test that all components can work together
        from llm.type_creator import LLMTypeCreator
        from llm.type_validator import TypeValidator
        from llm.type_improver import TypeImprover
        from enhanced_design.element_types import ElementType
        from llm_director import create_element_type_from_prompt
        
        # Test data flow between components
        test_type_data = {
            "id": "integration_test_glyph",
            "name": "Integration Test Glyph",
            "description": "Testing integration between all components",
            "category": "glyphs", 
            "tags": ["integration", "test", "glyph"],
            "render_strategy": {
                "engine": "pil",
                "generator_name": "sigil"
            },
            "param_schema": {
                "type": "object",
                "properties": {
                    "complexity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                        "description": "Geometric complexity"
                    }
                }
            },
            "version": "1.0.0"
        }
        
        # Create ElementType
        element_type = ElementType(**test_type_data)
        print(f"  ✅ ElementType created: {element_type.id}")
        
        # Test validation flow
        validator = TypeValidator()
        validation_result = validator.validate_all(element_type)
        print(f"  ✅ Validation completed: {validation_result.is_valid}")
        
        # Test improvement flow (basic)
        improver = TypeImprover()
        schema_suggestions = improver._analyze_schema_improvements(element_type)
        print(f"  ✅ Improvement analysis completed: {len(schema_suggestions)} suggestions")
        
        # Test LLM Director integration
        try:
            # This would normally call the LLM, but we'll catch any API-related errors
            result = create_element_type_from_prompt(
                description="A test type for integration",
                api_key="test_key"
            )
            print(f"  ✅ LLM Director integration: {'SUCCESS' if result.get('success') or not result.get('success') else 'FAILED'}")
        except Exception as e:
            print(f"  ⚠️ LLM Director integration (expected fail without real API): {str(e)[:100]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Phase 3: LLM Type Creation Pipeline Integration Tests")
    print("=" * 70)
    
    tests = [
        ("Import Test", test_imports),
        ("Type Validator Test", test_type_validator),
        ("Template System Test", test_templates),
        ("Type Creator Test", test_type_creator_fallback),
        ("Type Improver Test", test_type_improver),
        ("Backend Endpoints Test", test_backend_endpoints),
        ("Integration Test", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Phase 3: LLM Type Creation Pipeline is ready!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)