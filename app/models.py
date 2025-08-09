# ABOUTME: Pydantic models for content types in the digital garden
# ABOUTME: Defines content models with growth stages and garden vocabulary

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Growth stage enum for content lifecycle
class GrowthStage(str, Enum):
    SEEDLING = "seedling"
    BUDDING = "budding"
    GROWING = "growing"
    EVERGREEN = "evergreen"


class BaseContent(BaseModel):
    title: str
    created: datetime
    updated: datetime
    tags: List[str]

    # Existing optional fields
    status: str = "Evergreen"
    series: Optional[str] = None
    difficulty: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    related_content: Optional[List[str]] = None
    visibility: str = "public"

    # New growth stage fields
    growth_stage: GrowthStage = GrowthStage.SEEDLING
    tended_count: int = Field(default=0, ge=0)  # Must be non-negative
    garden_bed: Optional[str] = None
    connections: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    def tend(self):
        """Increment the tended count when content is updated."""
        self.tended_count += 1

    def should_advance_growth_stage(self) -> bool:
        """Determine if content should advance to the next growth stage."""
        # Evergreen content doesn't advance
        if self.growth_stage == GrowthStage.EVERGREEN:
            return False

        # Logic for advancement based on tended_count
        if self.growth_stage == GrowthStage.SEEDLING and self.tended_count >= 1:
            return True
        elif self.growth_stage == GrowthStage.BUDDING and self.tended_count >= 3:
            return True
        elif self.growth_stage == GrowthStage.GROWING and self.tended_count >= 5:
            return True
        return False

    def check_growth_stage_regression(self, new_stage: str) -> bool:
        """Check if a new growth stage would be a regression."""
        stage_order = {
            GrowthStage.SEEDLING: 0,
            GrowthStage.BUDDING: 1,
            GrowthStage.GROWING: 2,
            GrowthStage.EVERGREEN: 3,
        }

        # Convert string to enum if needed
        if isinstance(new_stage, str):
            try:
                new_stage = GrowthStage(new_stage)
            except ValueError:
                return False

        current_order = stage_order.get(self.growth_stage, 0)
        new_order = stage_order.get(new_stage, 0)

        # Allow same stage or progression, but not regression
        return new_order >= current_order


class Bookmark(BaseContent):
    url: str
    description: Optional[str] = None
    via_url: Optional[str] = None
    via_title: Optional[str] = None
    commentary: Optional[str] = None
    screenshot_path: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None


class TIL(BaseContent):
    pass  # Inherits all fields from BaseContent


class Note(BaseContent):
    pass  # Inherits all fields from BaseContent


class ContentMetadata(BaseModel):
    series: Optional[str] = None
    difficulty: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    related_content: Optional[List[str]] = None
