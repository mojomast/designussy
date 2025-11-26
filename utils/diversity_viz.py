"""
Diversity Visualization Module

This module provides comprehensive visualization utilities for diversity metrics
and analytics in the NanoBanana generation system.

Features:
- Parameter distribution plots
- Diversity timeline visualizations
- Comprehensive dashboard data generation
- Text-based reports as matplotlib fallback
- Base64 encoded images for web display
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import base64
import io
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# Optional imports with fallbacks
try:
    import matplotlib.pyplot as plt
    import matplotlib
    import numpy as np
    matplotlib.use('Agg')  # Use non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib not available - using text-based visualizations")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️ pandas not available - using basic data processing")

# Import diversity components
try:
    from storage.diversity_tracker import DiversityTracker, DiversityTrend
    from utils.diversity_metrics import DiversityReport, DiversityAnalyzer
    HAS_DIVERSITY_COMPONENTS = True
except ImportError:
    HAS_DIVERSITY_COMPONENTS = False
    print("⚠️ Diversity components not available")


class DiversityVisualizer:
    """
    Main diversity visualization engine.
    
    Provides comprehensive visualization capabilities with fallbacks
    for environments without matplotlib.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize diversity components if available
        if HAS_DIVERSITY_COMPONENTS:
            self.tracker = DiversityTracker()
            self.analyzer = DiversityAnalyzer()
        else:
            self.tracker = None
            self.analyzer = None
    
    def plot_parameter_distribution(self, params_list: List[Dict[str, Any]]) -> str:
        """
        Generate distribution plot for parameter sets.
        
        Args:
            params_list: List of parameter dictionaries
            
        Returns:
            Base64 encoded PNG image or text report
        """
        if not params_list:
            return self._generate_text_report("No parameter data provided")
        
        try:
            if HAS_MATPLOTLIB:
                return self._create_matplotlib_distribution_plot(params_list)
            else:
                return self._create_text_distribution_report(params_list)
                
        except Exception as e:
            self.logger.error(f"Distribution plot generation failed: {e}")
            return self._generate_text_report(f"Plot generation failed: {str(e)}")
    
    def plot_diversity_timeline(self, type_id: str, days: int = 30) -> str:
        """
        Generate timeline plot for diversity metrics over time.
        
        Args:
            type_id: Element type to analyze
            days: Number of days to show
            
        Returns:
            Base64 encoded PNG image or text report
        """
        if not self.tracker:
            return self._generate_text_report("Diversity tracking not available")
        
        try:
            if HAS_MATPLOTLIB:
                return self._create_matplotlib_timeline_plot(type_id, days)
            else:
                return self._create_text_timeline_report(type_id, days)
                
        except Exception as e:
            self.logger.error(f"Timeline plot generation failed: {e}")
            return self._generate_text_report(f"Timeline plot generation failed: {str(e)}")
    
    def create_diversity_dashboard(self, type_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive diversity dashboard data.
        
        Args:
            type_id: Element type to create dashboard for
            
        Returns:
            Dictionary with dashboard data including plots and statistics
        """
        try:
            dashboard = {
                "type_id": type_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "summary_statistics": {},
                "trends": {},
                "recommendations": [],
                "plots": {}
            }
            
            if not self.tracker or not self.analyzer:
                dashboard["error"] = "Diversity components not available"
                return dashboard
            
            # Get recent diversity history
            history = self.tracker.get_type_diversity_history(type_id, days=30)
            
            if not history:
                dashboard["summary_statistics"] = {
                    "status": "no_data",
                    "message": "No diversity data available for this type"
                }
                return dashboard
            
            # Calculate summary statistics
            dashboard["summary_statistics"] = self._calculate_summary_stats(history)
            
            # Generate trend analysis
            metrics = set(record.metric_name for record in history)
            for metric in metrics:
                trend = self.tracker.analyze_diversity_trends(type_id, metric, days=30)
                if trend:
                    dashboard["trends"][metric] = trend.to_dict()
            
            # Generate recommendations
            dashboard["recommendations"] = self._generate_recommendations(history, dashboard["trends"])
            
            # Generate plots
            if HAS_MATPLOTLIB:
                try:
                    # Create timeline plot
                    timeline_plot = self.plot_diversity_timeline(type_id, days=30)
                    dashboard["plots"]["timeline"] = timeline_plot
                    
                    # Create parameter distribution plot (if we have parameter data)
                    # This would typically come from recent generation data
                    dashboard["plots"]["distribution"] = "parameter_distribution_placeholder"
                    
                except Exception as e:
                    self.logger.warning(f"Dashboard plot generation failed: {e}")
                    dashboard["plots"]["error"] = str(e)
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Dashboard creation failed: {e}")
            return {
                "type_id": type_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def generate_diversity_heatmap(self, 
                                  element_types: List[str],
                                  metric_name: str,
                                  days: int = 30) -> str:
        """
        Generate heatmap showing diversity across multiple element types.
        
        Args:
            element_types: List of element types to include
            metric_name: Metric to visualize
            days: Number of days to analyze
            
        Returns:
            Base64 encoded heatmap image or text report
        """
        try:
            if not self.tracker:
                return self._generate_text_report("Diversity tracking not available")
            
            if HAS_MATPLOTLIB:
                return self._create_matplotlib_heatmap(element_types, metric_name, days)
            else:
                return self._create_text_heatmap_report(element_types, metric_name, days)
                
        except Exception as e:
            self.logger.error(f"Heatmap generation failed: {e}")
            return self._generate_text_report(f"Heatmap generation failed: {str(e)}")
    
    def create_cluster_visualization(self, 
                                    params_list: List[Dict[str, Any]], 
                                    n_clusters: int = 5) -> str:
        """
        Create cluster visualization for parameter sets.
        
        Args:
            params_list: List of parameter dictionaries
            n_clusters: Number of clusters to create
            
        Returns:
            Base64 encoded cluster plot or text report
        """
        if not self.analyzer:
            return self._generate_text_report("Diversity analyzer not available")
        
        try:
            if HAS_MATPLOTLIB:
                return self._create_matplotlib_cluster_plot(params_list, n_clusters)
            else:
                return self._create_text_cluster_report(params_list, n_clusters)
                
        except Exception as e:
            self.logger.error(f"Cluster visualization failed: {e}")
            return self._generate_text_report(f"Cluster visualization failed: {str(e)}")
    
    # Private methods for matplotlib-based visualizations
    
    def _create_matplotlib_distribution_plot(self, params_list: List[Dict[str, Any]]) -> str:
        """Create matplotlib-based distribution plot."""
        # Extract numeric parameters
        numeric_data = self._extract_numeric_parameters(params_list)
        
        if not numeric_data:
            return self._generate_text_report("No numeric parameters found for distribution plot")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Parameter Distribution Analysis', fontsize=16, fontweight='bold')
        
        # Flatten all values for overall distribution
        all_values = []
        param_names = []
        
        for i, params in enumerate(numeric_data):
            for j, value in enumerate(params):
                all_values.append(value)
                if j < len(param_names):
                    param_names.append(f"Param_{j}")
                else:
                    param_names.append(f"Param_{j}")
        
        # Plot 1: Overall histogram
        axes[0, 0].hist(all_values, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Overall Parameter Distribution')
        axes[0, 0].set_xlabel('Parameter Value')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Box plot for outliers
        if len(all_values) > 10:
            axes[0, 1].boxplot(all_values, patch_artist=True,
                              boxprops=dict(facecolor='lightgreen', alpha=0.7))
            axes[0, 1].set_title('Parameter Box Plot (Outlier Detection)')
            axes[0, 1].set_ylabel('Parameter Value')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Scatter plot (first two parameters if available)
        if len(numeric_data) > 1 and len(numeric_data[0]) >= 2:
            x_vals = [params[0] for params in numeric_data]
            y_vals = [params[1] for params in numeric_data if len(params) > 1]
            
            min_len = min(len(x_vals), len(y_vals))
            axes[1, 0].scatter(x_vals[:min_len], y_vals[:min_len], 
                             alpha=0.6, c='coral', s=50)
            axes[1, 0].set_title('Parameter Relationship (First 2 Params)')
            axes[1, 0].set_xlabel('Parameter 1')
            axes[1, 0].set_ylabel('Parameter 2')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Parameter statistics
        axes[1, 1].axis('off')
        
        # Calculate statistics
        if HAS_PANDAS and all_values:
            values_series = pd.Series(all_values)
            stats_text = f"""Parameter Statistics:
            
Total Samples: {len(all_values)}
Mean: {values_series.mean():.3f}
Std Dev: {values_series.std():.3f}
Min: {values_series.min():.3f}
Max: {values_series.max():.3f}
Median: {values_series.median():.3f}
Skewness: {values_series.skew():.3f}

Diversity Metrics:
Entropy Score: {self._calculate_entropy(all_values):.3f}
Coefficient of Variation: {self._calculate_cv(all_values):.3f}
"""
        else:
            # Basic statistics without pandas
            mean_val = sum(all_values) / len(all_values)
            variance = sum((x - mean_val) ** 2 for x in all_values) / len(all_values)
            std_val = variance ** 0.5
            
            stats_text = f"""Parameter Statistics:
            
Total Samples: {len(all_values)}
Mean: {mean_val:.3f}
Std Dev: {std_val:.3f}
Min: {min(all_values):.3f}
Max: {max(all_values):.3f}

Diversity Metrics:
Entropy Score: {self._calculate_entropy(all_values):.3f}
Coefficient of Variation: {self._calculate_cv(all_values):.3f}
"""
        
        axes[1, 1].text(0.1, 0.9, stats_text, transform=axes[1, 1].transAxes,
                       fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_matplotlib_timeline_plot(self, type_id: str, days: int) -> str:
        """Create matplotlib-based timeline plot."""
        # Get diversity history
        history = self.tracker.get_type_diversity_history(type_id, days=days)
        
        if not history:
            return self._generate_text_report(f"No diversity history found for type: {type_id}")
        
        # Group by metric
        metric_data = defaultdict(list)
        for record in history:
            metric_data[record.metric_name].append((record.timestamp, record.metric_value))
        
        # Create subplot for each metric (max 4 to avoid overcrowding)
        metrics = list(metric_data.keys())[:4]
        n_plots = len(metrics)
        
        if n_plots == 0:
            return self._generate_text_report("No metrics found for timeline plot")
        
        fig, axes = plt.subplots(n_plots, 1, figsize=(12, 4 * n_plots))
        if n_plots == 1:
            axes = [axes]
        
        fig.suptitle(f'Diversity Metrics Timeline - {type_id}', fontsize=16, fontweight='bold')
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for i, metric_name in enumerate(metrics):
            data_points = metric_data[metric_name]
            
            if not data_points:
                continue
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x[0])
            
            timestamps = [point[0] for point in data_points]
            values = [point[1] for point in data_points]
            
            # Convert timestamps to matplotlib dates
            dates = [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]  # Days since first
            
            axes[i].plot(dates, values, marker='o', linewidth=2, markersize=4, 
                        color=colors[i % len(colors)], alpha=0.8)
            axes[i].set_title(f'{metric_name.title()} Over Time')
            axes[i].set_xlabel('Days Since Start')
            axes[i].set_ylabel('Metric Value')
            axes[i].grid(True, alpha=0.3)
            
            # Add trend line if enough data points
            if len(values) > 2:
                z = np.polyfit(dates, values, 1)
                p = np.poly1d(z)
                axes[i].plot(dates, p(dates), "--", color='red', alpha=0.7, linewidth=1)
                
                # Add trend direction text
                trend = "Increasing" if z[0] > 0 else "Decreasing" if z[0] < 0 else "Stable"
                axes[i].text(0.05, 0.95, f'Trend: {trend}', transform=axes[i].transAxes,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
                           verticalalignment='top')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_matplotlib_heatmap(self, element_types: List[str], metric_name: str, days: int) -> str:
        """Create matplotlib-based heatmap."""
        # Get data for all types
        type_data = {}
        for etype in element_types:
            history = self.tracker.get_type_diversity_history(etype, metric_name, days)
            if history:
                values = [record.metric_value for record in history]
                type_data[etype] = {
                    'mean': sum(values) / len(values),
                    'std': self._calculate_cv(values),
                    'count': len(values),
                    'latest': values[-1] if values else 0
                }
        
        if not type_data:
            return self._generate_text_report(f"No data found for metric: {metric_name}")
        
        # Prepare heatmap data
        etypes = list(type_data.keys())
        metrics = ['mean', 'std', 'count', 'latest']
        
        # Normalize data for heatmap
        heatmap_data = []
        for metric in metrics:
            values = [type_data[etype][metric] for etype in etypes]
            # Normalize to 0-1 range
            min_val, max_val = min(values), max(values)
            if max_val > min_val:
                normalized = [(v - min_val) / (max_val - min_val) for v in values]
            else:
                normalized = [0.5] * len(values)
            heatmap_data.append(normalized)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(max(8, len(etypes) * 2), 6))
        
        im = ax.imshow(heatmap_data, cmap='RdYlBu_r', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(range(len(etypes)))
        ax.set_xticklabels(etypes, rotation=45, ha='right')
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels([m.title() for m in metrics])
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Normalized Value', rotation=270, labelpad=15)
        
        # Add text annotations with actual values
        for i in range(len(metrics)):
            for j in range(len(etypes)):
                actual_value = type_data[etypes[j]][metrics[i]]
                text = ax.text(j, i, f'{actual_value:.2f}',
                             ha="center", va="center", color="black", fontsize=8)
        
        ax.set_title(f'{metric_name.title()} Heatmap Across Element Types')
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_matplotlib_cluster_plot(self, params_list: List[Dict[str, Any]], n_clusters: int) -> str:
        """Create matplotlib-based cluster visualization."""
        if not self.analyzer:
            return self._generate_text_report("Diversity analyzer not available")
        
        # Perform clustering
        cluster_result = self.analyzer.cluster_analysis(params_list, n_clusters)
        
        if "error" in cluster_result:
            return self._generate_text_report(f"Clustering failed: {cluster_result['error']}")
        
        # Extract numeric data for plotting
        numeric_data = self._extract_numeric_parameters(params_list)
        if not numeric_data:
            return self._generate_text_report("No numeric parameters found for clustering")
        
        # Use first two dimensions for 2D plot
        plot_data = []
        for params in numeric_data:
            if len(params) >= 2:
                plot_data.append([params[0], params[1]])
        
        if not plot_data:
            return self._generate_text_report("Insufficient dimensions for 2D cluster plot")
        
        plot_data = np.array(plot_data)
        labels = cluster_result.get('cluster_labels', [0] * len(plot_data))
        
        # Create cluster plot
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        
        # Plot each cluster with different colors
        colors = plt.cm.Set3(np.linspace(0, 1, max(labels) + 1))
        
        for cluster_id in set(labels):
            mask = np.array(labels) == cluster_id
            cluster_points = plot_data[mask]
            ax.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                      c=[colors[cluster_id]], s=50, alpha=0.7,
                      label=f'Cluster {cluster_id}')
        
        ax.set_xlabel('Parameter 1')
        ax.set_ylabel('Parameter 2')
        ax.set_title(f'Parameter Clusters (n_clusters={n_clusters})')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add cluster statistics
        cluster_sizes = cluster_result.get('cluster_sizes', {})
        stats_text = f"Clustering Statistics:\n"
        for cluster_id, size in cluster_sizes.items():
            percentage = (size / len(plot_data)) * 100
            stats_text += f"Cluster {cluster_id}: {size} points ({percentage:.1f}%)\n"
        
        if 'silhouette_score' in cluster_result:
            stats_text += f"Silhouette Score: {cluster_result['silhouette_score']:.3f}"
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
               verticalalignment='top', fontfamily='monospace', fontsize=9)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    # Private methods for text-based visualizations
    
    def _create_text_distribution_report(self, params_list: List[Dict[str, Any]]) -> str:
        """Create text-based distribution report."""
        numeric_data = self._extract_numeric_parameters(params_list)
        
        if not numeric_data:
            return "=== PARAMETER DISTRIBUTION REPORT ===\nNo numeric parameters found for analysis."
        
        all_values = []
        for params in numeric_data:
            all_values.extend(params)
        
        if not all_values:
            return "=== PARAMETER DISTRIBUTION REPORT ===\nNo values found for analysis."
        
        # Calculate basic statistics
        mean_val = sum(all_values) / len(all_values)
        variance = sum((x - mean_val) ** 2 for x in all_values) / len(all_values)
        std_val = variance ** 0.5
        
        # Create simple histogram representation
        min_val, max_val = min(all_values), max(all_values)
        range_size = max_val - min_val
        bin_size = range_size / 10 if range_size > 0 else 1
        
        bins = [0] * 10
        for value in all_values:
            bin_idx = int((value - min_val) / bin_size) if bin_size > 0 else 0
            bin_idx = min(9, max(0, bin_idx))
            bins[bin_idx] += 1
        
        max_count = max(bins)
        
        report = "=== PARAMETER DISTRIBUTION REPORT ===\n\n"
        report += f"Total Samples: {len(all_values)}\n"
        report += f"Parameters per Sample: {len(numeric_data[0]) if numeric_data else 0}\n\n"
        
        report += "STATISTICAL SUMMARY:\n"
        report += f"  Mean: {mean_val:.3f}\n"
        report += f"  Std Dev: {std_val:.3f}\n"
        report += f"  Min: {min_val:.3f}\n"
        report += f"  Max: {max_val:.3f}\n"
        report += f"  Range: {range_size:.3f}\n\n"
        
        report += "DISTRIBUTION HISTOGRAM:\n"
        for i, count in enumerate(bins):
            bin_start = min_val + i * bin_size
            bin_end = bin_start + bin_size
            bar_length = int((count / max_count) * 40) if max_count > 0 else 0
            bar = "█" * bar_length
            report += f"  [{bin_start:6.2f}-{bin_end:6.2f}] {bar} ({count})\n"
        
        report += "\nDIVERSITY METRICS:\n"
        report += f"  Entropy Score: {self._calculate_entropy(all_values):.3f}\n"
        report += f"  Coefficient of Variation: {self._calculate_cv(all_values):.3f}\n"
        
        return report
    
    def _create_text_timeline_report(self, type_id: str, days: int) -> str:
        """Create text-based timeline report."""
        history = self.tracker.get_type_diversity_history(type_id, days=days)
        
        if not history:
            return f"=== DIVERSITY TIMELINE REPORT ===\nNo diversity history found for type: {type_id}"
        
        # Group by metric
        metric_data = defaultdict(list)
        for record in history:
            metric_data[record.metric_name].append((record.timestamp, record.metric_value))
        
        report = f"=== DIVERSITY TIMELINE REPORT ===\n"
        report += f"Element Type: {type_id}\n"
        report += f"Period: {days} days\n"
        report += f"Total Records: {len(history)}\n\n"
        
        for metric_name, data_points in metric_data.items():
            if not data_points:
                continue
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x[0])
            
            values = [point[1] for point in data_points]
            
            report += f"METRIC: {metric_name}\n"
            report += "  Recent Values (Last 10):\n"
            
            # Show last 10 values
            for i, (timestamp, value) in enumerate(data_points[-10:]):
                days_ago = (datetime.utcnow() - timestamp).days
                report += f"    {i+1:2d}. {value:8.3f} ({days_ago} days ago)\n"
            
            # Simple trend analysis
            if len(values) >= 3:
                recent_avg = sum(values[-3:]) / 3
                early_avg = sum(values[:3]) / 3
                
                if recent_avg > early_avg * 1.1:
                    trend = "↗ INCREASING"
                elif recent_avg < early_avg * 0.9:
                    trend = "↘ DECREASING"
                else:
                    trend = "→ STABLE"
                
                report += f"  Trend: {trend}\n"
            
            # Statistics
            report += f"  Current: {values[-1]:.3f}\n"
            report += f"  Average: {sum(values)/len(values):.3f}\n"
            report += f"  Range: {min(values):.3f} - {max(values):.3f}\n\n"
        
        return report
    
    def _create_text_heatmap_report(self, element_types: List[str], metric_name: str, days: int) -> str:
        """Create text-based heatmap report."""
        type_data = {}
        for etype in element_types:
            history = self.tracker.get_type_diversity_history(etype, metric_name, days)
            if history:
                values = [record.metric_value for record in history]
                type_data[etype] = {
                    'mean': sum(values) / len(values),
                    'count': len(values),
                    'latest': values[-1] if values else 0
                }
        
        if not type_data:
            return f"=== DIVERSITY HEATMAP REPORT ===\nNo data found for metric: {metric_name}"
        
        report = f"=== DIVERSITY HEATMAP REPORT ===\n"
        report += f"Metric: {metric_name}\n"
        report += f"Period: {days} days\n"
        report += f"Element Types: {len(element_types)}\n\n"
        
        report += "TYPE COMPARISON:\n"
        
        # Create simple ASCII representation
        for etype, data in type_data.items():
            # Normalize values for simple bar representation
            values = [data['mean'], data['count'] / 10, data['latest']]  # Normalize count
            max_val = max(values) if max(values) > 0 else 1
            
            bars = []
            for val in values:
                bar_length = int((val / max_val) * 20)
                bars.append("█" * bar_length)
            
            report += f"  {etype:<15} │{bars[0]:<20}│ Mean: {data['mean']:.3f}\n"
            report += f"  {' ':<15} │{bars[1]:<20}│ Count: {data['count']}\n"
            report += f"  {' ':<15} │{bars[2]:<20}│ Latest: {data['latest']:.3f}\n"
            report += f"  {'-'*50}\n"
        
        return report
    
    def _create_text_cluster_report(self, params_list: List[Dict[str, Any]], n_clusters: int) -> str:
        """Create text-based cluster report."""
        if not self.analyzer:
            return "=== CLUSTER ANALYSIS REPORT ===\nDiversity analyzer not available."
        
        cluster_result = self.analyzer.cluster_analysis(params_list, n_clusters)
        
        if "error" in cluster_result:
            return f"=== CLUSTER ANALYSIS REPORT ===\nClustering failed: {cluster_result['error']}"
        
        report = f"=== CLUSTER ANALYSIS REPORT ===\n"
        report += f"Parameters: {len(params_list)} samples\n"
        report += f"Requested Clusters: {n_clusters}\n"
        report += f"Actual Clusters: {cluster_result.get('n_clusters', 'Unknown')}\n\n"
        
        # Cluster sizes
        cluster_sizes = cluster_result.get('cluster_sizes', {})
        report += "CLUSTER DISTRIBUTION:\n"
        
        for cluster_id, size in cluster_sizes.items():
            percentage = (size / len(params_list)) * 100
            report += f"  Cluster {cluster_id}: {size:3d} samples ({percentage:5.1f}%)\n"
        
        # Cluster quality
        if 'silhouette_score' in cluster_result:
            score = cluster_result['silhouette_score']
            report += f"\nCLUSTER QUALITY:\n"
            report += f"  Silhouette Score: {score:.3f}\n"
            
            if score > 0.5:
                quality = "EXCELLENT"
            elif score > 0.25:
                quality = "GOOD"
            elif score > 0.0:
                quality = "FAIR"
            else:
                quality = "POOR"
            
            report += f"  Quality Rating: {quality}\n"
        
        # Simple parameter analysis
        numeric_data = self._extract_numeric_parameters(params_list)
        if numeric_data and len(numeric_data[0]) >= 2:
            report += "\nPARAMETER ANALYSIS:\n"
            
            # Calculate means for first two parameters
            param1_means = []
            param2_means = []
            
            labels = cluster_result.get('cluster_labels', [])
            for i, params in enumerate(numeric_data):
                if len(params) >= 2 and i < len(labels):
                    cluster_id = labels[i]
                    if cluster_id not in param1_means:
                        param1_means.append([])
                        param2_means.append([])
                    param1_means[cluster_id].append(params[0])
                    param2_means[cluster_id].append(params[1])
            
            for cluster_id in range(len(param1_means)):
                p1_mean = sum(param1_means[cluster_id]) / len(param1_means[cluster_id])
                p2_mean = sum(param2_means[cluster_id]) / len(param2_means[cluster_id])
                report += f"  Cluster {cluster_id} Center: ({p1_mean:.2f}, {p2_mean:.2f})\n"
        
        return report
    
    # Utility methods
    
    def _generate_text_report(self, message: str) -> str:
        """Generate a simple text report."""
        return f"=== DIVERSITY VISUALIZATION REPORT ===\n\n{message}\n"
    
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
    
    def _calculate_summary_stats(self, history) -> Dict[str, Any]:
        """Calculate summary statistics from diversity history."""
        if not history:
            return {"status": "no_data"}
        
        # Group by metric
        metric_data = defaultdict(list)
        for record in history:
            metric_data[record.metric_name].append(record.metric_value)
        
        summary = {
            "total_records": len(history),
            "metrics_tracked": len(metric_data),
            "date_range": {
                "earliest": min(record.timestamp for record in history).isoformat() + "Z",
                "latest": max(record.timestamp for record in history).isoformat() + "Z"
            },
            "metric_averages": {}
        }
        
        for metric_name, values in metric_data.items():
            summary["metric_averages"][metric_name] = {
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else 0,
                "data_points": len(values)
            }
        
        return summary
    
    def _generate_recommendations(self, history, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on diversity analysis."""
        recommendations = []
        
        # Analyze trends for recommendations
        for metric_name, trend_data in trends.items():
            trend_direction = trend_data.get("trend_direction", "unknown")
            trend_strength = trend_data.get("trend_strength", 0)
            
            if trend_direction == "decreasing" and trend_strength > 0.3:
                recommendations.append(
                    f"Metric '{metric_name}' shows declining diversity - "
                    "consider expanding parameter ranges or adjusting generation strategy"
                )
            elif trend_direction == "increasing" and trend_strength > 0.5:
                recommendations.append(
                    f"Metric '{metric_name}' shows strong improving diversity - "
                    "current strategy is working well"
                )
        
        # Analyze current values
        metric_latest = defaultdict(float)
        for record in history:
            metric_latest[record.metric_name] = record.metric_value
        
        for metric_name, current_value in metric_latest.items():
            if current_value < 0.3:
                recommendations.append(
                    f"Metric '{metric_name}' has low current value ({current_value:.2f}) - "
                    "consider increasing diversity settings"
                )
            elif current_value > 0.8:
                recommendations.append(
                    f"Metric '{metric_name}' has high current value ({current_value:.2f}) - "
                    "diversity might be too high, consider tightening ranges"
                )
        
        if not recommendations:
            recommendations.append("Diversity metrics appear to be in good range")
        
        return recommendations
    
    def _calculate_entropy(self, values: List[float]) -> float:
        """Calculate entropy for a list of values."""
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


        return recommendations
    
    def _calculate_cv(self, values: List[float]) -> float:
        """Calculate coefficient of variation."""
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
    
    def plot_parameter_distribution_for_type(self, type_id: str) -> str:
        """
        Generate parameter distribution plot for a specific element type.
        
        Args:
            type_id: Element type to analyze
            
        Returns:
            Base64 encoded PNG image or text report
        """
        try:
            # This would typically fetch recent parameter data for the type
            # For now, we'll return a placeholder
            return self._generate_text_report(f"Parameter distribution for type: {type_id} (placeholder)")
        except Exception as e:
            self.logger.error(f"Parameter distribution for type {type_id} failed: {e}")
            return self._generate_text_report(f"Failed to generate parameter distribution for {type_id}: {str(e)}")


# Create DiversityViz alias for backward compatibility
DiversityViz = DiversityVisualizer