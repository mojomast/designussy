# Asset Metadata System Documentation

## Overview

The Asset Metadata System is a comprehensive solution for tracking, managing, and searching generated assets in the NanoBanana Generator. It provides versioning capabilities, intelligent search, tag management, and export/import functionality.

## Features

### 🔍 **Intelligent Search & Discovery**
- Full-text search across titles, descriptions, and content
- Advanced filtering by tags, categories, and attributes
- Relevance scoring and ranking
- Search suggestions and autocomplete
- Faceted search with dynamic filters

### 🏷️ **Tag Management**
- Automatic tag categorization (style, color, theme, emotion, etc.)
- Tag validation and sanitization
- Popular tag discovery
- Tag hierarchy and relationships
- Intelligent tag suggestions

### 📊 **Asset Versioning**
- Complete version history tracking
- Parent-child relationship management
- Change detection and diffing
- Rollback capabilities
- Branch support for experimental variations

### 💾 **Storage & Persistence**
- SQLite database for metadata storage
- Full-text search indexing (FTS5)
- Relationship tracking between assets
- Usage analytics and access counting
- Soft deletion with recovery options

### 📤 **Export & Import**
- JSON and CSV export formats
- Complete system backups
- Data migration utilities
- Bulk import capabilities
- Version control for metadata

## Quick Start

### Enable the Metadata System

1. **Configure environment variables** in your `.env` file:
   ```bash
   # Enable metadata system
   METADATA_ENABLED=true
   
   # Database configuration
   METADATA_DB_PATH=./storage/metadata.db
   
   # Search configuration
   SEARCH_MAX_RESULTS=1000
   MIN_RELEVANCE_SCORE=0.1
   ```

2. **Start the API server** - metadata system initializes automatically:
   ```bash
   python backend.py
   ```

3. **Access the API documentation** at `http://localhost:8001/docs`

### Basic Usage

#### Generate an Asset with Metadata
```python
import requests

# Generate an asset with metadata
response = requests.post(
    "http://localhost:8001/assets",
    json={
        "generator_type": "enso",
        "width": 800,
        "height": 800,
        "user_metadata": {
            "title": "My Zen Circle",
            "description": "A peaceful meditation circle",
            "tags": ["zen", "peaceful", "meditation"],
            "author": "Artist Name"
        }
    }
)

asset_id = response.json()["asset_id"]
```

#### Search for Assets
```python
# Search by text
response = requests.get(
    "http://localhost:8001/assets",
    params={
        "search": "zen peaceful",
        "limit": 10
    }
)

# Filter by tags
response = requests.get(
    "http://localhost:8001/assets",
    params={
        "tags": "zen,meditation",
        "category": "glyphs"
    }
)

# Advanced search with filters
response = requests.get(
    "http://localhost:8001/assets",
    params={
        "search": "circle",
        "generator_type": "enso",
        "author": "Artist Name",
        "limit": 20,
        "offset": 0
    }
)
```

## API Reference

### Asset Management

#### `GET /assets`
List assets with search and filtering capabilities.

**Query Parameters:**
- `search` (string): Full-text search query
- `tags` (string): Comma-separated list of required tags
- `category` (string): Asset category filter (`backgrounds`, `glyphs`, `creatures`, `ui`)
- `generator_type` (string): Generator type filter
- `author` (string): Author filter
- `limit` (int): Number of results (1-100, default: 50)
- `offset` (int): Results offset (default: 0)

**Example Response:**
```json
{
  "status": "success",
  "assets": [
    {
      "asset_id": "uuid-string",
      "title": "Zen Circle",
      "generator_type": "enso",
      "category": "glyphs",
      "width": 800,
      "height": 800,
      "tags": ["zen", "peaceful", "circle"],
      "created_at": "2025-11-24T22:00:00.000Z",
      "relevance_score": 0.95
    }
  ],
  "total_count": 1,
  "facets": {
    "categories": {
      "name": "categories",
      "values": [{"value": "glyphs", "count": 1}]
    }
  }
}
```

#### `GET /assets/{asset_id}`
Get detailed metadata for a specific asset.

**Response includes:**
- Complete asset metadata
- Version history
- Similar assets
- Usage statistics

#### `GET /assets/{asset_id}/versions`
Get version history for an asset.

**Response includes:**
- Complete version timeline
- Change summaries
- Version statistics
- Rollback capabilities

### Tag Management

#### `GET /tags`
Get popular tags with usage statistics.

**Query Parameters:**
- `limit` (int): Number of tags (1-200, default: 50)
- `category` (string): Filter by tag category

#### `GET /tags/search`
Search for tags by name.

**Query Parameters:**
- `query` (string): Tag search query
- `limit` (int): Number of results (1-100, default: 20)

#### `POST /assets/{asset_id}/tags`
Add tags to an asset.

**Request Body:**
```json
{
  "tags": ["new", "tags", "here"]
}
```

### Metadata Operations

#### `PUT /assets/{asset_id}/metadata`
Update asset metadata.

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "author": "New Author",
  "tags": ["updated", "tags"],
  "is_favorite": true
}
```

#### `DELETE /assets/{asset_id}`
Delete an asset (soft delete by default).

**Query Parameters:**
- `permanent` (boolean): Permanently delete instead of soft delete

### System Statistics

#### `GET /metadata/stats`
Get comprehensive system statistics.

**Response includes:**
- Storage statistics
- Tag statistics
- Search analytics
- System health

### Export/Import

#### `POST /metadata/export`
Export asset metadata.

**Query Parameters:**
- `format` (string): Export format (`json`, `csv`)
- `include_deleted` (boolean): Include deleted assets
- `asset_ids` (string): Comma-separated asset IDs to export

## Search Query Syntax

### Text Search

#### Basic Search
- Single words: `zen`
- Phrases: `"peaceful circle"`
- Multiple terms: `zen peaceful meditation`

#### Field-Specific Search
- Title: `title:circle`
- Description: `description:peaceful`
- Author: `author:"John Doe"`
- Generator: `generator:enso`

#### Advanced Operators
- AND: `zen AND peaceful`
- OR: `circle OR enso`
- NOT: `dark NOT background`
- Wildcards: `circ*` (matches circle, circular, etc.)

### Filter Search

#### Tag Filtering
- Single tag: `tags=zen`
- Multiple tags: `tags=zen,peaceful,meditation`
- Tag categories: Filter by predefined categories

#### Attribute Filtering
- Category: `category=backgrounds`
- Generator type: `generator_type=enso`
- Author: `author="Artist Name"`
- Date range: Filter by creation date

#### Dimension Filtering
- Width range: `width_min=800&width_max=1200`
- Height range: `height_min=600&height_max=1000`
- Aspect ratio: Compute from width/height

### Search Examples

#### Find Zen-Related Assets
```
GET /assets?search=zen peaceful
```
Finds assets with "zen" and "peaceful" in title, description, or tags.

#### Find High-Quality Textures
```
GET /assets?category=backgrounds&tags=high-quality,texture&generator_type=parchment
```
Finds high-quality parchment textures in backgrounds category.

#### Find Assets by Specific Artist
```
GET /assets?author="John Doe"&limit=20
```
Finds all assets created by "John Doe".

#### Find Similar Assets
```
GET /assets/{asset_id}
```
Response includes `similar_assets` array with related assets.

#### Complex Search with Multiple Filters
```
GET /assets?
  search=circle&
  tags=zen,peaceful&
  category=glyphs&
  generator_type=enso&
  author="Master Artist"&
  limit=50&
  offset=0
```
Combines text search, tag filtering, category, generator type, and author filters.

## Tag Management Guide

### Tag Categories

Tags are automatically categorized into:

- **Style**: `abstract`, `realistic`, `minimal`, `detailed`
- **Color**: `red`, `blue`, `dark`, `bright`, `vibrant`
- **Theme**: `fantasy`, `sci-fi`, `vintage`, `modern`
- **Emotion**: `peaceful`, `energetic`, `calm`, `dramatic`
- **Quality**: `high`, `low`, `draft`, `professional`
- **Composition**: `centered`, `asymmetric`, `vertical`, `horizontal`
- **Subject**: `animal`, `plant`, `geometric`, `organic`
- **Mood**: `serene`, `mysterious`, `joyful`, `melancholic`

### Tag Validation Rules

- **Length**: 2-50 characters
- **Characters**: Letters, numbers, spaces, hyphens, underscores
- **No consecutive special characters**: `--` or `__` not allowed
- **No leading/trailing special characters**
- **No reserved words**: `admin`, `system`, `null`, etc.

### Tag Suggestions

The system provides intelligent tag suggestions based on:

1. **Generator Type**: Automatic tags based on asset type
2. **Similar Assets**: Tags used in similar assets
3. **Generation Parameters**: Tags derived from quality and style settings
4. **Text Analysis**: Keywords extracted from title and description
5. **Popular Tags**: Suggestions from frequently used tags

### Tag Hierarchy

Tags can have hierarchical relationships:

- **Broader**: General categories (e.g., `color` → `red`)
- **Narrower**: Specific subcategories (e.g., `red` → `crimson`)
- **Related**: Similar concepts (e.g., `dark` ↔ `shadow`)

## Version Control

### Version Types

- **Minor Changes**: Metadata updates, small parameter tweaks
- **Major Changes**: Significant visual or parameter modifications
- **Parameter Updates**: Generation parameter modifications
- **Quality Changes**: Quality setting modifications
- **Reformat**: Format, size, or dimension changes
- **Reborn**: Complete regeneration with new seed

### Version Operations

#### Create Version
```python
# Version creation is automatic when regenerating with same asset_id
new_metadata = old_metadata.create_version(
    quality="high",
    title="Enhanced Version"
)
```

#### View Version History
```python
GET /assets/{asset_id}/versions
```

#### Compare Versions
```python
GET /assets/{asset_id}/versions?compare=v1,v2
```

#### Rollback to Previous Version
```python
POST /assets/{asset_id}/rollback
{
    "target_version": 2,
    "reason": "Preferred this version"
}
```

## Export/Import

### Export Formats

#### JSON Export
Complete metadata export including:
- Asset metadata
- Tag relationships
- Version history
- System statistics

#### CSV Export
Tabular format for spreadsheet applications:
- Asset properties as columns
- JSON fields as serialized strings
- Compatible with Excel, Google Sheets

#### Backup Export
Complete system backup including:
- Database file
- Metadata export
- Configuration backup

### Import Capabilities

#### Validation
- Schema validation
- Data integrity checks
- Duplicate detection
- Tag validation

#### Merge Options
- **Skip Duplicates**: Ignore existing assets
- **Overwrite**: Replace existing metadata
- **Merge Tags**: Combine tag lists
- **Validate Only**: Check without importing

### Backup Strategy

#### Automated Backups
```bash
# Configuration
METADATA_BACKUP_ENABLED=true
METADATA_BACKUP_INTERVAL=3600  # Every hour
```

#### Manual Backup
```python
# Create backup
response = requests.post("/metadata/export", params={"format": "backup"})

# List backups
response = requests.get("/metadata/backups")

# Restore from backup
response = requests.post("/metadata/restore", 
    json={"backup_path": "/path/to/backup.zip"})
```

## Best Practices

### Asset Organization

1. **Use Descriptive Titles**: Clear, searchable titles help discovery
2. **Add Relevant Tags**: Use both broad and specific tags
3. **Categorize Properly**: Assign appropriate categories
4. **Include Descriptions**: Detailed descriptions improve searchability
5. **Track Versions**: Use version control for iterative improvements

### Search Optimization

1. **Use Specific Keywords**: More targeted searches yield better results
2. **Combine Filters**: Use multiple filters for precise results
3. **Leverage Categories**: Narrow results with category filters
4. **Use Author Filters**: Find assets by specific creators
5. **Check Popular Tags**: Use frequently used tags for better results

### Tag Management

1. **Follow Naming Conventions**: Consistent tag naming
2. **Use Hierarchical Tags**: Group related tags logically
3. **Avoid Redundancy**: Don't create duplicate or near-duplicate tags
4. **Validate Before Adding**: Ensure tags meet validation rules
5. **Update Tags Regularly**: Keep tags relevant and current

### Performance Optimization

1. **Use Pagination**: Limit results to reasonable numbers
2. **Filter Early**: Apply filters to reduce search scope
3. **Cache Popular Searches**: Store frequently accessed results
4. **Index Properly**: Ensure database indexes are optimized
5. **Monitor Storage**: Keep database size manageable

### Data Integrity

1. **Regular Backups**: Schedule automated backups
2. **Validate Imports**: Check data before importing
3. **Monitor Usage**: Track access patterns and storage
4. **Clean Orphaned Data**: Remove unused tags and relationships
5. **Version Control**: Maintain version history for important assets

## Troubleshooting

### Common Issues

#### Search Returns No Results
- Check spelling and syntax
- Try broader search terms
- Verify filters are not too restrictive
- Ensure assets exist in the system

#### Tag Addition Fails
- Check tag validation rules
- Verify tag length limits
- Ensure no reserved words
- Check for special character restrictions

#### Export Fails
- Check file permissions
- Verify disk space availability
- Ensure database connectivity
- Check export format validity

#### Performance Issues
- Monitor database size
- Check search query complexity
- Verify indexing status
- Consider archiving old assets

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Invalid request parameters | Check parameter syntax and values |
| 404 | Asset not found | Verify asset ID exists |
| 500 | Internal server error | Check system logs and database connectivity |
| 503 | Metadata system disabled | Enable METADATA_ENABLED in configuration |

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
METADATA_DEBUG=true
```

View logs:
```bash
tail -f logs/application.log | grep "metadata"
```

## Advanced Usage

### Custom Search Algorithms

Implement custom relevance scoring:
```python
# Custom search with weighted fields
query = MetadataQuery(
    text="zen circle",
    field_weights={
        'title': 3.0,
        'description': 2.0,
        'tags': 2.5,
        'author': 1.0
    },
    boost_factors={
        'category': 1.2,
        'quality': 1.5
    }
)
```

### Bulk Operations

#### Bulk Tag Updates
```python
# Update multiple assets with same tags
asset_ids = ["id1", "id2", "id3"]
tags = ["bulk", "update", "tags"]

for asset_id in asset_ids:
    requests.post(f"/assets/{asset_id}/tags", json={"tags": tags})
```

#### Bulk Metadata Export
```python
# Export filtered assets
response = requests.post("/metadata/export", json={
    "format": "json",
    "filters": {
        "category": "backgrounds",
        "date_from": "2025-01-01",
        "tags": ["texture", "dark"]
    }
})
```

### Integration Examples

#### Frontend Integration
```javascript
// Search component
async function searchAssets(query, filters) {
    const params = new URLSearchParams({
        search: query,
        ...filters
    });
    
    const response = await fetch(`/assets?${params}`);
    const data = await response.json();
    
    return {
        assets: data.assets,
        total: data.total_count,
        facets: data.facets
    };
}

// Tag suggestion component
async function getTagSuggestions(assetId) {
    const response = await fetch(`/assets/${assetId}/tags/suggestions`);
    return await response.json();
}
```

#### Batch Processing
```python
# Process multiple assets
def process_asset_batch(asset_ids):
    for asset_id in asset_ids:
        # Update metadata
        update_metadata(asset_id)
        
        # Generate suggestions
        suggestions = get_tag_suggestions(asset_id)
        
        # Store recommendations
        store_recommendations(asset_id, suggestions)
```

## System Architecture

### Database Schema

```sql
-- Main assets table
CREATE TABLE assets (
    asset_id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    generator_type TEXT NOT NULL,
    parameters TEXT,
    created_at DATETIME,
    width INTEGER,
    height INTEGER,
    format TEXT,
    size_bytes INTEGER,
    hash TEXT,
    tags TEXT,
    category TEXT,
    -- Additional fields...
);

-- Tag relationships
CREATE TABLE asset_tags (
    asset_id TEXT,
    tag TEXT,
    created_at DATETIME,
    FOREIGN KEY (asset_id) REFERENCES assets
);

-- Full-text search
CREATE VIRTUAL TABLE assets_fts USING fts5(
    asset_id,
    title,
    description,
    author,
    generator_type,
    tags,
    category
);
```

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/assets` | List/search assets |
| GET | `/assets/{id}` | Get asset details |
| GET | `/assets/{id}/versions` | Get version history |
| POST | `/assets/{id}/tags` | Add tags |
| PUT | `/assets/{id}/metadata` | Update metadata |
| DELETE | `/assets/{id}` | Delete asset |
| GET | `/tags` | Get popular tags |
| GET | `/tags/search` | Search tags |
| GET | `/metadata/stats` | System statistics |
| POST | `/metadata/export` | Export metadata |

## Support

### Getting Help

1. **API Documentation**: Visit `/docs` for interactive API docs
2. **Health Check**: Use `/health` endpoint for system status
3. **Logs**: Check application logs for detailed error information
4. **Statistics**: Monitor `/metadata/stats` for system health

### Reporting Issues

When reporting issues, include:
- Error message and stack trace
- API endpoint and request details
- System configuration
- Steps to reproduce
- Expected vs actual behavior

### Performance Monitoring

Key metrics to monitor:
- Search response times
- Database query performance
- Storage usage and growth
- Tag usage patterns
- Asset creation rates
- Export/import success rates

## Changelog

### Version 1.0.0 (Current)
- Initial release of asset metadata system
- Full CRUD operations for assets
- Advanced search with relevance scoring
- Tag management and categorization
- Version control and rollback
- Export/import capabilities
- Comprehensive API coverage
- Extensive test coverage

### Future Releases

#### Planned Features
- Machine learning-based tag suggestions
- Visual similarity search
- Collaborative filtering for recommendations
- Advanced analytics dashboard
- Real-time collaboration features
- Plugin system for custom generators
- GraphQL API support
- Streaming updates via WebSockets

---

*For additional support and updates, visit the project repository or contact the development team.*