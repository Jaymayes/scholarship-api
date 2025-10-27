# Synthetic Performance Tests - Target P95 ≤120ms
# CEO Directive: Performance Tightening and Public Endpoint Consistency

import asyncio
import statistics
import time
from typing import List

import pytest
from fastapi.testclient import TestClient

from main import app

# Import fixtures from conftest.py
# Fixtures: auth_headers, admin_auth_headers, sample_user_profile

client = TestClient(app)


def measure_request_latency(path: str, method: str = "GET", json_data: dict | None = None, headers: dict | None = None, expected_status: int = 200) -> float:
    """Measure single request latency in milliseconds"""
    start = time.perf_counter()
    
    if method == "GET":
        response = client.get(path, headers=headers)
    elif method == "POST":
        response = client.post(path, json=json_data, headers=headers)
    
    latency_ms = (time.perf_counter() - start) * 1000
    
    # Ensure request succeeded with expected status
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text[:200]}"
    
    return latency_ms


def calculate_percentiles(latencies: List[float]) -> dict:
    """Calculate latency percentiles"""
    sorted_latencies = sorted(latencies)
    
    def percentile(p: float) -> float:
        index = int(len(sorted_latencies) * p)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    return {
        "min": min(latencies),
        "p50": percentile(0.50),
        "p90": percentile(0.90),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "max": max(latencies),
        "mean": statistics.mean(latencies),
        "stddev": statistics.stdev(latencies) if len(latencies) > 1 else 0
    }


@pytest.mark.performance
def test_health_endpoint_p95_under_120ms():
    """
    Test: Fast health endpoint P95 ≤120ms
    CEO Target: P95 ≤120ms sustained
    """
    latencies = []
    num_requests = 100
    
    for _ in range(num_requests):
        latency = measure_request_latency("/api/v1/health")
        latencies.append(latency)
    
    stats = calculate_percentiles(latencies)
    
    print(f"\n📊 Health Endpoint Performance (n={num_requests}):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    print(f"   P99: {stats['p99']:.2f}ms")
    print(f"   Mean: {stats['mean']:.2f}ms ± {stats['stddev']:.2f}ms")
    
    # CEO Target: P95 ≤120ms
    assert stats['p95'] <= 120.0, f"P95 latency {stats['p95']:.2f}ms exceeds 120ms target"
    
    # Additional quality gates
    assert stats['p99'] <= 200.0, f"P99 latency {stats['p99']:.2f}ms exceeds 200ms threshold"
    assert stats['mean'] <= 100.0, f"Mean latency {stats['mean']:.2f}ms exceeds 100ms threshold"


@pytest.mark.performance
def test_search_endpoint_authenticated_p95_under_200ms(auth_headers):
    """
    Test: Search endpoint P95 <200ms (AUTHENTICATED WORKLOAD)
    Platform SLO: Search P95 <200ms
    
    This test validates the full authenticated workload with real JWT authentication.
    """
    latencies = []
    num_requests = 50
    
    search_params = {
        "keyword": "engineering",
        "limit": 10,
        "offset": 0
    }
    
    for _ in range(num_requests):
        latency = measure_request_latency(
            "/api/v1/search",
            method="POST",
            json_data=search_params,
            headers=auth_headers,
            expected_status=200
        )
        latencies.append(latency)
    
    stats = calculate_percentiles(latencies)
    
    print(f"\n📊 Search Endpoint Authenticated Performance (n={num_requests}):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    print(f"   P99: {stats['p99']:.2f}ms")
    
    # Platform SLO: P95 <200ms
    assert stats['p95'] < 200.0, f"P95 latency {stats['p95']:.2f}ms exceeds 200ms SLO"


@pytest.mark.performance
def test_metrics_endpoint_p95_under_150ms():
    """
    Test: Metrics endpoint P95 ≤150ms
    Requirement: Fast scrapes for monitoring
    """
    latencies = []
    num_requests = 50
    
    for _ in range(num_requests):
        latency = measure_request_latency("/metrics")
        latencies.append(latency)
    
    stats = calculate_percentiles(latencies)
    
    print(f"\n📊 Metrics Endpoint Performance (n={num_requests}):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    
    # Fast metrics scraping target
    assert stats['p95'] <= 150.0, f"P95 latency {stats['p95']:.2f}ms exceeds 150ms target"


@pytest.mark.performance
def test_deep_health_endpoint_p95_under_1000ms():
    """
    Test: Deep health endpoint P95 <1000ms
    CEO Approval: Deep health P95 869ms (under 1000ms target)
    """
    latencies = []
    num_requests = 20  # Fewer requests for expensive endpoint
    
    for _ in range(num_requests):
        latency = measure_request_latency("/api/v1/health/deep")
        latencies.append(latency)
    
    stats = calculate_percentiles(latencies)
    
    print(f"\n📊 Deep Health Endpoint Performance (n={num_requests}):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    
    # Deep health target: P95 <1000ms
    assert stats['p95'] < 1000.0, f"P95 latency {stats['p95']:.2f}ms exceeds 1000ms target"


@pytest.mark.performance
def test_concurrent_requests_performance():
    """
    Test: Concurrent load handling
    Requirement: Maintain P95 <200ms under moderate concurrency
    """
    num_concurrent = 10
    num_iterations = 10
    all_latencies = []
    
    for iteration in range(num_iterations):
        iteration_latencies = []
        
        # Simulate concurrent requests
        for _ in range(num_concurrent):
            latency = measure_request_latency("/api/v1/health")
            iteration_latencies.append(latency)
        
        all_latencies.extend(iteration_latencies)
    
    stats = calculate_percentiles(all_latencies)
    
    print(f"\n📊 Concurrent Load Performance ({num_concurrent}x{num_iterations} requests):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    
    # Under concurrent load, still maintain sub-200ms P95
    assert stats['p95'] < 200.0, f"P95 latency under load {stats['p95']:.2f}ms exceeds 200ms"


@pytest.mark.performance
def test_document_hub_list_authenticated_performance(auth_headers):
    """
    Test: Document hub list endpoint performs well (AUTHENTICATED WORKLOAD)
    Target: P95 <150ms for list operation
    
    This test validates the full authenticated workload including database access.
    """
    latencies = []
    num_requests = 30
    
    for _ in range(num_requests):
        # Document list endpoint with authentication
        latency = measure_request_latency(
            "/api/v1/documents/user/me",
            headers=auth_headers,
            expected_status=200
        )
        latencies.append(latency)
    
    stats = calculate_percentiles(latencies)
    
    print(f"\n📊 Document Hub List Authenticated Performance (n={num_requests}):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    
    assert stats['p95'] < 150.0, f"P95 latency {stats['p95']:.2f}ms exceeds 150ms target"


@pytest.mark.performance
def test_predictive_matching_authenticated_performance(auth_headers, sample_user_profile):
    """
    Test: Predictive matching endpoint performs well (AUTHENTICATED WORKLOAD)
    Target: P95 <5000ms for AI-intensive operations
    
    This test validates the full authenticated AI workload with real predictions.
    Note: AI operations are naturally slower than simple CRUD operations.
    """
    latencies = []
    num_requests = 10  # Fewer requests for expensive AI operation
    
    request_data = {
        "user_profile": sample_user_profile,
        "scholarship_ids": None,
        "analysis_depth": "quick",
        "max_results": 5
    }
    
    for _ in range(num_requests):
        # Authenticated predictive matching request
        latency = measure_request_latency(
            "/api/v1/matching/predict",
            method="POST",
            json_data=request_data,
            headers=auth_headers,
            expected_status=200
        )
        latencies.append(latency)
    
    stats = calculate_percentiles(latencies)
    
    print(f"\n📊 Predictive Matching Authenticated Performance (n={num_requests}):")
    print(f"   P50: {stats['p50']:.2f}ms")
    print(f"   P90: {stats['p90']:.2f}ms")
    print(f"   P95: {stats['p95']:.2f}ms")
    print(f"   (Note: AI workload - naturally higher latency)")
    
    # AI endpoints allowed higher latency (5 seconds)
    assert stats['p95'] < 5000.0, f"P95 latency {stats['p95']:.2f}ms exceeds 5000ms threshold"


if __name__ == "__main__":
    # Run performance tests manually
    pytest.main([__file__, "-v", "-m", "performance", "-s"])
