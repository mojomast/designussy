"""
Asset Metadata Schema

This module defines the comprehensive metadata model for tracking asset provenance,
versioning, and organization in the NanoBanana Generator system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class AssetFormat(str, Enum):
    """Supported asset formats."""
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"
    SVG = "svg"


class AssetCategory(str, Enum):
    """Asset categories for organization."""
    BACKGROUND = "backgrounds"
    GLYPH = "glyphs"
    CREATURE = "creatures"
    UI = "ui"


class AssetStatus(str, Enum):
    """Asset lifecycle status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"


class AssetMetadata(BaseModel):
    """
    Comprehensive metadata model for generated assets.
    
    This model captures all relevant information about an asset including:
    - Core identity and versioning information
    - Generation parameters and provenance
    - User-defined metadata for organization
    - Usage tracking and analytics
    - Relationships with other assets
    """
    
    # Core identity
    asset_id: str = Field(..., description="Unique asset identifier")
    version: int = Field(1, ge=1, description="Version number")
    parent_id: Optional[str] = Field(None, description="Parent asset ID for regenerations")
    
    # Generation information
    generator_type: str = Field(..., description="Generator that created this asset")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    seed: Optional[int] = Field(None, description="Random seed used for generation")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Asset properties
    width: int = Field(..., ge=1, description="Asset width in pixels")
    height: int = Field(..., ge=1, description="Asset height in pixels")
    format: AssetFormat = Field(..., description="Asset format")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    hash: str = Field(..., description="SHA256 hash of asset content")
    
    # User-defined metadata
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    category: Optional[AssetCategory] = Field(None, description="Asset category")
    description: Optional[str] = Field(None, description="User description")
    author: Optional[str] = Field(None, description="Creator name/identifier")
    title: Optional[str] = Field(None, description="Human-readable title")
    
    # Usage tracking
    access_count: int = Field(0, ge=0, description="Number of times accessed")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    download_count: int = Field(0, ge=0, description="Number of downloads")
    
    # Asset lifecycle
    status: AssetStatus = Field(AssetStatus.ACTIVE, description="Asset status")
    is_favorite: bool = Field(False, description="Marked as favorite")
    
    # Relationships
    related_assets: List[str] = Field(default_factory=list, description="Related asset IDs")
    derived_from: Optional[str] = Field(None, description="Source asset ID for derivatives")
    
    # Technical metadata
    quality: Optional[str] = Field(None, description="Generation quality setting")
    complexity: Optional[float] = Field(None, description="Complexity level (0.0-1.0)")
    randomness: Optional[float] = Field(None, description="Randomness level (0.0-1.0)")
    base_color: Optional[str] = Field(None, description="Base color hex")
    color_palette: Optional[List[str]] = Field(None, description="Custom color palette")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
    
    @classmethod
    def create_new(cls, generator_type: str, width: int, height: int, 
                   format: AssetFormat, size_bytes: int, hash: str,
                   **kwargs) -> 'AssetMetadata':
        """
        Create a new asset metadata entry.
        
        Args:
            generator_type: Type of generator used
            width: Asset width
            height: Asset height  
            format: Asset format
            size_bytes: File size
            hash: Content hash
            **kwargs: Additional metadata fields
            
        Returns:
            New AssetMetadata instance
        """
        return cls(
            asset_id=str(uuid.uuid4()),
            version=1,
            generator_type=generator_type,
            width=width,
            height=height,
            format=format,
            size_bytes=size_bytes,
            hash=hash,
            **kwargs
        )
    
    def create_version(self, **kwargs) -> 'AssetMetadata':
        """
        Create a new version of this asset.
        
        Args:
            **kwargs: Updated field values
            
        Returns:
            New AssetMetadata instance as a new version
        """
        new_data = self.dict()
        new_data.update(kwargs)
        new_data.update({
            'asset_id': self.asset_id,
            'version': self.version + 1,
            'parent_id': self.parent_id or self.asset_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        return cls(**new_data)
    
    def get_version_string(self) -> str:
        """
        Get human-readable version string.
        
        Returns:
            Version string in format "v{version}"
        """
        return f"v{self.version}"
    
    def get_file_extension(self) -> str:
        """
        Get file extension based on format.
        
        Returns:
            File extension string
        """
        format_map = {
            AssetFormat.PNG: ".png",
            AssetFormat.JPG: ".jpg",
            AssetFormat.JPEG: ".jpeg", 
            AssetFormat.WEBP: ".webp",
            AssetFormat.SVG: ".svg"
        }
        return format_map.get(self.format, ".png")
    
    def get_filename(self, include_version: bool = True) -> str:
        """
        Generate filename for the asset.
        
        Args:
            include_version: Whether to include version in filename
            
        Returns:
            Generated filename
        """
        version_str = self.get_version_string() if include_version else ""
        title = self.title or f"{self.generator_type}_{self.asset_id[:8]}"
        return f"{title}{version_str}{self.get_file_extension()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssetMetadata':
        """Create instance from dictionary."""
        return cls(**data)


class AssetVersion(BaseModel):
    """
    Model for tracking asset version relationships.
    """
    asset_id: str
    version: int
    parent_version: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    changes: Dict[str, Any] = Field(default_factory=dict)
    is_major_change: bool = Field(False)
    change_description: Optional[str] = None


class AssetRelationship(BaseModel):
    """
    Model for tracking relationships between assets.
    """
    source_id: str
    target_id: str
    relationship_type: str  # "derived_from", "related_to", "variant_of", etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssetAnalytics(BaseModel):
    """
    Model for tracking asset usage analytics.
    """
    asset_id: str
    date: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(0)
    download_count: int = Field(0)
    unique_users: int = Field(0)
    average_rating: Optional[float] = Field(None)
    tags_searched: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)


class MetadataQuery(BaseModel):
    """
    Model for metadata search queries.
    """
    text: Optional[str] = Field(None, description="Full-text search query")
    tags: Optional[List[str]] = Field(None, description="Required tags")
    category: Optional[AssetCategory] = Field(None, description="Asset category")
    generator_type: Optional[str] = Field(None, description="Generator type")
    author: Optional[str] = Field(None, description="Author filter")
    date_from: Optional[datetime] = Field(None, description="Created after date")
    date_to: Optional[datetime] = Field(None, description="Created before date")
    width_min: Optional[int] = Field(None, description="Minimum width")
    width_max: Optional[int] = Field(None, description="Maximum width")
    height_min: Optional[int] = Field(None, description="Minimum height")
    height_max: Optional[int] = Field(None, description="Maximum height")
    status: Optional[AssetStatus] = Field(None, description="Asset status")
    is_favorite: Optional[bool] = Field(None, description="Favorite filter")
    limit: int = Field(50, ge=1, le=1000, description="Results limit")
    offset: int = Field(0, ge=0, description="Results offset")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")


class MetadataStats(BaseModel):
    """
    Model for metadata system statistics.
    """
    total_assets: int
    total_versions: int
    total_tags: int
    assets_by_category: Dict[str, int]
    assets_by_generator: Dict[str, int]
    total_storage_bytes: int
    average_file_size: float
    most_popular_tags: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    database_size_bytes: int
    last_backup: Optional[datetime] = None