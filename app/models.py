from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, validator
from enum import Enum


class GrowthStage(Enum):
    SEEDLING = "seedling"
    BUDDING = "budding"
    GROWING = "growing"
    EVERGREEN = "evergreen"


class BaseContent(BaseModel):
    # Required fields
    title: str
    created: datetime
    updated: datetime
    tags: List[str]

    # Optional fields with defaults
    status: str = "Evergreen"
    series: Optional[str] = None
    difficulty: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    related_content: Optional[List[str]] = None
    visibility: str = "public"
    
    # Growth stage fields
    growth_stage: str = "seedling"
    tended_count: int = Field(default=0, ge=0)  # Must be non-negative
    garden_bed: Optional[str] = None
    connections: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @validator('growth_stage')
    def validate_growth_stage(cls, v):
        valid_stages = {"seedling", "budding", "growing", "evergreen"}
        if v not in valid_stages:
            raise ValueError(f"growth_stage must be one of {valid_stages}")
        return v
    
    def tend(self):
        """Increment the tended count when content is updated."""
        self.tended_count += 1
    
    def should_advance_growth_stage(self):
        """Determine if content should advance to the next growth stage."""
        # Basic logic for growth stage advancement based on tended_count
        if self.growth_stage == "seedling" and self.tended_count >= 1:
            return "budding"
        elif self.growth_stage == "budding" and self.tended_count >= 3:
            return "growing"
        elif self.growth_stage == "growing" and self.tended_count >= 5:
            return "evergreen"
        return self.growth_stage
    
    def check_growth_stage_regression(self):
        """Prevent growth stage regression - evergreen stays evergreen."""
        if self.growth_stage == "evergreen":
            return "evergreen"
        return self.growth_stage


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
    difficulty: Optional[str] = None
    prerequisites: Optional[List[str]] = None


class Note(BaseContent):
    series: Optional[str] = None


class ContentMetadata(BaseModel):
    series: Optional[str] = None
    difficulty: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    related_content: Optional[List[str]] = None
    visibility: str = "public"