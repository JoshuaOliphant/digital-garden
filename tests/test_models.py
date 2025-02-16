import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import BaseContent, Bookmark, TIL, Note, ContentMetadata
from app.main import ContentManager

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

def test_get_mixed_content_pagination():
    # Test basic pagination
    result = ContentManager.get_mixed_content(page=1, per_page=5)
    assert len(result["content"]) <= 5
    assert "next_page" in result
    assert "total" in result
    assert "current_page" in result
    assert "total_pages" in result

    # Test out of range page
    empty_result = ContentManager.get_mixed_content(page=9999, per_page=5)
    assert len(empty_result["content"]) == 0
    assert empty_result["next_page"] is None

    # Test invalid page numbers
    with pytest.raises(ValueError):
        ContentManager.get_mixed_content(page=0)
    with pytest.raises(ValueError):
        ContentManager.get_mixed_content(page=-1)
    with pytest.raises(ValueError):
        ContentManager.get_mixed_content(per_page=0)

def test_get_mixed_content_structure():
    result = ContentManager.get_mixed_content(page=1, per_page=10)
    
    # Test overall structure
    assert "content" in result
    assert "total" in result
    assert isinstance(result["content"], list)
    
    # Test content item structure
    if result["content"]:
        item = result["content"][0]
        assert "name" in item
        assert "title" in item
        assert "content_type" in item
        assert "type_indicator" in item
        assert "url" in item
        assert "excerpt" in item
        assert "metadata" in item

def test_get_mixed_content_sorting():
    result = ContentManager.get_mixed_content(page=1, per_page=20)
    
    if len(result["content"]) > 1:
        # Convert dates to datetime objects for comparison
        dates = []
        for item in result["content"]:
            date = item.get("created")
            if not date:
                date = item.get("metadata", {}).get("created")
            if isinstance(date, str):
                date = datetime.strptime(date, "%Y-%m-%d")
            dates.append(date)
        
        # Verify dates are in descending order
        assert all(dates[i] >= dates[i+1] for i in range(len(dates)-1))

def test_get_mixed_content_error_handling():
    # Test error collection
    result = ContentManager.get_mixed_content(page=1)
    assert "errors" in result
    
    # Even with some errors, should still return content
    if result["content"]:
        assert isinstance(result["content"], list)
        assert all(isinstance(item, dict) for item in result["content"])

def test_get_mixed_content_type_indicators():
    result = ContentManager.get_mixed_content(page=1)
    
    if result["content"]:
        for item in result["content"]:
            assert "type_indicator" in item
            assert item["type_indicator"] in ["Note", "How To", "Bookmark", "TIL"]
            assert item["content_type"] in ["notes", "how_to", "bookmarks", "til"] 