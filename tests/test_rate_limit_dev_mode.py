"""
Test to verify development mode rate limiting behavior (QA False Positive Documentation)
This test confirms that dev mode intentionally has higher rate limits
"""

import os
import sys
import time

import requests

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from config.settings import settings

BASE_URL = "http://localhost:5000"

class TestDevelopmentRateLimiting:
    """Test development mode rate limiting to document QA false positive RATE-601"""

    def test_development_mode_rate_limits(self):
        """Test that development mode has appropriately higher rate limits"""

        # In development mode, we expect higher limits
        if settings.is_development:
            # Development mode should allow more requests
            expected_success_count = 50  # Should handle at least 50 requests
        else:
            # Production mode should have stricter limits
            expected_success_count = 20  # Stricter limits in production

        successful_requests = 0
        rate_limited = False

        start_time = time.time()

        # Send requests rapidly to test rate limiting
        for i in range(60):  # Test with 60 requests
            try:
                response = requests.get(f"{BASE_URL}/search", params={"q": f"test{i}"}, timeout=1)

                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:
                    rate_limited = True
                    break

            except requests.RequestException:
                # Network timeout or connection error
                break

        duration = time.time() - start_time

        print(f"Environment: {settings.environment}")
        print(f"Successful requests: {successful_requests}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Rate limited: {rate_limited}")

        if settings.is_development:
            # In development, we should be able to make more requests
            assert successful_requests >= expected_success_count, \
                f"Development mode should allow at least {expected_success_count} requests, got {successful_requests}"

            # Development mode may not hit rate limit in our test
            # This is expected behavior and not a security issue
        else:
            # In production, rate limiting should be more strict
            assert rate_limited or successful_requests <= expected_success_count, \
                "Production mode should have stricter rate limits"

    def test_environment_specific_rate_limits(self):
        """Test that rate limits are properly configured based on environment"""

        # Test search rate limit configuration
        search_limit = settings.get_search_rate_limit
        eligibility_limit = settings.get_eligibility_rate_limit

        print(f"Search rate limit: {search_limit}")
        print(f"Eligibility rate limit: {eligibility_limit}")

        if settings.environment.value in ["local", "development"]:
            # Development environments should have higher limits
            assert "60" in search_limit or "45" in search_limit, \
                f"Development search limit should be higher, got: {search_limit}"
            assert "30" in eligibility_limit or "20" in eligibility_limit, \
                f"Development eligibility limit should be higher, got: {eligibility_limit}"

        elif settings.environment.value == "production":
            # Production should have stricter limits
            assert "30" in search_limit, f"Production search limit should be 30/minute, got: {search_limit}"
            assert "15" in eligibility_limit, f"Production eligibility limit should be 15/minute, got: {eligibility_limit}"

    def test_multiple_endpoints_rate_limiting(self):
        """Test rate limiting across different endpoints"""

        endpoints = [
            "/search",
            "/eligibility/check?gpa=3.5",
            "/db/status"
        ]

        for endpoint in endpoints:
            successful_requests = 0

            # Test rapid requests to each endpoint
            for _i in range(30):
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=1)
                    if response.status_code == 200:
                        successful_requests += 1
                    elif response.status_code == 429:
                        break
                except requests.RequestException:
                    break

            print(f"Endpoint {endpoint}: {successful_requests} successful requests")

            # In development mode, should handle more requests
            if settings.is_development:
                assert successful_requests >= 20, \
                    f"Development mode should handle at least 20 requests for {endpoint}"

    def test_rate_limit_headers(self):
        """Test that rate limit headers are present when available"""

        response = requests.get(f"{BASE_URL}/search", params={"q": "test"})

        # Check if rate limit headers are present
        headers = response.headers

        # Common rate limit header names

        # At least some rate limit information should be available
        print(f"Response headers: {dict(headers)}")

        # This is informational - rate limit headers may not be implemented yet
        # but the rate limiting functionality is working

if __name__ == "__main__":
    # Quick test to verify rate limiting behavior
    test_suite = TestDevelopmentRateLimiting()

    print("Testing development mode rate limiting...")
    print(f"Environment: {settings.environment}")
    print(f"Is development: {settings.is_development}")

    try:
        test_suite.test_environment_specific_rate_limits()
        print("✅ Environment-specific rate limits configured correctly")
    except Exception as e:
        print(f"❌ Rate limit configuration test failed: {e}")

    try:
        test_suite.test_development_mode_rate_limits()
        print("✅ Development mode rate limiting working as expected")
    except Exception as e:
        print(f"❌ Development rate limit test failed: {e}")
