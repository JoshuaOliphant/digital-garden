#!/usr/bin/env python3
"""
Simple test to verify dark mode implementation without Playwright.
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_page_has_dark_mode_elements():
    """Test that the home page includes dark mode toggle elements."""
    response = client.get("/")
    assert response.status_code == 200
    
    html_content = response.text
    
    # Check for Alpine.js
    assert 'alpinejs' in html_content.lower(), "Alpine.js should be included"
    
    # Check for dark mode toggle button
    assert 'data-testid="dark-mode-toggle"' in html_content, "Dark mode toggle button should exist"
    
    # Check for theme detection script
    assert "localStorage.getItem('theme')" in html_content, "Theme detection script should be present"
    
    # Check for Alpine dark mode component
    assert 'darkModeToggle' in html_content, "Dark mode toggle component should be defined"
    
    # Check for dark mode CSS classes
    assert 'dark:bg-[#0f1419]' in html_content, "Dark mode background color should be defined"
    assert 'dark:text-[#e6f1ff]' in html_content, "Dark mode text color should be defined"
    
    # Check for icons in toggle
    assert 'M12 3v1m0 16v1m9-9h-1M4' in html_content, "Sun icon should be present"
    assert 'M20.354 15.354A9 9' in html_content, "Moon icon should be present"
    
    print("✅ All dark mode elements are present in the template!")

if __name__ == "__main__":
    test_home_page_has_dark_mode_elements()
    print("\n🎉 Dark mode implementation verified successfully!")