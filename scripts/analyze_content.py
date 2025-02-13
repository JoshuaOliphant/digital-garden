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
    
    async def _predict_engagement(self, text: str, metadata: Dict) -> Dict:
        """Predict content engagement potential using Claude."""
        prompt = f"""
        Analyze this content and metadata to predict engagement potential:
        
        Content:
        {text[:1500]}
        
        Metadata:
        {json.dumps(metadata, indent=2)}
        
        Please predict:
        1. Target audience engagement level (0-100)
        2. Social sharing potential (0-100)
        3. Discussion/comment potential (0-100)
        4. Content longevity (0-100)
        5. Factors affecting engagement
        
        Also suggest:
        1. Ways to increase engagement
        2. Best platforms/channels for sharing
        3. Potential discussion topics
        
        Return predictions and suggestions as a JSON object.
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
                engagement_predictions = await self._predict_engagement(text_content, metadata)
                
                # Store analysis results
                self.quality_metrics[file_path] = {
                    "quality": quality_metrics,
                    "seo": seo_suggestions,
                    "readability": readability_metrics,
                    "engagement": engagement_predictions,
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
        console.print("\n[bold]Content Analysis Report[/bold]\n")
        
        # Content Type Statistics
        console.print("[bold]Content Type Statistics:[/bold]")
        stats_table = Table(show_header=True, header_style="bold")
        stats_table.add_column("Content Type")
        stats_table.add_column("Total Files")
        stats_table.add_column("Valid Files")
        stats_table.add_column("Invalid Files")
        
        for content_type, total in self.total_files.items():
            invalid = len(self.missing_required[content_type].get('front_matter', [])) + \
                     len(self.missing_required[content_type].get('invalid_front_matter', [])) + \
                     len(self.missing_required[content_type].get('invalid_yaml', []))
            valid = total - invalid
            stats_table.add_row(content_type, str(total), str(valid), str(invalid))
        
        console.print(stats_table)
        console.print()
        
        # Field Usage Statistics
        console.print("[bold]Field Usage Statistics:[/bold]")
        for content_type, fields in self.field_usage.items():
            console.print(f"\n[bold]{content_type}:[/bold]")
            field_table = Table(show_header=True, header_style="bold")
            field_table.add_column("Field")
            field_table.add_column("Usage Count")
            field_table.add_column("Types")
            
            for field, count in fields.items():
                types = ", ".join(self.field_types[content_type][field])
                field_table.add_row(field, str(count), types)
            
            console.print(field_table)
        
        # Quality Metrics Summary
        console.print("\n[bold]Quality Metrics Summary:[/bold]")
        quality_table = Table(show_header=True, header_style="bold")
        quality_table.add_column("Metric")
        quality_table.add_column("Average Score")
        quality_table.add_column("Files Below Threshold")
        
        metrics = {
            "Writing Quality": ("quality.style_score", 70),
            "Technical Accuracy": ("quality.technical_score", 80),
            "SEO Score": ("seo.overall_score", 75),
            "Readability": ("readability.flesch_reading_ease", 60),
            "Engagement Potential": ("engagement.target_audience_engagement", 70)
        }
        
        for metric_name, (metric_path, threshold) in metrics.items():
            total_score = 0
            below_threshold = 0
            count = 0
            
            for file_metrics in self.quality_metrics.values():
                try:
                    score = self._get_nested_value(file_metrics, metric_path)
                    if score is not None:
                        total_score += score
                        count += 1
                        if score < threshold:
                            below_threshold += 1
                except (KeyError, TypeError):
                    continue
            
            if count > 0:
                avg_score = round(total_score / count, 2)
                quality_table.add_row(
                    metric_name,
                    str(avg_score),
                    str(below_threshold)
                )
        
        console.print(quality_table)
        
        # Content Clusters
        console.print("\n[bold]Content Clusters:[/bold]")
        cluster_counts = defaultdict(int)
        for cluster_id in self.content_clusters.values():
            cluster_counts[cluster_id] += 1
        
        cluster_table = Table(show_header=True, header_style="bold")
        cluster_table.add_column("Cluster ID")
        cluster_table.add_column("Number of Files")
        
        for cluster_id, count in sorted(cluster_counts.items()):
            cluster_table.add_row(str(cluster_id), str(count))
        
        console.print(cluster_table)
        
        # Missing Required Fields
        if any(self.missing_required.values()):
            console.print("\n[bold]Missing Required Fields:[/bold]")
            for content_type, missing in self.missing_required.items():
                if missing:
                    console.print(f"\n[bold]{content_type}:[/bold]")
                    for field, files in missing.items():
                        if files:
                            console.print(f"  {field}: {len(files)} files")
        
        # Save detailed report
        self._save_detailed_report()
    
    def _get_nested_value(self, d: Dict, path: str) -> Optional[float]:
        """Get value from nested dictionary using dot notation path."""
        try:
            value = d
            for key in path.split('.'):
                value = value[key]
            return float(value)
        except (KeyError, TypeError, ValueError):
            return None
    
    def _save_detailed_report(self):
        """Save detailed analysis results to a JSON file."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": dict(self.total_files),
            "field_usage": dict(self.field_usage),
            "field_types": {k: {f: list(t) for f, t in v.items()} 
                          for k, v in self.field_types.items()},
            "missing_required": dict(self.missing_required),
            "content_clusters": self.content_clusters,
            "quality_metrics": self.quality_metrics
        }
        
        with open('content_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        console.print(f"\n[green]Detailed report saved to content_analysis_report.json[/green]")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze content quality and structure')
    parser.add_argument('--file', help='Analyze a specific file')
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