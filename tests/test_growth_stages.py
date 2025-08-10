# ABOUTME: Tests for the growth stages system in the digital garden
# ABOUTME: These tests verify content lifecycle management using garden metaphors

import pytest
from datetime import datetime
from pydantic import ValidationError

# Import the actual implementations
from app.models import BaseContent, Bookmark, TIL, Note, GrowthStage
from app.vocabulary_helper import (
    convert_to_garden_vocabulary,
    GROWTH_STAGES,
    get_growth_stage_color,
    get_growth_stage_emoji,
)


class TestGrowthStageEnum:
    """Test the GrowthStage enum that defines valid growth stages."""

    def test_growth_stage_enum_values(self):
        """Test that GrowthStage enum has correct values."""
        assert GrowthStage.SEEDLING.value == "seedling"
        assert GrowthStage.BUDDING.value == "budding"
        assert GrowthStage.GROWING.value == "growing"
        assert GrowthStage.EVERGREEN.value == "evergreen"

    def test_growth_stage_enum_has_all_stages(self):
        """Test that all expected growth stages exist."""
        stages = [stage.value for stage in GrowthStage]
        assert "seedling" in stages
        assert "budding" in stages
        assert "growing" in stages
        assert "evergreen" in stages
        assert len(stages) == 4


class TestBaseContentGrowthStage:
    """Test growth stage functionality in BaseContent model."""

    def test_base_content_accepts_valid_growth_stage(self):
        """Test that BaseContent accepts valid growth stage values."""
        for stage in ["seedling", "budding", "growing", "evergreen"]:
            content = BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                growth_stage=stage,
            )
            assert content.growth_stage == GrowthStage(stage)

    def test_base_content_rejects_invalid_growth_stage(self):
        """Test that BaseContent raises error for invalid growth stage."""
        with pytest.raises(ValidationError) as exc_info:
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                growth_stage="invalid_stage",
            )
        errors = exc_info.value.errors()
        assert any("growth_stage" in str(error) for error in errors)

    def test_growth_stage_defaults_to_seedling(self):
        """Test that growth_stage defaults to 'seedling' for new content."""
        content = BaseContent(
            title="New Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.growth_stage == GrowthStage.SEEDLING

    def test_existing_content_without_growth_stage(self):
        """Test that existing content without growth_stage loads with default."""
        # Simulate loading existing content without growth_stage field
        content = BaseContent(
            title="Existing Content",
            created=datetime(2024, 1, 1),
            updated=datetime(2024, 1, 2),
            tags=["existing"],
            status="Evergreen",  # Old field still works
        )
        assert content.growth_stage == GrowthStage.SEEDLING
        assert content.status == "Evergreen"  # Backward compatibility


class TestTendedCount:
    """Test the tended_count functionality."""

    def test_tended_count_defaults_to_zero(self):
        """Test that tended_count defaults to 0 for new content."""
        content = BaseContent(
            title="New Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.tended_count == 0

    def test_tended_count_increments(self):
        """Test that tended_count increments when tend() is called."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            tended_count=5,
        )
        content.tend()
        assert content.tended_count == 6

    def test_tended_count_non_negative(self):
        """Test that tended_count cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                tended_count=-1,
            )
        errors = exc_info.value.errors()
        assert any("tended_count" in str(error) for error in errors)


class TestGardenBed:
    """Test the garden_bed field functionality."""

    def test_garden_bed_is_optional(self):
        """Test that garden_bed field is optional."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.garden_bed is None

    def test_garden_bed_accepts_string(self):
        """Test that garden_bed accepts string values."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            garden_bed="vegetable-garden",
        )
        assert content.garden_bed == "vegetable-garden"

    def test_garden_bed_validates_type(self):
        """Test that garden_bed validates as string type."""
        with pytest.raises(ValidationError) as exc_info:
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                garden_bed=123,  # Should be string
            )
        errors = exc_info.value.errors()
        assert any("garden_bed" in str(error) for error in errors)


class TestConnections:
    """Test the connections field functionality."""

    def test_connections_defaults_to_empty_list(self):
        """Test that connections defaults to empty list."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.connections == []

    def test_connections_accepts_list_of_ids(self):
        """Test that connections accepts list of content IDs."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            connections=["note-1", "til-2", "bookmark-3"],
        )
        assert content.connections == ["note-1", "til-2", "bookmark-3"]

    def test_connections_validates_type(self):
        """Test that connections validates as list type."""
        with pytest.raises(ValidationError) as exc_info:
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                connections="not-a-list",  # Should be list
            )
        errors = exc_info.value.errors()
        assert any("connections" in str(error) for error in errors)


class TestVocabularyMapping:
    """Test vocabulary mapping functions."""

    def test_convert_created_to_planted(self):
        """Test that 'created' converts to 'planted'."""
        result = convert_to_garden_vocabulary("created")
        assert result == "planted"

    def test_convert_updated_to_tended(self):
        """Test that 'updated' converts to 'tended'."""
        result = convert_to_garden_vocabulary("updated")
        assert result == "tended"

    def test_convert_unknown_term_unchanged(self):
        """Test that unknown terms remain unchanged."""
        result = convert_to_garden_vocabulary("unknown")
        assert result == "unknown"

    def test_growth_stages_constant_exists(self):
        """Test that GROWTH_STAGES constant is defined."""
        assert GROWTH_STAGES is not None
        assert isinstance(GROWTH_STAGES, dict)
        assert len(GROWTH_STAGES) > 0

    def test_growth_stage_colors_mapping(self):
        """Test that growth stages have color mappings."""
        for stage in ["seedling", "budding", "growing", "evergreen"]:
            color = get_growth_stage_color(stage)
            assert color is not None
            assert isinstance(color, str)
            assert len(color) > 0

    def test_growth_stage_emojis_mapping(self):
        """Test that growth stages have emoji mappings."""
        for stage in ["seedling", "budding", "growing", "evergreen"]:
            emoji = get_growth_stage_emoji(stage)
            assert emoji is not None
            assert isinstance(emoji, str)
            assert len(emoji) > 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing content."""

    def test_existing_content_loads_without_new_fields(self):
        """Test that content loads without growth stage fields."""
        # Simulate loading old content that only has required fields
        content = BaseContent(
            title="Old Content",
            created=datetime(2023, 1, 1),
            updated=datetime(2023, 1, 2),
            tags=["old"],
            status="Budding",
        )
        # Should have default values for new fields
        assert content.growth_stage == GrowthStage.SEEDLING
        assert content.tended_count == 0
        assert content.garden_bed is None
        assert content.connections == []

    def test_growth_stage_preserved_on_update(self):
        """Test that growth stage is preserved when updating content."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="evergreen",
        )
        # Update other fields
        content.title = "Updated Title"
        content.tags = ["test", "updated"]
        # Growth stage should remain unchanged
        assert content.growth_stage == GrowthStage.EVERGREEN


class TestSpecializedModels:
    """Test that specialized content models inherit growth stage functionality."""

    def test_bookmark_has_growth_stage(self):
        """Test that Bookmark model has growth stage field."""
        bookmark = Bookmark(
            title="Test Bookmark",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            url="https://example.com",
            growth_stage="budding",
        )
        assert bookmark.growth_stage == GrowthStage.BUDDING

    def test_til_has_growth_stage(self):
        """Test that TIL model has growth stage field."""
        til = TIL(
            title="Test TIL",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="growing",
        )
        assert til.growth_stage == GrowthStage.GROWING

    def test_note_has_growth_stage(self):
        """Test that Note model has growth stage field."""
        note = Note(
            title="Test Note",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="evergreen",
        )
        assert note.growth_stage == GrowthStage.EVERGREEN


class TestGrowthLogic:
    """Test growth stage progression logic."""

    def test_should_advance_growth_stage(self):
        """Test logic for when content should advance growth stage."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="seedling",
            tended_count=10,
        )
        # With 10 tends, seedling should be ready to advance
        assert content.should_advance_growth_stage() is True

        # Evergreen content should never advance
        content.growth_stage = GrowthStage.EVERGREEN
        content.tended_count = 100
        assert content.should_advance_growth_stage() is False

    def test_growth_stage_regression_check(self):
        """Test that growth stages don't regress."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="evergreen",
        )
        # Should not allow regression from evergreen to growing
        assert content.check_growth_stage_regression("growing") is False
        # Should allow progression or same stage
        assert content.check_growth_stage_regression("evergreen") is True
