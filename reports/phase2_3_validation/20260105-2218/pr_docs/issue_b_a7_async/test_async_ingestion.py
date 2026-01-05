"""
Tests for A7 Async Ingestion
Run with: pytest test_async_ingestion.py -v
"""
import pytest
import httpx
import uuid
import os

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:5000")

@pytest.mark.asyncio
async def test_ingest_returns_202():
    """Ingest endpoint should return 202 Accepted"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/ingest",
            json={
                "event_type": "test_event",
                "payload": {"test": True},
                "source": "pytest"
            }
        )
        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == True
        assert "event_id" in data

@pytest.mark.asyncio
async def test_idempotency_key():
    """Same idempotency key should return cached result"""
    idempotency_key = str(uuid.uuid4())
    
    async with httpx.AsyncClient() as client:
        # First request
        r1 = await client.post(
            f"{BASE_URL}/api/v1/ingest",
            json={"event_type": "test", "payload": {}},
            headers={"X-Idempotency-Key": idempotency_key}
        )
        
        # Second request with same key
        r2 = await client.post(
            f"{BASE_URL}/api/v1/ingest",
            json={"event_type": "test", "payload": {}},
            headers={"X-Idempotency-Key": idempotency_key}
        )
        
        assert r1.json()["event_id"] == r2.json()["event_id"]
        assert r2.json()["processing"] == "cached"

@pytest.mark.asyncio
async def test_status_endpoint():
    """Should be able to check event processing status"""
    async with httpx.AsyncClient() as client:
        # Ingest event
        r = await client.post(
            f"{BASE_URL}/api/v1/ingest",
            json={"event_type": "status_test", "payload": {}}
        )
        event_id = r.json()["event_id"]
        
        # Check status
        status = await client.get(f"{BASE_URL}/api/v1/ingest/{event_id}/status")
        assert status.status_code == 200
        assert "status" in status.json()
