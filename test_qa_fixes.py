#!/usr/bin/env python3
"""
Test script for QA fixes verification
Tests SEC-001, DB-001, and RATE-001 fixes
"""

import os
import sys
import requests
import time
import json
from datetime import datetime

def test_sec_001_jwt_secret():
    """Test SEC-001: JWT secret key configuration"""
    print("Testing SEC-001: JWT Secret Key Configuration")
    
    try:
        from config.settings import settings
        
        # Test 1: Check if JWT secret is configured
        if hasattr(settings, 'jwt_secret_key') and settings.jwt_secret_key:
            if settings.jwt_secret_key == "your-secret-key-change-in-production":
                print("❌ SEC-001: Default JWT secret still in use")
                return False
            else:
                print(f"✅ SEC-001: JWT secret configured (length: {len(settings.jwt_secret_key)})")
                return True
        else:
            print("❌ SEC-001: JWT secret not configured")
            return False
            
    except Exception as e:
        print(f"❌ SEC-001: Error checking JWT configuration: {e}")
        return False

def test_db_001_database_status():
    """Test DB-001: Database status endpoint"""
    print("Testing DB-001: Database Status Endpoint")
    
    try:
        response = requests.get("http://localhost:5000/api/v1/database/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "database_status" in data and data["database_status"] == "connected":
                print("✅ DB-001: Database status endpoint working")
                return True
            else:
                print(f"❌ DB-001: Unexpected response format: {data}")
                return False
        else:
            print(f"❌ DB-001: Status {response.status_code}, Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ DB-001: Error testing database status: {e}")
        return False

def test_rate_001_rate_limiting():
    """Test RATE-001: Rate limiting functionality"""
    print("Testing RATE-001: Rate Limiting")
    
    # Test with very rapid requests to trigger rate limiting
    endpoint = "http://localhost:5000/api/v1/search"
    success_count = 0
    rate_limited_count = 0
    
    # Make 30 rapid requests
    print("Making 30 rapid requests to test rate limiting...")
    for i in range(30):
        try:
            response = requests.get(f"{endpoint}?q=ratetest{i}", timeout=2)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"✅ RATE-001: Got 429 on request {i+1}")
                # Check for proper headers
                if "Retry-After" in response.headers:
                    print(f"✅ RATE-001: Retry-After header present: {response.headers['Retry-After']}")
                return True
            
            # Small delay to allow requests to process
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    if rate_limited_count > 0:
        print(f"✅ RATE-001: Rate limiting working ({rate_limited_count} rate limited)")
        return True
    else:
        print(f"❌ RATE-001: No rate limiting detected ({success_count} successful requests)")
        return False

def test_unified_error_format():
    """Test unified error response format"""
    print("Testing unified error response format")
    
    # Test 404 error
    try:
        response = requests.get("http://localhost:5000/nonexistent", timeout=5)
        if response.status_code == 404:
            data = response.json()
            required_fields = ['trace_id', 'code', 'message', 'status', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            if not missing_fields:
                print("✅ ERROR FORMAT: 404 errors use unified format")
                return True
            else:
                print(f"❌ ERROR FORMAT: Missing fields in 404 response: {missing_fields}")
                return False
    except Exception as e:
        print(f"❌ ERROR FORMAT: Error testing 404 format: {e}")
        return False

def run_all_tests():
    """Run all QA fix tests"""
    print("=" * 60)
    print("QA FIXES VERIFICATION TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("SEC-001", test_sec_001_jwt_secret),
        ("DB-001", test_db_001_database_status),
        ("RATE-001", test_rate_001_rate_limiting),
        ("ERROR FORMAT", test_unified_error_format)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: Test execution failed: {e}")
            results[test_name] = False
        print()
    
    # Summary
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL QA FIXES VERIFIED!")
    else:
        print("⚠️  Some issues still need to be addressed")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)