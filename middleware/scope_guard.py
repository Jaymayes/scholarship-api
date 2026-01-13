"""
CEO v2.6 Scope Guard - HITL-CEO-20260113-CUTOVER-V2
Fail-fast on ASSIGNED_APP mismatch during startup.
"""
import os
import sys


def verify_scope_guard() -> None:
    """Verify ASSIGNED_APP matches expected service identity. Fail-fast on mismatch."""
    assigned_app = os.getenv("ASSIGNED_APP", "")
    expected_app = "scholarship_api"
    
    if assigned_app and assigned_app != expected_app:
        print(f"SCOPE GUARD VIOLATION: ASSIGNED_APP={assigned_app} does not match expected={expected_app}")
        print("Exiting to prevent cross-service contamination.")
        sys.exit(1)
    
    os.environ["ASSIGNED_APP"] = expected_app
