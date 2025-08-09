import pytest
from datetime import datetime
from app.main import ContentManager


@pytest.mark.asyncio
async def test_get_mixed_content_pagination():
    # Test basic pagination
    result = await ContentManager.get_mixed_content(page=1, per_page=5)
    assert len(result["content"]) <= 5
    assert "next_page" in result
    assert "total" in result
    assert "current_page" in result
    assert "total_pages" in result

    # Test out of range page
    empty_result = await ContentManager.get_mixed_content(page=9999, per_page=5)
    assert len(empty_result["content"]) == 0
    assert empty_result["next_page"] is None

    # Test invalid page numbers
    with pytest.raises(ValueError):
        await ContentManager.get_mixed_content(page=0)
    with pytest.raises(ValueError):
        await ContentManager.get_mixed_content(page=-1)
    with pytest.raises(ValueError):
        await ContentManager.get_mixed_content(per_page=0)


@pytest.mark.asyncio
async def test_get_mixed_content_structure():
    result = await ContentManager.get_mixed_content(page=1, per_page=10)

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


@pytest.mark.asyncio
async def test_get_mixed_content_sorting():
    result = await ContentManager.get_mixed_content(page=1, per_page=20)

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
        assert all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1))


@pytest.mark.asyncio
async def test_get_mixed_content_error_handling():
    # Test error collection
    result = await ContentManager.get_mixed_content(page=1)
    assert "errors" in result

    # Even with some errors, should still return content
    if result["content"]:
        assert isinstance(result["content"], list)
        assert all(isinstance(item, dict) for item in result["content"])


@pytest.mark.asyncio
async def test_get_mixed_content_type_indicators():
    result = await ContentManager.get_mixed_content(page=1)

    if result["content"]:
        for item in result["content"]:
            assert "type_indicator" in item
            assert item["type_indicator"] in ["Note", "How To", "Bookmark", "TIL"]
            assert item["content_type"] in ["notes", "how_to", "bookmarks", "til"]
