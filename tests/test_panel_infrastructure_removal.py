"""
Test suite for verifying complete removal of sliding panel infrastructure.
These tests should FAIL initially and PASS after removal is complete.
"""

import ast
import os
import pytest
import re
from pathlib import Path
from typing import List, Set
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class TestPanelInfrastructureRemoval:
    """Comprehensive tests to verify complete removal of sliding panel infrastructure."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    def test_panel_navigation_js_removed(self):
        """Test that panel-navigation.js no longer exists."""
        js_path = PROJECT_ROOT / "app" / "static" / "js" / "panel-navigation.js"
        assert not js_path.exists(), f"Panel navigation JS still exists at {js_path}"
    
    def test_sliding_panel_template_removed(self):
        """Test that sliding_panel.html partial no longer exists."""
        template_path = PROJECT_ROOT / "app" / "templates" / "partials" / "sliding_panel.html"
        assert not template_path.exists(), f"Sliding panel template still exists at {template_path}"
    
    def test_base_html_has_no_panel_scripts(self):
        """Test that base.html contains no references to panel-navigation.js."""
        base_path = PROJECT_ROOT / "app" / "templates" / "base.html"
        if base_path.exists():
            content = base_path.read_text()
            assert "panel-navigation.js" not in content, \
                "base.html still contains reference to panel-navigation.js"
            assert "panel-navigation" not in content.lower(), \
                "base.html still contains panel navigation references"
    
    def test_no_panel_css_classes(self):
        """Test that no sliding panel CSS classes remain in templates."""
        template_dir = PROJECT_ROOT / "app" / "templates"
        panel_classes = [
            r'class="[^"]*panel[^"]*"',
            r'class="[^"]*slide[^"]*"',
            r'class="[^"]*sliding[^"]*"',
            r'panel-content',
            r'panel-navigation',
            r'sliding-panel',
            r'slide-panel'
        ]
        
        issues = []
        for template_file in template_dir.rglob("*.html"):
            content = template_file.read_text()
            for pattern in panel_classes:
                if re.search(pattern, content, re.IGNORECASE):
                    # Skip if it's in a comment
                    if not re.search(f'<!--.*{pattern}.*-->', content, re.IGNORECASE | re.DOTALL):
                        issues.append(f"{template_file.name}: Found panel CSS class pattern '{pattern}'")
        
        assert not issues, f"Panel CSS classes found:\n" + "\n".join(issues)
    
    def test_no_panel_html_elements(self):
        """Test that no panel-specific HTML elements exist in templates."""
        template_dir = PROJECT_ROOT / "app" / "templates"
        panel_elements = [
            r'<div[^>]*id="[^"]*panel[^"]*"',
            r'<div[^>]*data-panel[^>]*>',
            r'x-data=".*panel.*"',
            r'@panel',
            r'\$panel'
        ]
        
        issues = []
        for template_file in template_dir.rglob("*.html"):
            content = template_file.read_text()
            for pattern in panel_elements:
                if re.search(pattern, content, re.IGNORECASE):
                    # Skip if it's in a comment
                    if not re.search(f'<!--.*{pattern}.*-->', content, re.IGNORECASE | re.DOTALL):
                        issues.append(f"{template_file.name}: Found panel HTML element pattern '{pattern}'")
        
        assert not issues, f"Panel HTML elements found:\n" + "\n".join(issues)
    
    def test_garden_walk_template_removed(self):
        """Test that garden_walk.html no longer exists."""
        template_path = PROJECT_ROOT / "app" / "templates" / "garden_walk.html"
        assert not template_path.exists(), f"Garden walk template still exists at {template_path}"
    
    def test_garden_walk_route_removed(self, client):
        """Test that /garden-walk route returns 404."""
        response = client.get("/garden-walk")
        assert response.status_code == 404, \
            f"Garden walk route still exists, returned status {response.status_code}"
    
    def test_state_management_functions_removed(self):
        """Test that serialize/deserialize_garden_state functions are removed from main.py."""
        main_path = PROJECT_ROOT / "app" / "main.py"
        if main_path.exists():
            content = main_path.read_text()
            
            # Parse the Python file
            try:
                tree = ast.parse(content)
                function_names = [node.name for node in ast.walk(tree) 
                                 if isinstance(node, ast.FunctionDef)]
                
                assert "serialize_garden_state" not in function_names, \
                    "serialize_garden_state function still exists in main.py"
                assert "deserialize_garden_state" not in function_names, \
                    "deserialize_garden_state function still exists in main.py"
            except SyntaxError as e:
                pytest.fail(f"Failed to parse main.py: {e}")
    
    def test_panel_test_files_removed(self):
        """Test that old panel test files are removed."""
        test_files = [
            PROJECT_ROOT / "tests" / "test_sliding_panel_ui.py",
            PROJECT_ROOT / "tests" / "test_share_state_persistence.py",
            PROJECT_ROOT / "tests" / "test_url_state_management.py"
        ]
        
        existing_files = [f for f in test_files if f.exists()]
        assert not existing_files, \
            f"Panel test files still exist: {[str(f) for f in existing_files]}"
    
    def test_demo_content_removed(self):
        """Test that demo-panel-navigation.md is removed."""
        demo_path = PROJECT_ROOT / "app" / "content" / "notes" / "demo-panel-navigation.md"
        assert not demo_path.exists(), f"Demo panel content still exists at {demo_path}"
    
    def test_no_panel_references_in_python(self):
        """Test that no panel references remain in Python code."""
        python_files = list((PROJECT_ROOT / "app").rglob("*.py"))
        panel_keywords = [
            "sliding_panel",
            "panel_navigation", 
            "garden_walk",
            "serialize_garden_state",
            "deserialize_garden_state",
            "panel_state",
            "panel_content"
        ]
        
        issues = []
        for py_file in python_files:
            content = py_file.read_text()
            for keyword in panel_keywords:
                if keyword in content.lower():
                    # Check if it's in a comment or string
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if keyword in line.lower():
                            # Skip if it's a comment
                            if not line.strip().startswith('#'):
                                issues.append(f"{py_file.relative_to(PROJECT_ROOT)}:{i} - Found '{keyword}'")
        
        assert not issues, f"Panel references found in Python code:\n" + "\n".join(issues[:10])
    
    def test_no_panel_imports(self):
        """Test that no imports or includes of removed panel files exist."""
        all_files = list((PROJECT_ROOT / "app").rglob("*.py")) + \
                   list((PROJECT_ROOT / "app").rglob("*.html"))
        
        import_patterns = [
            r'from.*sliding_panel.*import',
            r'import.*sliding_panel',
            r'from.*panel_navigation.*import',
            r'import.*panel_navigation',
            r'include.*sliding_panel',
            r'include.*panel.?navigation'
        ]
        
        issues = []
        for file_path in all_files:
            content = file_path.read_text()
            for pattern in import_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"{file_path.relative_to(PROJECT_ROOT)}: Found import pattern '{pattern}'")
        
        assert not issues, f"Panel imports/includes found:\n" + "\n".join(issues)
    
    def test_no_garden_walk_references(self):
        """Test that no references to garden-walk route remain."""
        files_to_check = list((PROJECT_ROOT / "app").rglob("*.py")) + \
                         list((PROJECT_ROOT / "app").rglob("*.html")) + \
                         list((PROJECT_ROOT / "app").rglob("*.md"))
        
        issues = []
        for file_path in files_to_check:
            if file_path.name == "test_panel_infrastructure_removal.py":
                continue  # Skip this test file
            
            content = file_path.read_text()
            if "garden-walk" in content or "garden_walk" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if "garden-walk" in line or "garden_walk" in line:
                        # Skip if it's a comment
                        if not line.strip().startswith('#') and not line.strip().startswith('//'):
                            issues.append(f"{file_path.relative_to(PROJECT_ROOT)}:{i}")
        
        assert not issues, f"Garden walk references found:\n" + "\n".join(issues[:10])
    
    def test_no_panel_css_files(self):
        """Test that no panel-specific CSS files exist."""
        css_dir = PROJECT_ROOT / "app" / "static" / "css"
        if css_dir.exists():
            panel_css_files = [
                f for f in css_dir.glob("*panel*.css")
            ]
            assert not panel_css_files, f"Panel CSS files still exist: {panel_css_files}"
    
    def test_no_panel_javascript_references(self):
        """Test that no JavaScript files reference panel functionality."""
        js_dir = PROJECT_ROOT / "app" / "static" / "js"
        if js_dir.exists():
            js_files = list(js_dir.glob("*.js"))
            
            panel_keywords = ["panel", "slide", "sliding", "garden-walk"]
            issues = []
            
            for js_file in js_files:
                content = js_file.read_text()
                for keyword in panel_keywords:
                    if keyword in content.lower():
                        issues.append(f"{js_file.name}: Contains '{keyword}'")
            
            assert not issues, f"Panel references in JavaScript:\n" + "\n".join(issues)
    
    def test_core_routes_still_work(self, client):
        """Test that core application routes still function after panel removal."""
        # Test main routes that should still work
        core_routes = [
            "/",
            "/til",
            "/bookmarks"
        ]
        
        for route in core_routes:
            response = client.get(route)
            assert response.status_code == 200, \
                f"Core route {route} broken after panel removal: status {response.status_code}"
    
    def test_no_broken_template_includes(self):
        """Test that no templates try to include removed panel templates."""
        template_dir = PROJECT_ROOT / "app" / "templates"
        
        include_patterns = [
            r'{%\s*include\s+["\'].*sliding_panel.*["\']',
            r'{%\s*include\s+["\'].*panel.*["\']',
            r'{%\s*extends\s+["\'].*panel.*["\']'
        ]
        
        issues = []
        for template_file in template_dir.rglob("*.html"):
            content = template_file.read_text()
            for pattern in include_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        # Check if it's actually a panel-related include
                        if any(x in match.lower() for x in ['sliding', 'panel', 'navigation']):
                            issues.append(f"{template_file.name}: {match}")
        
        assert not issues, f"Broken template includes found:\n" + "\n".join(issues)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])