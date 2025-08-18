"""
Test script for Agent Bridge functionality
Demonstrates task execution, capabilities, and integration
"""

import json
import time
import uuid
import jwt
import requests
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:5000"
SHARED_SECRET = "test_secret_for_agent_bridge_demo"
AGENT_ID = "scholarship_api"

def create_test_jwt(payload: dict) -> str:
    """Create JWT token for testing"""
    token_payload = {
        **payload,
        "iss": "auto-com-center",
        "aud": "scholar-sync-agents", 
        "iat": int(time.time()),
        "exp": int(time.time()) + 300  # 5 minute expiry
    }
    
    return jwt.encode(token_payload, SHARED_SECRET, algorithm="HS256")

def test_agent_capabilities():
    """Test GET /agent/capabilities"""
    print("=== Testing Agent Capabilities ===")
    
    response = requests.get(f"{BASE_URL}/agent/capabilities")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Agent ID: {data['agent_id']}")
        print(f"Name: {data['name']}")
        print(f"Capabilities: {data['capabilities']}")
        print(f"Health: {data['health']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_agent_health():
    """Test GET /agent/health"""
    print("\n=== Testing Agent Health ===")
    
    response = requests.get(f"{BASE_URL}/agent/health")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Command Center Configured: {data['command_center_configured']}")
        print(f"Shared Secret Configured: {data['shared_secret_configured']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_task_execution_without_auth():
    """Test task execution without JWT (should fail)"""
    print("\n=== Testing Task Without Auth (Should Fail) ===")
    
    task = {
        "task_id": str(uuid.uuid4()),
        "action": "scholarship_api.search",
        "payload": {
            "query": "engineering",
            "filters": {},
            "pagination": {"page": 1, "size": 5}
        },
        "reply_to": "http://example.com/callback",
        "trace_id": str(uuid.uuid4()),
        "requested_by": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/agent/task", json=task)
    print(f"Status: {response.status_code} (Expected: 401)")
    
    if response.status_code == 401:
        print("✅ Correctly rejected unauthorized request")
        return True
    else:
        print("❌ Should have rejected unauthorized request")
        return False

def test_task_execution_with_auth():
    """Test task execution with JWT (mock scenario)"""
    print("\n=== Testing Task With Auth (Mock JWT) ===")
    
    task_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    task = {
        "task_id": task_id,
        "action": "scholarship_api.search",
        "payload": {
            "query": "engineering scholarships",
            "filters": {
                "min_amount": 1000,
                "fields_of_study": ["engineering"]
            },
            "pagination": {"page": 1, "size": 5}
        },
        "reply_to": "http://example.com/callback",
        "trace_id": trace_id,
        "requested_by": "test_user"
    }
    
    # Create mock JWT token
    token = create_test_jwt({
        "agent_id": AGENT_ID,
        "action": "task_execution",
        "task_id": task_id
    })
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Agent-Id": AGENT_ID,
        "X-Trace-Id": trace_id
    }
    
    print(f"Sending task {task_id[:8]}... with action: {task['action']}")
    
    try:
        response = requests.post(f"{BASE_URL}/agent/task", json=task, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 202:
            data = response.json()
            print(f"✅ Task accepted: {data['message']}")
            print(f"Task ID: {data['task_id']}")
            print(f"Status: {data['status']}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed (check SHARED_SECRET configuration)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ Unexpected status: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_registration():
    """Test agent registration endpoint"""
    print("\n=== Testing Agent Registration ===")
    
    token = create_test_jwt({
        "agent_id": AGENT_ID,
        "action": "register"
    })
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Agent-Id": AGENT_ID
    }
    
    try:
        response = requests.post(f"{BASE_URL}/agent/register", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Registration successful: {data['message']}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed for registration")
            return False
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        return False

def test_search_functionality():
    """Test that regular search still works (backward compatibility)"""
    print("\n=== Testing Backward Compatibility (Regular Search) ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/search?q=engineering&limit=3")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Regular search works: Found {len(data.get('items', []))} scholarships")
        print(f"Total available: {data.get('total', 0)}")
        return True
    else:
        print(f"❌ Regular search failed: {response.text}")
        return False

def main():
    """Run all Agent Bridge tests"""
    print("🚀 Agent Bridge Functionality Test Suite")
    print("=" * 50)
    
    tests = [
        ("Agent Capabilities", test_agent_capabilities),
        ("Agent Health", test_agent_health),
        ("Task Without Auth", test_task_execution_without_auth),
        ("Task With Auth", test_task_execution_with_auth),
        ("Agent Registration", test_registration),
        ("Backward Compatibility", test_search_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Agent Bridge is working correctly.")
    else:
        print("⚠️  Some tests failed. Check configuration and implementation.")
        
    # Configuration notes
    print("\n" + "=" * 50)
    print("📝 CONFIGURATION NOTES")
    print("=" * 50)
    print("• For full functionality, set these environment variables:")
    print("  - COMMAND_CENTER_URL=https://auto-com-center-jamarrlmayes.replit.app")
    print("  - SHARED_SECRET=<your_shared_secret>")
    print("  - AGENT_BASE_URL=<this_agent_url>")
    print("• JWT authentication requires matching shared secret between services")
    print("• Agent Bridge preserves all existing API functionality")

if __name__ == "__main__":
    main()