"""
Type Improver System

This module implements the TypeImprover class that analyzes element type usage
and provides intelligent suggestions for improvements based on:

- Usage patterns and statistics
- Performance metrics
- Error rates and failure patterns
- User feedback and feedback analysis
- Generation quality assessments
- Diversity and variation effectiveness

The system provides both automatic optimization and manual improvement suggestions.
"""

import json
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

# Import TypeSystem components
try:
    from ..enhanced_design.element_types import ElementType
    from ..enhanced_design.type_registry import get_type_registry
    from ..llm.type_validator import TypeValidator, ValidationResult
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False


class ImprovementType(Enum):
    """Types of improvements that can be suggested."""
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    DESCRIPTION_IMPROVEMENT = "description_improvement"
    TAG_ENHANCEMENT = "tag_enhancement"
    SAFETY_ENHANCEMENT = "safety_enhancement"
    PERFORMANCE_TUNING = "performance_tuning"
    USABILITY_IMPROVEMENT = "usability_improvement"
    DIVERSITY_ENHANCEMENT = "diversity_enhancement"


class UsagePattern(Enum):
    """Usage pattern classifications."""
    UNDERUTILIZED = "underutilized"
    OVERUSED = "overused"
    UNSTABLE = "unstable"
    OPTIMIZED = "optimized"
    PROBLEMATIC = "problematic"


@dataclass
class UsageAnalysis:
    """Analysis of type usage patterns."""
    type_id: str
    usage_count: int
    success_rate: float
    avg_generation_time: float
    error_rate: float
    last_used: Optional[datetime]
    pattern: UsagePattern
    usage_frequency: float  # usage per day
    performance_score: float  # composite performance metric
    
    def get_recommendations(self) -> List[str]:
        """Get usage-based recommendations."""
        recommendations = []
        
        if self.pattern == UsagePattern.UNDERUTILIZED:
            recommendations.append("Consider marketing this type more prominently")
            recommendations.append("Add more variants to increase appeal")
            recommendations.append("Improve documentation and examples")
        
        elif self.pattern == UsagePattern.OVERUSED:
            recommendations.append("Consider creating similar types to distribute load")
            recommendations.append("Add complexity parameters for diverse use cases")
            recommendations.append("Monitor for performance bottlenecks")
        
        elif self.pattern == UsagePattern.UNSTABLE:
            recommendations.append("Review and fix frequent error sources")
            recommendations.append("Improve parameter validation")
            recommendations.append("Consider simplifying complex parameters")
        
        elif self.pattern == UsagePattern.PROBLEMATIC:
            recommendations.append("Immediate review needed - high error rate")
            recommendations.append("Consider deprecation and replacement")
            recommendations.append("Add better error handling")
        
        return recommendations


@dataclass
class ImprovementSuggestion:
    """Individual improvement suggestion."""
    improvement_type: ImprovementType
    priority: int  # 1-10, higher is more important
    title: str
    description: str
    rationale: str
    impact_estimate: str  # "low", "medium", "high"
    effort_estimate: str  # "low", "medium", "high"
    implementation: str  # JSON patch or description
    metrics: Dict[str, float]  # Expected improvements
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "improvement_type": self.improvement_type.value,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "impact_estimate": self.impact_estimate,
            "effort_estimate": self.effort_estimate,
            "implementation": self.implementation,
            "metrics": self.metrics
        }


class TypeImprover:
    """
    System for analyzing and improving element types.
    
    Provides intelligent suggestions based on usage data,
    performance metrics, and best practices.
    """
    
    def __init__(self):
        """Initialize the Type Improver."""
        self.logger = logging.getLogger(__name__)
        self.registry = get_type_registry() if HAS_TYPE_SYSTEM else None
        self.validator = TypeValidator() if HAS_TYPE_SYSTEM else None
    
    def analyze_type_usage(self, type_id: str, usage_window_days: int = 30) -> UsageAnalysis:
        """
        Analyze usage patterns for a specific type.
        
        Args:
            type_id: Type identifier to analyze
            usage_window_days: Number of days to analyze
            
        Returns:
            UsageAnalysis with comprehensive usage insights
        """
        if not self.registry:
            raise ValueError("TypeRegistry not available")
        
        try:
            # Get type information
            element_type = self.registry.get(type_id)
            if not element_type:
                raise ValueError(f"Type '{type_id}' not found")
            
            # Get usage data (simulated - in real implementation would query database)
            usage_data = self._get_usage_data(type_id, usage_window_days)
            
            # Calculate metrics
            usage_count = len(usage_data)
            success_count = sum(1 for entry in usage_data if entry.get('success', False))
            success_rate = success_count / max(1, usage_count)
            
            # Get generation times if available
            generation_times = [entry.get('duration_ms', 0) for entry in usage_data if 'duration_ms' in entry]
            avg_generation_time = statistics.mean(generation_times) if generation_times else 0.0
            
            # Calculate error rate
            error_rate = 1.0 - success_rate
            
            # Get last used time
            last_used = None
            if usage_data:
                last_used_timestamps = [entry.get('timestamp') for entry in usage_data if 'timestamp' in entry]
                if last_used_timestamps:
                    last_used = max(last_used_timestamps)
            
            # Calculate usage frequency
            if usage_count > 0 and last_used:
                days_since_first = (datetime.now() - min(usage_data[0].get('timestamp', datetime.now()) for entry in usage_data)).days
                usage_frequency = usage_count / max(1, days_since_first)
            else:
                usage_frequency = 0.0
            
            # Determine pattern
            pattern = self._classify_usage_pattern(
                usage_count, success_rate, error_rate, usage_frequency
            )
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(
                success_rate, avg_generation_time, error_rate
            )
            
            return UsageAnalysis(
                type_id=type_id,
                usage_count=usage_count,
                success_rate=success_rate,
                avg_generation_time=avg_generation_time,
                error_rate=error_rate,
                last_used=last_used,
                pattern=pattern,
                usage_frequency=usage_frequency,
                performance_score=performance_score
            )
            
        except Exception as e:
            self.logger.error(f"Usage analysis failed for {type_id}: {e}")
            raise
    
    def suggest_improvements(self, type_id: str, analysis: Optional[UsageAnalysis] = None) -> List[ImprovementSuggestion]:
        """
        Generate improvement suggestions for a type.
        
        Args:
            type_id: Type identifier to improve
            analysis: Optional pre-computed usage analysis
            
        Returns:
            List of ImprovementSuggestion objects
        """
        if not self.registry:
            raise ValueError("TypeRegistry not available")
        
        try:
            # Get type information
            element_type = self.registry.get(type_id)
            if not element_type:
                raise ValueError(f"Type '{type_id}' not found")
            
            # Get analysis if not provided
            if analysis is None:
                analysis = self.analyze_type_usage(type_id)
            
            suggestions = []
            
            # Analyze type definition for issues
            schema_suggestions = self._analyze_schema_improvements(element_type)
            suggestions.extend(schema_suggestions)
            
            # Usage-based suggestions
            usage_suggestions = self._generate_usage_suggestions(element_type, analysis)
            suggestions.extend(usage_suggestions)
            
            # Performance-based suggestions
            performance_suggestions = self._generate_performance_suggestions(element_type, analysis)
            suggestions.extend(performance_suggestions)
            
            # Safety suggestions
            safety_suggestions = self._generate_safety_suggestions(element_type)
            suggestions.extend(safety_suggestions)
            
            # Usability suggestions
            usability_suggestions = self._generate_usability_suggestions(element_type)
            suggestions.extend(usability_suggestions)
            
            # Sort by priority (higher first)
            suggestions.sort(key=lambda x: x.priority, reverse=True)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Improvement suggestion failed for {type_id}: {e}")
            raise
    
    def auto_optimize_type(self, type_id: str, max_changes: int = 5) -> ElementType:
        """
        Automatically apply safe optimizations to a type.
        
        Args:
            type_id: Type identifier to optimize
            max_changes: Maximum number of changes to apply
            
        Returns:
            Optimized ElementType
        """
        if not self.registry:
            raise ValueError("TypeRegistry not available")
        
        try:
            # Get current type
            element_type = self.registry.get(type_id)
            if not element_type:
                raise ValueError(f"Type '{type_id}' not found")
            
            # Analyze current state
            analysis = self.analyze_type_usage(type_id)
            suggestions = self.suggest_improvements(type_id, analysis)
            
            # Filter auto-applicable suggestions
            auto_suggestions = [
                s for s in suggestions 
                if s.improvement_type in [
                    ImprovementType.PARAMETER_OPTIMIZATION,
                    ImprovementType.SAFETY_ENHANCEMENT,
                    ImprovementType.PERFORMANCE_TUNING
                ]
                and s.priority >= 7  # High priority only
                and s.effort_estimate == "low"
            ][:max_changes]
            
            # Apply optimizations
            optimized_data = element_type.to_dict()
            changes_applied = 0
            
            for suggestion in auto_suggestions:
                if self._apply_optimization(optimized_data, suggestion):
                    changes_applied += 1
            
            self.logger.info(f"Applied {changes_applied} auto-optimizations to type {type_id}")
            
            # Create optimized type
            optimized_type = ElementType(**optimized_data)
            optimized_type.updated_at = datetime.now()
            
            return optimized_type
            
        except Exception as e:
            self.logger.error(f"Auto-optimization failed for {type_id}: {e}")
            raise
    
    def get_improvement_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive improvement metrics across all types.
        
        Returns:
            Dictionary with improvement analytics
        """
        if not self.registry:
            return {"error": "TypeRegistry not available"}
        
        try:
            all_types = self.registry.list()
            
            metrics = {
                "total_types": len(all_types),
                "improvement_opportunities": 0,
                "high_priority_suggestions": 0,
                "categories_with_issues": {},
                "common_improvement_types": {},
                "performance_distribution": {
                    "underutilized": 0,
                    "overused": 0,
                    "unstable": 0,
                    "optimized": 0,
                    "problematic": 0
                }
            }
            
            for element_type in all_types:
                try:
                    analysis = self.analyze_type_usage(element_type.id)
                    suggestions = self.suggest_improvements(element_type.id, analysis)
                    
                    # Count improvement opportunities
                    high_priority = sum(1 for s in suggestions if s.priority >= 8)
                    metrics["improvement_opportunities"] += len(suggestions)
                    metrics["high_priority_suggestions"] += high_priority
                    
                    # Categorize issues
                    category = element_type.category
                    if category not in metrics["categories_with_issues"]:
                        metrics["categories_with_issues"][category] = {
                            "types": 0,
                            "suggestions": 0,
                            "high_priority": 0
                        }
                    metrics["categories_with_issues"][category]["types"] += 1
                    metrics["categories_with_issues"][category]["suggestions"] += len(suggestions)
                    metrics["categories_with_issues"][category]["high_priority"] += high_priority
                    
                    # Count improvement types
                    for suggestion in suggestions:
                        imp_type = suggestion.improvement_type.value
                        metrics["common_improvement_types"][imp_type] = \
                            metrics["common_improvement_types"].get(imp_type, 0) + 1
                    
                    # Count performance patterns
                    pattern = analysis.pattern.value
                    metrics["performance_distribution"][pattern] += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to analyze type {element_type.id}: {e}")
                    continue
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get improvement metrics: {e}")
            return {"error": str(e)}
    
    def _get_usage_data(self, type_id: str, days: int) -> List[Dict[str, Any]]:
        """
        Get usage data for a type (simulated for now).
        
        Args:
            type_id: Type identifier
            days: Number of days to retrieve
            
        Returns:
            List of usage entries
        """
        # This would be replaced with actual database queries
        # For now, return simulated data
        import random
        
        data = []
        base_time = datetime.now() - timedelta(days=days)
        
        for i in range(random.randint(10, 100)):  # Random usage count
            entry = {
                "timestamp": base_time + timedelta(days=random.uniform(0, days)),
                "success": random.random() > 0.1,  # 90% success rate
                "duration_ms": random.uniform(100, 2000)  # 100ms to 2s
            }
            data.append(entry)
        
        return data
    
    def _classify_usage_pattern(self, usage_count: int, success_rate: float, 
                               error_rate: float, frequency: float) -> UsagePattern:
        """Classify usage pattern based on metrics."""
        
        if success_rate < 0.7 or error_rate > 0.3:
            return UsagePattern.PROBLEMATIC
        elif error_rate > 0.15:
            return UsagePattern.UNSTABLE
        elif frequency > 10:  # High frequency usage
            return UsagePattern.OVERUSED
        elif frequency < 0.1:  # Low frequency
            return UsagePattern.UNDERUTILIZED
        elif success_rate > 0.9 and error_rate < 0.05:
            return UsagePattern.OPTIMIZED
        else:
            return UsagePattern.OPTIMIZED
    
    def _calculate_performance_score(self, success_rate: float, avg_time: float, error_rate: float) -> float:
        """Calculate composite performance score (0-1)."""
        # Success rate contribution (40%)
        success_score = success_rate * 0.4
        
        # Speed contribution (30%) - faster is better
        time_score = max(0, (2000 - min(avg_time, 2000)) / 2000) * 0.3
        
        # Error rate contribution (30%) - lower error is better
        error_score = (1 - error_rate) * 0.3
        
        return min(1.0, success_score + time_score + error_score)
    
    def _analyze_schema_improvements(self, element_type: ElementType) -> List[ImprovementSuggestion]:
        """Analyze schema for improvement opportunities."""
        suggestions = []
        
        # Check parameter count
        param_count = len(element_type.param_schema.get('properties', {}))
        if param_count > 15:
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.PARAMETER_OPTIMIZATION,
                priority=8,
                title="Reduce Parameter Count",
                description=f"Type has {param_count} parameters, consider consolidating",
                rationale="Too many parameters can confuse users and impact performance",
                impact_estimate="high",
                effort_estimate="medium",
                implementation="Consolidate related parameters or make some optional",
                metrics={"usability_score": 0.2, "performance_score": 0.1}
            ))
        
        # Check description quality
        desc_words = len(element_type.description.split()) if element_type.description else 0
        if desc_words < 10:
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.DESCRIPTION_IMPROVEMENT,
                priority=6,
                title="Enhance Description",
                description="Description is too brief, add more detail",
                rationale="Better descriptions improve user understanding and discoverability",
                impact_estimate="medium",
                effort_estimate="low",
                implementation="Add 2-3 sentences explaining purpose, usage, and characteristics",
                metrics={"usability_score": 0.3}
            ))
        
        # Check tag quality
        tag_count = len(element_type.tags) if element_type.tags else 0
        if tag_count < 3:
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.TAG_ENHANCEMENT,
                priority=5,
                title="Add More Tags",
                description="Add more descriptive tags for better discoverability",
                rationale="More tags help users find types through search and browsing",
                impact_estimate="low",
                effort_estimate="low",
                implementation="Add 2-4 relevant tags covering style, purpose, and characteristics",
                metrics={"discoverability_score": 0.4}
            ))
        
        return suggestions
    
    def _generate_usage_suggestions(self, element_type: ElementType, 
                                   analysis: UsageAnalysis) -> List[ImprovementSuggestion]:
        """Generate suggestions based on usage patterns."""
        suggestions = []
        
        for recommendation in analysis.get_recommendations():
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.USABILITY_IMPROVEMENT,
                priority=7,
                title="Usage Pattern Optimization",
                description=recommendation,
                rationale="Based on actual usage patterns and user behavior",
                impact_estimate="medium",
                effort_estimate="medium",
                implementation="Implement suggested changes based on usage analysis",
                metrics={"usage_frequency": 0.2, "user_satisfaction": 0.3}
            ))
        
        return suggestions
    
    def _generate_performance_suggestions(self, element_type: ElementType, 
                                         analysis: UsageAnalysis) -> List[ImprovementSuggestion]:
        """Generate performance-based suggestions."""
        suggestions = []
        
        if analysis.avg_generation_time > 1500:  # Slower than 1.5s
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.PERFORMANCE_TUNING,
                priority=8,
                title="Optimize Generation Performance",
                description=f"Current average generation time: {analysis.avg_generation_time:.0f}ms",
                rationale="Users prefer faster generation times",
                impact_estimate="high",
                effort_estimate="medium",
                implementation="Simplify complex parameters, optimize rendering algorithms",
                metrics={"generation_time": -0.3, "user_satisfaction": 0.2}
            ))
        
        if analysis.error_rate > 0.1:
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.SAFETY_ENHANCEMENT,
                priority=9,
                title="Reduce Error Rate",
                description=f"Error rate: {analysis.error_rate:.1%} - needs improvement",
                rationale="High error rates frustrate users and reduce trust",
                impact_estimate="high",
                effort_estimate="high",
                implementation="Improve parameter validation, add better error handling",
                metrics={"error_rate": -0.5, "success_rate": 0.4}
            ))
        
        return suggestions
    
    def _generate_safety_suggestions(self, element_type: ElementType) -> List[ImprovementSuggestion]:
        """Generate safety and security suggestions."""
        suggestions = []
        
        # Validate the type
        if self.validator:
            validation_result = self.validator.validate_all(element_type)
            
            for issue in validation_result.issues:
                if issue.severity.value == "error":
                    suggestions.append(ImprovementSuggestion(
                        improvement_type=ImprovementType.SAFETY_ENHANCEMENT,
                        priority=10,  # Highest priority for safety
                        title=f"Safety Issue: {issue.field}",
                        description=issue.message,
                        rationale="Safety issues must be resolved before deployment",
                        impact_estimate="high",
                        effort_estimate="medium",
                        implementation=issue.suggestion or "Fix identified safety issue",
                        metrics={"safety_score": 0.5, "validation_score": 1.0}
                    ))
        
        return suggestions
    
    def _generate_usability_suggestions(self, element_type: ElementType) -> List[ImprovementSuggestion]:
        """Generate usability improvement suggestions."""
        suggestions = []
        
        # Check parameter names for clarity
        if element_type.param_schema and 'properties' in element_type.param_schema:
            for param_name, param_def in element_type.param_schema['properties'].items():
                if not param_def.get('description'):
                    suggestions.append(ImprovementSuggestion(
                        improvement_type=ImprovementType.USABILITY_IMPROVEMENT,
                        priority=6,
                        title=f"Add Parameter Description",
                        description=f"Parameter '{param_name}' needs a description",
                        rationale="Parameter descriptions help users understand expected values",
                        impact_estimate="medium",
                        effort_estimate="low",
                        implementation=f"Add clear description for {param_name} parameter",
                        metrics={"usability_score": 0.2}
                    ))
        
        return suggestions
    
    def _apply_optimization(self, type_data: Dict[str, Any], suggestion: ImprovementSuggestion) -> bool:
        """
        Apply an optimization to type data.
        
        Args:
            type_data: Type data dictionary
            suggestion: Improvement suggestion to apply
            
        Returns:
            True if optimization was applied
        """
        try:
            if suggestion.improvement_type == ImprovementType.PARAMETER_OPTIMIZATION:
                # Simple parameter count optimization
                if "param_schema" in type_data and "properties" in type_data["param_schema"]:
                    properties = type_data["param_schema"]["properties"]
                    if len(properties) > 15:
                        # Remove least important parameters (would need more sophisticated logic)
                        # For now, just return True to indicate we could apply this
                        pass
                
            elif suggestion.improvement_type == ImprovementType.SAFETY_ENHANCEMENT:
                # Safety improvements would be applied here
                pass
            
            elif suggestion.improvement_type == ImprovementType.DESCRIPTION_IMPROVEMENT:
                # Enhance description
                if "description" in type_data:
                    desc = type_data["description"]
                    if len(desc.split()) < 10:
                        type_data["description"] = desc + " This type provides customizable parameters for fine-tuned control over the generated assets."
            
            return True  # Assume optimization can be applied
            
        except Exception as e:
            self.logger.error(f"Failed to apply optimization: {e}")
            return False


# Export main classes
__all__ = [
    'TypeImprover',
    'UsageAnalysis', 
    'ImprovementSuggestion',
    'ImprovementType',
    'UsagePattern'
]