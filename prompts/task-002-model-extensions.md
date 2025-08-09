# Task 002: Extend Pydantic Models with Growth Stage

## Context
The Digital Garden philosophy includes the concept of content maturity stages. Currently, the application uses Pydantic models for content validation but lacks garden-specific fields. The existing BaseContent model in `app/models.py` needs extension to support growth stages while maintaining backward compatibility.

## Objective
Extend the existing Pydantic models to include growth stage tracking, enabling content to be classified as seedling, budding, growing, or evergreen. This forms the data foundation for all garden features.

## Test Requirements

Write these tests FIRST before any implementation:

### 1. Model Validation Tests (`tests/test_models_growth.py`)
```python
def test_growth_stage_enum_values():
    """Test that only valid growth stages are accepted"""
    # Test valid stages: seedling, budding, growing, evergreen
    # Test invalid stages raise ValidationError
    # Test case sensitivity handling
    
def test_growth_stage_default_value():
    """Test that new content defaults to seedling stage"""
    # Create content without specifying growth_stage
    # Verify it defaults to "seedling"
    # Test that explicit stages override default
    
def test_growth_stage_model_integration():
    """Test growth stage integrates with existing fields"""
    # Test BaseContent with growth_stage
    # Test all content types inherit growth_stage
    # Verify no conflicts with existing fields
```

### 2. Migration Tests (`tests/test_content_migration.py`)
```python
def test_existing_content_migration():
    """Test that existing content handles growth stage gracefully"""
    # Load content without growth_stage field
    # Verify it gets assigned appropriate default
    # Test that existing functionality isn't broken
    
def test_frontmatter_parsing_with_growth():
    """Test YAML frontmatter parsing includes growth stage"""
    # Parse markdown with growth_stage in frontmatter
    # Parse markdown without growth_stage
    # Verify both cases work correctly
```

### 3. Business Logic Tests (`tests/test_growth_logic.py`)
```python
def test_growth_stage_metadata():
    """Test growth stage metadata (emoji, color, description)"""
    # Test each stage has correct emoji
    # Test each stage has correct color mapping
    # Test each stage has meaningful description
    
def test_growth_stage_progression():
    """Test logical progression of growth stages"""
    # Verify stages can progress forward
    # Test that regression is possible (evergreen → budding)
    # Test transition rules if any
```

## Implementation Hints

1. **Model Structure**:
   ```python
   # Consider using Enum for type safety
   # Add to BaseContent for inheritance
   # Include metadata dict for UI display
   ```

2. **Growth Stage Definitions**:
   ```python
   GROWTH_STAGES = {
       "seedling": {"emoji": "🌱", "color": "stone", "desc": "Just planted"},
       "budding": {"emoji": "🌿", "color": "amber", "desc": "Taking shape"},
       "growing": {"emoji": "🪴", "color": "lime", "desc": "Developing"},
       "evergreen": {"emoji": "🌳", "color": "emerald", "desc": "Mature"}
   }
   ```

3. **Backward Compatibility**:
   - Use Optional fields with defaults
   - Handle missing fields in existing content
   - Don't break existing API contracts

4. **Validation Approach**:
   - Use Pydantic validators for custom logic
   - Consider field validators for stage transitions
   - Maintain clear error messages

## Integration Points

- **Previous Task**: Uses color definitions from Task 001 for stage colors
- **Next Tasks**: Task 003 will use growth stages in template vocabulary
- **ContentManager**: Must handle growth stage in parsing and caching
- **API Routes**: Existing routes should return growth stage without breaking

## Acceptance Criteria Checklist

Before marking this task complete, ensure:

- [ ] All tests written first and failing appropriately
- [ ] BaseContent model includes growth_stage field
- [ ] Valid stages: seedling, budding, growing, evergreen enforced
- [ ] Default stage is "seedling" for new content
- [ ] Existing content migration handled without errors
- [ ] Growth stage metadata (emoji, color, description) accessible
- [ ] All existing tests still pass
- [ ] No breaking changes to API responses
- [ ] ContentManager correctly parses growth_stage from frontmatter
- [ ] 100% test coverage for new code

## Resources

- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [Python Enum Documentation](https://docs.python.org/3/library/enum.html)
- [Pydantic Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Digital Garden Growth Stages](https://maggieappleton.com/garden-history)

## Expected Deliverables

1. Updated models.py with growth stage support
2. Comprehensive test suite for growth stages
3. Migration logic for existing content
4. Documentation of growth stage usage
5. No breaking changes to existing functionality

## Code Quality Requirements

- Type hints for all new methods
- Docstrings explaining growth stage logic
- Clear validation error messages
- Maintain existing code style

Remember: Red → Green → Refactor. Write the test, see it fail, then implement just enough to pass!