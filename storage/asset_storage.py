"""
Asset Storage Backend

This module provides the SQLite-based storage backend for managing asset metadata,
including database operations, connection management, and data persistence.
"""

import os
import sqlite3
import json
import logging
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
from pathlib import Path
import threading
import time

from .metadata_schema import (
    AssetMetadata, AssetVersion, AssetRelationship, AssetAnalytics,
    MetadataQuery, MetadataStats, AssetFormat, AssetCategory, AssetStatus
)


class DatabaseConnection:
    """
    Context manager for database connections with proper error handling.
    """
    
    def __init__(self, db_path: str, timeout: float = 30.0):
        self.db_path = db_path
        self.timeout = timeout
        self._lock = threading.Lock()
    
    def __enter__(self):
        self._lock.acquire()
        try:
            self.conn = sqlite3.connect(
                self.db_path, 
                timeout=self.timeout,
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=10000")
            self.conn.execute("PRAGMA temp_store=memory")
            return self.conn
        except Exception as e:
            self._lock.release()
            raise e
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.conn.close()
            self._lock.release()


class AssetStorage:
    """
    SQLite-based storage backend for asset metadata management.
    
    Provides comprehensive CRUD operations, connection management, and
    database maintenance for the asset metadata system.
    """
    
    def __init__(self, db_path: str = "./storage/metadata.db"):
        """
        Initialize the asset storage backend.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database schema
        self._init_database()
        
        self.logger.info(f"AssetStorage initialized with database: {db_path}")
    
    def _init_database(self):
        """Initialize the database schema if it doesn't exist."""
        with DatabaseConnection(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create assets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    parent_id TEXT,
                    generator_type TEXT NOT NULL,
                    parameters TEXT,  -- JSON
                    seed INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    format TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    hash TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    category TEXT,
                    description TEXT,
                    author TEXT,
                    title TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed DATETIME,
                    download_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    is_favorite BOOLEAN DEFAULT 0,
                    related_assets TEXT,  -- JSON array
                    derived_from TEXT,
                    quality TEXT,
                    complexity REAL,
                    randomness REAL,
                    base_color TEXT,
                    color_palette TEXT,  -- JSON array
                    FOREIGN KEY (parent_id) REFERENCES assets(asset_id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_generator_type ON assets(generator_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_author ON assets(author)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_hash ON assets(hash)")
            
            # Create tags table for efficient tag searches
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
                    UNIQUE(asset_id, tag)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_tags_asset ON asset_tags(asset_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_tags_tag ON asset_tags(tag)")
            
            # Create asset relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON
                    FOREIGN KEY (source_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
                    UNIQUE(source_id, target_id, relationship_type)
                )
            """)
            
            # Create analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    download_count INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    average_rating REAL,
                    tags_searched TEXT,  -- JSON array
                    search_queries TEXT,  -- JSON array
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
                    UNIQUE(asset_id, date)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_asset ON asset_analytics(asset_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_date ON asset_analytics(date)")
            
            # Create full-text search virtual table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts USING fts5(
                    asset_id,
                    title,
                    description,
                    author,
                    generator_type,
                    tags,
                    category,
                    content='assets',
                    content_rowid='rowid'
                )
            """)
            
            conn.commit()
            
            self.logger.info("Database schema initialized successfully")
    
    def store_asset(self, metadata: AssetMetadata) -> bool:
        """
        Store or update an asset metadata record.
        
        Args:
            metadata: AssetMetadata to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if asset already exists
                cursor.execute("SELECT asset_id FROM assets WHERE asset_id = ?", (metadata.asset_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    cursor.execute("""
                        UPDATE assets SET
                            version = ?,
                            parent_id = ?,
                            generator_type = ?,
                            parameters = ?,
                            seed = ?,
                            updated_at = ?,
                            width = ?,
                            height = ?,
                            format = ?,
                            size_bytes = ?,
                            hash = ?,
                            tags = ?,
                            category = ?,
                            description = ?,
                            author = ?,
                            title = ?,
                            access_count = ?,
                            last_accessed = ?,
                            download_count = ?,
                            status = ?,
                            is_favorite = ?,
                            related_assets = ?,
                            derived_from = ?,
                            quality = ?,
                            complexity = ?,
                            randomness = ?,
                            base_color = ?,
                            color_palette = ?
                        WHERE asset_id = ?
                    """, (
                        metadata.version,
                        metadata.parent_id,
                        metadata.generator_type,
                        json.dumps(metadata.parameters),
                        metadata.seed,
                        metadata.updated_at.isoformat() + "Z",
                        metadata.width,
                        metadata.height,
                        metadata.format.value,
                        metadata.size_bytes,
                        metadata.hash,
                        json.dumps(metadata.tags),
                        metadata.category.value if metadata.category else None,
                        metadata.description,
                        metadata.author,
                        metadata.title,
                        metadata.access_count,
                        metadata.last_accessed.isoformat() + "Z" if metadata.last_accessed else None,
                        metadata.download_count,
                        metadata.status.value,
                        metadata.is_favorite,
                        json.dumps(metadata.related_assets),
                        metadata.derived_from,
                        metadata.quality,
                        metadata.complexity,
                        metadata.randomness,
                        metadata.base_color,
                        json.dumps(metadata.color_palette) if metadata.color_palette else None,
                        metadata.asset_id
                    ))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO assets (
                            asset_id, version, parent_id, generator_type, parameters, seed,
                            created_at, updated_at, width, height, format, size_bytes, hash,
                            tags, category, description, author, title, access_count,
                            last_accessed, download_count, status, is_favorite,
                            related_assets, derived_from, quality, complexity,
                            randomness, base_color, color_palette
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metadata.asset_id,
                        metadata.version,
                        metadata.parent_id,
                        metadata.generator_type,
                        json.dumps(metadata.parameters),
                        metadata.seed,
                        metadata.created_at.isoformat() + "Z",
                        metadata.updated_at.isoformat() + "Z",
                        metadata.width,
                        metadata.height,
                        metadata.format.value,
                        metadata.size_bytes,
                        metadata.hash,
                        json.dumps(metadata.tags),
                        metadata.category.value if metadata.category else None,
                        metadata.description,
                        metadata.author,
                        metadata.title,
                        metadata.access_count,
                        metadata.last_accessed.isoformat() + "Z" if metadata.last_accessed else None,
                        metadata.download_count,
                        metadata.status.value,
                        metadata.is_favorite,
                        json.dumps(metadata.related_assets),
                        metadata.derived_from,
                        metadata.quality,
                        metadata.complexity,
                        metadata.randomness,
                        metadata.base_color,
                        json.dumps(metadata.color_palette) if metadata.color_palette else None
                    ))
                
                # Update tags
                self._update_asset_tags(metadata.asset_id, metadata.tags, cursor)
                
                # Update FTS index
                self._update_fts_index(metadata, cursor)
                
                conn.commit()
                self.logger.info(f"Stored asset metadata: {metadata.asset_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing asset metadata: {e}")
            return False
    
    def get_asset(self, asset_id: str, include_deleted: bool = False) -> Optional[AssetMetadata]:
        """
        Retrieve asset metadata by asset ID.
        
        Args:
            asset_id: Asset ID to retrieve
            include_deleted: Whether to include deleted assets
            
        Returns:
            AssetMetadata if found, None otherwise
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM assets WHERE asset_id = ?"
                params = [asset_id]
                
                if not include_deleted:
                    query += " AND status != 'deleted'"
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return self._row_to_asset_metadata(row)
                
        except Exception as e:
            self.logger.error(f"Error retrieving asset metadata: {e}")
            return None
    
    def get_assets_by_query(self, query: MetadataQuery) -> Tuple[List[AssetMetadata], int]:
        """
        Search assets using metadata query.
        
        Args:
            query: MetadataQuery with search criteria
            
        Returns:
            Tuple of (asset list, total count)
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic query
                where_conditions = []
                params = []
                
                # Text search in FTS
                if query.text:
                    where_conditions.append("assets.asset_id IN (SELECT asset_id FROM assets_fts WHERE assets_fts MATCH ?)")
                    params.append(query.text)
                
                # Tag filter
                if query.tags:
                    tag_placeholders = ",".join("?" * len(query.tags))
                    where_conditions.append(f"""
                        assets.asset_id IN (
                            SELECT asset_id FROM asset_tags 
                            WHERE tag IN ({tag_placeholders})
                            GROUP BY asset_id 
                            HAVING COUNT(DISTINCT tag) = {len(query.tags)}
                        )
                    """)
                    params.extend(query.tags)
                
                # Category filter
                if query.category:
                    where_conditions.append("assets.category = ?")
                    params.append(query.category.value)
                
                # Generator type filter
                if query.generator_type:
                    where_conditions.append("assets.generator_type = ?")
                    params.append(query.generator_type)
                
                # Author filter
                if query.author:
                    where_conditions.append("assets.author = ?")
                    params.append(query.author)
                
                # Date range filter
                if query.date_from:
                    where_conditions.append("assets.created_at >= ?")
                    params.append(query.date_from.isoformat() + "Z")
                
                if query.date_to:
                    where_conditions.append("assets.created_at <= ?")
                    params.append(query.date_to.isoformat() + "Z")
                
                # Dimension filters
                if query.width_min:
                    where_conditions.append("assets.width >= ?")
                    params.append(query.width_min)
                
                if query.width_max:
                    where_conditions.append("assets.width <= ?")
                    params.append(query.width_max)
                
                if query.height_min:
                    where_conditions.append("assets.height >= ?")
                    params.append(query.height_min)
                
                if query.height_max:
                    where_conditions.append("assets.height <= ?")
                    params.append(query.height_max)
                
                # Status filter
                if query.status:
                    where_conditions.append("assets.status = ?")
                    params.append(query.status.value)
                
                # Favorite filter
                if query.is_favorite is not None:
                    where_conditions.append("assets.is_favorite = ?")
                    params.append(query.is_favorite)
                
                # Exclude deleted by default
                where_conditions.append("assets.status != 'deleted'")
                
                # Build WHERE clause
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # Count total results
                count_query = f"SELECT COUNT(*) as total FROM assets WHERE {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # Get paginated results
                order_direction = "DESC" if query.sort_order == "desc" else "ASC"
                order_field = query.sort_by if query.sort_by in [
                    'created_at', 'updated_at', 'title', 'generator_type', 'category', 'author'
                ] else 'created_at'
                
                data_query = f"""
                    SELECT assets.* FROM assets 
                    WHERE {where_clause}
                    ORDER BY assets.{order_field} {order_direction}
                    LIMIT ? OFFSET ?
                """
                
                params.extend([query.limit, query.offset])
                cursor.execute(data_query, params)
                rows = cursor.fetchall()
                
                assets = [self._row_to_asset_metadata(row) for row in rows]
                
                return assets, total
                
        except Exception as e:
            self.logger.error(f"Error searching assets: {e}")
            return [], 0
    
    def delete_asset(self, asset_id: str, permanent: bool = False) -> bool:
        """
        Delete or soft-delete an asset.
        
        Args:
            asset_id: Asset ID to delete
            permanent: Whether to permanently delete or soft-delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                if permanent:
                    # Hard delete
                    cursor.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
                    cursor.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
                    cursor.execute("DELETE FROM asset_analytics WHERE asset_id = ?", (asset_id,))
                    cursor.execute("DELETE FROM assets_fts WHERE asset_id = ?", (asset_id,))
                else:
                    # Soft delete
                    cursor.execute("UPDATE assets SET status = 'deleted' WHERE asset_id = ?", (asset_id,))
                
                conn.commit()
                self.logger.info(f"{'Permanently deleted' if permanent else 'Soft deleted'} asset: {asset_id}")
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error deleting asset: {e}")
            return False
    
    def update_asset_metadata(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields of an asset metadata.
        
        Args:
            asset_id: Asset ID to update
            updates: Dictionary of field updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if asset exists
                cursor.execute("SELECT asset_id FROM assets WHERE asset_id = ? AND status != 'deleted'", (asset_id,))
                if not cursor.fetchone():
                    return False
                
                # Build update query
                allowed_fields = {
                    'title', 'description', 'author', 'tags', 'category', 
                    'is_favorite', 'status', 'related_assets', 'quality',
                    'complexity', 'randomness', 'base_color', 'color_palette'
                }
                
                set_clauses = []
                params = []
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        if field == 'tags' and isinstance(value, list):
                            set_clauses.append("tags = ?")
                            params.append(json.dumps(value))
                            # Update tags table
                            cursor.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
                            for tag in value:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO asset_tags (asset_id, tag) VALUES (?, ?)",
                                    (asset_id, tag)
                                )
                        elif field == 'related_assets' and isinstance(value, list):
                            set_clauses.append("related_assets = ?")
                            params.append(json.dumps(value))
                        elif field == 'color_palette' and isinstance(value, list):
                            set_clauses.append("color_palette = ?")
                            params.append(json.dumps(value))
                        elif field in ['category', 'status'] and value is not None:
                            set_clauses.append(f"{field} = ?")
                            params.append(value.value if hasattr(value, 'value') else value)
                        elif field in ['quality', 'description', 'author', 'title', 'base_color']:
                            set_clauses.append(f"{field} = ?")
                            params.append(value)
                        elif field in ['is_favorite'] and isinstance(value, bool):
                            set_clauses.append(f"{field} = ?")
                            params.append(value)
                        elif field in ['complexity', 'randomness'] and isinstance(value, (int, float)):
                            set_clauses.append(f"{field} = ?")
                            params.append(value)
                
                if not set_clauses:
                    return False
                
                # Add updated_at timestamp
                set_clauses.append("updated_at = ?")
                params.append(datetime.utcnow().isoformat() + "Z")
                params.append(asset_id)
                
                query = f"UPDATE assets SET {', '.join(set_clauses)} WHERE asset_id = ?"
                cursor.execute(query, params)
                
                # Update FTS index
                cursor.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
                row = cursor.fetchone()
                if row:
                    self._update_fts_index(self._row_to_asset_metadata(row), cursor)
                
                conn.commit()
                self.logger.info(f"Updated asset metadata: {asset_id}")
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error updating asset metadata: {e}")
            return False
    
    def increment_access_count(self, asset_id: str) -> bool:
        """
        Increment the access count for an asset.
        
        Args:
            asset_id: Asset ID to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE assets 
                    SET access_count = access_count + 1, 
                        last_accessed = ?
                    WHERE asset_id = ? AND status != 'deleted'
                """, (datetime.utcnow().isoformat() + "Z", asset_id))
                
                # Update analytics
                today = datetime.utcnow().date()
                cursor.execute("""
                    INSERT OR REPLACE INTO asset_analytics 
                    (asset_id, date, access_count, download_count, unique_users, created_at, updated_at)
                    VALUES (?, ?, 
                        COALESCE((SELECT access_count FROM asset_analytics WHERE asset_id = ? AND date = ?), 0) + 1,
                        COALESCE((SELECT download_count FROM asset_analytics WHERE asset_id = ? AND date = ?), 0),
                        COALESCE((SELECT unique_users FROM asset_analytics WHERE asset_id = ? AND date = ?), 0),
                        ?, ?
                    )
                """, (
                    asset_id, today.isoformat(),
                    asset_id, today.isoformat(),
                    asset_id, today.isoformat(), 
                    asset_id, today.isoformat(),
                    datetime.utcnow().isoformat() + "Z",
                    datetime.utcnow().isoformat() + "Z"
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error incrementing access count: {e}")
            return False
    
    def get_stats(self) -> MetadataStats:
        """
        Get comprehensive metadata system statistics.
        
        Returns:
            MetadataStats object with system statistics
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) as count FROM assets WHERE status != 'deleted'")
                total_assets = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM assets")
                total_versions = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(DISTINCT tag) as count FROM asset_tags")
                total_tags = cursor.fetchone()['count']
                
                # Storage metrics
                cursor.execute("SELECT SUM(size_bytes) as total FROM assets WHERE status != 'deleted'")
                storage_result = cursor.fetchone()
                total_storage_bytes = storage_result['total'] or 0
                
                cursor.execute("SELECT AVG(size_bytes) as avg FROM assets WHERE status != 'deleted'")
                avg_result = cursor.fetchone()
                average_file_size = float(avg_result['avg'] or 0)
                
                # Category breakdown
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM assets 
                    WHERE status != 'deleted' AND category IS NOT NULL
                    GROUP BY category
                """)
                assets_by_category = {row['category']: row['count'] for row in cursor.fetchall()}
                
                # Generator breakdown
                cursor.execute("""
                    SELECT generator_type, COUNT(*) as count 
                    FROM assets 
                    WHERE status != 'deleted'
                    GROUP BY generator_type
                """)
                assets_by_generator = {row['generator_type']: row['count'] for row in cursor.fetchall()}
                
                # Popular tags
                cursor.execute("""
                    SELECT tag, COUNT(*) as count 
                    FROM asset_tags 
                    GROUP BY tag 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                most_popular_tags = [
                    {"tag": row['tag'], "count": row['count']} 
                    for row in cursor.fetchall()
                ]
                
                # Recent activity
                cursor.execute("""
                    SELECT asset_id, title, generator_type, created_at 
                    FROM assets 
                    WHERE status != 'deleted'
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                recent_activity = [
                    {
                        "asset_id": row['asset_id'],
                        "title": row['title'] or f"{row['generator_type']}_{row['asset_id'][:8]}",
                        "generator_type": row['generator_type'],
                        "created_at": row['created_at']
                    }
                    for row in cursor.fetchall()
                ]
                
                # Database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return MetadataStats(
                    total_assets=total_assets,
                    total_versions=total_versions,
                    total_tags=total_tags,
                    assets_by_category=assets_by_category,
                    assets_by_generator=assets_by_generator,
                    total_storage_bytes=total_storage_bytes,
                    average_file_size=average_file_size,
                    most_popular_tags=most_popular_tags,
                    recent_activity=recent_activity,
                    database_size_bytes=db_size
                )
                
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return MetadataStats(
                total_assets=0, total_versions=0, total_tags=0,
                assets_by_category={}, assets_by_generator={},
                total_storage_bytes=0, average_file_size=0,
                most_popular_tags=[], recent_activity=[], database_size_bytes=0
            )
    
    def _row_to_asset_metadata(self, row) -> AssetMetadata:
        """Convert database row to AssetMetadata object."""
        return AssetMetadata(
            asset_id=row['asset_id'],
            version=row['version'],
            parent_id=row['parent_id'],
            generator_type=row['generator_type'],
            parameters=json.loads(row['parameters']) if row['parameters'] else {},
            seed=row['seed'],
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')),
            width=row['width'],
            height=row['height'],
            format=AssetFormat(row['format']),
            size_bytes=row['size_bytes'],
            hash=row['hash'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            category=AssetCategory(row['category']) if row['category'] else None,
            description=row['description'],
            author=row['author'],
            title=row['title'],
            access_count=row['access_count'],
            last_accessed=datetime.fromisoformat(row['last_accessed'].replace('Z', '+00:00')) if row['last_accessed'] else None,
            download_count=row['download_count'],
            status=AssetStatus(row['status']),
            is_favorite=bool(row['is_favorite']),
            related_assets=json.loads(row['related_assets']) if row['related_assets'] else [],
            derived_from=row['derived_from'],
            quality=row['quality'],
            complexity=row['complexity'],
            randomness=row['randomness'],
            base_color=row['base_color'],
            color_palette=json.loads(row['color_palette']) if row['color_palette'] else None
        )
    
    def _update_asset_tags(self, asset_id: str, tags: List[str], cursor):
        """Update the tags table for an asset."""
        # Remove existing tags
        cursor.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
        
        # Add new tags
        for tag in tags:
            if tag.strip():  # Skip empty tags
                cursor.execute(
                    "INSERT OR IGNORE INTO asset_tags (asset_id, tag) VALUES (?, ?)",
                    (asset_id, tag.strip())
                )
    
    def _update_fts_index(self, metadata: AssetMetadata, cursor):
        """Update the full-text search index for an asset."""
        # Delete existing entry
        cursor.execute("DELETE FROM assets_fts WHERE asset_id = ?", (metadata.asset_id,))
        
        # Insert new entry
        cursor.execute("""
            INSERT INTO assets_fts (asset_id, title, description, author, generator_type, tags, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.asset_id,
            metadata.title or "",
            metadata.description or "",
            metadata.author or "",
            metadata.generator_type,
            " ".join(metadata.tags),
            metadata.category.value if metadata.category else ""
        ))
    
    def vacuum_database(self) -> bool:
        """
        Optimize the database by running VACUUM.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
                self.logger.info("Database vacuum completed successfully")
                return True
        except Exception as e:
            self.logger.error(f"Error during database vacuum: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path to save the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with DatabaseConnection(self.db_path) as conn:
                # Create backup using SQLite's backup API
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating database backup: {e}")
            return False