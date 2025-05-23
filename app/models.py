from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

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
    
    model_config = ConfigDict(extra="allow")

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