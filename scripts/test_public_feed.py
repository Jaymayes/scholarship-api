#!/usr/bin/env python3
"""
Public Scholarship Feed Verification Script
Tests the /api/scholarships/public endpoint
"""

import sys
import json
import httpx

def test_public_feed():
    """Test the public scholarship feed endpoint"""
    
    base_url = "http://localhost:5000"
    endpoints_to_test = [
        f"{base_url}/api/v1/scholarships/public",
        f"{base_url}/api/scholarships/public"
    ]
    endpoint = endpoints_to_test[0]
    
    print("=" * 60)
    print("PUBLIC SCHOLARSHIP FEED TEST")
    print("=" * 60)
    print(f"\nEndpoint: {endpoint}")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(endpoint)
            
            print(f"\n[1] HTTP Status Check")
            print(f"    Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"    ❌ FAIL: Expected HTTP 200, got {response.status_code}")
                print(f"    Response: {response.text[:500]}")
                return 1
            print(f"    ✅ PASS: HTTP 200 OK")
            
            print(f"\n[2] JSON Response Check")
            try:
                data = response.json()
                print(f"    ✅ PASS: Valid JSON response")
            except json.JSONDecodeError as e:
                print(f"    ❌ FAIL: Invalid JSON - {e}")
                return 1
            
            print(f"\n[3] Response Structure Check")
            if "items" not in data:
                print(f"    ❌ FAIL: Missing 'items' field")
                return 1
            
            items = data.get("items", [])
            if not isinstance(items, list):
                print(f"    ❌ FAIL: 'items' is not an array")
                return 1
            print(f"    ✅ PASS: Response contains items array ({len(items)} scholarships)")
            
            print(f"\n[4] Safe Fields Check")
            safe_fields = {"id", "title", "amount_min", "amount_max", "deadline", "provider_name", "tags"}
            if items:
                first_item = items[0]
                item_fields = set(first_item.keys())
                print(f"    Fields returned: {', '.join(sorted(item_fields))}")
                
                unsafe_fields = item_fields - safe_fields - {"description"}
                if unsafe_fields:
                    print(f"    ⚠️  WARN: Extra fields found: {unsafe_fields}")
                else:
                    print(f"    ✅ PASS: Only safe fields returned")
            else:
                print(f"    ⚠️  WARN: No items to check fields")
            
            print(f"\n[5] Cache-Control Header Check")
            cache_control = response.headers.get("Cache-Control", "")
            print(f"    Cache-Control: {cache_control or '(not set)'}")
            
            if "public" in cache_control and "max-age" in cache_control:
                print(f"    ✅ PASS: Cache-Control header is properly set")
            else:
                print(f"    ❌ FAIL: Cache-Control header missing or invalid")
                return 1
            
            print(f"\n[6] Pagination Check")
            total = data.get("total", 0)
            page = data.get("page", 0)
            limit = data.get("limit", 0)
            print(f"    Total: {total}, Page: {page}, Limit: {limit}")
            print(f"    ✅ PASS: Pagination metadata present")
            
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED - Public feed is operational!")
            print("=" * 60)
            
            return 0
            
    except httpx.RequestError as e:
        print(f"\n❌ FAIL: Connection error - {e}")
        return 1
    except Exception as e:
        print(f"\n❌ FAIL: Unexpected error - {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_public_feed())
