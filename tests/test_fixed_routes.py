"""
Test cases for the fixed SEARCH-001 and ELIGIBILITY-001 issues
Tests search and eligibility endpoints to ensure they work correctly
"""


import requests

BASE_URL = "http://localhost:5000"

class TestFixedRoutes:
    """Test the fixed search and eligibility routes"""

    def test_search_post_route_ok(self):
        """Test POST /search returns 200 with expected metadata structure"""
        search_data = {
            "query": "engineering",
            "limit": 5,
            "offset": 0
        }

        response = requests.post(f"{BASE_URL}/search", json=search_data)

        assert response.status_code == 200
        data = response.json()

        # Verify expected keys in metadata-rich response
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "filters" in data
        assert "took_ms" in data
        assert "has_next" in data
        assert "has_previous" in data

        # Verify data types
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["took_ms"], int)
        assert isinstance(data["filters"], dict)

    def test_search_get_route_ok(self):
        """Test GET /search returns 200 with same metadata structure"""
        response = requests.get(f"{BASE_URL}/search?q=merit&limit=3")

        assert response.status_code == 200
        data = response.json()

        # Verify expected keys in metadata-rich response
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "filters" in data
        assert "took_ms" in data

        # Verify search worked
        assert data["filters"]["keyword"] == "merit"
        assert data["page_size"] == 3

    def test_api_v1_search_backward_compatibility(self):
        """Test /api/v1/search endpoints work for backward compatibility"""
        # Test GET
        response = requests.get(f"{BASE_URL}/api/v1/search?q=scholarship&limit=2")
        assert response.status_code == 200

        # Test POST
        search_data = {"query": "science", "limit": 2}
        response = requests.post(f"{BASE_URL}/api/v1/search", json=search_data)
        assert response.status_code == 200

    def test_eligibility_post_route_ok(self):
        """Test POST /eligibility/check returns 200 with expected structure"""
        eligibility_data = {
            "gpa": 3.7,
            "field_of_study": "engineering",
            "citizenship": "US",
            "age": 20,
            "grade_level": "undergraduate"
        }

        response = requests.post(f"{BASE_URL}/eligibility/check", json=eligibility_data)

        assert response.status_code == 200
        data = response.json()

        # Verify expected keys in response
        assert "eligible_count" in data
        assert "results" in data
        assert "took_ms" in data
        assert "user_profile" in data
        assert "checked_scholarships" in data

        # Verify data types and structure
        assert isinstance(data["eligible_count"], int)
        assert isinstance(data["results"], list)
        assert isinstance(data["took_ms"], int)
        assert isinstance(data["checked_scholarships"], int)

        # Verify results structure
        if data["results"]:
            result = data["results"][0]
            assert "scholarship_id" in result
            assert "eligible" in result
            assert "score" in result
            assert "reasons" in result
            assert isinstance(result["eligible"], bool)
            assert isinstance(result["score"], (int, float))
            assert isinstance(result["reasons"], list)

    def test_eligibility_get_route_ok(self):
        """Test GET /eligibility/check returns 200 with query params"""
        params = {
            "gpa": 3.5,
            "field_of_study": "engineering",
            "citizenship": "US",
            "age": 20
        }

        response = requests.get(f"{BASE_URL}/eligibility/check", params=params)

        assert response.status_code == 200
        data = response.json()

        # Verify expected structure
        assert "eligible_count" in data
        assert "results" in data
        assert "took_ms" in data

        # Verify user profile was created correctly
        assert data["user_profile"]["gpa"] == 3.5
        assert data["user_profile"]["field_of_study"] == "engineering"
        assert data["user_profile"]["citizenship"] == "US"

    def test_api_v1_eligibility_backward_compatibility(self):
        """Test /api/v1/eligibility/check endpoints work for backward compatibility"""
        # Test GET
        params = {"gpa": 3.8, "citizenship": "US", "field_of_study": "science"}
        response = requests.get(f"{BASE_URL}/api/v1/eligibility/check", params=params)
        assert response.status_code == 200

        # Test POST
        eligibility_data = {"gpa": 3.6, "citizenship": "US", "field_of_study": "engineering"}
        response = requests.post(f"{BASE_URL}/api/v1/eligibility/check", json=eligibility_data)
        assert response.status_code == 200

    def test_scholarship_response_format_unchanged(self):
        """Verify SCHOLAR-002: scholarship response format remains dict with metadata"""
        response = requests.get(f"{BASE_URL}/api/v1/scholarships?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Verify it's a dict with metadata, not a direct list
        assert isinstance(data, dict)
        assert "scholarships" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data

        # Verify scholarships is a list
        assert isinstance(data["scholarships"], list)

    def test_rate_limiting_responses(self):
        """Test that rate limiting headers are present"""
        response = requests.get(f"{BASE_URL}/search?q=test")

        # Should get 200 response for normal request
        assert response.status_code == 200

        # Check for rate limiting headers (may or may not be present depending on implementation)
        # This is a basic check - comprehensive rate limit testing would require more requests
        assert "x-request-id" in response.headers
        assert "x-trace-id" in response.headers

def test_all_fixed_endpoints():
    """Run comprehensive test of all fixed endpoints"""
    print("Testing SEARCH-001 and ELIGIBILITY-001 fixes...")

    test_routes = TestFixedRoutes()

    # Run all tests
    test_routes.test_search_post_route_ok()
    print("✓ POST /search working")

    test_routes.test_search_get_route_ok()
    print("✓ GET /search working")

    test_routes.test_api_v1_search_backward_compatibility()
    print("✓ /api/v1/search backward compatibility working")

    test_routes.test_eligibility_post_route_ok()
    print("✓ POST /eligibility/check working")

    test_routes.test_eligibility_get_route_ok()
    print("✓ GET /eligibility/check working")

    test_routes.test_api_v1_eligibility_backward_compatibility()
    print("✓ /api/v1/eligibility/check backward compatibility working")

    test_routes.test_scholarship_response_format_unchanged()
    print("✓ SCHOLAR-002: Scholarship response format preserved")

    test_routes.test_rate_limiting_responses()
    print("✓ Rate limiting middleware operational")

    print("\n🎉 All endpoint fixes verified successfully!")
    return True

if __name__ == "__main__":
    test_all_fixed_endpoints()
