"""
Type Creation Prompt Templates

This module contains comprehensive prompt templates for LLM-powered type creation,
including system prompts, examples, constraints, and safety rules.

The templates are designed to:
- Guide LLM to create valid ElementType definitions
- Ensure safety and security constraints are followed
- Provide clear examples of good type definitions
- Support various categories and use cases
- Enable natural language to structured output conversion
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """Types of prompts available."""
    TYPE_CREATION = "type_creation"
    TYPE_REFINEMENT = "type_refinement"
    TYPE_VALIDATION = "type_validation"
    TEMPLATE_GENERATION = "template_generation"


@dataclass
class PromptTemplate:
    """Template for a specific prompt type."""
    system_prompt: str
    user_prompt_template: str
    constraints: List[str]
    examples: List[str]
    safety_rules: List[str]


class TypeCreationPrompts:
    """
    Collection of prompt templates for LLM type creation.
    
    These prompts are designed to work with structured output schemas
    and include comprehensive examples and constraints.
    """
    
    # Core safety constraints
    SAFETY_CONSTRAINTS = [
        "Maximum 20 parameters per type definition",
        "No external URLs or scripts allowed",
        "Only use predefined generator names and engines",
        "No code execution or dynamic loading",
        "All parameter values must be bounded and validated",
        "No user input fields that could be exploited"
    ]
    
    # Allowed generators and engines
    ALLOWED_GENERATORS = ["parchment", "enso", "sigil", "giraffe", "kangaroo"]
    ALLOWED_ENGINES = ["pil", "cairo", "skia"]
    VALID_CATEGORIES = [
        "backgrounds", "glyphs", "creatures", "ui", "effects",
        "patterns", "textures", "decorations", "symbols"
    ]
    
    @staticmethod
    def get_system_prompt(prompt_type: PromptType, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get system prompt for the specified type.
        
        Args:
            prompt_type: Type of prompt needed
            context: Additional context information
            
        Returns:
            Formatted system prompt
        """
        base_prompts = {
            PromptType.TYPE_CREATION: TypeCreationPrompts._get_creation_system_prompt(),
            PromptType.TYPE_REFINEMENT: TypeCreationPrompts._get_refinement_system_prompt(),
            PromptType.TYPE_VALIDATION: TypeCreationPrompts._get_validation_system_prompt(),
            PromptType.TEMPLATE_GENERATION: TypeCreationPrompts._get_template_system_prompt()
        }
        
        system_prompt = base_prompts.get(prompt_type, base_prompts[PromptType.TYPE_CREATION])
        
        # Add context if provided
        if context:
            system_prompt += TypeCreationPrompts._add_context_section(context)
        
        return system_prompt
    
    @staticmethod
    def _get_creation_system_prompt() -> str:
        """Get system prompt for type creation."""
        return """
You are an expert ElementType designer for the Unwritten Worlds asset generation system.

Your expertise includes:
- Asset generation pipelines and rendering engines
- JSON schema design and validation
- User experience and interface design
- Parameter optimization and safety constraints

TASK: Create valid ElementType definitions from natural language descriptions.

CORE SCHEMA REQUIREMENTS:
- id: Unique alphanumeric identifier (with _ or - allowed)
- name: Human-readable, descriptive name
- description: Detailed explanation of what this type creates
- category: One of: backgrounds, glyphs, creatures, ui, effects, patterns, textures, decorations, symbols
- tags: Array of searchable keywords
- render_strategy: Defines how to generate assets
  - engine: One of pil, cairo, skia
  - generator_name: One of parchment, enso, sigil, giraffe, kangaroo
- param_schema: JSON schema for type parameters
- version: Semantic version (default: "1.0.0")

PARAMETER DESIGN GUIDELINES:
- Maximum 20 parameters per type
- Use appropriate data types (boolean, integer, float, string)
- Provide clear descriptions and validation bounds
- Use sensible defaults (avoid extremes)
- Keep parameter names descriptive and lowercase_with_underscores

SAFETY CONSTRAINTS:
- Maximum 20 parameters per type definition
- No external URLs or scripts allowed
- Only use predefined generator names and engines
- No code execution or dynamic loading
- All parameter values must be bounded and validated
- No user input fields that could be exploited
"""
    
    @staticmethod
    def _get_refinement_system_prompt() -> str:
        """Get system prompt for type refinement."""
        return """
You are an expert ElementType refiner for the Unwritten Worlds system.

TASK: Improve existing ElementType definitions based on user feedback.

REFINEMENT PRINCIPLES:
- Maintain the core purpose and identity of the existing type
- Keep the same ID and category unless specifically requested
- Improve descriptions, tags, and parameter schemas
- Address specific user concerns and feedback
- Optimize parameter ranges and defaults
- Enhance usability and clarity

SAFETY RULES:
- Never change the generator_name or engine to unsafe values
- Don't add more than 20 parameters
- Don't introduce external URLs or scripts
- Keep parameter bounds reasonable and safe
- Maintain backward compatibility where possible

RULES FOR IMPROVEMENT:
- Better descriptions make types easier to understand
- More specific tags improve discoverability
- Parameter bounds should prevent edge cases
- Defaults should represent common use cases
- Names should be clear and descriptive
"""
    
    @staticmethod
    def _get_validation_system_prompt() -> str:
        """Get system prompt for type validation."""
        return """
You are an expert ElementType validator for the Unwritten Worlds system.

TASK: Validate ElementType definitions and provide improvement suggestions.

VALIDATION CRITERIA:
1. Schema Completeness
   - All required fields present
   - Proper data types
   - Valid enum values

2. Parameter Safety
   - Bounded ranges
   - No unlimited values
   - Reasonable defaults

3. Render Strategy Validity
   - Available generator
   - Supported engine
   - Compatible combinations

4. Usability
   - Clear descriptions
   - Descriptive names
   - Useful tags

5. Best Practices
   - Clean parameter schema
   - Logical groupings
   - Performance considerations
"""
    
    @staticmethod
    def _get_template_system_prompt() -> str:
        """Get system prompt for template generation."""
        return """
You are an expert template designer for the Unwritten Worlds ElementType system.

TASK: Create ElementType templates for common use cases.

TEMPLATE PRINCIPLES:
- Provide starting points for common type categories
- Include typical parameters and configurations
- Use proven parameter schemas as foundations
- Include comprehensive documentation
- Enable easy customization and extension

CATEGORY TEMPLATES:
- Glyphs: Symbolic elements with controllable complexity
- Creatures: Organic forms with size and style variation
- Backgrounds: Textures and scenes with mood control
- Effects: Visual enhancements with intensity controls
- UI: Interface elements with sizing and styling options
- Patterns: Repeating designs with density and scale
"""
    
    @staticmethod
    def _add_context_section(context: Dict[str, Any]) -> str:
        """Add context section to system prompt."""
        sections = ["", "CONTEXT INFORMATION:"]
        
        if 'avoid_types' in context:
            sections.append(f"- Avoid creating similar types to: {', '.join(context['avoid_types'])}")
        
        if 'preferred_categories' in context:
            sections.append(f"- Prefer these categories: {', '.join(context['preferred_categories'])}")
        
        if 'user_preferences' in context:
            prefs = context['user_preferences']
            sections.append(f"- User preferences: {prefs}")
        
        if 'style_guidelines' in context:
            sections.append(f"- Style guidelines: {context['style_guidelines']}")
        
        return "\n".join(sections)
    
    @staticmethod
    def get_user_prompt_template(prompt_type: PromptType) -> str:
        """
        Get user prompt template for the specified type.
        
        Args:
            prompt_type: Type of prompt needed
            
        Returns:
            User prompt template with placeholders
        """
        templates = {
            PromptType.TYPE_CREATION: """
Create an ElementType for: {description}

{additional_context}

Provide a complete, valid JSON object matching the ElementType schema.
""",
            PromptType.TYPE_REFINEMENT: """
Refine this ElementType based on user feedback:

EXISTING TYPE:
{existing_type}

USER FEEDBACK:
"{feedback}"

Provide an improved ElementType definition as a valid JSON object.
""",
            PromptType.TYPE_VALIDATION: """
Validate this ElementType and suggest improvements:

TYPE TO VALIDATE:
{element_type}

Provide validation results and improvement suggestions.
""",
            PromptType.TEMPLATE_GENERATION: """
Create a template for {category} category types.

Template should include:
- Standard parameter schema
- Common configurations
- Usage guidelines
- Extension examples

Provide a template ElementType as a valid JSON object.
"""
        }
        
        return templates.get(prompt_type, templates[PromptType.TYPE_CREATION])
    
    @staticmethod
    def get_good_examples() -> List[str]:
        """
        Get examples of good ElementType definitions.
        
        Returns:
            List of JSON examples demonstrating best practices
        """
        return [
            # Mystical Glyph
            """{
    "id": "mystical_glyph",
    "name": "Mystical Glyph",
    "description": "Ancient symbols with mystical properties, featuring complex geometric patterns",
    "category": "glyphs",
    "tags": ["mystical", "ancient", "symbol", "geometric", "complex"],
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
                "description": "Geometric complexity of the symbol"
            },
            "mysticism_level": {
                "type": "float",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.7,
                "description": "Intensity of mystical properties"
            },
            "symbol_size": {
                "type": "integer",
                "minimum": 64,
                "maximum": 512,
                "default": 256,
                "description": "Size of the symbol in pixels"
            },
            "ink_density": {
                "type": "float",
                "minimum": 0.1,
                "maximum": 1.0,
                "default": 0.8,
                "description": "Thickness of symbol lines"
            }
        }
    },
    "version": "1.0.0"
}""",
            
            # Void Parchment
            """{
    "id": "void_parchment",
    "name": "Void Parchment",
    "description": "Dark parchment textures for mystical backgrounds, featuring aged paper with void-like properties",
    "category": "backgrounds",
    "tags": ["void", "parchment", "dark", "background", "aged", "textured"],
    "render_strategy": {
        "engine": "pil",
        "generator_name": "parchment"
    },
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
            },
            "void_presence": {
                "type": "float",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.5,
                "description": "Amount of void-like distortions"
            },
            "grain_density": {
                "type": "integer",
                "minimum": 10,
                "maximum": 100,
                "default": 50,
                "description": "Paper grain density"
            }
        }
    },
    "version": "1.0.0"
}""",
            
            # Celestial Enso
            """{
    "id": "celestial_enso",
    "name": "Celestial Enso",
    "description": "Circular brush strokes representing cosmic energy and celestial movements",
    "category": "glyphs",
    "tags": ["enso", "celestial", "cosmic", "circular", "brush", "energy"],
    "render_strategy": {
        "engine": "pil",
        "generator_name": "enso"
    },
    "param_schema": {
        "type": "object",
        "properties": {
            "color_hex": {
                "type": "string",
                "pattern": "^#[0-9A-Fa-f]{6}$",
                "default": "#FFD700",
                "description": "Base color of the enso"
            },
            "complexity": {
                "type": "integer",
                "minimum": 20,
                "maximum": 100,
                "default": 60,
                "description": "Number of brush strokes"
            },
            "chaos": {
                "type": "float",
                "minimum": 0.1,
                "maximum": 2.0,
                "default": 0.8,
                "description": "Irregularity of the circle"
            },
            "celestial_intensity": {
                "type": "float",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.7,
                "description": "Brightness and glow effect"
            },
            "text_overlay": {
                "type": "string",
                "maxLength": 50,
                "default": "COSMIC ENERGY",
                "description": "Optional text overlay"
            }
        }
    },
    "version": "1.0.0"
}"""
        ]
    
    @staticmethod
    def get_safety_guidelines() -> List[str]:
        """
        Get comprehensive safety guidelines for type creation.
        
        Returns:
            List of safety rules and best practices
        """
        return [
            "PARAMETER LIMITS: Maximum 20 parameters per type definition",
            "URL RESTRICTION: No external URLs or hyperlinks allowed",
            "SCRIPT PREVENTION: No dynamic script loading or execution",
            "GENERATOR WHITELIST: Only use: parchment, enso, sigil, giraffe, kangaroo",
            "ENGINE WHITELIST: Only use: pil, cairo, skia",
            "CATEGORY VALIDATION: Only use predefined categories",
            "BOUNDED VALUES: All numeric parameters must have min/max bounds",
            "SAFE DEFAULTS: Default values should be safe and reasonable",
            "NO_USER_INPUT: Avoid parameters that accept arbitrary user input",
            "ESCAPE_SAFETY: No parameters that could be used for injection attacks",
            "RESOURCE_LIMITS: Avoid parameters that could cause excessive resource usage",
            "SCHEMA_VALIDATION: Ensure parameter schema follows JSON Schema standards",
            "DESCRIPTION_CLARITY: Provide clear, non-misleading descriptions",
            "TAG_RELEVANCE: Tags should accurately describe the type's purpose",
            "NAME_DESCRIPTIVENESS: Names should clearly indicate what the type creates",
            "BACKWARD_COMPATIBILITY: Avoid breaking changes in parameter schemas",
            "PERFORMANCE_AWARENESS: Consider computational cost of generated assets",
            "ACCESSIBILITY: Ensure types can be used by diverse user scenarios"
        ]
    
    @staticmethod
    def get_category_guidelines() -> Dict[str, Dict[str, Any]]:
        """
        Get guidelines for different type categories.
        
        Returns:
            Dictionary mapping categories to their specific guidelines
        """
        return {
            "glyphs": {
                "description": "Symbols, icons, and visual markers",
                "typical_parameters": ["complexity", "style", "size", "ink_density"],
                "safety_notes": "Ensure symbols don't contain offensive content",
                "examples": ["mystical_glyph", "power_symbol", "runic_text"],
                "common_tags": ["symbol", "icon", "geometric", "ink", "ancient"]
            },
            "creatures": {
                "description": "Organic beings, animals, and life forms",
                "typical_parameters": ["size", "complexity", "mood", "species_type"],
                "safety_notes": "Avoid generating harmful or dangerous creatures",
                "examples": ["mystical_animal", "void_creature", "elemental_being"],
                "common_tags": ["creature", "organic", "living", "animal", "mystical"]
            },
            "backgrounds": {
                "description": "Scenes, textures, and environmental elements",
                "typical_parameters": ["texture", "darkness", "style", "color_palette"],
                "safety_notes": "Ensure backgrounds don't create visual confusion",
                "examples": ["void_parchment", "mystical_forest", "cosmic_scene"],
                "common_tags": ["background", "texture", "scene", "environment", "atmospheric"]
            },
            "effects": {
                "description": "Visual effects, particles, and enhancements",
                "typical_parameters": ["intensity", "duration", "color", "size"],
                "safety_notes": "Avoid effects that could cause visual discomfort",
                "examples": ["ink_splash", "energy_glow", "particle_trail"],
                "common_tags": ["effect", "visual", "enhancement", "particle", "glow"]
            },
            "ui": {
                "description": "User interface elements and controls",
                "typical_parameters": ["size", "style", "color", "transparency"],
                "safety_notes": "Ensure UI elements are accessible and usable",
                "examples": ["mystical_button", "void_panel", "glyph_container"],
                "common_tags": ["ui", "interface", "button", "panel", "control"]
            },
            "patterns": {
                "description": "Repeating designs and textures",
                "typical_parameters": ["density", "scale", "complexity", "repetition"],
                "safety_notes": "Avoid patterns that could trigger photosensitive reactions",
                "examples": ["void_pattern", "mystical_repeat", "glyph_sequence"],
                "common_tags": ["pattern", "repeat", "texture", "design", "geometric"]
            }
        }


# Export main classes and functions
__all__ = [
    'PromptType',
    'PromptTemplate', 
    'TypeCreationPrompts'
]