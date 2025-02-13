#!/usr/bin/env python3
import os
import yaml
import glob
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pydantic import ValidationError
import anthropic
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import markdown
import html2text

from app.models import BaseContent, Bookmark, TIL, Note, ContentMetadata
from app.config import ai_config

CONTENT_DIR = "app/content"

class ContentValidator:
    """Validates content quality, links, and accessibility using Claude."""
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ai_config.anthropic_api_key)
    
    def check_writing_style(self, content: str) -> Dict[str, any]:
        """Analyze writing style consistency and quality."""
        prompt = f"""Analyze this content for writing style and quality. Focus on:
        1. Tone consistency
        2. Technical accuracy
        3. Clarity and readability
        4. Grammar and spelling
        
        Content: {content[:1000]}  # Limit content length
        
        Respond with a JSON object containing:
        {{
            "style_score": 1-10 rating,
            "tone": "formal|casual|mixed",
            "improvements": ["suggestion1", "suggestion2"],
            "grammar_issues": ["issue1", "issue2"]
        }}
        """
        
        response = self.client.messages.create(
            model=ai_config.claude_model,
            max_tokens=ai_config.claude_max_tokens,
            temperature=ai_config.claude_temperature,
            system=ai_config.system_prompts["analysis"],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return yaml.safe_load(response.content[0].text)

    def validate_links(self, content: str) -> List[Dict[str, any]]:
        """Check if links are valid and accessible."""
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        results = []
        
        for text, url in links:
            try:
                parsed = urlparse(url)
                if not parsed.scheme:
                    results.append({
                        "text": text,
                        "url": url,
                        "valid": False,
                        "error": "Missing URL scheme (http/https)"
                    })
                    continue
                
                response = requests.head(url, allow_redirects=True, timeout=5)
                results.append({
                    "text": text,
                    "url": url,
                    "valid": 200 <= response.status_code < 400,
                    "status_code": response.status_code
                })
            except Exception as e:
                results.append({
                    "text": text,
                    "url": url,
                    "valid": False,
                    "error": str(e)
                })
        
        return results

    def check_accessibility(self, content: str) -> Dict[str, any]:
        """Check content for accessibility issues."""
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        issues = []
        
        # Check image alt text
        images = soup.find_all('img')
        for img in images:
            if not img.get('alt'):
                issues.append(f"Missing alt text for image: {img.get('src', 'unknown')}")
        
        # Check heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        prev_level = 0
        for h in headings:
            level = int(h.name[1])
            if level - prev_level > 1:
                issues.append(f"Skipped heading level: {h.name} after h{prev_level}")
            prev_level = level
        
        return {
            "issues": issues,
            "images_total": len(images),
            "images_with_alt": len([img for img in images if img.get('alt')]),
            "headings_total": len(headings)
        }

class FrontMatterValidator:
    def __init__(self):
        self.model_map = {
            'bookmarks': Bookmark,
            'til': TIL,
            'notes': Note,
            'how_to': Note,
            'pages': Note
        }
        self.errors = []
        self.fixes_applied = []
        self.content_validator = ContentValidator()
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return datetime.now()

    def _fix_common_issues(self, metadata: Dict) -> Dict:
        """Fix common front matter issues."""
        fixed = metadata.copy()
        
        # Ensure dates are in correct format
        for date_field in ['created', 'updated']:
            if date_field in fixed and isinstance(fixed[date_field], str):
                fixed[date_field] = self._parse_date(fixed[date_field])
        
        # Ensure tags is a list
        if 'tags' in fixed:
            if isinstance(fixed['tags'], str):
                fixed['tags'] = [tag.strip() for tag in fixed['tags'].split(',')]
            elif not isinstance(fixed['tags'], list):
                fixed['tags'] = []
        
        # Set default values for missing fields
        if 'status' not in fixed:
            fixed['status'] = "Evergreen"
        if 'visibility' not in fixed:
            fixed['visibility'] = "public"
        
        return fixed

    def validate_file(self, file_path: str, content_type: str, fix: bool = False) -> Tuple[bool, List[str]]:
        """Validate front matter and content in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                return False, ["No front matter found"]
            
            try:
                _, fm, md_content = content.split('---', 2)
                metadata = yaml.safe_load(fm)
                
                if fix:
                    metadata = self._fix_common_issues(metadata)
                
                # Get appropriate model
                model_class = self.model_map.get(content_type, BaseContent)
                
                try:
                    # Validate with model
                    validated = model_class(**metadata)
                    
                    # Perform enhanced validation
                    validation_results = {
                        "writing_style": self.content_validator.check_writing_style(md_content),
                        "links": self.content_validator.validate_links(md_content),
                        "accessibility": self.content_validator.check_accessibility(md_content)
                    }
                    
                    # Collect validation issues
                    issues = []
                    
                    # Writing style issues
                    if validation_results["writing_style"]["style_score"] < 7:
                        issues.extend(validation_results["writing_style"]["improvements"])
                    
                    # Link issues
                    invalid_links = [l for l in validation_results["links"] if not l["valid"]]
                    if invalid_links:
                        issues.extend([f"Invalid link: {l['url']} - {l.get('error', l.get('status_code'))}" 
                                    for l in invalid_links])
                    
                    # Accessibility issues
                    if validation_results["accessibility"]["issues"]:
                        issues.extend(validation_results["accessibility"]["issues"])
                    
                    if fix and metadata != validated.model_dump():
                        # Write fixed content back to file
                        fixed_content = f"---\n{yaml.dump(validated.model_dump(), default_flow_style=False)}---{md_content}"
                        backup_path = f"{file_path}.bak"
                        os.rename(file_path, backup_path)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        self.fixes_applied.append(f"Fixed and validated {file_path}")
                    
                    return len(issues) == 0, issues
                    
                except ValidationError as e:
                    return False, [f"{err['loc']}: {err['msg']}" for err in e.errors()]
                
            except ValueError:
                return False, ["Invalid front matter format"]
            except yaml.YAMLError as e:
                return False, [f"YAML parsing error: {str(e)}"]
            
        except Exception as e:
            return False, [f"Error processing file: {str(e)}"]

    def validate_all(self, fix: bool = False) -> None:
        """Validate all content files."""
        for content_dir in glob.glob(f"{CONTENT_DIR}/*"):
            if not os.path.isdir(content_dir):
                continue
            
            content_type = os.path.basename(content_dir)
            print(f"\nValidating {content_type} content...")
            
            for file_path in glob.glob(f"{content_dir}/*.md"):
                valid, errors = self.validate_file(file_path, content_type, fix)
                if not valid:
                    rel_path = os.path.relpath(file_path, CONTENT_DIR)
                    self.errors.append((rel_path, errors))

    def print_report(self) -> None:
        """Print validation report."""
        if not self.errors and not self.fixes_applied:
            print("\nAll content files are valid! 🎉")
            return
        
        if self.fixes_applied:
            print("\nFixes Applied:")
            for fix in self.fixes_applied:
                print(f"✓ {fix}")
        
        if self.errors:
            print("\nValidation Errors:")
            for file_path, errors in self.errors:
                print(f"\n{file_path}:")
                for error in errors:
                    print(f"  ✗ {error}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate front matter and content in files')
    parser.add_argument('--fix', action='store_true', help='Try to fix common issues')
    args = parser.parse_args()
    
    validator = FrontMatterValidator()
    validator.validate_all(args.fix)
    validator.print_report()

if __name__ == "__main__":
    main() 