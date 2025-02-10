#!/usr/bin/env python3
import os
import yaml
import glob
from collections import defaultdict
from typing import Dict, Set, List
from datetime import datetime

CONTENT_DIR = "app/content"

class ContentAnalyzer:
    def __init__(self):
        self.field_usage = defaultdict(lambda: defaultdict(int))
        self.missing_required = defaultdict(lambda: defaultdict(list))
        self.field_types = defaultdict(lambda: defaultdict(set))
        self.total_files = defaultdict(int)
        self.required_fields = {
            'title': str,
            'created': (str, datetime),
            'updated': (str, datetime),
            'tags': list
        }

    def analyze_file(self, file_path: str, content_type: str):
        self.total_files[content_type] += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.startswith('---'):
                self.missing_required[content_type]['front_matter'].append(file_path)
                return
            
            try:
                _, fm, _ = content.split('---', 2)
                metadata = yaml.safe_load(fm)
                
                # Track field usage
                for field, value in metadata.items():
                    self.field_usage[content_type][field] += 1
                    self.field_types[content_type][field].add(type(value).__name__)
                
                # Check required fields
                for field, expected_type in self.required_fields.items():
                    if field not in metadata:
                        self.missing_required[content_type][field].append(file_path)
                    elif not isinstance(metadata[field], expected_type):
                        if isinstance(expected_type, tuple):
                            if not any(isinstance(metadata[field], t) for t in expected_type):
                                self.missing_required[content_type][f"{field}_type"].append(file_path)
                        else:
                            self.missing_required[content_type][f"{field}_type"].append(file_path)
                
            except ValueError:
                self.missing_required[content_type]['invalid_front_matter'].append(file_path)
            except yaml.YAMLError:
                self.missing_required[content_type]['invalid_yaml'].append(file_path)
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def analyze_all(self):
        for content_dir in glob.glob(f"{CONTENT_DIR}/*"):
            if not os.path.isdir(content_dir):
                continue
                
            content_type = os.path.basename(content_dir)
            for file_path in glob.glob(f"{content_dir}/*.md"):
                self.analyze_file(file_path, content_type)

    def print_report(self):
        print("\n=== Content Analysis Report ===\n")
        
        for content_type in sorted(self.total_files.keys()):
            print(f"\n## {content_type.upper()} ({self.total_files[content_type]} files)")
            
            print("\nField Usage:")
            for field, count in sorted(self.field_usage[content_type].items()):
                percentage = (count / self.total_files[content_type]) * 100
                types = ", ".join(sorted(self.field_types[content_type][field]))
                print(f"  - {field}: {count} ({percentage:.1f}%) [{types}]")
            
            print("\nMissing Required Fields:")
            for field, files in sorted(self.missing_required[content_type].items()):
                if files:
                    print(f"  - {field}: {len(files)} files")
                    for file in files[:3]:  # Show first 3 examples
                        print(f"    - {os.path.basename(file)}")
                    if len(files) > 3:
                        print(f"    - ... and {len(files) - 3} more")

def main():
    analyzer = ContentAnalyzer()
    analyzer.analyze_all()
    analyzer.print_report()

if __name__ == "__main__":
    main() 