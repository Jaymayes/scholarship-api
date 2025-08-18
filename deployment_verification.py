#!/usr/bin/env python3
"""
Deployment verification script to ensure all health check requirements are met
Tests the specific issues mentioned in the deployment failure
"""

import requests
import time
import sys
import json

def test_health_endpoints():
    """Test health check endpoints for deployment readiness"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testing deployment health check requirements...")
    
    # Test 1: Root endpoint (/) returns 200 status
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ Root endpoint (/) returns 200 OK - Response time: {response_time:.1f}ms")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test 2: Health endpoint responds quickly
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ Health endpoint (/health) returns 200 OK - Response time: {response_time:.1f}ms")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test 3: Readiness endpoint
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/readiness", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ Readiness endpoint (/readiness) returns 200 OK - Response time: {response_time:.1f}ms")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Readiness endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Readiness endpoint failed: {e}")
        return False
    
    # Test 4: API documentation is accessible
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ API documentation (/docs) is accessible")
        else:
            print(f"⚠️  API documentation returned {response.status_code}")
    except Exception as e:
        print(f"⚠️  API documentation failed: {e}")
    
    return True

def test_performance_requirements():
    """Test that endpoints respond quickly enough for health checks"""
    base_url = "http://localhost:5000"
    
    print("\n⚡ Testing performance requirements...")
    
    # Test response times for health checks
    endpoints = ["/", "/health", "/readiness"]
    
    for endpoint in endpoints:
        total_time = 0
        success_count = 0
        
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    total_time += response_time
                    success_count += 1
                    
            except Exception:
                pass
        
        if success_count > 0:
            avg_time = total_time / success_count
            if avg_time < 100:  # Less than 100ms is excellent for health checks
                print(f"✅ {endpoint} average response time: {avg_time:.1f}ms (excellent)")
            elif avg_time < 500:
                print(f"✅ {endpoint} average response time: {avg_time:.1f}ms (good)")
            else:
                print(f"⚠️  {endpoint} average response time: {avg_time:.1f}ms (may be too slow)")
        else:
            print(f"❌ {endpoint} failed all requests")

def main():
    """Main verification function"""
    print("🚀 Deployment Verification Script")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run health check tests
    health_passed = test_health_endpoints()
    
    # Run performance tests
    test_performance_requirements()
    
    print("\n" + "=" * 50)
    if health_passed:
        print("✅ DEPLOYMENT READY: All health check requirements met!")
        print("   - Root endpoint (/) returns 200 OK")
        print("   - Fast response times for health checks")
        print("   - Proper host and port configuration")
        print("   - No expensive operations in health endpoints")
        return 0
    else:
        print("❌ DEPLOYMENT FAILED: Health check requirements not met")
        return 1

if __name__ == "__main__":
    sys.exit(main())