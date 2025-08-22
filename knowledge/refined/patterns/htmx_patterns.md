# HTMX Patterns - Digital Garden

## Infinite Scroll Pattern
```html
<div hx-get="/api/content?page={{ next_page }}" 
     hx-trigger="revealed" 
     hx-swap="afterend"
     hx-indicator="#loading-spinner">
    <!-- Content cards -->
</div>
```

## Partial Template Loading
```html
<!-- Trigger -->
<button hx-get="/partials/content-card" 
        hx-target="#content-container"
        hx-swap="beforeend">
    Load More
</button>

<!-- Target -->
<div id="content-container">
    <!-- Cards inserted here -->
</div>
```

## Dynamic Content Updates
```html
<!-- Poll for updates -->
<div hx-get="/api/notifications"
     hx-trigger="every 30s"
     hx-swap="innerHTML">
</div>
```

## Form Submission
```html
<form hx-post="/api/content"
      hx-target="#result"
      hx-swap="innerHTML">
    <input name="title" required>
    <button type="submit">Save</button>
</form>
```

## Error Handling
```html
<div hx-get="/api/data"
     hx-trigger="load"
     hx-on::response-error="handleError(event)">
</div>
```

## Notes
- Always use hx-indicator for loading states
- Prefer afterend/beforeend for list additions
- Use innerHTML for complete replacements
- Add error handlers for robustness