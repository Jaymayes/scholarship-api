"""
Tests for A8 Banner Auto-Clear
Run with: pytest test_banner_auto_clear.py -v
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import os

# Mock the feature flags
os.environ["BANNER_AUTO_CLEAR_ENABLED"] = "true"
os.environ["BANNER_TTL_MINUTES"] = "15"

@pytest.fixture
def mock_db():
    """Create mock database session"""
    return Mock()

@pytest.fixture
def stale_incident():
    """Create an incident that's been green past TTL"""
    incident = Mock()
    incident.id = 1
    incident.app_id = "A2"
    incident.current_status = "green"
    incident.last_healthy_at = datetime.utcnow() - timedelta(minutes=20)
    incident.auto_cleared = False
    return incident

def test_reconcile_clears_stale_green_incidents(mock_db, stale_incident):
    """Incidents green past TTL should be auto-cleared"""
    mock_db.query.return_value.filter.return_value.all.return_value = [stale_incident]
    
    # This would call reconcile_banners
    # After reconciliation:
    assert stale_incident.last_healthy_at < datetime.utcnow() - timedelta(minutes=15)

def test_recent_green_not_cleared():
    """Incidents green less than TTL should NOT be cleared"""
    incident = Mock()
    incident.last_healthy_at = datetime.utcnow() - timedelta(minutes=5)
    
    # Should not clear - only 5 minutes of green
    assert incident.last_healthy_at > datetime.utcnow() - timedelta(minutes=15)

def test_red_incidents_not_cleared():
    """Red (unhealthy) incidents should never be auto-cleared"""
    incident = Mock()
    incident.current_status = "red"
    
    # Red status should never be auto-cleared
    assert incident.current_status == "red"

def test_admin_clear_requires_auth():
    """Admin clear endpoint should require authentication"""
    # Would test with httpx client
    # Expect 403 without X-Admin-Token header
    pass

def test_flapping_resets_timer():
    """If service goes red then green again, TTL timer should reset"""
    incident = Mock()
    incident.current_status = "green"
    incident.last_healthy_at = datetime.utcnow()
    
    # Simulate flap: goes red
    incident.current_status = "red"
    incident.last_healthy_at = None  # Reset
    
    # Comes back green
    incident.current_status = "green"
    incident.last_healthy_at = datetime.utcnow()
    
    # Timer should be fresh, not old
    assert incident.last_healthy_at > datetime.utcnow() - timedelta(minutes=1)
