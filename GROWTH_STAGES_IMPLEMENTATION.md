# Growth Stages TDD Implementation Plan

## Overview
Transform digital garden from static "status" to dynamic growth-based system with organic vocabulary and enhanced tracking.

## TDD Test Requirements (Write These First)

### Phase 1 Tests - Model Foundation
1. **test_growth_stage_enum_validation** - BaseContent accepts valid growth_stage values (seedling, budding, growing, evergreen)
2. **test_invalid_growth_stage_raises_error** - Invalid growth_stage raises ValidationError with helpful message
3. **test_growth_stage_default_seedling** - growth_stage defaults to "seedling" for new content without field
4. **test_backward_compatibility_status_mapping** - Existing content with "status" field maps to appropriate growth_stage
5. **test_tended_count_field** - tended_count field accepts integer values and defaults to 0

### Phase 2 Tests - Template Vocabulary  
6. **test_template_vocabulary_planted** - Templates display "planted" instead of "created" 
7. **test_template_vocabulary_tended** - Templates display "tended" instead of "updated"
8. **test_growth_stage_emoji_display** - Growth stages display correct emoji (🌱 seedling, 🌿 budding, 🌳 growing, 🌲 evergreen)
9. **test_growth_stage_color_mapping** - Growth stages have proper CSS color classes

### Phase 3 Tests - Enhanced Features
10. **test_garden_bed_optional_field** - garden_bed field is optional string for categorization
11. **test_connections_list_validation** - connections field stores list of valid content IDs
12. **test_tended_count_increment** - tended_count increments when content is updated

## Implementation Tasks by Phase

### Phase 1: Model Foundation (Est: 2-3 days)

#### Task 1.1: Create Growth Stage System
- **File**: `app/models.py`
- **Priority**: High
- **Effort**: Medium
- **Dependencies**: None

**Acceptance Criteria**:
- Create `GrowthStage` enum with values: seedling, budding, growing, evergreen
- Add emoji and color mapping dictionaries
- Write tests 1, 2, 3 before implementation

**Implementation Steps**:
1. Add enum import: `from enum import Enum`
2. Create `GrowthStage(str, Enum)` class
3. Create `GROWTH_STAGE_EMOJIS` and `GROWTH_STAGE_COLORS` dictionaries
4. Write failing tests first
5. Implement enum to pass tests

#### Task 1.2: Update BaseContent Model
- **File**: `app/models.py`  
- **Priority**: High
- **Effort**: Medium
- **Dependencies**: Task 1.1

**Acceptance Criteria**:
- Add new fields while preserving existing ones
- Implement backward compatibility for status field
- All existing tests continue to pass
- Write tests 4, 5 before implementation

**Implementation Steps**:
1. Write failing tests for backward compatibility
2. Add new fields to BaseContent:
   - `growth_stage: GrowthStage = GrowthStage.SEEDLING`
   - `tended_count: int = 0` 
   - `garden_bed: Optional[str] = None`
   - `connections: List[str] = []`
3. Add `@field_validator` for status->growth_stage mapping
4. Implement model validation logic

#### Task 1.3: Model Test Coverage
- **File**: `tests/test_models.py`
- **Priority**: High  
- **Effort**: Low
- **Dependencies**: Task 1.2

**Acceptance Criteria**:
- All 5 model tests pass
- Edge cases covered (empty values, invalid types)
- Backward compatibility thoroughly tested

### Phase 2: Template Vocabulary Migration (Est: 2-3 days)

#### Task 2.1: Update Content Card Template
- **File**: `app/templates/partials/content_card.html`
- **Priority**: High
- **Effort**: Medium
- **Dependencies**: Task 1.2

**Acceptance Criteria**:
- Display "planted" instead of "created"
- Display "tended" instead of "updated"  
- Show growth stage emoji and colors
- Write tests 6, 7, 8, 9 before changes

**Implementation Steps**:
1. Write template rendering tests
2. Update time display vocabulary
3. Add growth stage visual indicators
4. Test responsive design

#### Task 2.2: Update All Template Files
- **Files**: All templates in `app/templates/`
- **Priority**: High
- **Effort**: High
- **Dependencies**: Task 2.1

**Acceptance Criteria**:
- Consistent vocabulary across all templates
- Growth stage indicators work everywhere
- No broken layouts or missing data

**Templates to Update**:
- `base.html` - Check for date displays
- `content_page.html` - Individual content view
- `index.html` - Home page content cards
- `partials/*.html` - All partial templates

#### Task 2.3: CSS Styling for Growth Stages
- **File**: `app/static/src/input.css` (Tailwind)
- **Priority**: Medium
- **Effort**: Low
- **Dependencies**: Task 2.1

**Acceptance Criteria**:
- Growth stage colors defined in CSS
- Hover states and transitions work
- Accessible color contrast maintained

### Phase 3: Enhanced Features (Est: 3-4 days)

#### Task 3.1: Implement Tended Count Logic
- **File**: `app/main.py` (ContentManager)
- **Priority**: Medium
- **Effort**: Medium
- **Dependencies**: Task 1.2

**Acceptance Criteria**:
- tended_count increments on content updates
- Logic works with existing caching system
- Write test 12 before implementation

**Implementation Steps**:
1. Write failing test for increment logic
2. Add update tracking in `_parse_front_matter`
3. Implement increment logic
4. Test with real content files

#### Task 3.2: Garden Bed Categorization
- **File**: `app/main.py`, templates
- **Priority**: Low
- **Effort**: Low  
- **Dependencies**: Task 2.2

**Acceptance Criteria**:
- garden_bed field displays in templates
- Filtering by garden bed works
- Write test 10 before implementation

#### Task 3.3: Connections System
- **File**: `app/models.py`, `app/main.py`
- **Priority**: Medium
- **Effort**: High
- **Dependencies**: Task 1.2

**Acceptance Criteria**:
- connections field validates content IDs
- Related content displays in templates
- Bidirectional relationship support
- Write test 11 before implementation

**Implementation Steps**:
1. Write comprehensive connection validation tests
2. Add content ID validation logic
3. Update templates to show connections
4. Implement relationship queries

### Phase 4: Integration & Testing (Est: 2 days)

#### Task 4.1: End-to-End Testing
- **Files**: `tests/test_main.py`, new integration tests
- **Priority**: High
- **Effort**: Medium
- **Dependencies**: All previous tasks

**Acceptance Criteria**:
- All existing functionality preserved
- New features work end-to-end
- Performance benchmarks met
- No regression in existing tests

#### Task 4.2: Content Migration Utilities
- **File**: `scripts/migrate_to_growth_stages.py`
- **Priority**: Medium
- **Effort**: Low
- **Dependencies**: All previous tasks

**Acceptance Criteria**:
- Script safely migrates existing content
- Dry-run mode available
- Backup and rollback capabilities
- Comprehensive logging

## File Changes Summary

### Core Files to Modify:
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/app/models.py` - Add growth stage enum and new fields
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/app/main.py` - Update parsing logic  
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/tests/test_models.py` - Add comprehensive model tests
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/app/templates/partials/content_card.html` - Update vocabulary and visual indicators

### Template Files (vocabulary updates):
- All files in `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/app/templates/`

### New Files to Create:
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/tests/test_growth_stages.py` - Dedicated growth stage tests
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/digital_garden/scripts/migrate_to_growth_stages.py` - Migration utility

## Testing Strategy

### TDD Process:
1. Write failing test first
2. Run test to confirm it fails
3. Write minimal code to pass test
4. Refactor while keeping tests green
5. Repeat for next feature

### Test Categories:
- **Unit Tests**: Model validation, enum behavior
- **Integration Tests**: Template rendering, content parsing
- **End-to-End Tests**: Full content lifecycle with new fields

### Success Criteria:
- All existing tests continue to pass
- All 12 new tests pass
- No performance regression
- Backward compatibility maintained
- Zero broken existing content

## Rollback Plan

### Immediate Rollback Steps:
1. Revert model changes in `app/models.py`
2. Restore original templates from git
3. Remove new test files
4. Clear any cached content

### Data Protection:
- All existing content files remain unchanged
- No destructive migrations during development
- Git branch protection throughout implementation

## Risk Mitigation Checklist

- [ ] All existing tests pass before starting
- [ ] Each phase tested independently  
- [ ] Backward compatibility verified at each step
- [ ] Performance monitoring throughout
- [ ] Rollback procedure tested
- [ ] Content file backup before any migration
- [ ] Template fallbacks implemented
- [ ] Error handling comprehensive