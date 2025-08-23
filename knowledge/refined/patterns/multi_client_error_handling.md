# Pattern: Multi-Client Error Handling
**Category**: Error Handling
**Confidence**: High
**Validated**: 2+ instances

## Description
Design error handlers that intelligently serve different response formats based on client type (API, browser, HTMX) using content negotiation, maintaining consistency while providing appropriate formats.

## When to Apply
- Web applications with both UI and API endpoints
- Systems serving multiple client types
- FastAPI applications with mixed consumers
- HTMX-enhanced applications
- Progressive enhancement scenarios

## Implementation Pattern

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors with content negotiation."""
    
    # Detect client type
    is_api = request.url.path.startswith("/api/")
    wants_json = request.headers.get("Accept") == "application/json"
    is_htmx = request.headers.get("HX-Request") == "true"
    
    # API or JSON clients
    if is_api or wants_json:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc.detail)}
        )
    
    # HTMX partial responses
    if is_htmx:
        return HTMLResponse(
            content="<div>Content not found</div>",
            status_code=404
        )
    
    # Full HTML for browser clients
    template = env.get_template("404.html")
    html_content = template.render(request=request)
    return HTMLResponse(content=html_content, status_code=404)
```

## Key Components

### 1. Client Detection Logic
```python
# Check URL patterns
is_api = request.url.path.startswith("/api/")

# Check Accept headers
wants_json = "application/json" in request.headers.get("Accept", "")

# Check HTMX headers
is_htmx = request.headers.get("HX-Request") == "true"
```

### 2. Response Format Hierarchy
1. API endpoints → JSON
2. JSON Accept header → JSON
3. HTMX requests → Partial HTML
4. Browser requests → Full HTML

### 3. Error Context Enhancement
```python
# Provide helpful context in error responses
context = {
    "error_id": str(uuid.uuid4())[:8],
    "timestamp": datetime.now().isoformat(),
    "recent_content": get_recent_content(),
    "suggestions": get_relevant_suggestions()
}
```

## Evidence from Digital Garden

### Instance 1: 404 Handler
- Differentiates API vs browser requests
- Provides recent content for discovery
- Maintains site navigation in error state

### Instance 2: 500 Handler
- Includes error tracking IDs
- Shows debug info in development only
- Logs complete error for debugging

## Benefits
- Single handler serves all client types
- Consistent error handling logic
- Appropriate response formats
- Graceful degradation
- Better user experience

## Security Considerations

### Progressive Disclosure
```python
if os.getenv("ENVIRONMENT") != "production":
    # Development: Show full details
    context["traceback"] = traceback.format_exc()
    context["error_type"] = type(exc).__name__
else:
    # Production: User-friendly only
    context["message"] = "An error occurred"
```

## Testing Strategy

```python
def test_error_handler_content_negotiation():
    # Test API response
    response = client.get("/api/missing", 
                         headers={"Accept": "application/json"})
    assert response.headers["content-type"] == "application/json"
    
    # Test browser response
    response = client.get("/missing")
    assert "<!DOCTYPE html>" in response.text
    
    # Test HTMX response
    response = client.get("/missing", 
                         headers={"HX-Request": "true"})
    assert "<div" in response.text
```

## Common Pitfalls
- ❌ Forgetting to check all header variations
- ❌ Not handling missing headers gracefully
- ❌ Exposing sensitive info in production
- ❌ Inconsistent error ID formats

## Related Patterns
- Error Pages as Navigation Tools
- Progressive Error Disclosure
- Content Negotiation Pattern

## Configuration

```python
# Environment-based configuration
DEBUG_MODE = os.getenv("ENVIRONMENT") != "production"
ERROR_TEMPLATE_DIR = "templates/errors/"
ERROR_LOG_LEVEL = "DEBUG" if DEBUG_MODE else "ERROR"
```

## Checklist
- [ ] Detect all client types (API, JSON, HTMX, browser)
- [ ] Provide appropriate response formats
- [ ] Include helpful context in errors
- [ ] Implement progressive disclosure
- [ ] Add error tracking/logging
- [ ] Test all client type scenarios
- [ ] Maintain consistent error IDs