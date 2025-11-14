"""
Debug Routes Listing - Temporary diagnostic endpoint
For Gate 0 /docs investigation
"""

from fastapi import APIRouter, Request
from typing import List, Dict

router = APIRouter()

@router.get("/_diagnostic/routes", tags=["Diagnostics"])
async def list_routes(request: Request):
    """
    List all registered FastAPI routes for debugging
    
    Returns:
        Dictionary with all registered routes, methods, and paths
    """
    routes = []
    for route in request.app.routes:
        route_info = {
            "path": getattr(route, "path", "N/A"),
            "name": getattr(route, "name", "N/A"),
            "methods": list(getattr(route, "methods", set()))
        }
        routes.append(route_info)
    
    return {
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x["path"]),
        "docs_url": request.app.docs_url,
        "openapi_url": request.app.openapi_url,
        "redoc_url": request.app.redoc_url
    }
