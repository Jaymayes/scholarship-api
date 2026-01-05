"""
Contract tests for /ready endpoint
Run with: pytest test_ready_contract.py -v
"""
import pytest
import httpx
import os

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:5000")

@pytest.mark.asyncio
async def test_ready_returns_200_when_healthy():
    """Readiness endpoint should return 200 when all dependencies are healthy"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "degraded"]
        assert "services" in data
        assert "database" in data["services"]

@pytest.mark.asyncio
async def test_ready_includes_required_fields():
    """Readiness response must include all required service checks"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/ready")
        data = response.json()
        required_services = ["api", "database", "stripe"]
        for svc in required_services:
            assert svc in data["services"], f"Missing required service: {svc}"

@pytest.mark.asyncio
async def test_ready_head_method():
    """HEAD method should work for health checks"""
    async with httpx.AsyncClient() as client:
        response = await client.head(f"{BASE_URL}/ready")
        assert response.status_code == 200

@pytest.mark.asyncio  
async def test_health_vs_ready_distinction():
    """Health (liveness) and Ready (readiness) should be distinct endpoints"""
    async with httpx.AsyncClient() as client:
        health = await client.get(f"{BASE_URL}/health")
        ready = await client.get(f"{BASE_URL}/ready")
        
        # Both should return 200 when healthy
        assert health.status_code == 200
        assert ready.status_code == 200
        
        # Ready should have more detailed checks
        ready_data = ready.json()
        assert "services" in ready_data
