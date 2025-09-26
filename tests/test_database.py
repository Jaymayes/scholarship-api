"""
Test Suite for Database Integration
Phase 2: Testing PostgreSQL integration and data persistence
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from models.database import SessionLocal
from services.database_service import DatabaseService

client = TestClient(app)

def get_test_token():
    """Get authentication token for testing"""
    response = client.post(
        "/api/v1/auth/login-simple",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]

class TestDatabaseIntegration:
    """Test database operations and persistence"""

    def test_database_status(self):
        """Test database connection status"""
        token = get_test_token()
        response = client.get(
            "/api/v1/database/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["database_status"] == "connected"
        assert data["database_type"] == "PostgreSQL"
        assert data["total_scholarships"] >= 15  # Should have our migrated data

    def test_get_scholarships_from_database(self):
        """Test retrieving scholarships directly from PostgreSQL"""
        token = get_test_token()
        response = client.get(
            "/api/v1/database/scholarships?limit=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "scholarships" in data
        assert "total_count" in data
        assert len(data["scholarships"]) <= 5
        assert data["total_count"] >= 15

    def test_get_specific_scholarship_from_database(self):
        """Test retrieving a specific scholarship from PostgreSQL"""
        token = get_test_token()

        # First get a scholarship ID
        list_response = client.get(
            "/api/v1/database/scholarships?limit=1",
            headers={"Authorization": f"Bearer {token}"}
        )
        scholarship_id = list_response.json()["scholarships"][0]["id"]

        # Get specific scholarship
        response = client.get(
            f"/api/v1/database/scholarships/{scholarship_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scholarship_id
        assert "eligibility_criteria" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_log_interaction_to_database(self):
        """Test logging user interactions to PostgreSQL"""
        token = get_test_token()

        interaction_data = {
            "scholarship_id": "sch_001",
            "interaction_type": "viewed",
            "search_query": "engineering",
            "filters_applied": {"min_gpa": 3.0},
            "match_score": 0.85,
            "position_in_results": 1,
            "source": "search"
        }

        response = client.post(
            "/api/v1/database/interactions",
            headers={"Authorization": f"Bearer {token}"},
            json=interaction_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "interaction_id" in data
        assert data["status"] == "logged"

    def test_analytics_summary_from_database(self):
        """Test retrieving analytics summary from PostgreSQL"""
        token = get_test_token()
        response = client.get(
            "/api/v1/database/analytics/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_scholarships" in data
        assert "total_interactions" in data
        assert "total_searches" in data
        assert data["total_scholarships"] >= 15

    def test_database_search_with_filters(self):
        """Test database search with various filters"""
        token = get_test_token()

        # Test keyword search
        response = client.get(
            "/api/v1/database/scholarships?keyword=engineering",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

        # Test amount filter
        response = client.get(
            "/api/v1/database/scholarships?min_amount=10000",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify all results meet the criteria
        for scholarship in data["scholarships"]:
            assert scholarship["amount"] >= 10000

    def test_database_vs_memory_consistency(self):
        """Test that database and memory services return consistent data"""
        token = get_test_token()

        # Get data from database endpoint
        db_response = client.get(
            "/api/v1/database/scholarships?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Get data from regular endpoint (memory-based)
        memory_response = client.get("/api/v1/scholarships?limit=10")

        assert db_response.status_code == 200
        assert memory_response.status_code == 200

        db_data = db_response.json()
        memory_data = memory_response.json()

        # Should have same total count (basic consistency check)
        assert db_data["total_count"] == memory_data["total_count"]

class TestDatabaseServiceDirect:
    """Test database service layer directly"""

    def test_database_service_migration(self):
        """Test that migration created all expected data"""
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)

            # Test getting scholarships
            result = db_service.get_scholarships(limit=20)
            assert result["total_count"] == 15
            assert len(result["scholarships"]) == 15

            # Test getting specific scholarship
            scholarship = db_service.get_scholarship_by_id("sch_001")
            assert scholarship is not None
            assert scholarship["name"] == "National Merit Engineering Scholarship"

        finally:
            db.close()

    def test_database_service_analytics(self):
        """Test analytics functionality"""
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)

            # Test analytics summary
            summary = db_service.get_analytics_summary()
            assert summary["total_scholarships"] == 15
            assert summary["total_interactions"] >= 0

        finally:
            db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
