"""
Diversity Tracker

This module provides comprehensive diversity tracking and analytics
for the NanoBanana generation system.

Features:
- Track diversity metrics over time
- Store reports in SQLite database
- Generate diversity trends and insights
- Integration with existing storage system
"""

from typing import List, Dict, Any, Optional, Tuple
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import os
from contextlib import contextmanager

# Import diversity metrics
try:
    from utils.diversity_metrics import DiversityAnalyzer
    # Import DiversityReport only if available, otherwise define a simple version
    try:
        from utils.diversity_metrics import DiversityReport
    except ImportError:
        # Simple fallback for DiversityReport
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class DiversityReport:
            """Simple fallback DiversityReport."""
            timestamp: datetime
            sample_count: int
            metric_scores: dict
            parameter_coverage: dict = None
            recommendations: list = None
            
            def to_dict(self) -> dict:
                return {
                    "timestamp": self.timestamp.isoformat() + "Z",
                    "sample_count": self.sample_count,
                    "metric_scores": self.metric_scores,
                    "parameter_coverage": self.parameter_coverage,
                    "recommendations": self.recommendations or []
                }
    
    HAS_DIVERSITY_METRICS = True
except ImportError:
    HAS_DIVERSITY_METRICS = False
    print("⚠️ Diversity metrics not available")

# Import type system components
try:
    from enhanced_design.element_types import ElementType
    HAS_TYPE_SYSTEM = True
except ImportError:
    HAS_TYPE_SYSTEM = False
    print("⚠️ Type system not available")


@dataclass
class DiversityRecord:
    """Record of diversity metrics for a specific time."""
    timestamp: datetime
    element_type: str
    metric_name: str
    metric_value: float
    sample_count: int
    additional_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "element_type": self.element_type,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "sample_count": self.sample_count,
            "additional_data": json.dumps(self.additional_data)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiversityRecord':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
            element_type=data["element_type"],
            metric_name=data["metric_name"],
            metric_value=data["metric_value"],
            sample_count=data["sample_count"],
            additional_data=json.loads(data.get("additional_data", "{}"))
        )


@dataclass
class DiversityTrend:
    """Trend analysis for diversity metrics."""
    element_type: str
    metric_name: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    current_value: float
    average_value: float
    min_value: float
    max_value: float
    data_points: List[Tuple[datetime, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "element_type": self.element_type,
            "metric_name": self.metric_name,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "current_value": self.current_value,
            "average_value": self.average_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "data_points": [(ts.isoformat() + "Z", val) for ts, val in self.data_points]
        }


class DiversityTracker:
    """
    Main diversity tracking system with SQLite storage.
    
    Provides comprehensive tracking of diversity metrics over time
    with trend analysis and reporting capabilities.
    """
    
    def __init__(self, db_path: str = "diversity_tracking.db"):
        """
        Initialize diversity tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.analyzer = DiversityAnalyzer() if HAS_DIVERSITY_METRICS else None
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) if os.path.dirname(db_path) else ".", exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        self.logger.info(f"DiversityTracker initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create diversity records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS diversity_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        element_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        sample_count INTEGER NOT NULL,
                        additional_data TEXT
                    )
                """)
                
                # Create diversity reports table (for full reports)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS diversity_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        element_type TEXT,
                        report_data TEXT NOT NULL
                    )
                """)
                
                # Create separate indexes for better query performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON diversity_records (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_element_type ON diversity_records (element_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric ON diversity_records (metric_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp_reports ON diversity_reports (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_element_type_reports ON diversity_reports (element_type)")
                
                # Create index on compound queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_type_metric_timestamp
                    ON diversity_records (element_type, metric_name, timestamp)
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def record_generation(self, 
                         element_type: str,
                         diversity_report: DiversityReport,
                         additional_context: Dict[str, Any] = None) -> bool:
        """
        Record diversity metrics from a generation session.
        
        Args:
            element_type: Type of element generated
            diversity_report: Diversity analysis report
            additional_context: Additional context data
            
        Returns:
            True if recording was successful
        """
        try:
            if not self.analyzer:
                self.logger.warning("DiversityAnalyzer not available - skipping record")
                return False
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Store individual metric records
                for metric_name, metric_value in diversity_report.metric_scores.items():
                    record = DiversityRecord(
                        timestamp=diversity_report.timestamp,
                        element_type=element_type,
                        metric_name=metric_name,
                        metric_value=metric_value,
                        sample_count=diversity_report.sample_count,
                        additional_data=additional_context or {}
                    )
                    
                    cursor.execute("""
                        INSERT INTO diversity_records 
                        (timestamp, element_type, metric_name, metric_value, sample_count, additional_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        record.timestamp.isoformat() + "Z",
                        record.element_type,
                        record.metric_name,
                        record.metric_value,
                        record.sample_count,
                        json.dumps(record.additional_data)
                    ))
                
                # Store full report
                cursor.execute("""
                    INSERT INTO diversity_reports 
                    (timestamp, element_type, report_data)
                    VALUES (?, ?, ?)
                """, (
                    diversity_report.timestamp.isoformat() + "Z",
                    element_type,
                    json.dumps(diversity_report.to_dict())
                ))
                
                conn.commit()
                self.logger.debug(f"Recorded diversity data for {element_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to record diversity data: {e}")
            return False
    
    def get_type_diversity_history(self, 
                                  element_type: str, 
                                  metric_name: str = None,
                                  days: int = 30) -> List[DiversityRecord]:
        """
        Get diversity history for a specific element type.
        
        Args:
            element_type: Type of element to get history for
            metric_name: Specific metric to filter by (None for all metrics)
            days: Number of days to look back
            
        Returns:
            List of diversity records
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query based on parameters
                query = """
                    SELECT timestamp, element_type, metric_name, metric_value, 
                           sample_count, additional_data
                    FROM diversity_records 
                    WHERE element_type = ? AND timestamp >= ?
                """
                params = [element_type, cutoff_date.isoformat() + "Z"]
                
                if metric_name:
                    query += " AND metric_name = ?"
                    params.append(metric_name)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to DiversityRecord objects
                records = []
                for row in rows:
                    record_data = {
                        "timestamp": row["timestamp"],
                        "element_type": row["element_type"],
                        "metric_name": row["metric_name"],
                        "metric_value": row["metric_value"],
                        "sample_count": row["sample_count"],
                        "additional_data": json.loads(row["additional_data"] or "{}")
                    }
                    records.append(DiversityRecord.from_dict(record_data))
                
                self.logger.debug(f"Retrieved {len(records)} diversity records for {element_type}")
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get diversity history: {e}")
            return []
    
    def analyze_diversity_trends(self, 
                                element_type: str, 
                                metric_name: str,
                                days: int = 30) -> Optional[DiversityTrend]:
        """
        Analyze diversity trends for a specific metric.
        
        Args:
            element_type: Type of element to analyze
            metric_name: Metric to analyze trends for
            days: Number of days to analyze
            
        Returns:
            DiversityTrend analysis or None if insufficient data
        """
        try:
            # Get historical data
            history = self.get_type_diversity_history(element_type, metric_name, days)
            
            if len(history) < 2:
                self.logger.debug(f"Insufficient data for trend analysis: {len(history)} points")
                return None
            
            # Prepare data points
            data_points = [(record.timestamp, record.metric_value) for record in history]
            data_points.sort(key=lambda x: x[0])  # Sort by timestamp
            
            values = [point[1] for point in data_points]
            
            # Calculate trend statistics
            current_value = values[-1]
            average_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            
            # Simple trend analysis
            if len(values) >= 3:
                # Compare recent values to earlier values
                recent_avg = sum(values[-3:]) / 3
                early_avg = sum(values[:3]) / 3
                
                if recent_avg > early_avg * 1.1:
                    trend_direction = "increasing"
                    trend_strength = min(1.0, (recent_avg - early_avg) / early_avg)
                elif recent_avg < early_avg * 0.9:
                    trend_direction = "decreasing"
                    trend_strength = min(1.0, (early_avg - recent_avg) / early_avg)
                else:
                    trend_direction = "stable"
                    trend_strength = 0.0
            else:
                trend_direction = "insufficient_data"
                trend_strength = 0.0
            
            return DiversityTrend(
                element_type=element_type,
                metric_name=metric_name,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                current_value=current_value,
                average_value=average_value,
                min_value=min_value,
                max_value=max_value,
                data_points=data_points
            )
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return None
    
    def generate_diversity_report(self, 
                                 element_type: str = None,
                                 days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive diversity report.
        
        Args:
            element_type: Specific element type to report on (None for all types)
            days: Number of days to include in report
            
        Returns:
            Comprehensive diversity report dictionary
        """
        try:
            # Get relevant data
            if element_type:
                history = self.get_type_diversity_history(element_type, days=days)
                types_to_analyze = [element_type]
            else:
                # Get all types
                types_to_analyze = self._get_available_types(days)
                history = []
                for etype in types_to_analyze:
                    history.extend(self.get_type_diversity_history(etype, days=days))
            
            # Generate report structure
            report = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "report_period_days": days,
                "element_types": types_to_analyze,
                "total_records": len(history),
                "metrics": {},
                "trends": {},
                "summary": {}
            }
            
            # Analyze each type and metric
            type_metrics = {}
            for record in history:
                if record.element_type not in type_metrics:
                    type_metrics[record.element_type] = {}
                if record.metric_name not in type_metrics[record.element_type]:
                    type_metrics[record.element_type][record.metric_name] = []
                type_metrics[record.element_type][record.metric_name].append(record.metric_value)
            
            # Calculate statistics for each type/metric combination
            for etype, metrics in type_metrics.items():
                report["metrics"][etype] = {}
                for metric_name, values in metrics.items():
                    if len(values) > 0:
                        report["metrics"][etype][metric_name] = {
                            "current_value": values[-1],
                            "average": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "data_points": len(values),
                            "coefficient_of_variation": self._calculate_cv(values)
                        }
                
                # Generate trend analysis
                for metric_name in metrics.keys():
                    trend = self.analyze_diversity_trends(etype, metric_name, days)
                    if trend:
                        if etype not in report["trends"]:
                            report["trends"][etype] = {}
                        report["trends"][etype][metric_name] = trend.to_dict()
            
            # Generate overall summary
            report["summary"] = self._generate_summary_stats(report["metrics"])
            
            self.logger.info(f"Generated diversity report for {len(types_to_analyze)} types over {days} days")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate diversity report: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def get_diversity_statistics(self) -> Dict[str, Any]:
        """
        Get overall diversity tracking statistics.
        
        Returns:
            Dictionary with tracking statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get basic counts
                cursor.execute("SELECT COUNT(*) as total_records FROM diversity_records")
                total_records = cursor.fetchone()["total_records"]
                
                cursor.execute("SELECT COUNT(*) as total_reports FROM diversity_reports")
                total_reports = cursor.fetchone()["total_reports"]
                
                cursor.execute("SELECT COUNT(DISTINCT element_type) as unique_types FROM diversity_records")
                unique_types = cursor.fetchone()["unique_types"]
                
                cursor.execute("SELECT COUNT(DISTINCT metric_name) as unique_metrics FROM diversity_records")
                unique_metrics = cursor.fetchone()["unique_metrics"]
                
                # Get date range
                cursor.execute("""
                    SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest 
                    FROM diversity_records
                """)
                date_range = cursor.fetchone()
                
                # Get metric value ranges
                cursor.execute("""
                    SELECT metric_name, MIN(metric_value) as min_val, MAX(metric_value) as max_val,
                           AVG(metric_value) as avg_val
                    FROM diversity_records 
                    GROUP BY metric_name
                """)
                metric_stats = cursor.fetchall()
                
                stats = {
                    "total_records": total_records,
                    "total_reports": total_reports,
                    "unique_types": unique_types,
                    "unique_metrics": unique_metrics,
                    "date_range": {
                        "earliest": date_range["earliest"],
                        "latest": date_range["latest"]
                    },
                    "metric_statistics": [
                        {
                            "metric": row["metric_name"],
                            "min_value": row["min_val"],
                            "max_value": row["max_val"],
                            "average_value": row["avg_val"]
                        }
                        for row in metric_stats
                    ],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get diversity statistics: {e}")
            return {"error": str(e)}
    
    def record_generation(self,
                         type_id: str,
                         generation_params: Dict[str, Any] = None,
                         diversity_score: float = None,
                         asset_metadata: Dict[str, Any] = None) -> bool:
        """
        Record a generation event for diversity tracking.
        
        Args:
            type_id: ElementType identifier
            generation_params: Generation parameters used
            diversity_score: Diversity score for this generation
            asset_metadata: Additional asset metadata
            
        Returns:
            True if recording was successful
        """
        try:
            # Create a simple diversity report for recording
            if not diversity_score:
                diversity_score = 0.5  # Default moderate diversity
            
            additional_context = {
                "generation_params": generation_params or {},
                "asset_metadata": asset_metadata or {}
            }
            
            # Use current time and create a basic report
            current_time = datetime.utcnow()
            additional_context = additional_context or {}
            additional_context.update({
                "generation_params": generation_params or {},
                "asset_metadata": asset_metadata or {}
            })
            
            # Store individual metric records directly
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Store the diversity score as a metric
                cursor.execute("""
                    INSERT INTO diversity_records
                    (timestamp, element_type, metric_name, metric_value, sample_count, additional_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    current_time.isoformat() + "Z",
                    type_id,
                    "generation_diversity",
                    diversity_score,
                    1,
                    json.dumps(additional_context)
                ))
                
                # Store full report data
                report_data = {
                    "timestamp": current_time.isoformat() + "Z",
                    "sample_count": 1,
                    "metric_scores": {"generation_diversity": diversity_score},
                    "recommendations": []
                }
                
                cursor.execute("""
                    INSERT INTO diversity_reports
                    (timestamp, element_type, report_data)
                    VALUES (?, ?, ?)
                """, (
                    current_time.isoformat() + "Z",
                    type_id,
                    json.dumps(report_data)
                ))
                
                conn.commit()
                self.logger.debug(f"Recorded generation diversity data for {type_id}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to record generation: {e}")
            return False

    def get_current_diversity_metrics(self, type_id: str) -> Dict[str, Any]:
        """
        Get current diversity metrics for a type.
        
        Args:
            type_id: ElementType identifier
            
        Returns:
            Current diversity metrics
        """
        try:
            # Get recent history (last 7 days)
            history = self.get_type_diversity_history(type_id, days=7)
            
            if not history:
                return {"status": "no_data", "message": "No recent diversity data available"}
            
            # Group by metric and get latest values
            metrics = {}
            for record in history:
                if record.metric_name not in metrics:
                    metrics[record.metric_name] = {
                        "current_value": record.metric_value,
                        "latest_timestamp": record.timestamp.isoformat() + "Z",
                        "sample_count": record.sample_count
                    }
            
            return {
                "type_id": type_id,
                "metrics": metrics,
                "total_records": len(history),
                "analysis_period_days": 7,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get current diversity metrics: {e}")
            return {"error": str(e)}

    def analyze_diversity_trend(self, type_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze diversity trends for a type (singular version).
        
        Args:
            type_id: ElementType identifier
            days: Number of days to analyze
            
        Returns:
            Trend analysis results
        """
        try:
            # Get all metrics for the type and analyze each
            history = self.get_type_diversity_history(type_id, days=days)
            
            if not history:
                return {"status": "no_data", "message": f"No data found for type {type_id}"}
            
            # Group by metric
            metrics = {}
            for record in history:
                if record.metric_name not in metrics:
                    metrics[record.metric_name] = []
                metrics[record.metric_name].append(record)
            
            # Analyze trends for each metric
            trends = {}
            for metric_name, records in metrics.items():
                if len(records) >= 2:
                    # Sort by timestamp
                    records.sort(key=lambda x: x.timestamp)
                    values = [r.metric_value for r in records]
                    
                    # Simple trend calculation
                    recent_avg = sum(values[-3:]) / min(3, len(values))
                    early_avg = sum(values[:3]) / min(3, len(values))
                    
                    if recent_avg > early_avg * 1.05:
                        trend = "increasing"
                    elif recent_avg < early_avg * 0.95:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                    
                    trends[metric_name] = {
                        "trend": trend,
                        "current_value": values[-1],
                        "average_value": sum(values) / len(values),
                        "data_points": len(values)
                    }
            
            return {
                "type_id": type_id,
                "trends": trends,
                "days_analyzed": days,
                "total_records": len(history),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze diversity trend: {e}")
            return {"error": str(e)}

    def get_overall_diversity_overview(self) -> Dict[str, Any]:
        """
        Get system-wide diversity overview.
        
        Returns:
            Overview of diversity across all types
        """
        try:
            # Get basic statistics
            stats = self.get_diversity_statistics()
            
            # Get recent data for all types
            types = self._get_available_types(days=30)
            
            overview = {
                "total_types": len(types),
                "total_records": stats.get("total_records", 0),
                "unique_metrics": stats.get("unique_metrics", 0),
                "data_period_days": 30,
                "system_health": "unknown"
            }
            
            # Determine system health based on metrics
            if stats.get("total_records", 0) > 100:
                overview["system_health"] = "healthy"
            elif stats.get("total_records", 0) > 10:
                overview["system_health"] = "moderate"
            else:
                overview["system_health"] = "low_activity"
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get overall diversity overview: {e}")
            return {"error": str(e)}

    def get_type_diversity_rankings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get type diversity rankings.
        
        Args:
            limit: Maximum number of types to return
            
        Returns:
            List of types ranked by diversity
        """
        try:
            types = self._get_available_types(days=30)
            rankings = []
            
            for type_id in types:
                history = self.get_type_diversity_history(type_id, days=30)
                
                if history:
                    # Calculate diversity score based on metric variation
                    values = [r.metric_value for r in history]
                    diversity_score = self._calculate_cv(values)
                    
                    rankings.append({
                        "type_id": type_id,
                        "diversity_score": diversity_score,
                        "record_count": len(values),
                        "avg_value": sum(values) / len(values) if values else 0
                    })
            
            # Sort by diversity score
            rankings.sort(key=lambda x: x["diversity_score"], reverse=True)
            
            return rankings[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get type diversity rankings: {e}")
            return []

    def get_diversity_health_metrics(self) -> Dict[str, Any]:
        """
        Get system diversity health metrics.
        
        Returns:
            Health metrics for the diversity system
        """
        try:
            stats = self.get_diversity_statistics()
            rankings = self.get_type_diversity_rankings()
            
            health_metrics = {
                "system_health_score": 0.0,
                "active_types_count": len(rankings),
                "high_diversity_types": len([r for r in rankings if r["diversity_score"] > 0.7]),
                "low_diversity_types": len([r for r in rankings if r["diversity_score"] < 0.3]),
                "total_data_points": stats.get("total_records", 0),
                "days_of_data": 30,  # Based on recent data
                "recommendations": []
            }
            
            # Calculate health score
            if health_metrics["active_types_count"] > 0:
                diversity_ratio = health_metrics["high_diversity_types"] / health_metrics["active_types_count"]
                data_health = min(1.0, health_metrics["total_data_points"] / 100)
                health_metrics["system_health_score"] = (diversity_ratio + data_health) / 2
            
            # Generate recommendations
            if health_metrics["high_diversity_types"] < health_metrics["active_types_count"] * 0.3:
                health_metrics["recommendations"].append("Consider increasing diversity settings for some types")
            
            if health_metrics["total_data_points"] < 50:
                health_metrics["recommendations"].append("Generate more assets to improve diversity tracking")
            
            if not health_metrics["recommendations"]:
                health_metrics["recommendations"].append("Diversity system is performing well")
            
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get diversity health metrics: {e}")
            return {"error": str(e)}

    def generate_comprehensive_report(self,
                                    type_ids: List[str] = None,
                                    days: int = 30,
                                    include_charts: bool = True,
                                    include_recommendations: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive diversity report.
        
        Args:
            type_ids: Specific types to include (None for all)
            days: Analysis period
            include_charts: Whether to include chart data
            include_recommendations: Whether to include recommendations
            
        Returns:
            Comprehensive report dictionary
        """
        try:
            # Determine types to analyze
            if type_ids is None:
                type_ids = self._get_available_types(days=days)
            
            report_id = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            report = {
                "report_id": report_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "analysis_period_days": days,
                "types_analyzed": type_ids,
                "summary": {},
                "detailed_analysis": {},
                "charts": {},
                "recommendations": []
            }
            
            # Generate summary
            report["summary"] = self.get_overall_diversity_overview()
            
            # Generate detailed analysis for each type
            for type_id in type_ids:
                report["detailed_analysis"][type_id] = self.analyze_diversity_trend(type_id, days)
            
            # Add charts if requested
            if include_charts:
                # These would typically generate base64 chart images
                report["charts"]["timeline"] = "chart_data_placeholder"
                report["charts"]["distribution"] = "chart_data_placeholder"
            
            # Add recommendations if requested
            if include_recommendations:
                report["recommendations"] = self._generate_comprehensive_recommendations(type_ids, days)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {e}")
            return {"error": str(e)}

    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics.
        
        Returns:
            System-wide statistics
        """
        try:
            return self.get_diversity_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get system statistics: {e}")
            return {"error": str(e)}

    def _generate_comprehensive_recommendations(self, type_ids: List[str], days: int) -> List[str]:
        """
        Generate comprehensive recommendations for multiple types.
        
        Args:
            type_ids: Types to analyze
            days: Analysis period
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        try:
            for type_id in type_ids:
                history = self.get_type_diversity_history(type_id, days=days)
                
                if history:
                    values = [r.metric_value for r in history]
                    avg_diversity = sum(values) / len(values)
                    
                    if avg_diversity < 0.3:
                        recommendations.append(f"Type '{type_id}' shows low diversity - consider expanding parameter ranges")
                    elif avg_diversity > 0.8:
                        recommendations.append(f"Type '{type_id}' has high diversity - current settings are working well")
            
            if not recommendations:
                recommendations.append("All analyzed types show good diversity performance")
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to system error")
        
        return recommendations
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old diversity records to manage database size.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete old records
                cursor.execute("""
                    DELETE FROM diversity_records 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat() + "Z",))
                
                deleted_records = cursor.rowcount
                
                # Delete old reports
                cursor.execute("""
                    DELETE FROM diversity_reports 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat() + "Z",))
                
                deleted_reports = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_records} records and {deleted_reports} reports older than {days_to_keep} days")
                return deleted_records + deleted_reports
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
            return 0
    
    def export_diversity_data(self, 
                             element_type: str = None,
                             format: str = "json",
                             days: int = 30) -> Dict[str, Any]:
        """
        Export diversity data for external analysis.
        
        Args:
            element_type: Specific element type to export (None for all)
            format: Export format ("json" or "csv")
            days: Number of days to export
            
        Returns:
            Export results with data and metadata
        """
        try:
            # Get data
            if element_type:
                history = self.get_type_diversity_history(element_type, days=days)
            else:
                types_to_export = self._get_available_types(days)
                history = []
                for etype in types_to_export:
                    history.extend(self.get_type_diversity_history(etype, days=days))
            
            # Prepare export data
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat() + "Z",
                "element_type": element_type,
                "period_days": days,
                "record_count": len(history),
                "format": format
            }
            
            if format.lower() == "json":
                export_data["data"] = [record.to_dict() for record in history]
            elif format.lower() == "csv":
                # Convert to CSV format
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(["timestamp", "element_type", "metric_name", "metric_value", "sample_count", "additional_data"])
                
                # Write data
                for record in history:
                    writer.writerow([
                        record.timestamp.isoformat() + "Z",
                        record.element_type,
                        record.metric_name,
                        record.metric_value,
                        record.sample_count,
                        json.dumps(record.additional_data)
                    ])
                
                export_data["csv_data"] = output.getvalue()
                output.close()
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Exported {len(history)} diversity records in {format} format")
            return export_data
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _get_available_types(self, days: int = 30) -> List[str]:
        """Get list of element types with data in the specified period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT DISTINCT element_type 
                    FROM diversity_records 
                    WHERE timestamp >= ?
                    ORDER BY element_type
                """, (cutoff_date.isoformat() + "Z",))
                
                return [row["element_type"] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get available types: {e}")
            return []
    
    def _calculate_cv(self, values: List[float]) -> float:
        """Calculate coefficient of variation."""
        if not values or len(values) < 2:
            return 0.0
        
        try:
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                return 0.0
            
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_val = variance ** 0.5
            
            return std_val / mean_val
            
        except Exception:
            return 0.0
    
    def _generate_summary_stats(self, metrics: Dict[str, Dict[str, Dict[str, float]]]) -> Dict[str, Any]:
        """Generate summary statistics from metrics data."""
        try:
            summary = {
                "total_element_types": len(metrics),
                "total_metrics": 0,
                "high_diversity_types": [],  # Types with good diversity scores
                "needs_improvement": [],     # Types with low diversity
                "metric_averages": {}
            }
            
            # Analyze each type
            for etype, type_metrics in metrics.items():
                type_diversity_scores = []
                
                for metric_name, metric_stats in type_metrics.items():
                    summary["total_metrics"] += 1
                    
                    # Track metric averages
                    if metric_name not in summary["metric_averages"]:
                        summary["metric_averages"][metric_name] = []
                    summary["metric_averages"][metric_name].append(metric_stats["average"])
                    
                    # Collect diversity scores (assuming higher is better)
                    if "coefficient_of_variation" in metric_stats:
                        type_diversity_scores.append(metric_stats["coefficient_of_variation"])
                
                # Classify types
                if type_diversity_scores:
                    avg_diversity = sum(type_diversity_scores) / len(type_diversity_scores)
                    
                    if avg_diversity > 0.7:
                        summary["high_diversity_types"].append(etype)
                    elif avg_diversity < 0.3:
                        summary["needs_improvement"].append(etype)
            
            # Calculate metric averages
            for metric_name, values in summary["metric_averages"].items():
                summary["metric_averages"][metric_name] = sum(values) / len(values)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary stats: {e}")
            return {"error": str(e)}