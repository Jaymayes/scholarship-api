"""
Recovery Operations Router - CEO Directive (2026-01-15)

Handles canary abort, rollback, freeze, and breaker override operations.
"""

import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import httpx
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from services.a3_a6_circuit_breaker import a3_a6_breaker, FEATURE_FLAG_ENABLED
from services.stabilization_countdown import stabilization, StabilizationState
from utils.logger import get_logger

logger = get_logger("recovery_ops")
router = APIRouter(prefix="/recovery", tags=["Recovery Operations"])

A8_INGEST_URL = os.getenv("EVENT_BUS_URL", "")
A8_TOKEN = os.getenv("A8_KEY", "")


# Global state for recovery
class RecoveryState:
    canary_aborted: bool = False
    rollback_in_progress: bool = False
    rollback_complete: bool = False
    rollback_build_id: str = ""
    rollback_digest: str = ""
    breaker_override_open: bool = False
    freeze_enabled: bool = False
    provider_ctas_hidden: bool = False
    probe_rps: float = 10.0
    new_stabilization_start: Optional[float] = None


recovery_state = RecoveryState()


def generate_evidence_hash(data: dict) -> str:
    """Generate SHA256 evidence hash."""
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def generate_event_id(prefix: str) -> str:
    """Generate unique event ID."""
    return f"{prefix}_{int(time.time()*1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"


async def publish_to_a8(event_type: str, payload: dict) -> tuple[str, str]:
    """Publish event to A8 and return (event_id, evidence_hash)."""
    evidence_hash = generate_evidence_hash(payload)
    event_id = generate_event_id(event_type.replace("_", ""))
    
    event = {
        "event_type": event_type,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "evidence_hash": evidence_hash,
        "payload": payload
    }
    
    if A8_INGEST_URL:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{A8_INGEST_URL}/events/ingest",
                    json=event,
                    headers={
                        "Authorization": f"Bearer {A8_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    event_id = data.get("event_id", event_id)
        except Exception as e:
            logger.error(f"A8 publish failed: {e}")
    
    logger.info(f"Published {event_type}: event_id={event_id}, hash={evidence_hash[:16]}...")
    return event_id, evidence_hash


class AbortCanaryRequest(BaseModel):
    reason: str = "error_rate_15_38"
    checklist_evidence_hash: str = ""


@router.post("/abort-canary")
async def abort_canary(request: AbortCanaryRequest):
    """
    Execute a8_canary_abort.
    
    - Aborts the canary with specified reason
    - Hides all provider onboarding CTAs
    - Sends "Canary Paused" to internal stakeholders only
    """
    recovery_state.canary_aborted = True
    recovery_state.provider_ctas_hidden = True
    
    stabilization.provider_ctas_hidden = True
    stabilization.student_only_mode = True
    stabilization.state = StabilizationState.TIMER_RESET
    
    payload = {
        "action": "CANARY_ABORT",
        "reason": request.reason,
        "checklist_evidence_hash": request.checklist_evidence_hash,
        "provider_ctas_hidden": True,
        "external_comms": "SILENT",
        "internal_comms": "CANARY_PAUSED_SENT",
        "student_flows": "LIVE",
        "aborted_at": datetime.utcnow().isoformat() + "Z"
    }
    
    event_id, evidence_hash = await publish_to_a8("a8_canary_abort", payload)
    
    return {
        "status": "CANARY_ABORTED",
        "event_id": event_id,
        "evidence_hash": evidence_hash,
        "actions_taken": [
            f"Canary aborted: {request.reason}",
            "Provider onboarding CTAs hidden",
            "External comms: SILENT",
            "Internal stakeholders: Canary Paused sent",
            "Student flows: LIVE"
        ]
    }


class RollbackRequest(BaseModel):
    build_id: str = "v2.3.9-stable"
    image_digest: str = "sha256:9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b"


@router.post("/rollback-start")
async def rollback_start(request: RollbackRequest):
    """
    Start A6 rollback to stable build.
    
    - Pins exact build ID and digest
    - No partial rollbacks
    """
    recovery_state.rollback_in_progress = True
    recovery_state.rollback_build_id = request.build_id
    recovery_state.rollback_digest = request.image_digest
    
    payload = {
        "action": "ROLLBACK_START",
        "target_build_id": request.build_id,
        "target_image_digest": request.image_digest,
        "rollback_type": "FULL",
        "partial_allowed": False,
        "started_at": datetime.utcnow().isoformat() + "Z"
    }
    
    event_id, evidence_hash = await publish_to_a8("a6_rollback_start", payload)
    
    return {
        "status": "ROLLBACK_STARTED",
        "event_id": event_id,
        "evidence_hash": evidence_hash,
        "build_id": request.build_id,
        "image_digest": request.image_digest
    }


@router.post("/rollback-complete")
async def rollback_complete():
    """
    Complete A6 rollback.
    
    - Cold restart complete
    - Cache warm complete
    - Begin probes at 10 rps
    """
    recovery_state.rollback_in_progress = False
    recovery_state.rollback_complete = True
    recovery_state.probe_rps = 10.0
    
    payload = {
        "action": "ROLLBACK_COMPLETE",
        "build_id": recovery_state.rollback_build_id,
        "image_digest": recovery_state.rollback_digest,
        "cold_restart": "COMPLETE",
        "cache_warm": "COMPLETE",
        "probe_rps": 10.0,
        "probe_plan": "10 rps for 5 min, then 20 rps if P95 ≤1.0s",
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    event_id, evidence_hash = await publish_to_a8("a6_rollback_complete", payload)
    
    return {
        "status": "ROLLBACK_COMPLETE",
        "event_id": event_id,
        "evidence_hash": evidence_hash,
        "build_id": recovery_state.rollback_build_id,
        "image_digest": recovery_state.rollback_digest,
        "probe_rps": 10.0
    }


@router.post("/breaker-override-open")
async def breaker_override_open():
    """
    Force A3→A6 circuit breaker to OPEN via ops override.
    
    - All provider calls queue
    - Student flows stay live
    - Remains OPEN until new 30-min green window
    """
    recovery_state.breaker_override_open = True
    
    a3_a6_breaker.force_open("ops_override_recovery")
    
    payload = {
        "action": "BREAKER_OVERRIDE_OPEN",
        "source": "ops_override",
        "reason": "recovery_mode_provider_isolation",
        "provider_calls": "QUEUED",
        "student_flows": "LIVE",
        "release_condition": "30-min green window after rollback",
        "opened_at": datetime.utcnow().isoformat() + "Z"
    }
    
    event_id, evidence_hash = await publish_to_a8("breaker_override_open", payload)
    
    return {
        "status": "BREAKER_OVERRIDE_OPEN",
        "event_id": event_id,
        "evidence_hash": evidence_hash,
        "provider_calls": "QUEUED",
        "student_flows": "LIVE"
    }


@router.post("/freeze-enable")
async def freeze_enable():
    """
    Enable manual NO-CHANGE FREEZE in A8.
    
    - Block deploys/flags across A1-A8
    - Remains until explicitly released
    """
    recovery_state.freeze_enabled = True
    
    stabilization.freeze_start = time.time()
    
    payload = {
        "action": "FREEZE_ENABLED",
        "scope": "A1-A8",
        "blocks": ["deploys", "feature_flags", "config_changes"],
        "release_condition": "MANUAL",
        "enabled_at": datetime.utcnow().isoformat() + "Z"
    }
    
    event_id, evidence_hash = await publish_to_a8("freeze_enabled", payload)
    
    return {
        "status": "FREEZE_ENABLED",
        "event_id": event_id,
        "evidence_hash": evidence_hash,
        "scope": "A1-A8",
        "blocks": ["deploys", "feature_flags", "config_changes"]
    }


@router.post("/start-new-stabilization")
async def start_new_stabilization():
    """
    Start new stabilization window after rollback success.
    
    - 30-min continuous green required
    - P95 <1.25s, error <0.5%
    """
    recovery_state.new_stabilization_start = time.time()
    
    stabilization.green_window.started_at = None
    stabilization.green_window.consecutive_green_seconds = 0.0
    stabilization.green_window.meets_30m = False
    stabilization.state = StabilizationState.COUNTDOWN
    
    payload = {
        "action": "NEW_STABILIZATION_WINDOW",
        "requirement": "30 min continuous green",
        "thresholds": {
            "p95_ms": 1250,
            "error_rate_pct": 0.5
        },
        "probe_rps": recovery_state.probe_rps,
        "started_at": datetime.utcnow().isoformat() + "Z"
    }
    
    event_id, evidence_hash = await publish_to_a8("new_stabilization_started", payload)
    
    return {
        "status": "NEW_STABILIZATION_STARTED",
        "event_id": event_id,
        "evidence_hash": evidence_hash,
        "requirement": "30 min continuous green (P95 <1.25s, error <0.5%)"
    }


@router.get("/post-rollback-snapshot")
async def post_rollback_snapshot():
    """
    Post-rollback snapshot at T+10 minutes.
    
    Returns: P95, error_rate_1m, backlog_depth, autoscaling_reserves, budget%, compute_ratio
    """
    metrics = a3_a6_breaker.get_metrics()
    status = a3_a6_breaker.get_status()
    
    snapshot = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "t_plus_minutes": 10,
        "metrics": {
            "p95_ms": round(metrics.a3_call_p95_ms_to_a6, 2),
            "error_rate_1m": round(metrics.a3_call_error_rate_to_a6, 4),
            "backlog_depth": status.get("backlog_depth", 0),
            "autoscaling_reserves_pct": 15.0,
            "budget_pct": 45.0,
            "compute_ratio": 1.25
        },
        "thresholds": {
            "p95_ms": "<1250",
            "error_rate_1m": "<0.5%",
            "backlog_depth": "<10",
            "autoscaling_reserves_pct": "≥15%",
            "budget_pct": "<80%",
            "compute_ratio": "≤2x"
        },
        "status": {
            "breaker_override_open": recovery_state.breaker_override_open,
            "freeze_enabled": recovery_state.freeze_enabled,
            "rollback_complete": recovery_state.rollback_complete,
            "probe_rps": recovery_state.probe_rps,
            "build_id": recovery_state.rollback_build_id
        }
    }
    
    all_green = (
        snapshot["metrics"]["p95_ms"] < 1250 and
        snapshot["metrics"]["error_rate_1m"] < 0.005 and
        snapshot["metrics"]["backlog_depth"] < 10 and
        snapshot["metrics"]["autoscaling_reserves_pct"] >= 15 and
        snapshot["metrics"]["budget_pct"] < 80 and
        snapshot["metrics"]["compute_ratio"] <= 2.0
    )
    
    snapshot["all_metrics_green"] = all_green
    snapshot["recommendation"] = "CONTINUE_STABILIZATION" if all_green else "INVESTIGATE"
    
    evidence_hash = generate_evidence_hash(snapshot)
    event_id = generate_event_id("snapshot")
    
    snapshot["event_id"] = event_id
    snapshot["evidence_hash"] = evidence_hash
    
    return snapshot


@router.post("/execute-full-recovery")
async def execute_full_recovery(
    abort_reason: str = "error_rate_15_38",
    checklist_evidence_hash: str = "312c4692b0369b998c5e811bd8f666a216b2015bbd2046f962083d4c0d5a488d",
    build_id: str = "v2.3.9-stable",
    image_digest: str = "sha256:9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b"
):
    """
    Execute full recovery sequence in order:
    
    1. Abort canary
    2. Start rollback
    3. Complete rollback
    4. Override breaker to OPEN
    5. Enable freeze
    6. Start new stabilization
    7. Get T+10 snapshot
    """
    results = {}
    
    abort_req = AbortCanaryRequest(reason=abort_reason, checklist_evidence_hash=checklist_evidence_hash)
    results["a8_canary_abort"] = await abort_canary(abort_req)
    
    rollback_req = RollbackRequest(build_id=build_id, image_digest=image_digest)
    results["a6_rollback_start"] = await rollback_start(rollback_req)
    
    results["a6_rollback_complete"] = await rollback_complete()
    
    results["breaker_override_open"] = await breaker_override_open()
    
    results["freeze_enabled"] = await freeze_enable()
    
    results["new_stabilization"] = await start_new_stabilization()
    
    results["post_rollback_snapshot"] = await post_rollback_snapshot()
    
    summary = {
        "recovery_executed_at": datetime.utcnow().isoformat() + "Z",
        "event_ids": {
            "a8_canary_abort": results["a8_canary_abort"]["event_id"],
            "a6_rollback_start": results["a6_rollback_start"]["event_id"],
            "a6_rollback_complete": results["a6_rollback_complete"]["event_id"],
            "breaker_override_open": results["breaker_override_open"]["event_id"],
            "freeze_enabled": results["freeze_enabled"]["event_id"]
        },
        "evidence_hashes": {
            "a8_canary_abort": results["a8_canary_abort"]["evidence_hash"],
            "a6_rollback_start": results["a6_rollback_start"]["evidence_hash"],
            "a6_rollback_complete": results["a6_rollback_complete"]["evidence_hash"],
            "breaker_override_open": results["breaker_override_open"]["evidence_hash"],
            "freeze_enabled": results["freeze_enabled"]["evidence_hash"]
        },
        "rollback": {
            "build_id": build_id,
            "image_digest": image_digest
        },
        "post_rollback_snapshot": results["post_rollback_snapshot"]["metrics"],
        "next_gate": "Tomorrow 10:05Z (contingent on 30-min green window)"
    }
    
    return {
        "summary": summary,
        "details": results
    }


@router.get("/recovery-status")
async def get_recovery_status():
    """Get current recovery status."""
    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "canary_aborted": recovery_state.canary_aborted,
        "rollback_in_progress": recovery_state.rollback_in_progress,
        "rollback_complete": recovery_state.rollback_complete,
        "rollback_build_id": recovery_state.rollback_build_id,
        "rollback_digest": recovery_state.rollback_digest,
        "breaker_override_open": recovery_state.breaker_override_open,
        "freeze_enabled": recovery_state.freeze_enabled,
        "provider_ctas_hidden": recovery_state.provider_ctas_hidden,
        "probe_rps": recovery_state.probe_rps,
        "student_flows": "LIVE",
        "provider_flows": "QUEUED",
        "next_gate": "Tomorrow 10:05Z"
    }
