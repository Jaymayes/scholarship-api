"""
Canonical Scholarship Pages Router
Serves SEO-optimized scholarship pages at their canonical URLs for search engine indexing.
"""
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
import logging
import json
import re

from production.auto_page_maker_seo import seo_service, ScholarshipPage

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["scholarship-pages"],
    responses={
        200: {"description": "SEO-optimized HTML page"},
        404: {"description": "Scholarship page not found"},
        500: {"description": "Internal server error"},
    }
)

def render_scholarship_page_html(page: ScholarshipPage) -> str:
    """
    Render ScholarshipPage object to complete SEO-optimized HTML
    
    Args:
        page: ScholarshipPage object with all SEO data
        
    Returns:
        Complete HTML string with proper SEO metadata
    """
    # Escape HTML content for security
    def escape_html(text: str) -> str:
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))
    
    # Generate content sections HTML
    content_html = ""
    for block in page.content_blocks:
        content_html += f"""
        <section class="content-section" id="{block.get('section', 'section')}">
            <h2>{escape_html(block['heading'])}</h2>
            <p>{escape_html(block['content'])}</p>
        </section>
        """
    
    # Generate internal links HTML
    internal_links_html = ""
    if page.internal_links:
        internal_links_html = """
        <section class="internal-links">
            <h3>Related Scholarships</h3>
            <div class="link-grid">
        """
        for link in page.internal_links:
            internal_links_html += f'<a href="{escape_html(link["url"])}" class="related-link">{escape_html(link["text"])}</a>'
        
        internal_links_html += """
            </div>
        </section>
        """
    
    # Generate keywords meta tag
    keywords_meta = ""
    if page.keywords:
        keywords_meta = f'<meta name="keywords" content="{escape_html(", ".join(page.keywords))}">'
    
    # Complete HTML document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(page.title)}</title>
    <meta name="description" content="{escape_html(page.meta_description)}">
    {keywords_meta}
    <link rel="canonical" href="{escape_html(page.canonical_url)}">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="{escape_html(page.title)}">
    <meta property="og:description" content="{escape_html(page.meta_description)}">
    <meta property="og:url" content="{escape_html(page.canonical_url)}">
    <meta property="og:type" content="website">
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
{json.dumps(page.structured_data, indent=2)}
    </script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #ffffff;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        main {{
            padding: 3rem 0;
        }}
        
        .content-section {{
            margin-bottom: 3rem;
            background: #f8fafc;
            padding: 2rem;
            border-radius: 12px;
            border-left: 4px solid #3b82f6;
        }}
        
        .content-section h2 {{
            color: #1e40af;
            font-size: 1.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }}
        
        .content-section p {{
            font-size: 1.1rem;
            line-height: 1.7;
        }}
        
        .internal-links {{
            background: #eff6ff;
            padding: 2rem;
            border-radius: 12px;
            margin-top: 3rem;
        }}
        
        .internal-links h3 {{
            color: #1e40af;
            margin-bottom: 1.5rem;
            font-size: 1.3rem;
        }}
        
        .link-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }}
        
        .related-link {{
            display: block;
            padding: 1rem 1.5rem;
            background: white;
            color: #2563eb;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.2s ease;
            border: 1px solid #e5e7eb;
            font-weight: 500;
        }}
        
        .related-link:hover {{
            background: #dbeafe;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        
        footer {{
            background: #1f2937;
            color: white;
            text-align: center;
            padding: 2rem 0;
            margin-top: 4rem;
        }}
        
        .breadcrumb {{
            padding: 1rem 0;
            background: #f1f5f9;
        }}
        
        .breadcrumb a {{
            color: #2563eb;
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            
            .container {{
                padding: 0 15px;
            }}
            
            .content-section {{
                padding: 1.5rem;
            }}
            
            .link-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <nav class="breadcrumb">
        <div class="container">
            <a href="/">Home</a> &gt; <a href="/scholarships">Scholarships</a> &gt; {escape_html(page.h1_title)}
        </div>
    </nav>
    
    <header>
        <div class="container">
            <h1>{escape_html(page.h1_title)}</h1>
            <p class="subtitle">Find and apply for scholarship opportunities</p>
        </div>
    </header>
    
    <main>
        <div class="container">
            {content_html}
            {internal_links_html}
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2025 Scholarship Discovery API. All rights reserved. | <a href="/search" style="color: #93c5fd;">Search Scholarships</a> | <a href="/sitemap.xml" style="color: #93c5fd;">Sitemap</a></p>
        </div>
    </footer>
</body>
</html>"""
    
    return html_content

@router.get("/scholarships/{slug_and_id}", response_class=HTMLResponse)
async def get_scholarship_detail_page(
    slug_and_id: str = Path(..., description="URL slug and ID in format: slug-sch_id_123")
) -> HTMLResponse:
    """
    🎯 SERVE CANONICAL SCHOLARSHIP DETAIL PAGE
    
    Serves individual scholarship pages at their canonical URLs for SEO indexing.
    URL format: /scholarships/{slug}-{scholarship_id}
    
    Args:
        slug_and_id: Combined slug and ID (e.g., "engineering-excellence-scholarship-sch_eng_001")
        
    Returns:
        Complete HTML page with SEO metadata
    """
    try:
        # Extract scholarship ID from slug_and_id
        # Format: "engineering-excellence-scholarship-sch_eng_001"
        scholarship_id = None
        
        # Look for scholarship ID pattern at the end
        id_match = re.search(r'-(sch_[a-zA-Z0-9_]+)$', slug_and_id)
        if id_match:
            scholarship_id = id_match.group(1)
        else:
            raise HTTPException(status_code=404, detail="Invalid scholarship URL format")
        
        # Find matching scholarship
        scholarship = None
        for s in seo_service.sample_scholarships:
            if s["id"] == scholarship_id:
                scholarship = s
                break
        
        if not scholarship:
            # Try to match base ID (in case of variations)
            base_id = scholarship_id.split('_var_')[0] if '_var_' in scholarship_id else scholarship_id
            for s in seo_service.sample_scholarships:
                if s["id"] == base_id:
                    scholarship = s.copy()
                    scholarship["id"] = scholarship_id  # Use the variant ID
                    break
        
        if not scholarship:
            logger.warning(f"Scholarship not found for ID: {scholarship_id}")
            raise HTTPException(status_code=404, detail="Scholarship not found")
        
        # Generate the scholarship page
        page = seo_service.generate_scholarship_detail_page(scholarship)
        
        # Render to HTML
        html_content = render_scholarship_page_html(page)
        
        logger.info(f"✅ Served scholarship page: {scholarship_id}")
        return HTMLResponse(content=html_content, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error serving scholarship page {slug_and_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load scholarship page")

@router.get("/scholarships/category/{category}", response_class=HTMLResponse)
async def get_category_listing_page(
    category: str = Path(..., description="Category name (e.g., engineering, computer-science)")
) -> HTMLResponse:
    """
    📂 SERVE CANONICAL CATEGORY LISTING PAGE
    
    Serves category aggregation pages at their canonical URLs for SEO indexing.
    URL format: /scholarships/category/{category}
    
    Args:
        category: Category name or slug
        
    Returns:
        Complete HTML page with category scholarship listings
    """
    try:
        # Convert URL slug back to category name
        category_name = category.replace('-', ' ').title()
        
        # Find scholarships for this category
        category_scholarships = []
        for s in seo_service.sample_scholarships:
            if s["field_of_study"].lower().replace(' ', '-') == category.lower():
                category_scholarships.append(s)
        
        # If no exact match, try partial matching
        if not category_scholarships:
            for s in seo_service.sample_scholarships:
                if category.lower() in s["field_of_study"].lower():
                    category_scholarships.append(s)
        
        # Fallback to all scholarships if none found
        if not category_scholarships:
            category_scholarships = seo_service.sample_scholarships[:3]
            category_name = category.replace('-', ' ').title()
        
        # Generate the category page
        page = seo_service.generate_category_listing_page(category_name, category_scholarships)
        
        # Render to HTML
        html_content = render_scholarship_page_html(page)
        
        logger.info(f"✅ Served category page: {category}")
        return HTMLResponse(content=html_content, status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Error serving category page {category}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load category page")

@router.get("/scholarships/amount/{amount_range}", response_class=HTMLResponse)
async def get_amount_range_page(
    amount_range: str = Path(..., description="Amount range in format: min-max (e.g., 5000-10000)")
) -> HTMLResponse:
    """
    💰 SERVE CANONICAL AMOUNT RANGE PAGE
    
    Serves amount-based scholarship pages at their canonical URLs for SEO indexing.
    URL format: /scholarships/amount/{min}-{max}
    
    Args:
        amount_range: Amount range string (e.g., "5000-10000")
        
    Returns:
        Complete HTML page with scholarships in the amount range
    """
    try:
        # Parse amount range
        try:
            parts = amount_range.split('-')
            if len(parts) != 2:
                raise ValueError("Invalid range format")
            min_amount = int(parts[0])
            max_amount = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=404, detail="Invalid amount range format")
        
        # Find scholarships in this amount range
        range_scholarships = []
        for s in seo_service.sample_scholarships:
            if min_amount <= s["amount"] <= max_amount:
                range_scholarships.append(s)
        
        # If no scholarships in exact range, find closest ones
        if not range_scholarships:
            # Get scholarships closest to the range
            all_scholarships = sorted(seo_service.sample_scholarships, 
                                    key=lambda x: abs(x["amount"] - (min_amount + max_amount) / 2))
            range_scholarships = all_scholarships[:3]
        
        # Generate the amount range page
        page = seo_service.generate_amount_range_page(min_amount, max_amount, range_scholarships)
        
        # Render to HTML
        html_content = render_scholarship_page_html(page)
        
        logger.info(f"✅ Served amount range page: {amount_range}")
        return HTMLResponse(content=html_content, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error serving amount range page {amount_range}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load amount range page")