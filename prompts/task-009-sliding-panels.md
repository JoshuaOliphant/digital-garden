# Task 009: Build Sliding Panel Mechanism with Alpine.js

## Context
You've completed the foundation and navigation phases. The homepage now has a topographical layout with growth stages and garden paths. It's time to implement the signature sliding notes interface inspired by Andy Matuschak's notes. Alpine.js (15KB) will provide client-side state management while maintaining the no-build-step requirement.

## Objective
Create a horizontal sliding panel interface for desktop that allows readers to explore connected content in a spatial, memorable way. Panels should stack intelligently, animate smoothly, and provide intuitive navigation.

## Test Requirements

Write these tests FIRST before any implementation:

### 1. Alpine.js Integration Tests (`tests/test_alpine_integration.py`)
```python
async def test_alpine_loads_correctly():
    """Test Alpine.js initializes without conflicts with HTMX"""
    # Verify Alpine.js script loads
    # Test no conflicts with HTMX attributes
    # Verify both libraries coexist peacefully
    
async def test_alpine_panel_state():
    """Test Alpine.js manages panel state correctly"""
    # Test initial state has empty stack
    # Test adding panels updates state
    # Test state persistence in Alpine store
```

### 2. Panel Behavior Tests (`tests/test_panel_behavior.py`)
```python
async def test_panel_stacking_logic():
    """Test intelligent panel stacking"""
    # Open note A, then B from A - B appears to right
    # Open note C from A - C replaces B
    # Navigate back to B - B replaces C at same position
    
async def test_panel_depth_limit():
    """Test maximum panel depth enforcement"""
    # Open 5 panels (configured maximum)
    # Attempt to open 6th panel
    # Verify oldest panel is removed or blocked
    
async def test_panel_animations():
    """Test smooth panel transitions"""
    # Verify CSS transitions applied
    # Test animation duration (< 300ms)
    # Test no jank during animations
```

### 3. Navigation Tests (`tests/test_panel_navigation.py`)
```python
async def test_keyboard_navigation():
    """Test keyboard controls for panels"""
    # Test arrow keys navigate between panels
    # Test Escape closes current panel
    # Test Tab cycles through panel links
    
async def test_panel_close_behavior():
    """Test panel closing logic"""
    # Close middle panel - others adjust
    # Close last panel - focus returns to previous
    # Close all panels - return to base state
```

### 4. Performance Tests (`tests/test_panel_performance.py`)
```python
async def test_animation_performance():
    """Test animations run at 60fps"""
    # Measure frame rate during transitions
    # Verify no dropped frames
    # Test with multiple panels open
    
async def test_memory_management():
    """Test memory usage with many panels"""
    # Open and close many panels
    # Verify memory is released
    # Test no memory leaks
```

## Implementation Hints

1. **Alpine.js Component Structure**:
   ```javascript
   function gardenWalk() {
     return {
       stack: [],        // Array of open note IDs
       currentIndex: 0,  // Currently focused panel
       maxDepth: 5,      // Maximum panels shown
       
       openNote(noteId, fromPanel) {
         // Implement stacking logic here
       },
       
       closePanel(index) {
         // Handle panel removal
       },
       
       navigateTo(index) {
         // Focus specific panel
       }
     }
   }
   ```

2. **HTML Structure**:
   ```html
   <div x-data="gardenWalk()" class="sliding-panels">
     <template x-for="(note, index) in stack">
       <div class="panel" :style="panelStyle(index)">
         <!-- Panel content -->
       </div>
     </template>
   </div>
   ```

3. **CSS Transitions**:
   - Use CSS transforms for smooth sliding
   - Apply will-change for performance
   - Progressive enhancement approach

4. **HTMX Integration**:
   - Panels load content via HTMX
   - Alpine manages positioning
   - Events coordinate between libraries

## Integration Points

- **Previous Tasks**: Builds on topographical navigation from Phase 2
- **Next Task**: Task 010 will add URL state management to make walks bookmarkable
- **HTMX**: Must coordinate with HTMX for content loading
- **Mobile**: Task 012 will adapt this for mobile devices

## Acceptance Criteria Checklist

Before marking this task complete, ensure:

- [ ] All tests written first and failing appropriately
- [ ] Alpine.js integrated without breaking existing functionality
- [ ] Panels slide horizontally on desktop
- [ ] Smooth animations at 60fps verified
- [ ] Intelligent stacking logic implemented
- [ ] Keyboard navigation fully functional
- [ ] Maximum depth limit enforced
- [ ] Memory properly managed
- [ ] No conflicts with HTMX
- [ ] Graceful degradation without JavaScript
- [ ] All existing tests still pass

## Resources

- [Alpine.js Documentation](https://alpinejs.dev/start-here)
- [Alpine.js + HTMX Integration](https://alpinejs.dev/advanced/extending)
- [CSS Transforms Performance](https://web.dev/animations-guide/)
- [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)

## Expected Deliverables

1. Alpine.js component for panel management
2. CSS for smooth panel transitions
3. HTML templates with Alpine directives
4. Comprehensive test suite
5. Performance benchmarks documented
6. No breaking changes to existing features

## Performance Requirements

- Initial render < 100ms
- Panel transitions < 300ms
- 60fps during animations
- Memory usage < 50MB with 5 panels
- Works on 2015+ devices

Remember: This is a core differentiating feature. Focus on user experience and smooth interactions!