"""
Variation Strategies

This module implements the VariationEngine and various strategy classes
for creating diverse outputs from ElementType definitions.

Available strategies:
- JitterStrategy: Randomize parameters within bounds
- StrategyPoolStrategy: Select from multiple generation approaches  
- SeededStrategy: Reproducible randomness with seeds
- ParameterSamplingStrategy: Smart parameter distribution
- CompositionalStrategy: Multi-element combinations
"""

from typing import Dict, Any, Optional, List, Union, Tuple
import logging
import random
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio
import os

# Import type system components
try:
    from enhanced_design.element_types import (
        ElementType, DiversityConfig, DiversityJitterConfig,
        DiversityStrategyPoolConfig, DiversitySeededConfig,
        DiversityParameterSamplingConfig, DiversityCompositionalConfig
    )
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    # Create mock classes for fallback
    class ElementType:
        pass
    class DiversityConfig:
        pass

# Import diversity components (Phase 4)
try:
    from utils.diversity_metrics import DiversityAnalyzer, DiversityReport
    from storage.diversity_tracker import DiversityTracker
    from utils.diversity_viz import DiversityVisualizer
    HAS_DIVERSITY_COMPONENTS = True
except ImportError:
    HAS_DIVERSITY_COMPONENTS = False
    print("⚠️ Diversity components not available - Phase 4 features limited")

# Import batch processing components (Phase 3)
try:
    from utils.batch_job import BatchRequest, GenerationRequest, BatchOptions
    HAS_BATCH_SYSTEM = True
except ImportError:
    HAS_BATCH_SYSTEM = False
    print("⚠️ Batch system not available - batch processing limited")


class GeneratedAsset:
    """Represents a generated asset for diversity analysis."""
    
    def __init__(self, asset_id: str, parameters: Dict[str, Any], image_data: bytes = None, metadata: Dict[str, Any] = None):
        self.asset_id = asset_id
        self.parameters = parameters
        self.image_data = image_data
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_id": self.asset_id,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() + "Z"
        }


class DiversityAnalyzer:
    """Phase 4: Diversity analysis and metrics for the variation engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize diversity components if available
        if HAS_DIVERSITY_COMPONENTS:
            self.metrics_analyzer = DiversityAnalyzer() if HAS_DIVERSITY_COMPONENTS else None
            self.tracker = DiversityTracker() if HAS_DIVERSITY_COMPONENTS else None
            self.visualizer = DiversityVisualizer() if HAS_DIVERSITY_COMPONENTS else None
        else:
            self.metrics_analyzer = None
            self.tracker = None
            self.visualizer = None
    
    def calculate_parameter_diversity(self, params_list: List[Dict[str, Any]]) -> float:
        """Calculate diversity score for parameter sets (0-1)."""
        try:
            if not self.metrics_analyzer:
                return self._calculate_basic_diversity(params_list)
            
            return self.metrics_analyzer.calculate_parameter_diversity(params_list)
            
        except Exception as e:
            self.logger.warning(f"Parameter diversity calculation failed: {e}")
            return self._calculate_basic_diversity(params_list)
    
    def calculate_output_diversity(self, assets_list: List[GeneratedAsset]) -> float:
        """Analyze output asset diversity."""
        try:
            if not self.metrics_analyzer:
                return self._calculate_basic_output_diversity(assets_list)
            
            # Convert GeneratedAsset objects to dictionaries for analysis
            assets_data = [asset.to_dict() for asset in assets_list]
            return self.metrics_analyzer.calculate_output_diversity(assets_data)
            
        except Exception as e:
            self.logger.warning(f"Output diversity calculation failed: {e}")
            return self._calculate_basic_output_diversity(assets_list)
    
    def analyze_variation_coverage(self, element_type: ElementType, samples: int = 100) -> DiversityReport:
        """Test variation coverage for an element type."""
        try:
            if not self.metrics_analyzer:
                return self._create_basic_coverage_report(element_type, samples)
            
            return self.metrics_analyzer.analyze_variation_coverage(element_type.id, samples)
            
        except Exception as e:
            self.logger.warning(f"Variation coverage analysis failed: {e}")
            return self._create_basic_coverage_report(element_type, samples)
    
    def generate_diverse_batch(self,
                              element_type: ElementType,
                              base_params: Dict[str, Any],
                              count: int,
                              seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate a batch of diverse parameter sets."""
        diverse_params = []
        
        try:
            if not element_type.diversity_config:
                # Fallback to basic random variation
                return self._generate_basic_diverse_batch(base_params, count, seed)
            
            # Use the element type's diversity configuration
            for i in range(count):
                # Generate unique seed for each variation
                variation_seed = seed + i if seed is not None else None
                
                # Apply variations using the variation engine
                varied_params = self._apply_diverse_variation(
                    element_type, base_params, element_type.diversity_config, variation_seed
                )
                
                diverse_params.append(varied_params)
            
            self.logger.info(f"Generated {len(diverse_params)} diverse parameter sets")
            return diverse_params
            
        except Exception as e:
            self.logger.error(f"Diverse batch generation failed: {e}")
            return [base_params.copy() for _ in range(count)]  # Fallback to identical params
    
    def get_diversity_metrics(self, params_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get comprehensive diversity metrics for parameter sets."""
        try:
            if not self.metrics_analyzer:
                return self._calculate_basic_metrics(params_list)
            
            metrics = {}
            
            # Parameter diversity
            metrics["parameter_diversity"] = self.calculate_parameter_diversity(params_list)
            
            # Basic statistical measures
            numeric_values = []
            for params in params_list:
                for value in params.values():
                    if isinstance(value, (int, float)):
                        numeric_values.append(float(value))
            
            if numeric_values:
                metrics["mean_value"] = np.mean(numeric_values)
                metrics["std_deviation"] = np.std(numeric_values)
                metrics["coefficient_of_variation"] = metrics["std_deviation"] / metrics["mean_value"] if metrics["mean_value"] > 0 else 0
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Diversity metrics calculation failed: {e}")
            return {"parameter_diversity": 0.0}
    
    def visualize_diversity(self, params_list: List[Dict[str, Any]], plot_type: str = "distribution") -> str:
        """Generate diversity visualization."""
        try:
            if not self.visualizer:
                return "Visualization not available - diversity components not installed"
            
            if plot_type == "distribution":
                return self.visualizer.plot_parameter_distribution(params_list)
            else:
                return "Unknown plot type - supported: distribution"
                
        except Exception as e:
            self.logger.warning(f"Diversity visualization failed: {e}")
            return f"Visualization failed: {str(e)}"
    
    # Private helper methods for fallback implementations
    
    def _calculate_basic_diversity(self, params_list: List[Dict[str, Any]]) -> float:
        """Basic diversity calculation without external dependencies."""
        if len(params_list) < 2:
            return 0.0
        
        try:
            # Extract all numeric values
            all_values = []
            for params in params_list:
                for value in params.values():
                    if isinstance(value, (int, float)):
                        all_values.append(float(value))
            
            if not all_values:
                return 0.0
            
            # Calculate coefficient of variation as diversity measure
            mean_val = np.mean(all_values)
            std_val = np.std(all_values)
            
            if mean_val == 0:
                return 0.0
            
            cv = std_val / mean_val
            return min(1.0, cv)  # Normalize to 0-1
            
        except Exception:
            return 0.0
    
    def _calculate_basic_output_diversity(self, assets_list: List[GeneratedAsset]) -> float:
        """Basic output diversity calculation."""
        if len(assets_list) < 2:
            return 0.0
        
        try:
            # Simple diversity based on parameter variety
            param_sets = [set(asset.parameters.keys()) for asset in assets_list]
            
            # Count unique parameter combinations
            unique_combinations = len(set(frozenset(params.items()) for params in [asset.parameters for asset in assets_list]))
            
            return min(1.0, unique_combinations / len(assets_list))
            
        except Exception:
            return 0.0
    
    def _create_basic_coverage_report(self, element_type: ElementType, samples: int) -> DiversityReport:
        """Create basic coverage report without external dependencies."""
        return DiversityReport(
            timestamp=datetime.utcnow(),
            sample_count=samples,
            metric_scores={"coverage": 0.5},
            recommendations=["Install diversity components for detailed analysis"]
        )
    
    def _generate_basic_diverse_batch(self, base_params: Dict[str, Any], count: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate basic diverse batch without advanced strategies."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        diverse_params = []
        
        for i in range(count):
            varied_params = base_params.copy()
            
            # Add random variation to numeric parameters
            for param_name, value in varied_params.items():
                if isinstance(value, (int, float)):
                    variation = random.uniform(-0.1, 0.1)  # ±10% variation
                    if isinstance(value, int):
                        varied_params[param_name] = max(1, int(value * (1 + variation)))
                    else:
                        varied_params[param_name] = value * (1 + variation)
            
            # Ensure unique seed for each
            varied_params["seed"] = (seed or 0) + i if seed else random.randint(1, 1000000)
            diverse_params.append(varied_params)
        
        return diverse_params
    
    def _calculate_basic_metrics(self, params_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate basic diversity metrics."""
        try:
            metrics = {"parameter_diversity": 0.0}
            
            if not params_list:
                return metrics
            
            # Extract all numeric values
            all_values = []
            for params in params_list:
                for value in params.values():
                    if isinstance(value, (int, float)):
                        all_values.append(float(value))
            
            if all_values:
                metrics["parameter_diversity"] = self._calculate_basic_diversity(params_list)
                metrics["mean_value"] = np.mean(all_values)
                metrics["std_deviation"] = np.std(all_values)
                metrics["min_value"] = min(all_values)
                metrics["max_value"] = max(all_values)
                metrics["value_range"] = max(all_values) - min(all_values)
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Basic metrics calculation failed: {e}")
            return {"parameter_diversity": 0.0}
    
    def _apply_diverse_variation(self,
                                element_type: ElementType,
                                base_params: Dict[str, Any],
                                diversity_config: DiversityConfig,
                                seed: Optional[int] = None) -> Dict[str, Any]:
        """Apply diverse variation using the element type's configuration."""
        try:
            # Create a temporary variation engine for this operation
            temp_engine = VariationEngine()
            return temp_engine.apply_variations(element_type, base_params, diversity_config, seed)
        except Exception as e:
            self.logger.warning(f"Diverse variation application failed: {e}")
            return base_params.copy()


class VariationStrategy(ABC):
    """Abstract base class for all variation strategies."""
    
    @abstractmethod
    def apply_variation(self, 
                       base_params: Dict[str, Any],
                       strategy_config: Any,
                       seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply variation strategy to base parameters.
        
        Args:
            base_params: Base parameters to vary
            strategy_config: Strategy-specific configuration
            seed: Optional seed for reproducible randomness
            
        Returns:
            Varied parameters dictionary
        """
        pass


class JitterStrategy(VariationStrategy):
    """Strategy for randomizing parameters within bounds."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def apply_variation(self, 
                       base_params: Dict[str, Any],
                       strategy_config: DiversityJitterConfig,
                       seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply jitter variation to parameters.
        
        Args:
            base_params: Base parameters to jitter
            strategy_config: Jitter configuration
            seed: Optional seed for reproducible randomness
            
        Returns:
            Parameters with jitter applied
        """
        if not HAS_TYPE_SYSTEM or not isinstance(strategy_config, DiversityJitterConfig):
            return base_params
            
        # Set random seed for reproducibility
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        varied_params = base_params.copy()
        affected_params = strategy_config.affected_parameters or list(base_params.keys())
        jitter_amount = strategy_config.jitter_amount
        
        for param_name in affected_params:
            if param_name in varied_params:
                value = varied_params[param_name]
                
                if isinstance(value, (int, float)):
                    # Numeric jitter
                    if isinstance(value, int):
                        range_val = max(1, int(abs(value) * jitter_amount))
                        jitter = random.randint(-range_val, range_val)
                        varied_params[param_name] = max(0, value + jitter)
                    else:
                        # Float jitter
                        jitter = random.uniform(-jitter_amount, jitter_amount)
                        varied_params[param_name] = value * (1.0 + jitter)
                
                elif isinstance(value, str) and value.startswith('#'):
                    # Color jitter - vary RGB components
                    try:
                        hex_color = value.lstrip('#')
                        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                        
                        # Apply jitter to each component
                        r = max(0, min(255, int(r * (1.0 + random.uniform(-jitter_amount, jitter_amount)))))
                        g = max(0, min(255, int(g * (1.0 + random.uniform(-jitter_amount, jitter_amount)))))
                        b = max(0, min(255, int(b * (1.0 + random.uniform(-jitter_amount, jitter_amount)))))
                        
                        varied_params[param_name] = f"#{r:02x}{g:02x}{b:02x}"
                    except (ValueError, IndexError):
                        # Fallback if color parsing fails
                        pass
                
                # Handle other parameter types as needed
                # Could add more specific handling for lists, dicts, etc.
        
        self.logger.debug(f"Applied jitter variation: {base_params} -> {varied_params}")
        return varied_params


class StrategyPoolStrategy(VariationStrategy):
    """Strategy for selecting from predefined parameter sets."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def apply_variation(self, 
                       base_params: Dict[str, Any],
                       strategy_config: DiversityStrategyPoolConfig,
                       seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply strategy pool variation by selecting from predefined sets.
        
        Args:
            base_params: Base parameters (used as fallback)
            strategy_config: Strategy pool configuration
            seed: Optional seed for reproducible selection
            
        Returns:
            Parameters from selected strategy
        """
        if not HAS_TYPE_SYSTEM or not isinstance(strategy_config, DiversityStrategyPoolConfig):
            return base_params
            
        # Set random seed for reproducible selection
        if seed is not None:
            random.seed(seed)
        
        # Select a strategy from the pool (weighted selection possible)
        strategy_sets = strategy_config.strategy_pool
        if not strategy_sets:
            return base_params
            
        selected_strategy = random.choice(strategy_sets)
        
        # Merge selected strategy with base parameters
        varied_params = base_params.copy()
        varied_params.update(selected_strategy)
        
        self.logger.debug(f"Applied strategy pool variation: selected from {len(strategy_sets)} strategies")
        return varied_params


class SeededStrategy(VariationStrategy):
    """Strategy for reproducible randomness with controlled variation strength."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def apply_variation(self, 
                       base_params: Dict[str, Any],
                       strategy_config: DiversitySeededConfig,
                       seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply seeded variation for reproducible results.
        
        Args:
            base_params: Base parameters to vary
            strategy_config: Seeded configuration
            seed: Seed for reproducible randomness
            
        Returns:
            Reproducibly varied parameters
        """
        if not HAS_TYPE_SYSTEM or not isinstance(strategy_config, DiversitySeededConfig):
            return base_params
            
        if seed is None:
            seed = strategy_config.seed
            
        # Use seed for deterministic variation
        random.seed(seed)
        np.random.seed(seed)
        
        varied_params = base_params.copy()
        variation_strength = strategy_config.variation_strength
        
        # Apply systematic variations based on variation strength
        for param_name, value in varied_params.items():
            if isinstance(value, (int, float)):
                # Create a systematic variation based on seed
                variation_factor = random.uniform(1.0 - variation_strength, 1.0 + variation_strength)
                varied_params[param_name] = value * variation_factor
        
        self.logger.debug(f"Applied seeded variation with strength {variation_strength}")
        return varied_params


class ParameterSamplingStrategy(VariationStrategy):
    """Strategy for smart parameter distribution using statistical sampling."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def apply_variation(self, 
                       base_params: Dict[str, Any],
                       strategy_config: DiversityParameterSamplingConfig,
                       seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply parameter sampling based on distribution configurations.
        
        Args:
            base_params: Base parameters
            strategy_config: Parameter sampling configuration
            seed: Optional seed for reproducible sampling
            
        Returns:
            Parameters sampled from distributions
        """
        if not HAS_TYPE_SYSTEM or not isinstance(strategy_config, DiversityParameterSamplingConfig):
            return base_params
            
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        varied_params = base_params.copy()
        distributions = strategy_config.distributions
        
        for param_name, dist_config in distributions.items():
            dist_type = dist_config.get('type', 'uniform')
            dist_params = dist_config.get('params', {})
            
            if param_name in varied_params:
                try:
                    # Sample from the specified distribution
                    if dist_type == 'normal':
                        mean = dist_params.get('mean', varied_params[param_name])
                        std = dist_params.get('std', 1.0)
                        sample_value = np.random.normal(mean, std)
                    elif dist_type == 'uniform':
                        min_val = dist_params.get('min', varied_params[param_name] * 0.5)
                        max_val = dist_params.get('max', varied_params[param_name] * 1.5)
                        sample_value = np.random.uniform(min_val, max_val)
                    elif dist_type == 'triangular':
                        mode = dist_params.get('mode', varied_params[param_name])
                        min_val = dist_params.get('min', mode * 0.5)
                        max_val = dist_params.get('max', mode * 1.5)
                        sample_value = np.random.triangular(min_val, mode, max_val)
                    elif dist_type == 'exponential':
                        scale = dist_params.get('scale', 1.0)
                        sample_value = np.random.exponential(scale)
                    else:
                        continue  # Unknown distribution type
                    
                    # Convert to appropriate type
                    original_value = varied_params[param_name]
                    if isinstance(original_value, int):
                        varied_params[param_name] = int(sample_value)
                    else:
                        varied_params[param_name] = sample_value
                        
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Failed to sample parameter {param_name}: {e}")
        
        self.logger.debug(f"Applied parameter sampling to {len(distributions)} parameters")
        return varied_params


class CompositionalStrategy(VariationStrategy):
    """Strategy for combining multiple variation approaches."""
    
    def __init__(self, variation_engine: Optional['VariationEngine'] = None):
        self.logger = logging.getLogger(__name__)
        self.variation_engine = variation_engine
    
    def apply_variation(self, 
                       base_params: Dict[str, Any],
                       strategy_config: DiversityCompositionalConfig,
                       seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply compositional variation by combining multiple strategies.
        
        Args:
            base_params: Base parameters
            strategy_config: Compositional configuration
            seed: Optional seed for reproducible composition
            
        Returns:
            Parameters with compositional variations applied
        """
        if not HAS_TYPE_SYSTEM or not isinstance(strategy_config, DiversityCompositionalConfig):
            return base_params
            
        varied_params = base_params.copy()
        composition = strategy_config.composition
        
        if not composition:
            return varied_params
            
        # Apply each composition step in order
        for i, composition_step in enumerate(composition):
            try:
                # Each step should define a strategy and its parameters
                strategy_type = composition_step.get('strategy')
                strategy_params = composition_step.get('params', {})
                
                if strategy_type and self.variation_engine:
                    # Apply the specific strategy
                    step_seed = seed + i if seed is not None else None
                    varied_params = self.variation_engine._apply_single_strategy(
                        varied_params, strategy_type, strategy_params, step_seed
                    )
                    
            except Exception as e:
                self.logger.warning(f"Failed to apply composition step {i}: {e}")
        
        self.logger.debug(f"Applied compositional variation with {len(composition)} steps")
        return varied_params


class VariationEngine:
    """
    Main variation engine that orchestrates different variation strategies.
    
    This engine (enhanced with Phase 4 diversity capabilities):
    - Manages strategy implementations
    - Applies variations based on DiversityConfig
    - Provides a unified interface for all variation approaches
    - Maintains reproducibility with seeds
    - Supports diversity analysis and metrics (Phase 4)
    - Enables efficient batch processing (Phase 4)
    """
    
    def __init__(self):
        """Initialize the variation engine with all strategies."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategy implementations
        self.strategies = {
            'jitter': JitterStrategy(),
            'strategy_pool': StrategyPoolStrategy(),
            'seeded': SeededStrategy(),
            'parameter_sampling': ParameterSamplingStrategy(),
            'compositional': CompositionalStrategy(self)
        }
        
        # Initialize diversity analyzer (Phase 4)
        self.diversity_analyzer = DiversityAnalyzer()
        
        self.logger.info(f"Initialized VariationEngine with {len(self.strategies)} strategies + diversity analysis")
    
    def apply_variations(self,
                        element_type: ElementType,
                        base_params: Dict[str, Any],
                        diversity_config: DiversityConfig,
                        seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Apply variations to parameters based on diversity configuration.
        
        Args:
            element_type: ElementType definition
            base_params: Base parameters to vary
            diversity_config: Diversity configuration
            seed: Optional seed for reproducible variations
            
        Returns:
            Parameters with variations applied
        """
        if not HAS_TYPE_SYSTEM or not isinstance(element_type, ElementType):
            return base_params
            
        strategy = diversity_config.strategy
        varied_params = base_params.copy()
        
        try:
            # Get the appropriate strategy configuration
            strategy_config_map = {
                'jitter': diversity_config.jitter,
                'strategy_pool': diversity_config.strategy_pool,
                'seeded': diversity_config.seeded,
                'parameter_sampling': diversity_config.parameter_sampling,
                'compositional': diversity_config.compositional
            }
            
            strategy_config = strategy_config_map.get(strategy.value if hasattr(strategy, 'value') else strategy)
            
            if strategy_config and strategy in self.strategies:
                varied_params = self.strategies[strategy].apply_variation(
                    base_params=varied_params,
                    strategy_config=strategy_config,
                    seed=seed
                )
            
            # Apply global diversity settings
            if diversity_config.diversity_target < 1.0:
                varied_params = self._apply_diversity_target(varied_params, diversity_config.diversity_target)
            
            self.logger.debug(f"Applied variation strategy '{strategy}' to {len(base_params)} parameters")
            return varied_params
            
        except Exception as e:
            self.logger.error(f"Failed to apply variations: {e}")
            return base_params
    
    def _apply_single_strategy(self,
                             params: Dict[str, Any],
                             strategy_type: str,
                             strategy_config: Dict[str, Any],
                             seed: Optional[int] = None) -> Dict[str, Any]:
        """Apply a single strategy (used by compositional strategy)."""
        if strategy_type not in self.strategies:
            return params
            
        strategy = self.strategies[strategy_type]
        
        # Convert strategy_config dict to appropriate object if needed
        if not HAS_TYPE_SYSTEM:
            return params
            
        return strategy.apply_variation(params, strategy_config, seed)
    
    def _apply_diversity_target(self, params: Dict[str, Any], diversity_target: float) -> Dict[str, Any]:
        """Apply global diversity target to parameters."""
        # Scale parameters based on diversity target
        # This is a simplified implementation - could be more sophisticated
        scale_factor = 0.5 + (diversity_target * 0.5)
        
        varied_params = params.copy()
        for param_name, value in varied_params.items():
            if isinstance(value, (int, float)):
                if isinstance(value, int):
                    varied_params[param_name] = max(1, int(value * scale_factor))
                else:
                    varied_params[param_name] = value * scale_factor
        
        return varied_params
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available variation strategies."""
        return list(self.strategies.keys())
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific strategy."""
        strategy_info = {
            'jitter': 'Randomize parameters within bounds',
            'strategy_pool': 'Select from predefined parameter sets',
            'seeded': 'Reproducible randomness with controlled variation',
            'parameter_sampling': 'Smart parameter distribution using statistics',
            'compositional': 'Combine multiple variation approaches'
        }
        
        return strategy_info.get(strategy_name)
    
    def validate_diversity_config(self, diversity_config: DiversityConfig) -> Dict[str, Any]:
        """Validate a diversity configuration."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not HAS_TYPE_SYSTEM:
            validation_result['valid'] = False
            validation_result['errors'].append("Type system not available")
            return validation_result
            
        try:
            # Check if strategy exists
            strategy = diversity_config.strategy
            if hasattr(strategy, 'value'):
                strategy_name = strategy.value
            else:
                strategy_name = str(strategy)
                
            if strategy_name not in self.strategies:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Unknown strategy: {strategy_name}")
            
            # Validate strategy-specific configurations
            strategy_config_map = {
                'jitter': diversity_config.jitter,
                'strategy_pool': diversity_config.strategy_pool,
                'seeded': diversity_config.seeded,
                'parameter_sampling': diversity_config.parameter_sampling,
                'compositional': diversity_config.compositional
            }
            
            strategy_config = strategy_config_map.get(strategy_name)
            if not strategy_config:
                validation_result['warnings'].append(f"Strategy '{strategy_name}' has no configuration")
                
            # Validate diversity target
            if not (0.0 <= diversity_config.diversity_target <= 1.0):
                validation_result['valid'] = False
                validation_result['errors'].append("Diversity target must be between 0.0 and 1.0")
                
            # Validate max variations
            if diversity_config.max_variations < 1:
                validation_result['valid'] = False
                validation_result['errors'].append("Max variations must be at least 1")
                
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {e}")
        
        return validation_result
    
        def __repr__(self) -> str:
            """String representation of the variation engine."""
            return f"VariationEngine(strategies={list(self.strategies.keys())})"
        
        # ==================== Phase 4: Batch Variation Methods ====================
        
        def generate_diverse_batch(self,
                                  element_type: ElementType,
                                  base_params: Dict[str, Any],
                                  count: int,
                                  seed: Optional[int] = None,
                                  async_mode: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
            """
            Generate a batch of diverse parameter sets efficiently.
            
            Args:
                element_type: ElementType definition
                base_params: Base parameters to vary
                count: Number of variations to generate
                seed: Base seed for reproducible variations
                async_mode: If True, returns job info for async processing
                
            Returns:
                List of diverse parameter sets or async job info
            """
            try:
                if not HAS_TYPE_SYSTEM:
                    self.logger.warning("Type system not available for batch generation")
                    return [base_params.copy() for _ in range(count)]
                
                # Use diversity analyzer for efficient batch generation
                return self.diversity_analyzer.generate_diverse_batch(
                    element_type, base_params, count, seed
                )
                
            except Exception as e:
                self.logger.error(f"Batch diversity generation failed: {e}")
                return [base_params.copy() for _ in range(count)]
        
        def analyze_batch_diversity(self, params_list: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Analyze diversity of a parameter batch."""
            try:
                # Use diversity analyzer for analysis
                metrics = self.diversity_analyzer.get_diversity_metrics(params_list)
                
                # Add batch-specific metrics
                analysis = {
                    "batch_size": len(params_list),
                    "diversity_metrics": metrics,
                    "recommendations": self._generate_batch_recommendations(params_list, metrics),
                    "analysis_timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                return analysis
                
            except Exception as e:
                self.logger.error(f"Batch diversity analysis failed: {e}")
                return {"error": str(e), "batch_size": len(params_list)}
        
        def _generate_batch_recommendations(self, params_list: List[Dict[str, Any]], metrics: Dict[str, float]) -> List[str]:
            """Generate recommendations for improving batch diversity."""
            recommendations = []
            
            try:
                # Analyze parameter diversity
                param_diversity = metrics.get("parameter_diversity", 0.0)
                
                if param_diversity < 0.3:
                    recommendations.append("Low diversity detected - consider using compositional or parameter sampling strategies")
                elif param_diversity > 0.9:
                    recommendations.append("Very high diversity - may want to focus on specific parameter ranges")
                
                # Analyze value ranges
                if "value_range" in metrics:
                    value_range = metrics["value_range"]
                    if value_range < 10:
                        recommendations.append("Narrow value range - consider expanding parameter bounds")
                
                # Coefficient of variation analysis
                if "coefficient_of_variation" in metrics:
                    cv = metrics["coefficient_of_variation"]
                    if cv < 0.1:
                        recommendations.append("Low variation in values - increase jitter or sampling range")
                    elif cv > 2.0:
                        recommendations.append("Very high variation - consider constraining extreme values")
                
                if not recommendations:
                    recommendations.append("Batch diversity appears well-balanced")
                    
            except Exception as e:
                self.logger.warning(f"Recommendation generation failed: {e}")
                recommendations.append("Unable to generate specific recommendations")
            
            return recommendations