"""
Developer Relations Router
Executive directive: SDK endpoints, quickstart guide, developer onboarding
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from production.sdk_quickstart import sdk_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/devrel",
    tags=["developer-relations"],
    responses={
        200: {"description": "Success"},
        500: {"description": "Internal server error"},
    }
)

@router.get("/quickstart")
async def get_quickstart_guide() -> dict[str, Any]:
    """
    📚 10-MINUTE QUICKSTART GUIDE
    Executive directive: Fast developer onboarding and adoption

    Returns:
        Complete quickstart guide with time-to-value under 10 minutes
    """
    try:
        quickstart_content = sdk_service.generate_ten_minute_quickstart()

        return {
            "message": "10-minute quickstart guide retrieved successfully",
            "quickstart_guide": {
                "title": "Scholarship Discovery API - 10-Minute Quickstart",
                "time_to_value": "Under 10 minutes",
                "content": quickstart_content
            },
            "next_steps": [
                "Create your API key using the billing endpoints",
                "Test basic search with curl or your preferred language",
                "Integrate into your application using our SDK examples",
                "Monitor usage and upgrade tier as needed"
            ]
        }

    except Exception as e:
        logger.error(f"❌ Quickstart guide error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quickstart guide: {str(e)}")

@router.get("/quickstart/markdown", response_class=PlainTextResponse)
async def get_quickstart_markdown():
    """
    📚 QUICKSTART GUIDE (MARKDOWN)
    Executive directive: Raw markdown for documentation sites
    """
    try:
        return PlainTextResponse(
            content=sdk_service.generate_ten_minute_quickstart(),
            media_type="text/markdown"
        )

    except Exception as e:
        logger.error(f"❌ Quickstart markdown error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quickstart markdown")

@router.get("/quickstart/html", response_class=HTMLResponse)
async def get_quickstart_html():
    """
    📚 QUICKSTART GUIDE (HTML)
    Executive directive: User-friendly HTML presentation
    """
    try:
        markdown_content = sdk_service.generate_ten_minute_quickstart()

        # Convert to simple HTML with syntax highlighting
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scholarship API - 10-Minute Quickstart</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #2563eb; border-bottom: 3px solid #e5e7eb; padding-bottom: 10px; }}
        h2 {{ color: #1f2937; margin-top: 30px; }}
        h3 {{ color: #4b5563; }}
        code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
        pre {{ background: #1f2937; color: #f9fafb; padding: 20px; border-radius: 8px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        .step {{ background: #eff6ff; border: 1px solid #dbeafe; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .step h3 {{ margin-top: 0; color: #1d4ed8; }}
        .checklist {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; }}
        .checklist ul {{ margin: 0; }}
        .warning {{ background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; padding: 10px; }}
        .success {{ background: #dcfce7; border: 1px solid #16a34a; border-radius: 8px; padding: 10px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        .emoji {{ font-size: 1.2em; }}
    </style>
</head>
<body>
    <pre style="white-space: pre-wrap; background: none; color: inherit; padding: 0;">{markdown_content}</pre>

    <script>
        // Copy code button functionality
        document.addEventListener('DOMContentLoaded', function() {{
            const codeBlocks = document.querySelectorAll('pre');
            codeBlocks.forEach(block => {{
                const button = document.createElement('button');
                button.textContent = 'Copy';
                button.style.cssText = 'position: absolute; top: 10px; right: 10px; padding: 5px 10px; background: #374151; color: white; border: none; border-radius: 4px; cursor: pointer;';
                block.style.position = 'relative';
                block.appendChild(button);

                button.onclick = () => {{
                    const code = block.textContent.replace('Copy', '').trim();
                    navigator.clipboard.writeText(code);
                    button.textContent = 'Copied!';
                    setTimeout(() => button.textContent = 'Copy', 2000);
                }};
            }});
        }});
    </script>
</body>
</html>"""

        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        logger.error(f"❌ Quickstart HTML error: {e}")
        return HTMLResponse(
            content="<h1>Quickstart guide temporarily unavailable</h1>",
            status_code=500
        )

@router.get("/sdk/curl")
async def get_curl_examples() -> dict[str, Any]:
    """
    🔧 CURL SDK EXAMPLES
    Executive directive: Minimal curl commands for immediate testing

    Returns:
        Complete curl command examples for all API endpoints
    """
    try:
        examples = sdk_service.get_curl_examples()

        return {
            "message": "cURL SDK examples retrieved successfully",
            "language": "curl",
            "description": "Minimal curl commands for immediate API testing",
            "examples": [
                {
                    "name": example.name,
                    "description": example.description,
                    "code": example.code
                }
                for example in examples
            ],
            "getting_started": "Copy and paste any example, replace the API key, and run in your terminal"
        }

    except Exception as e:
        logger.error(f"❌ cURL examples error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cURL examples: {str(e)}")

@router.get("/sdk/javascript")
async def get_javascript_sdk() -> dict[str, Any]:
    """
    🔧 JAVASCRIPT/TYPESCRIPT SDK
    Executive directive: Complete client library for web applications

    Returns:
        JavaScript/TypeScript SDK with React integration examples
    """
    try:
        examples = sdk_service.get_javascript_sdk()

        return {
            "message": "JavaScript/TypeScript SDK retrieved successfully",
            "language": "javascript",
            "description": "Complete TypeScript client library for web applications",
            "examples": [
                {
                    "name": example.name,
                    "description": example.description,
                    "code": example.code
                }
                for example in examples
            ],
            "features": [
                "TypeScript definitions included",
                "Promise-based API",
                "React hooks and components",
                "Automatic rate limit handling",
                "Error handling with retry logic"
            ],
            "installation": "npm install @scholarshipapi/client (coming soon)"
        }

    except Exception as e:
        logger.error(f"❌ JavaScript SDK error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get JavaScript SDK: {str(e)}")

@router.get("/sdk/python")
async def get_python_sdk() -> dict[str, Any]:
    """
    🔧 PYTHON SDK
    Executive directive: Full-featured client for backend integration

    Returns:
        Python SDK with Django integration examples
    """
    try:
        examples = sdk_service.get_python_sdk()

        return {
            "message": "Python SDK retrieved successfully",
            "language": "python",
            "description": "Full-featured Python client for backend integration",
            "examples": [
                {
                    "name": example.name,
                    "description": example.description,
                    "code": example.code
                }
                for example in examples
            ],
            "features": [
                "Type hints included",
                "Built-in error handling",
                "Django and Flask examples",
                "Rate limit monitoring",
                "Automatic retry logic"
            ],
            "installation": "pip install scholarship-api-client (coming soon)"
        }

    except Exception as e:
        logger.error(f"❌ Python SDK error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Python SDK: {str(e)}")

@router.get("/documentation")
async def get_developer_documentation() -> dict[str, Any]:
    """
    📚 COMPLETE DEVELOPER DOCUMENTATION
    Executive directive: Comprehensive developer onboarding experience

    Returns:
        Full developer documentation with SDKs and integration guides
    """
    try:
        documentation = sdk_service.generate_developer_documentation()

        return {
            "message": "Developer documentation retrieved successfully",
            "developer_documentation": documentation,
            "executive_summary": {
                "time_to_value": "Under 10 minutes",
                "supported_languages": ["curl", "JavaScript", "TypeScript", "Python"],
                "framework_integrations": ["React", "Django", "Node.js"],
                "key_benefits": [
                    "Rapid developer onboarding",
                    "Production-ready code examples",
                    "Comprehensive error handling",
                    "Rate limiting transparency"
                ]
            }
        }

    except Exception as e:
        logger.error(f"❌ Developer documentation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get developer documentation: {str(e)}")

@router.get("/examples/{framework}")
async def get_framework_examples(framework: str) -> dict[str, Any]:
    """
    🔧 FRAMEWORK-SPECIFIC EXAMPLES
    Executive directive: Tailored integration guides for popular frameworks

    Args:
        framework: Framework name (react, django, express, flask, vue, angular)

    Returns:
        Framework-specific integration examples and best practices
    """
    try:
        framework_examples = {
            "react": {
                "title": "React Integration",
                "description": "Custom hooks and components for scholarship search",
                "examples": [
                    {
                        "name": "useScholarshipSearch Hook",
                        "description": "React hook with error handling and loading states",
                        "code": "// See JavaScript SDK examples for complete React integration"
                    }
                ]
            },
            "django": {
                "title": "Django Integration",
                "description": "Views, models, and middleware for Django applications",
                "examples": [
                    {
                        "name": "ScholarshipSearchView",
                        "description": "Django class-based view with caching",
                        "code": "// See Python SDK examples for complete Django integration"
                    }
                ]
            },
            "express": {
                "title": "Express.js Integration",
                "description": "Middleware and route handlers for Node.js/Express",
                "examples": [
                    {
                        "name": "Express Middleware",
                        "description": "API proxy middleware with rate limiting",
                        "code": '''
const express = require('express');
const { ScholarshipAPIClient } = require('./scholarship-client');

const scholarshipMiddleware = (req, res, next) => {
  req.scholarshipAPI = new ScholarshipAPIClient(process.env.SCHOLARSHIP_API_KEY);
  next();
};

app.use('/api/scholarships', scholarshipMiddleware, (req, res) => {
  const { q, ...filters } = req.query;
  req.scholarshipAPI.search(q, filters)
    .then(results => res.json(results))
    .catch(error => res.status(500).json({ error: error.message }));
});'''
                    }
                ]
            },
            "flask": {
                "title": "Flask Integration",
                "description": "Flask routes and blueprints with error handling",
                "examples": [
                    {
                        "name": "Flask Blueprint",
                        "description": "Scholarship search blueprint with caching",
                        "code": '''
from flask import Blueprint, request, jsonify
from scholarship_api_client import ScholarshipAPIClient

scholarship_bp = Blueprint('scholarships', __name__)
client = ScholarshipAPIClient(os.environ['SCHOLARSHIP_API_KEY'])

@scholarship_bp.route('/search')
def search():
    query = request.args.get('q', '')
    try:
        results = client.search_scholarships(query, **request.args)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500'''
                    }
                ]
            }
        }

        if framework not in framework_examples:
            available = list(framework_examples.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Framework '{framework}' not found. Available: {', '.join(available)}"
            )

        return {
            "message": f"{framework.title()} integration examples retrieved successfully",
            "framework": framework,
            "integration_guide": framework_examples[framework],
            "additional_resources": {
                "full_documentation": "/devrel/documentation",
                "quickstart_guide": "/devrel/quickstart",
                "support": "support@scholarshipapi.com"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Framework examples error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get {framework} examples: {str(e)}")
