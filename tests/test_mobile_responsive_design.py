import pytest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
import re
from pathlib import Path
from app.main import app

client = TestClient(app)


class TestMobileNavigation:
    """Test mobile navigation functionality and elements."""

    def test_viewport_meta_tag_exists(self):
        """Test that viewport meta tag exists with correct mobile settings."""
        response = client.get("/")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        
        assert viewport_meta is not None, "Viewport meta tag must exist for mobile responsiveness"
        
        content = viewport_meta.get('content', '')
        assert 'width=device-width' in content, "Viewport must set width=device-width"
        assert 'initial-scale=1.0' in content, "Viewport must set initial-scale=1.0"

    def test_navigation_has_mobile_menu_toggle(self):
        """Test that navigation includes a mobile menu toggle button."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for mobile menu toggle button with appropriate classes or attributes
        mobile_toggle = soup.find('button', class_=re.compile(r'mobile-menu-toggle|menu-toggle'))
        
        if not mobile_toggle:
            # Also check for hamburger icon or menu button
            mobile_toggle = soup.find(['button', 'div'], attrs={
                'aria-label': re.compile(r'menu|navigation', re.I)
            })
        
        if not mobile_toggle:
            # Check for common mobile menu patterns
            mobile_toggle = soup.find(attrs={
                'data-toggle': 'mobile-menu'
            }) or soup.find(class_=re.compile(r'hamburger|menu-btn'))
        
        assert mobile_toggle is not None, (
            "Mobile navigation must include a menu toggle button "
            "with class 'mobile-menu-toggle' or similar mobile navigation identifier"
        )

    def test_navigation_menu_hidden_on_mobile(self):
        """Test that main navigation menu is hidden by default on mobile viewports."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main navigation list/menu
        nav_menu = soup.find('ul', class_=re.compile(r'flex space-x-6|nav-menu'))
        
        if not nav_menu:
            nav_menu = soup.select('nav ul')[0] if soup.select('nav ul') else None
        
        assert nav_menu is not None, "Navigation menu must exist"
        
        # Check if it has mobile-specific hiding classes
        classes = nav_menu.get('class', [])
        class_string = ' '.join(classes)
        
        # Should have mobile hiding classes like 'hidden md:flex' or 'md:block hidden'
        has_mobile_hiding = any([
            'hidden' in class_string and ('md:' in class_string or 'lg:' in class_string),
            'mobile-hidden' in class_string,
            'nav-hidden' in class_string
        ])
        
        assert has_mobile_hiding, (
            "Navigation menu must be hidden on mobile with classes like 'hidden md:flex' "
            "to implement responsive mobile menu behavior"
        )

    def test_mobile_menu_toggle_elements(self):
        """Test that mobile menu toggle has proper accessibility and visual elements."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find any mobile menu related elements
        toggle_elements = soup.find_all(['button', 'div'], class_=re.compile(r'mobile|menu|toggle'))
        
        if not toggle_elements:
            toggle_elements = soup.find_all(attrs={'aria-label': re.compile(r'menu', re.I)})
        
        # Should have at least one mobile menu related element
        assert len(toggle_elements) > 0, (
            "Must have mobile menu toggle elements with appropriate classes "
            "(mobile-menu-toggle, hamburger, menu-btn) or aria-label containing 'menu'"
        )
        
        # If a button exists, it should have proper accessibility
        buttons = [el for el in toggle_elements if el.name == 'button']
        if buttons:
            button = buttons[0]
            has_aria_label = button.get('aria-label') is not None
            has_meaningful_class = any(cls in button.get('class', []) for cls in 
                                     ['mobile-menu-toggle', 'menu-toggle', 'hamburger'])
            
            assert has_aria_label or has_meaningful_class, (
                "Mobile menu toggle button must have aria-label or descriptive class names "
                "for accessibility"
            )


class TestTouchTargets:
    """Test that interactive elements meet 44px minimum touch target requirements."""

    def test_interactive_elements_meet_44px_minimum(self):
        """Test that all interactive elements have minimum 44px touch targets."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all interactive elements (buttons, links)
        interactive_elements = soup.find_all(['a', 'button', 'input[type="submit"]', 'input[type="button"]'])
        
        # Check CSS file for touch target classes
        css_file_path = Path("app/static/css/main.css")
        css_content = ""
        if css_file_path.exists():
            css_content = css_file_path.read_text()
        
        # Look for touch target related CSS classes
        touch_target_classes = [
            'touch-target',
            'touch-44',
            'min-touch',
            'mobile-touch'
        ]
        
        has_touch_target_css = any(cls in css_content for cls in touch_target_classes)
        
        # Check if interactive elements have touch-friendly classes
        elements_with_touch_classes = []
        for element in interactive_elements[:5]:  # Check first 5 elements
            classes = element.get('class', [])
            class_string = ' '.join(classes) if isinstance(classes, list) else classes
            
            has_touch_class = any(touch_cls in class_string for touch_cls in touch_target_classes)
            if has_touch_class:
                elements_with_touch_classes.append(element)
        
        assert has_touch_target_css or len(elements_with_touch_classes) > 0, (
            "Interactive elements must have CSS classes for 44px minimum touch targets. "
            "Expected classes like 'touch-target', 'touch-44', 'min-touch', or 'mobile-touch' "
            "in CSS or applied to elements"
        )

    def test_mobile_touch_target_classes_exist(self):
        """Test that CSS includes mobile touch target utility classes."""
        css_file_path = Path("app/static/css/main.css")
        assert css_file_path.exists(), "CSS file must exist"
        
        css_content = css_file_path.read_text()
        
        # Look for touch target related CSS rules
        touch_target_patterns = [
            r'\.touch-target.*?{[^}]*min-(height|width):\s*44px',
            r'\.touch-44.*?{[^}]*44px',
            r'\.min-touch.*?{[^}]*44px',
            r'@media.*mobile.*touch.*44px',
            r'button.*{[^}]*min-height:\s*44px',
            r'\.mobile-touch.*44px'
        ]
        
        has_touch_target_rules = any(
            re.search(pattern, css_content, re.DOTALL | re.IGNORECASE) 
            for pattern in touch_target_patterns
        )
        
        assert has_touch_target_rules, (
            "CSS must include touch target rules ensuring 44px minimum height/width "
            "for mobile accessibility. Expected patterns like '.touch-target { min-height: 44px; }' "
            "or similar mobile touch optimization rules"
        )

    def test_navigation_links_have_proper_padding(self):
        """Test that navigation links have adequate padding for thumb-friendly interaction."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find navigation links
        nav_links = soup.select('nav a')
        assert len(nav_links) > 0, "Navigation must contain links"
        
        css_file_path = Path("app/static/css/main.css")
        if css_file_path.exists():
            css_content = css_file_path.read_text()
            
            # Check for mobile-specific navigation padding
            mobile_nav_patterns = [
                r'@media.*max-width.*nav.*a.*{[^}]*padding',
                r'@media.*mobile.*nav.*{[^}]*padding',
                r'\.nav-mobile.*{[^}]*padding',
                r'nav.*a.*{[^}]*padding.*[2-9]rem',  # Generous padding
                r'\.mobile.*nav.*padding'
            ]
            
            has_mobile_nav_padding = any(
                re.search(pattern, css_content, re.DOTALL | re.IGNORECASE)
                for pattern in mobile_nav_patterns
            )
            
            # Also check if nav links have touch-friendly classes
            nav_links_with_padding = [
                link for link in nav_links 
                if any(cls in link.get('class', []) for cls in ['py-2', 'py-3', 'p-3', 'touch-target'])
            ]
            
            assert has_mobile_nav_padding or len(nav_links_with_padding) > 0, (
                "Navigation links must have adequate padding for mobile touch targets. "
                "Expected mobile-specific CSS rules or padding classes on nav links"
            )


class TestHorizontalScrollPrevention:
    """Test prevention of horizontal scrolling on mobile devices."""

    def test_body_prevents_horizontal_scroll(self):
        """Test that body element has CSS rules to prevent horizontal overflow."""
        css_file_path = Path("app/static/css/main.css")
        assert css_file_path.exists(), "CSS file must exist"
        
        css_content = css_file_path.read_text()
        
        # Look for horizontal scroll prevention rules
        overflow_patterns = [
            r'body.*{[^}]*overflow-x:\s*hidden',
            r'html.*{[^}]*overflow-x:\s*hidden',
            r'\*.*{[^}]*overflow-x:\s*hidden',
            r'\.overflow-x-hidden',
            r'@media.*mobile.*overflow-x:\s*hidden'
        ]
        
        has_overflow_prevention = any(
            re.search(pattern, css_content, re.DOTALL | re.IGNORECASE)
            for pattern in overflow_patterns
        )
        
        assert has_overflow_prevention, (
            "CSS must include overflow-x: hidden rules to prevent horizontal scrolling. "
            "Expected rules like 'body { overflow-x: hidden; }' or similar overflow prevention"
        )

    def test_containers_respect_viewport_width(self):
        """Test that container elements don't exceed viewport width."""
        css_file_path = Path("app/static/css/main.css")
        css_content = css_file_path.read_text()
        
        # Look for max-width constraints and responsive container rules
        container_patterns = [
            r'\.container.*{[^}]*max-width',
            r'@media.*max-width.*container',
            r'\.w-full.*max-width',
            r'width:\s*100%.*max-width',
            r'\.max-w-',
            r'box-sizing:\s*border-box'
        ]
        
        has_container_constraints = any(
            re.search(pattern, css_content, re.DOTALL | re.IGNORECASE)
            for pattern in container_patterns
        )
        
        # Also check HTML structure for responsive containers
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        containers = soup.find_all(class_=re.compile(r'container|max-w|w-full'))
        has_container_elements = len(containers) > 0
        
        assert has_container_constraints and has_container_elements, (
            "Containers must have max-width constraints and responsive sizing. "
            "Expected CSS rules for container max-width and HTML elements with "
            "container/max-width classes"
        )

    def test_code_blocks_handle_overflow(self):
        """Test that code blocks don't cause horizontal scrolling."""
        # Test with content that might have code blocks
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        css_file_path = Path("app/static/css/main.css")
        css_content = css_file_path.read_text()
        
        # Look for code block overflow handling
        code_overflow_patterns = [
            r'code.*{[^}]*overflow',
            r'pre.*{[^}]*overflow',
            r'\.code.*{[^}]*overflow',
            r'\.highlight.*{[^}]*overflow',
            r'@media.*code.*overflow',
            r'word-wrap:\s*break-word',
            r'overflow-wrap:\s*break-word',
            r'white-space:\s*pre-wrap'
        ]
        
        has_code_overflow_handling = any(
            re.search(pattern, css_content, re.DOTALL | re.IGNORECASE)
            for pattern in code_overflow_patterns
        )
        
        assert has_code_overflow_handling, (
            "Code blocks must handle overflow to prevent horizontal scrolling. "
            "Expected CSS rules for pre/code elements with overflow handling, "
            "word-wrap, or white-space rules"
        )

    def test_mobile_viewport_constraints(self):
        """Test mobile-specific viewport and width constraints."""
        css_file_path = Path("app/static/css/main.css")
        css_content = css_file_path.read_text()
        
        # Look for mobile-specific width constraints
        mobile_width_patterns = [
            r'@media.*max-width:\s*768px.*{[^}]*width',
            r'@media.*max-width:\s*640px.*{[^}]*width',
            r'@media.*mobile.*width.*100%',
            r'\.mobile.*{[^}]*width.*100%',
            r'@media.*max-width.*overflow'
        ]
        
        has_mobile_constraints = any(
            re.search(pattern, css_content, re.DOTALL | re.IGNORECASE)
            for pattern in mobile_width_patterns
        )
        
        assert has_mobile_constraints, (
            "CSS must include mobile-specific width and overflow constraints. "
            "Expected @media queries for mobile breakpoints with width/overflow rules"
        )


class TestMobileResponsiveIntegration:
    """Integration tests for mobile responsive behavior."""

    @pytest.mark.parametrize("viewport_width", [320, 375, 414, 768])
    def test_responsive_breakpoints(self, viewport_width):
        """Test that responsive design handles various mobile viewport widths."""
        # This test validates that CSS has appropriate breakpoints
        css_file_path = Path("app/static/css/main.css")
        css_content = css_file_path.read_text()
        
        # Check for responsive breakpoints around the test viewport width
        breakpoint_patterns = [
            rf'@media.*max-width:\s*{viewport_width}px',
            rf'@media.*min-width:\s*{viewport_width}px',
            r'@media.*max-width:\s*640px',  # Small mobile
            r'@media.*max-width:\s*768px',  # Large mobile/small tablet
        ]
        
        has_relevant_breakpoints = any(
            re.search(pattern, css_content, re.IGNORECASE)
            for pattern in breakpoint_patterns
        )
        
        assert has_relevant_breakpoints, (
            f"CSS must include media queries for mobile viewport width {viewport_width}px. "
            "Expected responsive breakpoints at common mobile sizes (640px, 768px)"
        )

    def test_mobile_performance_indicators(self):
        """Test that mobile-specific performance optimizations are in place."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for mobile performance indicators
        performance_indicators = []
        
        # Check for lazy loading
        lazy_elements = soup.find_all(attrs={'loading': 'lazy'})
        if lazy_elements:
            performance_indicators.append('lazy_loading')
            
        # Check for responsive images
        responsive_images = soup.find_all('img', class_=re.compile(r'responsive|w-full|max-w'))
        if responsive_images:
            performance_indicators.append('responsive_images')
            
        # Check CSS for mobile-first approach
        css_file_path = Path("app/static/css/main.css")
        if css_file_path.exists():
            css_content = css_file_path.read_text()
            if '@media (min-width:' in css_content:
                performance_indicators.append('mobile_first_css')
        
        assert len(performance_indicators) >= 1, (
            "Mobile responsive design should include performance optimizations. "
            "Expected indicators: lazy loading, responsive images, or mobile-first CSS"
        )

    def test_accessibility_mobile_features(self):
        """Test that mobile responsive features maintain accessibility."""
        response = client.get("/")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        accessibility_features = []
        
        # Check for skip links
        skip_links = soup.find_all('a', href='#main-content') or soup.find_all('a', class_='skip-link')
        if skip_links:
            accessibility_features.append('skip_links')
            
        # Check for proper heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            accessibility_features.append('heading_structure')
            
        # Check for aria labels on interactive elements
        aria_elements = soup.find_all(attrs={'aria-label': True})
        if aria_elements:
            accessibility_features.append('aria_labels')
        
        assert len(accessibility_features) >= 2, (
            "Mobile responsive design must maintain accessibility features. "
            "Expected: skip links, proper heading structure, and aria labels"
        )


if __name__ == "__main__":
    pytest.main([__file__])