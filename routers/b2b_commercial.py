"""
B2B Commercial Execution API
Aggressive ARR targets with real-time tracking and partner management
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from middleware.auth import User, require_admin, require_auth
from models.database import get_db
from production.b2b_commercial_execution import (
    PricingTier,
    b2b_commercial_service,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/commercial",
    tags=["B2B Commercial Execution"],
    responses={
        500: {"description": "Internal server error"}
    }
)

@router.get("/arr-targets",
    summary="Get 30/60/90 day ARR targets and current progress",
    description="Track progress against aggressive B2B ARR targets: $150k → $250k → $500k run-rates")
async def get_arr_targets_progress(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get current progress against 30/60/90 day ARR targets"""
    try:
        progress = b2b_commercial_service.get_arr_progress(db)

        # Add real-time metrics
        current_metrics = b2b_commercial_service.get_current_funnel_metrics(db)

        logger.info(f"📊 ARR progress requested by {user.user_id} ({user.roles}) - Current: {current_metrics.paid_count} paid providers")

        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "targets_progress": progress,
            "current_funnel_metrics": current_metrics.__dict__,
            "summary": {
                "total_providers_in_funnel": sum([
                    current_metrics.invited_count, current_metrics.meeting_count,
                    current_metrics.pilot_count, current_metrics.listings_live_count,
                    current_metrics.first_application_count, current_metrics.paid_count
                ]),
                "paid_conversions": current_metrics.paid_count,
                "pipeline_health": "strong" if current_metrics.pipeline_coverage and current_metrics.pipeline_coverage >= 3 else "needs attention"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get ARR progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ARR progress: {str(e)}")

@router.get("/pricing-packages",
    summary="Get commercial pricing packages",
    description="B2B pricing tiers: Listings+Promotion, Recruitment Dashboard, Analytics")
async def get_pricing_packages(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    segment: str | None = Query(None, description="Filter by target segment: university, foundation, corporate"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get all commercial pricing packages with segment filtering"""
    try:
        packages = b2b_commercial_service.get_pricing_packages()

        # Filter by segment if requested
        if segment:
            packages = [pkg for pkg in packages if pkg["target_segment"] == segment or pkg["target_segment"] == "all"]

        logger.info(f"💰 Pricing packages requested by {user.user_id} ({user.roles}) - {len(packages)} packages returned")

        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "packages": packages,
            "summary": {
                "total_packages": len(packages),
                "price_range": {
                    "min_monthly": min(pkg["pricing"]["monthly"] for pkg in packages),
                    "max_monthly": max(pkg["pricing"]["monthly"] for pkg in packages)
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to get pricing packages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pricing packages: {str(e)}")

@router.post("/providers/{provider_id}/upgrade",
    summary="Upgrade provider to paid tier",
    description="Convert provider to paid commercial tier for ARR acceleration")
async def upgrade_provider_tier(
    provider_id: str,
    tier: PricingTier,
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin())
):
    """Upgrade provider to paid commercial tier"""
    try:
        # SECURITY AUDIT: Provider tier upgrade
        logger.warning(f"🔐 AUDIT: Provider upgrade initiated - Provider: {provider_id}, Tier: {tier.value}, Admin: {user.user_id} ({user.email})")

        upgrade_result = b2b_commercial_service.upgrade_provider_tier(provider_id, tier, db)

        # SECURITY AUDIT: Log successful upgrade
        logger.warning(f"🔐 AUDIT: Provider upgrade completed - Provider: {provider_id}, Tier: {tier.value}, Admin: {user.user_id}, Revenue: ${upgrade_result['annual_revenue']:,.0f} ARR")
        logger.info(f"💰 Provider {provider_id} upgraded to {tier.value} by admin {user.user_id}")
        logger.info(f"📈 Revenue impact: ${upgrade_result['annual_revenue']:,.0f} ARR")

        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "upgrade_details": upgrade_result,
            "message": f"Provider successfully upgraded to {upgrade_result['package_name']}"
        }

    except ValueError as e:
        logger.warning(f"Provider upgrade failed - {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upgrade provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upgrade provider: {str(e)}")

@router.get("/weekly-report",
    summary="Generate weekly Provider Engine report",
    description="Comprehensive B2B performance report with pipeline coverage ≥3x and LTV:CAC ≥3:1")
async def get_weekly_provider_engine_report(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Generate weekly Provider Engine report for executive tracking"""
    try:
        report = b2b_commercial_service.generate_weekly_provider_engine_report(db)

        # Log key metrics for monitoring
        exec_summary = report["executive_summary"]
        logger.info(f"📊 Weekly report generated by {user.user_id} ({user.roles}) - {exec_summary['total_providers_live']} providers live")
        logger.info(f"💰 ARR run-rate: ${exec_summary['arr_runrate_k']}k")
        logger.info(f"🎯 Pipeline coverage: {exec_summary['pipeline_coverage']}x")

        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "report": report,
            "quick_stats": {
                "providers_live": exec_summary["total_providers_live"],
                "paid_providers": exec_summary["paid_providers"],
                "arr_runrate_k": exec_summary["arr_runrate_k"],
                "pipeline_health": "strong" if exec_summary.get("pipeline_coverage", 0) >= 3 else "needs attention",
                "ltv_cac_health": "strong" if exec_summary.get("ltv_cac_ratio", 0) >= 3 else "needs attention"
            }
        }

    except Exception as e:
        logger.error(f"Failed to generate weekly report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate weekly report: {str(e)}")

@router.get("/funnel-metrics",
    summary="Get real-time B2B funnel conversion metrics",
    description="Track invited → meeting → pilot → listings → application → paid conversion rates")
async def get_funnel_metrics(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get real-time B2B funnel conversion metrics"""
    try:
        metrics = b2b_commercial_service.get_current_funnel_metrics(db)

        # Calculate conversion rates for quick analysis
        total_in_funnel = sum([
            metrics.invited_count, metrics.meeting_count, metrics.pilot_count,
            metrics.listings_live_count, metrics.first_application_count, metrics.paid_count
        ])

        conversion_analysis = {
            "funnel_efficiency": (metrics.paid_count / total_in_funnel * 100) if total_in_funnel > 0 else 0,
            "time_to_value_health": {
                "listing_health": "good" if metrics.avg_time_to_first_listing and metrics.avg_time_to_first_listing <= 7 else "needs attention",
                "application_health": "good" if metrics.avg_time_to_first_application and metrics.avg_time_to_first_application <= 14 else "needs attention"
            },
            "pipeline_strength": "strong" if metrics.pipeline_coverage and metrics.pipeline_coverage >= 3 else "weak"
        }

        logger.info(f"📊 Funnel metrics requested by {user.user_id} ({user.roles}) - {total_in_funnel} total in funnel, {metrics.paid_count} paid")

        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "funnel_metrics": metrics.__dict__,
            "conversion_analysis": conversion_analysis,
            "targets": {
                "time_to_first_listing_days": 7,
                "time_to_first_application_days": 14,
                "pipeline_coverage_minimum": 3.0,
                "ltv_cac_minimum": 3.0
            }
        }

    except Exception as e:
        logger.error(f"Failed to get funnel metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve funnel metrics: {str(e)}")

@router.get("/commercial-dashboard",
    summary="Executive commercial dashboard",
    description="High-level dashboard for tracking B2B commercial execution against aggressive targets")
async def get_commercial_dashboard(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Executive commercial dashboard with key B2B metrics"""
    try:
        # Get comprehensive metrics
        arr_progress = b2b_commercial_service.get_arr_progress(db)
        funnel_metrics = b2b_commercial_service.get_current_funnel_metrics(db)
        pricing_packages = b2b_commercial_service.get_pricing_packages()

        # Calculate executive summary
        total_providers = sum([
            funnel_metrics.invited_count, funnel_metrics.meeting_count,
            funnel_metrics.pilot_count, funnel_metrics.listings_live_count,
            funnel_metrics.first_application_count, funnel_metrics.paid_count
        ])

        current_arr_k = arr_progress.get("day_30", {}).get("current", {}).get("arr_runrate_k", 0)

        executive_summary = {
            "total_providers_in_pipeline": total_providers,
            "paid_providers": funnel_metrics.paid_count,
            "current_arr_runrate_k": current_arr_k,
            "next_milestone": "Day 30: $150k ARR" if current_arr_k < 150 else "Day 60: $250k ARR" if current_arr_k < 250 else "Day 90: $500k ARR",
            "health_status": {
                "pipeline": "strong" if funnel_metrics.pipeline_coverage and funnel_metrics.pipeline_coverage >= 3 else "needs attention",
                "ltv_cac": "strong" if funnel_metrics.ltv_cac_ratio and funnel_metrics.ltv_cac_ratio >= 3 else "needs attention",
                "time_to_value": "good" if (funnel_metrics.avg_time_to_first_listing or 0) <= 7 and (funnel_metrics.avg_time_to_first_application or 0) <= 14 else "needs attention"
            }
        }

        logger.info(f"📊 Commercial dashboard accessed by {user.user_id} ({user.roles}) - {total_providers} providers, ${current_arr_k}k ARR")

        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "executive_summary": executive_summary,
            "detailed_metrics": {
                "arr_targets_progress": arr_progress,
                "funnel_metrics": funnel_metrics.__dict__,
                "available_packages": len(pricing_packages)
            },
            "action_items": [
                "Accelerate pilot-to-paid conversion" if funnel_metrics.pilot_count > funnel_metrics.paid_count * 2 else None,
                "Improve time-to-first-listing" if funnel_metrics.avg_time_to_first_listing and funnel_metrics.avg_time_to_first_listing > 7 else None,
                "Scale organic traffic for provider ROI" if current_arr_k < 150 else None,
                "Increase pipeline coverage" if funnel_metrics.pipeline_coverage and funnel_metrics.pipeline_coverage < 3 else None
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get commercial dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve commercial dashboard: {str(e)}")

# Health check endpoint
@router.get("/health",
    summary="B2B Commercial service health check",
    description="Verify B2B commercial execution engine is operational")
async def health_check(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth())
):
    """Health check for B2B commercial execution service"""
    return {
        "success": True,
        "service": "B2B Commercial Execution",
        "status": "operational",
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "targets": {
            "30_day_arr_target_k": 150,
            "60_day_arr_target_k": 250,
            "90_day_arr_target_k": 500
        }
    }
