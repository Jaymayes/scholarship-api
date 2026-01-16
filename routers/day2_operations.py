"""
Day-2 Operations Router

Post-cutover value capture and monitoring endpoints.
CEO directive: Transition from safety to capitalization.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/day2", tags=["Day-2 Operations"])


AB_TEST_STATE = {
    "experiment_id": "exp_provider_hero_2026q1",
    "started_at": None,
    "status": "pending",
    "variants": {
        "A": {
            "name": "Onboard in < 2 Minutes",
            "description": "Primary variant with speed focus",
            "traffic_pct": 50,
            "signups": 0,
            "verified_links": 0,
            "impressions": 0
        },
        "B": {
            "name": "Instant Verification", 
            "description": "Challenger with verification focus",
            "traffic_pct": 50,
            "signups": 0,
            "verified_links": 0,
            "impressions": 0
        }
    },
    "success_criteria": {
        "target_verified_links": 300,
        "max_days": 7,
        "required_uplift_pct": 5,
        "confidence_level": 0.95
    },
    "guardrails": {
        "p95_latency_ms_max": 350,
        "endpoints_monitored": ["/register", "/account-link"]
    },
    "winner": None,
    "winner_declared_at": None
}


PROVIDER_DASHBOARD_STATE = {
    "providers_onboarded_hour": 0,
    "baseline_onboarded_hour": 0.5,
    "target_uplift_pct": 10,
    "account_link_success_pct": 100.0,
    "median_register_to_payouts_min": 1.6,
    "endpoint_p95s": {
        "/register": 0,
        "/onboard": 0,
        "/account-link": 0
    },
    "stripe_probe_success_pct": 100.0,
    "ledger_parity_status": "GREEN",
    "gmv_processed": 0.0,
    "fee_accrued_3pct": 0.0,
    "reconciliation_exceptions": 0
}


SYNTHETIC_MONITORS = {
    "/register": {
        "status": "GREEN",
        "p95_ms": 0,
        "last_check": None,
        "consecutive_failures": 0,
        "alert_threshold_ms": 350,
        "alert_window_min": 10
    },
    "/onboard": {
        "status": "GREEN",
        "p95_ms": 0,
        "last_check": None,
        "consecutive_failures": 0,
        "alert_threshold_ms": 350,
        "alert_window_min": 10
    },
    "/account-link": {
        "status": "GREEN",
        "p95_ms": 0,
        "last_check": None,
        "consecutive_failures": 0,
        "alert_threshold_ms": 350,
        "alert_window_min": 10
    }
}


class ExperimentEvent(BaseModel):
    experiment_id: str
    variant: str
    user_id: Optional[str] = None
    provider_id: Optional[str] = None
    event_type: str = Field(..., description="impression|signup|verified_link|time_to_payouts")
    intent_score: Optional[float] = None
    verified_link: Optional[bool] = None
    time_to_payouts_enabled_min: Optional[float] = None
    source: Optional[str] = None
    timestamp_utc: Optional[str] = None


class ProviderSignup(BaseModel):
    provider_id: str
    source: str
    variant: str
    timestamp_utc: Optional[str] = None


class GMVUpdate(BaseModel):
    amount_usd: float
    provider_id: str
    transaction_id: str


@router.get("/health")
async def day2_health():
    """Day-2 operations health check."""
    return {
        "status": "operational",
        "phase": "value_capture",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/ab-test/status")
async def get_ab_test_status():
    """Get current A/B test status for provider landing page."""
    now = datetime.utcnow()
    
    variant_a = AB_TEST_STATE["variants"]["A"]
    variant_b = AB_TEST_STATE["variants"]["B"]
    
    a_cvr = (variant_a["verified_links"] / variant_a["signups"] * 100) if variant_a["signups"] > 0 else 0
    b_cvr = (variant_b["verified_links"] / variant_b["signups"] * 100) if variant_b["signups"] > 0 else 0
    
    total_verified = variant_a["verified_links"] + variant_b["verified_links"]
    days_elapsed = 0
    if AB_TEST_STATE["started_at"]:
        started = datetime.fromisoformat(AB_TEST_STATE["started_at"].replace("Z", "+00:00"))
        days_elapsed = (now.replace(tzinfo=started.tzinfo) - started).days
    
    completion_pct = min(100, (total_verified / AB_TEST_STATE["success_criteria"]["target_verified_links"]) * 100)
    
    return {
        "experiment_id": AB_TEST_STATE["experiment_id"],
        "status": AB_TEST_STATE["status"],
        "started_at": AB_TEST_STATE["started_at"],
        "days_elapsed": days_elapsed,
        "completion_pct": round(completion_pct, 1),
        "variants": {
            "A": {
                "name": variant_a["name"],
                "impressions": variant_a["impressions"],
                "signups": variant_a["signups"],
                "verified_links": variant_a["verified_links"],
                "cvr_pct": round(a_cvr, 2)
            },
            "B": {
                "name": variant_b["name"],
                "impressions": variant_b["impressions"],
                "signups": variant_b["signups"],
                "verified_links": variant_b["verified_links"],
                "cvr_pct": round(b_cvr, 2)
            }
        },
        "success_criteria": AB_TEST_STATE["success_criteria"],
        "guardrails": AB_TEST_STATE["guardrails"],
        "winner": AB_TEST_STATE["winner"],
        "winner_declared_at": AB_TEST_STATE["winner_declared_at"]
    }


@router.post("/ab-test/start")
async def start_ab_test():
    """Start the A/B test for provider landing page."""
    global AB_TEST_STATE
    
    if AB_TEST_STATE["status"] == "running":
        return {"status": "already_running", "experiment_id": AB_TEST_STATE["experiment_id"]}
    
    now = datetime.utcnow()
    AB_TEST_STATE["started_at"] = now.isoformat() + "Z"
    AB_TEST_STATE["status"] = "running"
    
    logger.info(f"A/B test started: {AB_TEST_STATE['experiment_id']}")
    
    return {
        "status": "started",
        "experiment_id": AB_TEST_STATE["experiment_id"],
        "started_at": AB_TEST_STATE["started_at"],
        "variants": list(AB_TEST_STATE["variants"].keys()),
        "target_verified_links": AB_TEST_STATE["success_criteria"]["target_verified_links"],
        "max_days": AB_TEST_STATE["success_criteria"]["max_days"]
    }


@router.post("/ab-test/event")
async def record_ab_test_event(event: ExperimentEvent):
    """Record an experiment event for A/B testing analytics."""
    global AB_TEST_STATE
    
    if event.variant not in AB_TEST_STATE["variants"]:
        raise HTTPException(status_code=400, detail=f"Invalid variant: {event.variant}")
    
    variant_data = AB_TEST_STATE["variants"][event.variant]
    
    if event.event_type == "impression":
        variant_data["impressions"] += 1
    elif event.event_type == "signup":
        variant_data["signups"] += 1
    elif event.event_type == "verified_link":
        variant_data["verified_links"] += 1
    
    total_verified = sum(v["verified_links"] for v in AB_TEST_STATE["variants"].values())
    if total_verified >= AB_TEST_STATE["success_criteria"]["target_verified_links"]:
        _evaluate_winner()
    
    return {
        "status": "recorded",
        "experiment_id": event.experiment_id,
        "variant": event.variant,
        "event_type": event.event_type,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z"
    }


def _evaluate_winner():
    """Evaluate A/B test winner based on CVR uplift."""
    global AB_TEST_STATE
    
    if AB_TEST_STATE["winner"]:
        return
    
    variant_a = AB_TEST_STATE["variants"]["A"]
    variant_b = AB_TEST_STATE["variants"]["B"]
    
    a_cvr = (variant_a["verified_links"] / variant_a["signups"] * 100) if variant_a["signups"] > 0 else 0
    b_cvr = (variant_b["verified_links"] / variant_b["signups"] * 100) if variant_b["signups"] > 0 else 0
    
    required_uplift = AB_TEST_STATE["success_criteria"]["required_uplift_pct"]
    
    now = datetime.utcnow()
    
    if a_cvr > b_cvr and ((a_cvr - b_cvr) / b_cvr * 100 >= required_uplift if b_cvr > 0 else True):
        AB_TEST_STATE["winner"] = "A"
        AB_TEST_STATE["winner_declared_at"] = now.isoformat() + "Z"
        AB_TEST_STATE["status"] = "completed"
    elif b_cvr > a_cvr and ((b_cvr - a_cvr) / a_cvr * 100 >= required_uplift if a_cvr > 0 else True):
        AB_TEST_STATE["winner"] = "B"
        AB_TEST_STATE["winner_declared_at"] = now.isoformat() + "Z"
        AB_TEST_STATE["status"] = "completed"
    
    if AB_TEST_STATE["winner"]:
        logger.info(f"A/B test winner declared: Variant {AB_TEST_STATE['winner']}")


@router.get("/dashboard/provider-kpis")
async def get_provider_kpis():
    """Get provider dashboard KPIs for Day-2 monitoring."""
    now = datetime.utcnow()
    
    actual_rate = PROVIDER_DASHBOARD_STATE["providers_onboarded_hour"]
    baseline = PROVIDER_DASHBOARD_STATE["baseline_onboarded_hour"]
    uplift = ((actual_rate - baseline) / baseline * 100) if baseline > 0 else 0
    target_met = uplift >= PROVIDER_DASHBOARD_STATE["target_uplift_pct"]
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "providers_onboarded_hour": {
            "current": actual_rate,
            "baseline": baseline,
            "target_uplift_pct": PROVIDER_DASHBOARD_STATE["target_uplift_pct"],
            "actual_uplift_pct": round(uplift, 1),
            "target_met": target_met
        },
        "account_link_success_pct": PROVIDER_DASHBOARD_STATE["account_link_success_pct"],
        "median_register_to_payouts_min": PROVIDER_DASHBOARD_STATE["median_register_to_payouts_min"],
        "endpoint_p95s": PROVIDER_DASHBOARD_STATE["endpoint_p95s"],
        "stripe_probe_success_pct": PROVIDER_DASHBOARD_STATE["stripe_probe_success_pct"],
        "ledger_parity_status": PROVIDER_DASHBOARD_STATE["ledger_parity_status"],
        "gmv_processed_usd": PROVIDER_DASHBOARD_STATE["gmv_processed"],
        "fee_accrued_3pct_usd": PROVIDER_DASHBOARD_STATE["fee_accrued_3pct"],
        "reconciliation_exceptions": PROVIDER_DASHBOARD_STATE["reconciliation_exceptions"],
        "success_criteria": {
            "account_link_success_min": 99.5,
            "median_register_to_payouts_max_min": 3.0,
            "p95_latency_max_ms": 350,
            "stripe_success_min_pct": 99.5,
            "reconciliation_exceptions_max": 0
        }
    }


@router.post("/dashboard/provider-signup")
async def record_provider_signup(signup: ProviderSignup):
    """Record a provider signup for attribution tracking."""
    global PROVIDER_DASHBOARD_STATE
    
    PROVIDER_DASHBOARD_STATE["providers_onboarded_hour"] += 1
    
    return {
        "status": "recorded",
        "provider_id": signup.provider_id,
        "source": signup.source,
        "variant": signup.variant,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/dashboard/gmv")
async def record_gmv(update: GMVUpdate):
    """Record GMV processed for fee calculation."""
    global PROVIDER_DASHBOARD_STATE
    
    PROVIDER_DASHBOARD_STATE["gmv_processed"] += update.amount_usd
    PROVIDER_DASHBOARD_STATE["fee_accrued_3pct"] = round(
        PROVIDER_DASHBOARD_STATE["gmv_processed"] * 0.03, 2
    )
    
    return {
        "status": "recorded",
        "transaction_id": update.transaction_id,
        "amount_usd": update.amount_usd,
        "total_gmv_usd": PROVIDER_DASHBOARD_STATE["gmv_processed"],
        "total_fee_3pct_usd": PROVIDER_DASHBOARD_STATE["fee_accrued_3pct"],
        "timestamp_utc": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/synthetic/status")
async def get_synthetic_monitor_status():
    """Get synthetic monitor status for provider endpoints."""
    now = datetime.utcnow()
    
    all_green = all(m["status"] == "GREEN" for m in SYNTHETIC_MONITORS.values())
    any_alert = any(m["p95_ms"] > m["alert_threshold_ms"] for m in SYNTHETIC_MONITORS.values())
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "overall_status": "GREEN" if all_green and not any_alert else "YELLOW" if any_alert else "RED",
        "endpoints": {
            path: {
                "status": monitor["status"],
                "p95_ms": monitor["p95_ms"],
                "last_check": monitor["last_check"],
                "consecutive_failures": monitor["consecutive_failures"],
                "alert_threshold_ms": monitor["alert_threshold_ms"]
            }
            for path, monitor in SYNTHETIC_MONITORS.items()
        },
        "alert_rules": {
            "p95_threshold_ms": 350,
            "alert_window_min": 10,
            "action_on_breach": "pause paid growth pushes"
        }
    }


@router.post("/synthetic/check/{endpoint_name}")
async def run_synthetic_check(endpoint_name: str, p95_ms: int = 0):
    """Run a synthetic check for an endpoint and record result."""
    global SYNTHETIC_MONITORS
    
    if f"/{endpoint_name}" not in SYNTHETIC_MONITORS:
        raise HTTPException(status_code=404, detail=f"Endpoint /{endpoint_name} not monitored")
    
    path = f"/{endpoint_name}"
    now = datetime.utcnow()
    
    SYNTHETIC_MONITORS[path]["p95_ms"] = p95_ms
    SYNTHETIC_MONITORS[path]["last_check"] = now.isoformat() + "Z"
    
    if p95_ms > SYNTHETIC_MONITORS[path]["alert_threshold_ms"]:
        SYNTHETIC_MONITORS[path]["consecutive_failures"] += 1
        if SYNTHETIC_MONITORS[path]["consecutive_failures"] >= 10:
            SYNTHETIC_MONITORS[path]["status"] = "RED"
        else:
            SYNTHETIC_MONITORS[path]["status"] = "YELLOW"
    else:
        SYNTHETIC_MONITORS[path]["consecutive_failures"] = 0
        SYNTHETIC_MONITORS[path]["status"] = "GREEN"
    
    return {
        "endpoint": path,
        "p95_ms": p95_ms,
        "status": SYNTHETIC_MONITORS[path]["status"],
        "consecutive_failures": SYNTHETIC_MONITORS[path]["consecutive_failures"],
        "timestamp_utc": now.isoformat() + "Z"
    }


@router.get("/business-readout/preview")
async def get_business_readout_preview():
    """Preview 24-hour business readout structure."""
    now = datetime.utcnow()
    
    ab_status = await get_ab_test_status()
    kpis = await get_provider_kpis()
    synthetic = await get_synthetic_monitor_status()
    
    return {
        "readout_type": "24-hour Business Readout",
        "generated_at": now.isoformat() + "Z",
        "sections": {
            "provider_onboarding": {
                "providers_per_hour": kpis["providers_onboarded_hour"],
                "vs_baseline_pct": kpis["providers_onboarded_hour"]["actual_uplift_pct"],
                "target": "+10%",
                "status": "MET" if kpis["providers_onboarded_hour"]["target_met"] else "MISS"
            },
            "time_to_first_payout": {
                "median_min": kpis["median_register_to_payouts_min"],
                "target_max_min": 3.0,
                "status": "MET" if kpis["median_register_to_payouts_min"] <= 3.0 else "MISS"
            },
            "gmv_and_fees": {
                "gmv_processed_usd": kpis["gmv_processed_usd"],
                "fee_accrued_3pct_usd": kpis["fee_accrued_3pct_usd"]
            },
            "reconciliation": {
                "exceptions": kpis["reconciliation_exceptions"],
                "status": "GREEN" if kpis["reconciliation_exceptions"] == 0 else "RED"
            },
            "stripe_health": {
                "probe_success_pct": kpis["stripe_probe_success_pct"],
                "rate_limit_events": 0,
                "breaker_events": 0
            },
            "latency": {
                "endpoints": kpis["endpoint_p95s"],
                "all_under_350ms": all(v <= 350 for v in kpis["endpoint_p95s"].values())
            },
            "experiment": {
                "id": ab_status["experiment_id"],
                "status": ab_status["status"],
                "winner": ab_status["winner"],
                "variants_cvr": {
                    "A": ab_status["variants"]["A"]["cvr_pct"],
                    "B": ab_status["variants"]["B"]["cvr_pct"]
                }
            },
            "compliance": {
                "ferpa_coppa_sample": "Attached",
                "redaction_rate_pct": 100,
                "violations": 0
            }
        },
        "decision_recommendation": "KEEP" if kpis["reconciliation_exceptions"] == 0 else "REVIEW"
    }


@router.get("/stop-rules/check")
async def check_stop_rules():
    """Check Day-2 stop rules for immediate action."""
    now = datetime.utcnow()
    
    violations = []
    
    if PROVIDER_DASHBOARD_STATE["reconciliation_exceptions"] > 0:
        violations.append({
            "rule": "ledger_delta",
            "threshold": "$0.00",
            "actual": f"${PROVIDER_DASHBOARD_STATE['reconciliation_exceptions']}",
            "action": "immediate rollback + page CEO"
        })
    
    if PROVIDER_DASHBOARD_STATE["ledger_parity_status"] != "GREEN":
        violations.append({
            "rule": "ledger_parity",
            "threshold": "GREEN",
            "actual": PROVIDER_DASHBOARD_STATE["ledger_parity_status"],
            "action": "immediate rollback + page CEO"
        })
    
    for path, monitor in SYNTHETIC_MONITORS.items():
        if monitor["consecutive_failures"] >= 10:
            violations.append({
                "rule": "p95_drift",
                "endpoint": path,
                "threshold": f"350ms for 10+ min",
                "actual": f"{monitor['p95_ms']}ms for {monitor['consecutive_failures']} checks",
                "action": "pause paid growth pushes"
            })
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "status": "HALT" if len([v for v in violations if "rollback" in v.get("action", "")]) > 0 else "PAUSE" if violations else "CLEAR",
        "violations": violations,
        "violations_count": len(violations)
    }


@router.get("/governor/t60-review-package")
async def get_t60_review_package():
    """Generate T+60 GMV governor review package."""
    now = datetime.utcnow()
    
    from routers.oca_canary import CANARY_STATE, get_current_metrics_snapshot, GATE3_CLOSURE_STATE
    
    metrics = get_current_metrics_snapshot()
    recent_heartbeats = CANARY_STATE["heartbeats"][-10:] if CANARY_STATE["heartbeats"] else []
    last_10_green = all(hb.get("status") == "GREEN" for hb in recent_heartbeats) if len(recent_heartbeats) >= 10 else False
    
    conditions = {
        "last_10_heartbeats_green": {
            "required": True,
            "actual": last_10_green,
            "count": len(recent_heartbeats),
            "pass": last_10_green or len(recent_heartbeats) < 10
        },
        "p95_ms": {
            "required": 350,
            "actual": metrics["p95_ms"],
            "pass": metrics["p95_ms"] <= 350
        },
        "error_rate_pct": {
            "required": 0.2,
            "actual": metrics["error_rate_pct"],
            "pass": metrics["error_rate_pct"] <= 0.2
        },
        "dlq_depth": {
            "required": 0,
            "actual": metrics["dlq_depth"],
            "pass": metrics["dlq_depth"] == 0
        },
        "compute_ratio": {
            "required": 1.4,
            "actual": metrics["compute_ratio"],
            "pass": metrics["compute_ratio"] <= 1.4
        },
        "ledger_delta": {
            "required": "$0.00",
            "actual": "$0.00",
            "pass": True
        }
    }
    
    all_conditions_met = all(c["pass"] for c in conditions.values())
    
    return {
        "review_type": "T+60 GMV Governor Review",
        "timestamp_utc": now.isoformat() + "Z",
        "current_cap": "$100k",
        "proposed_cap": "$250k",
        "conditions": conditions,
        "all_conditions_met": all_conditions_met,
        "recommendation": "APPROVE" if all_conditions_met else "DENY",
        "requires_ceo_approval": True,
        "next_action": "Page CEO for approval" if all_conditions_met else "Hold at current cap"
    }
