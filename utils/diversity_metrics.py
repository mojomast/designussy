"""
Diversity Metrics Module

This module implements comprehensive diversity analysis and statistical measures
for parameter sets and generated assets in the NanoBanana system.

Key Features:
- Statistical diversity measures (entropy, coefficient of variation)
- Parameter distance calculations and clustering
- Diversity visualization utilities
- Comprehensive diversity reporting
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from enum import Enum

# Optional imports with fallbacks
try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️ scikit-learn not available - clustering analysis will be limited")

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib not available - visualization will be limited to text")


class DiversityMetric(Enum):
    """Types of diversity metrics available."""
    ENTROPY = "entropy"
    COEFFICIENT_OF_VARIATION = "coefficient_of_variation"
    PAIRWISE_DISTANCE = "pairwise_distance"
    SHANNON_DIVERSITY = "shannon_diversity"
    SIMPSON_DIVERSITY = "simpson_diversity"
    GINI_SIMPSON = "gini_simpson"


@dataclass
class DiversityReport:
    """Comprehensive diversity analysis report."""
    timestamp: datetime
    sample_count: int
    metric_scores: Dict[str, float]
    cluster_analysis: Optional[Dict[str, Any]] = None
    parameter_coverage: Optional[Dict[str, float]] = None
    recommendations: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "sample_count": self.sample_count,
            "metric_scores": self.metric_scores,
            "cluster_analysis": self.cluster_analysis,
            "parameter_coverage": self.parameter_coverage,
            "recommendations": self.recommendations or []
        }


class DiversityAnalyzer:
    """Main diversity analysis engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_parameter_diversity(self, params_list: List[Dict[str, Any]]) -> float:
        """
        Calculate diversity score for a list of parameter sets.
        
        Uses Shannon entropy and coefficient of variation to measure diversity.
        
        Args:
            params_list: List of parameter dictionaries
            
        Returns:
            Diversity score between 0-1 (higher = more diverse)
        """
        if len(params_list) < 2:
            return 0.0
            
        try:
            # Extract numeric parameters for analysis
            numeric_params = self._extract_numeric_parameters(params_list)
            
            if not numeric_params:
                return 0.0
                
            # Calculate diversity components
            entropy_score = self._calculate_shannon_entropy(numeric_params)
            cv_score = self._calculate_coefficient_of_variation(numeric_params)
            
            # Combine scores with weights
            diversity_score = (entropy_score * 0.6) + (cv_score * 0.4)
            
            return min(1.0, max(0.0, diversity_score))
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate parameter diversity: {e}")
            return 0.0
    
    def calculate_output_diversity(self, assets_data: List[Dict[str, Any]]) -> float:
        """
        Analyze diversity of output assets based on their characteristics.
        
        Args:
            assets_data: List of asset metadata dictionaries
            
        Returns:
            Output diversity score between 0-1
        """
        if len(assets_data) < 2:
            return 0.0
            
        try:
            # Extract diversity indicators from assets
            characteristics = self._extract_asset_characteristics(assets_data)
            
            # Calculate diversity across different characteristics
            diversity_scores = []
            
            # Color diversity
            if 'colors' in characteristics:
                color_diversity = self._calculate_color_diversity(characteristics['colors'])
                diversity_scores.append(color_diversity)
            
            # Size diversity  
            if 'sizes' in characteristics:
                size_diversity = self._calculate_coefficient_of_variation(characteristics['sizes'])
                diversity_scores.append(size_diversity)
            
            # Complexity diversity
            if 'complexity' in characteristics:
                complexity_diversity = self._calculate_shannon_entropy([characteristics['complexity']])
                diversity_scores.append(complexity_diversity)
            
            # Overall diversity as average of component scores
            if diversity_scores:
                return sum(diversity_scores) / len(diversity_scores)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.warning(f"Failed to calculate output diversity: {e}")
            return 0.0
    
    def analyze_variation_coverage(self, element_type: str, samples: int = 100) -> DiversityReport:
        """
        Test how well variations cover the parameter space.
        
        Args:
            element_type: Type of element to analyze
            samples: Number of samples to generate for analysis
            
        Returns:
            DiversityReport with coverage analysis
        """
        try:
            # Generate sample parameter sets
            sample_params = self._generate_parameter_samples(element_type, samples)
            
            if not sample_params:
                return DiversityReport(
                    timestamp=datetime.utcnow(),
                    sample_count=0,
                    metric_scores={"coverage": 0.0},
                    recommendations=["Unable to generate parameter samples"]
                )
            
            # Calculate basic metrics
            param_diversity = self.calculate_parameter_diversity(sample_params)
            
            # Analyze parameter coverage
            coverage_analysis = self._analyze_parameter_coverage(sample_params)
            
            # Generate recommendations
            recommendations = self._generate_coverage_recommendations(param_diversity, coverage_analysis)
            
            return DiversityReport(
                timestamp=datetime.utcnow(),
                sample_count=len(sample_params),
                metric_scores={
                    "parameter_diversity": param_diversity,
                    "coverage_score": coverage_analysis.get("overall_coverage", 0.0)
                },
                parameter_coverage=coverage_analysis,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {e}")
            return DiversityReport(
                timestamp=datetime.utcnow(),
                sample_count=0,
                metric_scores={"error": str(e)},
                recommendations=["Coverage analysis failed - check logs"]
            )
    
    def cluster_analysis(self, params_list: List[Dict[str, Any]], n_clusters: int = 5) -> Dict[str, Any]:
        """
        Perform clustering analysis on parameter sets.
        
        Args:
            params_list: List of parameter dictionaries
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary with clustering results
        """
        if len(params_list) < 2:
            return {"error": "Insufficient samples for clustering"}
        
        if not HAS_SKLEARN:
            # Fallback clustering using simple grouping
            return self._simple_clustering(params_list, n_clusters)
        
        try:
            # Extract numeric features
            numeric_data = self._extract_numeric_parameters(params_list)
            if not numeric_data:
                return {"error": "No numeric parameters found"}
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(numeric_data)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(params_list)), random_state=42)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Calculate silhouette score
            if len(set(cluster_labels)) > 1:
                sil_score = silhouette_score(features_scaled, cluster_labels)
            else:
                sil_score = 0.0
            
            # Analyze clusters
            cluster_analysis = {
                "n_clusters": len(set(cluster_labels)),
                "cluster_labels": cluster_labels.tolist(),
                "silhouette_score": float(sil_score),
                "cluster_centers": kmeans.cluster_centers_.tolist(),
                "cluster_sizes": defaultdict(int)
            }
            
            # Count samples per cluster
            for label in cluster_labels:
                cluster_analysis["cluster_sizes"][int(label)] += 1
            
            # Convert cluster sizes to regular dict
            cluster_analysis["cluster_sizes"] = dict(cluster_analysis["cluster_sizes"])
            
            return cluster_analysis
            
        except Exception as e:
            self.logger.error(f"Clustering analysis failed: {e}")
            return {"error": f"Clustering failed: {str(e)}"}
    
    def pairwise_distance_matrix(self, params_list: List[Dict[str, Any]]) -> np.ndarray:
        """
        Calculate pairwise distance matrix between parameter sets.
        
        Args:
            params_list: List of parameter dictionaries
            
        Returns:
            Numpy array of pairwise distances
        """
        if len(params_list) < 2:
            return np.array([])
        
        try:
            # Extract numeric features
            numeric_data = self._extract_numeric_parameters(params_list)
            if not numeric_data:
                return np.array([])
            
            n_samples = len(numeric_data)
            distance_matrix = np.zeros((n_samples, n_samples))
            
            # Calculate Euclidean distances
            for i in range(n_samples):
                for j in range(i + 1, n_samples):
                    # Normalize features for fair comparison
                    diff = np.array(numeric_data[i]) - np.array(numeric_data[j])
                    distance = np.sqrt(np.sum(diff ** 2))
                    distance_matrix[i][j] = distance
                    distance_matrix[j][i] = distance
            
            return distance_matrix
            
        except Exception as e:
            self.logger.error(f"Distance matrix calculation failed: {e}")
            return np.array([])


# Utility functions and helpers

def entropy_score(values: List[float]) -> float:
    """
    Calculate Shannon entropy for a list of values.
    
    Args:
        values: List of numerical values
        
    Returns:
        Entropy score (0 = no diversity, 1 = maximum diversity)
    """
    if not values or len(values) < 2:
        return 0.0
    
    try:
        # Create bins and calculate frequencies
        hist, _ = np.histogram(values, bins=min(10, len(values)))
        probabilities = hist / len(values)
        
        # Remove zero probabilities
        probabilities = probabilities[probabilities > 0]
        
        # Calculate entropy
        entropy = -sum(p * np.log2(p) for p in probabilities)
        
        # Normalize by maximum possible entropy
        max_entropy = np.log2(len(probabilities))
        return entropy / max_entropy if max_entropy > 0 else 0.0
        
    except Exception:
        return 0.0


def coefficient_of_variation(values: List[float]) -> float:
    """
    Calculate coefficient of variation for a list of values.
    
    Args:
        values: List of numerical values
        
    Returns:
        Coefficient of variation (0 = no variation, higher = more variation)
    """
    if not values or len(values) < 2:
        return 0.0
    
    try:
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if mean_val == 0:
            return 0.0
        
        # Normalize coefficient of variation to 0-1 range
        cv = std_val / mean_val
        return min(1.0, cv)
        
    except Exception:
        return 0.0


def pairwise_distance_matrix(params_list: List[Dict[str, Any]]) -> np.ndarray:
    """
    Calculate pairwise distance matrix between parameter sets.
    
    Args:
        params_list: List of parameter dictionaries
        
    Returns:
        Numpy array of pairwise distances
    """
    analyzer = DiversityAnalyzer()
    return analyzer.pairwise_distance_matrix(params_list)


def cluster_analysis(params_list: List[Dict[str, Any]], n_clusters: int = 5) -> Dict[str, Any]:
    """
    Perform K-means clustering analysis on parameter sets.
    
    Args:
        params_list: List of parameter dictionaries
        n_clusters: Number of clusters to create
        
    Returns:
        Dictionary with clustering results
    """
    analyzer = DiversityAnalyzer()
    return analyzer.cluster_analysis(params_list, n_clusters)


# Private helper methods for DiversityAnalyzer

def _extract_numeric_parameters(self, params_list: List[Dict[str, Any]]) -> List[List[float]]:
    """Extract numeric parameters from parameter dictionaries."""
    numeric_params = []
    
    for params in params_list:
        numeric_values = []
        for key, value in params.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                numeric_values.append(float(value))
            elif isinstance(value, str) and value.startswith('#'):
                # Extract RGB values from hex colors
                try:
                    hex_color = value.lstrip('#')
                    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                    numeric_values.extend([r/255.0, g/255.0, b/255.0])
                except (ValueError, IndexError):
                    pass
        
        if numeric_values:
            numeric_params.append(numeric_values)
    
    return numeric_params


def _calculate_shannon_entropy(self, numeric_data: List[List[float]]) -> float:
    """Calculate Shannon entropy across numeric parameters."""
    if not numeric_data:
        return 0.0
    
    try:
        # Combine all numeric values
        all_values = []
        for params in numeric_data:
            all_values.extend(params)
        
        return entropy_score(all_values)
        
    except Exception:
        return 0.0


def _calculate_coefficient_of_variation(self, numeric_data: List[List[float]]) -> float:
    """Calculate coefficient of variation across numeric parameters."""
    if not numeric_data:
        return 0.0
    
    try:
        # Combine all numeric values
        all_values = []
        for params in numeric_data:
            all_values.extend(params)
        
        return coefficient_of_variation(all_values)
        
    except Exception:
        return 0.0


def _extract_asset_characteristics(self, assets_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Extract diversity-relevant characteristics from assets."""
    characteristics = {
        "colors": [],
        "sizes": [],
        "complexity": []
    }
    
    for asset in assets_data:
        # Extract color information
        if "base_color" in asset and asset["base_color"]:
            try:
                color = asset["base_color"]
                if isinstance(color, str) and color.startswith('#'):
                    hex_color = color.lstrip('#')
                    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                    # Use RGB as color characteristics
                    characteristics["colors"].extend([r/255.0, g/255.0, b/255.0])
            except (ValueError, IndexError):
                pass
        
        # Extract size information
        if "width" in asset and "height" in asset:
            try:
                width = float(asset["width"])
                height = float(asset["height"])
                characteristics["sizes"].append(width * height)  # Area as size metric
            except (ValueError, TypeError):
                pass
        
        # Extract complexity information
        if "complexity" in asset:
            try:
                complexity = float(asset["complexity"])
                characteristics["complexity"].append(complexity)
            except (ValueError, TypeError):
                pass
    
    return characteristics


def _calculate_color_diversity(self, colors: List[float]) -> float:
    """Calculate diversity in color values."""
    if len(colors) < 3:  # Need at least one RGB triplet
        return 0.0
    
    try:
        # Group colors into triplets (RGB)
        color_triplets = [colors[i:i+3] for i in range(0, len(colors), 3)]
        if not color_triplets:
            return 0.0
        
        # Calculate color distance diversity
        diversity_scores = []
        for i, color1 in enumerate(color_triplets):
            for j, color2 in enumerate(color_triplets[i+1:], i+1):
                # Euclidean distance in RGB space
                distance = sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5
                diversity_scores.append(distance)
        
        if diversity_scores:
            avg_distance = sum(diversity_scores) / len(diversity_scores)
            # Normalize by maximum possible RGB distance (sqrt(3) ≈ 1.732)
            return min(1.0, avg_distance / 1.732)
        else:
            return 0.0
            
    except Exception:
        return 0.0


def _analyze_parameter_coverage(self, params_list: List[Dict[str, Any]]) -> Dict[str, float]:
    """Analyze how well parameters cover their valid ranges."""
    coverage_analysis = {}
    
    try:
        # Collect all parameters
        all_keys = set()
        for params in params_list:
            all_keys.update(params.keys())
        
        for key in all_keys:
            values = []
            for params in params_list:
                if key in params and isinstance(params[key], (int, float)):
                    values.append(params[key])
            
            if len(values) > 1:
                # Calculate coverage as range / (max - min)
                min_val = min(values)
                max_val = max(values)
                if max_val > min_val:
                    # Estimate theoretical range based on parameter type
                    theoretical_range = self._estimate_parameter_range(key, min_val, max_val)
                    coverage = min(1.0, (max_val - min_val) / theoretical_range)
                else:
                    coverage = 0.0
            else:
                coverage = 0.0
            
            coverage_analysis[f"{key}_coverage"] = coverage
        
        # Calculate overall coverage
        if coverage_analysis:
            overall_coverage = sum(coverage_analysis.values()) / len(coverage_analysis)
            coverage_analysis["overall_coverage"] = overall_coverage
        
        return coverage_analysis
        
    except Exception as e:
        self.logger.warning(f"Coverage analysis failed: {e}")
        return {"error": str(e)}


def _estimate_parameter_range(self, param_name: str, min_val: float, max_val: float) -> float:
    """Estimate the theoretical range for a parameter."""
    # Common parameter range estimates
    range_estimates = {
        "width": 2048,
        "height": 2048,
        "complexity": 10.0,
        "chaos": 1.0,
        "jitter_amount": 1.0,
        "randomness": 1.0,
        "seed": 1000000
    }
    
    # Use specific estimates or default based on value type
    if param_name in range_estimates:
        return range_estimates[param_name]
    elif min_val >= 0 and max_val <= 1:
        return 1.0  # Parameters in [0,1] range
    elif "color" in param_name.lower():
        return 255.0  # RGB color values
    else:
        # Fallback: use current range * 2 as estimate
        return max_val * 2 if max_val > 0 else 1.0


def _generate_coverage_recommendations(self, diversity_score: float, coverage: Dict[str, float]) -> List[str]:
    """Generate recommendations based on diversity analysis."""
    recommendations = []
    
    if diversity_score < 0.5:
        recommendations.append("Low diversity detected - consider increasing parameter ranges")
    
    if coverage.get("overall_coverage", 0) < 0.3:
        recommendations.append("Poor parameter coverage - widen parameter bounds")
    
    # Check specific parameter coverage
    for param, cov_score in coverage.items():
        if param.endswith("_coverage") and cov_score < 0.2:
            param_name = param[:-9]  # Remove "_coverage" suffix
            recommendations.append(f"Low coverage for {param_name} - consider expanding range")
    
    if not recommendations:
        recommendations.append("Good diversity and coverage detected")
    
    return recommendations


def _generate_parameter_samples(self, element_type: str, count: int) -> List[Dict[str, Any]]:
    """Generate sample parameter sets for analysis."""
    # This is a placeholder - in a real implementation, this would
    # generate diverse parameter samples based on element type schema
    try:
        # Simple random sampling approach
        import random
        random.seed(42)  # For reproducible results
        
        samples = []
        for i in range(count):
            sample = {
                "width": random.randint(128, 1024),
                "height": random.randint(128, 1024),
                "complexity": random.uniform(0.1, 1.0),
                "seed": random.randint(1, 10000)
            }
            samples.append(sample)
        
        return samples
        
    except Exception as e:
        self.logger.error(f"Parameter sampling failed: {e}")
        return []


def _simple_clustering(self, params_list: List[Dict[str, Any]], n_clusters: int) -> Dict[str, Any]:
    """Fallback clustering using simple grouping."""
    try:
        # Extract first numeric parameter for simple clustering
        numeric_data = self._extract_numeric_parameters(params_list)
        if not numeric_data:
            return {"error": "No numeric parameters for clustering"}
        
        # Simple clustering by first parameter value
        first_param_values = [params[0] for params in numeric_data]
        
        # Create clusters based on value ranges
        min_val = min(first_param_values)
        max_val = max(first_param_values)
        range_size = (max_val - min_val) / n_clusters
        
        cluster_labels = []
        for value in first_param_values:
            cluster_idx = min(int((value - min_val) / range_size), n_clusters - 1)
            cluster_labels.append(cluster_idx)
        
        # Calculate cluster sizes
        cluster_sizes = defaultdict(int)
        for label in cluster_labels:
            cluster_sizes[label] += 1
        
        return {
            "n_clusters": n_clusters,
            "cluster_labels": cluster_labels,
            "cluster_sizes": dict(cluster_sizes),
            "method": "simple_grouping",
            "note": "Using simple clustering due to missing scikit-learn"
        }
        
    except Exception as e:
        return {"error": f"Simple clustering failed: {str(e)}"}


# Bind private methods to the class
DiversityAnalyzer._extract_numeric_parameters = _extract_numeric_parameters
DiversityAnalyzer._calculate_shannon_entropy = _calculate_shannon_entropy
DiversityAnalyzer._calculate_coefficient_of_variation = _calculate_coefficient_of_variation
DiversityAnalyzer._extract_asset_characteristics = _extract_asset_characteristics
DiversityAnalyzer._calculate_color_diversity = _calculate_color_diversity
DiversityAnalyzer._analyze_parameter_coverage = _analyze_parameter_coverage
DiversityAnalyzer._estimate_parameter_range = _estimate_parameter_range
DiversityAnalyzer._generate_coverage_recommendations = _generate_coverage_recommendations
DiversityAnalyzer._generate_parameter_samples = _generate_parameter_samples
DiversityAnalyzer._simple_clustering = _simple_clustering

# Add missing methods to DiversityAnalyzer
def entropy_score_method(self, values: List[float]) -> float:
    """Calculate entropy for a list of values."""
    return entropy_score(values)

def get_entropy_breakdown_method(self, params_list: List[Dict[str, Any]]) -> Dict[str, float]:
    """Get entropy breakdown for parameter sets."""
    try:
        numeric_data = self._extract_numeric_parameters(params_list)
        if not numeric_data:
            return {}
        
        all_values = []
        for params in numeric_data:
            all_values.extend(params)
        
        return {
            "overall_entropy": self.entropy_score(all_values),
            "parameter_count": len(all_values),
            "sample_count": len(params_list)
        }
    except Exception as e:
        self.logger.warning(f"Entropy breakdown failed: {e}")
        return {}

def analyze_parameter_coverage_method(self, params_list: List[Dict[str, Any]]) -> Dict[str, float]:
    """Analyze parameter coverage for parameter sets."""
    try:
        coverage = {}
        
        # Collect all parameters
        all_keys = set()
        for params in params_list:
            all_keys.update(params.keys())
        
        for key in all_keys:
            values = []
            for params in params_list:
                if key in params and isinstance(params[key], (int, float)):
                    values.append(params[key])
            
            if len(values) > 1:
                min_val = min(values)
                max_val = max(values)
                if max_val > min_val:
                    theoretical_range = self._estimate_parameter_range(key, min_val, max_val)
                    coverage[f"{key}_coverage"] = min(1.0, (max_val - min_val) / theoretical_range)
                else:
                    coverage[f"{key}_coverage"] = 0.0
            else:
                coverage[f"{key}_coverage"] = 0.0
        
        if coverage:
            coverage["overall_coverage"] = sum(coverage.values()) / len(coverage)
        
        return coverage
    except Exception as e:
        self.logger.warning(f"Parameter coverage analysis failed: {e}")
        return {}

def get_improvement_recommendations_method(self, params_list: List[Dict[str, Any]], target_score: float = 0.8) -> List[str]:
    """Get improvement recommendations for parameter sets."""
    recommendations = []
    
    try:
        current_score = self.calculate_parameter_diversity(params_list)
        
        if current_score < target_score:
            recommendations.append("Low diversity detected - consider expanding parameter ranges")
        
        coverage = self.analyze_parameter_coverage(params_list)
        if coverage.get("overall_coverage", 0) < 0.3:
            recommendations.append("Poor parameter coverage - widen parameter bounds")
        
        # Check specific parameter coverage
        for param, cov_score in coverage.items():
            if param.endswith("_coverage") and cov_score < 0.2:
                param_name = param[:-9]  # Remove "_coverage" suffix
                recommendations.append(f"Low coverage for {param_name} - consider expanding range")
        
        if not recommendations:
            recommendations.append("Good diversity and coverage detected")
        
    except Exception as e:
        self.logger.warning(f"Recommendation generation failed: {e}")
        recommendations.append("Unable to generate recommendations due to system error")
    
    return recommendations

# Bind the methods
DiversityAnalyzer.entropy_score = entropy_score_method
DiversityAnalyzer.get_entropy_breakdown = get_entropy_breakdown_method
DiversityAnalyzer.analyze_parameter_coverage = analyze_parameter_coverage_method
DiversityAnalyzer.get_improvement_recommendations = get_improvement_recommendations_method

# Create DiversityMetrics alias for backward compatibility
DiversityMetrics = DiversityAnalyzer