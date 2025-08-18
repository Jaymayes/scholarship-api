#!/usr/bin/env python3
"""
Deployment Verification Script
Tests all critical endpoints for deployment readiness
"""

import requests
import time
import sys

def test_endpoint(url, endpoint_name, expected_status=200, max_response_time=1.0):
    """Test an endpoint and measure response time"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        response_time = time.time() - start_time
        
        success = response.status_code == expected_status and response_time <= max_response_time
        status_icon = "✅" if success else "❌"
        
        print(f"{status_icon} {endpoint_name}: {response.status_code} ({response_time:.3f}s)")
        
        if success:
            return True
        else:
            if response.status_code != expected_status:
                print(f"   Expected status {expected_status}, got {response.status_code}")
            if response_time > max_response_time:
                print(f"   Response time {response_time:.3f}s exceeds {max_response_time}s limit")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint_name}: Request failed - {e}")
        return False

def main():
    """Run deployment verification tests"""
    base_url = "http://localhost:5000"
    
    print("🔍 Deployment Verification - Testing Critical Endpoints")
    print("=" * 60)
    
    tests = [
        (f"{base_url}/", "Root endpoint (/)", 200, 3.0),  # Deployment health checks can be slower
        (f"{base_url}/health", "Health endpoint (/health)", 200, 0.1),
        (f"{base_url}/readiness", "Readiness endpoint (/readiness)", 200, 0.1),
        (f"{base_url}/api", "API status (/api)", 200, 0.1),
        (f"{base_url}/docs", "API documentation (/docs)", 200, 1.0),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, name, expected_status, max_time in tests:
        if test_endpoint(url, name, expected_status, max_time):
            passed += 1
    
    print("=" * 60)
    if passed == total:
        print(f"✅ DEPLOYMENT READY: All {total} tests passed!")
        print("   - All endpoints return expected status codes")
        print("   - All response times are within deployment limits")
        print("   - Application is ready for production deployment")
        sys.exit(0)
    else:
        print(f"❌ DEPLOYMENT NOT READY: {passed}/{total} tests passed")
        print("   - Please fix failing endpoints before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()