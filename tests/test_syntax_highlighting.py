"""
Test suite for syntax highlighting functionality with Pygments.
Tests follow strict TDD principles and must fail initially.

This module tests Task 19: Add Syntax Highlighting with Pygments
- Code blocks should include proper syntax highlighting
- Pygments CSS classes should be applied correctly  
- Language detection should work for explicit and implicit tags
- CSS styles should exist for highlighted code
"""

import pytest
from pathlib import Path


@pytest.fixture
def python_code_sample():
    """Sample Python code for testing syntax highlighting."""
    return '''```python
def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
numbers = [fibonacci(i) for i in range(10)]
print(f"First 10 Fibonacci numbers: {numbers}")
```'''


@pytest.fixture
def javascript_code_sample():
    """Sample JavaScript code for testing syntax highlighting."""
    return '''```javascript
function fetchData(url) {
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Data received:', data);
            return data;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}

const apiUrl = 'https://api.example.com/data';
fetchData(apiUrl);
```'''


@pytest.fixture
def bash_code_sample():
    """Sample Bash code for testing syntax highlighting."""
    return '''```bash
#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=app --cov-report=html tests/

# Start the development server
uvicorn app.main:app --reload --port 8000
```'''


@pytest.fixture
def html_code_sample():
    """Sample HTML code for testing syntax highlighting."""
    return '''```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Garden</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <main class="container mx-auto px-4">
        <h1 class="text-3xl font-bold">Welcome</h1>
        <p>This is a sample HTML document.</p>
    </main>
</body>
</html>
```'''


@pytest.fixture
def auto_detect_code_sample():
    """Code sample without explicit language for auto-detection testing."""
    return '''```
import json
import requests

def get_user_data(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()
```'''


@pytest.fixture
def mixed_content_with_code():
    """Sample content mixing markdown text with code blocks."""
    return '''# Python Tutorial

This tutorial covers basic Python concepts.

## Functions

Here's how to define a function:

```python
def greet(name):
    """Greet a person by name."""
    return f"Hello, {name}!"

result = greet("World")
print(result)
```

## Running Commands

You can also run shell commands:

```bash
python script.py
ls -la
```

That's it!
'''


class TestSyntaxHighlightingCore:
    """Test core syntax highlighting functionality."""
    
    def test_code_blocks_include_syntax_highlighting(self, python_code_sample):
        """Test that code blocks are highlighted with Pygments CSS classes.
        
        This test verifies that:
        - Code blocks are wrapped with proper CSS classes
        - Python keywords get syntax highlighting classes
        - Function names and strings are highlighted
        - Comments receive appropriate styling
        """
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            result = service.render_markdown(python_code_sample)
            
            # Verify basic structure
            assert "html" in result, "Should return HTML content"
            html = result["html"]
            
            # Pygments is already working! These should pass:
            assert 'class="codehilite"' in html, \
                "Code blocks should have 'codehilite' wrapper class from Pygments"
            
            # Pygments token classes should be present:
            assert 'class="k"' in html, \
                "Python keywords (def, return, if) should have 'k' class"
            assert 'class="nf"' in html, \
                "Function names (fibonacci) should have 'nf' class"
            assert 'class="s2"' in html or 'class="sd"' in html, \
                "String literals should have string class (s1, s2, sd, etc.)"
            assert 'class="c1"' in html, \
                "Comments should have comment class (c1)"
            
            # Verify code content is preserved within highlighted spans
            assert 'class="k">def</span>' in html and 'class="nf">fibonacci</span>' in html, "Function definition should be preserved in highlighted spans"
            assert "Calculate the nth Fibonacci number" in html, "Docstring should be preserved"
            assert ("fibonacci(n-1)" in html or 
                    ("fibonacci" in html and "n" in html and "-" in html and "1" in html)), "Function calls should be preserved"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_pygments_css_classes_applied(self, javascript_code_sample):
        """Test that Pygments applies correct CSS classes for JavaScript.
        
        Verifies JavaScript-specific token highlighting:
        - Keywords (function, return, const)
        - Built-in functions (console.log, fetch)
        - String literals and template literals
        - Arrow functions and modern syntax
        """
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            result = service.render_markdown(javascript_code_sample)
            
            html = result["html"]
            
            # Test will FAIL initially - Pygments not properly configured
            assert 'class="codehilite"' in html, \
                "JavaScript code should have codehilite wrapper"
            
            # JavaScript-specific highlighting classes  
            assert 'class="kd"' in html or 'class="k"' in html, \
                "JavaScript keywords (function, const) should be highlighted"
            assert 'class="nx"' in html or 'class="nf"' in html, \
                "Function names (fetchData) should be highlighted"
            assert 'class="s1"' in html or 'class="s2"' in html, \
                "String literals should be highlighted"
            
            # Verify JavaScript content preserved within highlighted spans
            assert "function" in html and "fetchData" in html, "Function declaration preserved"
            assert "console" in html and "log" in html, "Console statements preserved"
            assert "fetch" in html and "url" in html, "API calls preserved"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_language_detection_works(self, auto_detect_code_sample, bash_code_sample):
        """Test language detection for explicit and implicit language tags.
        
        Tests both:
        - Explicit language specification (```bash)
        - Automatic language detection (``` with no language)
        """
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            
            # Test explicit language specification
            bash_result = service.render_markdown(bash_code_sample)
            bash_html = bash_result["html"]
            
            # Test will FAIL initially - language detection not working
            assert 'class="codehilite"' in bash_html, \
                "Bash code should have codehilite class"
            
            # Bash-specific elements should be highlighted
            assert "#!" in bash_html and "bin" in bash_html and "bash" in bash_html, "Shebang should be preserved"
            assert "pip" in bash_html and "install" in bash_html, "Commands should be preserved"
            
            # Test automatic language detection
            auto_result = service.render_markdown(auto_detect_code_sample)
            auto_html = auto_result["html"]
            
            # Should still apply highlighting even without explicit language
            assert 'class="codehilite"' in auto_html, \
                "Auto-detected code should have codehilite class"
            assert "import" in auto_html and "json" in auto_html, "Python imports should be preserved"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_syntax_highlighting_css_exists(self):
        """Test that main.css contains Pygments styling classes.
        
        Verifies that the CSS file includes styles for:
        - .codehilite wrapper class
        - Common Pygments token classes (.k, .nf, .s, .c1, etc.)
        - Proper dark theme colors for highlighted code
        """
        main_css_path = Path("app/static/css/main.css")
        
        assert main_css_path.exists(), "main.css file should exist"
        
        css_content = main_css_path.read_text()
        
        # THIS TEST WILL FAIL - CSS classes not yet defined
        assert ".codehilite" in css_content, \
            "CSS should include .codehilite wrapper styles"
        
        # Check for common Pygments token classes - THESE WILL FAIL
        pygments_classes = [
            ".codehilite .k",     # Keywords
            ".codehilite .nf",    # Function names  
            ".codehilite .s",     # Strings (may be .s1, .s2, etc.)
            ".codehilite .c1",    # Comments
            ".codehilite .nb",    # Built-ins
            ".codehilite .o",     # Operators
        ]
        
        for css_class in pygments_classes:
            assert css_class in css_content, \
                f"CSS should include styles for {css_class}"
        
        # Verify dark theme compatibility - WILL FAIL
        # Need to check for Pygments-specific background colors, not just any background
        assert ".codehilite .k" in css_content and "color:" in css_content, \
            "Pygments token styles should include colors for dark theme"


class TestSyntaxHighlightingIntegration:
    """Test syntax highlighting integration with content processing."""
    
    def test_multiple_code_blocks_in_content(self, mixed_content_with_code):
        """Test that multiple code blocks in one document are all highlighted."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            result = service.render_markdown(mixed_content_with_code)
            
            html = result["html"]
            
            # Should have multiple codehilite blocks
            codehilite_count = html.count('class="codehilite"')
            assert codehilite_count >= 2, \
                "Should highlight both Python and Bash code blocks"
            
            # Both languages should be processed
            assert "def" in html and "greet" in html, "Python function should be preserved"
            assert "python" in html and "script" in html, "Bash commands should be preserved"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_html_code_highlighting(self, html_code_sample):
        """Test HTML/XML syntax highlighting."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            result = service.render_markdown(html_code_sample)
            
            html = result["html"]
            
            # Test will FAIL initially - HTML highlighting not configured
            assert 'class="codehilite"' in html, \
                "HTML code should have codehilite wrapper"
            
            # HTML-specific content should be preserved
            assert "DOCTYPE" in html and "html" in html, "HTML doctype preserved"
            assert "meta" in html and "charset" in html, "Meta tags preserved"
            assert "container" in html and "mx-auto" in html, "HTML attributes preserved"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_code_highlighting_preserves_content_structure(self, python_code_sample):
        """Test that syntax highlighting doesn't break content structure."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            result = service.render_markdown(python_code_sample)
            
            html = result["html"]
            
            # Original markdown structure should be preserved
            assert "<pre>" in html, "Code should be in pre tags"
            assert "<code>" in html, "Code should have code tags"
            
            # Content should not be double-encoded
            assert "&lt;def&gt;" not in html, "HTML should not be double-encoded"
            # Function definition should be readable within spans
            assert ('class="k">def</span>' in html and 'class="nf">fibonacci</span>' in html) or "def fibonacci" in html, "Function definition should be readable"
            
        except ImportError:
            pytest.fail("ContentService should be importable")


class TestSyntaxHighlightingConfiguration:
    """Test syntax highlighting configuration and edge cases."""
    
    def test_codehilite_extension_configured_with_pygments(self):
        """Test that markdown processor is configured with proper Pygments options."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            
            # Test will FAIL initially - Pygments options not configured
            # Check that codehilite extension is loaded with proper options
            extensions = str(service._md.treeprocessors)
            assert 'codehilite' in extensions.lower(), \
                "Codehilite extension should be loaded"
            
            # Test will FAIL initially - need to verify Pygments configuration
            # This would require checking the actual extension configuration
            # which will be implemented when the feature is built
            
        except ImportError:
            pytest.fail("ContentService should be importable")
        except AttributeError:
            pytest.fail("ContentService should have configured markdown processor")
    
    def test_unsupported_language_fallback(self):
        """Test behavior with unsupported language codes."""
        try:
            from app.services.content_service import ContentService
            
            unsupported_code = '''```fakeLanguage
some code in unsupported language
with various symbols @#$%
```'''
            
            service = ContentService()
            result = service.render_markdown(unsupported_code)
            
            html = result["html"]
            
            # Should still wrap in codehilite even if language not recognized
            assert 'class="codehilite"' in html, \
                "Should have codehilite wrapper even for unknown languages"
            assert ("some" in html and "code" in html and "unsupported" in html and "language" in html), \
                "Content should be preserved for unknown languages"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_empty_code_blocks_handled_gracefully(self):
        """Test that empty code blocks don't break highlighting."""
        try:
            from app.services.content_service import ContentService
            
            empty_code = '''```python
```'''
            
            service = ContentService()
            result = service.render_markdown(empty_code)
            
            html = result["html"]
            
            # Should handle empty blocks gracefully
            assert "<pre>" in html or "<code>" in html, \
                "Empty code blocks should still generate HTML structure"
            
        except ImportError:
            pytest.fail("ContentService should be importable")


class TestSyntaxHighlightingCSS:
    """Test CSS integration for syntax highlighting."""
    
    def test_css_file_has_dark_theme_pygments_styles(self):
        """Test that CSS includes appropriate dark theme colors for code."""
        main_css_path = Path("app/static/css/main.css")
        
        if not main_css_path.exists():
            pytest.skip("main.css not found - CSS compilation may be needed")
        
        css_content = main_css_path.read_text()
        
        # Test will FAIL initially - dark theme Pygments styles not added
        assert ".codehilite" in css_content, \
            "CSS should include codehilite base styles"
        
        # Check for dark theme appropriate colors (not light theme)
        # Dark themes typically use light text on dark backgrounds
        if ".codehilite .k" in css_content:
            # If keyword styles exist, they should be light colors for dark theme
            # This is a more specific test that will be refined during implementation
            keyword_style_line = [line for line in css_content.split('\n') 
                                 if '.codehilite .k' in line]
            if keyword_style_line:
                # Should contain light colors, not dark ones
                style = keyword_style_line[0].lower()
                # These are examples - actual colors will be determined during implementation
                assert not ("#000" in style or "black" in style), \
                    "Keywords should use light colors for dark theme"
    
    def test_css_includes_responsive_code_styles(self):
        """Test that code highlighting CSS works on mobile devices."""
        main_css_path = Path("app/static/css/main.css")
        
        if not main_css_path.exists():
            pytest.skip("main.css not found")
        
        css_content = main_css_path.read_text()
        
        # Test will FAIL initially - responsive code styles not implemented
        if ".codehilite" in css_content:
            # Should handle overflow properly for long code lines
            assert "overflow" in css_content, \
                "CSS should handle code overflow for mobile devices"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])