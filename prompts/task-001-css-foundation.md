# Task 001: CSS Foundation with Garden Color Palette

## Context
You're beginning the Digital Garden Modernization project. The existing application uses FastAPI with HTMX and Tailwind CSS. Currently, Tailwind is loaded via CDN which needs to be migrated to a compiled approach. This is the first task in establishing the garden aesthetic.

## Objective
Create a CSS foundation with garden-themed color palette supporting both light and dark modes. This will establish the visual design system that all subsequent features will build upon.

## Test Requirements

Write these tests FIRST before any implementation:

### 1. Color Contrast Tests (`tests/test_css_colors.py`)
```python
def test_light_mode_color_contrast():
    """Verify light mode colors meet WCAG AA standards"""
    # Test that cream background with sage text has contrast ratio >= 4.5:1
    # Test that all color combinations meet accessibility standards
    
def test_dark_mode_color_contrast():
    """Verify dark mode colors meet WCAG AA standards"""
    # Test deep blue-black background with bioluminescent accents
    # Ensure improved contrast ratios for night reading
```

### 2. CSS Variable Tests (`tests/test_css_variables.py`)
```python
def test_css_variables_exist():
    """Verify all required CSS variables are defined"""
    # Check for --color-background, --color-primary, --color-secondary
    # Check for --color-accent, --color-action in both themes
    
def test_css_theme_switching():
    """Verify theme variables switch correctly"""
    # Test that [data-theme="dark"] overrides :root variables
    # Test that all color variables have dark mode equivalents
```

### 3. Integration Tests (`tests/test_theme_integration.py`)
```python
def test_compiled_css_loads():
    """Verify compiled CSS loads instead of CDN"""
    # Test that base.html doesn't reference Tailwind CDN
    # Test that /static/css/output.css exists and loads
    
def test_theme_persistence():
    """Verify theme choice persists across sessions"""
    # Test localStorage saves theme preference
    # Test theme loads correctly on page refresh
```

## Implementation Hints

1. **Color Palette Structure**:
   - Define colors as CSS custom properties
   - Use HSL values for easier manipulation
   - Create semantic color names (not just color values)

2. **File Organization**:
   ```
   static/css/
   ├── variables.css    (color definitions)
   ├── themes.css       (theme switching logic)
   └── output.css       (compiled Tailwind + custom)
   ```

3. **Theme Switching Approach**:
   - Use `data-theme` attribute on `<html>` element
   - Store preference in localStorage
   - Include system preference detection as fallback

4. **Accessibility Considerations**:
   - Use tools like WebAIM contrast checker
   - Test with color blindness simulators
   - Ensure focus indicators remain visible

## Integration Points

- **Next Task**: Task 002 will extend Pydantic models with growth stages that will use these color definitions
- **Dependent Tasks**: Task 004 will complete the Tailwind migration building on this foundation
- **Templates**: All Jinja2 templates will reference these CSS variables

## Acceptance Criteria Checklist

Before marking this task complete, ensure:

- [ ] All tests written first and failing appropriately
- [ ] Light mode colors defined: Cream (#FAFAF8), Sage (#6B8E6B, #A3B88C), Earth (#8B7355, #D4C5B9), Sky (#5B8FA3)
- [ ] Dark mode colors defined: Deep blue-black (#1a1f2e) with bioluminescent accents
- [ ] All color combinations pass WCAG AA contrast standards
- [ ] CSS variables organized in :root and [data-theme="dark"] selectors
- [ ] Theme switching works without JavaScript (CSS-only fallback)
- [ ] All tests passing with 100% coverage for new code
- [ ] No visual regressions in existing pages

## Resources

- [WCAG Contrast Requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [CSS Custom Properties Guide](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [HSL Color Model](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/hsl)
- [Tailwind CSS Configuration](https://tailwindcss.com/docs/configuration)

## Expected Deliverables

1. CSS files with color variables and theme logic
2. Test files with comprehensive coverage
3. Updated configuration for CSS compilation
4. Documentation of color palette usage
5. No breaking changes to existing functionality

Remember: Write tests first, make them fail, then implement the minimum code needed to make them pass!