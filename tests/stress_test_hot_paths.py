# Incident: Hot-Path Canary Tests
# Stress test POST /matching/predict and /documents/bulk-analyze
# Verify no auth regressions and stable P95

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from main import app


class HotPathStressTest:
    """
    Stress testing for critical hot paths
    Validates performance under load and auth stability
    """
    
    def __init__(self, client: TestClient):
        self.client = client
        self.results = {
            "predictive_matching": [],
            "document_bulk_analyze": [],
            "auth_stability": []
        }
    
    def run_stress_test(
        self,
        endpoint: str,
        method: str,
        payload: Dict,
        headers: Dict,
        num_requests: int = 100,
        concurrent_workers: int = 10
    ) -> Dict:
        """
        Run stress test on an endpoint
        
        Returns:
        - Latency statistics (P50, P95, P99)
        - Error rate
        - Auth regression detection
        """
        latencies = []
        errors = []
        auth_failures = []
        
        def make_request():
            start = time.perf_counter()
            
            try:
                if method == "POST":
                    response = self.client.post(endpoint, json=payload, headers=headers)
                elif method == "GET":
                    response = self.client.get(endpoint, headers=headers)
                
                latency_ms = (time.perf_counter() - start) * 1000
                
                # Check for auth regressions
                if response.status_code == 401:
                    auth_failures.append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "latency_ms": latency_ms
                    })
                elif response.status_code >= 500:
                    errors.append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "latency_ms": latency_ms,
                        "body": response.text[:200]
                    })
                else:
                    latencies.append(latency_ms)
                
                return latency_ms, response.status_code
            except Exception as e:
                errors.append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
                return None, None
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in futures]
        
        # Calculate statistics
        stats = self._calculate_stats(latencies)
        stats["total_requests"] = num_requests
        stats["successful_requests"] = len(latencies)
        stats["error_count"] = len(errors)
        stats["auth_failures"] = len(auth_failures)
        stats["error_rate"] = (len(errors) / num_requests) * 100
        stats["auth_failure_rate"] = (len(auth_failures) / num_requests) * 100
        stats["errors"] = errors[:5]  # Sample errors
        stats["auth_failures_sample"] = auth_failures[:5]
        
        return stats
    
    def _calculate_stats(self, latencies: List[float]) -> Dict:
        """Calculate latency percentiles"""
        if not latencies:
            return {
                "p50": 0, "p90": 0, "p95": 0, "p99": 0,
                "min": 0, "max": 0, "mean": 0, "stddev": 0
            }
        
        sorted_latencies = sorted(latencies)
        
        def percentile(p: float) -> float:
            idx = int(len(sorted_latencies) * p)
            return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
        
        return {
            "p50": percentile(0.50),
            "p90": percentile(0.90),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
            "min": min(latencies),
            "max": max(latencies),
            "mean": statistics.mean(latencies),
            "stddev": statistics.stdev(latencies) if len(latencies) > 1 else 0
        }
    
    def print_results(self, test_name: str, stats: Dict):
        """Print stress test results"""
        print(f"\n{'='*80}")
        print(f"🔥 STRESS TEST: {test_name}")
        print(f"{'='*80}")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful_requests']} ({(stats['successful_requests']/stats['total_requests']*100):.1f}%)")
        print(f"Errors: {stats['error_count']} ({stats['error_rate']:.1f}%)")
        print(f"Auth Failures: {stats['auth_failures']} ({stats['auth_failure_rate']:.1f}%)")
        print(f"\nLatency Distribution:")
        print(f"  P50: {stats['p50']:.1f}ms")
        print(f"  P90: {stats['p90']:.1f}ms")
        print(f"  P95: {stats['p95']:.1f}ms  {'✅' if stats['p95'] <= 120 else '⚠️ Above 120ms target'}")
        print(f"  P99: {stats['p99']:.1f}ms")
        print(f"  Mean: {stats['mean']:.1f}ms ± {stats['stddev']:.1f}ms")
        
        if stats['errors']:
            print(f"\n⚠️ Sample Errors:")
            for err in stats['errors'][:3]:
                print(f"  - {err}")
        
        if stats['auth_failures_sample']:
            print(f"\n🔴 Auth Failures Detected:")
            for af in stats['auth_failures_sample'][:3]:
                print(f"  - {af}")
        
        print(f"{'='*80}\n")


@pytest.mark.stress
def test_predictive_matching_stress(auth_headers, sample_user_profile):
    """
    Stress test: POST /api/v1/matching/predict
    100 concurrent requests, verify P95 stable and no auth regressions
    """
    client = TestClient(app)
    tester = HotPathStressTest(client)
    
    payload = {
        "user_profile": sample_user_profile,
        "scholarship_ids": None,
        "analysis_depth": "quick",
        "max_results": 5
    }
    
    stats = tester.run_stress_test(
        endpoint="/api/v1/matching/predict",
        method="POST",
        payload=payload,
        headers=auth_headers,
        num_requests=100,
        concurrent_workers=10
    )
    
    tester.print_results("Predictive Matching", stats)
    
    # Assertions
    assert stats['error_rate'] < 5.0, f"Error rate {stats['error_rate']:.1f}% exceeds 5%"
    assert stats['auth_failure_rate'] == 0.0, f"Auth regressions detected: {stats['auth_failures']} failures"
    assert stats['p95'] < 5000, f"P95 {stats['p95']:.1f}ms exceeds 5000ms threshold for AI endpoint"


@pytest.mark.stress
def test_document_bulk_analyze_stress(auth_headers):
    """
    Stress test: POST /api/v1/documents/bulk-analyze
    50 concurrent requests (expensive operation), verify stability
    """
    client = TestClient(app)
    tester = HotPathStressTest(client)
    
    payload = {
        "document_ids": ["doc-1", "doc-2", "doc-3"],
        "analysis_types": ["extract_gpa", "extract_activities"]
    }
    
    stats = tester.run_stress_test(
        endpoint="/api/v1/documents/bulk-analyze",
        method="POST",
        payload=payload,
        headers=auth_headers,
        num_requests=50,
        concurrent_workers=5
    )
    
    tester.print_results("Document Bulk Analyze", stats)
    
    # Assertions
    assert stats['error_rate'] < 10.0, f"Error rate {stats['error_rate']:.1f}% exceeds 10%"
    assert stats['auth_failure_rate'] == 0.0, f"Auth regressions detected: {stats['auth_failures']} failures"


@pytest.mark.stress
def test_quick_wins_stress(auth_headers, sample_user_profile):
    """
    Stress test: POST /api/v1/matching/quick-wins
    Verify performance under load
    """
    client = TestClient(app)
    tester = HotPathStressTest(client)
    
    payload = {
        "user_profile": sample_user_profile,
        "limit": 5
    }
    
    stats = tester.run_stress_test(
        endpoint="/api/v1/matching/quick-wins",
        method="POST",
        payload=payload,
        headers=auth_headers,
        num_requests=100,
        concurrent_workers=10
    )
    
    tester.print_results("Quick Wins Endpoint", stats)
    
    # Assertions
    assert stats['error_rate'] < 5.0, f"Error rate {stats['error_rate']:.1f}% exceeds 5%"
    assert stats['auth_failure_rate'] == 0.0, "Auth regressions detected"


@pytest.mark.stress
def test_stretch_opportunities_stress(auth_headers, sample_user_profile):
    """
    Stress test: POST /api/v1/matching/stretch-opportunities
    Verify performance and stability
    """
    client = TestClient(app)
    tester = HotPathStressTest(client)
    
    payload = {
        "user_profile": sample_user_profile,
        "limit": 5
    }
    
    stats = tester.run_stress_test(
        endpoint="/api/v1/matching/stretch-opportunities",
        method="POST",
        payload=payload,
        headers=auth_headers,
        num_requests=100,
        concurrent_workers=10
    )
    
    tester.print_results("Stretch Opportunities Endpoint", stats)
    
    # Assertions
    assert stats['error_rate'] < 5.0, f"Error rate {stats['error_rate']:.1f}% exceeds 5%"
    assert stats['auth_failure_rate'] == 0.0, "Auth regressions detected"


if __name__ == "__main__":
    # Run stress tests manually
    pytest.main([__file__, "-v", "-m", "stress", "-s"])
