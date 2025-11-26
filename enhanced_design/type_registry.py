"""
Type Registry System

This module implements the TypeRegistry class for managing dynamic element types
with SQLite persistence and in-memory caching.

The registry provides:
- CRUD operations for element types
- SQLite-backed persistence
- LRU caching for performance
- Automatic schema validation
- Search and filtering capabilities
"""

import sqlite3
import json
import logging
import os
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from .element_types import ElementType, validate_param_schema


class TypeRegistry:
    """
    Registry for managing dynamic element types with persistence and caching.
    
    Features:
    - SQLite persistence for durability
    - LRU caching for performance
    - Thread-safe operations
    - Automatic schema validation
    - Search and filtering
    - Usage analytics
    """
    
    def __init__(self, storage_path: str = "storage/types/type_registry.db", 
                 cache_size: int = 1000, auto_migrate: bool = True):
        """
        Initialize the type registry.
        
        Args:
            storage_path: Path to SQLite database file
            cache_size: Maximum number of types to cache in memory
            auto_migrate: Whether to automatically run migrations on startup
        """
        self.storage_path = storage_path
        self.cache_size = cache_size
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Create storage directory if it doesn't exist
        storage_dir = Path(storage_path).parent
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        if auto_migrate:
            self._migrate_database()
        
        # Cache for frequently accessed types
        self._type_cache: Dict[str, ElementType] = {}
        self._cache_order: List[str] = []  # For LRU tracking
        self._load_all_lock = threading.Lock()  # Prevent concurrent full loads
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.cursor()
            
            # Create types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS element_types (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    render_strategy TEXT,  -- JSON object
                    param_schema TEXT,  -- JSON object
                    variants TEXT,  -- JSON array
                    diversity_config TEXT,  -- JSON object
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    llm_prompt TEXT,
                    llm_model TEXT,
                    version TEXT NOT NULL,
                    parent_type_id TEXT,
                    is_active BOOLEAN NOT NULL,
                    is_template BOOLEAN NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT,  -- JSON object for additional data
                    FOREIGN KEY (parent_type_id) REFERENCES element_types (id)
                )
            """)
            
            # Create usage analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS type_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_id TEXT NOT NULL,
                    action TEXT NOT NULL,  -- 'generate', 'view', 'edit', etc.
                    timestamp TIMESTAMP NOT NULL,
                    parameters TEXT,  -- JSON object
                    success BOOLEAN,
                    duration_ms REAL,
                    user_agent TEXT,
                    FOREIGN KEY (type_id) REFERENCES element_types (id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_types_category 
                ON element_types(category)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_types_active 
                ON element_types(is_active)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_types_usage 
                ON element_types(usage_count DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_type_timestamp 
                ON type_usage(type_id, timestamp DESC)
            """)
            
            conn.commit()
        
        self.logger.info(f"Type registry initialized at {self.storage_path}")
    
    def _migrate_database(self) -> None:
        """Run database migrations if needed."""
        # This is where you would add migration logic for schema changes
        # For now, we just check if the database structure is correct
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(element_types)")
                columns = {row[1] for row in cursor.fetchall()}
                
                required_columns = {
                    'id', 'name', 'description', 'category', 'tags',
                    'render_strategy', 'param_schema', 'variants',
                    'diversity_config', 'created_by', 'created_at',
                    'version', 'is_active', 'is_template', 'usage_count'
                }
                
                missing_columns = required_columns - columns
                if missing_columns:
                    self.logger.warning(f"Missing database columns: {missing_columns}")
                    # In a real implementation, you would run migrations here
                
        except Exception as e:
            self.logger.error(f"Error during database migration: {e}")
            raise
    
    def _serialize_for_storage(self, element_type: ElementType) -> Dict[str, Any]:
        """Serialize an ElementType for database storage."""
        data = element_type.dict()
        
        # Convert complex objects to JSON strings
        json_fields = ['tags', 'render_strategy', 'param_schema', 'variants', 'diversity_config', 'metadata']
        for field in json_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], (list, dict)):
                    data[field] = json.dumps(data[field])
        
        return data
    
    def _deserialize_from_storage(self, data: Dict[str, Any]) -> ElementType:
        """Deserialize data from database into an ElementType."""
        # Convert JSON strings back to objects
        json_fields = ['tags', 'render_strategy', 'param_schema', 'variants', 'diversity_config', 'metadata']
        for field in json_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse JSON for field {field}")
                        data[field] = None
        
        return ElementType(**data)
    
    def _add_to_cache(self, element_type: ElementType) -> None:
        """Add element type to the LRU cache."""
        type_id = element_type.id
        
        # Remove from cache if it already exists
        if type_id in self._type_cache:
            self._cache_order.remove(type_id)
        
        # Add to cache
        self._type_cache[type_id] = element_type
        self._cache_order.append(type_id)
        
        # Evict oldest entries if cache is full
        while len(self._type_cache) > self.cache_size:
            oldest_id = self._cache_order.pop(0)
            del self._type_cache[oldest_id]
            self.logger.debug(f"Evicted type {oldest_id} from cache")
    
    def _remove_from_cache(self, type_id: str) -> bool:
        """Remove element type from cache."""
        if type_id in self._type_cache:
            del self._type_cache[type_id]
            if type_id in self._cache_order:
                self._cache_order.remove(type_id)
            return True
        return False
    
    def _get_from_cache(self, type_id: str) -> Optional[ElementType]:
        """Get element type from cache and update LRU order."""
        if type_id in self._type_cache:
            # Update LRU order
            self._cache_order.remove(type_id)
            self._cache_order.append(type_id)
            return self._type_cache[type_id]
        return None
    
    def load_all(self, force_refresh: bool = False) -> Dict[str, ElementType]:
        """
        Load all element types from the database.
        
        Args:
            force_refresh: Whether to force a reload from database
            
        Returns:
            Dictionary mapping type IDs to ElementType instances
        """
        # Use lock to prevent concurrent full loads
        with self._load_all_lock:
            # Check if we already have all types loaded and not forcing refresh
            if not force_refresh and len(self._type_cache) > 0:
                return self._type_cache.copy()
            
            self.logger.info("Loading all element types from database")
            
            types_dict = {}
            
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM element_types WHERE is_active = 1")
                    
                    for row in cursor.fetchall():
                        # Convert row to dictionary using column names
                        column_names = [description[0] for description in cursor.description]
                        data = dict(zip(column_names, row))
                        
                        try:
                            element_type = self._deserialize_from_storage(data)
                            types_dict[element_type.id] = element_type
                        except Exception as e:
                            self.logger.error(f"Failed to deserialize type {data.get('id', 'unknown')}: {e}")
                            continue
                
                # Update cache
                self._type_cache.clear()
                self._cache_order.clear()
                for element_type in types_dict.values():
                    self._add_to_cache(element_type)
                
                self.logger.info(f"Loaded {len(types_dict)} element types")
                return types_dict
                
            except Exception as e:
                self.logger.error(f"Failed to load element types: {e}")
                raise
    
    def get(self, type_id: str) -> Optional[ElementType]:
        """
        Get an element type by ID.
        
        Args:
            type_id: The type identifier
            
        Returns:
            ElementType instance if found, None otherwise
        """
        with self._lock:
            # Try cache first
            cached = self._get_from_cache(type_id)
            if cached:
                return cached
            
            # Load from database
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM element_types WHERE id = ? AND is_active = 1", (type_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        # Convert row to dictionary
                        column_names = [description[0] for description in cursor.description]
                        data = dict(zip(column_names, row))
                        
                        element_type = self._deserialize_from_storage(data)
                        self._add_to_cache(element_type)
                        return element_type
                    
                    return None
                    
            except Exception as e:
                self.logger.error(f"Failed to get type {type_id}: {e}")
                return None
    
    def list(self, category: Optional[str] = None, tags: Optional[List[str]] = None,
             search: Optional[str] = None, limit: Optional[int] = None,
             offset: Optional[int] = None, active_only: bool = True) -> List[ElementType]:
        """
        List element types with optional filtering.
        
        Args:
            category: Filter by category
            tags: Filter by tags (types must have all specified tags)
            search: Search in name, description, and tags
            limit: Maximum number of results to return
            offset: Number of results to skip
            active_only: Whether to only return active types
            
        Returns:
            List of matching ElementType instances
        """
        with self._lock:
            # Build query
            where_conditions = []
            params = []
            
            if active_only:
                where_conditions.append("is_active = 1")
            
            if category:
                where_conditions.append("category = ?")
                params.append(category)
            
            if search:
                where_conditions.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Add ordering
            order_clause = "ORDER BY usage_count DESC, created_at DESC"
            
            # Add limit and offset
            limit_clause = ""
            if limit:
                limit_clause += f" LIMIT {limit}"
                if offset:
                    limit_clause += f" OFFSET {offset}"
            elif offset:
                limit_clause = f" OFFSET {offset}"
            
            query = f"""
                SELECT * FROM element_types 
                {where_clause} 
                {order_clause}
                {limit_clause}
            """
            
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    
                    types = []
                    for row in cursor.fetchall():
                        column_names = [description[0] for description in cursor.description]
                        data = dict(zip(column_names, row))
                        
                        try:
                            element_type = self._deserialize_from_storage(data)
                            
                            # Filter by tags if specified
                            if tags:
                                type_tags = set(element_type.tags)
                                if not all(tag in type_tags for tag in tags):
                                    continue
                            
                            types.append(element_type)
                        except Exception as e:
                            self.logger.error(f"Failed to deserialize type {data.get('id', 'unknown')}: {e}")
                            continue
                
                return types
                
            except Exception as e:
                self.logger.error(f"Failed to list element types: {e}")
                return []
    
    def add(self, element_type: ElementType, validate_schema: bool = True) -> bool:
        """
        Add a new element type to the registry.
        
        Args:
            element_type: The element type to add
            validate_schema: Whether to validate the parameter schema
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            # Validate parameter schema if requested
            if validate_schema and element_type.param_schema:
                try:
                    validate_param_schema(element_type.param_schema)
                except ValueError as e:
                    self.logger.error(f"Parameter schema validation failed: {e}")
                    return False
            
            # Check if type already exists
            if self.get(element_type.id):
                self.logger.warning(f"Type {element_type.id} already exists")
                return False
            
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    data = self._serialize_for_storage(element_type)
                    
                    cursor.execute("""
                        INSERT INTO element_types 
                        (id, name, description, category, tags, render_strategy, param_schema,
                         variants, diversity_config, created_by, created_at, llm_prompt, llm_model,
                         version, parent_type_id, is_active, is_template, usage_count, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['id'], data['name'], data['description'], data['category'],
                        data['tags'], data['render_strategy'], data['param_schema'],
                        data['variants'], data['diversity_config'], data['created_by'],
                        data['created_at'], data['llm_prompt'], data['llm_model'],
                        data['version'], data['parent_type_id'], data['is_active'],
                        data['is_template'], data['usage_count'], data.get('metadata')
                    ))
                    
                    conn.commit()
                
                # Add to cache
                self._add_to_cache(element_type)
                
                self.logger.info(f"Added element type: {element_type.id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add element type {element_type.id}: {e}")
                return False
    
    def update(self, element_type: ElementType, validate_schema: bool = True) -> bool:
        """
        Update an existing element type.
        
        Args:
            element_type: The updated element type
            validate_schema: Whether to validate the parameter schema
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            # Validate parameter schema if requested
            if validate_schema and element_type.param_schema:
                try:
                    validate_param_schema(element_type.param_schema)
                except ValueError as e:
                    self.logger.error(f"Parameter schema validation failed: {e}")
                    return False
            
            # Update timestamp
            element_type.updated_at = datetime.now()
            
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    data = self._serialize_for_storage(element_type)
                    
                    cursor.execute("""
                        UPDATE element_types 
                        SET name = ?, description = ?, category = ?, tags = ?, 
                            render_strategy = ?, param_schema = ?, variants = ?,
                            diversity_config = ?, updated_at = ?, llm_prompt = ?,
                            llm_model = ?, version = ?, parent_type_id = ?,
                            is_active = ?, is_template = ?, usage_count = ?,
                            metadata = ?
                        WHERE id = ?
                    """, (
                        data['name'], data['description'], data['category'], data['tags'],
                        data['render_strategy'], data['param_schema'], data['variants'],
                        data['diversity_config'], data['updated_at'], data['llm_prompt'],
                        data['llm_model'], data['version'], data['parent_type_id'],
                        data['is_active'], data['is_template'], data['usage_count'],
                        data.get('metadata'), data['id']
                    ))
                    
                    if cursor.rowcount == 0:
                        self.logger.warning(f"No rows updated for type {element_type.id}")
                        return False
                    
                    conn.commit()
                
                # Update cache
                self._add_to_cache(element_type)
                
                self.logger.info(f"Updated element type: {element_type.id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to update element type {element_type.id}: {e}")
                return False
    
    def delete(self, type_id: str, soft_delete: bool = True) -> bool:
        """
        Delete an element type from the registry.
        
        Args:
            type_id: The type identifier to delete
            soft_delete: Whether to use soft delete (deactivate) or hard delete
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    
                    if soft_delete:
                        cursor.execute(
                            "UPDATE element_types SET is_active = 0, updated_at = ? WHERE id = ?",
                            (datetime.now(), type_id)
                        )
                    else:
                        cursor.execute("DELETE FROM element_types WHERE id = ?", (type_id,))
                    
                    if cursor.rowcount == 0:
                        self.logger.warning(f"No type found to delete: {type_id}")
                        return False
                    
                    conn.commit()
                
                # Remove from cache
                self._remove_from_cache(type_id)
                
                self.logger.info(f"Deleted element type: {type_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to delete element type {type_id}: {e}")
                return False
    
    def increment_usage(self, type_id: str) -> bool:
        """
        Increment usage count for a type and log usage.
        
        Args:
            type_id: The type identifier
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()
                    
                    # Increment usage count
                    cursor.execute(
                        "UPDATE element_types SET usage_count = usage_count + 1 WHERE id = ?",
                        (type_id,)
                    )
                    
                    if cursor.rowcount == 0:
                        return False
                    
                    conn.commit()
                
                # Update cache
                cached = self._get_from_cache(type_id)
                if cached:
                    cached.increment_usage()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to increment usage for type {type_id}: {e}")
                return False
    
    def get_usage_stats(self, type_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for types.
        
        Args:
            type_id: Specific type to get stats for, or None for all types
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                if type_id:
                    cursor.execute("""
                        SELECT usage_count, created_at, last_used
                        FROM element_types 
                        WHERE id = ?
                    """, (type_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'type_id': type_id,
                            'usage_count': row[0],
                            'created_at': row[1],
                            'last_used': row[2]
                        }
                    return {}
                
                else:
                    # Get overall statistics
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_types,
                            SUM(usage_count) as total_usage,
                            AVG(usage_count) as avg_usage,
                            MAX(usage_count) as max_usage,
                            COUNT(CASE WHEN is_active THEN 1 END) as active_types
                        FROM element_types
                    """)
                    
                    row = cursor.fetchone()
                    return {
                        'total_types': row[0],
                        'total_usage': row[1],
                        'avg_usage': row[2] or 0,
                        'max_usage': row[3] or 0,
                        'active_types': row[4]
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            return {}
    
    def search(self, query: str, limit: int = 50) -> List[ElementType]:
        """
        Search for element types using full-text search.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching ElementType instances
        """
        return self.list(search=query, limit=limit)
    
    def get_categories(self) -> List[str]:
        """
        Get all available categories.
        
        Returns:
            List of category names
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT category FROM element_types WHERE is_active = 1 ORDER BY category")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get categories: {e}")
            return []
    
    def get_tags(self, limit: Optional[int] = None) -> List[str]:
        """
        Get all available tags.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of unique tags
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                query = "SELECT tags FROM element_types WHERE is_active = 1"
                
                tags = set()
                for row in cursor.execute(query):
                    if row[0]:
                        type_tags = json.loads(row[0])
                        if isinstance(type_tags, list):
                            tags.update(type_tags)
                
                tag_list = sorted(list(tags))
                if limit:
                    return tag_list[:limit]
                return tag_list
                
        except Exception as e:
            self.logger.error(f"Failed to get tags: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                # Get basic counts
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_types,
                        COUNT(CASE WHEN is_active THEN 1 END) as active_types,
                        COUNT(CASE WHEN is_template THEN 1 END) as template_types,
                        SUM(usage_count) as total_usage
                    FROM element_types
                """)
                counts = cursor.fetchone()
                
                # Get category distribution
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM element_types 
                    WHERE is_active = 1
                    GROUP BY category
                    ORDER BY count DESC
                """)
                categories = dict(cursor.fetchall())
                
                # Get most used types
                cursor.execute("""
                    SELECT id, name, usage_count
                    FROM element_types 
                    WHERE is_active = 1
                    ORDER BY usage_count DESC
                    LIMIT 10
                """)
                top_types = [{'id': row[0], 'name': row[1], 'usage_count': row[2]} 
                           for row in cursor.fetchall()]
                
                return {
                    'total_types': counts[0],
                    'active_types': counts[1],
                    'template_types': counts[2],
                    'total_usage': counts[3],
                    'categories': categories,
                    'top_types': top_types,
                    'cache_size': len(self._type_cache),
                    'storage_path': self.storage_path
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        with self._lock:
            self._type_cache.clear()
            self._cache_order.clear()
            self.logger.info("Type registry cache cleared")
    
    def export_types(self, type_ids: Optional[List[str]] = None) -> str:
        """
        Export types to JSON format.
        
        Args:
            type_ids: Specific types to export, or None for all
            
        Returns:
            JSON string containing exported types
        """
        if type_ids:
            types = []
            for type_id in type_ids:
                element_type = self.get(type_id)
                if element_type:
                    types.append(element_type.dict())
        else:
            # Get all types
            all_types = self.load_all()
            types = [element_type.dict() for element_type in all_types.values()]
        
        return json.dumps(types, indent=2, default=str)
    
    def import_types(self, json_data: str, merge: bool = True) -> Tuple[int, List[str]]:
        """
        Import types from JSON format.
        
        Args:
            json_data: JSON string containing types
            merge: Whether to merge with existing types or replace
            
        Returns:
            Tuple of (success_count, error_messages)
        """
        try:
            types_data = json.loads(json_data)
            if not isinstance(types_data, list):
                raise ValueError("Expected a list of element types")
            
            success_count = 0
            errors = []
            
            for type_data in types_data:
                try:
                    element_type = ElementType(**type_data)
                    
                    if merge:
                        # Try to update existing, otherwise add new
                        if self.get(element_type.id):
                            if not self.update(element_type):
                                errors.append(f"Failed to update type {element_type.id}")
                            else:
                                success_count += 1
                        else:
                            if not self.add(element_type):
                                errors.append(f"Failed to add type {element_type.id}")
                            else:
                                success_count += 1
                    else:
                        # Replace existing
                        if self.get(element_type.id):
                            self.delete(element_type.id, soft_delete=False)
                        
                        if not self.add(element_type):
                            errors.append(f"Failed to add type {element_type.id}")
                        else:
                            success_count += 1
                
                except Exception as e:
                    errors.append(f"Failed to import type: {e}")
            
            self.logger.info(f"Imported {success_count} types with {len(errors)} errors")
            return success_count, errors
            
        except Exception as e:
            self.logger.error(f"Failed to import types: {e}")
            return 0, [str(e)]


# Global registry instance
_global_registry: Optional[TypeRegistry] = None


def get_type_registry() -> TypeRegistry:
    """Get the global type registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TypeRegistry()
    return _global_registry


def set_type_registry(registry: TypeRegistry) -> None:
    """Set the global type registry instance."""
    global _global_registry
    _global_registry = registry