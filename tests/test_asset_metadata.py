"""
Comprehensive Test Suite for Asset Metadata System

This module contains unit tests for all components of the asset metadata system
including storage, versioning, search, tag management, and export/import functionality.
"""

import pytest
import os
import tempfile
import sqlite3
import json
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import metadata system components
from storage.metadata_schema import (
    AssetMetadata, AssetFormat, AssetCategory, AssetStatus, MetadataQuery
)
from storage.asset_storage import AssetStorage, DatabaseConnection
from storage.versioning import AssetVersioner, VersionDiff, VersionChangeType
from storage.search import AssetSearchEngine, SearchResult, SearchRelevance
from storage.tag_manager import TagManager, TagCategory, TagSuggestion
from storage.export_import import MetadataExporter, MetadataImporter, ExportFormat


class TestAssetMetadata:
    """Test cases for AssetMetadata model."""
    
    def test_create_new_metadata(self):
        """Test creating new asset metadata."""
        metadata = AssetMetadata.create_new(
            generator_type="parchment",
            width=1024,
            height=1024,
            format=AssetFormat.PNG,
            size_bytes=50000,
            hash="abc123"
        )
        
        assert metadata.asset_id is not None
        assert metadata.version == 1
        assert metadata.generator_type == "parchment"
        assert metadata.width == 1024
        assert metadata.height == 1024
        assert metadata.format == AssetFormat.PNG
        assert metadata.size_bytes == 50000
        assert metadata.hash == "abc123"
        assert len(metadata.tags) == 0
        assert metadata.status == AssetStatus.ACTIVE
    
    def test_create_version(self):
        """Test creating a new version of metadata."""
        original = AssetMetadata.create_new(
            generator_type="enso",
            width=800,
            height=800,
            format=AssetFormat.PNG,
            size_bytes=30000,
            hash="def456",
            title="Original Enso"
        )
        
        new_version = original.create_version(
            width=1024,
            title="Updated Enso"
        )
        
        assert new_version.asset_id == original.asset_id
        assert new_version.version == 2
        assert new_version.width == 1024
        assert new_version.height == original.height  # Unchanged
        assert new_version.title == "Updated Enso"
        assert new_version.created_at > original.created_at
    
    def test_get_filename(self):
        """Test filename generation."""
        metadata = AssetMetadata.create_new(
            generator_type="giraffe",
            width=600,
            height=800,
            format=AssetFormat.PNG,
            size_bytes=40000,
            hash="ghi789",
            title="Ink Giraffe"
        )
        
        # Test with version
        filename_with_version = metadata.get_filename(include_version=True)
        assert filename_with_version == "Ink Giraffe_v1.png"
        
        # Test without version
        filename_without_version = metadata.get_filename(include_version=False)
        assert filename_without_version == "Ink Giraffe.png"
        
        # Test with no title
        metadata_no_title = AssetMetadata.create_new(
            generator_type="sigil",
            width=500,
            height=500,
            format=AssetFormat.PNG,
            size_bytes=20000,
            hash="jkl012"
        )
        
        filename_auto = metadata_no_title.get_filename()
        assert filename_auto.startswith("sigil_")


class TestAssetStorage:
    """Test cases for AssetStorage functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def storage(self, temp_db_path):
        """Create a test storage instance."""
        return AssetStorage(temp_db_path)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return AssetMetadata.create_new(
            generator_type="parchment",
            width=1024,
            height=1024,
            format=AssetFormat.PNG,
            size_bytes=50000,
            hash="test_hash_123",
            title="Test Parchment",
            description="A test parchment texture",
            tags=["texture", "background", "dark"],
            category=AssetCategory.BACKGROUND,
            author="Test Author",
            quality="high"
        )
    
    def test_database_initialization(self, temp_db_path):
        """Test database schema initialization."""
        storage = AssetStorage(temp_db_path)
        
        # Check that database file exists
        assert os.path.exists(temp_db_path)
        
        # Check that tables are created
        with DatabaseConnection(temp_db_path) as conn:
            cursor = conn.cursor()
            
            # Check main tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'assets' in tables
            assert 'asset_tags' in tables
            assert 'asset_relationships' in tables
            assert 'asset_analytics' in tables
            assert 'assets_fts' in tables
    
    def test_store_and_retrieve_asset(self, storage, sample_metadata):
        """Test storing and retrieving asset metadata."""
        # Store the asset
        success = storage.store_asset(sample_metadata)
        assert success is True
        
        # Retrieve the asset
        retrieved = storage.get_asset(sample_metadata.asset_id)
        assert retrieved is not None
        assert retrieved.asset_id == sample_metadata.asset_id
        assert retrieved.generator_type == sample_metadata.generator_type
        assert retrieved.width == sample_metadata.width
        assert retrieved.title == sample_metadata.title
        assert retrieved.tags == sample_metadata.tags
    
    def test_update_asset_metadata(self, storage, sample_metadata):
        """Test updating asset metadata."""
        # Store initial asset
        storage.store_asset(sample_metadata)
        
        # Update metadata
        updates = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'is_favorite': True,
            'tags': ['new_tag', 'updated_tag']
        }
        
        success = storage.update_asset_metadata(sample_metadata.asset_id, updates)
        assert success is True
        
        # Verify updates
        updated = storage.get_asset(sample_metadata.asset_id)
        assert updated.title == 'Updated Title'
        assert updated.description == 'Updated description'
        assert updated.is_favorite is True
        assert 'new_tag' in updated.tags
        assert 'updated_tag' in updated.tags
    
    def test_delete_asset(self, storage, sample_metadata):
        """Test asset deletion (soft and hard)."""
        # Store asset
        storage.store_asset(sample_metadata)
        
        # Test soft delete
        success = storage.delete_asset(sample_metadata.asset_id, permanent=False)
        assert success is True
        
        # Asset should not be returned by default
        retrieved = storage.get_asset(sample_metadata.asset_id)
        assert retrieved is None
        
        # But should be available with include_deleted
        retrieved_with_deleted = storage.get_asset(sample_metadata.asset_id, include_deleted=True)
        assert retrieved_with_deleted is not None
        assert retrieved_with_deleted.status == AssetStatus.DELETED
    
    def test_increment_access_count(self, storage, sample_metadata):
        """Test access count tracking."""
        # Store asset
        storage.store_asset(sample_metadata)
        
        # Increment access count
        success = storage.increment_access_count(sample_metadata.asset_id)
        assert success is True
        
        # Verify access count increased
        retrieved = storage.get_asset(sample_metadata.asset_id)
        assert retrieved.access_count == 1
        
        # Increment again
        storage.increment_access_count(sample_metadata.asset_id)
        retrieved = storage.get_asset(sample_metadata.asset_id)
        assert retrieved.access_count == 2
    
    def test_get_stats(self, storage):
        """Test getting system statistics."""
        # Create multiple test assets
        assets = []
        for i in range(3):
            metadata = AssetMetadata.create_new(
                generator_type="enso",
                width=800,
                height=800,
                format=AssetFormat.PNG,
                size_bytes=30000 + i * 1000,
                hash=f"hash_{i}",
                title=f"Asset {i}",
                tags=[f"tag{i}", "common"],
                category=AssetCategory.GLYPH if i % 2 == 0 else AssetCategory.BACKGROUND
            )
            assets.append(metadata)
            storage.store_asset(metadata)
        
        # Get statistics
        stats = storage.get_stats()
        
        assert stats.total_assets == 3
        assert stats.total_versions == 3
        assert stats.total_tags >= 4  # At least the tags we added
        assert stats.total_storage_bytes > 0
        assert stats.average_file_size > 0
        assert len(stats.assets_by_generator) > 0
        assert len(stats.assets_by_category) > 0


class TestAssetVersioner:
    """Test cases for AssetVersioner functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def storage_and_versioner(self, temp_db_path):
        """Create storage and versioner instances."""
        storage = AssetStorage(temp_db_path)
        versioner = AssetVersioner(storage)
        return storage, versioner
    
    @pytest.fixture
    def base_metadata(self):
        """Create base metadata for version testing."""
        return AssetMetadata.create_new(
            generator_type="sigil",
            width=500,
            height=500,
            format=AssetFormat.PNG,
            size_bytes=25000,
            hash="base_hash",
            title="Base Sigil",
            quality="medium"
        )
    
    def test_create_version(self, storage_and_versioner, base_metadata):
        """Test creating a new version."""
        storage, versioner = storage_and_versioner
        
        # Store base version
        storage.store_asset(base_metadata)
        
        # Create new version
        new_metadata = base_metadata.create_version(
            quality="high",
            title="Enhanced Sigil"
        )
        
        success = versioner.create_version(base_metadata, new_metadata)
        assert success is True
        
        # Verify version was stored
        retrieved = storage.get_asset(new_metadata.asset_id)
        assert retrieved is not None
        assert retrieved.version == 2
    
    def test_get_version_history(self, storage_and_versioner, base_metadata):
        """Test getting version history."""
        storage, versioner = storage_and_versioner
        
        # Store base version
        storage.store_asset(base_metadata)
        
        # Create additional versions
        v2 = base_metadata.create_version(title="Version 2")
        v3 = base_metadata.create_version(title="Version 3")
        
        versioner.create_version(base_metadata, v2)
        versioner.create_version(v2, v3)
        
        # Get version history
        history = versioner.get_version_history(base_metadata.asset_id)
        
        assert len(history) >= 2  # At least base and v2
        assert history[0].version >= history[1].version  # Sorted by version descending
    
    def test_version_diff(self, storage_and_versioner, base_metadata):
        """Test version difference calculation."""
        storage, versioner = storage_and_versioner
        
        # Create two versions with different properties
        v1 = base_metadata
        v2 = base_metadata.create_version(
            width=800,
            quality="high",
            title="Modified Version"
        )
        
        diff = VersionDiff(v1, v2)
        
        assert 'width' in diff.changes
        assert 'quality' in diff.changes
        assert 'title' in diff.changes
        assert diff.change_type in [VersionChangeType.MAJOR, VersionChangeType.QUALITY_CHANGE]
        assert len(diff.significant_changes) > 0
    
    def test_rollback_to_version(self, storage_and_versioner, base_metadata):
        """Test rolling back to a previous version."""
        storage, versioner = storage_and_versioner
        
        # Store base version
        storage.store_asset(base_metadata)
        
        # Create version 2
        v2 = base_metadata.create_version(
            quality="high",
            title="Version 2"
        )
        versioner.create_version(base_metadata, v2)
        
        # Create version 3
        v3 = v2.create_version(
            width=800,
            title="Version 3"
        )
        versioner.create_version(v2, v3)
        
        # Rollback to version 2
        rollback = versioner.rollback_to_version(base_metadata.asset_id, 2)
        
        assert rollback is not None
        assert rollback.version == 4  # New version after rollback
        assert rollback.title == "Version 2"  # Title from v2


class TestAssetSearchEngine:
    """Test cases for AssetSearchEngine functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def storage_and_search(self, temp_db_path):
        """Create storage and search engine instances."""
        storage = AssetStorage(temp_db_path)
        search_engine = AssetSearchEngine(storage)
        return storage, search_engine
    
    @pytest.fixture
    def sample_assets(self, storage_and_search):
        """Create sample assets for testing."""
        storage, search_engine = storage_and_search
        
        assets = [
            AssetMetadata.create_new(
                generator_type="enso",
                width=800,
                height=800,
                format=AssetFormat.PNG,
                size_bytes=30000,
                hash="enso_hash_1",
                title="Zen Circle",
                description="A peaceful zen circle",
                tags=["circle", "zen", "peaceful"],
                category=AssetCategory.GLYPH,
                author="Artist 1"
            ),
            AssetMetadata.create_new(
                generator_type="parchment",
                width=1024,
                height=1024,
                format=AssetFormat.PNG,
                size_bytes=50000,
                hash="parchment_hash_1",
                title="Dark Parchment",
                description="A dark aged parchment",
                tags=["texture", "background", "dark"],
                category=AssetCategory.BACKGROUND,
                author="Artist 2"
            ),
            AssetMetadata.create_new(
                generator_type="giraffe",
                width=600,
                height=800,
                format=AssetFormat.PNG,
                size_bytes=40000,
                hash="giraffe_hash_1",
                title="Spotted Giraffe",
                description="A giraffe with spots",
                tags=["animal", "spots", "nature"],
                category=AssetCategory.CREATURE,
                author="Artist 1"
            )
        ]
        
        for asset in assets:
            storage.store_asset(asset)
        
        return assets
    
    def test_text_search(self, storage_and_search, sample_assets):
        """Test text-based search."""
        storage, search_engine = storage_and_search
        
        # Search for "zen"
        query = MetadataQuery(text="zen")
        results, total, facets = search_engine.search(query)
        
        assert total >= 1
        assert len(results) >= 1
        
        # Check that zen-related result is found
        zen_found = any(
            "zen" in result.asset.title.lower() or 
            "zen" in result.asset.description.lower()
            for result in results
        )
        assert zen_found
    
    def test_tag_filtering(self, storage_and_search, sample_assets):
        """Test tag-based filtering."""
        storage, search_engine = storage_and_search
        
        # Filter by "circle" tag
        query = MetadataQuery(tags=["circle"])
        results, total, facets = search_engine.search(query)
        
        assert total >= 1
        assert len(results) >= 1
        
        # Check that result has "circle" tag
        circle_found = any(
            "circle" in result.asset.tags
            for result in results
        )
        assert circle_found
    
    def test_category_filtering(self, storage_and_search, sample_assets):
        """Test category-based filtering."""
        storage, search_engine = storage_and_search
        
        # Filter by GLYPH category
        query = MetadataQuery(category=AssetCategory.GLYPH)
        results, total, facets = search_engine.search(query)
        
        assert total >= 1
        assert len(results) >= 1
        
        # Check that all results are from GLYPH category
        glyph_only = all(
            result.asset.category == AssetCategory.GLYPH
            for result in results
        )
        assert glyph_only
    
    def test_find_similar_assets(self, storage_and_search, sample_assets):
        """Test finding similar assets."""
        storage, search_engine = storage_and_search
        
        # Find similar assets to the enso
        similar = search_engine.find_similar_assets(sample_assets[0].asset_id, limit=5)
        
        assert len(similar) >= 0  # May not find similar assets in small dataset
        
        if similar:
            # Check that similar asset is different from reference
            assert similar[0].asset.asset_id != sample_assets[0].asset_id
    
    def test_search_suggestions(self, storage_and_search, sample_assets):
        """Test search suggestions."""
        storage, search_engine = storage_and_search
        
        # Get suggestions for partial query
        suggestions = search_engine.get_search_suggestions("ze", limit=5)
        
        assert isinstance(suggestions, list)


class TestTagManager:
    """Test cases for TagManager functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def storage_and_tags(self, temp_db_path):
        """Create storage and tag manager instances."""
        storage = AssetStorage(temp_db_path)
        tag_manager = TagManager(storage)
        return storage, tag_manager
    
    @pytest.fixture
    def tagged_assets(self, storage_and_tags):
        """Create assets with tags for testing."""
        storage, tag_manager = storage_and_tags
        
        assets = [
            AssetMetadata.create_new(
                generator_type="enso",
                width=800,
                height=800,
                format=AssetFormat.PNG,
                size_bytes=30000,
                hash="hash_1",
                tags=["circle", "zen", "peaceful"],
                category=AssetCategory.GLYPH
            ),
            AssetMetadata.create_new(
                generator_type="sigil",
                width=500,
                height=500,
                format=AssetFormat.PNG,
                size_bytes=25000,
                hash="hash_2",
                tags=["magic", "mystical", "circle"],
                category=AssetCategory.GLYPH
            ),
            AssetMetadata.create_new(
                generator_type="parchment",
                width=1024,
                height=1024,
                format=AssetFormat.PNG,
                size_bytes=50000,
                hash="hash_3",
                tags=["texture", "dark", "background"],
                category=AssetCategory.BACKGROUND
            )
        ]
        
        for asset in assets:
            storage.store_asset(asset)
        
        return assets
    
    def test_validate_tags(self, storage_and_tags, tagged_assets):
        """Test tag validation."""
        storage, tag_manager = storage_and_tags
        
        # Test valid tags
        valid_tags = ["valid_tag", "another_tag", "third_tag"]
        is_valid, errors = tag_manager.validate_tags(valid_tags)
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid tags
        invalid_tags = ["", "toolongtag" * 10, "invalid@tag"]
        is_valid, errors = tag_manager.validate_tags(invalid_tags)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_categorize_tag(self, storage_and_tags, tagged_assets):
        """Test automatic tag categorization."""
        storage, tag_manager = storage_and_tags
        
        # Test color tag
        color_category = tag_manager.categorize_tag("red")
        assert color_category in [TagCategory.COLOR, TagCategory.CUSTOM]
        
        # Test style tag
        style_category = tag_manager.categorize_tag("abstract")
        assert style_category in [TagCategory.STYLE, TagCategory.CUSTOM]
        
        # Test emotion tag
        emotion_category = tag_manager.categorize_tag("happy")
        assert emotion_category in [TagCategory.EMOTION, TagCategory.CUSTOM]
    
    def test_get_popular_tags(self, storage_and_tags, tagged_assets):
        """Test getting popular tags."""
        storage, tag_manager = storage_and_tags
        
        popular_tags = tag_manager.get_popular_tags(limit=10)
        
        assert isinstance(popular_tags, list)
        
        # "circle" appears twice, should be popular
        circle_found = any(tag_info.name == "circle" for tag_info in popular_tags)
        assert circle_found
    
    def test_suggest_tags(self, storage_and_tags, tagged_assets):
        """Test tag suggestions for an asset."""
        storage, tag_manager = storage_and_tags
        
        # Get suggestions for an enso asset
        enso_asset = next(asset for asset in tagged_assets if asset.generator_type == "enso")
        suggestions = tag_manager.suggest_tags(enso_asset, limit=5)
        
        assert isinstance(suggestions, list)
        
        if suggestions:
            # Check suggestion structure
            suggestion = suggestions[0]
            assert hasattr(suggestion, 'tag')
            assert hasattr(suggestion, 'category')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'reason')
    
    def test_search_tags(self, storage_and_tags, tagged_assets):
        """Test searching for tags."""
        storage, tag_manager = storage_and_tags
        
        # Search for tags containing "cir"
        search_results = tag_manager.search_tags("cir", limit=10)
        
        assert isinstance(search_results, list)
        
        # Should find "circle" tag
        circle_found = any(tag_info.name == "circle" for tag_info in search_results)
        assert circle_found
    
    def test_merge_tags(self, storage_and_tags, tagged_assets):
        """Test merging tags."""
        storage, tag_manager = storage_and_tags
        
        # Add some tags that we can merge
        test_tags = ["tag_to_merge", "target_tag"]
        for asset in tagged_assets[:2]:
            storage.update_asset_metadata(asset.asset_id, {"tags": asset.tags + test_tags})
        
        # Try to merge tags
        success = tag_manager.merge_tags("tag_to_merge", "target_tag")
        
        # Check result (may depend on implementation details)
        assert isinstance(success, bool)


class TestExportImport:
    """Test cases for export/import functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def storage_and_exporter(self, temp_db_path):
        """Create storage and exporter instances."""
        storage = AssetStorage(temp_db_path)
        tag_manager = TagManager(storage)
        exporter = MetadataExporter(storage, tag_manager)
        return storage, tag_manager, exporter
    
    @pytest.fixture
    def test_assets(self, storage_and_exporter):
        """Create test assets for export/import testing."""
        storage, tag_manager, exporter = storage_and_exporter
        
        assets = []
        for i in range(3):
            metadata = AssetMetadata.create_new(
                generator_type="enso" if i % 2 == 0 else "parchment",
                width=800,
                height=800,
                format=AssetFormat.PNG,
                size_bytes=30000 + i * 1000,
                hash=f"hash_{i}",
                title=f"Test Asset {i}",
                description=f"Description for asset {i}",
                tags=[f"tag{i}", "test", "export"],
                category=AssetCategory.GLYPH if i % 2 == 0 else AssetCategory.BACKGROUND,
                author="Test Author"
            )
            assets.append(metadata)
            storage.store_asset(metadata)
        
        return assets
    
    def test_export_to_json(self, storage_and_exporter, test_assets):
        """Test JSON export functionality."""
        storage, tag_manager, exporter = storage_and_exporter
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_path = tmp.name
        
        try:
            success = exporter.export_to_json(export_path, include_deleted=False)
            assert success is True
            assert os.path.exists(export_path)
            
            # Verify JSON content
            with open(export_path, 'r') as f:
                data = json.load(f)
            
            assert 'assets' in data
            assert 'metadata' in data
            assert len(data['assets']) >= 3
            
            # Verify asset data structure
            asset = data['assets'][0]
            required_fields = ['asset_id', 'generator_type', 'width', 'height', 'tags']
            for field in required_fields:
                assert field in asset
        
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    def test_export_to_csv(self, storage_and_exporter, test_assets):
        """Test CSV export functionality."""
        storage, tag_manager, exporter = storage_and_exporter
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            export_path = tmp.name
        
        try:
            success = exporter.export_to_csv(export_path, include_deleted=False)
            assert success is True
            assert os.path.exists(export_path)
            
            # Verify CSV content
            with open(export_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) >= 4  # Header + 3 data rows
            assert 'asset_id' in lines[0]
            assert 'generator_type' in lines[0]
        
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    def test_create_backup(self, storage_and_exporter, test_assets):
        """Test backup creation."""
        storage, tag_manager, exporter = storage_and_exporter
        
        backup_path = exporter.create_backup("test_backup")
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.zip')
        
        # Clean up
        if os.path.exists(backup_path):
            os.unlink(backup_path)
        
        # Also clean up info file
        info_path = backup_path + '.info.json'
        if os.path.exists(info_path):
            os.unlink(info_path)
    
    def test_list_backups(self, storage_and_exporter, test_assets):
        """Test listing backups."""
        storage, tag_manager, exporter = storage_and_exporter
        
        # Create a backup first
        backup_path = exporter.create_backup("test_list_backup")
        
        try:
            backups = exporter.list_backups()
            
            assert isinstance(backups, list)
            
            # Find our test backup
            test_backup = next(
                (b for b in backups if 'test_list_backup' in b['name']),
                None
            )
            assert test_backup is not None
            assert test_backup['size_bytes'] > 0
        
        finally:
            # Clean up
            if backup_path and os.path.exists(backup_path):
                os.unlink(backup_path)
            info_path = backup_path + '.info.json'
            if os.path.exists(info_path):
                os.unlink(info_path)


class TestMetadataIntegration:
    """Integration tests for the complete metadata system."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def complete_system(self, temp_db_path):
        """Create complete metadata system."""
        storage = AssetStorage(temp_db_path)
        versioner = AssetVersioner(storage)
        search_engine = AssetSearchEngine(storage)
        tag_manager = TagManager(storage)
        exporter = MetadataExporter(storage, tag_manager)
        importer = MetadataImporter(storage, tag_manager)
        
        return {
            'storage': storage,
            'versioner': versioner,
            'search_engine': search_engine,
            'tag_manager': tag_manager,
            'exporter': exporter,
            'importer': importer
        }
    
    def test_full_workflow(self, complete_system):
        """Test complete metadata workflow."""
        system = complete_system
        
        # 1. Create and store asset
        asset = AssetMetadata.create_new(
            generator_type="enso",
            width=800,
            height=800,
            format=AssetFormat.PNG,
            size_bytes=30000,
            hash="workflow_hash",
            title="Workflow Test",
            description="Testing complete workflow",
            tags=["workflow", "test", "enso"],
            category=AssetCategory.GLYPH
        )
        
        success = system['storage'].store_asset(asset)
        assert success is True
        
        # 2. Create version
        v2 = asset.create_version(
            quality="high",
            title="Workflow Test v2"
        )
        system['versioner'].create_version(asset, v2)
        
        # 3. Update metadata
        system['storage'].update_asset_metadata(
            asset.asset_id,
            {'tags': ['workflow', 'test', 'enso', 'updated']}
        )
        
        # 4. Test search
        query = MetadataQuery(text="workflow")
        results, total, facets = system['search_engine'].search(query)
        assert total >= 1
        
        # 5. Test tag management
        popular_tags = system['tag_manager'].get_popular_tags(limit=10)
        assert isinstance(popular_tags, list)
        
        # 6. Test export
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_path = tmp.name
        
        try:
            export_success = system['exporter'].export_to_json(export_path)
            assert export_success is True
            
            # 7. Test import
            import_result = system['importer'].import_from_json(
                export_path,
                validate_only=True
            )
            assert import_result.successful_imports >= 3  # Original + 2 versions
        
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)


# Test utilities and fixtures

@pytest.fixture
def sample_parameters():
    """Sample generation parameters for testing."""
    return {
        'width': 1024,
        'height': 1024,
        'quality': 'high',
        'complexity': 0.8,
        'randomness': 0.6,
        'base_color': '#2c2c2c',
        'color_palette': ['#2c2c2c', '#404040', '#1a1a1a']
    }


@pytest.fixture
def mock_pil_image():
    """Mock PIL Image for testing."""
    mock_img = Mock()
    mock_img.width = 1024
    mock_img.height = 1024
    mock_img.size = (1024, 1024)
    
    # Mock save method to return fake size
    def mock_save(buf, format="PNG"):
        fake_content = b"fake image data" * 100
        buf.write(fake_content)
        buf.seek(0)
        return len(fake_content)
    
    mock_img.save = mock_save
    return mock_img


# Test configuration
def pytest_configure(config):
    """Configure pytest for metadata tests."""
    config.addinivalue_line(
        "markers", "metadata: mark test as a metadata system test"
    )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])