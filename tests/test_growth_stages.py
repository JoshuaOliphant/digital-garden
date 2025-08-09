# ABOUTME: Tests for the growth stages system in the digital garden
# ABOUTME: These tests define behavior for content lifecycle management using garden metaphors

import pytest
from datetime import datetime
from enum import Enum
from pydantic import ValidationError

# Import existing models and non-existent features that need to be implemented
from app.models import BaseContent, Bookmark, TIL, Note
from app.models import GrowthStage  # This doesn't exist yet - needs implementation
from app.vocabulary_helper import (  # This module doesn't exist yet
    convert_to_garden_vocabulary,
    GROWTH_STAGES,
    get_growth_stage_color,
    get_growth_stage_emoji,
)


class TestGrowthStageEnum:
    """Test the GrowthStage enum that defines valid growth stages."""

    def test_growth_stage_enum_values(self):
        """Test that GrowthStage enum has correct values."""
        assert GrowthStage.SEEDLING == "seedling"
        assert GrowthStage.BUDDING == "budding"
        assert GrowthStage.GROWING == "growing"
        assert GrowthStage.EVERGREEN == "evergreen"

    def test_growth_stage_enum_is_complete(self):
        """Test that all expected growth stages are present."""
        expected_stages = {"seedling", "budding", "growing", "evergreen"}
        actual_stages = {stage.value for stage in GrowthStage}
        assert actual_stages == expected_stages


class TestBaseContentGrowthStageValidation:
    """Test growth stage validation in BaseContent model."""

    def test_base_content_accepts_valid_growth_stages(self):
        """Test that BaseContent accepts all valid growth_stage values."""
        valid_stages = ["seedling", "budding", "growing", "evergreen"]
        
        for stage in valid_stages:
            content = BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                growth_stage=stage,
            )
            assert content.growth_stage == stage

    def test_base_content_rejects_invalid_growth_stages(self):
        """Test that invalid growth_stage values raise ValidationError."""
        invalid_stages = ["invalid", "draft", "published", "mature", ""]
        
        for stage in invalid_stages:
            with pytest.raises(ValidationError) as exc_info:
                BaseContent(
                    title="Test Content",
                    created=datetime.now(),
                    updated=datetime.now(),
                    tags=["test"],
                    growth_stage=stage,
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
        assert content.growth_stage == "seedling"

    def test_growth_stage_enum_integration(self):
        """Test that BaseContent accepts GrowthStage enum values."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage=GrowthStage.EVERGREEN,
        )
        assert content.growth_stage == "evergreen"


class TestTendedCountTracking:
    """Test the tended_count field that tracks content updates."""

    def test_tended_count_defaults_to_zero(self):
        """Test that tended_count defaults to 0 for new content."""
        content = BaseContent(
            title="New Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.tended_count == 0

    def test_tended_count_increments_on_update(self):
        """Test that tended_count increments when content is updated."""
        # This test assumes there's a method to update content that increments tended_count
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            tended_count=5,
        )
        
        # Simulate an update - this would be handled by the update method
        content.tend()  # This method doesn't exist yet - needs implementation
        assert content.tended_count == 6

    def test_tended_count_is_non_negative(self):
        """Test that tended_count cannot be negative."""
        with pytest.raises(ValidationError):
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                tended_count=-1,
            )


class TestGardenBedField:
    """Test the garden_bed field for content organization."""

    def test_garden_bed_is_optional(self):
        """Test that garden_bed field is optional."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.garden_bed is None

    def test_garden_bed_accepts_valid_strings(self):
        """Test that garden_bed accepts valid string values."""
        valid_beds = ["programming", "data-science", "personal", "projects", "learning"]
        
        for bed in valid_beds:
            content = BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                garden_bed=bed,
            )
            assert content.garden_bed == bed

    def test_garden_bed_validates_as_string(self):
        """Test that garden_bed must be a string if provided."""
        with pytest.raises(ValidationError):
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                garden_bed=123,  # Should be string, not int
            )


class TestConnectionsField:
    """Test the connections field for linking related content."""

    def test_connections_defaults_to_empty_list(self):
        """Test that connections field defaults to empty list."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        assert content.connections == []

    def test_connections_accepts_list_of_content_ids(self):
        """Test that connections field accepts list of content IDs."""
        content_ids = ["note-123", "til-456", "bookmark-789"]
        
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            connections=content_ids,
        )
        assert content.connections == content_ids

    def test_connections_validates_as_list(self):
        """Test that connections must be a list."""
        with pytest.raises(ValidationError):
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                connections="not-a-list",  # Should be list, not string
            )


class TestVocabularyMapping:
    """Test the garden vocabulary helper functions."""

    def test_convert_created_to_planted(self):
        """Test that 'created' is converted to 'planted' in garden vocabulary."""
        result = convert_to_garden_vocabulary("created")
        assert result == "planted"

    def test_convert_updated_to_tended(self):
        """Test that 'updated' is converted to 'tended' in garden vocabulary."""
        result = convert_to_garden_vocabulary("updated")
        assert result == "tended"

    def test_convert_unknown_terms_unchanged(self):
        """Test that unknown terms are returned unchanged."""
        unknown_terms = ["title", "tags", "status", "description"]
        
        for term in unknown_terms:
            result = convert_to_garden_vocabulary(term)
            assert result == term

    def test_growth_stages_constant_exists(self):
        """Test that GROWTH_STAGES constant is properly defined."""
        assert isinstance(GROWTH_STAGES, dict)
        assert "seedling" in GROWTH_STAGES
        assert "budding" in GROWTH_STAGES
        assert "growing" in GROWTH_STAGES
        assert "evergreen" in GROWTH_STAGES

    def test_growth_stage_colors_mapping(self):
        """Test that growth stage colors map correctly."""
        expected_colors = {
            "seedling": "#10b981",  # emerald-500
            "budding": "#f59e0b",   # amber-500
            "growing": "#3b82f6",   # blue-500
            "evergreen": "#059669", # emerald-600
        }
        
        for stage, expected_color in expected_colors.items():
            color = get_growth_stage_color(stage)
            assert color == expected_color

    def test_growth_stage_emojis_mapping(self):
        """Test that growth stage emojis map correctly."""
        expected_emojis = {
            "seedling": "🌱",
            "budding": "🌿",
            "growing": "🌳",
            "evergreen": "🌲",
        }
        
        for stage, expected_emoji in expected_emojis.items():
            emoji = get_growth_stage_emoji(stage)
            assert emoji == expected_emoji


class TestExistingContentBackwardCompatibility:
    """Test that existing content without growth_stage loads properly."""

    def test_existing_content_loads_with_default_growth_stage(self):
        """Test that content without growth_stage gets default value."""
        # Simulate loading content that was created before growth stages existed
        content_data = {
            "title": "Existing Content",
            "created": datetime.now(),
            "updated": datetime.now(),
            "tags": ["test"],
            "status": "Evergreen",
        }
        
        content = BaseContent(**content_data)
        assert content.growth_stage == "seedling"  # Should get default

    def test_existing_content_preserves_growth_stage_if_present(self):
        """Test that existing content with growth_stage preserves the value."""
        content_data = {
            "title": "Existing Content",
            "created": datetime.now(),
            "updated": datetime.now(),
            "tags": ["test"],
            "growth_stage": "evergreen",
        }
        
        content = BaseContent(**content_data)
        assert content.growth_stage == "evergreen"


class TestSpecializedContentModels:
    """Test that specialized content models inherit growth stage behavior."""

    def test_bookmark_inherits_growth_stage(self):
        """Test that Bookmark model inherits growth stage functionality."""
        bookmark = Bookmark(
            title="Test Bookmark",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            url="https://example.com",
            growth_stage="budding",
        )
        assert bookmark.growth_stage == "budding"

    def test_til_inherits_growth_stage(self):
        """Test that TIL model inherits growth stage functionality."""
        til = TIL(
            title="Test TIL",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="growing",
        )
        assert til.growth_stage == "growing"

    def test_note_inherits_growth_stage(self):
        """Test that Note model inherits growth stage functionality."""
        note = Note(
            title="Test Note",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="evergreen",
        )
        assert note.growth_stage == "evergreen"


class TestGrowthStageProgression:
    """Test logical progression of growth stages."""

    def test_growth_stage_progression_logic(self):
        """Test that growth stages follow logical progression."""
        # This would test business logic for automatic stage progression
        # based on factors like tended_count, age, connections, etc.
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="seedling",
            tended_count=0,
        )
        
        # After being tended multiple times, it might auto-advance
        for _ in range(5):
            content.tend()
        
        # This logic doesn't exist yet but could auto-advance stages
        assert content.should_advance_growth_stage()  # Method doesn't exist yet
        
    def test_evergreen_content_stays_evergreen(self):
        """Test that evergreen content doesn't regress to earlier stages."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage="evergreen",
        )
        
        # Even with no tending, evergreen should stay evergreen
        assert content.growth_stage == "evergreen"
        # Simulate time passing without updates
        content.check_growth_stage_regression()  # Method doesn't exist yet
        assert content.growth_stage == "evergreen"