"""
Production Launch Router
Executive directive: Canary deployment, business instrumentation, war room reporting
"""
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from production.business_instrumentation import business_instrumentation
from production.canary_deployment import canary_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/launch",
    tags=["production-launch"],
    responses={
        200: {"description": "Success"},
        500: {"description": "Internal server error"},
    }
)

@router.post("/canary/initiate")
async def initiate_canary_deployment() -> dict[str, Any]:
    """
    🚀 INITIATE CANARY DEPLOYMENT
    Executive directive: Start 10% traffic ramp with SLO gates

    Returns:
        - Canary status and timeline
        - SLO gate configuration
        - War room schedule
    """
    try:
        result = canary_manager.initiate_canary()

        if result["status"] == "canary_initiated":
            # Start business instrumentation
            business_instrumentation.track_conversion_event(
                api_key="system_canary",
                event_type="canary_initiated",
                tier="production",
                cohort="launch_week"
            )

            logger.info("🎯 PRODUCTION LAUNCH: Canary deployment initiated")
            return {
                "message": "🚀 Canary deployment initiated successfully",
                "deployment_details": result,
                "executive_directive": "10% → 25% → 50% → 100% GA ramp with SLO gates",
                "war_room_active": True,
                "escalation_policy": "halt_on_any_gate_miss"
            }
        raise HTTPException(status_code=500, detail=f"Canary initiation failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ Canary initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate canary: {str(e)}")

@router.get("/canary/status")
async def get_canary_status() -> dict[str, Any]:
    """
    📊 GET CANARY DEPLOYMENT STATUS
    Executive directive: Real-time status for war room check-ins
    """
    try:
        deployment_status = canary_manager.get_deployment_status()
        slo_check = canary_manager.check_slo_gates()
        business_kpis = business_instrumentation.calculate_business_kpis()

        return {
            "deployment_status": deployment_status,
            "slo_health": slo_check,
            "business_kpis": business_kpis,
            "war_room_ready": True,
            "next_action": deployment_status.get("next_action", "monitor"),
            "escalation_required": not slo_check.get("all_gates_pass", True)
        }

    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get canary status: {str(e)}")

@router.post("/canary/promote")
async def promote_canary_stage() -> dict[str, Any]:
    """
    📈 PROMOTE CANARY TO NEXT STAGE
    Executive directive: Progress ramp if SLO gates pass
    """
    try:
        result = canary_manager.promote_stage()

        if result["status"] == "promoted":
            # Track business event
            business_instrumentation.track_conversion_event(
                api_key="system_canary",
                event_type="stage_promotion",
                tier="production",
                amount=0,
                cohort="launch_week"
            )

            logger.info(f"📈 STAGE PROMOTION: {result['new_stage']} ({result['traffic_percentage']}%)")
            return {
                "message": f"🎯 Promoted to {result['new_stage']} successfully",
                "promotion_details": result,
                "slo_gates_validated": True
            }
        if result["status"] == "promotion_blocked":
            logger.warning("⚠️ PROMOTION BLOCKED: SLO gates breach detected")
            return {
                "message": "⚠️ Promotion blocked due to SLO breach",
                "block_details": result,
                "action_required": "investigate_and_rollback"
            }
        if result["status"] == "production_ga_complete":
            logger.info("🎉 PRODUCTION GA COMPLETE: 100% traffic achieved")
            return {
                "message": "🎉 Production GA complete - 100% traffic",
                "ga_details": result,
                "launch_complete": True
            }
        raise HTTPException(status_code=400, detail=f"Unexpected promotion result: {result}")

    except Exception as e:
        logger.error(f"❌ Promotion error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to promote canary: {str(e)}")

@router.post("/business/track-activity")
async def track_consumer_activity(
    api_key: str,
    tier: str = "free",
    region: str = "us"
) -> dict[str, Any]:
    """
    👤 TRACK CONSUMER API ACTIVITY
    Executive directive: daily_active_consumer_keys KPI tracking
    """
    try:
        result = business_instrumentation.track_consumer_activity(
            api_key=api_key,
            tier=tier,
            region=region
        )

        return {
            "message": "Consumer activity tracked successfully",
            "tracking_details": result,
            "kpi_contribution": "daily_active_consumer_keys"
        }

    except Exception as e:
        logger.error(f"❌ Activity tracking error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track activity: {str(e)}")

@router.post("/business/track-conversion")
async def track_conversion_event(
    api_key: str,
    event_type: str,
    tier: str = "free",
    amount: float = 0.0,
    cohort: str = "2025-09"
) -> dict[str, Any]:
    """
    💰 TRACK CONVERSION FUNNEL EVENT
    Executive directive: free→paid conversion, ARPU tracking
    """
    try:
        result = business_instrumentation.track_conversion_event(
            api_key=api_key,
            event_type=event_type,
            tier=tier,
            amount=amount,
            cohort=cohort
        )

        return {
            "message": "Conversion event tracked successfully",
            "conversion_details": result,
            "revenue_impact": amount
        }

    except Exception as e:
        logger.error(f"❌ Conversion tracking error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track conversion: {str(e)}")

@router.get("/business/kpis")
async def get_business_kpis() -> dict[str, Any]:
    """
    📈 GET BUSINESS KPI DASHBOARD
    Executive directive: Real-time KPIs for leadership visibility
    """
    try:
        kpis = business_instrumentation.calculate_business_kpis()

        return {
            "message": "Business KPIs calculated successfully",
            "kpi_dashboard": kpis,
            "executive_summary": {
                "dau_health": "healthy" if kpis["daily_active_consumer_keys"] > 0 else "needs_attention",
                "conversion_health": "healthy" if kpis["conversion_rate_percent"] > 1.0 else "needs_optimization",
                "revenue_health": "healthy" if kpis["total_revenue_usd"] > 0 else "early_stage",
                "provider_health": "healthy" if kpis["provider_keys_active"] > 0 else "needs_acquisition"
            }
        }

    except Exception as e:
        logger.error(f"❌ KPI calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")

@router.get("/war-room/report")
async def generate_war_room_report() -> dict[str, Any]:
    """
    🎯 GENERATE WAR ROOM REPORT
    Executive directive: Twice-daily check-ins with SLO/burn-rate snapshots
    """
    try:
        report = business_instrumentation.generate_war_room_report()

        return {
            "message": "War room report generated successfully",
            "war_room_report": report,
            "next_checkin": report["next_war_room"],
            "escalation_required": report["escalation_required"]
        }

    except Exception as e:
        logger.error(f"❌ War room report error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.post("/simulate/traffic")
async def simulate_production_traffic(
    background_tasks: BackgroundTasks,
    requests_per_minute: int = 100,
    duration_minutes: int = 10
) -> dict[str, Any]:
    """
    🔄 SIMULATE PRODUCTION TRAFFIC
    Executive directive: Generate realistic traffic for canary validation
    """
    try:
        # Start background traffic simulation
        background_tasks.add_task(
            _simulate_traffic_background,
            requests_per_minute,
            duration_minutes
        )

        return {
            "message": "Production traffic simulation started",
            "simulation_config": {
                "requests_per_minute": requests_per_minute,
                "duration_minutes": duration_minutes,
                "total_requests": requests_per_minute * duration_minutes
            },
            "purpose": "canary_validation_and_slo_testing"
        }

    except Exception as e:
        logger.error(f"❌ Traffic simulation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")

async def _simulate_traffic_background(requests_per_minute: int, duration_minutes: int):
    """Background task to simulate production traffic"""
    import asyncio
    import random

    total_requests = requests_per_minute * duration_minutes
    delay_between_requests = 60 / requests_per_minute  # seconds

    logger.info(f"🔄 Starting traffic simulation: {total_requests} requests over {duration_minutes} minutes")

    for _i in range(total_requests):
        # Simulate consumer activity
        api_key = f"sim_key_{random.randint(1000, 9999)}"
        tier = random.choice(["free", "paid", "enterprise"])

        business_instrumentation.track_consumer_activity(
            api_key=api_key,
            tier=tier,
            region=random.choice(["us", "ca", "uk"])
        )

        # Simulate search performance
        business_instrumentation.track_search_performance(
            search_type=random.choice(["semantic", "keyword", "hybrid"]),
            latency_seconds=random.uniform(0.02, 0.15),
            tier=tier
        )

        # Occasional conversion events
        if random.random() < 0.05:  # 5% conversion rate
            business_instrumentation.track_conversion_event(
                api_key=api_key,
                event_type="upgrade_to_paid",
                tier="paid",
                amount=random.uniform(10, 100),
                cohort="2025-09"
            )

        await asyncio.sleep(delay_between_requests)

    logger.info(f"✅ Traffic simulation complete: {total_requests} requests processed")
