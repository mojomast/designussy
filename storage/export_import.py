"""
Export/Import System for Asset Metadata

This module provides comprehensive export and import capabilities for asset metadata,
including JSON export, bulk import, backup/restore functionality, and migration utilities.
"""

import os
import json
import csv
import zipfile
import shutil
import logging
import sqlite3
import enum
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union, BinaryIO
from pathlib import Path
from dataclasses import asdict
import tempfile

from .metadata_schema import AssetMetadata, MetadataStats
from .asset_storage import AssetStorage
from .tag_manager import TagManager


class ExportFormat(str, enum.Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    ZIP = "zip"


class ImportResult:
    """Result of an import operation."""
    def __init__(self):
        self.successful_imports = 0
        self.failed_imports = 0
        self.errors = []
        self.warnings = []
        self.duplicates_skipped = 0
        self.new_tags_created = 0
        self.new_assets_created = 0


class MetadataExporter:
    """
    Export system for asset metadata.
    
    Provides various export formats and backup capabilities.
    """
    
    def __init__(self, storage: AssetStorage, tag_manager: TagManager):
        """
        Initialize the metadata exporter.
        
        Args:
            storage: AssetStorage instance
            tag_manager: TagManager instance
        """
        self.storage = storage
        self.tag_manager = tag_manager
        self.logger = logging.getLogger(__name__)
        
        # Export configuration
        self.export_dir = os.getenv('METADATA_EXPORT_DIR', './backups')
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_to_json(self, output_path: str, include_deleted: bool = False,
                      asset_ids: Optional[List[str]] = None,
                      include_stats: bool = True) -> bool:
        """
        Export metadata to JSON format.
        
        Args:
            output_path: Path to save the JSON export
            include_deleted: Whether to include deleted assets
            asset_ids: Specific asset IDs to export (None for all)
            include_stats: Whether to include system statistics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                'metadata': {
                    'version': '1.0',
                    'export_date': datetime.utcnow().isoformat() + 'Z',
                    'export_type': 'full_metadata'
                },
                'assets': [],
                'tags': [],
                'relationships': []
            }
            
            # Export assets
            if asset_ids:
                # Export specific assets
                for asset_id in asset_ids:
                    asset = self.storage.get_asset(asset_id, include_deleted=include_deleted)
                    if asset:
                        export_data['assets'].append(asset.to_dict())
            else:
                # Export all assets with pagination
                from .metadata_schema import MetadataQuery, AssetStatus
                
                query = MetadataQuery(
                    status=None if include_deleted else AssetStatus.ACTIVE,
                    limit=1000,
                    offset=0,
                    sort_by="created_at",
                    sort_order="asc"
                )
                
                offset = 0
                while True:
                    query.offset = offset
                    assets, total = self.storage.get_assets_by_query(query)
                    
                    if not assets:
                        break
                    
                    for asset in assets:
                        export_data['assets'].append(asset.to_dict())
                    
                    offset += len(assets)
                    if offset >= total:
                        break
            
            # Export tag relationships
            export_data['tags'] = self._export_tag_relationships()
            
            # Export asset relationships
            export_data['relationships'] = self._export_asset_relationships()
            
            # Include statistics if requested
            if include_stats:
                export_data['statistics'] = self.storage.get_stats().__dict__
                export_data['tag_statistics'] = self.tag_manager.get_tag_statistics()
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Exported {len(export_data['assets'])} assets to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def export_to_csv(self, output_path: str, include_deleted: bool = False) -> bool:
        """
        Export metadata to CSV format.
        
        Args:
            output_path: Path to save the CSV export
            include_deleted: Whether to include deleted assets
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from .metadata_schema import MetadataQuery, AssetStatus
            
            query = MetadataQuery(
                status=None if include_deleted else AssetStatus.ACTIVE,
                limit=1000,
                offset=0,
                sort_by="created_at",
                sort_order="asc"
            )
            
            assets, total = self.storage.get_assets_by_query(query)
            
            if not assets:
                return False
            
            # Define CSV headers
            headers = [
                'asset_id', 'version', 'parent_id', 'generator_type', 'parameters',
                'seed', 'created_at', 'updated_at', 'width', 'height', 'format',
                'size_bytes', 'hash', 'tags', 'category', 'description', 'author',
                'title', 'access_count', 'download_count', 'status', 'is_favorite',
                'related_assets', 'derived_from', 'quality', 'complexity',
                'randomness', 'base_color', 'color_palette'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for asset in assets:
                    row_data = asset.to_dict()
                    
                    # Convert complex fields to JSON strings
                    for field in ['parameters', 'tags', 'related_assets', 'color_palette']:
                        if field in row_data and row_data[field] is not None:
                            row_data[field] = json.dumps(row_data[field])
                    
                    writer.writerow({key: str(value) for key, value in row_data.items()})
            
            self.logger.info(f"Exported {len(assets)} assets to CSV: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def create_backup(self, backup_name: Optional[str] = None, 
                     include_deleted: bool = False) -> Optional[str]:
        """
        Create a complete backup of the metadata system.
        
        Args:
            backup_name: Optional custom backup name
            include_deleted: Whether to include deleted assets
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            # Generate backup name if not provided
            if not backup_name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_name = f"metadata_backup_{timestamp}"
            
            # Create backup directory
            backup_dir = os.path.join(self.export_dir, backup_name)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup database file
            db_backup_path = os.path.join(backup_dir, "metadata.db")
            if os.path.exists(self.storage.db_path):
                shutil.copy2(self.storage.db_path, db_backup_path)
            
            # Export metadata as JSON
            json_export_path = os.path.join(backup_dir, "export.json")
            self.export_to_json(json_export_path, include_deleted=include_deleted)
            
            # Create ZIP archive
            zip_path = os.path.join(self.export_dir, f"{backup_name}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temporary directory
            shutil.rmtree(backup_dir)
            
            # Create backup info file
            backup_info = {
                'backup_name': backup_name,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'database_size': os.path.getsize(db_backup_path) if os.path.exists(db_backup_path) else 0,
                'include_deleted': include_deleted
            }
            
            info_path = zip_path + '.info.json'
            with open(info_path, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.logger.info(f"Created backup: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for file in os.listdir(self.export_dir):
                if file.endswith('.zip'):
                    info_file = os.path.join(self.export_dir, file + '.info.json')
                    
                    backup_info = {
                        'name': file[:-4],  # Remove .zip extension
                        'file_path': os.path.join(self.export_dir, file),
                        'created_at': None,
                        'size_bytes': 0,
                        'database_size': 0,
                        'include_deleted': False
                    }
                    
                    # Read backup info if available
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r') as f:
                                info_data = json.load(f)
                                backup_info.update(info_data)
                        except Exception:
                            pass
                    
                    # Get file size
                    try:
                        backup_info['size_bytes'] = os.path.getsize(backup_info['file_path'])
                    except Exception:
                        pass
                    
                    backups.append(backup_info)
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'] or '', reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def _export_tag_relationships(self) -> List[Dict[str, Any]]:
        """Export tag relationships and metadata."""
        try:
            from .asset_storage import DatabaseConnection
            
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT tag, COUNT(*) as usage_count
                    FROM asset_tags
                    GROUP BY tag
                    ORDER BY usage_count DESC
                """)
                
                tag_data = []
                for row in cursor.fetchall():
                    tag_info = self.tag_manager.get_tag_info(row['tag'])
                    if tag_info:
                        tag_data.append(asdict(tag_info))
                
                return tag_data
                
        except Exception as e:
            self.logger.error(f"Error exporting tag relationships: {e}")
            return []
    
    def _export_asset_relationships(self) -> List[Dict[str, Any]]:
        """Export asset relationships."""
        try:
            from .asset_storage import DatabaseConnection
            
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT source_id, target_id, relationship_type, created_at, metadata
                    FROM asset_relationships
                    ORDER BY created_at DESC
                """)
                
                relationships = []
                for row in cursor.fetchall():
                    relationships.append({
                        'source_id': row['source_id'],
                        'target_id': row['target_id'],
                        'relationship_type': row['relationship_type'],
                        'created_at': row['created_at'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    })
                
                return relationships
                
        except Exception as e:
            self.logger.error(f"Error exporting asset relationships: {e}")
            return []


class MetadataImporter:
    """
    Import system for asset metadata.
    
    Provides various import capabilities and data validation.
    """
    
    def __init__(self, storage: AssetStorage, tag_manager: TagManager):
        """
        Initialize the metadata importer.
        
        Args:
            storage: AssetStorage instance
            tag_manager: TagManager instance
        """
        self.storage = storage
        self.tag_manager = tag_manager
        self.logger = logging.getLogger(__name__)
        
        # Import configuration
        self.validate_imports = os.getenv('VALIDATE_IMPORTS', 'true').lower() == 'true'
        self.skip_duplicates = os.getenv('SKIP_DUPLICATES', 'true').lower() == 'true'
        self.merge_tags = os.getenv('MERGE_TAGS', 'false').lower() == 'true'
    
    def import_from_json(self, input_path: str, overwrite_existing: bool = False,
                        validate_only: bool = False) -> ImportResult:
        """
        Import metadata from JSON file.
        
        Args:
            input_path: Path to JSON file
            overwrite_existing: Whether to overwrite existing assets
            validate_only: Only validate without importing
            
        Returns:
            ImportResult with import statistics
        """
        result = ImportResult()
        
        try:
            # Load JSON data
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'assets' not in data:
                result.errors.append("Invalid JSON format: missing 'assets' key")
                return result
            
            # Validate and import assets
            for asset_data in data['assets']:
                try:
                    if validate_only:
                        # Just validate the asset data
                        asset = AssetMetadata.from_dict(asset_data)
                        is_valid, errors = self._validate_asset(asset)
                        if not is_valid:
                            result.errors.extend([f"Asset {asset.asset_id}: {error}" for error in errors])
                            result.failed_imports += 1
                        else:
                            result.successful_imports += 1
                    else:
                        # Actually import the asset
                        import_result = self._import_asset(asset_data, overwrite_existing)
                        if import_result['success']:
                            result.successful_imports += 1
                            if import_result['new_asset']:
                                result.new_assets_created += 1
                        else:
                            result.failed_imports += 1
                            if 'error' in import_result:
                                result.errors.append(f"Asset {asset_data.get('asset_id', 'unknown')}: {import_result['error']}")
                        result.duplicates_skipped += import_result.get('duplicates_skipped', 0)
                        
                except Exception as e:
                    result.failed_imports += 1
                    result.errors.append(f"Failed to import asset {asset_data.get('asset_id', 'unknown')}: {str(e)}")
            
            # Import tags if available
            if 'tags' in data and not validate_only:
                tag_result = self._import_tags(data['tags'])
                result.new_tags_created += tag_result['new_tags']
                result.errors.extend(tag_result['errors'])
                result.warnings.extend(tag_result['warnings'])
            
            # Import relationships if available
            if 'relationships' in data and not validate_only:
                rel_result = self._import_relationships(data['relationships'])
                result.errors.extend(rel_result['errors'])
            
        except Exception as e:
            result.errors.append(f"Failed to load JSON file: {str(e)}")
        
        return result
    
    def import_from_csv(self, input_path: str, overwrite_existing: bool = False) -> ImportResult:
        """
        Import metadata from CSV file.
        
        Args:
            input_path: Path to CSV file
            overwrite_existing: Whether to overwrite existing assets
            
        Returns:
            ImportResult with import statistics
        """
        result = ImportResult()
        
        try:
            with open(input_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        # Parse JSON fields
                        for field in ['parameters', 'tags', 'related_assets', 'color_palette']:
                            if field in row and row[field]:
                                try:
                                    row[field] = json.loads(row[field])
                                except json.JSONDecodeError:
                                    row[field] = None
                        
                        # Import the asset
                        import_result = self._import_asset(row, overwrite_existing)
                        if import_result['success']:
                            result.successful_imports += 1
                            if import_result['new_asset']:
                                result.new_assets_created += 1
                        else:
                            result.failed_imports += 1
                            if 'error' in import_result:
                                result.errors.append(f"Asset {row.get('asset_id', 'unknown')}: {import_result['error']}")
                        
                        result.duplicates_skipped += import_result.get('duplicates_skipped', 0)
                        
                    except Exception as e:
                        result.failed_imports += 1
                        result.errors.append(f"Failed to import asset {row.get('asset_id', 'unknown')}: {str(e)}")
                        
        except Exception as e:
            result.errors.append(f"Failed to load CSV file: {str(e)}")
        
        return result
    
    def restore_backup(self, backup_path: str, restore_only_missing: bool = True,
                      validate_only: bool = False) -> ImportResult:
        """
        Restore from a backup file.
        
        Args:
            backup_path: Path to backup file
            restore_only_missing: Only restore assets that don't exist
            validate_only: Only validate without restoring
            
        Returns:
            ImportResult with restore statistics
        """
        result = ImportResult()
        
        try:
            # Extract backup to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Look for export.json file
                export_files = ['export.json', 'metadata/export.json']
                json_path = None
                
                for export_file in export_files:
                    potential_path = os.path.join(temp_dir, export_file)
                    if os.path.exists(potential_path):
                        json_path = potential_path
                        break
                
                if not json_path:
                    result.errors.append("No export.json found in backup")
                    return result
                
                # Import from JSON
                result = self.import_from_json(json_path, 
                                             overwrite_existing=not restore_only_missing,
                                             validate_only=validate_only)
                
        except Exception as e:
            result.errors.append(f"Failed to restore backup: {str(e)}")
        
        return result
    
    def _import_asset(self, asset_data: Dict[str, Any], overwrite_existing: bool) -> Dict[str, Any]:
        """Import a single asset from data."""
        try:
            # Check if asset already exists
            asset_id = asset_data.get('asset_id')
            if not asset_id:
                return {'success': False, 'error': 'Missing asset_id'}
            
            existing_asset = self.storage.get_asset(asset_id)
            
            if existing_asset and not overwrite_existing:
                if self.skip_duplicates:
                    return {
                        'success': True, 
                        'new_asset': False, 
                        'duplicates_skipped': 1
                    }
                else:
                    return {
                        'success': False, 
                        'error': f"Asset {asset_id} already exists"
                    }
            
            # Create AssetMetadata object
            asset = AssetMetadata.from_dict(asset_data)
            
            # Validate asset if configured
            if self.validate_imports:
                is_valid, errors = self._validate_asset(asset)
                if not is_valid:
                    return {'success': False, 'error': f"Validation failed: {'; '.join(errors)}"}
            
            # Store asset
            success = self.storage.store_asset(asset)
            
            if success:
                return {
                    'success': True,
                    'new_asset': existing_asset is None,
                    'duplicates_skipped': 0
                }
            else:
                return {'success': False, 'error': 'Failed to store asset'}
                
        except Exception as e:
            return {'success': False, 'error': f"Import error: {str(e)}"}
    
    def _validate_asset(self, asset: AssetMetadata) -> Tuple[bool, List[str]]:
        """Validate an asset before import."""
        errors = []
        
        # Basic validation
        if not asset.asset_id:
            errors.append("Missing asset_id")
        
        if not asset.generator_type:
            errors.append("Missing generator_type")
        
        if asset.width <= 0 or asset.height <= 0:
            errors.append("Invalid dimensions")
        
        if not asset.hash:
            errors.append("Missing content hash")
        
        # Tag validation
        if asset.tags:
            valid_tags, invalid_tags = self.tag_manager.validate_tags(asset.tags)
            if invalid_tags:
                errors.append(f"Invalid tags: {invalid_tags}")
        
        return len(errors) == 0, errors
    
    def _import_tags(self, tag_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import tag metadata."""
        result = {'new_tags': 0, 'errors': [], 'warnings': []}
        
        try:
            for tag_info_data in tag_data:
                try:
                    # Check if tag exists
                    existing_info = self.tag_manager.get_tag_info(tag_info_data['name'])
                    
                    if existing_info:
                        result['warnings'].append(f"Tag '{tag_info_data['name']}' already exists")
                        if self.merge_tags:
                            # Could merge tag information here
                            pass
                    else:
                        # Tag doesn't exist, but we can't create it without associated assets
                        result['new_tags'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"Failed to import tag info: {str(e)}")
                    
        except Exception as e:
            result['errors'].append(f"Failed to import tags: {str(e)}")
        
        return result
    
    def _import_relationships(self, relationship_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import asset relationships."""
        result = {'errors': []}
        
        try:
            from .asset_storage import DatabaseConnection
            
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                for rel_data in relationship_data:
                    try:
                        # Validate that both assets exist
                        source_exists = self.storage.get_asset(rel_data['source_id']) is not None
                        target_exists = self.storage.get_asset(rel_data['target_id']) is not None
                        
                        if source_exists and target_exists:
                            # Insert relationship
                            cursor.execute("""
                                INSERT OR IGNORE INTO asset_relationships 
                                (source_id, target_id, relationship_type, created_at, metadata)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                rel_data['source_id'],
                                rel_data['target_id'],
                                rel_data['relationship_type'],
                                rel_data['created_at'],
                                json.dumps(rel_data.get('metadata', {}))
                            ))
                        else:
                            result['errors'].append(
                                f"Cannot create relationship: source or target asset not found"
                            )
                            
                    except Exception as e:
                        result['errors'].append(f"Failed to import relationship: {str(e)}")
                        
                conn.commit()
                
        except Exception as e:
            result['errors'].append(f"Failed to import relationships: {str(e)}")
        
        return result


class MigrationManager:
    """
    Migration utilities for schema changes and data transformations.
    """
    
    def __init__(self, storage: AssetStorage):
        """
        Initialize the migration manager.
        
        Args:
            storage: AssetStorage instance
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        
        # Migration tracking
        self.migration_log = os.path.join(os.path.dirname(storage.db_path), 'migrations.log')
    
    def create_migration_backup(self, migration_name: str) -> str:
        """
        Create a backup before applying migrations.
        
        Args:
            migration_name: Name of the migration
            
        Returns:
            Path to backup file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_migration_{migration_name}_{timestamp}"
        
        exporter = MetadataExporter(self.storage, None)
        backup_path = exporter.create_backup(backup_name)
        
        # Log the backup creation
        self._log_migration(f"Created pre-migration backup: {backup_path}")
        
        return backup_path
    
    def apply_migration(self, migration_func, migration_name: str, 
                       backup: bool = True) -> bool:
        """
        Apply a migration function with backup and rollback support.
        
        Args:
            migration_func: Function to apply the migration
            migration_name: Name of the migration
            backup: Whether to create backup before migration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = None
            
            if backup:
                backup_path = self.create_migration_backup(migration_name)
                if not backup_path:
                    self.logger.error("Failed to create migration backup")
                    return False
            
            # Apply migration
            success = migration_func()
            
            if success:
                self._log_migration(f"Applied migration: {migration_name}")
                self.logger.info(f"Migration {migration_name} completed successfully")
            else:
                self._log_migration(f"Migration failed: {migration_name}")
                self.logger.error(f"Migration {migration_name} failed")
                
                # Rollback from backup if available
                if backup_path and os.path.exists(backup_path):
                    self.logger.info("Attempting rollback from backup")
                    try:
                        importer = MetadataImporter(self.storage, None)
                        result = importer.restore_backup(backup_path)
                        if result.successful_imports > 0:
                            self.logger.info("Rollback completed successfully")
                        else:
                            self.logger.error("Rollback failed")
                    except Exception as e:
                        self.logger.error(f"Rollback failed: {e}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error applying migration {migration_name}: {e}")
            return False
    
    def _log_migration(self, message: str):
        """Log migration activity."""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            log_entry = f"[{timestamp}] {message}\n"
            
            with open(self.migration_log, 'a') as f:
                f.write(log_entry)
                
        except Exception:
            pass  # Don't fail migration if logging fails
    
    def get_migration_history(self) -> List[Dict[str, str]]:
        """
        Get migration history.
        
        Returns:
            List of migration records
        """
        migrations = []
        
        try:
            if os.path.exists(self.migration_log):
                with open(self.migration_log, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # Parse log entry
                            if line.startswith('[') and '] ' in line:
                                timestamp_part, message = line.split('] ', 1)
                                timestamp = timestamp_part[1:]  # Remove '['
                                
                                migrations.append({
                                    'timestamp': timestamp,
                                    'message': message
                                })
                                
        except Exception as e:
            self.logger.error(f"Error reading migration history: {e}")
        
        return sorted(migrations, key=lambda x: x['timestamp'])


# Utility functions

def get_exporter(storage: AssetStorage, tag_manager: TagManager) -> MetadataExporter:
    """Get a configured metadata exporter."""
    return MetadataExporter(storage, tag_manager)


def get_importer(storage: AssetStorage, tag_manager: TagManager) -> MetadataImporter:
    """Get a configured metadata importer."""
    return MetadataImporter(storage, tag_manager)


def get_migration_manager(storage: AssetStorage) -> MigrationManager:
    """Get a configured migration manager."""
    return MigrationManager(storage)


def create_full_backup(storage: AssetStorage, tag_manager: TagManager, 
                      backup_name: Optional[str] = None) -> Optional[str]:
    """Create a complete system backup."""
    exporter = MetadataExporter(storage, tag_manager)
    return exporter.create_backup(backup_name)


def restore_from_backup(storage: AssetStorage, tag_manager: TagManager,
                       backup_path: str, restore_only_missing: bool = True) -> ImportResult:
    """Restore system from backup."""
    importer = MetadataImporter(storage, tag_manager)
    return importer.restore_backup(backup_path, restore_only_missing)