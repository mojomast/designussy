/**
 * @fileoverview TypeBrowser React Component
 * @description Component for browsing and searching element types
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import { APIClient } from '../utils/api-client.js';

/**
 * Component for browsing and searching element types
 * @param {Object} props - Component props
 * @param {Function} props.onTypeSelect - Callback when a type is selected
 * @param {Function} props.onTypePreview - Callback for type preview
 * @param {string} props.theme - Theme to apply
 * @param {boolean} props.showPreview - Whether to show preview thumbnails
 * @param {Array} props.selectedTypes - Currently selected types
 * @returns {JSX.Element} TypeBrowser component
 */
const TypeBrowser = ({
  onTypeSelect = () => {},
  onTypePreview = () => {},
  theme = 'dark',
  showPreview = true,
  selectedTypes = [],
  className = '',
  ...props
}) => {
  const [types, setTypes] = useState([]);
  const [filteredTypes, setFilteredTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTags, setSelectedTags] = useState([]);
  const [sortBy, setSortBy] = useState('name');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [apiClient] = useState(() => new APIClient({ endpoint: 'http://localhost:8001' }));

  // Load types from API
  useEffect(() => {
    loadTypes();
  }, []);

  // Filter and sort types when filters change
  useEffect(() => {
    filterAndSortTypes();
  }, [types, searchTerm, selectedCategory, selectedTags, sortBy]);

  const loadTypes = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8001/types');
      const data = await response.json();
      
      if (data.status === 'success' && data.types) {
        setTypes(data.types);
      } else {
        throw new Error(data.error || 'Failed to load types');
      }
    } catch (err) {
      console.error('Failed to load types:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const filterAndSortTypes = useCallback(() => {
    let filtered = [...types];

    // Filter by search term
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(type => 
        type.name.toLowerCase().includes(term) ||
        type.description.toLowerCase().includes(term) ||
        (type.tags && type.tags.some(tag => tag.toLowerCase().includes(term)))
      );
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(type => type.category === selectedCategory);
    }

    // Filter by tags
    if (selectedTags.length > 0) {
      filtered = filtered.filter(type => 
        type.tags && selectedTags.every(tag => type.tags.includes(tag))
      );
    }

    // Sort types
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'category':
          return a.category.localeCompare(b.category);
        case 'created':
          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        case 'modified':
          return new Date(b.updated_at || 0) - new Date(a.updated_at || 0);
        default:
          return 0;
      }
    });

    setFilteredTypes(filtered);
  }, [types, searchTerm, selectedCategory, selectedTags, sortBy]);

  const handleTypeClick = useCallback((type) => {
    onTypeSelect(type);
  }, [onTypeSelect]);

  const handleTagToggle = useCallback((tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  }, []);

  const handleClearFilters = useCallback(() => {
    setSearchTerm('');
    setSelectedCategory('all');
    setSelectedTags([]);
  }, []);

  // Get unique categories and tags
  const categories = useMemo(() => {
    const cats = [...new Set(types.map(type => type.category).filter(Boolean))];
    return cats.sort();
  }, [types]);

  const allTags = useMemo(() => {
    const tags = new Set();
    types.forEach(type => {
      if (type.tags) {
        type.tags.forEach(tag => tags.add(tag));
      }
    });
    return Array.from(tags).sort();
  }, [types]);

  const isTypeSelected = useCallback((typeId) => {
    return selectedTypes.some(t => t.id === typeId);
  }, [selectedTypes]);

  const handlePreviewGenerate = useCallback(async (type) => {
    try {
      const response = await fetch(`http://localhost:8001/generate/${type.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parameters: {},
          quality: 'preview'
        })
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        onTypePreview(type, url);
      }
    } catch (err) {
      console.error('Failed to generate preview:', err);
    }
  }, [onTypePreview]);

  if (loading) {
    return (
      <div className={`uw-type-browser ${theme} ${className}`} {...props}>
        <div className="uw-loading-state">
          <div className="uw-spinner"></div>
          <p>Loading element types...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`uw-type-browser ${theme} ${className}`} {...props}>
        <div className="uw-error-state">
          <p>Error loading types: {error}</p>
          <button 
            className="uw-btn uw-btn-secondary" 
            onClick={loadTypes}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`uw-type-browser ${theme} ${className}`} {...props}>
      {/* Browser Header */}
      <div className="uw-browser-header">
        <div className="uw-header-left">
          <h2 className="uw-browser-title">Element Types</h2>
          <span className="uw-type-count">
            {filteredTypes.length} of {types.length} types
          </span>
        </div>

        <div className="uw-header-right">
          {/* View Mode Toggle */}
          <div className="uw-view-toggle">
            <button
              className={`uw-btn-icon ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="Grid view"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
              </svg>
            </button>
            <button
              className={`uw-btn-icon ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="List view"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
                <line x1="3" y1="6" x2="3.01" y2="6"/>
                <line x1="3" y1="12" x2="3.01" y2="12"/>
                <line x1="3" y1="18" x2="3.01" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      <div className="uw-filters-panel">
        <div className="uw-search-container">
          <input
            type="text"
            className="uw-search-input"
            placeholder="Search types, descriptions, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <svg className="uw-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="21 21l-4.35-4.35"/>
          </svg>
        </div>

        <div className="uw-filters-row">
          {/* Category Filter */}
          <select
            className="uw-filter-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            ))}
          </select>

          {/* Sort Options */}
          <select
            className="uw-filter-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="name">Sort by Name</option>
            <option value="category">Sort by Category</option>
            <option value="created">Sort by Created</option>
            <option value="modified">Sort by Modified</option>
          </select>

          {/* Clear Filters */}
          <button
            className="uw-btn uw-btn-secondary"
            onClick={handleClearFilters}
          >
            Clear Filters
          </button>
        </div>

        {/* Tag Filter */}
        {allTags.length > 0 && (
          <div className="uw-tag-filters">
            <label className="uw-filter-label">Filter by tags:</label>
            <div className="uw-tag-list">
              {allTags.slice(0, 10).map(tag => (
                <button
                  key={tag}
                  className={`uw-tag ${selectedTags.includes(tag) ? 'selected' : ''}`}
                  onClick={() => handleTagToggle(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Types Display */}
      <div className={`uw-types-display ${viewMode}`}>
        {filteredTypes.length === 0 ? (
          <div className="uw-empty-state">
            <p>No types found matching your criteria.</p>
            <button 
              className="uw-btn uw-btn-secondary" 
              onClick={handleClearFilters}
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className={`uw-types-${viewMode}`}>
            {filteredTypes.map(type => (
              <div
                key={type.id}
                className={`uw-type-card ${isTypeSelected(type.id) ? 'selected' : ''}`}
                onClick={() => handleTypeClick(type)}
              >
                <div className="uw-type-header">
                  <h3 className="uw-type-name">{type.name}</h3>
                  <span className="uw-type-category">{type.category}</span>
                </div>

                <p className="uw-type-description">{type.description}</p>

                {type.tags && type.tags.length > 0 && (
                  <div className="uw-type-tags">
                    {type.tags.slice(0, 3).map(tag => (
                      <span key={tag} className="uw-tag">{tag}</span>
                    ))}
                    {type.tags.length > 3 && (
                      <span className="uw-tag-count">+{type.tags.length - 3}</span>
                    )}
                  </div>
                )}

                {showPreview && (
                  <div className="uw-type-actions">
                    <button
                      className="uw-btn uw-btn-primary uw-btn-small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePreviewGenerate(type);
                      }}
                    >
                      Preview
                    </button>
                    <button
                      className="uw-btn uw-btn-secondary uw-btn-small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTypeClick(type);
                      }}
                    >
                      Select
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// PropTypes definition
TypeBrowser.propTypes = {
  onTypeSelect: PropTypes.func,
  onTypePreview: PropTypes.func,
  theme: PropTypes.oneOf(['default', 'dark', 'minimal', 'chaotic']),
  showPreview: PropTypes.bool,
  selectedTypes: PropTypes.array,
  className: PropTypes.string
};

export default TypeBrowser;