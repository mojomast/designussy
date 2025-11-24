"""
Asset Versioning System

This module provides comprehensive versioning capabilities for assets, including
parent-child relationship tracking, version comparison, rollback functionality,
and branching support.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import difflib

from .metadata_schema import AssetMetadata, AssetVersion, AssetRelationship
from .asset_storage import AssetStorage


class VersionChangeType(str, Enum):
    """Types of changes between asset versions."""
    MINOR = "minor"          # Small changes, same generation
    MAJOR = "major"          # Significant changes
    PARAMETER_UPDATE = "parameter_update"  # Generation parameters changed
    QUALITY_CHANGE = "quality_change"      # Quality settings changed
    REFORMAT = "reformat"      # Format or size changed
    REBORN = "reborn"         # Completely regenerated with new seed


class VersionDiff:
    """
    Represents the differences between two asset versions.
    """
    
    def __init__(self, from_version: AssetMetadata, to_version: AssetMetadata):
        self.from_version = from_version
        self.to_version = to_version
        self.changes = self._calculate_changes()
        self.change_type = self._determine_change_type()
        self.significant_changes = self._identify_significant_changes()
    
    def _calculate_changes(self) -> Dict[str, Any]:
        """Calculate the differences between two versions."""
        changes = {}
        
        # Compare basic properties
        if self.from_version.width != self.to_version.width:
            changes['width'] = {'from': self.from_version.width, 'to': self.to_version.width}
        
        if self.from_version.height != self.to_version.height:
            changes['height'] = {'from': self.from_version.height, 'to': self.to_version.height}
        
        if self.from_version.format != self.to_version.format:
            changes['format'] = {'from': self.from_version.format.value, 'to': self.to_version.format.value}
        
        if self.from_version.size_bytes != self.to_version.size_bytes:
            changes['size_bytes'] = {'from': self.from_version.size_bytes, 'to': self.to_version.size_bytes}
        
        # Compare parameters
        if self.from_version.parameters != self.to_version.parameters:
            changes['parameters'] = {'from': self.from_version.parameters, 'to': self.to_version.parameters}
        
        # Compare quality settings
        quality_fields = ['quality', 'complexity', 'randomness', 'base_color']
        for field in quality_fields:
            from_val = getattr(self.from_version, field)
            to_val = getattr(self.to_version, field)
            if from_val != to_val:
                changes[field] = {'from': from_val, 'to': to_val}
        
        # Compare user metadata
        metadata_fields = ['title', 'description', 'author', 'tags', 'category']
        for field in metadata_fields:
            from_val = getattr(self.from_version, field)
            to_val = getattr(self.to_version, field)
            if from_val != to_val:
                changes[field] = {'from': from_val, 'to': to_val}
        
        # Check if it's a complete regeneration (different hash)
        if self.from_version.hash != self.to_version.hash:
            changes['content_hash'] = {'from': self.from_version.hash, 'to': self.to_version.hash}
        
        return changes
    
    def _determine_change_type(self) -> VersionChangeType:
        """Determine the type of change between versions."""
        if not self.changes:
            return VersionChangeType.MINOR
        
        # Check for format/size changes
        if any(field in self.changes for field in ['width', 'height', 'format', 'size_bytes']):
            return VersionChangeType.REFORMAT
        
        # Check for quality parameter changes
        if any(field in self.changes for field in ['quality', 'complexity', 'randomness']):
            return VersionChangeType.QUALITY_CHANGE
        
        # Check for generation parameter changes
        if 'parameters' in self.changes:
            return VersionChangeType.PARAMETER_UPDATE
        
        # Check if content is completely different (new seed/regeneration)
        if 'content_hash' in self.changes:
            return VersionChangeType.REBORN
        
        # If only user metadata changed, it's minor
        metadata_fields = ['title', 'description', 'author', 'tags', 'category']
        if all(field not in self.changes for field in ['width', 'height', 'format', 'size_bytes', 'parameters', 'quality', 'complexity', 'randomness', 'content_hash']):
            return VersionChangeType.MINOR
        
        return VersionChangeType.MAJOR
    
    def _identify_significant_changes(self) -> List[str]:
        """Identify which changes are considered significant."""
        significant_fields = [
            'width', 'height', 'format', 'size_bytes', 'parameters', 
            'quality', 'complexity', 'randomness', 'content_hash'
        ]
        return [field for field in self.changes.keys() if field in significant_fields]
    
    def get_change_summary(self) -> str:
        """Get a human-readable summary of changes."""
        if not self.changes:
            return "No significant changes"
        
        summary_parts = []
        
        if self.change_type == VersionChangeType.MINOR:
            summary_parts.append("Minor changes to metadata")
        elif self.change_type == VersionChangeType.MAJOR:
            summary_parts.append("Major changes detected")
        elif self.change_type == VersionChangeType.PARAMETER_UPDATE:
            summary_parts.append("Generation parameters updated")
        elif self.change_type == VersionChangeType.QUALITY_CHANGE:
            summary_parts.append("Quality settings changed")
        elif self.change_type == VersionChangeType.REFORMAT:
            summary_parts.append("Format or dimensions changed")
        elif self.change_type == VersionChangeType.REBORN:
            summary_parts.append("Asset completely regenerated")
        
        # Add specific change details
        change_details = []
        for field, change in self.changes.items():
            if field == 'width':
                change_details.append(f"size: {change['from']}x{self.from_version.height} → {change['to']}x{self.to_version.height}")
            elif field == 'height':
                change_details.append(f"size: {self.from_version.width}x{change['from']} → {self.to_version.width}x{change['to']}")
            elif field == 'format':
                change_details.append(f"format: {change['from']} → {change['to']}")
            elif field == 'quality':
                change_details.append(f"quality: {change['from']} → {change['to']}")
            elif field == 'parameters':
                param_count = len(change['to']) if isinstance(change['to'], dict) else 0
                change_details.append(f"{param_count} parameter(s) updated")
            elif field == 'content_hash':
                change_details.append("visual content changed")
            elif field == 'tags':
                added = set(change['to']) - set(change['from']) if change['from'] else set(change['to'])
                removed = set(change['from']) - set(change['to']) if change['from'] else set()
                if added:
                    change_details.append(f"added tags: {', '.join(added)}")
                if removed:
                    change_details.append(f"removed tags: {', '.join(removed)}")
        
        if change_details:
            summary_parts.append(" (" + "; ".join(change_details) + ")")
        
        return "".join(summary_parts)


@dataclass
class VersionBranch:
    """Represents a branch in the version tree."""
    name: str
    base_version: int
    created_at: datetime
    description: Optional[str] = None
    is_active: bool = True


class AssetVersioner:
    """
    Comprehensive asset versioning system.
    
    Provides version management, parent-child tracking, comparison,
    rollback capabilities, and branching support.
    """
    
    def __init__(self, storage: AssetStorage):
        """
        Initialize the asset versioner.
        
        Args:
            storage: AssetStorage instance for data persistence
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for version relationships
        self._version_cache = {}
        self._branch_cache = {}
    
    def create_version(self, parent_metadata: AssetMetadata, new_metadata: AssetMetadata,
                      change_description: Optional[str] = None, 
                      is_major_change: bool = False) -> bool:
        """
        Create a new version of an asset.
        
        Args:
            parent_metadata: The parent asset metadata
            new_metadata: The new version metadata
            change_description: Optional description of changes
            is_major_change: Whether this is a major change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create version relationship
            version_relationship = AssetVersion(
                asset_id=new_metadata.asset_id,
                version=new_metadata.version,
                parent_version=parent_metadata.version if parent_metadata.asset_id == new_metadata.asset_id else None,
                changes={},
                is_major_change=is_major_change,
                change_description=change_description
            )
            
            # Calculate and store the version diff
            if parent_metadata.asset_id == new_metadata.asset_id:
                version_diff = VersionDiff(parent_metadata, new_metadata)
                version_relationship.changes = version_diff.changes
                
                # Auto-determine if it's a major change based on diff
                if not is_major_change:
                    version_relationship.is_major_change = (
                        version_diff.change_type in [
                            VersionChangeType.MAJOR, 
                            VersionChangeType.REBORN, 
                            VersionChangeType.REFORMAT
                        ] or len(version_diff.significant_changes) > 3
                    )
            
            # Store the new version
            success = self.storage.store_asset(new_metadata)
            
            if success:
                # Cache the version relationship
                cache_key = f"{new_metadata.asset_id}:{new_metadata.version}"
                self._version_cache[cache_key] = version_relationship
                
                self.logger.info(
                    f"Created version {new_metadata.version} for asset {new_metadata.asset_id} "
                    f"({'major' if version_relationship.is_major_change else 'minor'} change)"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating version: {e}")
            return False
    
    def get_version_history(self, asset_id: str, include_deleted: bool = False) -> List[AssetMetadata]:
        """
        Get the complete version history for an asset.
        
        Args:
            asset_id: Asset ID to get history for
            include_deleted: Whether to include deleted versions
            
        Returns:
            List of AssetMetadata objects ordered by version
        """
        try:
            from .metadata_schema import MetadataQuery, AssetStatus
            
            query = MetadataQuery(
                text=f"asset_id:{asset_id}",
                status=None if include_deleted else AssetStatus.ACTIVE,
                sort_by="version",
                sort_order="asc",
                limit=1000,
                offset=0
            )
            
            assets, total = self.storage.get_assets_by_query(query)
            
            # Filter to only this asset's versions and sort by version
            asset_versions = [asset for asset in assets if asset.asset_id == asset_id]
            asset_versions.sort(key=lambda x: x.version)
            
            return asset_versions
            
        except Exception as e:
            self.logger.error(f"Error getting version history: {e}")
            return []
    
    def get_version_diff(self, asset_id: str, from_version: int, to_version: int) -> Optional[VersionDiff]:
        """
        Get the differences between two specific versions.
        
        Args:
            asset_id: Asset ID
            from_version: Starting version number
            to_version: Ending version number
            
        Returns:
            VersionDiff object if found, None otherwise
        """
        try:
            from_version_meta = self.storage.get_asset(f"{asset_id}:v{from_version}")
            to_version_meta = self.storage.get_asset(f"{asset_id}:v{to_version}")
            
            # Handle version ID format (asset_id might be formatted differently)
            if not from_version_meta:
                # Try alternative asset ID format
                from_version_meta = self.storage.get_asset(asset_id)
                if from_version_meta and from_version_meta.version != from_version:
                    history = self.get_version_history(asset_id)
                    from_version_meta = next((v for v in history if v.version == from_version), None)
            
            if not to_version_meta:
                # Try alternative asset ID format
                to_version_meta = self.storage.get_asset(asset_id)
                if to_version_meta and to_version_meta.version != to_version:
                    history = self.get_version_history(asset_id)
                    to_version_meta = next((v for v in history if v.version == to_version), None)
            
            if from_version_meta and to_version_meta:
                return VersionDiff(from_version_meta, to_version_meta)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting version diff: {e}")
            return None
    
    def rollback_to_version(self, asset_id: str, target_version: int, 
                          new_description: Optional[str] = None) -> Optional[AssetMetadata]:
        """
        Rollback an asset to a previous version.
        
        Args:
            asset_id: Asset ID to rollback
            target_version: Version number to rollback to
            new_description: Optional description for the rollback
            
        Returns:
            New AssetMetadata for the rollback version, None if failed
        """
        try:
            # Get the target version
            history = self.get_version_history(asset_id)
            target_metadata = next((v for v in history if v.version == target_version), None)
            
            if not target_metadata:
                self.logger.error(f"Target version {target_version} not found for asset {asset_id}")
                return None
            
            # Get current version to determine next version number
            current_metadata = self.storage.get_asset(asset_id)
            if not current_metadata:
                return None
            
            # Create rollback metadata
            rollback_metadata = target_metadata.create_version(
                description=new_description or f"Rollback to version {target_version}",
                updated_at=datetime.utcnow()
            )
            
            # Store the rollback as a new version
            success = self.storage.store_asset(rollback_metadata)
            
            if success:
                self.logger.info(f"Rolled back asset {asset_id} to version {target_version}")
                return rollback_metadata
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
            return None
    
    def create_branch(self, asset_id: str, branch_name: str, 
                     base_version: int, description: Optional[str] = None) -> bool:
        """
        Create a new branch from an existing version.
        
        Args:
            asset_id: Asset ID to branch from
            branch_name: Name for the new branch
            base_version: Version to branch from
            description: Optional branch description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the base version
            history = self.get_version_history(asset_id)
            base_metadata = next((v for v in history if v.version == base_version), None)
            
            if not base_metadata:
                self.logger.error(f"Base version {base_version} not found for asset {asset_id}")
                return False
            
            # Create branch metadata (same as base but as new branch)
            branch_metadata = base_metadata.create_version(
                title=f"{base_metadata.title} [{branch_name}]" if base_metadata.title else None,
                description=description or f"Branch '{branch_name}' from version {base_version}",
                updated_at=datetime.utcnow()
            )
            
            # Store the branch
            success = self.storage.store_asset(branch_metadata)
            
            if success:
                # Cache the branch
                branch = VersionBranch(
                    name=branch_name,
                    base_version=base_version,
                    created_at=datetime.utcnow(),
                    description=description
                )
                self._branch_cache[f"{asset_id}:{branch_name}"] = branch
                
                self.logger.info(f"Created branch '{branch_name}' from version {base_version}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return False
    
    def get_branch_history(self, asset_id: str, branch_name: str) -> List[AssetMetadata]:
        """
        Get the version history for a specific branch.
        
        Args:
            asset_id: Asset ID
            branch_name: Branch name
            
        Returns:
            List of AssetMetadata for the branch
        """
        try:
            from .metadata_schema import MetadataQuery
            
            # Search for assets in this branch
            query = MetadataQuery(
                text=f"asset_id:{asset_id} AND title:*{branch_name}*",
                sort_by="version",
                sort_order="asc",
                limit=1000,
                offset=0
            )
            
            assets, total = self.storage.get_assets_by_query(query)
            return [asset for asset in assets if branch_name in (asset.title or "")]
            
        except Exception as e:
            self.logger.error(f"Error getting branch history: {e}")
            return []
    
    def merge_branch(self, source_asset_id: str, target_asset_id: str, 
                    source_branch: str, merge_description: Optional[str] = None) -> Optional[AssetMetadata]:
        """
        Merge a branch back into the main asset.
        
        Args:
            source_asset_id: Source asset ID (branch)
            target_asset_id: Target asset ID (main branch)
            source_branch: Branch name to merge
            merge_description: Optional merge description
            
        Returns:
            New AssetMetadata for the merged version, None if failed
        """
        try:
            # Get the latest version from the branch
            branch_history = self.get_branch_history(source_asset_id, source_branch)
            if not branch_history:
                self.logger.error(f"No history found for branch {source_branch}")
                return None
            
            latest_branch_version = max(branch_history, key=lambda x: x.version)
            
            # Get the current main version
            main_metadata = self.storage.get_asset(target_asset_id)
            if not main_metadata:
                self.logger.error(f"Target asset {target_asset_id} not found")
                return None
            
            # Create merge metadata
            merge_metadata = latest_branch_version.create_version(
                asset_id=target_asset_id,  # Use target asset ID
                version=main_metadata.version + 1,
                description=merge_description or f"Merged branch '{source_branch}'",
                updated_at=datetime.utcnow()
            )
            
            # Store the merge
            success = self.storage.store_asset(merge_metadata)
            
            if success:
                self.logger.info(f"Merged branch '{source_branch}' into asset {target_asset_id}")
                return merge_metadata
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error merging branch: {e}")
            return None
    
    def compare_versions(self, asset_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        Compare two specific versions and return detailed comparison.
        
        Args:
            asset_id: Asset ID
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dictionary with comparison results
        """
        try:
            version_diff = self.get_version_diff(asset_id, version1, version2)
            if not version_diff:
                return {"error": "Versions not found or comparison failed"}
            
            return {
                "asset_id": asset_id,
                "version1": version1,
                "version2": version2,
                "change_type": version_diff.change_type.value,
                "change_summary": version_diff.get_change_summary(),
                "changes": version_diff.changes,
                "significant_changes": version_diff.significant_changes,
                "is_major_change": version_diff.change_type in [
                    VersionChangeType.MAJOR, VersionChangeType.REBORN, VersionChangeType.REFORMAT
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return {"error": str(e)}
    
    def get_version_statistics(self, asset_id: str) -> Dict[str, Any]:
        """
        Get comprehensive version statistics for an asset.
        
        Args:
            asset_id: Asset ID to get statistics for
            
        Returns:
            Dictionary with version statistics
        """
        try:
            history = self.get_version_history(asset_id, include_deleted=True)
            
            if not history:
                return {"error": "No versions found"}
            
            # Calculate statistics
            total_versions = len(history)
            active_versions = len([v for v in history if v.status.value != 'deleted'])
            major_changes = 0
            minor_changes = 0
            
            # Analyze change types
            for i in range(1, len(history)):
                diff = VersionDiff(history[i-1], history[i])
                if diff.change_type in [VersionChangeType.MAJOR, VersionChangeType.REBORN, VersionChangeType.REFORMAT]:
                    major_changes += 1
                else:
                    minor_changes += 1
            
            # Timeline analysis
            if len(history) > 1:
                first_creation = min(v.created_at for v in history)
                last_update = max(v.updated_at for v in history)
                timespan_days = (last_update - first_creation).days
                avg_versions_per_day = total_versions / max(timespan_days, 1)
            else:
                timespan_days = 0
                avg_versions_per_day = 0
            
            # Size evolution
            size_changes = []
            for i in range(1, len(history)):
                if history[i].size_bytes != history[i-1].size_bytes:
                    size_changes.append({
                        'version': history[i].version,
                        'from_size': history[i-1].size_bytes,
                        'to_size': history[i].size_bytes,
                        'change_bytes': history[i].size_bytes - history[i-1].size_bytes
                    })
            
            return {
                "asset_id": asset_id,
                "total_versions": total_versions,
                "active_versions": active_versions,
                "major_changes": major_changes,
                "minor_changes": minor_changes,
                "first_created": min(v.created_at for v in history).isoformat(),
                "last_updated": max(v.updated_at for v in history).isoformat(),
                "timespan_days": timespan_days,
                "avg_versions_per_day": round(avg_versions_per_day, 2),
                "size_evolution": size_changes,
                "version_breakdown": {
                    "by_status": {status.value: len([v for v in history if v.status.value == status.value]) 
                                 for status in [v.status for v in history]},
                    "by_quality": {quality: len([v for v in history if v.quality == quality]) 
                                  for quality in set(v.quality for v in history if v.quality)}
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting version statistics: {e}")
            return {"error": str(e)}
    
    def cleanup_old_versions(self, asset_id: str, keep_versions: int = 10) -> int:
        """
        Clean up old versions keeping only the specified number of recent versions.
        
        Args:
            asset_id: Asset ID to clean up
            keep_versions: Number of recent versions to keep
            
        Returns:
            Number of versions cleaned up
        """
        try:
            history = self.get_version_history(asset_id, include_deleted=True)
            
            if len(history) <= keep_versions:
                return 0
            
            # Sort by version and identify versions to delete
            history.sort(key=lambda x: x.version, reverse=True)
            versions_to_delete = history[keep_versions:]
            
            cleaned_count = 0
            for version in versions_to_delete:
                if self.storage.delete_asset(f"{asset_id}:v{version.version}", permanent=True):
                    cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old versions for asset {asset_id}")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old versions: {e}")
            return 0