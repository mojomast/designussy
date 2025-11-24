"""
Tag Management System

This module provides comprehensive tag management capabilities including tag validation,
hierarchy support, popularity tracking, suggestions, and tag relationship management.
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum
import string

from .metadata_schema import AssetMetadata
from .asset_storage import AssetStorage, DatabaseConnection


class TagValidationError(Exception):
    """Exception raised for tag validation errors."""
    pass


class TagCategory(str, Enum):
    """Categories of tags for organization."""
    STYLE = "style"
    COLOR = "color"
    THEME = "theme"
    EMOTION = "emotion"
    QUALITY = "quality"
    COMPOSITION = "composition"
    SUBJECT = "subject"
    MOOD = "mood"
    CUSTOM = "custom"


@dataclass
class TagInfo:
    """Information about a tag including metadata."""
    name: str
    category: TagCategory
    usage_count: int
    first_used: datetime
    last_used: datetime
    popularity_score: float
    synonyms: List[str]
    related_tags: List[str]
    description: Optional[str] = None


@dataclass
class TagHierarchy:
    """Represents a hierarchical tag relationship."""
    parent_tag: str
    child_tags: List[str]
    relationship_type: str  # "broader", "narrower", "related"
    strength: float  # 0.0-1.0 strength of relationship


@dataclass
class TagSuggestion:
    """Tag suggestion with context and confidence."""
    tag: str
    category: TagCategory
    confidence: float
    reason: str
    usage_count: int
    synonyms: List[str] = None


class TagManager:
    """
    Comprehensive tag management system.
    
    Provides tag validation, categorization, hierarchy support, popularity tracking,
    intelligent suggestions, and relationship management.
    """
    
    def __init__(self, storage: AssetStorage):
        """
        Initialize the tag manager.
        
        Args:
            storage: AssetStorage instance for data access
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        
        # Tag configuration
        self.max_tag_length = int(os.getenv('MAX_TAG_LENGTH', '50'))
        self.max_tags_per_asset = int(os.getenv('MAX_TAGS_PER_ASSET', '20'))
        self.min_tag_length = int(os.getenv('MIN_TAG_LENGTH', '2'))
        self.popularity_threshold = int(os.getenv('TAG_POPULARITY_THRESHOLD', '5'))
        
        # Tag categories and their patterns
        self.tag_patterns = {
            TagCategory.COLOR: [
                r'.*(red|blue|green|yellow|purple|orange|pink|brown|black|white|gray|grey).*',
                r'.*(bright|dark|light|vibrant|pastel|neon).*',
                r'.*(color|色彩|颜色).*'
            ],
            TagCategory.STYLE: [
                r'.*(abstract|realistic|cartoon|anime|manga|sketch|painting|photo).*',
                r'.*(minimal|maximal|retro|vintage|modern|futuristic).*',
                r'.*(style|风格|样式).*'
            ],
            TagCategory.EMOTION: [
                r'.*(happy|sad|angry|calm|excited|peaceful|melancholic).*',
                r'.*(joy|sorrow|rage|serenity|bliss|despair).*',
                r'.*(emotion|feeling|mood|情感|情绪).*'
            ],
            TagCategory.THEME: [
                r'.*(fantasy|sci-fi|horror|romance|adventure|mystery).*',
                r'.*(mythology|legend|fairy|dragon|space|cyberpunk).*',
                r'.*(theme|主题|题材).*'
            ],
            TagCategory.QUALITY: [
                r'.*(high|low|medium|ultra|professional|amateur).*',
                r'.*(detailed|simple|complex|clean|noisy).*',
                r'.*(quality|resolution|清晰度|质量).*'
            ]
        }
        
        # Common tag synonyms
        self.tag_synonyms = {
            'dark': ['shadow', 'night', 'void', 'black', 'gloom'],
            'light': ['bright', 'glow', 'white', 'luminous', 'radiant'],
            'red': ['crimson', 'scarlet', 'ruby', 'blood'],
            'blue': ['azure', 'navy', 'cobalt', 'indigo'],
            'green': ['emerald', 'forest', 'jade', 'olive'],
            'happy': ['joyful', 'cheerful', 'bright', 'positive'],
            'sad': ['melancholy', 'blue', 'gloomy', 'dejected'],
            'modern': ['contemporary', 'current', 'new', 'fresh'],
            'vintage': ['classic', 'retro', 'old', 'antique', 'nostalgic'],
            'fantasy': ['magical', 'mystical', 'enchanted', 'mythical'],
            'realistic': ['photorealistic', 'lifelike', 'natural', 'true']
        }
        
        # Popular tags cache
        self._popular_tags_cache = None
        self._cache_timestamp = None
        self._cache_duration = timedelta(hours=1)
        
        # Tag hierarchy cache
        self._hierarchy_cache = {}
    
    def validate_tag(self, tag: str) -> Tuple[bool, List[str]]:
        """
        Validate a tag and return validation results.
        
        Args:
            tag: Tag to validate
            
        Returns:
            Tuple of (is_valid, validation_messages)
        """
        errors = []
        
        if not tag or not tag.strip():
            errors.append("Tag cannot be empty")
            return False, errors
        
        tag_clean = tag.strip().lower()
        
        # Length validation
        if len(tag_clean) < self.min_tag_length:
            errors.append(f"Tag too short (minimum {self.min_tag_length} characters)")
        
        if len(tag_clean) > self.max_tag_length:
            errors.append(f"Tag too long (maximum {self.max_tag_length} characters)")
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag_clean):
            errors.append("Tag can only contain letters, numbers, spaces, hyphens, and underscores")
        
        # Reserved words validation
        reserved_words = {'admin', 'system', 'null', 'undefined', 'delete', 'update', 'select'}
        if tag_clean in reserved_words:
            errors.append(f"'{tag_clean}' is a reserved word")
        
        # No consecutive special characters
        if re.search(r'[-_]{2,}', tag_clean):
            errors.append("Tag cannot contain consecutive hyphens or underscores")
        
        # No leading/trailing special characters
        if re.match(r'^[-_]', tag_clean) or re.match(r'[-_]$', tag_clean):
            errors.append("Tag cannot start or end with hyphens or underscores")
        
        return len(errors) == 0, errors
    
    def validate_tags(self, tags: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of tags.
        
        Args:
            tags: List of tags to validate
            
        Returns:
            Tuple of (valid_tags, invalid_tags)
        """
        valid_tags = []
        invalid_tags = []
        
        # Check maximum number of tags
        if len(tags) > self.max_tags_per_asset:
            self.logger.warning(f"Too many tags: {len(tags)} > {self.max_tags_per_asset}")
        
        for tag in tags[:self.max_tags_per_asset]:  # Limit to max tags
            is_valid, errors = self.validate_tag(tag)
            if is_valid:
                valid_tags.append(tag.strip().lower())
            else:
                invalid_tags.append(tag)
                self.logger.warning(f"Invalid tag '{tag}': {'; '.join(errors)}")
        
        return valid_tags, invalid_tags
    
    def categorize_tag(self, tag: str) -> TagCategory:
        """
        Automatically categorize a tag based on patterns and content.
        
        Args:
            tag: Tag to categorize
            
        Returns:
            TagCategory for the tag
        """
        tag_lower = tag.lower()
        
        # Check against patterns
        for category, patterns in self.tag_patterns.items():
            for pattern in patterns:
                if re.match(pattern, tag_lower, re.IGNORECASE):
                    return category
        
        # Check synonyms
        for synonym_group, synonyms in self.tag_synonyms.items():
            if tag_lower in synonyms:
                # Determine category based on synonym group
                if synonym_group in ['red', 'blue', 'green', 'dark', 'light']:
                    return TagCategory.COLOR
                elif synonym_group in ['happy', 'sad', 'emotion']:
                    return TagCategory.EMOTION
                elif synonym_group in ['modern', 'vintage', 'style']:
                    return TagCategory.STYLE
                elif synonym_group in ['fantasy', 'theme']:
                    return TagCategory.THEME
                elif synonym_group in ['high', 'low', 'quality']:
                    return TagCategory.QUALITY
        
        # Default category
        return TagCategory.CUSTOM
    
    def get_tag_info(self, tag: str) -> Optional[TagInfo]:
        """
        Get comprehensive information about a tag.
        
        Args:
            tag: Tag to get information for
            
        Returns:
            TagInfo object or None if tag not found
        """
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Get tag usage statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as usage_count,
                        MIN(created_at) as first_used,
                        MAX(a.created_at) as last_used
                    FROM asset_tags at
                    JOIN assets a ON at.asset_id = a.asset_id
                    WHERE at.tag = ? AND a.status != 'deleted'
                """, (tag.lower(),))
                
                row = cursor.fetchone()
                if not row or row['usage_count'] == 0:
                    return None
                
                usage_count = row['usage_count']
                first_used = datetime.fromisoformat(row['first_used'].replace('Z', '+00:00'))
                last_used = datetime.fromisoformat(row['last_used'].replace('Z', '+00:00'))
                
                # Calculate popularity score
                days_active = (last_used - first_used).days + 1
                popularity_score = usage_count / max(days_active, 1)
                
                # Get synonyms
                synonyms = self._get_tag_synonyms(tag)
                
                # Get related tags
                related_tags = self._get_related_tags(tag, cursor)
                
                # Categorize tag
                category = self.categorize_tag(tag)
                
                return TagInfo(
                    name=tag,
                    category=category,
                    usage_count=usage_count,
                    first_used=first_used,
                    last_used=last_used,
                    popularity_score=popularity_score,
                    synonyms=synonyms,
                    related_tags=related_tags,
                    description=self._get_tag_description(tag)
                )
                
        except Exception as e:
            self.logger.error(f"Error getting tag info for '{tag}': {e}")
            return None
    
    def get_popular_tags(self, limit: int = 50, category: Optional[TagCategory] = None,
                        days: Optional[int] = None) -> List[TagInfo]:
        """
        Get popular tags with filtering options.
        
        Args:
            limit: Maximum number of tags to return
            category: Filter by tag category
            days: Only consider tags used in the last N days
            
        Returns:
            List of TagInfo objects sorted by popularity
        """
        try:
            # Check cache first
            cache_key = f"popular_{limit}_{category}_{days}"
            if (self._popular_tags_cache and self._cache_timestamp and
                datetime.utcnow() - self._cache_timestamp < self._cache_duration):
                return self._popular_tags_cache.get(cache_key, [])
            
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with date filter
                date_filter = ""
                params = []
                
                if days:
                    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
                    date_filter = "AND a.created_at >= ?"
                    params.append(cutoff_date)
                
                cursor.execute(f"""
                    SELECT 
                        at.tag,
                        COUNT(*) as usage_count,
                        MIN(a.created_at) as first_used,
                        MAX(a.created_at) as last_used
                    FROM asset_tags at
                    JOIN assets a ON at.asset_id = a.asset_id
                    WHERE a.status != 'deleted' {date_filter}
                    GROUP BY at.tag
                    HAVING usage_count >= ?
                    ORDER BY usage_count DESC
                    LIMIT ?
                """, params + [self.popularity_threshold, limit])
                
                popular_tags = []
                
                for row in cursor.fetchall():
                    tag = row['tag']
                    usage_count = row['usage_count']
                    first_used = datetime.fromisoformat(row['first_used'].replace('Z', '+00:00'))
                    last_used = datetime.fromisoformat(row['last_used'].replace('Z', '+00:00'))
                    
                    # Categorize tag
                    tag_category = self.categorize_tag(tag)
                    
                    # Filter by category if specified
                    if category and tag_category != category:
                        continue
                    
                    # Calculate popularity score
                    days_active = (last_used - first_used).days + 1
                    popularity_score = usage_count / max(days_active, 1)
                    
                    tag_info = TagInfo(
                        name=tag,
                        category=tag_category,
                        usage_count=usage_count,
                        first_used=first_used,
                        last_used=last_used,
                        popularity_score=popularity_score,
                        synonyms=self._get_tag_synonyms(tag),
                        related_tags=self._get_related_tags(tag, cursor)
                    )
                    
                    popular_tags.append(tag_info)
                
                # Cache results
                if not self._popular_tags_cache:
                    self._popular_tags_cache = {}
                self._popular_tags_cache[cache_key] = popular_tags
                self._cache_timestamp = datetime.utcnow()
                
                return popular_tags
                
        except Exception as e:
            self.logger.error(f"Error getting popular tags: {e}")
            return []
    
    def suggest_tags(self, asset: AssetMetadata, limit: int = 10) -> List[TagSuggestion]:
        """
        Generate intelligent tag suggestions for an asset.
        
        Args:
            asset: Asset to suggest tags for
            limit: Maximum number of suggestions
            
        Returns:
            List of TagSuggestion objects
        """
        suggestions = []
        
        try:
            # Suggest based on generator type
            generator_suggestions = self._suggest_from_generator(asset.generator_type)
            suggestions.extend(generator_suggestions)
            
            # Suggest based on existing tags in similar assets
            similar_suggestions = self._suggest_from_similar_assets(asset)
            suggestions.extend(similar_suggestions)
            
            # Suggest based on parameters
            parameter_suggestions = self._suggest_from_parameters(asset.parameters)
            suggestions.extend(parameter_suggestions)
            
            # Suggest based on title/description
            text_suggestions = self._suggest_from_text(asset.title, asset.description)
            suggestions.extend(text_suggestions)
            
            # Suggest based on quality settings
            quality_suggestions = self._suggest_from_quality(asset)
            suggestions.extend(quality_suggestions)
            
            # Deduplicate and sort by confidence
            seen_tags = set()
            unique_suggestions = []
            
            for suggestion in suggestions:
                if suggestion.tag not in seen_tags:
                    seen_tags.add(suggestion.tag)
                    unique_suggestions.append(suggestion)
            
            # Sort by confidence and usage count
            unique_suggestions.sort(key=lambda x: (x.confidence, x.usage_count), reverse=True)
            
            return unique_suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"Error suggesting tags: {e}")
            return []
    
    def _suggest_from_generator(self, generator_type: str) -> List[TagSuggestion]:
        """Suggest tags based on generator type."""
        suggestions = []
        
        # Generator-specific tag mappings
        generator_tags = {
            'parchment': [('texture', TagCategory.STYLE, 0.9), ('background', TagCategory.COMPOSITION, 0.8),
                         ('paper', TagCategory.SUBJECT, 0.7), ('aged', TagCategory.STYLE, 0.8)],
            'enso': [('circle', TagCategory.SUBJECT, 0.9), ('zen', TagCategory.MOOD, 0.8),
                    ('meditation', TagCategory.MOOD, 0.7), ('spiritual', TagCategory.THEME, 0.8)],
            'sigil': [('magic', TagCategory.THEME, 0.9), ('symbol', TagCategory.SUBJECT, 0.8),
                     ('mystical', TagCategory.THEME, 0.8), ('occult', TagCategory.THEME, 0.7)],
            'giraffe': [('animal', TagCategory.SUBJECT, 0.9), ('tall', TagCategory.QUALITY, 0.7),
                       ('spots', TagCategory.COLOR, 0.8), ('nature', TagCategory.THEME, 0.7)],
            'kangaroo': [('animal', TagCategory.SUBJECT, 0.9), ('marsupial', TagCategory.SUBJECT, 0.8),
                        ('jumping', TagCategory.STYLE, 0.7), ('australian', TagCategory.THEME, 0.6)]
        }
        
        if generator_type in generator_tags:
            for tag_name, category, confidence in generator_tags[generator_type]:
                suggestions.append(TagSuggestion(
                    tag=tag_name,
                    category=category,
                    confidence=confidence,
                    reason=f"Common tag for {generator_type} generators",
                    usage_count=0,
                    synonyms=self._get_tag_synonyms(tag_name)
                ))
        
        return suggestions
    
    def _suggest_from_similar_assets(self, asset: AssetMetadata) -> List[TagSuggestion]:
        """Suggest tags from similar assets."""
        suggestions = []
        
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Find assets with similar characteristics
                query_conditions = ["a.status != 'deleted'"]
                params = []
                
                if asset.category:
                    query_conditions.append("a.category = ?")
                    params.append(asset.category.value)
                
                query_conditions.append("a.generator_type = ?")
                params.append(asset.generator_type)
                
                # Get tags from similar assets
                cursor.execute(f"""
                    SELECT DISTINCT at2.tag, COUNT(*) as usage_count
                    FROM assets a1
                    JOIN assets a2 ON a1.generator_type = a2.generator_type 
                           AND (a1.category = a2.category OR a1.category IS NULL OR a2.category IS NULL)
                    JOIN asset_tags at1 ON a1.asset_id = at1.asset_id
                    JOIN asset_tags at2 ON a2.asset_id = at2.asset_id
                    WHERE a1.asset_id = ? AND a2.asset_id != a1.asset_id
                          AND {' AND '.join(query_conditions)}
                    GROUP BY at2.tag
                    ORDER BY usage_count DESC
                    LIMIT 20
                """, [asset.asset_id] + params)
                
                for row in cursor.fetchall():
                    tag = row['tag']
                    usage_count = row['usage_count']
                    
                    # Skip if asset already has this tag
                    if tag in asset.tags:
                        continue
                    
                    # Calculate confidence based on usage frequency
                    confidence = min(0.8, usage_count / 10.0)
                    
                    suggestions.append(TagSuggestion(
                        tag=tag,
                        category=self.categorize_tag(tag),
                        confidence=confidence,
                        reason=f"Used in {usage_count} similar assets",
                        usage_count=usage_count,
                        synonyms=self._get_tag_synonyms(tag)
                    ))
                
        except Exception as e:
            self.logger.error(f"Error getting similar asset tags: {e}")
        
        return suggestions
    
    def _suggest_from_parameters(self, parameters: Dict[str, Any]) -> List[TagSuggestion]:
        """Suggest tags based on generation parameters."""
        suggestions = []
        
        if not parameters:
            return suggestions
        
        # Parameter-based tag mappings
        param_mappings = {
            'complexity': {1: [('simple', TagCategory.QUALITY, 0.7)],
                          5: [('detailed', TagCategory.QUALITY, 0.8)],
                          10: [('complex', TagCategory.QUALITY, 0.9)]},
            'quality': {'low': [('draft', TagCategory.QUALITY, 0.6)],
                       'high': [('polished', TagCategory.QUALITY, 0.8)],
                       'ultra': [('premium', TagCategory.QUALITY, 0.9)]},
            'chaos': {0.5: [('ordered', TagCategory.STYLE, 0.7)],
                     1.0: [('balanced', TagCategory.STYLE, 0.8)],
                     2.0: [('chaotic', TagCategory.STYLE, 0.9)]}
        }
        
        for param_name, value in parameters.items():
            if param_name in param_mappings and value in param_mappings[param_name]:
                for tag_name, category, confidence in param_mappings[param_name][value]:
                    suggestions.append(TagSuggestion(
                        tag=tag_name,
                        category=category,
                        confidence=confidence,
                        reason=f"Based on {param_name}={value}",
                        usage_count=0,
                        synonyms=self._get_tag_synonyms(tag_name)
                    ))
        
        return suggestions
    
    def _suggest_from_text(self, title: Optional[str], description: Optional[str]) -> List[TagSuggestion]:
        """Suggest tags based on title and description text."""
        suggestions = []
        
        text = f"{title or ''} {description or ''}".lower()
        
        # Extract meaningful words from text
        import string
        translator = str.maketrans('', '', string.punctuation)
        cleaned_text = text.translate(translator)
        words = cleaned_text.split()
        
        # Filter words and create tag suggestions
        meaningful_words = [word for word in words 
                          if len(word) >= 3 and word not in self._get_stop_words()]
        
        for word in meaningful_words[:5]:  # Limit to top 5 words
            # Check if this might be a good tag
            is_valid, errors = self.validate_tag(word)
            if is_valid and len(word) <= self.max_tag_length:
                suggestions.append(TagSuggestion(
                    tag=word,
                    category=self.categorize_tag(word),
                    confidence=0.5,
                    reason="Extracted from text",
                    usage_count=0,
                    synonyms=self._get_tag_synonyms(word)
                ))
        
        return suggestions
    
    def _suggest_from_quality(self, asset: AssetMetadata) -> List[TagSuggestion]:
        """Suggest tags based on asset quality settings."""
        suggestions = []
        
        # Quality-based suggestions
        if asset.quality:
            quality_tags = {
                'low': [('rough', TagCategory.QUALITY, 0.6), ('sketch', TagCategory.STYLE, 0.7)],
                'medium': [('balanced', TagCategory.QUALITY, 0.7), ('standard', TagCategory.QUALITY, 0.6)],
                'high': [('refined', TagCategory.QUALITY, 0.8), ('detailed', TagCategory.QUALITY, 0.9)],
                'ultra': [('premium', TagCategory.QUALITY, 0.9), ('perfect', TagCategory.QUALITY, 0.8)]
            }
            
            if asset.quality in quality_tags:
                for tag_name, category, confidence in quality_tags[asset.quality]:
                    suggestions.append(TagSuggestion(
                        tag=tag_name,
                        category=category,
                        confidence=confidence,
                        reason=f"Based on {asset.quality} quality",
                        usage_count=0,
                        synonyms=self._get_tag_synonyms(tag_name)
                    ))
        
        return suggestions
    
    def get_tag_hierarchy(self) -> Dict[str, TagHierarchy]:
        """
        Get the complete tag hierarchy.
        
        Returns:
            Dictionary mapping parent tags to TagHierarchy objects
        """
        try:
            if self._hierarchy_cache:
                return self._hierarchy_cache
            
            hierarchy = {}
            
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Get tag co-occurrence data
                cursor.execute("""
                    SELECT 
                        at1.tag as tag1,
                        at2.tag as tag2,
                        COUNT(*) as cooccurrence
                    FROM asset_tags at1
                    JOIN asset_tags at2 ON at1.asset_id = at2.asset_id
                    WHERE at1.tag < at2.tag  -- Avoid duplicates
                    GROUP BY at1.tag, at2.tag
                    HAVING cooccurrence >= 3  -- Minimum co-occurrence threshold
                    ORDER BY cooccurrence DESC
                """)
                
                tag_relationships = defaultdict(list)
                
                for row in cursor.fetchall():
                    tag1 = row['tag1']
                    tag2 = row['tag2']
                    cooccurrence = row['cooccurrence']
                    
                    # Determine relationship type and strength
                    if cooccurrence >= 10:
                        relationship_type = "broader"
                        strength = min(1.0, cooccurrence / 20.0)
                    elif cooccurrence >= 5:
                        relationship_type = "related"
                        strength = min(1.0, cooccurrence / 10.0)
                    else:
                        relationship_type = "related"
                        strength = cooccurrence / 10.0
                    
                    # Create bidirectional relationships
                    tag_relationships[tag1].append((tag2, relationship_type, strength))
                    tag_relationships[tag2].append((tag1, relationship_type, strength))
            
            # Build hierarchy
            for parent_tag, relationships in tag_relationships.items():
                child_tags = [tag for tag, rel_type, strength in relationships 
                             if rel_type == "broader"]
                related_tags = [tag for tag, rel_type, strength in relationships 
                               if rel_type == "related"]
                
                # Calculate average strength
                if relationships:
                    avg_strength = sum(strength for _, _, strength in relationships) / len(relationships)
                else:
                    avg_strength = 0.0
                
                hierarchy[parent_tag] = TagHierarchy(
                    parent_tag=parent_tag,
                    child_tags=child_tags,
                    related_tags=related_tags,
                    relationship_type="root",
                    strength=avg_strength
                )
            
            # Cache the hierarchy
            self._hierarchy_cache = hierarchy
            
            return hierarchy
            
        except Exception as e:
            self.logger.error(f"Error getting tag hierarchy: {e}")
            return {}
    
    def search_tags(self, query: str, limit: int = 20) -> List[TagInfo]:
        """
        Search for tags by name or description.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of TagInfo objects matching the query
        """
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Search in tag names
                cursor.execute("""
                    SELECT 
                        at.tag,
                        COUNT(*) as usage_count,
                        MIN(a.created_at) as first_used,
                        MAX(a.created_at) as last_used
                    FROM asset_tags at
                    JOIN assets a ON at.asset_id = a.asset_id
                    WHERE at.tag LIKE ? AND a.status != 'deleted'
                    GROUP BY at.tag
                    HAVING usage_count >= ?
                    ORDER BY usage_count DESC
                    LIMIT ?
                """, (f"%{query.lower()}%", self.popularity_threshold, limit))
                
                tags = []
                
                for row in cursor.fetchall():
                    tag = row['tag']
                    usage_count = row['usage_count']
                    first_used = datetime.fromisoformat(row['first_used'].replace('Z', '+00:00'))
                    last_used = datetime.fromisoformat(row['last_used'].replace('Z', '+00:00'))
                    
                    # Calculate popularity score
                    days_active = (last_used - first_used).days + 1
                    popularity_score = usage_count / max(days_active, 1)
                    
                    tag_info = TagInfo(
                        name=tag,
                        category=self.categorize_tag(tag),
                        usage_count=usage_count,
                        first_used=first_used,
                        last_used=last_used,
                        popularity_score=popularity_score,
                        synonyms=self._get_tag_synonyms(tag),
                        related_tags=self._get_related_tags(tag, cursor)
                    )
                    
                    tags.append(tag_info)
                
                return tags
                
        except Exception as e:
            self.logger.error(f"Error searching tags: {e}")
            return []
    
    def merge_tags(self, source_tag: str, target_tag: str) -> bool:
        """
        Merge one tag into another (move all usage from source to target).
        
        Args:
            source_tag: Tag to merge from
            target_tag: Tag to merge to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Validate both tags exist
                cursor.execute("SELECT tag FROM asset_tags WHERE tag = ?", (source_tag,))
                if not cursor.fetchone():
                    self.logger.error(f"Source tag '{source_tag}' not found")
                    return False
                
                cursor.execute("SELECT tag FROM asset_tags WHERE tag = ?", (target_tag,))
                if not cursor.fetchone():
                    self.logger.error(f"Target tag '{target_tag}' not found")
                    return False
                
                # Check for conflicts (same asset having both tags)
                cursor.execute("""
                    SELECT at1.asset_id
                    FROM asset_tags at1
                    JOIN asset_tags at2 ON at1.asset_id = at2.asset_id
                    WHERE at1.tag = ? AND at2.tag = ?
                    LIMIT 1
                """, (source_tag, target_tag))
                
                if cursor.fetchone():
                    self.logger.warning(f"Cannot merge: some assets have both '{source_tag}' and '{target_tag}' tags")
                    return False
                
                # Merge tags
                cursor.execute("""
                    UPDATE asset_tags 
                    SET tag = ?
                    WHERE tag = ?
                """, (target_tag, source_tag))
                
                affected_rows = cursor.rowcount
                conn.commit()
                
                # Clear caches
                self._clear_caches()
                
                self.logger.info(f"Merged {affected_rows} tag instances from '{source_tag}' to '{target_tag}'")
                return affected_rows > 0
                
        except Exception as e:
            self.logger.error(f"Error merging tags: {e}")
            return False
    
    def delete_tag(self, tag: str, keep_usage: bool = False) -> bool:
        """
        Delete a tag from the system.
        
        Args:
            tag: Tag to delete
            keep_usage: Whether to keep asset usage or remove it
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                if keep_usage:
                    # Just remove the tag from tracking but keep asset associations
                    cursor.execute("DELETE FROM asset_tags WHERE tag = ?", (tag,))
                else:
                    # Completely remove the tag
                    cursor.execute("DELETE FROM asset_tags WHERE tag = ?", (tag,))
                
                affected_rows = cursor.rowcount
                conn.commit()
                
                # Clear caches
                self._clear_caches()
                
                self.logger.info(f"Deleted tag '{tag}' ({affected_rows} usage instances)")
                return affected_rows > 0
                
        except Exception as e:
            self.logger.error(f"Error deleting tag: {e}")
            return False
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive tag statistics.
        
        Returns:
            Dictionary with tag statistics
        """
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(DISTINCT tag) as count FROM asset_tags")
                total_tags = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM asset_tags")
                total_usage = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(DISTINCT asset_id) as count FROM asset_tags")
                tagged_assets = cursor.fetchone()['count']
                
                # Usage distribution
                cursor.execute("""
                    SELECT 
                        usage_count,
                        COUNT(*) as tag_count
                    FROM (
                        SELECT tag, COUNT(*) as usage_count
                        FROM asset_tags
                        GROUP BY tag
                    ) t
                    GROUP BY usage_count
                    ORDER BY usage_count DESC
                    LIMIT 10
                """)
                usage_distribution = [dict(row) for row in cursor.fetchall()]
                
                # Category distribution
                category_stats = defaultdict(int)
                
                # Get all tags and categorize them
                cursor.execute("SELECT DISTINCT tag FROM asset_tags ORDER BY tag")
                for row in cursor.fetchall():
                    tag = row['tag']
                    category = self.categorize_tag(tag)
                    category_stats[category.value] += 1
                
                # Recent tag activity (last 30 days)
                cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM asset_tags at
                    JOIN assets a ON at.asset_id = a.asset_id
                    WHERE a.created_at >= ?
                """, (cutoff_date,))
                recent_usage = cursor.fetchone()['count']
                
                return {
                    'total_tags': total_tags,
                    'total_usage': total_usage,
                    'tagged_assets': tagged_assets,
                    'average_usage_per_tag': total_usage / max(total_tags, 1),
                    'usage_distribution': usage_distribution,
                    'category_distribution': dict(category_stats),
                    'recent_usage_30_days': recent_usage,
                    'most_popular_tag': self._get_most_popular_tag(cursor)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting tag statistics: {e}")
            return {}
    
    def _get_tag_synonyms(self, tag: str) -> List[str]:
        """Get synonyms for a tag."""
        tag_lower = tag.lower()
        
        # Check if tag has defined synonyms
        for synonym_group, synonyms in self.tag_synonyms.items():
            if tag_lower in synonyms:
                return [s for s in synonyms if s != tag_lower]
        
        return []
    
    def _get_related_tags(self, tag: str, cursor) -> List[str]:
        """Get tags related to the given tag."""
        try:
            cursor.execute("""
                SELECT DISTINCT at2.tag
                FROM asset_tags at1
                JOIN asset_tags at2 ON at1.asset_id = at2.asset_id
                WHERE at1.tag = ? AND at2.tag != ?
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """, (tag, tag))
            
            return [row['tag'] for row in cursor.fetchall()]
            
        except Exception:
            return []
    
    def _get_tag_description(self, tag: str) -> Optional[str]:
        """Get a description for a tag."""
        # Simple tag descriptions
        descriptions = {
            'dark': 'Tags related to dark, shadowy, or nocturnal themes',
            'light': 'Tags related to bright, luminous, or daytime themes',
            'abstract': 'Non-representational or conceptual art styles',
            'realistic': 'Photorealistic or lifelike representations',
            'fantasy': 'Imaginative or supernatural themes',
            'minimal': 'Simple, clean, or minimalist designs',
            'detailed': 'Rich in detail and complexity',
            'vintage': 'Classic, retro, or historical styling'
        }
        
        return descriptions.get(tag.lower())
    
    def _get_stop_words(self) -> Set[str]:
        """Get stop words for tag processing."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'been', 'be', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
    
    def _get_most_popular_tag(self, cursor) -> Optional[str]:
        """Get the most popular tag."""
        cursor.execute("""
            SELECT tag, COUNT(*) as usage_count
            FROM asset_tags
            GROUP BY tag
            ORDER BY usage_count DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        return row['tag'] if row else None
    
    def _clear_caches(self):
        """Clear all internal caches."""
        self._popular_tags_cache = None
        self._cache_timestamp = None
        self._hierarchy_cache = {}
    
    def cleanup_orphan_tags(self) -> int:
        """
        Remove tags that are no longer associated with any active assets.
        
        Returns:
            Number of tags cleaned up
        """
        try:
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Find orphan tags (tags without active asset associations)
                cursor.execute("""
                    SELECT DISTINCT at.tag
                    FROM asset_tags at
                    LEFT JOIN assets a ON at.asset_id = a.asset_id AND a.status != 'deleted'
                    WHERE a.asset_id IS NULL
                """)
                
                orphan_tags = [row['tag'] for row in cursor.fetchall()]
                
                # Delete orphan tags
                cleaned_count = 0
                for tag in orphan_tags:
                    cursor.execute("DELETE FROM asset_tags WHERE tag = ?", (tag,))
                    cleaned_count += cursor.rowcount
                
                conn.commit()
                
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} orphan tag instances")
                    self._clear_caches()
                
                return len(orphan_tags)
                
        except Exception as e:
            self.logger.error(f"Error cleaning up orphan tags: {e}")
            return 0