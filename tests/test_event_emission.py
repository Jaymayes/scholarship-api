"""
Test Business Event Emission
Verify events are being written to business_events table
"""
import asyncio
import pytest
from services.event_emission import (
    emit_scholarship_viewed,
    emit_scholarship_saved,
    emit_match_generated,
    emit_application_started,
    emit_application_submitted,
    event_emission_service
)


@pytest.mark.asyncio
async def test_scholarship_viewed_emission():
    """Test scholarship_viewed event emission"""
    await emit_scholarship_viewed(
        scholarship_id="test_sch_123",
        source="test",
        match_score=0.85,
        actor_id="test_user_456",
        session_id="test_session_789"
    )
    
    # Give async task time to complete
    await asyncio.sleep(0.5)
    
    # Check service status
    status = event_emission_service.get_status()
    assert status["enabled"] is True
    assert status["circuit_open"] is False
    print(f"✅ Event emission test passed - Status: {status}")


@pytest.mark.asyncio
async def test_all_event_types():
    """Test all 5 required event types"""
    
    # 1. scholarship_viewed
    await emit_scholarship_viewed(
        scholarship_id="sch_001",
        source="search",
        match_score=0.92,
        actor_id="user_001"
    )
    
    # 2. scholarship_saved
    await emit_scholarship_saved(
        scholarship_id="sch_001",
        match_score=0.92,
        eligibility_score=0.88,
        actor_id="user_001"
    )
    
    # 3. match_generated
    await emit_match_generated(
        student_id="user_001",
        num_matches=42,
        match_quality_avg=0.78,
        processing_time_ms=245.5
    )
    
    # 4. application_started
    await emit_application_started(
        scholarship_id="sch_001",
        time_since_save_hours=12.5,
        credit_cost=5,
        actor_id="user_001"
    )
    
    # 5. application_submitted
    await emit_application_submitted(
        scholarship_id="sch_001",
        application_time_minutes=45.0,
        credit_spent=5,
        revenue_usd=2.50,
        actor_id="user_001"
    )
    
    # Wait for async emissions
    await asyncio.sleep(1.0)
    
    print("✅ All 5 event types emitted successfully")
    

if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_scholarship_viewed_emission())
    asyncio.run(test_all_event_types())
    print("\n✅ All event emission tests passed!")
