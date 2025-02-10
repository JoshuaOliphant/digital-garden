#!/usr/bin/env python3
import os
import yaml
import glob
from datetime import datetime
from typing import Dict, List, Tuple
from pydantic import ValidationError

from app.models import BaseContent, Bookmark, TIL, Note, ContentMetadata

CONTENT_DIR = "app/content"

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
        """Validate front matter in a file."""
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
                    
                    if fix and metadata != validated.model_dump():
                        # Write fixed content back to file
                        fixed_content = f"---\n{yaml.dump(validated.model_dump(), default_flow_style=False)}---{md_content}"
                        backup_path = f"{file_path}.bak"
                        os.rename(file_path, backup_path)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        self.fixes_applied.append(f"Fixed and validated {file_path}")
                    
                    return True, []
                    
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
    parser = argparse.ArgumentParser(description='Validate front matter in content files')
    parser.add_argument('--fix', action='store_true', help='Try to fix common issues')
    args = parser.parse_args()
    
    validator = FrontMatterValidator()
    validator.validate_all(args.fix)
    validator.print_report()

if __name__ == "__main__":
    main() 