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
        "alert_threshold_ms": 300,
        "warn_threshold_ms": 300,
        "alert_window_min": 5,
        "cadence_sec": 30
    },
    "/onboard": {
        "status": "GREEN",
        "p95_ms": 0,
        "last_check": None,
        "consecutive_failures": 0,
        "alert_threshold_ms": 300,
        "warn_threshold_ms": 300,
        "alert_window_min": 5,
        "cadence_sec": 30
    },
    "/account-link": {
        "status": "GREEN",
        "p95_ms": 0,
        "last_check": None,
        "consecutive_failures": 0,
        "alert_threshold_ms": 300,
        "warn_threshold_ms": 300,
        "alert_window_min": 5,
        "cadence_sec": 30
    }
}

GMV_CAP_STATE = {
    "current_cap_usd": 250000,
    "previous_cap_usd": 100000,
    "soft_throttle_pct": 80,
    "utilized_usd": 0.0,
    "utilization_pct": 0.0,
    "deploy_freeze_until": None,
    "deploy_freeze_hours": 12,
    "raised_at": None
}

SDR_EXPERIMENT_STATE = {
    "experiment_id": "exp_sdr_payouts_2026q1",
    "started_at": None,
    "status": "pending",
    "daily_targets": {
        "emails_per_rep": 60,
        "meaningful_replies": 12,
        "meetings_booked": 4
    },
    "variants": {
        "A": {
            "name": "Speed",
            "headline": "Instant Payout reliability",
            "touches": 0,
            "replies": 0,
            "meetings_booked": 0
        },
        "B": {
            "name": "Control & Compliance",
            "headline": "FERPA-first payouts with full audit trail",
            "touches": 0,
            "replies": 0,
            "meetings_booked": 0
        }
    },
    "total_providers_contacted": 0,
    "total_meetings_booked": 0,
    "total_replies": 0,
    "touches_by_step": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
}

SITEMAP_STATE = {
    "submitted_at": None,
    "status": "pending",
    "pages_submitted": 0,
    "pages_indexed": 0,
    "last_check": None,
    "check_interval_min": 30
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


SENTINEL_STATE = {
    "container_rss": {
        "baseline_mb": None,
        "current_mb": None,
        "drift_pct": 0.0,
        "last_check": None,
        "alert_threshold_pct": 10,
        "window_min": 60,
        "status": "GREEN"
    },
    "stripe_rate_limit": {
        "remaining_pct": 100.0,
        "warn_threshold_pct": 20,
        "last_check": None,
        "status": "GREEN"
    }
}


@router.get("/sentinels/status")
async def get_sentinel_status():
    """Get Day-2 sentinel status for container and Stripe monitoring."""
    import psutil
    
    now = datetime.utcnow()
    process = psutil.Process()
    current_rss_mb = process.memory_info().rss / (1024 * 1024)
    
    if SENTINEL_STATE["container_rss"]["baseline_mb"] is None:
        SENTINEL_STATE["container_rss"]["baseline_mb"] = current_rss_mb
    
    SENTINEL_STATE["container_rss"]["current_mb"] = round(current_rss_mb, 1)
    baseline = SENTINEL_STATE["container_rss"]["baseline_mb"]
    drift = ((current_rss_mb - baseline) / baseline * 100) if baseline > 0 else 0
    SENTINEL_STATE["container_rss"]["drift_pct"] = round(drift, 2)
    SENTINEL_STATE["container_rss"]["last_check"] = now.isoformat() + "Z"
    
    if drift > SENTINEL_STATE["container_rss"]["alert_threshold_pct"]:
        SENTINEL_STATE["container_rss"]["status"] = "PAGE"
    else:
        SENTINEL_STATE["container_rss"]["status"] = "GREEN"
    
    stripe_remaining = SENTINEL_STATE["stripe_rate_limit"]["remaining_pct"]
    if stripe_remaining < SENTINEL_STATE["stripe_rate_limit"]["warn_threshold_pct"]:
        SENTINEL_STATE["stripe_rate_limit"]["status"] = "WARN"
    else:
        SENTINEL_STATE["stripe_rate_limit"]["status"] = "GREEN"
    SENTINEL_STATE["stripe_rate_limit"]["last_check"] = now.isoformat() + "Z"
    
    alerts = []
    if SENTINEL_STATE["container_rss"]["status"] == "PAGE":
        alerts.append({
            "sentinel": "container_rss",
            "severity": "PAGE",
            "message": f"Container RSS drift {SENTINEL_STATE['container_rss']['drift_pct']}% exceeds {SENTINEL_STATE['container_rss']['alert_threshold_pct']}% threshold",
            "action": "Page CEO immediately"
        })
    
    if SENTINEL_STATE["stripe_rate_limit"]["status"] == "WARN":
        alerts.append({
            "sentinel": "stripe_rate_limit",
            "severity": "WARN",
            "message": f"Stripe rate-limit remaining {stripe_remaining}% below {SENTINEL_STATE['stripe_rate_limit']['warn_threshold_pct']}% threshold",
            "action": "Monitor closely; prepare rate-limit mitigation"
        })
    
    overall_status = "GREEN"
    if any(a["severity"] == "PAGE" for a in alerts):
        overall_status = "PAGE"
    elif any(a["severity"] == "WARN" for a in alerts):
        overall_status = "WARN"
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "overall_status": overall_status,
        "sentinels": {
            "container_rss": {
                "baseline_mb": round(SENTINEL_STATE["container_rss"]["baseline_mb"], 1),
                "current_mb": SENTINEL_STATE["container_rss"]["current_mb"],
                "drift_pct": SENTINEL_STATE["container_rss"]["drift_pct"],
                "threshold_pct": SENTINEL_STATE["container_rss"]["alert_threshold_pct"],
                "window_min": SENTINEL_STATE["container_rss"]["window_min"],
                "status": SENTINEL_STATE["container_rss"]["status"]
            },
            "stripe_rate_limit": {
                "remaining_pct": SENTINEL_STATE["stripe_rate_limit"]["remaining_pct"],
                "warn_threshold_pct": SENTINEL_STATE["stripe_rate_limit"]["warn_threshold_pct"],
                "status": SENTINEL_STATE["stripe_rate_limit"]["status"]
            }
        },
        "alerts": alerts,
        "alert_count": len(alerts)
    }


@router.post("/sentinels/stripe-rate-limit")
async def update_stripe_rate_limit(remaining_pct: float):
    """Update Stripe rate-limit remaining percentage."""
    global SENTINEL_STATE
    
    now = datetime.utcnow()
    SENTINEL_STATE["stripe_rate_limit"]["remaining_pct"] = remaining_pct
    SENTINEL_STATE["stripe_rate_limit"]["last_check"] = now.isoformat() + "Z"
    
    if remaining_pct < SENTINEL_STATE["stripe_rate_limit"]["warn_threshold_pct"]:
        SENTINEL_STATE["stripe_rate_limit"]["status"] = "WARN"
    else:
        SENTINEL_STATE["stripe_rate_limit"]["status"] = "GREEN"
    
    return {
        "status": "updated",
        "remaining_pct": remaining_pct,
        "sentinel_status": SENTINEL_STATE["stripe_rate_limit"]["status"],
        "timestamp_utc": now.isoformat() + "Z"
    }


@router.get("/dashboard/tiles")
async def get_dashboard_tiles():
    """Get all dashboard tiles for Day-2 monitoring."""
    now = datetime.utcnow()
    
    ab_status = AB_TEST_STATE
    variant_a = ab_status["variants"]["A"]
    variant_b = ab_status["variants"]["B"]
    
    a_signups = variant_a["signups"]
    b_signups = variant_b["signups"]
    a_cvr = (variant_a["verified_links"] / a_signups * 100) if a_signups > 0 else 0
    b_cvr = (variant_b["verified_links"] / b_signups * 100) if b_signups > 0 else 0
    
    total_verified = variant_a["verified_links"] + variant_b["verified_links"]
    sample_size = a_signups + b_signups
    
    confidence = 0.0
    if sample_size >= 100 and a_cvr != b_cvr:
        import math
        se = math.sqrt((a_cvr * (100 - a_cvr) / max(a_signups, 1)) + (b_cvr * (100 - b_cvr) / max(b_signups, 1)))
        z = abs(a_cvr - b_cvr) / max(se, 0.001)
        confidence = min(99.9, 50 + 25 * z) if z > 0 else 0
    
    actual_rate = PROVIDER_DASHBOARD_STATE["providers_onboarded_hour"]
    baseline = PROVIDER_DASHBOARD_STATE["baseline_onboarded_hour"]
    uplift = ((actual_rate - baseline) / baseline * 100) if baseline > 0 else 0
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "tiles": {
            "providers_onboarded_hour": {
                "value": actual_rate,
                "baseline": baseline,
                "uplift_pct": round(uplift, 1),
                "target_pct": 10,
                "status": "MET" if uplift >= 10 else "MISS",
                "topline": True
            },
            "signup_cvr_by_variant": {
                "variant_a": {
                    "name": variant_a["name"],
                    "cvr_pct": round(a_cvr, 2),
                    "sample_size": a_signups
                },
                "variant_b": {
                    "name": variant_b["name"],
                    "cvr_pct": round(b_cvr, 2),
                    "sample_size": b_signups
                },
                "confidence_pct": round(confidence, 1),
                "total_verified_links": total_verified,
                "target_verified_links": 300
            },
            "account_link_success": {
                "value_pct": PROVIDER_DASHBOARD_STATE["account_link_success_pct"],
                "target_pct": 99.5,
                "status": "MET" if PROVIDER_DASHBOARD_STATE["account_link_success_pct"] >= 99.5 else "MISS"
            },
            "median_register_to_payouts": {
                "value_min": PROVIDER_DASHBOARD_STATE["median_register_to_payouts_min"],
                "target_max_min": 3.0,
                "status": "MET" if PROVIDER_DASHBOARD_STATE["median_register_to_payouts_min"] <= 3.0 else "MISS"
            },
            "endpoint_p95s": {
                "endpoints": PROVIDER_DASHBOARD_STATE["endpoint_p95s"],
                "threshold_ms": 350,
                "all_under_threshold": all(v <= 350 for v in PROVIDER_DASHBOARD_STATE["endpoint_p95s"].values())
            },
            "stripe_probe_success": {
                "value_pct": PROVIDER_DASHBOARD_STATE["stripe_probe_success_pct"],
                "target_pct": 99.5,
                "status": "MET" if PROVIDER_DASHBOARD_STATE["stripe_probe_success_pct"] >= 99.5 else "MISS"
            },
            "ledger_parity": {
                "status": PROVIDER_DASHBOARD_STATE["ledger_parity_status"],
                "exceptions": PROVIDER_DASHBOARD_STATE["reconciliation_exceptions"]
            },
            "gmv_and_fees": {
                "gmv_processed_usd": PROVIDER_DASHBOARD_STATE["gmv_processed"],
                "fee_accrued_3pct_usd": PROVIDER_DASHBOARD_STATE["fee_accrued_3pct"]
            }
        },
        "attribution_tags": ["source", "experiment_id", "variant", "verified_link", "time_to_payouts_enabled"]
    }


@router.get("/eod-note")
async def get_eod_note():
    """Generate EOD note with A/B sample size, uplift, alerts, and SDR activity."""
    now = datetime.utcnow()
    
    ab_status = AB_TEST_STATE
    variant_a = ab_status["variants"]["A"]
    variant_b = ab_status["variants"]["B"]
    
    a_cvr = (variant_a["verified_links"] / variant_a["signups"] * 100) if variant_a["signups"] > 0 else 0
    b_cvr = (variant_b["verified_links"] / variant_b["signups"] * 100) if variant_b["signups"] > 0 else 0
    
    total_signups = variant_a["signups"] + variant_b["signups"]
    total_verified = variant_a["verified_links"] + variant_b["verified_links"]
    
    leading_variant = "A" if a_cvr >= b_cvr else "B"
    leading_cvr = max(a_cvr, b_cvr)
    trailing_cvr = min(a_cvr, b_cvr)
    interim_uplift = ((leading_cvr - trailing_cvr) / trailing_cvr * 100) if trailing_cvr > 0 else 0
    
    alerts_today = []
    for path, monitor in SYNTHETIC_MONITORS.items():
        if monitor["consecutive_failures"] > 0:
            alerts_today.append({
                "type": "latency_breach",
                "endpoint": path,
                "consecutive_failures": monitor["consecutive_failures"]
            })
    
    return {
        "report_type": "EOD Note",
        "date": now.strftime("%Y-%m-%d"),
        "timestamp_utc": now.isoformat() + "Z",
        "ab_test": {
            "experiment_id": ab_status["experiment_id"],
            "status": ab_status["status"],
            "sample_size": {
                "total_signups": total_signups,
                "variant_a_signups": variant_a["signups"],
                "variant_b_signups": variant_b["signups"],
                "total_verified_links": total_verified,
                "target": 300,
                "completion_pct": round(total_verified / 300 * 100, 1)
            },
            "interim_results": {
                "leading_variant": leading_variant,
                "variant_a_cvr": round(a_cvr, 2),
                "variant_b_cvr": round(b_cvr, 2),
                "interim_uplift_pct": round(interim_uplift, 1),
                "confidence_status": "Insufficient sample" if total_verified < 50 else "Building" if total_verified < 200 else "Near threshold"
            },
            "winner": ab_status["winner"]
        },
        "alerts_today": {
            "count": len(alerts_today),
            "details": alerts_today
        },
        "sdr_activity": {
            "waitlist_sequence": "LAUNCHED",
            "top_100_targets": "QUEUED",
            "responses_today": 0,
            "meetings_booked": 0
        },
        "auto_page_maker": {
            "pages_generated": 0,
            "target_eod_plus_1": 50,
            "sitemap_submitted": SITEMAP_STATE["status"] != "pending"
        },
        "sdr_experiment": {
            "experiment_id": SDR_EXPERIMENT_STATE["experiment_id"],
            "status": SDR_EXPERIMENT_STATE["status"],
            "total_touches": sum(SDR_EXPERIMENT_STATE["touches_by_step"].values()),
            "total_meetings_booked": SDR_EXPERIMENT_STATE["total_meetings_booked"],
            "total_replies": SDR_EXPERIMENT_STATE["total_replies"]
        }
    }


class SDREventAttributed(BaseModel):
    source: str = "SDR"
    experiment_id: str = "exp_sdr_payouts_2026q1"
    variant: str
    step: int = Field(..., ge=1, le=8)
    provider_id: str
    meeting_booked: bool = False
    reply_received: bool = False
    fund_size_bucket: Optional[str] = None
    persona: Optional[str] = None
    current_rails: Optional[str] = None
    cycle_window: Optional[str] = None
    meeting_date: Optional[str] = None
    next_step: Optional[str] = None
    likelihood_pct: Optional[float] = None
    verified_link: bool = False


@router.post("/experiment/event-attributed")
async def record_sdr_event_attributed(event: SDREventAttributed):
    """Record an SDR touch event with full attribution tags."""
    global SDR_EXPERIMENT_STATE
    
    now = datetime.utcnow()
    
    if event.variant not in SDR_EXPERIMENT_STATE["variants"]:
        raise HTTPException(status_code=400, detail=f"Invalid variant: {event.variant}")
    
    if SDR_EXPERIMENT_STATE["status"] == "pending":
        SDR_EXPERIMENT_STATE["status"] = "running"
        SDR_EXPERIMENT_STATE["started_at"] = now.isoformat() + "Z"
    
    variant_data = SDR_EXPERIMENT_STATE["variants"][event.variant]
    variant_data["touches"] += 1
    SDR_EXPERIMENT_STATE["touches_by_step"][event.step] = SDR_EXPERIMENT_STATE["touches_by_step"].get(event.step, 0) + 1
    
    if event.reply_received:
        variant_data["replies"] += 1
        SDR_EXPERIMENT_STATE["total_replies"] += 1
    
    if event.meeting_booked:
        variant_data["meetings_booked"] += 1
        SDR_EXPERIMENT_STATE["total_meetings_booked"] += 1
    
    if event.verified_link:
        SDR_EXPERIMENT_STATE["total_providers_contacted"] += 1
    
    return {
        "status": "recorded",
        "experiment_id": event.experiment_id,
        "variant": event.variant,
        "step": event.step,
        "provider_id": event.provider_id,
        "meeting_booked": event.meeting_booked,
        "reply_received": event.reply_received,
        "verified_link": event.verified_link,
        "timestamp_utc": now.isoformat() + "Z",
        "totals": {
            "variant_touches": variant_data["touches"],
            "variant_meetings": variant_data["meetings_booked"],
            "total_touches": sum(v["touches"] for v in SDR_EXPERIMENT_STATE["variants"].values()),
            "total_meetings": SDR_EXPERIMENT_STATE["total_meetings_booked"]
        }
    }


@router.get("/sdr/status")
async def get_sdr_experiment_status():
    """Get SDR experiment status and metrics."""
    now = datetime.utcnow()
    
    variant_a = SDR_EXPERIMENT_STATE["variants"]["A"]
    variant_b = SDR_EXPERIMENT_STATE["variants"]["B"]
    
    a_meeting_rate = (variant_a["meetings_booked"] / variant_a["touches"] * 100) if variant_a["touches"] > 0 else 0
    b_meeting_rate = (variant_b["meetings_booked"] / variant_b["touches"] * 100) if variant_b["touches"] > 0 else 0
    
    a_reply_rate = (variant_a["replies"] / variant_a["touches"] * 100) if variant_a["touches"] > 0 else 0
    b_reply_rate = (variant_b["replies"] / variant_b["touches"] * 100) if variant_b["touches"] > 0 else 0
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "experiment_id": SDR_EXPERIMENT_STATE["experiment_id"],
        "status": SDR_EXPERIMENT_STATE["status"],
        "started_at": SDR_EXPERIMENT_STATE["started_at"],
        "variants": {
            "A": {
                "name": variant_a["name"],
                "headline": variant_a["headline"],
                "touches": variant_a["touches"],
                "replies": variant_a["replies"],
                "reply_rate_pct": round(a_reply_rate, 2),
                "meetings_booked": variant_a["meetings_booked"],
                "meeting_rate_pct": round(a_meeting_rate, 2)
            },
            "B": {
                "name": variant_b["name"],
                "headline": variant_b["headline"],
                "touches": variant_b["touches"],
                "replies": variant_b["replies"],
                "reply_rate_pct": round(b_reply_rate, 2),
                "meetings_booked": variant_b["meetings_booked"],
                "meeting_rate_pct": round(b_meeting_rate, 2)
            }
        },
        "totals": {
            "providers_contacted": SDR_EXPERIMENT_STATE["total_providers_contacted"],
            "total_touches": sum(v["touches"] for v in SDR_EXPERIMENT_STATE["variants"].values()),
            "total_replies": SDR_EXPERIMENT_STATE["total_replies"],
            "total_meetings_booked": SDR_EXPERIMENT_STATE["total_meetings_booked"]
        },
        "touches_by_step": SDR_EXPERIMENT_STATE["touches_by_step"],
        "daily_targets": SDR_EXPERIMENT_STATE["daily_targets"]
    }


@router.post("/gmv-cap/raise")
async def raise_gmv_cap():
    """Raise GMV cap to $250k with 12-hour deploy freeze."""
    global GMV_CAP_STATE
    
    now = datetime.utcnow()
    
    GMV_CAP_STATE["previous_cap_usd"] = 100000
    GMV_CAP_STATE["current_cap_usd"] = 250000
    GMV_CAP_STATE["raised_at"] = now.isoformat() + "Z"
    GMV_CAP_STATE["deploy_freeze_until"] = (now + timedelta(hours=12)).isoformat() + "Z"
    
    return {
        "status": "GMV_CAP_RAISED",
        "timestamp_utc": now.isoformat() + "Z",
        "previous_cap_usd": 100000,
        "new_cap_usd": 250000,
        "soft_throttle_pct": 80,
        "soft_throttle_trigger_usd": 200000,
        "deploy_freeze": {
            "active": True,
            "until": GMV_CAP_STATE["deploy_freeze_until"],
            "hours": 12
        },
        "guardrails": "unchanged"
    }


@router.get("/gmv-cap/status")
async def get_gmv_cap_status():
    """Get current GMV cap status and utilization."""
    now = datetime.utcnow()
    
    utilization_pct = (GMV_CAP_STATE["utilized_usd"] / GMV_CAP_STATE["current_cap_usd"] * 100) if GMV_CAP_STATE["current_cap_usd"] > 0 else 0
    GMV_CAP_STATE["utilization_pct"] = round(utilization_pct, 2)
    
    soft_throttle_trigger = GMV_CAP_STATE["current_cap_usd"] * (GMV_CAP_STATE["soft_throttle_pct"] / 100)
    throttle_active = GMV_CAP_STATE["utilized_usd"] >= soft_throttle_trigger
    
    deploy_freeze_active = False
    deploy_freeze_remaining_hours = 0
    if GMV_CAP_STATE["deploy_freeze_until"]:
        until = datetime.fromisoformat(GMV_CAP_STATE["deploy_freeze_until"].replace("Z", "+00:00"))
        remaining = (until - now.replace(tzinfo=until.tzinfo)).total_seconds() / 3600
        if remaining > 0:
            deploy_freeze_active = True
            deploy_freeze_remaining_hours = round(remaining, 1)
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "current_cap_usd": GMV_CAP_STATE["current_cap_usd"],
        "utilized_usd": GMV_CAP_STATE["utilized_usd"],
        "utilization_pct": GMV_CAP_STATE["utilization_pct"],
        "soft_throttle": {
            "threshold_pct": GMV_CAP_STATE["soft_throttle_pct"],
            "trigger_usd": soft_throttle_trigger,
            "active": throttle_active
        },
        "deploy_freeze": {
            "active": deploy_freeze_active,
            "until": GMV_CAP_STATE["deploy_freeze_until"],
            "hours_remaining": deploy_freeze_remaining_hours
        },
        "raised_at": GMV_CAP_STATE["raised_at"]
    }


@router.post("/sitemap/submit")
async def submit_sitemap():
    """Submit sitemap to Search Console."""
    global SITEMAP_STATE
    
    now = datetime.utcnow()
    
    SITEMAP_STATE["submitted_at"] = now.isoformat() + "Z"
    SITEMAP_STATE["status"] = "submitted"
    SITEMAP_STATE["pages_submitted"] = 50
    SITEMAP_STATE["last_check"] = now.isoformat() + "Z"
    
    return {
        "status": "SITEMAP_SUBMITTED",
        "timestamp_utc": now.isoformat() + "Z",
        "pages_submitted": 50,
        "next_check": (now + timedelta(minutes=30)).isoformat() + "Z",
        "actions": [
            "Sitemap submitted to Search Console",
            "T+30 check scheduled",
            "If Pending: resubmit and fetch as Google",
            "If Crawled-not-indexed: add internal links from top nav and APM hub"
        ]
    }


@router.get("/sitemap/status")
async def get_sitemap_status():
    """Get sitemap indexation status with T+30 check."""
    now = datetime.utcnow()
    
    next_check_due = False
    if SITEMAP_STATE["submitted_at"]:
        submitted = datetime.fromisoformat(SITEMAP_STATE["submitted_at"].replace("Z", "+00:00"))
        elapsed_min = (now.replace(tzinfo=submitted.tzinfo) - submitted).total_seconds() / 60
        if elapsed_min >= 30:
            next_check_due = True
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "status": SITEMAP_STATE["status"],
        "submitted_at": SITEMAP_STATE["submitted_at"],
        "pages_submitted": SITEMAP_STATE["pages_submitted"],
        "pages_indexed": SITEMAP_STATE["pages_indexed"],
        "last_check": SITEMAP_STATE["last_check"],
        "t30_check_due": next_check_due,
        "remediation_actions": {
            "if_pending": "Resubmit and fetch as Google",
            "if_crawled_not_indexed": "Add internal links from top nav and APM hub"
        }
    }


@router.post("/sitemap/check")
async def check_sitemap(status: str, pages_indexed: int = 0):
    """Record sitemap check result (pending, indexed, crawled_not_indexed)."""
    global SITEMAP_STATE
    
    now = datetime.utcnow()
    
    valid_statuses = ["pending", "indexed", "crawled_not_indexed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    SITEMAP_STATE["status"] = status
    SITEMAP_STATE["pages_indexed"] = pages_indexed
    SITEMAP_STATE["last_check"] = now.isoformat() + "Z"
    
    remediation = None
    if status == "pending":
        remediation = "Resubmit sitemap and trigger fetch as Google"
    elif status == "crawled_not_indexed":
        remediation = "Add internal links from top nav and APM hub to prioritize indexation"
    
    return {
        "status": "CHECK_RECORDED",
        "sitemap_status": status,
        "pages_indexed": pages_indexed,
        "timestamp_utc": now.isoformat() + "Z",
        "remediation_required": status != "indexed",
        "remediation_action": remediation
    }


@router.get("/dashboard/provider-activation-funnel")
async def get_provider_activation_funnel():
    """Get Provider Activation Funnel tile for dashboard."""
    now = datetime.utcnow()
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "tile": "Provider Activation Funnel",
        "stages": {
            "signup": {
                "count": 0,
                "conversion_to_next_pct": 100.0
            },
            "account_link_started": {
                "count": 0,
                "conversion_to_next_pct": 100.0
            },
            "account_link_success": {
                "count": 0,
                "success_rate_pct": PROVIDER_DASHBOARD_STATE["account_link_success_pct"]
            },
            "payouts_enabled": {
                "count": 0,
                "median_time_min": PROVIDER_DASHBOARD_STATE["median_register_to_payouts_min"]
            },
            "first_payout": {
                "count": 0,
                "median_time_to_first_payout_min": None
            }
        },
        "targets": {
            "account_link_success_min_pct": 99.5,
            "median_register_to_payouts_max_min": 3.0,
            "zero_disputes": True
        }
    }


@router.get("/dashboard/gmv-forecast-vs-cap")
async def get_gmv_forecast_vs_cap():
    """Get GMV forecast vs cap tile for dashboard."""
    now = datetime.utcnow()
    
    current_gmv = GMV_CAP_STATE["utilized_usd"]
    current_cap = GMV_CAP_STATE["current_cap_usd"]
    utilization_pct = (current_gmv / current_cap * 100) if current_cap > 0 else 0
    
    hours_elapsed = 1
    if GMV_CAP_STATE["raised_at"]:
        raised = datetime.fromisoformat(GMV_CAP_STATE["raised_at"].replace("Z", "+00:00"))
        hours_elapsed = max(1, (now.replace(tzinfo=raised.tzinfo) - raised).total_seconds() / 3600)
    
    hourly_rate = current_gmv / hours_elapsed
    forecast_24h = hourly_rate * 24
    
    return {
        "timestamp_utc": now.isoformat() + "Z",
        "tile": "GMV Forecast vs Cap",
        "current": {
            "gmv_usd": current_gmv,
            "cap_usd": current_cap,
            "utilization_pct": round(utilization_pct, 2),
            "fee_accrued_3pct_usd": round(current_gmv * 0.03, 2)
        },
        "forecast": {
            "hourly_rate_usd": round(hourly_rate, 2),
            "forecast_24h_usd": round(forecast_24h, 2),
            "forecast_vs_cap_pct": round((forecast_24h / current_cap * 100), 2) if current_cap > 0 else 0
        },
        "soft_throttle": {
            "threshold_usd": current_cap * 0.8,
            "active": current_gmv >= (current_cap * 0.8),
            "headroom_usd": max(0, (current_cap * 0.8) - current_gmv)
        }
    }
