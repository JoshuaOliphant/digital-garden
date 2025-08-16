"""
Comprehensive tests for verifying complete removal of Alpine.js and Tailwind CSS.

These tests are designed to FAIL initially with the current implementation
and pass only after complete framework removal is implemented.
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestFrameworkRemoval:
    """Test suite for verifying complete Alpine.js and Tailwind CSS removal."""

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture(scope="class")  
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture(scope="class")
    def template_files(self, project_root: Path) -> List[Path]:
        """Get all HTML template files."""
        templates_dir = project_root / "app" / "templates"
        return list(templates_dir.rglob("*.html"))

    @pytest.fixture(scope="class")
    def css_files(self, project_root: Path) -> List[Path]:
        """Get all CSS files."""
        css_dir = project_root / "app" / "static" / "css"
        return list(css_dir.glob("*.css"))

    @pytest.fixture(scope="class")
    def package_json_path(self, project_root: Path) -> Path:
        """Get package.json path."""
        return project_root / "package.json"

    # Alpine.js Removal Tests
    
    def test_no_alpine_directives_in_templates(self, template_files: List[Path]):
        """Verify no Alpine.js directives exist in any template files."""
        alpine_patterns = [
            r'x-data\s*=', r'x-show\s*=', r'x-if\s*=', r'x-for\s*=', 
            r'x-model\s*=', r'@click\s*=', r'@submit\s*=',
        ]
        
        alpine_found = []
        for template_file in template_files:
            content = template_file.read_text(encoding='utf-8')
            for pattern in alpine_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    alpine_found.append(
                        f"File: {template_file.name}, Pattern: {pattern}, Matches: {matches}"
                    )
        
        assert not alpine_found, (
            f"Alpine.js directives found in templates:\n" + 
            "\n".join(alpine_found)
        )

    def test_no_alpine_references_in_html(self, template_files: List[Path]):
        """Verify no Alpine.js references exist in HTML files."""
        alpine_references = [r'Alpine\.', r'alpine\.js', r'alpinejs']
        
        references_found = []
        for template_file in template_files:
            content = template_file.read_text(encoding='utf-8')
            for pattern in alpine_references:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    references_found.append(
                        f"File: {template_file.name}, Pattern: {pattern}, Matches: {matches}"
                    )
        
        assert not references_found, (
            f"Alpine.js references found in templates:\n" +
            "\n".join(references_found)
        )

    # Tailwind CSS Removal Tests
    
    def test_no_tailwind_classes_in_templates(self, template_files: List[Path]):
        """Verify no Tailwind utility classes exist in template files."""
        tailwind_patterns = [
            r'\bcontainer\b', r'\bmx-auto\b', r'\bflex\b', r'\bgrid\b',
            r'\bp-\d+\b', r'\bpy-\d+\b', r'\bpx-\d+\b', r'\bm-\d+\b',
            r'\btext-\w+\b', r'\bbg-\w+\b', r'\bbg-garden-\w+\b',
            r'\btext-garden-\w+\b', r'\bjustify-\w+\b', r'\bitems-\w+\b',
        ]
        
        tailwind_classes_found = []
        for template_file in template_files:
            content = template_file.read_text(encoding='utf-8')
            for pattern in tailwind_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    tailwind_classes_found.append(
                        f"File: {template_file.name}, Pattern: {pattern}, Count: {len(matches)}"
                    )
        
        assert not tailwind_classes_found, (
            f"Tailwind CSS utility classes found in templates:\n" +
            "\n".join(tailwind_classes_found[:10])
        )

    def test_package_json_dependencies_removed(self, package_json_path: Path):
        """Verify Tailwind CSS dependencies are removed from package.json."""
        if not package_json_path.exists():
            pytest.skip("package.json does not exist")
            
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        tailwind_deps = ['tailwindcss', '@tailwindcss/typography', 'autoprefixer', 'postcss']
        found_deps = []
        all_deps = {}
        
        for dep_section in ['dependencies', 'devDependencies', 'peerDependencies']:
            if dep_section in package_data:
                all_deps.update(package_data[dep_section])
        
        for dep in tailwind_deps:
            if dep in all_deps:
                found_deps.append(f"{dep}: {all_deps[dep]}")
        
        assert not found_deps, (
            f"Tailwind CSS dependencies still found in package.json:\n" +
            "\n".join(found_deps)
        )

    def test_no_tailwind_config_file(self, project_root: Path):
        """Verify tailwind.config.js is removed."""
        tailwind_config = project_root / "tailwind.config.js"
        assert not tailwind_config.exists(), f"Tailwind config file still exists: {tailwind_config}"

    def test_no_postcss_config_file(self, project_root: Path):
        """Verify postcss.config.js is removed."""
        postcss_config = project_root / "postcss.config.js"
        assert not postcss_config.exists(), f"PostCSS config file still exists: {postcss_config}"

    def test_no_tailwind_build_scripts(self, package_json_path: Path):
        """Verify Tailwind build scripts are removed from package.json."""
        if not package_json_path.exists():
            pytest.skip("package.json does not exist")
            
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        if 'scripts' not in package_data:
            return
        
        tailwind_scripts = []
        for script_name, script_command in package_data['scripts'].items():
            if any(kw in script_command.lower() for kw in ['tailwind', 'build:css', 'watch:css']):
                tailwind_scripts.append(f"{script_name}: {script_command}")
        
        assert not tailwind_scripts, (
            f"Tailwind CSS build scripts still found:\n" + "\n".join(tailwind_scripts)
        )

    def test_no_tailwind_directives_in_css(self, css_files: List[Path]):
        """Verify no Tailwind directives exist in CSS files."""
        tailwind_directives = [r'@tailwind\s+base', r'@tailwind\s+components', 
                             r'@tailwind\s+utilities', r'--tw-']
        
        directives_found = []
        for css_file in css_files:
            content = css_file.read_text(encoding='utf-8')
            for pattern in tailwind_directives:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    directives_found.append(
                        f"File: {css_file.name}, Pattern: {pattern}, Count: {len(matches)}"
                    )
        
        assert not directives_found, (
            f"Tailwind CSS directives found in CSS files:\n" + "\n".join(directives_found)
        )

    def test_no_cdn_references(self, template_files: List[Path]):
        """Verify no Tailwind CDN scripts exist in HTML files."""
        cdn_patterns = [r'cdn\.tailwindcss\.com', r'tailwind\.config\s*=', r'tailwindcss']
        
        cdn_found = []
        for template_file in template_files:
            content = template_file.read_text(encoding='utf-8')
            for pattern in cdn_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    cdn_found.append(
                        f"File: {template_file.name}, Pattern: {pattern}, Matches: {matches}"
                    )
        
        assert not cdn_found, (
            f"Tailwind CSS CDN references found in templates:\n" + "\n".join(cdn_found)
        )

    # Functionality Preservation Tests
    
    def test_templates_still_render(self, client: TestClient):
        """Verify templates render without errors after framework removal."""
        routes_to_test = ["/", "/til", "/projects"]
        rendering_errors = []
        
        for route in routes_to_test:
            try:
                response = client.get(route)
                if response.status_code == 500:
                    rendering_errors.append(f"Route {route}: Server error (500)")
                elif response.status_code not in [200, 404]:
                    rendering_errors.append(f"Route {route}: Status {response.status_code}")
            except Exception as e:
                rendering_errors.append(f"Route {route}: Exception - {str(e)}")
        
        assert not rendering_errors, (
            f"Template rendering errors found:\n" + "\n".join(rendering_errors)
        )

    def test_htmx_functionality_preserved(self, template_files: List[Path]):
        """Verify HTMX functionality is preserved after framework removal."""
        htmx_patterns = [r'hx-get\s*=', r'htmx\.org']
        htmx_found = False
        
        for template_file in template_files:
            content = template_file.read_text(encoding='utf-8')
            for pattern in htmx_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    htmx_found = True
                    break
            if htmx_found:
                break
        
        assert htmx_found, (
            "HTMX functionality appears to be missing from templates. "
            "Ensure HTMX is preserved during framework removal."
        )

    def test_responsive_design_preserved(self, css_files: List[Path]):
        """Verify responsive design CSS exists after Tailwind removal."""
        responsive_patterns = [r'@media\s*\([^)]*min-width', r'@media\s*\([^)]*max-width']
        responsive_found = False
        
        for css_file in css_files:
            content = css_file.read_text(encoding='utf-8')
            for pattern in responsive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    responsive_found = True
                    break
            if responsive_found:
                break
        
        assert responsive_found, (
            "No responsive design CSS found. Ensure responsive styles replace Tailwind's utilities."
        )

    def test_custom_css_exists(self, css_files: List[Path]):
        """Verify custom CSS exists to replace framework functionality."""
        custom_css_indicators = [r'\.[\\w-]+\s*\{[^}]*\}', r'#[\\w-]+\s*\{[^}]*\}']
        custom_css_found = False
        
        for css_file in css_files:
            content = css_file.read_text(encoding='utf-8')
            if 'tailwindcss' in content or '--tw-' in content:
                continue
            for pattern in custom_css_indicators:
                if re.search(pattern, content, re.MULTILINE):
                    custom_css_found = True
                    break
            if custom_css_found:
                break
        
        assert custom_css_found, (
            "No custom CSS found to replace framework functionality."
        )