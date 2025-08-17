"""
Tests for GrowthStageRenderer service.

This test suite verifies the visual rendering functionality for growth stages
including symbol mapping, CSS class generation, and opacity values.
"""

import pytest
from app.models import GrowthStage
from app.services.growth_stage_renderer import GrowthStageRenderer


class TestGrowthStageRenderer:
    """Test the GrowthStageRenderer service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = GrowthStageRenderer()

    def test_render_stage_symbol_seedling(self):
        """Test that SEEDLING renders as bullet symbol."""
        symbol = self.renderer.render_stage_symbol(GrowthStage.SEEDLING)
        assert symbol == "•"

    def test_render_stage_symbol_budding(self):
        """Test that BUDDING renders as half circle symbol."""
        symbol = self.renderer.render_stage_symbol(GrowthStage.BUDDING)
        assert symbol == "◐"

    def test_render_stage_symbol_growing(self):
        """Test that GROWING renders as full circle symbol."""
        symbol = self.renderer.render_stage_symbol(GrowthStage.GROWING)
        assert symbol == "●"

    def test_render_stage_symbol_evergreen(self):
        """Test that EVERGREEN renders as square symbol."""
        symbol = self.renderer.render_stage_symbol(GrowthStage.EVERGREEN)
        assert symbol == "■"

    def test_render_stage_symbol_invalid_type(self):
        """Test that invalid stage type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.renderer.render_stage_symbol("invalid")
        assert "Invalid growth stage" in str(exc_info.value)
        assert "Must be a GrowthStage enum" in str(exc_info.value)

    def test_render_stage_symbol_none_value(self):
        """Test that None value raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.renderer.render_stage_symbol(None)
        assert "Invalid growth stage" in str(exc_info.value)

    def test_render_stage_css_class_seedling(self):
        """Test that SEEDLING generates correct CSS class."""
        css_class = self.renderer.render_stage_css_class(GrowthStage.SEEDLING)
        assert css_class == "growth-seedling"

    def test_render_stage_css_class_budding(self):
        """Test that BUDDING generates correct CSS class."""
        css_class = self.renderer.render_stage_css_class(GrowthStage.BUDDING)
        assert css_class == "growth-budding"

    def test_render_stage_css_class_growing(self):
        """Test that GROWING generates correct CSS class."""
        css_class = self.renderer.render_stage_css_class(GrowthStage.GROWING)
        assert css_class == "growth-growing"

    def test_render_stage_css_class_evergreen(self):
        """Test that EVERGREEN generates correct CSS class."""
        css_class = self.renderer.render_stage_css_class(GrowthStage.EVERGREEN)
        assert css_class == "growth-evergreen"

    def test_render_stage_css_class_invalid_type(self):
        """Test that invalid stage type raises ValueError for CSS class."""
        with pytest.raises(ValueError) as exc_info:
            self.renderer.render_stage_css_class("invalid")
        assert "Invalid growth stage" in str(exc_info.value)

    def test_render_stage_opacity_seedling(self):
        """Test that SEEDLING has opacity 0.6."""
        opacity = self.renderer.render_stage_opacity(GrowthStage.SEEDLING)
        assert opacity == 0.6

    def test_render_stage_opacity_budding(self):
        """Test that BUDDING has opacity 0.7."""
        opacity = self.renderer.render_stage_opacity(GrowthStage.BUDDING)
        assert opacity == 0.7

    def test_render_stage_opacity_growing(self):
        """Test that GROWING has opacity 0.8."""
        opacity = self.renderer.render_stage_opacity(GrowthStage.GROWING)
        assert opacity == 0.8

    def test_render_stage_opacity_evergreen(self):
        """Test that EVERGREEN has opacity 1.0."""
        opacity = self.renderer.render_stage_opacity(GrowthStage.EVERGREEN)
        assert opacity == 1.0

    def test_render_stage_opacity_invalid_type(self):
        """Test that invalid stage type raises ValueError for opacity."""
        with pytest.raises(ValueError) as exc_info:
            self.renderer.render_stage_opacity("invalid")
        assert "Invalid growth stage" in str(exc_info.value)

    def test_render_stage_opacity_values_in_range(self):
        """Test that all opacity values are between 0.0 and 1.0."""
        for stage in GrowthStage:
            opacity = self.renderer.render_stage_opacity(stage)
            assert 0.0 <= opacity <= 1.0

    def test_all_stage_symbols_defined(self):
        """Test that all growth stages have symbol mappings."""
        for stage in GrowthStage:
            symbol = self.renderer.render_stage_symbol(stage)
            assert symbol is not None
            assert isinstance(symbol, str)
            assert len(symbol) > 0

    def test_all_stage_css_classes_valid_format(self):
        """Test that all CSS classes follow the correct format."""
        for stage in GrowthStage:
            css_class = self.renderer.render_stage_css_class(stage)
            assert css_class.startswith("growth-")
            assert css_class == f"growth-{stage.value}"

    def test_symbols_are_unique(self):
        """Test that each growth stage has a unique symbol."""
        symbols = []
        for stage in GrowthStage:
            symbol = self.renderer.render_stage_symbol(stage)
            assert symbol not in symbols
            symbols.append(symbol)

    def test_opacity_progression_ascending(self):
        """Test that opacity values progress from low to high."""
        seedling_opacity = self.renderer.render_stage_opacity(GrowthStage.SEEDLING)
        budding_opacity = self.renderer.render_stage_opacity(GrowthStage.BUDDING)
        growing_opacity = self.renderer.render_stage_opacity(GrowthStage.GROWING)
        evergreen_opacity = self.renderer.render_stage_opacity(GrowthStage.EVERGREEN)

        assert seedling_opacity < budding_opacity
        assert budding_opacity < growing_opacity
        assert growing_opacity < evergreen_opacity

    def test_validate_stage_with_valid_enum(self):
        """Test that _validate_stage doesn't raise for valid enum."""
        # This should not raise any exception
        self.renderer._validate_stage(GrowthStage.SEEDLING)
        self.renderer._validate_stage(GrowthStage.BUDDING)
        self.renderer._validate_stage(GrowthStage.GROWING)
        self.renderer._validate_stage(GrowthStage.EVERGREEN)

    def test_stage_constants_are_class_attributes(self):
        """Test that symbol and opacity mappings are accessible as class attributes."""
        assert hasattr(GrowthStageRenderer, "STAGE_SYMBOLS")
        assert hasattr(GrowthStageRenderer, "STAGE_OPACITY")

        # Test that they contain the expected mappings
        assert len(GrowthStageRenderer.STAGE_SYMBOLS) == 4
        assert len(GrowthStageRenderer.STAGE_OPACITY) == 4

        # Test specific mappings
        assert GrowthStageRenderer.STAGE_SYMBOLS[GrowthStage.SEEDLING] == "•"
        assert GrowthStageRenderer.STAGE_OPACITY[GrowthStage.EVERGREEN] == 1.0


class TestGrowthStageRendererIntegration:
    """Integration tests for GrowthStageRenderer with other components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = GrowthStageRenderer()

    def test_renderer_works_with_basemodel_growth_stage(self):
        """Test that renderer works with growth stages from BaseContent model."""
        from app.models import BaseContent
        from datetime import datetime

        content = BaseContent(
            title="Test Content",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"],
            growth_stage=GrowthStage.GROWING,
        )

        # Should work seamlessly with content's growth stage
        symbol = self.renderer.render_stage_symbol(content.growth_stage)
        css_class = self.renderer.render_stage_css_class(content.growth_stage)
        opacity = self.renderer.render_stage_opacity(content.growth_stage)

        assert symbol == "●"
        assert css_class == "growth-growing"
        assert opacity == 0.8

    def test_renderer_handles_all_enum_values(self):
        """Test that renderer can handle all possible GrowthStage enum values."""
        for stage in GrowthStage:
            # All methods should work without raising exceptions
            symbol = self.renderer.render_stage_symbol(stage)
            css_class = self.renderer.render_stage_css_class(stage)
            opacity = self.renderer.render_stage_opacity(stage)

            # Basic validation
            assert isinstance(symbol, str)
            assert isinstance(css_class, str)
            assert isinstance(opacity, float)
            assert css_class.startswith("growth-")
