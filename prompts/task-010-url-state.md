# Task 010: Implement URL-Driven State Management for Garden Walks

## Context
The sliding panel mechanism from Task 009 is working beautifully with Alpine.js managing the client-side state. However, users can't share their garden walks or bookmark interesting paths. Following the "Bookmarkable by Design" principles, we need to synchronize the panel state with URL parameters.

## Objective
Make every garden walk shareable and bookmarkable by implementing URL-driven state management. Users should be able to share links that recreate their exact journey through the garden, and browser navigation should work intuitively.

## Test Requirements

Write these tests FIRST before any implementation:

### 1. URL Parameter Tests (`tests/test_url_parameters.py`)
```python
async def test_url_parameter_structure():
    """Test URL parameters correctly encode garden state"""
    # Test path parameter contains comma-separated note IDs
    # Test focus parameter indicates active panel
    # Test view parameter (sliding|stacked|single)
    # Test optional filters (tags, status)
    
async def test_url_length_limits():
    """Test URLs stay under 2000 character limit"""
    # Create path with maximum panels
    # Verify URL length < 2000 chars
    # Test URL shortening if needed
    
async def test_url_encoding():
    """Test special characters handled correctly"""
    # Test notes with spaces in names
    # Test notes with special characters
    # Verify proper URL encoding/decoding
```

### 2. State Synchronization Tests (`tests/test_state_sync.py`)
```python
async def test_url_to_state():
    """Test URL parameters initialize Alpine state"""
    # Load page with URL parameters
    # Verify Alpine state matches URL
    # Test all panels load correctly
    
async def test_state_to_url():
    """Test Alpine state updates URL"""
    # Open new panel via UI
    # Verify URL updates without reload
    # Test browser history updated
    
async def test_bidirectional_sync():
    """Test two-way synchronization"""
    # Change URL manually
    # Verify UI updates
    # Change UI
    # Verify URL updates
```

### 3. Browser Navigation Tests (`tests/test_browser_nav.py`)
```python
async def test_back_button():
    """Test browser back button behavior"""
    # Open panels A, B, C
    # Click back button
    # Verify returns to A, B state
    
async def test_forward_button():
    """Test browser forward button behavior"""
    # Navigate forward after going back
    # Verify state restored correctly
    
async def test_refresh_persistence():
    """Test state persists through refresh"""
    # Set up complex panel state
    # Refresh page
    # Verify exact state restored
```

### 4. Sharing Tests (`tests/test_sharing.py`)
```python
async def test_share_button():
    """Test share functionality"""
    # Click share button
    # Verify correct URL copied
    # Test native share API if available
    
async def test_shared_link_loads():
    """Test shared links recreate state"""
    # Load shared URL in new session
    # Verify all panels load
    # Verify focus on correct panel
    
async def test_social_sharing():
    """Test social media sharing formats"""
    # Generate Twitter share link
    # Generate email share link
    # Verify proper formatting
```

## Implementation Hints

1. **URL Parameter Schema**:
   ```python
   # /garden-walk?path=note1,note2,note3&focus=1&view=sliding
   # path: Comma-separated note IDs in order
   # focus: Index of currently active panel (0-based)
   # view: Display mode (sliding|stacked|single)
   # tags: Optional filter
   # status: Optional growth stage filter
   ```

2. **Alpine.js State Management**:
   ```javascript
   function gardenWalk() {
     return {
       // Initialize from URL on load
       init() {
         const params = new URLSearchParams(window.location.search);
         this.loadFromURL(params);
       },
       
       // Update URL without page reload
       updateURL() {
         const params = this.stateToParams();
         window.history.pushState({}, '', `?${params}`);
       },
       
       // Handle browser navigation
       handlePopState(event) {
         this.loadFromURL(new URLSearchParams(window.location.search));
       }
     }
   }
   ```

3. **HTMX Integration**:
   ```html
   <!-- Include state in HTMX requests -->
   <a hx-get="/api/panel/notes/example"
      hx-vals='{"preserveState": true}'
      hx-push-url="/garden-walk?path={{new_path}}">
   ```

4. **Server-Side Handling**:
   ```python
   @app.get("/garden-walk")
   async def garden_walk(
       path: str = Query(None),
       focus: int = Query(0),
       view: str = Query("sliding")
   ):
       # Parse and validate parameters
       # Load appropriate content
       # Render with state
   ```

## Integration Points

- **Previous Task**: Builds on Alpine.js panel mechanism from Task 009
- **Next Task**: Task 011 will create HTMX endpoints using these URL patterns
- **SEO**: URLs must be crawler-friendly and meaningful
- **Analytics**: Track popular paths and completion rates

## Acceptance Criteria Checklist

Before marking this task complete, ensure:

- [ ] All tests written first and failing appropriately
- [ ] URL parameters correctly encode all state
- [ ] Browser back/forward navigation works perfectly
- [ ] Page refresh preserves exact state
- [ ] URLs stay under 2000 character limit
- [ ] Share button copies correct URL
- [ ] Shared links recreate exact state
- [ ] No page reloads during navigation
- [ ] State syncs bidirectionally
- [ ] Graceful handling of invalid URLs
- [ ] All existing tests still pass

## Resources

- [URLSearchParams API](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams)
- [History API](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [Bookmarkable by Design Article](https://www.lorenstew.art/blog/bookmarkable-by-design-url-state-htmx/)
- [Web Share API](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share)

## Expected Deliverables

1. URL parameter handling in FastAPI routes
2. Alpine.js URL synchronization logic
3. Share button implementation
4. Browser navigation event handlers
5. Comprehensive test coverage
6. Documentation of URL schema

## User Experience Goals

- Sharing a link should feel magical
- Browser navigation should feel native
- URLs should be human-readable when possible
- State changes should be instant
- Invalid URLs should fail gracefully

Remember: Every interesting state should have a URL. Make exploration shareable!