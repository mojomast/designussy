"""
Directed Generator

This module implements the LLM-directed asset generator,
creating assets based on natural language prompts via the LLM Director.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .base_generator import BaseGenerator


@dataclass
class DirectedParams:
    """Parameters for LLM-directed generation."""
    color_hex: str
    complexity: int
    chaos: float
    prompt: str
    model: str
    confidence: float = 0.0
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


class DirectedGenerator(BaseGenerator):
    """
    Generator for LLM-directed asset creation.
    
    Uses natural language prompts to generate assets with parameters
    derived from LLM analysis via the llm_director module.
    """
    
    def __init__(self, generator_type: str = "enso", **kwargs):
        """
        Initialize the directed generator.
        
        Args:
            generator_type: Type of asset to generate ("enso", "sigil", etc.)
            **kwargs: Additional configuration options
        """
        # Import llm_director dynamically to avoid circular imports
        try:
            from llm_director import get_enso_params_from_prompt
            self.llm_director_available = True
            self._get_enso_params = get_enso_params_from_prompt
        except ImportError:
            self.llm_director_available = False
            self._get_enso_params = None
            print("⚠️ LLM Director not available for directed generation")
            
        super().__init__(
            generator_type=generator_type,
            **kwargs
        )
        
        self.generator_type = generator_type
        
    def generate(self, prompt: str, model: str = "gpt-4o", 
                 api_key: Optional[str] = None, base_url: Optional[str] = None,
                 **kwargs) -> Any:
        """
        Generate an asset using LLM-directed parameters.
        
        Args:
            prompt: Natural language description of the desired asset
            model: LLM model to use for analysis
            api_key: API key for LLM service
            base_url: Base URL for LLM service
            **kwargs: Additional generation parameters
            
        Returns:
            Generated PIL Image or other asset type
        """
        if not self.llm_director_available:
            raise RuntimeError("LLM Director not available for directed generation")
        
        self.logger.info(f"Generating {self.generator_type} from prompt: {prompt[:50]}...")
        
        # Get parameters from LLM Director
        try:
            if self.generator_type == "enso":
                params = self._get_enso_params(
                    prompt=prompt, 
                    api_key=api_key, 
                    model=model, 
                    base_url=base_url
                )
                
                # Create appropriate generator instance
                from .enso_generator import EnsoGenerator
                enso_gen = EnsoGenerator(
                    width=kwargs.get('width', 800),
                    height=kwargs.get('height', 800),
                    **kwargs
                )
                
                # Generate from LLM parameters
                return enso_gen.generate_from_params(
                    color_hex=params.color_hex,
                    complexity=params.complexity, 
                    chaos=params.chaos
                )
                
            else:
                # For other generator types, use generic generation
                # This can be extended as more LLM directors are implemented
                raise ValueError(f"LLM-directed generation not supported for {self.generator_type}")
                
        except Exception as e:
            self.logger.error(f"LLM-directed generation failed: {e}")
            raise RuntimeError(f"Failed to generate {self.generator_type} from prompt: {e}")
    
    def generate_batch_directed(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """
        Generate multiple assets from LLM-directed requests.
        
        Args:
            requests: List of generation request dictionaries
            
        Returns:
            List of generated assets
        """
        results = []
        
        for i, request in enumerate(requests):
            try:
                prompt = request.get('prompt', '')
                model = request.get('model', 'gpt-4o')
                api_key = request.get('api_key')
                base_url = request.get('base_url')
                generator_params = request.get('generator_params', {})
                
                asset = self.generate(
                    prompt=prompt,
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    **generator_params
                )
                
                results.append({
                    'index': i,
                    'success': True,
                    'asset': asset,
                    'prompt': prompt
                })
                
                self.logger.info(f"Generated directed asset #{i+1}/{len(requests)}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate directed asset #{i+1}: {e}")
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e),
                    'prompt': request.get('prompt', '')
                })
        
        return results
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of generator types that support LLM-directed generation.
        
        Returns:
            List of supported generator type names
        """
        return ["enso"]  # Currently only enso is supported
    
    def get_generator_type(self) -> str:
        """Get the generator type identifier."""
        return f"directed_{self.generator_type}"
    
    @staticmethod
    def get_default_params() -> dict:
        """
        Get default parameters for this generator type.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'generator_type': 'enso',
            'timeout': 30,
            'max_retries': 3
        }
    
    def save_directed_asset(self, asset: Any, prompt: str, index: int = 0) -> str:
        """
        Save an LLM-directed asset with descriptive naming.
        
        Args:
            asset: Generated asset to save
            prompt: Original prompt used for generation
            index: Asset index number
            
        Returns:
            Path to the saved file
        """
        # Create safe filename from prompt
        safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_prompt = safe_prompt.replace(' ', '_')
        
        if hasattr(asset, 'save'):
            # It's a PIL Image
            filename = f"{self.generator_type}_directed_{index}_{safe_prompt}.png"
            filepath = os.path.join(
                self.output_dir,
                self.category_map.get("glyphs", "glyphs"),
                filename
            )
            asset.save(filepath)
            self.logger.info(f"Saved directed {self.generator_type}: {filepath}")
            return filepath
        else:
            # Handle other asset types as needed
            self.logger.warning(f"Cannot save asset type: {type(asset)}")
            return ""
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate and analyze a prompt for LLM-directed generation.
        
        Args:
            prompt: Natural language prompt to validate
            
        Returns:
            Dictionary with validation results and suggestions
        """
        result = {
            'valid': True,
            'length_ok': True,
            'suggestions': [],
            'estimated_complexity': 'medium'
        }
        
        # Length validation
        if len(prompt) < 5:
            result['valid'] = False
            result['suggestions'].append("Prompt is too short. Add more descriptive details.")
        elif len(prompt) > 500:
            result['length_ok'] = False
            result['suggestions'].append("Prompt is quite long. Consider shortening for better focus.")
        
        # Content analysis
        prompt_lower = prompt.lower()
        
        # Color hints
        color_keywords = ['red', 'blue', 'green', 'yellow', 'purple', 'black', 'white',
                         'crimson', 'azure', 'golden', 'silver', 'dark', 'bright']
        has_color = any(keyword in prompt_lower for keyword in color_keywords)
        
        # Emotion/tone hints
        emotion_keywords = ['calm', 'aggressive', 'peaceful', 'chaotic', 'serene', 'violent',
                           'gentle', 'fierce', 'mysterious', 'bright']
        has_emotion = any(keyword in prompt_lower for keyword in emotion_keywords)
        
        # Complexity indicators
        if 'complex' in prompt_lower or 'intricate' in prompt_lower:
            result['estimated_complexity'] = 'high'
        elif 'simple' in prompt_lower or 'basic' in prompt_lower:
            result['estimated_complexity'] = 'low'
        
        # Suggestions
        if not has_color and not has_emotion:
            result['suggestions'].append("Consider adding color or emotional descriptors for better results.")
        
        return result