# Implementation Plan for Content Models and Search

1. **Add Pydantic Models for Content Types**
   - [x] Create new file `app/models.py`
   - [x] Add base content model with common fields:
     ```python
     # Required fields
     title: str
     created: datetime
     updated: datetime
     tags: List[str]
     
     # Optional fields with defaults
     status: str = "Evergreen"
     series: Optional[str] = None
     difficulty: Optional[str] = None
     prerequisites: Optional[List[str]] = None
     related_content: Optional[List[str]] = None
     visibility: str = "public"
     
     # Configuration to allow extra fields
     class Config:
         extra = "allow"
     ```
   - [x] Add specialized content models for each type:
     ```python
     # Bookmark: add required url field
     # TIL: add optional difficulty, prerequisites
     # Note: add optional series
     # Add validators and examples for each
     ```
   - [x] Add content metadata model:
     ```python
     # All fields optional with defaults
     series: Optional[str] = None
     difficulty: Optional[str] = None
     prerequisites: Optional[List[str]] = None
     related_content: Optional[List[str]] = None
     visibility: str = "public"
     ```
   - [x] Update main.py to use these models when parsing content
   - [x] Add error handling for invalid content structure
   - [x] Add tests for model validation

1a. **Content Migration Plan**
   - [ ] Create content analysis script:
     ```python
     # Scan all content files
     # Report current front matter fields
     # Identify missing required fields
     # Generate statistics on field usage
     ```
   - [ ] Create AI-powered metadata generator:
     ```python
     # Use Claude Sonnet 3.5 to analyze content
     # Determine appropriate difficulty level
     # Suggest prerequisites based on content
     # Identify related content through semantic similarity
     # Generate series suggestions for related posts
     # Validate generated metadata
     ```
   - [ ] Create front matter validation script:
     ```python
     # Validate against new models
     # Report validation errors
     # Suggest fixes for common issues
     ```
   - [ ] Create migration script:
     ```python
     # Backup original files
     # Process each file:
     #   1. Extract current front matter
     #   2. Get AI suggestions for new metadata
     #   3. Merge existing and new metadata
     #   4. Validate final result
     #   5. Write updated front matter
     # Track changes in a log file
     ```
   - [ ] Add interactive mode:
     ```python
     # Show AI suggestions for each file
     # Allow user to accept/reject/modify suggestions
     # Provide explanation for AI decisions
     # Allow batch approval of similar changes
     ```
   - [ ] Add dry-run option to preview changes
   - [ ] Add rollback capability
   - [ ] Add tests for migration tools
   - [ ] Create metadata enhancement script:
     ```python
     # Periodically analyze content for metadata updates
     # Suggest improvements based on new content
     # Update related_content as new posts are added
     # Maintain content graph relationships
     ```

2. **Implement Search Infrastructure**
   - [ ] Add dependencies to `pyproject.toml`:
     ```toml
     whoosh = "^2.7.4"
     ```
   - [ ] Create new file `app/search.py`
   - [ ] Implement `SearchManager` class with schema:
     ```python
     # Fields: path, title, content, tags, created, content_type
     # Add proper analyzers for each field
     # Include docstrings and type hints
     ```
   - [ ] Add index maintenance methods:
     ```python
     # Methods: create_index, rebuild_index, add_document, update_document
     # Include proper error handling
     # Add async support
     ```
   - [ ] Create search index directory structure
   - [ ] Add tests for search functionality

3. **Update Content Processing**
   - [ ] Modify `ContentManager.render_markdown`:
     ```python
     # Update to use Pydantic models
     # Add validation for front matter
     # Improve error messages for invalid content
     ```
   - [ ] Add content indexing to processing pipeline:
     ```python
     # Index content after rendering
     # Handle updates to existing content
     # Add proper error handling
     ```
   - [ ] Add content type detection
   - [ ] Update caching to work with new models
   - [ ] Add tests for content processing

4. **Add Search API Endpoints**
   - [ ] Create new search endpoints in main.py:
     ```python
     # GET /api/search
     # Parameters: q, content_type, tags, page, limit
     # Add proper response models
     ```
   - [ ] Add search results template `templates/search_results.html`:
     ```html
     # Include result highlighting
     # Add filtering options
     # Support pagination
     ```
   - [ ] Add search box to site header
   - [ ] Add search results page styling
   - [ ] Add keyboard shortcuts for search
   - [ ] Add tests for search endpoints

5. **Add Search Index Management**
   - [ ] Add startup event handler:
     ```python
     # Rebuild index on startup
     # Add progress logging
     # Handle errors gracefully
     ```
   - [ ] Add index rebuild command:
     ```python
     # CLI command to rebuild index
     # Add progress bar
     # Add error reporting
     ```
   - [ ] Add index statistics endpoint:
     ```python
     # Show index size
     # Show last update time
     # Show document counts by type
     ```
   - [ ] Add monitoring for index health
   - [ ] Add tests for index management

6. **Update Front Matter Standards**
   - [ ] Create front matter validation script:
     ```python
     # Check all content files
     # Report validation errors
     # Fix common issues automatically
     ```
   - [ ] Update existing content files:
     ```yaml
     # Add missing fields
     # Standardize date formats
     # Normalize tag names
     ```
   - [ ] Add front matter documentation
   - [ ] Create front matter template for new content
   - [ ] Add tests for front matter validation

7. **Add Content Relationship Features**
   - [ ] Implement series support:
     ```python
     # Add series metadata
     # Create series index pages
     # Add navigation between series posts
     ```
   - [ ] Add related content detection:
     ```python
     # Based on tags
     # Based on content similarity
     # Add suggestions to content pages
     ```
   - [ ] Add tag hierarchy support:
     ```python
     # Add parent/child relationships
     # Create tag overview pages
     # Update tag navigation
     ```
   - [ ] Add content graph visualization
   - [ ] Add tests for relationship features

8. **Performance Optimization**
   - [ ] Add search result caching:
     ```python
     # Cache common queries
     # Add cache invalidation
     # Monitor cache hit rates
     ```
   - [ ] Optimize index size:
     ```python
     # Configure field compression
     # Optimize stopwords
     # Add index pruning
     ```
   - [ ] Add search result ranking improvements:
     ```python
     # Boost recent content
     # Consider tag weights
     # Add popularity factors
     ```
   - [ ] Add performance monitoring
   - [ ] Add load testing

9. **Documentation and Testing**
   - [ ] Add API documentation:
     ```python
     # Document all endpoints
     # Add example requests/responses
     # Document error cases
     ```
   - [ ] Add model documentation:
     ```python
     # Document all fields
     # Add validation rules
     # Include examples
     ```
   - [ ] Add search documentation:
     ```python
     # Document query syntax
     # Document filtering options
     # Add search tips
     ```
   - [ ] Add integration tests
   - [ ] Add performance tests

Each story should be implemented in order as they build on each other. The AI agent should commit after each checkbox item is complete and ensure tests pass before moving to the next item.
