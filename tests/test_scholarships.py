"""
Test Suite for Scholarship API Endpoints
Comprehensive testing for scholarship functionality
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

# Test authentication helper
def get_test_auth_headers():
    """Get authentication headers for testing"""
    # Mock authentication for tests - in development mode with PUBLIC_READ_ENDPOINTS
    return {}

@pytest.fixture(scope="function")
def enable_public_endpoints():
    """Enable public read endpoints for testing"""
    with patch("config.settings.settings.public_read_endpoints", True):
        yield

class TestScholarshipEndpoints:
    """Test scholarship CRUD and search operations"""
    
    def test_get_all_scholarships(self, enable_public_endpoints):
        """Test retrieving all scholarships"""
        response = client.get("/api/v1/scholarships")
        assert response.status_code == 200
        data = response.json()
        assert "scholarships" in data
        assert "total_count" in data
        assert data["total_count"] > 0
    
    def test_get_scholarship_by_id(self):
        """Test retrieving a specific scholarship"""
        response = client.get("/api/v1/scholarships/sch_001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sch_001"
        assert "name" in data
        assert "eligibility_criteria" in data
    
    def test_get_nonexistent_scholarship(self):
        """Test retrieving non-existent scholarship returns 404"""
        response = client.get("/api/v1/scholarships/nonexistent")
        assert response.status_code == 404
        data = response.json()
        # Updated for unified error format
        assert data["code"] == "NOT_FOUND"
    
    def test_search_scholarships_by_keyword(self, enable_public_endpoints):
        """Test searching scholarships by keyword"""
        response = client.get("/api/v1/scholarships?keyword=engineering")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        # Verify results contain engineering-related scholarships
        scholarship_names = [s["name"].lower() for s in data["scholarships"]]
        assert any("engineering" in name for name in scholarship_names)
    
    def test_search_scholarships_by_gpa(self, enable_public_endpoints):
        """Test filtering scholarships by GPA requirement - user qualifies if they meet/exceed scholarship requirement"""
        response = client.get("/api/v1/scholarships?min_gpa=3.5")
        assert response.status_code == 200
        data = response.json()
        # Verify all results are scholarships the user qualifies for (user's 3.5 GPA >= scholarship requirement)
        for scholarship in data["scholarships"]:
            criteria = scholarship["eligibility_criteria"]
            if criteria["min_gpa"] is not None:
                # User with 3.5 GPA should qualify (3.5 >= scholarship requirement)
                assert 3.5 >= criteria["min_gpa"], f"User with 3.5 GPA should qualify for scholarship requiring {criteria['min_gpa']}"
    
    def test_search_scholarships_pagination(self, enable_public_endpoints):
        """Test pagination in scholarship search"""
        # Get first page
        response1 = client.get("/api/v1/scholarships?limit=5&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = client.get("/api/v1/scholarships?limit=5&offset=5")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify pages have different scholarships
        ids1 = {s["id"] for s in data1["scholarships"]}
        ids2 = {s["id"] for s in data2["scholarships"]}
        assert ids1.isdisjoint(ids2)  # No overlap
    
    def test_search_invalid_pagination(self):
        """Test invalid pagination parameters"""
        response = client.get("/api/v1/scholarships?limit=0")
        assert response.status_code == 422
        
        response = client.get("/api/v1/scholarships?offset=-1")
        assert response.status_code == 422

class TestEligibilityChecking:
    """Test eligibility checking functionality"""
    
    def test_eligibility_check_valid(self):
        """Test eligibility check with valid data"""
        user_profile = {
            "id": "test_user",
            "gpa": 3.8,
            "grade_level": "undergraduate",
            "field_of_study": "engineering",
            "citizenship": "US",
            "state_of_residence": "CA",
            "age": 20,
            "financial_need": False
        }
        
        response = client.post(
            "/api/v1/scholarships/eligibility-check",
            json={
                "user_profile": user_profile,
                "scholarship_id": "sch_001"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
        assert "match_score" in data
        assert "reasons" in data
        assert 0 <= data["match_score"] <= 1
    
    def test_bulk_eligibility_check(self):
        """Test bulk eligibility checking"""
        user_profile = {
            "id": "test_user",
            "gpa": 3.5,
            "grade_level": "undergraduate",
            "field_of_study": "engineering",
            "citizenship": "US",
            "state_of_residence": "CA",
            "age": 21,
            "financial_need": False
        }
        
        response = client.post(
            "/api/v1/scholarships/bulk-eligibility-check",
            json={
                "user_profile": user_profile,
                "scholarship_ids": ["sch_001", "sch_002", "sch_003"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Response is a direct list, not wrapped in "results"
        assert isinstance(data, list)
        assert len(data) == 3
        
        for result in data:
            assert "scholarship_id" in result
            assert "eligible" in result
            assert "match_score" in result
    
    def test_eligibility_check_invalid_user(self):
        """Test eligibility check with invalid user profile"""
        response = client.post(
            "/api/v1/scholarships/eligibility-check",
            json={
                "user_profile": {"invalid": "data"},
                "scholarship_id": "sch_001"
            }
        )
        assert response.status_code == 422
        data = response.json()
        # Updated for unified error format
        assert data["code"] == "VALIDATION_ERROR"
    
    def test_bulk_eligibility_too_many_scholarships(self):
        """Test bulk eligibility check with too many scholarships"""
        user_profile = {
            "id": "test_user",
            "gpa": 3.5,
            "grade_level": "undergraduate",
            "field_of_study": "engineering",
            "citizenship": "US",
            "state_of_residence": "CA",
            "age": 21,
            "financial_need": False
        }
        
        # Try with more than 50 scholarships
        scholarship_ids = [f"sch_{i:03d}" for i in range(1, 52)]
        
        response = client.post(
            "/api/v1/scholarships/bulk-eligibility-check",
            json={
                "user_profile": user_profile,
                "scholarship_ids": scholarship_ids
            }
        )
        assert response.status_code == 400

class TestRecommendations:
    """Test recommendation functionality"""
    
    def test_get_recommendations(self, enable_public_endpoints):
        """Test getting personalized recommendations"""
        # Use POST endpoint with user profile
        user_profile = {
            "id": "test_user",
            "gpa": 3.5,
            "grade_level": "undergraduate",
            "field_of_study": "engineering",
            "citizenship": "US",
            "state_of_residence": "CA",
            "age": 21,
            "financial_need": False
        }
        
        response = client.post("/api/v1/scholarships/recommendations", json={
            "user_profile": user_profile,
            "max_results": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "user_profile_summary" in data
        
        # Verify recommendations have required fields
        if data["recommendations"]:
            rec = data["recommendations"][0]
            assert "scholarship" in rec
            assert "recommendation_score" in rec
            assert "eligibility" in rec
    
    def test_recommendations_with_filters(self, enable_public_endpoints):
        """Test recommendations with additional filters"""
        user_profile = {
            "id": "test_user",
            "gpa": 3.5,
            "grade_level": "undergraduate",
            "field_of_study": "engineering",
            "citizenship": "US",
            "state_of_residence": "CA",
            "age": 21,
            "financial_need": False
        }
        
        response = client.post("/api/v1/scholarships/recommendations", json={
            "user_profile": user_profile,
            "max_results": 5,
            "filters": {
                "min_amount": 5000
            }
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify recommendations exist
        assert "recommendations" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])