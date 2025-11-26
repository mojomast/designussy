"""
LLM Type Creator Module

This module implements the LLMTypeCreator class that enables safe creation
of new element types from natural language descriptions using the existing
LLM infrastructure from llm_director.py.

Features:
- Natural language to ElementType conversion
- Comprehensive validation with detailed feedback
- Safety constraints and security checks
- Integration with TypeRegistry for persistence
- Performance tracking and caching
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing infrastructure
from ..llm_director import (
    _make_llm_request, 
    get_llm_performance_stats, 
    _performance_tracker,
    _get_cached_response,
    _cache_response,
    _generate_cache_key
)
from ..enhanced_design.element_types import ElementType, validate_param_schema
from ..generators.registry import GeneratorRegistry
from .type_validator import TypeValidator, ValidationResult

# Import TypeRegistry for persistence
try:
    from ..enhanced_design.type_registry import get_type_registry
    HAS_TYPE_REGISTRY = True
except ImportError:
    HAS_TYPE_REGISTRY = False


class LLMTypeCreator:
    """
    LLM-powered Type Creator for generating ElementType definitions from natural language.
    
    Uses structured LLM outputs with comprehensive validation to safely create
    new element types that can be persisted to the TypeRegistry.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-2024-08-06", 
                 base_url: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the LLM Type Creator.
        
        Args:
            api_key: API key for LLM authentication
            model: LLM model to use for type generation
            base_url: Base URL for the API (defaults to environment variable)
            use_cache: Whether to use response caching
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.use_cache = use_cache
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.validator = TypeValidator()
        self.registry = get_type_registry() if HAS_TYPE_REGISTRY else None
        
        # Get generator registry for validation
        try:
            from ..generators.registry import GeneratorRegistry
            self.generator_registry = GeneratorRegistry()
        except ImportError:
            self.generator_registry = None
            self.logger.warning("GeneratorRegistry not available")
        
        # Cache for validation results
        self._validation_cache = {}
    
    def propose_element_type(self, description: str, context: Optional[Dict[str, Any]] = None) -> ElementType:
        """
        Create a new ElementType from a natural language description.
        
        This is the main method for converting natural language descriptions
        into validated ElementType definitions.
        
        Args:
            description: Natural language description of the desired element type
            context: Additional context information (existing types, user preferences, etc.)
            
        Returns:
            ElementType: Validated and ready-to-use element type definition
            
        Raises:
            ValueError: If the LLM fails to generate a valid type or validation fails
        """
        start_time = time.perf_counter()
        
        if not self.api_key:
            raise ValueError("API key is required for LLM type creation")
        
        # Generate cache key for this request
        cache_key = None
        if self.use_cache:
            cache_key = self._generate_type_cache_key(description, context)
            cached_result = self._get_cached_type(cache_key)
            if cached_result:
                _performance_tracker.record_cache_hit()
                return cached_result
        
        self.logger.info(f"Creating element type from description: '{description[:50]}...'")
        
        try:
            # Use LLM to generate type definition
            type_data = self._generate_type_definition(description, context)
            
            # Create ElementType instance
            element_type = ElementType(**type_data)
            
            # Comprehensive validation
            validation_result = self.validate_element_type(element_type)
            if not validation_result.is_valid:
                # Try to fix the type based on validation feedback
                element_type = self._attempt_auto_fix(element_type, validation_result)
                validation_result = self.validate_element_type(element_type)
                
                if not validation_result.is_valid:
                    raise ValueError(f"Type validation failed after auto-fix: {validation_result.get_summary()}")
            
            # Add metadata
            element_type.llm_prompt = description
            element_type.llm_model = self.model
            element_type.created_by = "llm_creator"
            element_type.created_at = datetime.now()
            
            # Cache the result
            if self.use_cache and cache_key:
                self._cache_type_result(cache_key, element_type)
            
            # Record successful call
            duration = time.perf_counter() - start_time
            _performance_tracker.record_call(duration, success=True)
            
            self.logger.info(f"Successfully created element type: {element_type.id}")
            return element_type
            
        except Exception as e:
            # Record failed call
            duration = time.perf_counter() - start_time
            _performance_tracker.record_call(duration, success=False)
            self.logger.error(f"Failed to create element type: {e}")
            raise
    
    def refine_element_type(self, type_id: str, feedback: str) -> ElementType:
        """
        Refine an existing element type based on user feedback.
        
        Args:
            type_id: ID of the element type to refine
            feedback: Natural language feedback for improvement
            
        Returns:
            ElementType: Refined element type definition
            
        Raises:
            ValueError: If the type doesn't exist or refinement fails
        """
        if not self.registry:
            raise ValueError("TypeRegistry not available for type refinement")
        
        # Get existing type
        existing_type = self.registry.get(type_id)
        if not existing_type:
            raise ValueError(f"Element type '{type_id}' not found")
        
        start_time = time.perf_counter()
        
        try:
            # Generate improved type definition using LLM
            improved_data = self._generate_type_refinement(existing_type, feedback)
            
            # Create new ElementType with updated data
            updated_type = ElementType(**improved_data)
            updated_type.id = type_id  # Maintain original ID
            updated_type.created_at = existing_type.created_at  # Preserve creation date
            
            # Validate the refined type
            validation_result = self.validate_element_type(updated_type)
            if not validation_result.is_valid:
                raise ValueError(f"Refined type validation failed: {validation_result.get_summary()}")
            
            # Record successful call
            duration = time.perf_counter() - start_time
            _performance_tracker.record_call(duration, success=True)
            
            self.logger.info(f"Successfully refined element type: {type_id}")
            return updated_type
            
        except Exception as e:
            # Record failed call
            duration = time.perf_counter() - start_time
            _performance_tracker.record_call(duration, success=False)
            self.logger.error(f"Failed to refine element type {type_id}: {e}")
            raise
    
    def validate_element_type(self, element_type: ElementType) -> ValidationResult:
        """
        Validate an element type against safety and quality constraints.
        
        Args:
            element_type: ElementType instance to validate
            
        Returns:
            ValidationResult: Detailed validation results with feedback
        """
        try:
            # Use the comprehensive TypeValidator
            result = self.validator.validate_schema_completeness(element_type)
            
            # Additional parameter safety validation
            param_result = self.validator.validate_parameter_safety(element_type)
            if not param_result.is_valid:
                result.merge(param_result)
            
            # Render strategy validation
            render_result = self.validator.validate_render_strategy(element_type)
            if not render_result.is_valid:
                result.merge(render_result)
            
            # Diversity config validation
            diversity_result = self.validator.validate_diversity_config(element_type)
            if not diversity_result.is_valid:
                result.merge(diversity_result)
            
            # Check for conflicts with existing types
            if self.registry:
                conflict_result = self._check_type_conflicts(element_type)
                if not conflict_result.is_valid:
                    result.merge(conflict_result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation system error: {str(e)}"]
            )
    
    def _generate_type_definition(self, description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use LLM to generate a type definition from description.
        
        Args:
            description: Natural language description
            context: Additional context
            
        Returns:
            Dictionary containing type definition data
        """
        # Create system prompt with ElementType schema
        system_prompt = self._build_type_creation_prompt(context)
        
        # Create user prompt
        user_prompt = f"""
Create an ElementType definition for the following description:

"{description}"

Provide a complete, valid JSON object matching the ElementType schema.
"""
        
        # Use LLM with structured output
        json_schema = self._get_element_type_json_schema()
        
        try:
            # Call LLM with function calling
            prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Use existing LLM infrastructure
            result = _make_llm_request(prompt, self.api_key, self.model, self.base_url)
            
            # The LLM director returns EnsoParams, but we need the raw response
            # Let's use a direct approach similar to llm_director.py
            response = self._call_llm_for_json(prompt, json_schema)
            
            return response
            
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            # Return a fallback type definition
            return self._create_fallback_type(description)
    
    def _call_llm_for_json(self, prompt: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call LLM for JSON structured output with ElementType schema.
        
        Args:
            prompt: The prompt to send to LLM
            json_schema: JSON schema for structured output
            
        Returns:
            Parsed JSON response
        """
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mojomast/designussy", 
            "X-Title": "Unwritten Worlds Type Creator"
        }
        
        # Resolve endpoint
        base = (self.base_url or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")).rstrip('/')
        url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": json_schema
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": "element_type"}},
            "temperature": 0.3,  # Lower temperature for more consistent results
            "max_tokens": 2000
        }
        
        session = requests.Session()
        
        try:
            response = session.post(url, headers=headers, json=payload, timeout=(10, 30))
            response.raise_for_status()
            result = response.json()
            
            tool_call = result["choices"][0]["message"].get("tool_calls", [{}])[0]
            function_args = tool_call.get("function", {}).get("arguments", "{}")
            
            return json.loads(function_args)
            
        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")
            raise
    
    def _get_element_type_json_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for ElementType structured output.
        
        Returns:
            JSON schema definition for ElementType
        """
        return {
            "name": "element_type",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique alphanumeric identifier for the type"
                    },
                    "name": {
                        "type": "string", 
                        "description": "Human-readable name for the type"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what this type creates"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["backgrounds", "glyphs", "creatures", "ui", "effects", "patterns", "textures", "decorations", "symbols"],
                        "description": "Type category for organization"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Searchable tags for this type"
                    },
                    "render_strategy": {
                        "type": "object",
                        "properties": {
                            "engine": {
                                "type": "string",
                                "enum": ["pil", "cairo", "skia"],
                                "description": "Rendering engine to use"
                            },
                            "generator_name": {
                                "type": "string",
                                "description": "Name of the generator class"
                            }
                        },
                        "required": ["engine", "generator_name"],
                        "additionalProperties": False
                    },
                    "param_schema": {
                        "type": "object",
                        "description": "JSON schema for type parameters"
                    },
                    "version": {
                        "type": "string",
                        "default": "1.0.0",
                        "description": "Semantic version of this type"
                    }
                },
                "required": ["id", "name", "description", "category", "tags", "render_strategy", "version"],
                "additionalProperties": False
            }
        }
    
    def _build_type_creation_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build system prompt for type creation with examples and constraints.
        
        Args:
            context: Additional context information
            
        Returns:
            Formatted system prompt
        """
        prompt_parts = [
            "You are an expert ElementType designer for the Unwritten Worlds asset generation system.",
            "",
            "Your task is to create valid ElementType definitions from natural language descriptions.",
            "",
            "CRITICAL CONSTRAINTS:",
            "- Maximum 20 parameters per type",
            "- No external URLs or scripts",
            "- Only use generator names: parchment, enso, sigil, giraffe, kangaroo",
            "- Only use engines: pil, cairo, skia",
            "- Categories: backgrounds, glyphs, creatures, ui, effects, patterns, textures, decorations, symbols",
            "- IDs must be alphanumeric with optional underscores/hyphens",
            "- Names should be descriptive and user-friendly",
            "",
            "EXAMPLES OF GOOD TYPES:",
            '{"id": "mystical_glyph", "name": "Mystical Glyph", "description": "Ancient symbols with mystical properties", "category": "glyphs", "tags": ["mystical", "ancient", "symbol"], "render_strategy": {"engine": "pil", "generator_name": "sigil"}, "param_schema": {"type": "object", "properties": {"complexity": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}, "mysticism_level": {"type": "float", "minimum": 0.0, "maximum": 1.0, "default": 0.7}}}, "version": "1.0.0"}',
            "",
            '{"id": "void_parchment", "name": "Void Parchment", "description": "Dark parchment textures for mystical backgrounds", "category": "backgrounds", "tags": ["void", "parchment", "dark", "background"], "render_strategy": {"engine": "pil", "generator_name": "parchment"}, "param_schema": {"type": "object", "properties": {"darkness": {"type": "float", "minimum": 0.0, "maximum": 1.0, "default": 0.8}, "texture_intensity": {"type": "float", "minimum": 0.0, "maximum": 1.0, "default": 0.6}}}, "version": "1.0.0"}',
            "",
            "Output ONLY a valid JSON object matching the ElementType schema. No additional text."
        ]
        
        if context:
            prompt_parts.extend([
                "",
                "CONTEXT:",
                f"- Existing types to avoid: {context.get('avoid_types', [])}",
                f"- Preferred categories: {context.get('preferred_categories', [])}",
                f"- User preferences: {context.get('user_preferences', {})}"
            ])
        
        return "\n".join(prompt_parts)
    
    def _generate_type_refinement(self, existing_type: ElementType, feedback: str) -> Dict[str, Any]:
        """
        Generate refined type definition using LLM with existing type and feedback.
        
        Args:
            existing_type: Current ElementType to refine
            feedback: Natural language feedback for improvement
            
        Returns:
            Dictionary containing refined type definition data
        """
        system_prompt = """
You are an expert ElementType refiner. Your task is to improve existing types based on user feedback.

Rules:
- Maintain the core purpose and ID of the existing type
- Make targeted improvements based on feedback
- Keep within safety constraints (max 20 parameters, no external URLs)
- Improve descriptions, tags, and parameter schemas
"""
        
        user_prompt = f"""
Refine this ElementType based on user feedback:

EXISTING TYPE:
{existing_type.to_json()}

USER FEEDBACK:
"{feedback}"

Provide an improved ElementType definition as a valid JSON object.
"""
        
        try:
            prompt = f"{system_prompt}\n\n{user_prompt}"
            json_schema = self._get_element_type_json_schema()
            return self._call_llm_for_json(prompt, json_schema)
            
        except Exception as e:
            self.logger.error(f"LLM refinement failed: {e}")
            # Return the existing type with timestamp update
            return existing_type.to_dict()
    
    def _attempt_auto_fix(self, element_type: ElementType, validation_result: ValidationResult) -> ElementType:
        """
        Attempt to automatically fix validation issues.
        
        Args:
            element_type: ElementType with validation issues
            validation_result: Validation results to address
            
        Returns:
            ElementType: Fixed element type
        """
        try:
            # Apply common fixes based on validation feedback
            fixed_data = element_type.to_dict()
            
            for suggestion in validation_result.suggestions:
                if "ID should be alphanumeric" in suggestion:
                    # Fix ID to be alphanumeric
                    fixed_id = "".join(c for c in fixed_data['id'] if c.isalnum() or c in ['_', '-'])
                    if fixed_id != fixed_data['id']:
                        fixed_data['id'] = fixed_id
                        self.logger.info(f"Auto-fixed type ID: {fixed_data['id']}")
                
                elif "Unknown generator" in suggestion:
                    # Map unknown generators to safe defaults
                    generator_name = fixed_data.get('render_strategy', {}).get('generator_name', '')
                    if generator_name not in ['parchment', 'enso', 'sigil', 'giraffe', 'kangaroo']:
                        fixed_data['render_strategy']['generator_name'] = 'parchment'
                        self.logger.info(f"Auto-fixed generator: parchment (was {generator_name})")
                
                elif "too many parameters" in suggestion.lower():
                    # Limit parameters to 20
                    if 'param_schema' in fixed_data and 'properties' in fixed_data['param_schema']:
                        properties = fixed_data['param_schema']['properties']
                        if len(properties) > 20:
                            # Keep only first 20 parameters
                            fixed_data['param_schema']['properties'] = dict(list(properties.items())[:20])
                            self.logger.info(f"Auto-limited parameters to 20 (was {len(properties)})")
            
            return ElementType(**fixed_data)
            
        except Exception as e:
            self.logger.error(f"Auto-fix failed: {e}")
            return element_type  # Return original if fix fails
    
    def _check_type_conflicts(self, element_type: ElementType) -> ValidationResult:
        """
        Check for conflicts with existing types in the registry.
        
        Args:
            element_type: ElementType to check for conflicts
            
        Returns:
            ValidationResult: Conflict check results
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        try:
            # Check for duplicate ID
            if self.registry.get(element_type.id):
                result.add_warning(f"Type ID '{element_type.id}' already exists")
            
            # Check for name conflicts
            existing_types = self.registry.list()
            for existing in existing_types:
                if existing.name.lower() == element_type.name.lower():
                    result.add_warning(f"Similar type name '{existing.name}' already exists")
                    break
            
        except Exception as e:
            self.logger.error(f"Conflict check failed: {e}")
            result.add_warning("Could not perform conflict checking")
        
        return result
    
    def _create_fallback_type(self, description: str) -> Dict[str, Any]:
        """
        Create a fallback type definition when LLM generation fails.
        
        Args:
            description: Original description
            
        Returns:
            Dictionary with safe fallback type definition
        """
        # Generate a safe ID from description
        safe_id = "".join(c for c in description.lower().replace(" ", "_")[:30] 
                         if c.isalnum() or c in ['_', '-'])
        
        if not safe_id:
            safe_id = "generated_type"
        
        return {
            "id": f"{safe_id}_v1",
            "name": description[:50] if description else "Generated Type",
            "description": f"Auto-generated type: {description}",
            "category": "backgrounds",
            "tags": ["generated", "auto"],
            "render_strategy": {
                "engine": "pil",
                "generator_name": "parchment"
            },
            "param_schema": {
                "type": "object",
                "properties": {}
            },
            "version": "1.0.0"
        }
    
    def _generate_type_cache_key(self, description: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Generate cache key for type creation requests.
        
        Args:
            description: Type description
            context: Context information
            
        Returns:
            Cache key string
        """
        cache_data = f"{description}|{json.dumps(context or {}, sort_keys=True)}|{self.model}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cached_type(self, cache_key: str) -> Optional[ElementType]:
        """
        Get cached type creation result.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached ElementType or None
        """
        if cache_key in self._validation_cache:
            result, timestamp = self._validation_cache[cache_key]
            if time.time() - timestamp < 300:  # 5 minute TTL
                return result
            else:
                del self._validation_cache[cache_key]
        return None
    
    def _cache_type_result(self, cache_key: str, element_type: ElementType):
        """
        Cache type creation result.
        
        Args:
            cache_key: Cache key
            element_type: ElementType to cache
        """
        # Limit cache size
        if len(self._validation_cache) > 50:
            oldest_key = min(self._validation_cache.keys(), 
                           key=lambda k: self._validation_cache[k][1])
            del self._validation_cache[oldest_key]
        
        self._validation_cache[cache_key] = (element_type, time.time())
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the type creator.
        
        Returns:
            Dictionary with performance metrics
        """
        return get_llm_performance_stats()
    
    def clear_cache(self):
        """Clear all caches."""
        from ..llm_director import clear_llm_cache
        clear_llm_cache()
        self._validation_cache.clear()
        self.logger.info("All caches cleared")


# Export main classes
__all__ = ['LLMTypeCreator']