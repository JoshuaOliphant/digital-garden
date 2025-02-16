import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import BaseContent, Bookmark, TIL, Note, ContentMetadata

def test_base_content_required_fields():
    # Test that required fields must be provided
    with pytest.raises(ValidationError) as exc_info:
        BaseContent()
    
    errors = exc_info.value.errors()
    assert len(errors) == 4  # title, created, updated, tags are required
    assert any(err["loc"] == ("title",) for err in errors)
    assert any(err["loc"] == ("created",) for err in errors)
    assert any(err["loc"] == ("updated",) for err in errors)
    assert any(err["loc"] == ("tags",) for err in errors)

def test_base_content_valid():
    # Test valid base content
    content = BaseContent(
        title="Test Title",
        created=datetime.now(),
        updated=datetime.now(),
        tags=["test", "python"]
    )
    assert content.title == "Test Title"
    assert isinstance(content.created, datetime)
    assert isinstance(content.updated, datetime)
    assert content.tags == ["test", "python"]
    assert content.status == "Evergreen"  # default value
    assert content.visibility == "public"  # default value

def test_bookmark_model():
    # Test that bookmark requires URL
    with pytest.raises(ValidationError) as exc_info:
        Bookmark(
            title="Test Bookmark",
            created=datetime.now(),
            updated=datetime.now(),
            tags=["test"]
        )
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("url",) for err in errors)

    # Test valid bookmark
    bookmark = Bookmark(
        title="Test Bookmark",
        created=datetime.now(),
        updated=datetime.now(),
        tags=["test"],
        url="https://example.com"
    )
    assert bookmark.url == "https://example.com"

def test_til_model():
    # Test TIL with difficulty
    til = TIL(
        title="Test TIL",
        created=datetime.now(),
        updated=datetime.now(),
        tags=["test"],
        difficulty="intermediate"
    )
    assert til.difficulty == "intermediate"

    # Test TIL with prerequisites
    til = TIL(
        title="Test TIL",
        created=datetime.now(),
        updated=datetime.now(),
        tags=["test"],
        prerequisites=["python", "git"]
    )
    assert til.prerequisites == ["python", "git"]

def test_note_model():
    # Test Note with series
    note = Note(
        title="Test Note",
        created=datetime.now(),
        updated=datetime.now(),
        tags=["test"],
        series="Python Tips"
    )
    assert note.series == "Python Tips"

def test_content_metadata():
    # Test metadata model
    metadata = ContentMetadata(
        series="Test Series",
        difficulty="advanced",
        prerequisites=["python", "fastapi"],
        related_content=["post1", "post2"]
    )
    assert metadata.series == "Test Series"
    assert metadata.difficulty == "advanced"
    assert metadata.prerequisites == ["python", "fastapi"]
    assert metadata.related_content == ["post1", "post2"]
    assert metadata.visibility == "public"  # default value 