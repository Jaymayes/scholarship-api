"""
Tests for A8 Demo Mode
Run with: pytest test_demo_mode.py -v
"""
import pytest
import httpx
import os

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:5000")

@pytest.mark.asyncio
async def test_live_mode_excludes_test_data():
    """Live mode should NOT show test/simulated data"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/tiles/revenue?mode=live")
        data = response.json()
        
        assert data["mode"] == "live"
        assert data["label"] == "Live Data"
        assert data["warning"] is None
        
        # Verify no test data in response
        for item in data["data"]:
            assert item.get("namespace") != "simulated_audit"
            assert item.get("stripe_mode") != "test"

@pytest.mark.asyncio
async def test_demo_mode_shows_only_test_data():
    """Demo mode should ONLY show test/simulated data"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/tiles/revenue?mode=demo")
        data = response.json()
        
        assert data["mode"] == "demo"
        assert "DEMO" in data["label"]
        assert data["warning"] is not None
        
        # Verify only test data in response
        for item in data["data"]:
            is_test = (
                item.get("namespace") == "simulated_audit" or
                item.get("stripe_mode") == "test"
            )
            assert is_test, f"Live data found in demo mode: {item}"

@pytest.mark.asyncio
async def test_default_mode_is_live():
    """Default mode without parameter should be live"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/tiles/revenue")
        data = response.json()
        
        assert data["mode"] == "live"

@pytest.mark.asyncio
async def test_demo_mode_config_endpoint():
    """Config endpoint should return demo mode state"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/tiles/config/demo-mode")
        data = response.json()
        
        assert "enabled" in data
        assert isinstance(data["enabled"], bool)

@pytest.mark.asyncio
async def test_mode_switching_isolation():
    """Switching modes should not leak data between modes"""
    async with httpx.AsyncClient() as client:
        # Get live data
        live = await client.get(f"{BASE_URL}/api/tiles/revenue?mode=live")
        live_ids = {item["id"] for item in live.json()["data"]}
        
        # Get demo data
        demo = await client.get(f"{BASE_URL}/api/tiles/revenue?mode=demo")
        demo_ids = {item["id"] for item in demo.json()["data"]}
        
        # IDs should not overlap
        overlap = live_ids & demo_ids
        assert len(overlap) == 0, f"Data leak detected: {overlap}"
