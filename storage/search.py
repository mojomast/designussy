"""
Asset Search Engine

This module provides comprehensive search capabilities for the asset metadata system,
including full-text search, advanced filtering, similarity matching, and search analytics.
"""

import os
import re
import json
import logging
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

from .metadata_schema import AssetMetadata, MetadataQuery, AssetCategory, AssetStatus
from .asset_storage import AssetStorage


class SearchType(str, Enum):
    """Types of search operations."""
    EXACT = "exact"              # Exact match
    FUZZY = "fuzzy"              # Fuzzy matching
    SEMANTIC = "semantic"        # Semantic similarity (placeholder)
    TAG_BASED = "tag_based"      # Tag-based search
    PARAMETER_MATCH = "parameter_match"  # Parameter-based matching


class SearchRelevance(str, Enum):
    """Search result relevance levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SearchResult:
    """Individual search result with relevance scoring."""
    asset: AssetMetadata
    relevance_score: float
    relevance_level: SearchRelevance
    matched_fields: List[str]
    highlights: Dict[str, str]  # field -> highlighted_text
    explanation: Optional[str] = None


@dataclass
class SearchFacet:
    """Search facet for filtering and exploration."""
    name: str
    values: List[Dict[str, Any]]  # [{"value": ..., "count": ...}]
    total_count: int


@dataclass
class SearchAnalytics:
    """Search analytics and insights."""
    total_searches: int
    unique_queries: int
    popular_terms: List[Tuple[str, int]]
    search_types: Dict[str, int]
    avg_results_per_query: float
    no_result_queries: List[str]
    search_trends: Dict[str, int]  # date -> count


class AssetSearchEngine:
    """
    Advanced search engine for asset metadata.
    
    Provides full-text search, advanced filtering, similarity matching,
    search analytics, and intelligent suggestions.
    """
    
    def __init__(self, storage: AssetStorage):
        """
        Initialize the search engine.
        
        Args:
            storage: AssetStorage instance for data access
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        
        # Search configuration
        self.min_relevance_score = float(os.getenv('MIN_RELEVANCE_SCORE', '0.1'))
        self.max_results_per_query = int(os.getenv('SEARCH_MAX_RESULTS', '1000'))
        self.suggestion_limit = int(os.getenv('SEARCH_SUGGESTION_LIMIT', '10'))
        
        # Search analytics
        self._search_analytics = {
            'total_searches': 0,
            'query_history': [],
            'facet_clicks': defaultdict(int),
            'no_result_queries': set()
        }
        
        # Common stop words for search
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Tag synonyms for better search
        self.tag_synonyms = {
            'dark': ['void', 'black', 'night', 'shadow'],
            'light': ['bright', 'white', 'day', 'glow'],
            'geometric': ['shape', 'pattern', 'form', 'structure'],
            'organic': ['natural', 'flowing', 'curved', 'living'],
            'mystical': ['magic', 'arcane', 'enchanted', 'supernatural'],
            'modern': ['contemporary', 'current', 'new', 'fresh'],
            'vintage': ['classic', 'retro', 'old', 'antique']
        }
    
    def search(self, query: MetadataQuery) -> Tuple[List[SearchResult], int, Dict[str, Any]]:
        """
        Perform a comprehensive search with relevance scoring.
        
        Args:
            query: MetadataQuery with search criteria
            
        Returns:
            Tuple of (search_results, total_count, search_facets)
        """
        try:
            # Get base results from storage
            assets, total_count = self.storage.get_assets_by_query(query)
            
            # Apply relevance scoring and ranking
            search_results = self._rank_results(query, assets)
            
            # Generate search facets for filtering
            facets = self._generate_facets(assets, total_count)
            
            # Update analytics
            self._update_analytics(query, search_results, total_count)
            
            return search_results, total_count, facets
            
        except Exception as e:
            self.logger.error(f"Error performing search: {e}")
            return [], 0, {}
    
    def _rank_results(self, query: MetadataQuery, assets: List[AssetMetadata]) -> List[SearchResult]:
        """
        Rank search results by relevance.
        
        Args:
            query: The search query
            assets: List of assets to rank
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        if not assets:
            return []
        
        search_results = []
        
        for asset in assets:
            result = self._calculate_relevance(query, asset)
            if result.relevance_score >= self.min_relevance_score:
                search_results.append(result)
        
        # Sort by relevance score (descending)
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Apply limit
        return search_results[:query.limit]
    
    def _calculate_relevance(self, query: MetadataQuery, asset: AssetMetadata) -> SearchResult:
        """
        Calculate relevance score for an asset against the query.
        
        Args:
            query: The search query
            asset: Asset to calculate relevance for
            
        Returns:
            SearchResult with relevance scoring
        """
        relevance_score = 0.0
        matched_fields = []
        highlights = {}
        explanation_parts = []
        
        # Text search relevance (0-40 points)
        if query.text:
            text_score, text_fields, text_highlights = self._calculate_text_relevance(query.text, asset)
            relevance_score += text_score
            matched_fields.extend(text_fields)
            highlights.update(text_highlights)
            if text_score > 0:
                explanation_parts.append(f"Text match: {text_score:.1f}")
        
        # Tag relevance (0-30 points)
        if query.tags:
            tag_score, matched_tags = self._calculate_tag_relevance(query.tags, asset)
            relevance_score += tag_score
            if tag_score > 0:
                matched_fields.append('tags')
                explanation_parts.append(f"Tag match: {tag_score:.1f} ({matched_tags})")
        
        # Category relevance (0-15 points)
        if query.category:
            if asset.category == query.category:
                relevance_score += 15.0
                matched_fields.append('category')
                explanation_parts.append("Category match: 15.0")
        
        # Generator type relevance (0-10 points)
        if query.generator_type:
            if asset.generator_type == query.generator_type:
                relevance_score += 10.0
                matched_fields.append('generator_type')
                explanation_parts.append("Generator match: 10.0")
        
        # Author relevance (0-10 points)
        if query.author:
            if asset.author and asset.author.lower() == query.author.lower():
                relevance_score += 10.0
                matched_fields.append('author')
                explanation_parts.append("Author match: 10.0")
        
        # Date relevance (0-5 points) - recency bonus
        if query.date_from or query.date_to:
            date_score = self._calculate_date_relevance(asset.created_at, query.date_from, query.date_to)
            relevance_score += date_score
            if date_score > 0:
                explanation_parts.append(f"Date relevance: {date_score:.1f}")
        
        # Dimension relevance (0-5 points)
        dim_score = self._calculate_dimension_relevance(asset, query)
        relevance_score += dim_score
        if dim_score > 0:
            explanation_parts.append(f"Dimension match: {dim_score:.1f}")
        
        # Determine relevance level
        if relevance_score >= 30.0:
            relevance_level = SearchRelevance.HIGH
        elif relevance_score >= 15.0:
            relevance_level = SearchRelevance.MEDIUM
        else:
            relevance_level = SearchRelevance.LOW
        
        explanation = "; ".join(explanation_parts) if explanation_parts else "No specific matches"
        
        return SearchResult(
            asset=asset,
            relevance_score=relevance_score,
            relevance_level=relevance_level,
            matched_fields=list(set(matched_fields)),  # Remove duplicates
            highlights=highlights,
            explanation=explanation
        )
    
    def _calculate_text_relevance(self, search_text: str, asset: AssetMetadata) -> Tuple[float, List[str], Dict[str, str]]:
        """
        Calculate text-based relevance score.
        
        Args:
            search_text: Text to search for
            asset: Asset to evaluate
            
        Returns:
            Tuple of (score, matched_fields, highlights)
        """
        score = 0.0
        matched_fields = []
        highlights = {}
        
        # Parse search text for field-specific searches
        field_searches = self._parse_field_searches(search_text)
        
        # Search in title (high weight)
        if 'title' in field_searches or not field_searches:
            title_score = self._fuzzy_match_score(search_text, asset.title or "")
            if title_score > 0:
                score += title_score * 4.0  # High weight for title
                matched_fields.append('title')
                if title_score > 0.5:
                    highlights['title'] = self._highlight_matches(search_text, asset.title or "")
        
        # Search in description (medium weight)
        if 'description' in field_searches or not field_searches:
            desc_score = self._fuzzy_match_score(search_text, asset.description or "")
            if desc_score > 0:
                score += desc_score * 2.0  # Medium weight for description
                matched_fields.append('description')
                if desc_score > 0.3:
                    highlights['description'] = self._highlight_matches(search_text, asset.description or "")
        
        # Search in author (low weight)
        if 'author' in field_searches or not field_searches:
            author_score = self._fuzzy_match_score(search_text, asset.author or "")
            if author_score > 0:
                score += author_score * 1.5
                matched_fields.append('author')
        
        # Search in generator type (medium weight)
        if 'generator' in field_searches or not field_searches:
            gen_score = self._fuzzy_match_score(search_text, asset.generator_type)
            if gen_score > 0:
                score += gen_score * 2.5
                matched_fields.append('generator_type')
        
        # Search in tags (high weight for tags)
        tag_score = self._calculate_tag_text_relevance(search_text, asset.tags)
        if tag_score > 0:
            score += tag_score * 3.0
            matched_fields.append('tags')
        
        return min(score, 40.0), matched_fields, highlights  # Cap at 40 points
    
    def _calculate_tag_relevance(self, search_tags: List[str], asset: AssetMetadata) -> Tuple[float, List[str]]:
        """
        Calculate relevance based on tag matching.
        
        Args:
            search_tags: Tags to search for
            asset: Asset to evaluate
            
        Returns:
            Tuple of (score, matched_tags)
        """
        if not search_tags or not asset.tags:
            return 0.0, []
        
        score = 0.0
        matched_tags = []
        
        asset_tags_lower = [tag.lower() for tag in asset.tags]
        
        for search_tag in search_tags:
            search_tag_lower = search_tag.lower()
            
            # Exact tag match
            if search_tag_lower in asset_tags_lower:
                score += 10.0
                matched_tags.append(search_tag)
            else:
                # Fuzzy tag match
                best_match_score = 0.0
                best_match = None
                
                for asset_tag in asset_tags_lower:
                    match_score = self._fuzzy_match_score(search_tag_lower, asset_tag)
                    if match_score > best_match_score:
                        best_match_score = match_score
                        best_match = asset_tag
                
                if best_match_score > 0.7:  # High fuzzy match threshold
                    score += best_match_score * 5.0
                    matched_tags.append(search_tag)
                
                # Check tag synonyms
                for synonym_group, synonyms in self.tag_synonyms.items():
                    if search_tag_lower in synonyms and best_match in synonyms:
                        score += 3.0
                        matched_tags.append(search_tag)
                        break
        
        return min(score, 30.0), matched_tags  # Cap at 30 points
    
    def _calculate_tag_text_relevance(self, search_text: str, tags: List[str]) -> float:
        """Calculate relevance of search text against tags."""
        if not tags:
            return 0.0
        
        max_score = 0.0
        
        for tag in tags:
            # Calculate fuzzy match between search text and tag
            tag_score = self._fuzzy_match_score(search_text, tag)
            if tag_score > max_score:
                max_score = tag_score
        
        return max_score
    
    def _calculate_date_relevance(self, asset_date: datetime, date_from: Optional[datetime], 
                                 date_to: Optional[datetime]) -> float:
        """Calculate date-based relevance (recency bonus)."""
        score = 0.0
        
        # If within specified date range, give full points
        if date_from and date_to:
            if date_from <= asset_date <= date_to:
                return 5.0
        elif date_from:
            if asset_date >= date_from:
                # Recency bonus
                days_old = (datetime.utcnow() - asset_date).days
                score = max(0, 5.0 - (days_old / 30.0))  # Decay over 30 days
        elif date_to:
            if asset_date <= date_to:
                return 5.0
        
        return score
    
    def _calculate_dimension_relevance(self, asset: AssetMetadata, query: MetadataQuery) -> float:
        """Calculate relevance based on dimension matching."""
        score = 0.0
        
        # Width matching
        if query.width_min and asset.width >= query.width_min:
            score += 1.0
        if query.width_max and asset.width <= query.width_max:
            score += 1.0
        
        # Height matching
        if query.height_min and asset.height >= query.height_min:
            score += 1.0
        if query.height_max and asset.height <= query.height_max:
            score += 1.0
        
        # Exact dimension matches get bonus
        if (query.width_min == query.width_max and 
            query.width_min and asset.width == query.width_min):
            score += 1.0
        
        if (query.height_min == query.height_max and 
            query.height_min and asset.height == query.height_min):
            score += 1.0
        
        return min(score, 5.0)  # Cap at 5 points
    
    def _fuzzy_match_score(self, text1: str, text2: str) -> float:
        """
        Calculate fuzzy match score between two strings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1_norm = text1.lower().strip()
        text2_norm = text2.lower().strip()
        
        # Exact match
        if text1_norm == text2_norm:
            return 1.0
        
        # Check if one contains the other
        if text1_norm in text2_norm:
            return len(text1_norm) / len(text2_norm) * 0.9
        
        if text2_norm in text1_norm:
            return len(text2_norm) / len(text1_norm) * 0.9
        
        # Token-based similarity
        tokens1 = self._tokenize(text1_norm)
        tokens2 = self._tokenize(text2_norm)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(set(tokens1) & set(tokens2))
        union = len(set(tokens1) | set(tokens2))
        
        if union == 0:
            return 0.0
        
        jaccard_score = intersection / union
        
        # Add character-level similarity for better fuzzy matching
        char_similarity = self._character_similarity(text1_norm, text2_norm)
        
        # Combine scores
        combined_score = (jaccard_score * 0.7) + (char_similarity * 0.3)
        
        return min(combined_score, 1.0)
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into searchable terms."""
        # Remove punctuation and split
        import string
        translator = str.maketrans('', '', string.punctuation)
        cleaned_text = text.translate(translator)
        
        tokens = cleaned_text.split()
        
        # Remove stop words and filter short tokens
        return {token for token in tokens 
                if len(token) >= 2 and token not in self.stop_words}
    
    def _character_similarity(self, text1: str, text2: str) -> float:
        """Calculate character-level similarity."""
        if not text1 or not text2:
            return 0.0
        
        # Use sequence matcher for character similarity
        import difflib
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _parse_field_searches(self, search_text: str) -> Dict[str, str]:
        """
        Parse search text for field-specific searches.
        
        Args:
            search_text: Search text to parse
            
        Returns:
            Dictionary of field -> search_term
        """
        field_patterns = {
            'title': r'title:([^ ]+)',
            'description': r'description:([^ ]+)',
            'author': r'author:([^ ]+)',
            'generator': r'generator:([^ ]+)',
            'tag': r'tag:([^ ]+)'
        }
        
        field_searches = {}
        
        for field, pattern in field_patterns.items():
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                field_searches[field] = matches[0]
        
        return field_searches
    
    def _highlight_matches(self, search_text: str, text: str) -> str:
        """Add HTML highlights for matched terms in text."""
        if not search_text or not text:
            return text
        
        # Simple highlighting - wrap matches in <mark> tags
        import re
        
        # Split search text into terms
        search_terms = self._tokenize(search_text)
        
        highlighted_text = text
        for term in search_terms:
            if len(term) >= 2:  # Only highlight meaningful terms
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted_text = pattern.sub(f'<mark>{term}</mark>', highlighted_text)
        
        return highlighted_text
    
    def _generate_facets(self, assets: List[AssetMetadata], total_count: int) -> Dict[str, Any]:
        """
        Generate search facets for filtering and exploration.
        
        Args:
            assets: Search results
            total_count: Total number of matching assets
            
        Returns:
            Dictionary of facets
        """
        facets = {}
        
        # Category facet
        category_counts = Counter(asset.category.value for asset in assets if asset.category)
        facets['categories'] = SearchFacet(
            name="categories",
            values=[{"value": cat, "count": count} for cat, count in category_counts.most_common()],
            total_count=total_count
        )
        
        # Generator type facet
        generator_counts = Counter(asset.generator_type for asset in assets)
        facets['generators'] = SearchFacet(
            name="generators",
            values=[{"value": gen, "count": count} for gen, count in generator_counts.most_common()],
            total_count=total_count
        )
        
        # Tag facet (top 20 tags)
        all_tags = []
        for asset in assets:
            all_tags.extend(asset.tags)
        
        tag_counts = Counter(all_tags)
        facets['tags'] = SearchFacet(
            name="tags",
            values=[{"value": tag, "count": count} for tag, count in tag_counts.most_common(20)],
            total_count=len(tag_counts)
        )
        
        # Author facet
        author_counts = Counter(asset.author for asset in assets if asset.author)
        facets['authors'] = SearchFacet(
            name="authors",
            values=[{"value": author, "count": count} for author, count in author_counts.most_common()],
            total_count=len(author_counts)
        )
        
        # Format facet
        format_counts = Counter(asset.format.value for asset in assets)
        facets['formats'] = SearchFacet(
            name="formats",
            values=[{"value": fmt, "count": count} for fmt, count in format_counts.most_common()],
            total_count=total_count
        )
        
        # Quality facet
        quality_counts = Counter(asset.quality for asset in assets if asset.quality)
        facets['qualities'] = SearchFacet(
            name="qualities",
            values=[{"value": quality, "count": count} for quality, count in quality_counts.most_common()],
            total_count=len(quality_counts)
        )
        
        # Date range facet (group by month)
        date_counts = defaultdict(int)
        for asset in assets:
            month_key = asset.created_at.strftime("%Y-%m")
            date_counts[month_key] += 1
        
        facets['date_ranges'] = SearchFacet(
            name="date_ranges",
            values=[{"value": date, "count": count} for date, count in sorted(date_counts.items())],
            total_count=len(date_counts)
        )
        
        # Dimension ranges
        width_ranges = [
            {"range": "Small (< 512)", "min": 0, "max": 512},
            {"range": "Medium (512-1024)", "min": 512, "max": 1024},
            {"range": "Large (1024-2048)", "min": 1024, "max": 2048},
            {"range": "Extra Large (> 2048)", "min": 2048, "max": 99999}
        ]
        
        for width_range in width_ranges:
            count = len([a for a in assets if width_range["min"] <= a.width < width_range["max"]])
            width_range["count"] = count
        
        facets['width_ranges'] = SearchFacet(
            name="width_ranges",
            values=width_ranges,
            total_count=total_count
        )
        
        return facets
    
    def _update_analytics(self, query: MetadataQuery, results: List[SearchResult], total_count: int):
        """Update search analytics."""
        self._search_analytics['total_searches'] += 1
        
        # Track query
        query_text = query.text or ""
        self._search_analytics['query_history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'query': query_text,
            'result_count': len(results),
            'total_count': total_count
        })
        
        # Track no-result queries
        if len(results) == 0 and query_text:
            self._search_analytics['no_result_queries'].add(query_text)
        
        # Keep only recent history (last 1000 searches)
        if len(self._search_analytics['query_history']) > 1000:
            self._search_analytics['query_history'] = self._search_analytics['query_history'][-1000:]
    
    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get intelligent search suggestions based on partial query.
        
        Args:
            partial_query: Partial query to suggest completions for
            limit: Maximum number of suggestions
            
        Returns:
            List of suggestion dictionaries
        """
        try:
            suggestions = []
            partial_lower = partial_query.lower().strip()
            
            if len(partial_lower) < 2:
                return suggestions
            
            # Get popular terms from analytics
            if self._search_analytics['query_history']:
                recent_queries = [q['query'] for q in self._search_analytics['query_history'][-100:]]
                query_terms = []
                for query in recent_queries:
                    query_terms.extend(self._tokenize(query.lower()))
                
                term_counts = Counter(query_terms)
                popular_terms = [term for term, count in term_counts.most_common(50)]
                
                # Find terms that start with or contain the partial query
                for term in popular_terms:
                    if partial_lower in term and len(term) > len(partial_lower):
                        suggestions.append({
                            'type': 'term_completion',
                            'text': term,
                            'count': term_counts[term],
                            'relevance': 'high' if term.startswith(partial_lower) else 'medium'
                        })
            
            # Suggest based on existing tags
            from .asset_storage import DatabaseConnection
            with DatabaseConnection(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Get popular tags
                cursor.execute("""
                    SELECT tag, COUNT(*) as count 
                    FROM asset_tags 
                    WHERE tag LIKE ?
                    GROUP BY tag 
                    ORDER BY count DESC 
                    LIMIT ?
                """, (f"%{partial_lower}%", limit))
                
                for row in cursor.fetchall():
                    tag = row['tag']
                    count = row['count']
                    suggestions.append({
                        'type': 'tag_suggestion',
                        'text': tag,
                        'count': count,
                        'relevance': 'high' if tag.startswith(partial_lower) else 'medium'
                    })
            
            # Sort by relevance and count
            suggestions.sort(key=lambda x: (x['relevance'] == 'high', x['count']), reverse=True)
            
            return suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def get_search_analytics(self) -> SearchAnalytics:
        """
        Get comprehensive search analytics.
        
        Returns:
            SearchAnalytics object with search insights
        """
        try:
            query_history = self._search_analytics['query_history']
            
            # Calculate analytics
            total_searches = self._search_analytics['total_searches']
            unique_queries = len(set(q['query'] for q in query_history if q['query']))
            
            # Popular terms
            all_terms = []
            for query_data in query_history:
                query_text = query_data['query']
                if query_text:
                    all_terms.extend(self._tokenize(query_text.lower()))
            
            term_counts = Counter(all_terms)
            popular_terms = term_counts.most_common(20)
            
            # Search types (simplified)
            search_types = {
                'text_search': len([q for q in query_history if q['query']]),
                'filter_only': len([q for q in query_history if not q['query']]),
                'tag_search': len([q for q in query_history if 'tag:' in (q['query'] or '')])
            }
            
            # Average results per query
            result_counts = [q['result_count'] for q in query_history]
            avg_results = sum(result_counts) / len(result_counts) if result_counts else 0
            
            # Search trends (last 30 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            trends = defaultdict(int)
            for query_data in query_history:
                query_time = datetime.fromisoformat(query_data['timestamp'].replace('Z', '+00:00'))
                if start_date <= query_time <= end_date:
                    date_key = query_time.strftime('%Y-%m-%d')
                    trends[date_key] += 1
            
            return SearchAnalytics(
                total_searches=total_searches,
                unique_queries=unique_queries,
                popular_terms=popular_terms,
                search_types=search_types,
                avg_results_per_query=avg_results,
                no_result_queries=list(self._search_analytics['no_result_queries']),
                search_trends=dict(trends)
            )
            
        except Exception as e:
            self.logger.error(f"Error getting search analytics: {e}")
            return SearchAnalytics(
                total_searches=0, unique_queries=0, popular_terms=[],
                search_types={}, avg_results_per_query=0,
                no_result_queries=[], search_trends={}
            )
    
    def find_similar_assets(self, asset_id: str, limit: int = 10) -> List[SearchResult]:
        """
        Find assets similar to a given asset based on metadata and parameters.
        
        Args:
            asset_id: Asset ID to find similarities for
            limit: Maximum number of similar assets to return
            
        Returns:
            List of SearchResult objects with similarity scores
        """
        try:
            # Get the reference asset
            reference_asset = self.storage.get_asset(asset_id)
            if not reference_asset:
                return []
            
            # Create a search query based on the reference asset
            similar_query = MetadataQuery(
                category=reference_asset.category,
                generator_type=reference_asset.generator_type,
                tags=reference_asset.tags,
                limit=limit * 3,  # Get more results to filter from
                sort_by="created_at",
                sort_order="desc"
            )
            
            # Get candidate assets
            assets, total = self.storage.get_assets_by_query(similar_query)
            
            # Calculate similarity scores
            similar_results = []
            for asset in assets:
                if asset.asset_id == asset_id:  # Skip the reference asset itself
                    continue
                
                similarity_score = self._calculate_similarity(reference_asset, asset)
                
                if similarity_score > 0.1:  # Minimum similarity threshold
                    similar_results.append(SearchResult(
                        asset=asset,
                        relevance_score=similar_score * 100,  # Convert to percentage-like score
                        relevance_level=SearchRelevance.HIGH if similarity_score > 0.7 else SearchRelevance.MEDIUM,
                        matched_fields=['similarity'],
                        highlights={},
                        explanation=f"Similarity score: {similarity_score:.2f}"
                    ))
            
            # Sort by similarity score and return top results
            similar_results.sort(key=lambda x: x.relevance_score, reverse=True)
            return similar_results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding similar assets: {e}")
            return []
    
    def _calculate_similarity(self, asset1: AssetMetadata, asset2: AssetMetadata) -> float:
        """
        Calculate similarity between two assets.
        
        Args:
            asset1: First asset
            asset2: Second asset
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        similarity_score = 0.0
        
        # Category similarity (30% weight)
        if asset1.category and asset2.category and asset1.category == asset2.category:
            similarity_score += 0.3
        
        # Generator type similarity (25% weight)
        if asset1.generator_type == asset2.generator_type:
            similarity_score += 0.25
        
        # Tag similarity (20% weight)
        if asset1.tags and asset2.tags:
            common_tags = set(asset1.tags) & set(asset2.tags)
            total_tags = set(asset1.tags) | set(asset2.tags)
            if total_tags:
                tag_similarity = len(common_tags) / len(total_tags)
                similarity_score += tag_similarity * 0.2
        
        # Parameter similarity (15% weight)
        if asset1.parameters and asset2.parameters:
            common_params = set(asset1.parameters.keys()) & set(asset2.parameters.keys())
            if common_params:
                param_similarity = len(common_params) / max(len(asset1.parameters), len(asset2.parameters))
                similarity_score += param_similarity * 0.15
        
        # Quality settings similarity (10% weight)
        quality_fields = ['quality', 'complexity', 'randomness']
        quality_matches = 0
        total_quality_fields = 0
        
        for field in quality_fields:
            val1 = getattr(asset1, field)
            val2 = getattr(asset2, field)
            if val1 is not None and val2 is not None:
                total_quality_fields += 1
                if val1 == val2:
                    quality_matches += 1
        
        if total_quality_fields > 0:
            quality_similarity = quality_matches / total_quality_fields
            similarity_score += quality_similarity * 0.1
        
        return min(similarity_score, 1.0)
    
    def clear_analytics(self):
        """Clear search analytics data."""
        self._search_analytics = {
            'total_searches': 0,
            'query_history': [],
            'facet_clicks': defaultdict(int),
            'no_result_queries': set()
        }
        self.logger.info("Search analytics cleared")