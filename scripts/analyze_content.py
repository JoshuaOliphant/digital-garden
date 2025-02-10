#!/usr/bin/env python3
import os
import yaml
import glob
import json
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set, List, Optional
from datetime import datetime
from anthropic import Anthropic
from bs4 import BeautifulSoup
import markdown
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from textstat import textstat
import networkx as nx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from app.config import ai_config, content_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('content_analysis.log'),
        logging.StreamHandler()
    ]
)

console = Console()
client = Anthropic(api_key=ai_config.anthropic_api_key)

class ContentAnalyzer:
    def __init__(self):
        self.field_usage = defaultdict(lambda: defaultdict(int))
        self.missing_required = defaultdict(lambda: defaultdict(list))
        self.field_types = defaultdict(lambda: defaultdict(set))
        self.total_files = defaultdict(int)
        self.required_fields = content_config.required_fields
        self.content_graph = nx.DiGraph()
        self.md = markdown.Markdown(extensions=['extra'])
        self.content_clusters = {}
        self.quality_metrics = defaultdict(dict)
        
    def _extract_text_content(self, content: str) -> str:
        """Extract plain text from markdown content."""
        html = self.md.convert(content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    async def _analyze_content_quality(self, text: str) -> Dict:
        """Analyze content quality using Claude."""
        prompt = f"""
        Analyze this content for quality and provide metrics:
        
        Content:
        {text[:2000]}  # Limit content length
        
        Please analyze for:
        1. Writing style consistency
        2. Technical accuracy
        3. Clarity and readability
        4. SEO optimization
        5. Content completeness
        
        For each aspect, provide:
        - A score (0-100)
        - Specific issues found
        - Improvement suggestions
        
        Return the analysis as a JSON object.
        """
        
        response = await client.messages.create(
            model=ai_config.claude_model,
            max_tokens=ai_config.claude_max_tokens,
            temperature=ai_config.claude_temperature,
            system=ai_config.system_prompts["analysis"],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _get_seo_suggestions(self, text: str, metadata: Dict) -> Dict:
        """Get SEO optimization suggestions using Claude."""
        prompt = f"""
        Analyze this content and metadata for SEO optimization:
        
        Content:
        {text[:1500]}
        
        Metadata:
        {json.dumps(metadata, indent=2)}
        
        Please provide:
        1. Keyword analysis
        2. Meta description suggestions
        3. Title optimization
        4. Content structure recommendations
        5. Internal linking suggestions
        
        Return suggestions as a JSON object.
        """
        
        response = await client.messages.create(
            model=ai_config.claude_model,
            max_tokens=ai_config.claude_max_tokens,
            temperature=ai_config.claude_temperature,
            system=ai_config.system_prompts["analysis"],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    def _cluster_content(self):
        """Cluster content based on similarity."""
        # Collect all content texts
        texts = []
        file_paths = []
        for content_dir in glob.glob(f"{content_config.content_dir}/*"):
            if not os.path.isdir(content_dir):
                continue
            
            for file_path in glob.glob(f"{content_dir}/*.md"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                text = self._extract_text_content(content)
                texts.append(text)
                file_paths.append(file_path)
        
        if not texts:
            return
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english'
        )
        vectors = vectorizer.fit_transform(texts)
        
        # Cluster content
        n_clusters = min(len(texts) // 5 + 1, 10)  # Reasonable number of clusters
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(vectors)
        
        # Organize results
        for file_path, cluster_id in zip(file_paths, clusters):
            self.content_clusters[file_path] = cluster_id
    
    def _calculate_readability(self, text: str) -> Dict:
        """Calculate readability metrics."""
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "gunning_fog": textstat.gunning_fog(text),
            "smog_index": textstat.smog_index(text),
            "automated_readability_index": textstat.automated_readability_index(text),
            "coleman_liau_index": textstat.coleman_liau_index(text),
            "linsear_write_formula": textstat.linsear_write_formula(text),
            "dale_chall_readability_score": textstat.dale_chall_readability_score(text)
        }
    
    async def analyze_file(self, file_path: str, content_type: str):
        """Analyze a single content file."""
        self.total_files[content_type] += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                self.missing_required[content_type]['front_matter'].append(file_path)
                return
            
            try:
                _, fm, md_content = content.split('---', 2)
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
                
                # Extract text content
                text_content = self._extract_text_content(md_content)
                
                # Get content quality metrics
                quality_metrics = await self._analyze_content_quality(text_content)
                seo_suggestions = await self._get_seo_suggestions(text_content, metadata)
                readability_metrics = self._calculate_readability(text_content)
                
                # Store analysis results
                self.quality_metrics[file_path] = {
                    "quality": quality_metrics,
                    "seo": seo_suggestions,
                    "readability": readability_metrics,
                    "cluster": self.content_clusters.get(file_path)
                }
                
            except ValueError:
                self.missing_required[content_type]['invalid_front_matter'].append(file_path)
            except yaml.YAMLError as e:
                self.missing_required[content_type]['invalid_yaml'].append(file_path)
                
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
    
    async def analyze_all(self):
        """Analyze all content files."""
        # First, cluster content
        self._cluster_content()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for content_dir in glob.glob(f"{content_config.content_dir}/*"):
                if not os.path.isdir(content_dir):
                    continue
                
                content_type = os.path.basename(content_dir)
                task_id = progress.add_task(
                    f"Analyzing {content_type} content...",
                    total=None
                )
                
                for file_path in glob.glob(f"{content_dir}/*.md"):
                    await self.analyze_file(file_path, content_type)
                
                progress.update(task_id, completed=True)
    
    def print_report(self):
        """Print analysis report."""
        print("\n=== Content Analysis Report ===\n")
        
        # Print basic stats
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
                    for file in files[:3]:
                        print(f"    - {os.path.basename(file)}")
                    if len(files) > 3:
                        print(f"    - ... and {len(files) - 3} more")
        
        # Print quality metrics summary
        print("\n## Content Quality Metrics")
        table = Table(title="Quality Metrics Summary")
        table.add_column("File")
        table.add_column("Quality Score")
        table.add_column("SEO Score")
        table.add_column("Readability")
        table.add_column("Cluster")
        
        for file_path, metrics in self.quality_metrics.items():
            table.add_row(
                os.path.basename(file_path),
                str(metrics["quality"].get("overall_score", "N/A")),
                str(metrics["seo"].get("overall_score", "N/A")),
                str(metrics["readability"]["flesch_reading_ease"]),
                str(metrics["cluster"])
            )
        
        console.print(table)
        
        # Save detailed report
        report_path = "content_analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "field_usage": dict(self.field_usage),
                "missing_required": dict(self.missing_required),
                "quality_metrics": self.quality_metrics
            }, f, indent=2)
        
        print(f"\nDetailed report saved to {report_path}")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze content files')
    parser.add_argument('--file', help='Process a specific file')
    args = parser.parse_args()
    
    analyzer = ContentAnalyzer()
    
    if args.file:
        content_type = os.path.basename(os.path.dirname(args.file))
        await analyzer.analyze_file(args.file, content_type)
    else:
        await analyzer.analyze_all()
    
    analyzer.print_report()

if __name__ == "__main__":
    asyncio.run(main()) 