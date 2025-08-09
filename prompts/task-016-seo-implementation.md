# Task 016: Add SEO Metadata and Structured Data

## Context
The garden features are complete with sliding panels, content relationships, and statistics dashboard. Now we need to ensure the garden is discoverable and properly indexed by search engines. The growth stage system provides unique opportunities for SEO optimization, where content maturity affects indexing priority.

## Objective
Implement comprehensive SEO optimization including dynamic metadata generation, Schema.org structured data, Open Graph tags, and growth-stage-aware indexing strategies. Every page should be optimized for search engines while maintaining the garden philosophy.

## Test Requirements

Write these tests FIRST before any implementation:

### 1. Metadata Generation Tests (`tests/test_seo_metadata.py`)
```python
async def test_unique_meta_tags():
    """Test each page has unique title and description"""
    # Load multiple content pages
    # Verify unique meta titles (max 60 chars)
    # Verify unique descriptions (max 155 chars)
    # Test no duplicate metadata
    
async def test_metadata_quality():
    """Test metadata meets SEO best practices"""
    # Test title includes primary keyword
    # Test description is compelling
    # Test no keyword stuffing
    # Verify character limits enforced
    
async def test_growth_stage_metadata():
    """Test growth stage affects metadata"""
    # Seedling content has different meta strategy
    # Evergreen content prioritized
    # Test appropriate index/noindex tags
```

### 2. Structured Data Tests (`tests/test_structured_data.py`)
```python
async def test_schema_org_markup():
    """Test Schema.org JSON-LD implementation"""
    # Verify BlogPosting schema on notes
    # Test LearningResource schema for tutorials
    # Validate JSON-LD syntax
    # Test required properties present
    
async def test_breadcrumb_schema():
    """Test breadcrumb structured data"""
    # Verify BreadcrumbList schema
    # Test correct hierarchy
    # Validate position numbers
    
async def test_garden_path_schema():
    """Test Course schema for garden paths"""
    # Verify Course schema on paths
    # Test duration calculations
    # Validate learning objectives
```

### 3. Open Graph Tests (`tests/test_open_graph.py`)
```python
async def test_og_tags_present():
    """Test Open Graph tags on all content"""
    # Verify og:title, og:description
    # Test og:image with fallbacks
    # Verify og:url canonical
    # Test og:type appropriate
    
async def test_twitter_cards():
    """Test Twitter Card implementation"""
    # Verify twitter:card type
    # Test summary_large_image for featured content
    # Validate image dimensions
    
async def test_social_preview():
    """Test social media preview quality"""
    # Test image generation/selection
    # Verify text truncation
    # Test special characters handling
```

### 4. Sitemap Tests (`tests/test_sitemap.py`)
```python
async def test_sitemap_generation():
    """Test dynamic sitemap.xml generation"""
    # Verify all content included
    # Test lastmod dates accurate
    # Verify priority by growth stage
    # Test XML validity
    
async def test_sitemap_priorities():
    """Test growth stage affects priorities"""
    # Evergreen: 1.0 priority
    # Growing: 0.8 priority
    # Budding: 0.6 priority
    # Seedling: 0.4 priority
    
async def test_sitemap_performance():
    """Test sitemap generation performance"""
    # Test with 1000+ pages
    # Verify generation < 1 second
    # Test caching works
```

### 5. Indexing Control Tests (`tests/test_indexing.py`)
```python
async def test_robots_meta_tags():
    """Test indexing directives based on content"""
    # Seedlings: noindex, follow
    # Evergreen: index, follow, priority
    # Test robots.txt compliance
    
async def test_canonical_urls():
    """Test canonical URL implementation"""
    # Verify canonical on every page
    # Test no duplicate content issues
    # Verify absolute URLs used
```

## Implementation Hints

1. **SEO Metadata Class**:
   ```python
   class SEOMetadata(BaseModel):
       title: str  # Max 60 chars
       description: str  # Max 155 chars
       keywords: List[str]
       canonical_url: str
       og_image: Optional[str]
       index_policy: str  # "index" or "noindex"
       
   def generate_for_content(content):
       # Smart generation based on content type
       # Consider growth stage
       # Include primary keywords
   ```

2. **Structured Data Templates**:
   ```html
   <script type="application/ld+json">
   {
     "@context": "https://schema.org",
     "@type": "BlogPosting",
     "headline": "{{ seo.title }}",
     "datePublished": "{{ content.planted }}",
     "dateModified": "{{ content.last_tended }}",
     "author": {
       "@type": "Person",
       "name": "{{ author }}"
     }
   }
   </script>
   ```

3. **Growth Stage SEO Strategy**:
   ```python
   GROWTH_STAGE_SEO = {
       "seedling": {
           "index": "noindex",
           "priority": 0.4,
           "changefreq": "daily"
       },
       "evergreen": {
           "index": "index",
           "priority": 1.0,
           "changefreq": "monthly"
       }
   }
   ```

4. **Performance Optimizations**:
   - Cache generated metadata
   - Lazy load Open Graph images
   - Compress structured data
   - Use CDN for og:image

## Integration Points

- **Content Models**: Uses growth stages from Task 002
- **URL Structure**: Leverages clean URLs from Task 010
- **Templates**: Integrates with all page templates
- **RSS Feed**: Enhances existing feed with metadata
- **Analytics**: Tracks SEO performance metrics

## Acceptance Criteria Checklist

Before marking this task complete, ensure:

- [ ] All tests written first and failing appropriately
- [ ] Every page has unique meta title and description
- [ ] Schema.org structured data validates correctly
- [ ] Open Graph tags present on all content
- [ ] Twitter Cards configured properly
- [ ] Dynamic sitemap.xml generates with priorities
- [ ] Growth stage affects indexing decisions
- [ ] Canonical URLs implemented everywhere
- [ ] robots.txt properly configured
- [ ] RSS feed enhanced with categories
- [ ] All structured data validates in testing tools
- [ ] No SEO errors in Google Search Console simulator

## Resources

- [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Schema.org Documentation](https://schema.org/)
- [Open Graph Protocol](https://ogp.me/)
- [Twitter Cards Documentation](https://developer.twitter.com/en/docs/twitter-for-websites/cards)
- [Structured Data Testing Tool](https://developers.google.com/search/docs/advanced/structured-data)

## Expected Deliverables

1. SEOMetadata class with smart generation
2. Structured data templates for all content types
3. Dynamic sitemap generator with caching
4. Open Graph image handling system
5. Comprehensive SEO test suite
6. Documentation of SEO strategy

## SEO Goals

- Achieve rich snippets in search results
- Improve organic traffic by 20%
- Pass all Core Web Vitals
- Achieve featured snippets for evergreen content
- Enable knowledge graph inclusion

## Performance Requirements

- Metadata generation < 10ms per page
- Sitemap generation < 1 second for 1000 pages
- Zero impact on page load time
- Structured data < 10KB per page

Remember: Good SEO enhances discoverability without compromising the garden experience!