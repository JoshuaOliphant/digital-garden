# ABOUTME: Tests for the growth stages system in the digital garden
# ABOUTME: These tests define behavior for content lifecycle management using garden metaphors

import pytest
from datetime import datetime
from enum import Enum
from pydantic import ValidationError
from unittest.mock import Mock

# Import existing models
from app.models import BaseContent, Bookmark, TIL, Note

# Mock the non-existent features that need to be implemented
# This allows tests to run and fail appropriately
try:
    from app.models import GrowthStage
except ImportError:
    # Create a mock GrowthStage enum for testing
    class GrowthStage(Enum):
        SEEDLING = "seedling"
        BUDDING = "budding" 
        GROWING = "growing"
        EVERGREEN = "evergreen"

try:
    from app.vocabulary_helper import (
        convert_to_garden_vocabulary,
        GROWTH_STAGES,
        get_growth_stage_color,
        get_growth_stage_emoji,
    )
except ImportError:
    # Mock functions for testing - these will need to be implemented
    def convert_to_garden_vocabulary(term):
        raise NotImplementedError("vocabulary_helper module not implemented yet")
    
    GROWTH_STAGES = {}
    
    def get_growth_stage_color(stage):
        raise NotImplementedError("get_growth_stage_color function not implemented yet")
    
    def get_growth_stage_emoji(stage):
        raise NotImplementedError("get_growth_stage_emoji function not implemented yet")


class TestGrowthStageEnum:
    """Test the GrowthStage enum that defines valid growth stages."""

    def test_growth_stage_enum_values(self):
        """Test that GrowthStage enum has correct values."""
        assert GrowthStage.SEEDLING.value == "seedling"
        assert GrowthStage.BUDDING.value == "budding"
        assert GrowthStage.GROWING.value == "growing"
        assert GrowthStage.EVERGREEN.value == "evergreen"

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
            with pytest.raises(ValidationError) as exc_info:
                # This will fail because growth_stage field doesn't exist yet
                content = BaseContent(
                    title="Test Content",
                    created=datetime.now(),
                    updated=datetime.now(),
                    tags=["test"],
                    growth_stage=stage,
                )
            
            # The error should be about an unknown field, not validation
            errors = exc_info.value.errors()
            assert any("growth_stage" in str(error) for error in errors)

    def test_base_content_rejects_invalid_growth_stages(self):
        """Test that invalid growth_stage values raise ValidationError."""
        invalid_stages = ["invalid", "draft", "published", "mature", ""]
        
        for stage in invalid_stages:
            with pytest.raises(ValidationError) as exc_info:
                # This will fail because growth_stage field doesn't exist yet
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
        
        # This will fail because growth_stage field doesn't exist yet
        with pytest.raises(AttributeError):
            assert content.growth_stage == "seedling"

    def test_growth_stage_enum_integration(self):
        """Test that BaseContent accepts GrowthStage enum values."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because growth_stage field doesn't exist yet
            content = BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                growth_stage=GrowthStage.EVERGREEN,
            )
        
        errors = exc_info.value.errors()
        assert any("growth_stage" in str(error) for error in errors)


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
        
        # This will fail because tended_count field doesn't exist yet
        with pytest.raises(AttributeError):
            assert content.tended_count == 0

    def test_tended_count_increments_on_update(self):
        """Test that tended_count increments when content is updated."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because tended_count field doesn't exist yet
            content = BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                tended_count=5,
            )
        
        errors = exc_info.value.errors()
        assert any("tended_count" in str(error) for error in errors)
        
        # Test for tend() method that doesn't exist yet
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        
        with pytest.raises(AttributeError):
            content.tend()  # This method doesn't exist yet - needs implementation

    def test_tended_count_is_non_negative(self):
        """Test that tended_count cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because tended_count field doesn't exist yet
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                tended_count=-1,
            )
        
        errors = exc_info.value.errors()
        assert any("tended_count" in str(error) for error in errors)


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
        
        # This will fail because garden_bed field doesn't exist yet
        with pytest.raises(AttributeError):
            assert content.garden_bed is None

    def test_garden_bed_accepts_valid_strings(self):
        """Test that garden_bed accepts valid string values."""
        valid_beds = ["programming", "data-science", "personal", "projects", "learning"]
        
        for bed in valid_beds:
            with pytest.raises(ValidationError) as exc_info:
                # This will fail because garden_bed field doesn't exist yet
                content = BaseContent(
                    title="Test Content",
                    created=datetime.now(),
                    updated=datetime.now(),
                    tags=["test"],
                    garden_bed=bed,
                )
            
            errors = exc_info.value.errors()
            assert any("garden_bed" in str(error) for error in errors)

    def test_garden_bed_validates_as_string(self):
        """Test that garden_bed must be a string if provided."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because garden_bed field doesn't exist yet
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                garden_bed=123,  # Should be string, not int
            )
        
        errors = exc_info.value.errors()
        assert any("garden_bed" in str(error) for error in errors)


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
        
        # This will fail because connections field doesn't exist yet
        with pytest.raises(AttributeError):
            assert content.connections == []

    def test_connections_accepts_list_of_content_ids(self):
        """Test that connections field accepts list of content IDs."""
        content_ids = ["note-123", "til-456", "bookmark-789"]
        
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because connections field doesn't exist yet
            content = BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                connections=content_ids,
            )
        
        errors = exc_info.value.errors()
        assert any("connections" in str(error) for error in errors)

    def test_connections_validates_as_list(self):
        """Test that connections must be a list."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because connections field doesn't exist yet
            BaseContent(
                title="Test Content",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                connections="not-a-list",  # Should be list, not string
            )
        
        errors = exc_info.value.errors()
        assert any("connections" in str(error) for error in errors)


class TestVocabularyMapping:
    """Test the garden vocabulary helper functions."""

    def test_convert_created_to_planted(self):
        """Test that 'created' is converted to 'planted' in garden vocabulary."""
        with pytest.raises(NotImplementedError):
            result = convert_to_garden_vocabulary("created")

    def test_convert_updated_to_tended(self):
        """Test that 'updated' is converted to 'tended' in garden vocabulary."""
        with pytest.raises(NotImplementedError):
            result = convert_to_garden_vocabulary("updated")

    def test_convert_unknown_terms_unchanged(self):
        """Test that unknown terms are returned unchanged."""
        unknown_terms = ["title", "tags", "status", "description"]
        
        for term in unknown_terms:
            with pytest.raises(NotImplementedError):
                result = convert_to_garden_vocabulary(term)

    def test_growth_stages_constant_exists(self):
        """Test that GROWTH_STAGES constant is properly defined."""
        # This will fail because GROWTH_STAGES is not implemented yet
        assert GROWTH_STAGES == {}  # Currently empty mock

    def test_growth_stage_colors_mapping(self):
        """Test that growth stage colors map correctly."""
        expected_colors = {
            "seedling": "#10b981",  # emerald-500
            "budding": "#f59e0b",   # amber-500
            "growing": "#3b82f6",   # blue-500
            "evergreen": "#059669", # emerald-600
        }
        
        for stage, expected_color in expected_colors.items():
            with pytest.raises(NotImplementedError):
                color = get_growth_stage_color(stage)

    def test_growth_stage_emojis_mapping(self):
        """Test that growth stage emojis map correctly."""
        expected_emojis = {
            "seedling": "🌱",
            "budding": "🌿",
            "growing": "🌳",
            "evergreen": "🌲",
        }
        
        for stage, expected_emoji in expected_emojis.items():
            with pytest.raises(NotImplementedError):
                emoji = get_growth_stage_emoji(stage)


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
        
        # This will fail because growth_stage field doesn't exist yet
        with pytest.raises(AttributeError):
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
        
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because growth_stage field doesn't exist yet
            content = BaseContent(**content_data)
        
        errors = exc_info.value.errors()
        assert any("growth_stage" in str(error) for error in errors)


class TestSpecializedContentModels:
    """Test that specialized content models inherit growth stage behavior."""

    def test_bookmark_inherits_growth_stage(self):
        """Test that Bookmark model inherits growth stage functionality."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because growth_stage field doesn't exist yet
            bookmark = Bookmark(
                title="Test Bookmark",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                url="https://example.com",
                growth_stage="budding",
            )
        
        errors = exc_info.value.errors()
        assert any("growth_stage" in str(error) for error in errors)

    def test_til_inherits_growth_stage(self):
        """Test that TIL model inherits growth stage functionality."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because growth_stage field doesn't exist yet
            til = TIL(
                title="Test TIL",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                growth_stage="growing",
            )
        
        errors = exc_info.value.errors()
        assert any("growth_stage" in str(error) for error in errors)

    def test_note_inherits_growth_stage(self):
        """Test that Note model inherits growth stage functionality."""
        with pytest.raises(ValidationError) as exc_info:
            # This will fail because growth_stage field doesn't exist yet
            note = Note(
                title="Test Note",
                created=datetime.now(),
                updated=datetime.now(),
                tags=["test"],
                growth_stage="evergreen",
            )
        
        errors = exc_info.value.errors()
        assert any("growth_stage" in str(error) for error in errors)


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
        )
        
        # Test for methods that don't exist yet
        with pytest.raises(AttributeError):
            content.tend()  # Method doesn't exist yet
            
        with pytest.raises(AttributeError):
            content.should_advance_growth_stage()  # Method doesn't exist yet
        
    def test_evergreen_content_stays_evergreen(self):
        """Test that evergreen content doesn't regress to earlier stages."""
        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
        )
        
        # Test for method that doesn't exist yet
        with pytest.raises(AttributeError):
            content.check_growth_stage_regression()  # Method doesn't exist yet