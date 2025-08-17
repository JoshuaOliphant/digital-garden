"""
GrowthStageRenderer service for rendering growth stage visual elements.

This service provides methods to render growth stages as visual symbols,
CSS classes, and opacity values for the digital garden interface.
"""

from typing import Dict
from app.models import GrowthStage


class GrowthStageRenderer:
    """Service for rendering growth stage visual elements.

    Provides visual rendering for growth stages with symbols, CSS classes,
    and opacity values to create visual hierarchy in the digital garden.
    """

    # Symbol mappings for each growth stage (Unicode visual metaphors)
    STAGE_SYMBOLS: Dict[GrowthStage, str] = {
        GrowthStage.SEEDLING: "•",  # Small dot for new content
        GrowthStage.BUDDING: "◐",  # Half circle for developing content
        GrowthStage.GROWING: "●",  # Full circle for maturing content
        GrowthStage.EVERGREEN: "■",  # Square for stable content
    }

    # Opacity mappings for visual hierarchy (progression: 0.6 → 1.0)
    STAGE_OPACITY: Dict[GrowthStage, float] = {
        GrowthStage.SEEDLING: 0.6,  # Lower opacity for early content
        GrowthStage.BUDDING: 0.7,  # Medium-low opacity
        GrowthStage.GROWING: 0.8,  # Medium-high opacity
        GrowthStage.EVERGREEN: 1.0,  # Full opacity for mature content
    }

    def render_stage_symbol(self, stage: GrowthStage) -> str:
        """Return visual symbol for growth stage.

        Args:
            stage: The GrowthStage enum value

        Returns:
            Unicode symbol representing the growth stage

        Raises:
            ValueError: If stage is not a valid GrowthStage
        """
        self._validate_stage(stage)
        return self.STAGE_SYMBOLS[stage]

    def render_stage_css_class(self, stage: GrowthStage) -> str:
        """Generate CSS class name for growth stage.

        Args:
            stage: The GrowthStage enum value

        Returns:
            CSS class name in format "growth-{stage_name}"

        Raises:
            ValueError: If stage is not a valid GrowthStage
        """
        self._validate_stage(stage)
        return f"growth-{stage.value}"

    def render_stage_opacity(self, stage: GrowthStage) -> float:
        """Get opacity value for growth stage.

        Args:
            stage: The GrowthStage enum value

        Returns:
            Float opacity value between 0.0 and 1.0

        Raises:
            ValueError: If stage is not a valid GrowthStage
        """
        self._validate_stage(stage)
        return self.STAGE_OPACITY[stage]

    def _validate_stage(self, stage: GrowthStage) -> None:
        """Validate that stage is a valid GrowthStage enum.

        Args:
            stage: The value to validate

        Raises:
            ValueError: If stage is not a valid GrowthStage enum
        """
        if not isinstance(stage, GrowthStage):
            raise ValueError(
                f"Invalid growth stage: {stage}. Must be a GrowthStage enum."
            )

        if stage not in self.STAGE_SYMBOLS:
            raise ValueError(f"Unknown growth stage: {stage}")
