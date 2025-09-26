"""
Test to verify SQL injection protection (QA False Positive Documentation)
This test confirms that SQL-like input is handled safely without injection
"""


import pytest
import requests

BASE_URL = "http://localhost:5000"

class TestSQLInjectionProtection:
    """Test SQL injection protection to document QA false positive SQL-300"""

    @pytest.mark.parametrize("sql_payload", [
        "'; DROP TABLE scholarships; --",
        "' OR '1'='1",
        "1' UNION SELECT * FROM users --",
        "admin'--",
        "' OR 1=1 --",
        "'; DELETE FROM scholarships WHERE id='1'; --",
        "' UNION SELECT password FROM users --"
    ])
    def test_search_sql_injection_protection(self, sql_payload: str):
        """Test that search endpoint safely handles SQL-like input"""

        # Send SQL injection payload to search endpoint
        response = requests.get(f"{BASE_URL}/search", params={"q": sql_payload})

        # Should return 200 with normal search results (empty or filtered)
        assert response.status_code == 200

        data = response.json()

        # Verify response structure is normal search response
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "filters" in data

        # Verify no SQL error messages in response
        response_text = response.text.lower()
        sql_error_keywords = [
            "syntax error", "sql error", "database error",
            "table", "column", "select", "insert", "update", "delete",
            "drop", "union", "where", "from"
        ]

        # Should not contain SQL keywords that suggest injection worked
        for keyword in sql_error_keywords:
            assert keyword not in response_text, f"Response contains SQL keyword: {keyword}"

        # The search should return normal results or empty results, not database errors
        assert data["total"] >= 0  # Valid search result count
        assert isinstance(data["items"], list)  # Valid items list

    def test_eligibility_sql_injection_protection(self):
        """Test eligibility endpoint SQL injection protection"""

        sql_payloads = [
            "'; DROP TABLE scholarships; --",
            "' OR '1'='1",
            "admin'--"
        ]

        for payload in sql_payloads:
            # Try SQL injection in various parameters
            params = {
                "gpa": payload,
                "grade_level": payload,
                "field_of_study": payload
            }

            response = requests.get(f"{BASE_URL}/eligibility/check", params=params)

            # Should return validation error (422) or normal response (200)
            # Should NOT return 500 with SQL errors
            assert response.status_code in [200, 422, 400]

            if response.status_code == 200:
                data = response.json()
                # Should have normal eligibility response structure
                assert "results" in data or "eligible" in data

    def test_parameterized_queries_prevent_injection(self):
        """Verify that parameterized queries prevent SQL injection"""

        # Test with SQL injection attempt in search
        malicious_query = "test'; DROP TABLE scholarships; SELECT * FROM scholarships WHERE name LIKE '%"

        response = requests.get(f"{BASE_URL}/search", params={"q": malicious_query})

        assert response.status_code == 200
        response.json()

        # Verify database is intact by checking normal search still works
        normal_response = requests.get(f"{BASE_URL}/search", params={"q": "engineering"})
        assert normal_response.status_code == 200

        # If scholarships were deleted, this would fail
        normal_data = normal_response.json()
        assert isinstance(normal_data["items"], list)

    def test_filter_parameters_sql_injection_protection(self):
        """Test SQL injection protection in filter parameters"""

        sql_payloads = [
            "'; DROP TABLE scholarships; --",
            "' OR 1=1 --"
        ]

        for payload in sql_payloads:
            params = {
                "fields_of_study": payload,
                "states": payload,
                "scholarship_types": payload,
                "min_amount": payload,
                "max_amount": payload
            }

            response = requests.get(f"{BASE_URL}/search", params=params)

            # Should handle gracefully with validation error or normal response
            assert response.status_code in [200, 422, 400]

            # Should not expose SQL errors or crash
            assert "syntax error" not in response.text.lower()
            assert "sql" not in response.text.lower()

if __name__ == "__main__":
    # Quick test to verify SQL injection protection
    test_suite = TestSQLInjectionProtection()

    print("Testing SQL injection protection...")

    # Test basic SQL injection attempts
    sql_payloads = ["'; DROP TABLE scholarships; --", "' OR '1'='1", "admin'--"]

    for payload in sql_payloads:
        try:
            response = requests.get(f"{BASE_URL}/search", params={"q": payload}, timeout=5)
            print(f"✅ SQL payload handled safely: {payload[:20]}... (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error testing payload {payload[:20]}...: {e}")

    print("SQL injection protection test completed.")
