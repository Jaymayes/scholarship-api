#!/usr/bin/env python3
"""
QA Verification Script - Test Only (No Code Changes)
Comprehensive API health, security, and functionality verification
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

class APIVerifier:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 5
        self.results = {
            'meta': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'base_url': base_url,
                'environment_detected': None
            },
            'endpoints': [],
            'auth': {},
            'db': {},
            'search': {},
            'eligibility': {},
            'rate_limit_probe': {},
            'headers': {},
            'errors_observed': [],
            'conclusion': 'PASS'
        }
    
    def test_request(self, method: str, path: str, headers: Dict = None, json_data: Dict = None, expected_status: int = None) -> Dict[str, Any]:
        """Make a test request and capture comprehensive metrics"""
        url = f"{self.base_url}{path}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=json_data)
            elif method.upper() == 'HEAD':
                response = self.session.head(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            latency_ms = round((time.time() - start_time) * 1000, 2)
            
            # Parse response body
            body_sample_keys = []
            response_data = None
            try:
                response_data = response.json()
                if isinstance(response_data, dict):
                    body_sample_keys = list(response_data.keys())
            except:
                pass
            
            result = {
                'method': method.upper(),
                'path': path,
                'status': response.status_code,
                'latency_ms': latency_ms,
                'headers_subset': {
                    'content-type': response.headers.get('content-type', ''),
                    'x-xss-protection': response.headers.get('x-xss-protection', ''),
                    'x-frame-options': response.headers.get('x-frame-options', ''),
                    'x-content-type-options': response.headers.get('x-content-type-options', ''),
                    'strict-transport-security': response.headers.get('strict-transport-security', ''),
                    'access-control-allow-origin': response.headers.get('access-control-allow-origin', ''),
                    'retry-after': response.headers.get('retry-after', '')
                },
                'body_sample_keys': body_sample_keys,
                'response_data': response_data
            }
            
            # Track error envelopes
            if response.status_code >= 400:
                envelope_ok = False
                if response_data and isinstance(response_data, dict):
                    expected_fields = {'trace_id', 'code', 'message', 'status'}
                    if expected_fields.issubset(set(response_data.keys())):
                        envelope_ok = True
                
                self.results['errors_observed'].append({
                    'path': path,
                    'status': response.status_code,
                    'envelope_ok': envelope_ok
                })
            
            self.results['endpoints'].append(result)
            return result
            
        except Exception as e:
            result = {
                'method': method.upper(),
                'path': path,
                'status': 'ERROR',
                'latency_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e),
                'headers_subset': {},
                'body_sample_keys': [],
                'response_data': None
            }
            self.results['endpoints'].append(result)
            return result
    
    def verify_root_endpoint(self):
        """Test 1: Detect base URL and status"""
        print("🔍 Testing root endpoint...")
        result = self.test_request('GET', '/')
        
        if result['status'] == 200 and result['response_data']:
            data = result['response_data']
            required_keys = {'message', 'version', 'environment', 'docs', 'status', 'authentication'}
            if required_keys.issubset(set(data.keys())):
                self.results['meta']['environment_detected'] = data.get('environment', 'unknown')
                print(f"✅ Root endpoint OK - Environment: {data.get('environment')}")
                return True
            else:
                print(f"❌ Root endpoint missing keys. Expected: {required_keys}, Got: {list(data.keys())}")
                self.results['conclusion'] = 'WARN'
        else:
            print(f"❌ Root endpoint failed - Status: {result['status']}")
            self.results['conclusion'] = 'FAIL'
        return False
    
    def verify_operational_endpoints(self):
        """Test 2: Public/operational endpoints"""
        print("🔍 Testing operational endpoints...")
        
        endpoints = [
            ('/docs', 200),
            ('/healthz', 200),
            ('/readyz', [200, 503]),
            ('/metrics', 200)
        ]
        
        for path, expected_status in endpoints:
            result = self.test_request('GET', path)
            if isinstance(expected_status, list):
                if result['status'] in expected_status:
                    print(f"✅ {path} - Status: {result['status']} (expected)")
                else:
                    print(f"❌ {path} - Status: {result['status']} (expected {expected_status})")
                    self.results['conclusion'] = 'WARN'
            else:
                if result['status'] == expected_status:
                    print(f"✅ {path} - Status: {result['status']}")
                else:
                    print(f"❌ {path} - Status: {result['status']} (expected {expected_status})")
                    self.results['conclusion'] = 'WARN'
    
    def verify_database_status(self):
        """Test 3: Database status"""
        print("🔍 Testing database status...")
        
        db_routes = ['/db/status', '/api/v1/db/status']
        db_result = None
        
        for route in db_routes:
            result = self.test_request('GET', route)
            if result['status'] == 200:
                db_result = result
                self.results['db']['route_used'] = route
                break
            elif result['status'] == 404:
                print(f"📝 {route} - not found (as designed)")
            else:
                print(f"❌ {route} - Status: {result['status']}")
        
        if db_result and db_result['response_data']:
            data = db_result['response_data']
            self.results['db'].update({
                'available': data.get('status') == 'ok',
                'scholarships_count': data.get('scholarships_count'),
                'interactions_count': data.get('interactions_count')
            })
            print(f"✅ Database connected - Scholarships: {data.get('scholarships_count', 'N/A')}, Interactions: {data.get('interactions_count', 'N/A')}")
        else:
            self.results['db'].update({
                'available': False,
                'scholarships_count': None,
                'interactions_count': None,
                'route_used': None
            })
            print("❌ Database status not available")
            self.results['conclusion'] = 'WARN'
    
    def verify_auth_enforcement(self):
        """Test 4: Auth enforcement (no token path)"""
        print("🔍 Testing authentication enforcement...")
        
        protected_endpoints = [
            '/api/v1/scholarships',
            '/api/v1/analytics/summary'
        ]
        
        for endpoint in protected_endpoints:
            result = self.test_request('GET', endpoint)
            if result['status'] in [401, 403]:
                print(f"✅ {endpoint} - Properly protected (Status: {result['status']})")
                if endpoint == '/api/v1/scholarships':
                    self.results['auth']['scholarships_no_token_status'] = result['status']
                elif endpoint == '/api/v1/analytics/summary':
                    self.results['auth']['analytics_no_token_status'] = result['status']
            else:
                print(f"❌ {endpoint} - Auth bypass detected (Status: {result['status']})")
                self.results['conclusion'] = 'FAIL'
    
    def verify_core_functionality(self):
        """Test 5: Core functionality"""
        print("🔍 Testing core search functionality...")
        
        # Search GET
        result = self.test_request('GET', '/search')
        if result['status'] == 200 and result['response_data']:
            data = result['response_data']
            required_keys = {'items', 'total', 'page', 'page_size', 'filters', 'took_ms'}
            if required_keys.issubset(set(data.keys())):
                self.results['search']['get_status'] = 200
                self.results['search']['schema_ok'] = True
                self.results['search']['took_ms_present'] = 'took_ms' in data
                print("✅ Search GET - Schema OK")
            else:
                print(f"❌ Search GET - Missing keys: {required_keys - set(data.keys())}")
                self.results['conclusion'] = 'WARN'
        else:
            print(f"❌ Search GET failed - Status: {result['status']}")
            self.results['conclusion'] = 'WARN'
        
        # Search POST
        result = self.test_request('POST', '/search', json_data={"query": "merit"})
        self.results['search']['post_status'] = result['status']
        if result['status'] == 200:
            print("✅ Search POST - OK")
        else:
            print(f"❌ Search POST failed - Status: {result['status']}")
            self.results['conclusion'] = 'WARN'
        
        print("🔍 Testing eligibility functionality...")
        
        # Eligibility - valid case
        result = self.test_request('POST', '/eligibility/check', json_data={"gpa": 3.6})
        self.results['eligibility']['valid_status'] = result['status']
        if result['status'] == 200:
            print("✅ Eligibility valid case - OK")
        else:
            print(f"❌ Eligibility valid case failed - Status: {result['status']}")
            self.results['conclusion'] = 'WARN'
        
        # Eligibility - over max GPA
        result = self.test_request('POST', '/eligibility/check', json_data={"gpa": 4.3})
        self.results['eligibility']['over_max_status'] = result['status']
        if result['status'] == 422:
            print("✅ Eligibility over-max validation - OK")
        else:
            print(f"❌ Eligibility over-max validation - Status: {result['status']} (expected 422)")
            self.results['conclusion'] = 'WARN'
        
        # Eligibility - null GPA handling
        result = self.test_request('POST', '/eligibility/check', json_data={"gpa": None})
        self.results['eligibility']['null_gpa_status'] = result['status']
        if result['status'] in [200, 422]:
            print(f"✅ Eligibility null GPA handling - Status: {result['status']}")
        else:
            print(f"❌ Eligibility null GPA handling - Status: {result['status']}")
            self.results['conclusion'] = 'WARN'
    
    def verify_rate_limiting(self):
        """Test 6: Rate limiting (light probe)"""
        print("🔍 Testing rate limiting...")
        
        first_429_index = None
        retry_after = None
        requests_sent = 0
        
        for i in range(40):
            result = self.test_request('GET', '/search')
            requests_sent += 1
            
            if result['status'] == 429:
                first_429_index = i
                retry_after = result['headers_subset'].get('retry-after')
                print(f"✅ Rate limiting active - 429 at request #{i}")
                break
            elif result['status'] != 200:
                print(f"❌ Unexpected status during rate limit test: {result['status']}")
                break
        
        if first_429_index is None:
            print("📝 No 429 observed within 40 requests (likely dev thresholds)")
        
        self.results['rate_limit_probe'] = {
            'requests_sent': requests_sent,
            'first_429_index': first_429_index,
            'retry_after': retry_after
        }
    
    def verify_security_headers(self):
        """Test 7: Security headers"""
        print("🔍 Testing security headers...")
        
        # Test on multiple endpoints
        test_endpoints = ['/healthz', '/search']
        
        for endpoint in test_endpoints:
            result = self.test_request('GET', endpoint)
            headers = result['headers_subset']
            
            x_xss_present = bool(headers.get('x-xss-protection'))
            hsts_present = bool(headers.get('strict-transport-security'))
            
            self.results['headers'].update({
                'x_xss_protection_present': x_xss_present,
                'hsts_present': hsts_present
            })
            
            print(f"📝 {endpoint} headers:")
            print(f"  X-XSS-Protection: {'✅' if x_xss_present else '❌'}")
            print(f"  HSTS: {'✅' if hsts_present else '📝 Not set (OK for dev)'}")
            print(f"  X-Frame-Options: {'✅' if headers.get('x-frame-options') else '❌'}")
            print(f"  X-Content-Type-Options: {'✅' if headers.get('x-content-type-options') else '❌'}")
            break  # Only need one endpoint for header check
    
    def verify_trace_propagation(self):
        """Test 8: Observability cross-checks"""
        print("🔍 Testing trace propagation...")
        
        test_headers = {'X-Request-ID': 'test-trace-123'}
        result = self.test_request('GET', '/search', headers=test_headers)
        
        if result['status'] == 200:
            print("✅ Request with trace ID completed")
        else:
            print(f"❌ Trace test failed - Status: {result['status']}")
    
    def run_verification(self):
        """Run complete verification suite"""
        print(f"🚀 Starting API Verification - Base URL: {self.base_url}")
        print("=" * 60)
        
        try:
            self.verify_root_endpoint()
            self.verify_operational_endpoints()
            self.verify_database_status()
            self.verify_auth_enforcement()
            self.verify_core_functionality()
            self.verify_rate_limiting()
            self.verify_security_headers()
            self.verify_trace_propagation()
            
        except Exception as e:
            print(f"❌ Verification failed with error: {e}")
            self.results['conclusion'] = 'FAIL'
        
        print("=" * 60)
        print(f"🏁 Verification Complete - Overall: {self.results['conclusion']}")
        
        return self.results

def main():
    # Detect base URL from Replit environment
    base_url = "http://localhost:5000"  # Default fallback
    
    print("🔧 Detecting base URL...")
    
    # Test if local server is running
    try:
        response = requests.get(base_url, timeout=2)
        if response.status_code == 200:
            print(f"✅ Using local URL: {base_url}")
        else:
            print(f"❌ Local server not responding properly: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to {base_url}: {e}")
        return
    
    # Run verification
    verifier = APIVerifier(base_url)
    results = verifier.run_verification()
    
    # Save results
    with open('../QA_VERIFICATION_REPORT.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Reports saved:")
    print(f"   - QA_VERIFICATION_REPORT.json")
    print(f"   - QA_VERIFICATION_REPORT.md (will be generated)")
    
    return results

if __name__ == "__main__":
    main()