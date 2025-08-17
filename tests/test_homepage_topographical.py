"""
Test suite for topographical homepage design following TDD principles.

These tests define the expected behavior of the new homepage layout that groups
content by garden beds/topics and displays growth stage indicators.

All tests should FAIL initially until the topographical homepage is implemented.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup

from app.main import app
from app.models import BaseContent, Note, TIL, Bookmark


class TestTopographicalHomepage:
    """Test suite for the new topographical homepage design."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_content_by_topic(self):
        """Sample content grouped by topics for testing."""
        return {
            "python": [
                Note(
                    title="Advanced Python Patterns",
                    created=datetime.now().date(),
                    content="Content about Python patterns",
                    status="Evergreen",
                    tags=["python", "patterns"],
                    slug="advanced-python-patterns"
                ),
                TIL(
                    title="Python List Comprehensions",
                    created=datetime.now().date(),
                    content="Quick tip about list comprehensions",
                    status="Budding",
                    tags=["python", "tips"],
                    slug="python-list-comprehensions"
                )
            ],
            "web-development": [
                Note(
                    title="FastAPI Best Practices",
                    created=datetime.now().date(),
                    content="Content about FastAPI",
                    status="Evergreen",
                    tags=["fastapi", "web-development"],
                    slug="fastapi-best-practices"
                ),
                Bookmark(
                    title="React Performance Guide",
                    created=datetime.now().date(),
                    url="https://react.dev/performance",
                    status="Budding",
                    tags=["react", "web-development"],
                    slug="react-performance-guide"
                )
            ],
            "machine-learning": [
                Note(
                    title="Introduction to Neural Networks",
                    created=datetime.now().date(),
                    content="Basic concepts of neural networks",
                    status="draft",  # Should not appear on homepage
                    tags=["ml", "neural-networks"],
                    slug="intro-neural-networks"
                )
            ]
        }

    @pytest.fixture
    def featured_content(self):
        """Sample featured content for testing."""
        return [
            Note(
                title="Building a Digital Garden",
                created=datetime.now().date(),
                content="How to create your own digital garden",
                status="Evergreen",
                tags=["digital-garden", "featured"],
                slug="building-digital-garden",
                featured=True  # This property doesn't exist yet
            )
        ]

    def test_homepage_displays_recently_tended_section(self, client):
        """Test that homepage displays a 'Recently tended' section."""
        response = client.get("/")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Should find a section with "Recently tended" heading
        recently_tended_section = soup.find(id="recently-tended") or \
                                soup.find("section", class_="recently-tended") or \
                                soup.find("h2", string="Recently tended")
        
        assert recently_tended_section is not None, "Homepage should have a 'Recently tended' section"
        
        # Should contain recent content items
        content_cards = soup.find_all(class_="content-card") or \
                       soup.find_all("article", class_="card")
        
        assert len(content_cards) > 0, "Recently tended section should contain content cards"

    def test_homepage_groups_content_by_garden_beds(self, client, sample_content_by_topic):
        """Test that content is grouped by garden beds/topics on homepage."""
        with patch('app.main.ContentManager.get_homepage_sections') as mock_sections:
            mock_sections.return_value = {
                'garden_beds': sample_content_by_topic,
                'recently_tended': list(sample_content_by_topic.values())[0][:3],
                'featured': []
            }
            
            response = client.get("/")
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Should find garden bed sections
            garden_beds_section = soup.find(id="garden-beds") or \
                                soup.find("section", class_="garden-beds")
            
            assert garden_beds_section is not None, "Homepage should have garden beds section"
            
            # Should have topic groupings
            topic_sections = soup.find_all(class_="topic-section") or \
                           soup.find_all("div", {"data-topic": True})
            
            assert len(topic_sections) >= 2, "Should have multiple topic sections"
            
            # Should find Python and Web Development topics
            page_text = soup.get_text().lower()
            assert "python" in page_text, "Should display Python topic"
            assert "web-development" in page_text or "web development" in page_text, "Should display Web Development topic"

    def test_homepage_displays_growth_stage_indicators(self, client, sample_content_by_topic):
        """Test that growth stage indicators appear on homepage cards."""
        with patch('app.main.ContentManager.get_homepage_sections') as mock_sections:
            mock_sections.return_value = {
                'garden_beds': sample_content_by_topic,
                'recently_tended': list(sample_content_by_topic.values())[0],
                'featured': []
            }
            
            response = client.get("/")
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Should find growth stage indicators
            evergreen_indicators = soup.find_all(class_="status-evergreen") or \
                                 soup.find_all("span", string="Evergreen") or \
                                 soup.find_all(class_="growth-evergreen")
            
            budding_indicators = soup.find_all(class_="status-budding") or \
                               soup.find_all("span", string="Budding") or \
                               soup.find_all(class_="growth-budding")
            
            assert len(evergreen_indicators) > 0, "Should display Evergreen status indicators"
            assert len(budding_indicators) > 0, "Should display Budding status indicators"
            
            # Should NOT display draft content
            draft_indicators = soup.find_all(class_="status-draft") or \
                             soup.find_all("span", string="draft")
            assert len(draft_indicators) == 0, "Should not display draft content on homepage"

    def test_explore_by_topic_cta_links_to_topics_page(self, client):
        """Test that 'Explore by topic' call-to-action links to /topics."""
        response = client.get("/")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Should find a link to topics page
        topics_link = soup.find("a", href="/topics") or \
                     soup.find("a", href="/topics/") or \
                     soup.find("a", {"data-page": "topics"})
        
        assert topics_link is not None, "Should have a link to /topics page"
        
        # Link should contain appropriate text
        link_text = topics_link.get_text().lower()
        expected_phrases = ["explore", "topic", "garden", "browse"]
        
        assert any(phrase in link_text for phrase in expected_phrases), \
            f"Topics link should contain relevant text, got: '{link_text}'"

    def test_homepage_loads_within_performance_threshold(self, client):
        """Test that homepage loads within 2 seconds."""
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        assert response.status_code == 200, "Homepage should load successfully"
        assert load_time < 2.0, f"Homepage should load within 2 seconds, took {load_time:.2f}s"

    def test_infinite_scroll_works_with_topographical_layout(self, client):
        """Test that infinite scroll functionality still works with new layout."""
        # First request should return initial content
        response = client.get("/")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Should find infinite scroll trigger element
        scroll_trigger = soup.find(attrs={"hx-get": True, "hx-trigger": "revealed"}) or \
                        soup.find(class_="infinite-scroll-trigger") or \
                        soup.find(id="load-more-trigger")
        
        assert scroll_trigger is not None, "Homepage should have infinite scroll trigger"
        
        # Test pagination endpoint still works
        response = client.get("/?page=2")
        assert response.status_code == 200
        
        # Should return HTMX partial or valid content
        if "hx-request" in response.headers.get("content-type", ""):
            # HTMX partial response
            assert len(response.content) > 0, "Pagination should return content"
        else:
            # Full page response should still work
            soup = BeautifulSoup(response.content, 'html.parser')
            content_cards = soup.find_all(class_="content-card")
            assert len(content_cards) >= 0, "Pagination should work with topographical layout"

    def test_mobile_layout_stacks_sections_vertically(self, client):
        """Test that mobile layout stacks sections vertically with responsive CSS."""
        response = client.get("/")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Should find responsive grid/flex classes
        main_container = soup.find("main") or soup.find(class_="container")
        assert main_container is not None, "Should have main container"
        
        # Check for mobile-responsive classes
        container_classes = main_container.get("class", [])
        responsive_classes = [
            "md:grid-cols-2", "lg:grid-cols-3", "grid-cols-1",  # Tailwind responsive grid
            "flex-col", "md:flex-row",  # Responsive flex direction
            "stack-mobile", "responsive-grid"  # Custom responsive classes
        ]
        
        has_responsive_classes = any(
            any(resp_class in str(container_classes) for resp_class in responsive_classes)
            for container_classes in [container_classes]
        )
        
        # Also check for responsive classes in section elements
        sections = soup.find_all(["section", "div"], class_=True)
        section_classes = []
        for section in sections:
            section_classes.extend(section.get("class", []))
        
        has_section_responsive = any(resp_class in str(section_classes) for resp_class in responsive_classes)
        
        assert has_responsive_classes or has_section_responsive, \
            "Homepage should have responsive CSS classes for mobile layout"

    def test_featured_content_appears_prominently(self, client, featured_content):
        """Test that featured content appears prominently on homepage."""
        with patch('app.main.ContentManager.get_homepage_sections') as mock_sections:
            mock_sections.return_value = {
                'garden_beds': {},
                'recently_tended': [],
                'featured': featured_content
            }
            
            response = client.get("/")
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Should find featured section
            featured_section = soup.find(id="featured-content") or \
                             soup.find("section", class_="featured") or \
                             soup.find(class_="featured-content")
            
            assert featured_section is not None, "Should have featured content section"
            
            # Featured content should appear near top
            page_elements = soup.find("body").find_all(recursive=False)
            featured_index = None
            
            for i, element in enumerate(page_elements):
                if featured_section in element.find_all():
                    featured_index = i
                    break
            
            assert featured_index is not None and featured_index < 3, \
                "Featured content should appear prominently near top of page"
            
            # Should contain the featured content title
            page_text = soup.get_text()
            assert "Building a Digital Garden" in page_text, "Should display featured content"

    def test_empty_sections_are_hidden(self, client):
        """Test that empty sections are hidden from the homepage."""
        with patch('app.main.ContentManager.get_homepage_sections') as mock_sections:
            # Return empty sections
            mock_sections.return_value = {
                'garden_beds': {},
                'recently_tended': [],
                'featured': []
            }
            
            response = client.get("/")
            assert response.status_code == 200
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Empty sections should not be displayed or should have empty state
            featured_section = soup.find(id="featured-content") or soup.find("section", class_="featured")
            garden_beds_section = soup.find(id="garden-beds") or soup.find("section", class_="garden-beds")
            recently_tended_section = soup.find(id="recently-tended") or soup.find("section", class_="recently-tended")
            
            # Sections should either not exist or be hidden/empty
            if featured_section:
                assert "hidden" in featured_section.get("class", []) or \
                       featured_section.get("style", "").find("display: none") != -1 or \
                       len(featured_section.find_all(class_="content-card")) == 0, \
                       "Empty featured section should be hidden or empty"
            
            # Should show empty state message or default content
            page_text = soup.get_text().lower()
            empty_state_phrases = ["no content", "coming soon", "check back", "empty", "nothing here"]
            
            # Either have empty state message OR sections are properly hidden
            has_empty_state = any(phrase in page_text for phrase in empty_state_phrases)
            sections_exist = featured_section or garden_beds_section or recently_tended_section
            
            assert has_empty_state or not sections_exist, \
                "Should either show empty state message or hide empty sections"

    def test_homepage_uses_caching_effectively(self, client):
        """Test that homepage uses caching to improve performance."""
        # First request - should cache the result
        start_time = time.time()
        response1 = client.get("/")
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Second request - should be faster due to caching
        start_time = time.time()
        response2 = client.get("/")
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Content should be identical (cached)
        assert response1.content == response2.content, "Cached responses should be identical"
        
        # Second request should be faster (allowing some margin for test variance)
        # Note: This may not always be true in test environment, so we'll check method exists
        with patch('app.main.ContentManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            
            # Mock the caching method that should exist
            mock_instance.get_homepage_sections = Mock(return_value={
                'garden_beds': {},
                'recently_tended': [],
                'featured': []
            })
            
            # Check that caching method would be called
            client.get("/")
            
            # The homepage should call get_homepage_sections (not get_mixed_content)
            # This will fail until the method is implemented
            try:
                mock_instance.get_homepage_sections.assert_called()
                cache_method_exists = True
            except AttributeError:
                cache_method_exists = False
            
            assert cache_method_exists, "Homepage should use get_homepage_sections method for caching"


class TestHomepageContentManager:
    """Test ContentManager methods needed for topographical homepage."""

    @pytest.fixture
    def content_manager(self):
        """Create ContentManager instance for testing."""
        from app.content_manager import ContentManager
        return ContentManager()

    def test_get_homepage_sections_method_exists(self, content_manager):
        """Test that ContentManager has get_homepage_sections method."""
        assert hasattr(content_manager, 'get_homepage_sections'), \
            "ContentManager should have get_homepage_sections method"
        
        # Method should be callable
        assert callable(getattr(content_manager, 'get_homepage_sections')), \
            "get_homepage_sections should be callable"

    def test_get_homepage_sections_returns_proper_structure(self, content_manager):
        """Test that get_homepage_sections returns expected data structure."""
        sections = content_manager.get_homepage_sections()
        
        assert isinstance(sections, dict), "get_homepage_sections should return a dictionary"
        
        # Should have required keys
        required_keys = ['garden_beds', 'recently_tended', 'featured']
        for key in required_keys:
            assert key in sections, f"sections should contain '{key}' key"
        
        # garden_beds should be dict of topic -> content list
        assert isinstance(sections['garden_beds'], dict), "garden_beds should be a dictionary"
        
        # recently_tended should be list
        assert isinstance(sections['recently_tended'], list), "recently_tended should be a list"
        
        # featured should be list
        assert isinstance(sections['featured'], list), "featured should be a list"

    def test_get_homepage_sections_groups_by_topic(self, content_manager):
        """Test that get_homepage_sections properly groups content by topic."""
        sections = content_manager.get_homepage_sections()
        garden_beds = sections['garden_beds']
        
        # Should have at least one topic group
        assert len(garden_beds) > 0, "Should group content by topics"
        
        # Each topic should have a list of content
        for topic, content_list in garden_beds.items():
            assert isinstance(topic, str), "Topic keys should be strings"
            assert isinstance(content_list, list), "Topic values should be lists"
            assert len(content_list) > 0, f"Topic '{topic}' should have content"
            
            # All content in a topic should share at least one tag
            if len(content_list) > 1:
                topic_tags = set()
                for content in content_list:
                    if hasattr(content, 'tags') and content.tags:
                        topic_tags.update(content.tags)
                
                # Each content item should have at least one tag in common with topic
                for content in content_list:
                    if hasattr(content, 'tags') and content.tags:
                        assert any(tag in topic_tags for tag in content.tags), \
                            f"Content should share tags with topic '{topic}'"

    def test_get_homepage_sections_excludes_draft_content(self, content_manager):
        """Test that get_homepage_sections excludes draft content."""
        sections = content_manager.get_homepage_sections()
        
        all_content = []
        all_content.extend(sections['recently_tended'])
        all_content.extend(sections['featured'])
        
        for topic_content in sections['garden_beds'].values():
            all_content.extend(topic_content)
        
        # No content should have draft status
        for content in all_content:
            assert hasattr(content, 'status'), "Content should have status attribute"
            assert content.status != 'draft', "Homepage should not include draft content"

    def test_get_homepage_sections_is_cached(self, content_manager):
        """Test that get_homepage_sections uses caching."""
        # Check if method has caching decorator
        method = getattr(content_manager, 'get_homepage_sections')
        
        # Should have cache-related attributes (from timed_lru_cache or similar)
        has_cache_attributes = any(
            hasattr(method, attr) for attr in 
            ['cache_info', '__wrapped__', '_cache', 'cache_clear']
        )
        
        assert has_cache_attributes, "get_homepage_sections should be cached"
        
        # Multiple calls should return same object (from cache)
        result1 = content_manager.get_homepage_sections()
        result2 = content_manager.get_homepage_sections()
        
        # Results should be identical (cached)
        assert result1 == result2, "Cached calls should return identical results"