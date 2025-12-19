"""
Scholarship API SDK for A5 (Student Pilot) Integration
=======================================================

P0 Revenue Unblock: Provides minimal SDK for A5 to integrate with A2.

Usage:
    from sdk.a5_integration import ScholarshipAPIClient
    
    client = ScholarshipAPIClient()
    scholarships = client.search(q="engineering", min_amount=1000)
    summary = client.get_search_analytics()
"""

import os
from typing import Any
import httpx

class ScholarshipAPIClient:
    """
    SDK client for A5 (Student Pilot) to interact with A2 (Scholarship API).
    
    Endpoints:
    - GET /api/v1/scholarships/public - Public scholarship feed
    - GET /api/v1/search - Search with filters
    - GET /api/v1/analytics/search-summary - Search analytics for dashboards
    """
    
    def __init__(
        self, 
        base_url: str = None,
        timeout: float = 10.0
    ):
        self.base_url = base_url or os.getenv(
            "A2_API_URL", 
            "https://scholarship-api-jamarrlmayes.replit.app"
        )
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "X-App-Label": "student_pilot https://student-pilot-jamarrlmayes.replit.app"
        }
    
    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """Make HTTP request to A2 API"""
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
    
    def get_public_scholarships(
        self,
        q: str = None,
        min_amount: float = None,
        deadline_before: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict[str, Any]:
        """
        Get public scholarship feed with optional filters.
        
        Args:
            q: Keyword search
            min_amount: Minimum scholarship amount
            deadline_before: ISO date string for deadline filter
            limit: Number of results (max 100)
            offset: Pagination offset
        
        Returns:
            dict with 'items', 'total', 'etag' keys
        """
        params = {"limit": limit, "offset": offset}
        if q:
            params["q"] = q
        if min_amount:
            params["min_amount"] = min_amount
        if deadline_before:
            params["deadline_before"] = deadline_before
        
        return self._request("GET", "/api/v1/scholarships/public", params=params)
    
    def search(
        self,
        q: str = None,
        min_amount: float = None,
        max_amount: float = None,
        fields_of_study: list[str] = None,
        scholarship_types: list[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict[str, Any]:
        """
        Search scholarships with advanced filters.
        
        Args:
            q: Search query keyword
            min_amount: Minimum award amount
            max_amount: Maximum award amount  
            fields_of_study: Filter by field (STEM, ARTS, BUSINESS, etc.)
            scholarship_types: Filter by type (MERIT, NEED_BASED, etc.)
            limit: Results per page
            offset: Pagination offset
        
        Returns:
            dict with 'items', 'total', 'took_ms', 'filters' keys
        """
        params = {"limit": limit, "offset": offset}
        if q:
            params["q"] = q
        if min_amount:
            params["min_amount"] = min_amount
        if max_amount:
            params["max_amount"] = max_amount
        if fields_of_study:
            params["fields_of_study"] = fields_of_study
        if scholarship_types:
            params["scholarship_types"] = scholarship_types
        
        return self._request("GET", "/api/v1/search", params=params)
    
    def get_search_analytics(self, days: int = 7) -> dict[str, Any]:
        """
        Get search analytics summary for dashboard integration.
        
        Args:
            days: Number of days to analyze (1-90)
        
        Returns:
            dict with 'total_searches', 'top_queries', 'avg_response_time_ms' keys
        """
        return self._request("GET", f"/api/v1/analytics/search-summary?days={days}")
    
    def get_scholarship_by_id(self, scholarship_id: str) -> dict[str, Any]:
        """Get single scholarship by ID"""
        return self._request("GET", f"/api/v1/scholarships/{scholarship_id}")
    
    def health_check(self) -> dict[str, Any]:
        """Check A2 API health"""
        return self._request("GET", "/health")


# Convenience functions for quick integration
def get_scholarships(q: str = None, limit: int = 20) -> list[dict]:
    """Quick helper to get scholarships"""
    client = ScholarshipAPIClient()
    result = client.get_public_scholarships(q=q, limit=limit)
    return result.get("items", [])


def get_search_stats(days: int = 7) -> dict:
    """Quick helper to get search statistics"""
    client = ScholarshipAPIClient()
    return client.get_search_analytics(days=days)


# Example usage and test
if __name__ == "__main__":
    client = ScholarshipAPIClient()
    
    print("=== A5 SDK Test ===")
    
    print("\n1. Health check:")
    health = client.health_check()
    print(f"   Status: {health.get('status', 'unknown')}")
    
    print("\n2. Public scholarships:")
    public = client.get_public_scholarships(limit=3)
    print(f"   Total: {public.get('total', 0)}")
    
    print("\n3. Search analytics:")
    analytics = client.get_search_analytics(days=7)
    print(f"   Total searches: {analytics.get('total_searches', 0)}")
    print(f"   Status: {analytics.get('status', 'unknown')}")
    
    print("\n=== SDK Ready for A5 Integration ===")
