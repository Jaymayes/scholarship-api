#!/usr/bin/env python3
"""
Marketplace Connectivity Test (Supply-Demand Bridge)
Verifies connectivity between this API and Provider Registry
"""

import os
import sys
import json
import time
import httpx

def run_connectivity_test():
    """Run full connectivity test to Provider Registry (A6)"""
    
    print("=" * 60)
    print("MARKETPLACE CONNECTIVITY TEST")
    print("Supply-Demand Bridge Verification")
    print("=" * 60)
    
    a2_url = os.environ.get("SCHOLARSHIP_API_URL") or os.environ.get("API_URL")
    url_source = "environment"
    
    if not a2_url:
        a2_url = "http://localhost:5000"
        url_source = "default (local)"
    
    a2_url = a2_url.rstrip("/")
    
    print(f"\n[1] Environment Check")
    print(f"    Target URL: {a2_url}")
    print(f"    Source: {url_source}")
    
    result = {
        "a2_url": a2_url,
        "can_reach_health": False,
        "can_fetch_scholarships": False,
        "latency_ms": 0,
        "errors": [],
        "suggestions": []
    }
    
    print(f"\n[2] Connectivity Probe")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            start_time = time.time()
            
            print(f"\n    Health Check: GET {a2_url}/healthz")
            try:
                health_resp = client.get(f"{a2_url}/healthz")
                health_latency = int((time.time() - start_time) * 1000)
                
                if health_resp.status_code == 200:
                    print(f"    ✅ HTTP 200 OK ({health_latency}ms)")
                    result["can_reach_health"] = True
                    result["latency_ms"] = health_latency
                elif health_resp.status_code == 404:
                    print(f"    ⚠️  HTTP 404 - Trying /health instead...")
                    health_resp = client.get(f"{a2_url}/health")
                    if health_resp.status_code == 200:
                        print(f"    ✅ HTTP 200 OK (via /health)")
                        result["can_reach_health"] = True
                        result["latency_ms"] = int((time.time() - start_time) * 1000)
                    else:
                        print(f"    ❌ HTTP {health_resp.status_code}")
                        result["errors"].append(f"Health endpoint returned {health_resp.status_code}")
                else:
                    print(f"    ❌ HTTP {health_resp.status_code}")
                    result["errors"].append(f"Health check failed: HTTP {health_resp.status_code}")
            except httpx.RequestError as e:
                print(f"    ❌ Connection failed: {e}")
                result["errors"].append(f"Cannot reach health endpoint: {str(e)}")
            
            print(f"\n    Data Access: GET {a2_url}/api/scholarships/public")
            start_time = time.time()
            
            endpoints_to_try = [
                "/api/v1/scholarships/public",
                "/api/scholarships/public",
                "/api/v1/scholarships",
                "/api/v1/scholarships/search"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    data_resp = client.get(f"{a2_url}{endpoint}")
                    data_latency = int((time.time() - start_time) * 1000)
                    
                    if data_resp.status_code == 200:
                        print(f"    ✅ HTTP 200 OK via {endpoint} ({data_latency}ms)")
                        result["can_fetch_scholarships"] = True
                        
                        try:
                            data = data_resp.json()
                            if isinstance(data, list):
                                print(f"    📊 Found {len(data)} scholarships")
                            elif isinstance(data, dict):
                                items = data.get("items", data.get("scholarships", data.get("data", [])))
                                print(f"    📊 Found {len(items) if isinstance(items, list) else 'N/A'} scholarships")
                        except:
                            print(f"    📊 Response is valid JSON")
                        break
                        
                    elif data_resp.status_code == 401:
                        print(f"    ⚠️  HTTP 401 Unauthorized at {endpoint}")
                        result["errors"].append(f"401 at {endpoint} - API security may be too tight for public access")
                        result["suggestions"].append("Consider adding a public scholarships endpoint that doesn't require auth")
                        
                    elif data_resp.status_code == 403:
                        print(f"    ⚠️  HTTP 403 Forbidden at {endpoint}")
                        result["errors"].append(f"403 at {endpoint} - Missing permissions for scholarship data")
                        result["suggestions"].append("Students need to see scholarships without provider login")
                        
                    elif data_resp.status_code == 404:
                        print(f"    ⚠️  HTTP 404 at {endpoint} - trying next...")
                        continue
                    else:
                        print(f"    ❌ HTTP {data_resp.status_code} at {endpoint}")
                        
                except httpx.RequestError as e:
                    print(f"    ❌ Request failed: {e}")
                    result["errors"].append(f"Cannot fetch scholarships: {str(e)}")
            
            if not result["can_fetch_scholarships"]:
                result["errors"].append("No accessible scholarship endpoint found")
                result["suggestions"].append("Add GET /api/scholarships/public endpoint for cross-app access")
    
    except Exception as e:
        print(f"\n    ❌ Fatal error: {e}")
        result["errors"].append(f"Test failed: {str(e)}")
    
    print(f"\n[3] Report")
    print("-" * 60)
    print(json.dumps(result, indent=2))
    print("-" * 60)
    
    if not result["can_reach_health"] or not result["can_fetch_scholarships"]:
        print("\n⚠️  SUGGESTIONS:")
        if url_source == "default":
            print("   • Set PROVIDER_REGISTRY_URL environment variable to the correct A6 URL")
        for suggestion in result["suggestions"]:
            print(f"   • {suggestion}")
        print("\n❌ BRIDGE TEST FAILED")
        return 1
    else:
        print("\n✅ BRIDGE TEST PASSED - Marketplace connectivity verified!")
        return 0

if __name__ == "__main__":
    sys.exit(run_connectivity_test())
