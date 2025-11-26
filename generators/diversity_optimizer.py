"""
Diversity Optimizer

This module provides intelligent diversity optimization for the NanoBanana
generation system, automatically improving diversity configurations based on
analysis and LLM-powered suggestions.

Features:
- Automatic diversity optimization for element types
- Intelligent suggestions for improvement
- Diverse batch parameter generation
- LLM integration for advanced recommendations
- Integration with existing variation strategies
"""

from typing import List, Dict, Any, Optional, Tuple
import random
import logging
import json
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import math

# Import existing components
try:
    from enhanced_design.element_types import (
        ElementType, DiversityConfig, VariationStrategy,
        DiversityJitterConfig, DiversityStrategyPoolConfig,
        DiversitySeededConfig, DiversityParameterSamplingConfig,
        DiversityCompositionalConfig
    )
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    print("⚠️ Type system not available for diversity optimizer")

try:
    from utils.diversity_metrics import DiversityAnalyzer, DiversityReport
    from storage.diversity_tracker import DiversityTracker
    from utils.diversity_viz import DiversityVisualizer
    HAS_DIVERSITY_COMPONENTS = True
except ImportError:
    HAS_DIVERSITY_COMPONENTS = False
    print("⚠️ Diversity components not available")

try:
    from generators.variation_strategies import VariationEngine
    HAS_VARIATION_ENGINE = True
except ImportError:
    HAS_VARIATION_ENGINE = False
    print("⚠️ Variation engine not available")

# Optional LLM integration
try:
    from llm_director import get_enso_params_from_prompt
    HAS_LLM = True
except ImportError:
    HAS_LLM = False
    print("⚠️ LLM integration not available")


class OptimizationGoal(Enum):
    """Types of diversity optimization goals."""
    MAXIMIZE_DIVERSITY = "maximize_diversity"
    BALANCE_VARIETY = "balance_variety"
    IMPROVE_COVERAGE = "improve_coverage"
    REDUCE_CLUSTERING = "reduce_clustering"
    ENHANCE_UNIQUENESS = "enhance_uniqueness"


@dataclass
class OptimizationResult:
    """Result of diversity optimization."""
    original_element_type: ElementType
    optimized_element_type: ElementType
    optimization_goal: OptimizationGoal
    improvements_applied: List[str]
    predicted_diversity_score: float
    confidence: float
    recommendations: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_element_type": self.original_element_type.id if HAS_TYPE_SYSTEM else "unknown",
            "optimized_element_type": self.optimized_element_type.id if HAS_TYPE_SYSTEM else "unknown",
            "optimization_goal": self.optimization_goal.value,
            "improvements_applied": self.improvements_applied,
            "predicted_diversity_score": self.predicted_diversity_score,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat() + "Z"
        }


@dataclass
class DiversitySuggestion:
    """Individual diversity improvement suggestion."""
    parameter: str
    current_value: Any
    suggested_value: Any
    rationale: str
    impact_score: float  # 0-1 scale
    implementation_difficulty: str  # "easy", "medium", "hard"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parameter": self.parameter,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "rationale": self.rationale,
            "impact_score": self.impact_score,
            "implementation_difficulty": self.implementation_difficulty
        }


class DiversityOptimizer:
    """
    Main diversity optimization engine.
    
    Provides intelligent optimization of diversity configurations
    with automated improvement suggestions and batch generation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.analyzer = DiversityAnalyzer() if HAS_DIVERSITY_COMPONENTS else None
        self.tracker = DiversityTracker() if HAS_DIVERSITY_COMPONENTS else None
        self.visualizer = DiversityVisualizer() if HAS_DIVERSITY_COMPONENTS else None
        self.variation_engine = VariationEngine() if HAS_VARIATION_ENGINE else None
        
        self.logger.info("DiversityOptimizer initialized")
    
    def optimize_type_diversity(self, 
                               element_type: ElementType,
                               goal: OptimizationGoal = OptimizationGoal.BALANCE_VARIETY,
                               max_changes: int = 5) -> OptimizationResult:
        """
        Automatically optimize diversity configuration for an element type.
        
        Args:
            element_type: ElementType to optimize
            goal: Optimization goal to target
            max_changes: Maximum number of changes to apply
            
        Returns:
            OptimizationResult with optimized configuration
        """
        try:
            if not HAS_TYPE_SYSTEM:
                raise RuntimeError("Type system not available")
            
            if not element_type.diversity_config:
                # Create a default diversity config if none exists
                optimized_type = self._create_default_diversity_config(element_type)
                return OptimizationResult(
                    original_element_type=element_type,
                    optimized_element_type=optimized_type,
                    optimization_goal=goal,
                    improvements_applied=["Created default diversity configuration"],
                    predicted_diversity_score=0.5,
                    confidence=0.3,
                    recommendations=["Configure specific diversity parameters for better results"]
                )
            
            # Get optimization suggestions
            suggestions = self.suggest_diversity_improvements(element_type, goal)
            
            # Apply best suggestions up to max_changes
            optimized_type = element_type.copy() if hasattr(element_type, 'copy') else element_type
            applied_changes = []
            
            # Sort suggestions by impact score
            suggestions.sort(key=lambda x: x.impact_score, reverse=True)
            
            for suggestion in suggestions[:max_changes]:
                try:
                    success = self._apply_suggestion(optimized_type, suggestion)
                    if success:
                        applied_changes.append(f"Applied {suggestion.parameter}: {suggestion.current_value} → {suggestion.suggested_value}")
                except Exception as e:
                    self.logger.warning(f"Failed to apply suggestion {suggestion.parameter}: {e}")
            
            # Calculate predicted diversity score
            predicted_score = self._predict_diversity_score(optimized_type, goal)
            
            # Calculate confidence based on applied changes
            confidence = min(0.9, len(applied_changes) / max_changes * 0.8 + 0.2)
            
            # Generate final recommendations
            final_recommendations = self._generate_final_recommendations(element_type, optimized_type, goal)
            
            return OptimizationResult(
                original_element_type=element_type,
                optimized_element_type=optimized_type,
                optimization_goal=goal,
                improvements_applied=applied_changes,
                predicted_diversity_score=predicted_score,
                confidence=confidence,
                recommendations=final_recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Diversity optimization failed: {e}")
            return OptimizationResult(
                original_element_type=element_type,
                optimized_element_type=element_type,
                optimization_goal=goal,
                improvements_applied=[],
                predicted_diversity_score=0.0,
                confidence=0.0,
                recommendations=[f"Optimization failed: {str(e)}"]
            )
    
    def suggest_diversity_improvements(self, 
                                      element_type: ElementType,
                                      goal: OptimizationGoal = OptimizationGoal.BALANCE_VARIETY) -> List[DiversitySuggestion]:
        """
        Generate intelligent suggestions for diversity improvement.
        
        Args:
            element_type: ElementType to analyze
            goal: Optimization goal to target
            
        Returns:
            List of DiversitySuggestion objects
        """
        suggestions = []
        
        try:
            if not HAS_TYPE_SYSTEM:
                return []
            
            if not element_type.diversity_config:
                # Suggest creating diversity config
                suggestions.append(DiversitySuggestion(
                    parameter="diversity_config",
                    current_value=None,
                    suggested_value="Enable diversity configuration",
                    rationale="Diversity configuration is missing - this is essential for variation",
                    impact_score=0.9,
                    implementation_difficulty="easy"
                ))
                return suggestions
            
            diversity_config = element_type.diversity_config
            
            # Strategy-based suggestions
            strategy_suggestions = self._analyze_strategy_configuration(diversity_config, goal)
            suggestions.extend(strategy_suggestions)
            
            # Parameter-based suggestions
            param_suggestions = self._analyze_parameter_ranges(element_type, goal)
            suggestions.extend(param_suggestions)
            
            # Historical performance suggestions
            if self.tracker:
                history_suggestions = self._analyze_historical_performance(element_type, goal)
                suggestions.extend(history_suggestions)
            
            # LLM-powered suggestions if available
            if HAS_LLM and len(suggestions) < 10:
                llm_suggestions = self._generate_llm_suggestions(element_type, goal)
                suggestions.extend(llm_suggestions)
            
            # Sort by impact score
            suggestions.sort(key=lambda x: x.impact_score, reverse=True)
            
            self.logger.debug(f"Generated {len(suggestions)} diversity improvement suggestions")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {e}")
            return []
    
    def generate_diverse_batch(self, 
                              element_type: ElementType,
                              count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate diverse parameter sets for batch processing.
        
        Uses intelligent sampling strategies to ensure maximum diversity.
        
        Args:
            element_type: ElementType to generate parameters for
            count: Number of parameter sets to generate
            
        Returns:
            List of diverse parameter dictionaries
        """
        try:
            if not HAS_TYPE_SYSTEM:
                self.logger.error("Type system not available for batch generation")
                return []
            
            # Get default parameters
            base_params = element_type.get_default_params()
            
            # Determine sampling strategy based on diversity config
            sampling_strategy = self._determine_sampling_strategy(element_type)
            
            # Generate diverse parameters
            if sampling_strategy == "latin_hypercube":
                return self._generate_latin_hypercube_samples(base_params, count)
            elif sampling_strategy == "sobol":
                return self._generate_sobol_samples(base_params, count)
            elif sampling_strategy == "halton":
                return self._generate_halton_samples(base_params, count)
            else:  # random
                return self._generate_random_samples(base_params, count)
                
        except Exception as e:
            self.logger.error(f"Diverse batch generation failed: {e}")
            return []
    
    def analyze_optimization_opportunities(self, element_types: List[ElementType]) -> Dict[str, Any]:
        """
        Analyze optimization opportunities across multiple element types.
        
        Args:
            element_types: List of ElementTypes to analyze
            
        Returns:
            Comprehensive analysis with opportunities and priorities
        """
        try:
            if not HAS_TYPE_SYSTEM:
                return {"error": "Type system not available"}
            
            analysis = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "total_types": len(element_types),
                "optimization_opportunities": [],
                "priority_fixes": [],
                "system_wide_recommendations": [],
                "estimated_improvements": {}
            }
            
            # Analyze each type
            for element_type in element_types:
                if not element_type.diversity_config:
                    analysis["optimization_opportunities"].append({
                        "type_id": element_type.id,
                        "type_name": element_type.name,
                        "issue": "No diversity configuration",
                        "impact": "high",
                        "effort": "low",
                        "suggestion": "Add basic diversity configuration"
                    })
                    continue
                
                # Analyze diversity config
                config_analysis = self._analyze_diversity_configuration(element_type)
                
                if config_analysis["needs_optimization"]:
                    analysis["optimization_opportunities"].append({
                        "type_id": element_type.id,
                        "type_name": element_type.name,
                        "issues": config_analysis["issues"],
                        "current_score": config_analysis.get("current_diversity_score", 0.0),
                        "potential_improvement": config_analysis.get("potential_improvement", 0.0)
                    })
            
            # Identify priority fixes
            high_impact_low_effort = [
                opp for opp in analysis["optimization_opportunities"] 
                if opp.get("impact") == "high" and opp.get("effort") == "low"
            ]
            analysis["priority_fixes"] = high_impact_low_effort
            
            # System-wide recommendations
            analysis["system_wide_recommendations"] = self._generate_system_recommendations(element_types)
            
            # Calculate estimated improvements
            total_opportunities = len(analysis["optimization_opportunities"])
            if total_opportunities > 0:
                avg_improvement = sum(
                    opp.get("potential_improvement", 0.0) 
                    for opp in analysis["optimization_opportunities"]
                ) / total_opportunities
                
                analysis["estimated_improvements"] = {
                    "average_diversity_increase": avg_improvement,
                    "total_types_improvable": total_opportunities,
                    "priority_fixes_count": len(high_impact_low_effort)
                }
            
            self.logger.info(f"Analyzed {len(element_types)} types, found {len(analysis['optimization_opportunities'])} opportunities")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Optimization analysis failed: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    # Private helper methods
    
    def _create_default_diversity_config(self, element_type: ElementType) -> ElementType:
        """Create a default diversity configuration for an element type."""
        # Create default jitter configuration
        jitter_config = DiversityJitterConfig(
            jitter_amount=0.1,
            affected_parameters=list(element_type.get_default_params().keys())
        )
        
        # Create diversity config
        diversity_config = DiversityConfig(
            strategy=VariationStrategy.JITTER,
            jitter=jitter_config,
            diversity_target=0.7,
            max_variations=100
        )
        
        # Update element type
        updated_type = element_type.copy() if hasattr(element_type, 'copy') else element_type
        updated_type.diversity_config = diversity_config
        
        return updated_type
    
    def _analyze_strategy_configuration(self, diversity_config: DiversityConfig, goal: OptimizationGoal) -> List[DiversitySuggestion]:
        """Analyze strategy configuration and suggest improvements."""
        suggestions = []
        
        try:
            # Current strategy analysis
            current_strategy = diversity_config.strategy
            
            # Strategy effectiveness mapping
            strategy_effectiveness = {
                OptimizationGoal.MAXIMIZE_DIVERSITY: [VariationStrategy.COMPOSITIONAL, VariationStrategy.PARAMETER_SAMPLING],
                OptimizationGoal.BALANCE_VARIETY: [VariationStrategy.JITTER, VariationStrategy.SEEDED],
                OptimizationGoal.IMPROVE_COVERAGE: [VariationStrategy.PARAMETER_SAMPLING],
                OptimizationGoal.REDUCE_CLUSTERING: [VariationStrategy.STRATEGY_POOL],
                OptimizationGoal.ENHANCE_UNIQUENESS: [VariationStrategy.SEEDED, VariationStrategy.COMPOSITIONAL]
            }
            
            best_strategies = strategy_effectiveness.get(goal, [])
            
            if current_strategy not in best_strategies:
                # Suggest better strategy
                if best_strategies:
                    best_strategy = best_strategies[0]
                    suggestions.append(DiversitySuggestion(
                        parameter="strategy",
                        current_value=current_strategy.value,
                        suggested_value=best_strategy.value,
                        rationale=f"For goal '{goal.value}', '{best_strategy.value}' strategy is more effective",
                        impact_score=0.8,
                        implementation_difficulty="easy"
                    ))
            
            # Analyze strategy-specific parameters
            if current_strategy == VariationStrategy.JITTER and diversity_config.jitter:
                # Jitter-specific suggestions
                if diversity_config.jitter.jitter_amount < 0.1:
                    suggestions.append(DiversitySuggestion(
                        parameter="jitter_amount",
                        current_value=diversity_config.jitter.jitter_amount,
                        suggested_value=0.15,
                        rationale="Low jitter amount may not create enough variation",
                        impact_score=0.6,
                        implementation_difficulty="easy"
                    ))
                
                if len(diversity_config.jitter.affected_parameters) == 0:
                    suggestions.append(DiversitySuggestion(
                        parameter="affected_parameters",
                        current_value=[],
                        suggested_value="all",
                        rationale="Jittering all parameters will create more diverse outputs",
                        impact_score=0.7,
                        implementation_difficulty="medium"
                    ))
            
            elif current_strategy == VariationStrategy.SEEDED and diversity_config.seeded:
                # Seeded strategy suggestions
                if diversity_config.seeded.variation_strength < 0.05:
                    suggestions.append(DiversitySuggestion(
                        parameter="variation_strength",
                        current_value=diversity_config.seeded.variation_strength,
                        suggested_value=0.1,
                        rationale="Higher variation strength will create more distinct seeded variations",
                        impact_score=0.5,
                        implementation_difficulty="easy"
                    ))
            
        except Exception as e:
            self.logger.warning(f"Strategy analysis failed: {e}")
        
        return suggestions
    
    def _analyze_parameter_ranges(self, element_type: ElementType, goal: OptimizationGoal) -> List[DiversitySuggestion]:
        """Analyze parameter ranges and suggest improvements."""
        suggestions = []
        
        try:
            if not HAS_TYPE_SYSTEM:
                return suggestions
            
            param_schema = element_type.param_schema
            default_params = element_type.get_default_params()
            
            # Analyze parameter ranges in schema
            if "properties" in param_schema:
                for param_name, param_def in param_schema["properties"].items():
                    current_value = default_params.get(param_name)
                    
                    # Check for range constraints
                    if "minimum" in param_def and "maximum" in param_def:
                        min_val = param_def["minimum"]
                        max_val = param_def["maximum"]
                        current_range = max_val - min_val
                        
                        # Suggest wider ranges for diversity goals
                        if goal in [OptimizationGoal.MAXIMIZE_DIVERSITY, OptimizationGoal.IMPROVE_COVERAGE]:
                            if current_range < (max_val - min_val) * 0.8:
                                new_range = min_val + (max_val - min_val) * 0.9
                                suggestions.append(DiversitySuggestion(
                                    parameter=f"{param_name}_range",
                                    current_value=current_range,
                                    suggested_value=new_range,
                                    rationale=f"Wider range for {param_name} will improve diversity coverage",
                                    impact_score=0.6,
                                    implementation_difficulty="hard"
                                ))
                    
                    # Check for enum values (categorical parameters)
                    if "enum" in param_def and len(param_def["enum"]) < 5:
                        suggestions.append(DiversitySuggestion(
                            parameter=f"{param_name}_enum",
                            current_value=len(param_def["enum"]),
                            suggested_value=min(len(param_def["enum"]) + 3, 10),
                            rationale=f"More options for {param_name} will increase categorical diversity",
                            impact_score=0.5,
                            implementation_difficulty="medium"
                        ))
            
        except Exception as e:
            self.logger.warning(f"Parameter range analysis failed: {e}")
        
        return suggestions
    
    def _analyze_historical_performance(self, element_type: ElementType, goal: OptimizationGoal) -> List[DiversitySuggestion]:
        """Analyze historical performance and suggest improvements."""
        suggestions = []
        
        try:
            if not self.tracker:
                return suggestions
            
            # Get recent diversity history
            history = self.tracker.get_type_diversity_history(element_type.id, days=30)
            
            if len(history) < 5:
                suggestions.append(DiversitySuggestion(
                    parameter="tracking_data",
                    current_value=len(history),
                    suggested_value="More data needed",
                    rationale="Insufficient historical data for meaningful analysis",
                    impact_score=0.3,
                    implementation_difficulty="easy"
                ))
                return suggestions
            
            # Analyze metrics trends
            metric_performance = {}
            for record in history:
                if record.metric_name not in metric_performance:
                    metric_performance[record.metric_name] = []
                metric_performance[record.metric_name].append(record.metric_value)
            
            # Suggest improvements based on poor performance
            for metric_name, values in metric_performance.items():
                avg_value = sum(values) / len(values)
                
                if avg_value < 0.3:
                    suggestions.append(DiversitySuggestion(
                        parameter=f"{metric_name}_improvement",
                        current_value=avg_value,
                        suggested_value=0.5,
                        rationale=f"{metric_name} performance is low ({avg_value:.2f}), suggest configuration improvements",
                        impact_score=0.7,
                        implementation_difficulty="medium"
                    ))
                elif avg_value > 0.9:
                    suggestions.append(DiversitySuggestion(
                        parameter=f"{metric_name}_tuning",
                        current_value=avg_value,
                        suggested_value=0.8,
                        rationale=f"{metric_name} may be too high ({avg_value:.2f}), consider fine-tuning for better balance",
                        impact_score=0.4,
                        implementation_difficulty="easy"
                    ))
            
        except Exception as e:
            self.logger.warning(f"Historical performance analysis failed: {e}")
        
        return suggestions
    
    def _generate_llm_suggestions(self, element_type: ElementType, goal: OptimizationGoal) -> List[DiversitySuggestion]:
        """Generate LLM-powered suggestions for diversity improvement."""
        suggestions = []
        
        try:
            if not HAS_LLM:
                return suggestions
            
            # Create context for LLM
            context = {
                "element_type": {
                    "id": element_type.id,
                    "name": element_type.name,
                    "description": element_type.description,
                    "category": element_type.category,
                    "param_schema": element_type.param_schema
                },
                "diversity_config": element_type.diversity_config.dict() if element_type.diversity_config else None,
                "optimization_goal": goal.value
            }
            
            # This would normally call an LLM to generate suggestions
            # For now, we'll provide some intelligent rule-based suggestions
            
            # Analyze element type characteristics
            if "background" in element_type.category.lower():
                suggestions.append(DiversitySuggestion(
                    parameter="background_strategy",
                    current_value="default",
                    suggested_value="texture_variation",
                    rationale="Background elements benefit from texture and color variation strategies",
                    impact_score=0.6,
                    implementation_difficulty="medium"
                ))
            elif "glyph" in element_type.category.lower():
                suggestions.append(DiversitySuggestion(
                    parameter="glyph_complexity",
                    current_value="fixed",
                    suggested_value="adaptive",
                    rationale="Glyph elements should vary complexity based on visual impact",
                    impact_score=0.7,
                    implementation_difficulty="hard"
                ))
            elif "creature" in element_type.category.lower():
                suggestions.append(DiversitySuggestion(
                    parameter="creature_variation",
                    current_value="basic",
                    suggested_value="morphological",
                    rationale="Creature elements should vary form, posture, and characteristics",
                    impact_score=0.8,
                    implementation_difficulty="hard"
                ))
            
        except Exception as e:
            self.logger.warning(f"LLM suggestion generation failed: {e}")
        
        return suggestions
    
    def _apply_suggestion(self, element_type: ElementType, suggestion: DiversitySuggestion) -> bool:
        """Apply a single optimization suggestion."""
        try:
            if not HAS_TYPE_SYSTEM:
                return False
            
            if suggestion.parameter == "diversity_config":
                element_type.diversity_config = self._create_default_diversity_config(element_type).diversity_config
                return True
            
            elif suggestion.parameter == "strategy":
                # Update strategy
                if hasattr(VariationStrategy, suggestion.suggested_value.upper()):
                    new_strategy = getattr(VariationStrategy, suggestion.suggested_value.upper())
                    element_type.diversity_config.strategy = new_strategy
                    return True
            
            elif suggestion.parameter.startswith("jitter_amount"):
                if element_type.diversity_config.jitter:
                    element_type.diversity_config.jitter.jitter_amount = float(suggestion.suggested_value)
                    return True
            
            elif suggestion.parameter.startswith("affected_parameters"):
                if element_type.diversity_config.jitter:
                    if suggestion.suggested_value == "all":
                        element_type.diversity_config.jitter.affected_parameters = list(
                            element_type.get_default_params().keys()
                        )
                        return True
            
            elif suggestion.parameter.startswith("variation_strength"):
                if element_type.diversity_config.seeded:
                    element_type.diversity_config.seeded.variation_strength = float(suggestion.suggested_value)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to apply suggestion {suggestion.parameter}: {e}")
            return False
    
    def _predict_diversity_score(self, element_type: ElementType, goal: OptimizationGoal) -> float:
        """Predict diversity score for optimized configuration."""
        try:
            if not HAS_DIVERSITY_COMPONENTS:
                return 0.5  # Default prediction
            
            # Simple scoring based on configuration characteristics
            if not element_type.diversity_config:
                return 0.1
            
            score = 0.5  # Base score
            
            # Strategy bonus
            strategy_scores = {
                VariationStrategy.COMPOSITIONAL: 0.9,
                VariationStrategy.PARAMETER_SAMPLING: 0.8,
                VariationStrategy.STRATEGY_POOL: 0.7,
                VariationStrategy.SEEDED: 0.6,
                VariationStrategy.JITTER: 0.5
            }
            
            base_score = strategy_scores.get(element_type.diversity_config.strategy, 0.5)
            score = (score + base_score) / 2
            
            # Target diversity bonus
            target = element_type.diversity_config.diversity_target
            if target > 0.7:
                score += 0.2
            elif target < 0.3:
                score -= 0.2
            
            # Strategy-specific bonuses
            if element_type.diversity_config.jitter:
                if element_type.diversity_config.jitter.jitter_amount > 0.1:
                    score += 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception:
            return 0.5
    
    def _generate_final_recommendations(self, original_type: ElementType, optimized_type: ElementType, goal: OptimizationGoal) -> List[str]:
        """Generate final optimization recommendations."""
        recommendations = []
        
        try:
            # Configuration completeness check
            if not optimized_type.diversity_config:
                recommendations.append("Consider adding a diversity configuration to enable variation")
            elif optimized_type.diversity_config.strategy == VariationStrategy.JITTER:
                recommendations.append("Jitter strategy is good for basic variation; consider exploring compositional strategies for advanced diversity")
            elif optimized_type.diversity_config.strategy == VariationStrategy.COMPOSITIONAL:
                recommendations.append("Compositional strategy offers maximum flexibility - monitor performance and adjust as needed")
            
            # Parameter suggestions
            if len(optimized_type.variants) < 3:
                recommendations.append("Consider adding more variants to increase categorical diversity")
            
            # Performance monitoring
            recommendations.append("Monitor diversity metrics over time and adjust configuration based on results")
            
            # Integration suggestions
            if HAS_DIVERSITY_COMPONENTS:
                recommendations.append("Use diversity tracking and visualization to monitor optimization effectiveness")
            
        except Exception as e:
            self.logger.warning(f"Final recommendations generation failed: {e}")
            recommendations.append("Review optimization results and adjust configuration as needed")
        
        return recommendations
    
    def _determine_sampling_strategy(self, element_type: ElementType) -> str:
        """Determine best sampling strategy based on element type characteristics."""
        if not element_type.diversity_config:
            return "random"
        
        # Use configured sampling strategy if available
        if hasattr(element_type.diversity_config, 'sampling_strategy'):
            return element_type.diversity_config.sampling_strategy
        
        # Default strategy selection based on characteristics
        if "continuous" in str(element_type.param_schema):
            return "latin_hypercube"  # Good for continuous parameters
        elif len(element_type.variants) > 5:
            return "halton"  # Good for categorical combinations
        else:
            return "random"  # Simple fallback
    
    def _generate_random_samples(self, base_params: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Generate random diverse samples."""
        samples = []
        
        for i in range(count):
            sample = base_params.copy()
            
            # Add variation based on parameter types
            for param_name, value in sample.items():
                if isinstance(value, (int, float)):
                    # Add random variation (±10%)
                    variation = random.uniform(-0.1, 0.1)
                    if isinstance(value, int):
                        sample[param_name] = max(1, int(value * (1 + variation)))
                    else:
                        sample[param_name] = value * (1 + variation)
                elif isinstance(value, str) and value.startswith('#'):
                    # Vary color slightly
                    try:
                        hex_color = value.lstrip('#')
                        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                        
                        # Small random variations
                        r = max(0, min(255, r + random.randint(-10, 10)))
                        g = max(0, min(255, g + random.randint(-10, 10)))
                        b = max(0, min(255, b + random.randint(-10, 10)))
                        
                        sample[param_name] = f"#{r:02x}{g:02x}{b:02x}"
                    except (ValueError, IndexError):
                        pass
            
            # Add seed variation
            sample["seed"] = random.randint(1, 1000000)
            samples.append(sample)
        
        return samples
    
    def _generate_latin_hypercube_samples(self, base_params: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Generate Latin Hypercube samples for better coverage."""
        # Simplified Latin Hypercube implementation
        # In a full implementation, this would use specialized libraries
        
        samples = []
        numeric_params = [(name, value) for name, value in base_params.items() 
                         if isinstance(value, (int, float))]
        
        if not numeric_params:
            return self._generate_random_samples(base_params, count)
        
        for i in range(count):
            sample = base_params.copy()
            
            # Create Latin Hypercube sample points
            points = sorted([random.random() for _ in range(len(numeric_params))])
            
            for j, (param_name, base_value) in enumerate(numeric_params):
                if j < len(points):
                    # Map to parameter range (±20% for safety)
                    variation = (points[j] - 0.5) * 0.4  # ±20%
                    
                    if isinstance(base_value, int):
                        sample[param_name] = max(1, int(base_value * (1 + variation)))
                    else:
                        sample[param_name] = base_value * (1 + variation)
            
            sample["seed"] = random.randint(1, 1000000)
            samples.append(sample)
        
        return samples
    
    def _generate_sobol_samples(self, base_params: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Generate Sobol sequence samples."""
        # Simplified Sobol-like sequence (using simple deterministic sampling)
        # Full implementation would use specialized Sobol sequence generators
        
        return self._generate_latin_hypercube_samples(base_params, count)  # Fallback
    
    def _generate_halton_samples(self, base_params: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Generate Halton sequence samples."""
        # Simplified Halton sequence implementation
        # Full implementation would use specialized Halton sequence generators
        
        return self._generate_random_samples(base_params, count)  # Fallback
    
    def _analyze_diversity_configuration(self, element_type: ElementType) -> Dict[str, Any]:
        """Analyze diversity configuration and identify issues."""
        analysis = {
            "needs_optimization": False,
            "issues": [],
            "current_diversity_score": 0.0,
            "potential_improvement": 0.0
        }
        
        try:
            if not element_type.diversity_config:
                analysis["needs_optimization"] = True
                analysis["issues"].append("No diversity configuration")
                analysis["potential_improvement"] = 0.6
                return analysis
            
            config = element_type.diversity_config
            
            # Check strategy effectiveness
            if config.strategy == VariationStrategy.JITTER:
                if config.jitter and config.jitter.jitter_amount < 0.05:
                    analysis["issues"].append("Jitter amount too low for effective variation")
                    analysis["needs_optimization"] = True
            
            elif config.strategy == VariationStrategy.SEEDED:
                if config.seeded and config.seeded.variation_strength < 0.02:
                    analysis["issues"].append("Variation strength too low for seeded strategy")
                    analysis["needs_optimization"] = True
            
            # Check diversity target
            if config.diversity_target < 0.3:
                analysis["issues"].append("Diversity target too low")
                analysis["needs_optimization"] = True
            
            # Calculate current score (simplified)
            analysis["current_diversity_score"] = self._predict_diversity_score(element_type, OptimizationGoal.BALANCE_VARIETY)
            
            # Estimate potential improvement
            if analysis["needs_optimization"]:
                analysis["potential_improvement"] = min(0.4, 1.0 - analysis["current_diversity_score"])
            
        except Exception as e:
            self.logger.warning(f"Diversity configuration analysis failed: {e}")
            analysis["issues"].append(f"Analysis error: {str(e)}")
        
        return analysis
    
    def _generate_system_recommendations(self, element_types: List[ElementType]) -> List[str]:
        """Generate system-wide recommendations."""
        recommendations = []
        
        try:
            # Analyze overall configuration coverage
            types_with_diversity = sum(1 for et in element_types if et.diversity_config is not None)
            coverage = types_with_diversity / len(element_types) if element_types else 0
            
            if coverage < 0.5:
                recommendations.append(f"Only {coverage:.1%} of types have diversity configuration - consider enabling for all")
            elif coverage < 0.8:
                recommendations.append(f"Expand diversity configuration to more types (currently {coverage:.1%})")
            
            # Strategy distribution analysis
            strategy_counts = {}
            for et in element_types:
                if et.diversity_config:
                    strategy = et.diversity_config.strategy
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            # Recommend strategy diversification
            if VariationStrategy.JITTER in strategy_counts and strategy_counts[VariationStrategy.JITTER] > len(element_types) * 0.7:
                recommendations.append("Consider diversifying strategies beyond basic jitter for better variation")
            
            # Integration recommendations
            if HAS_DIVERSITY_COMPONENTS:
                recommendations.append("Enable diversity tracking and visualization for monitoring effectiveness")
            
        except Exception as e:
            self.logger.warning(f"System recommendations generation failed: {e}")
        
        return recommendations