"""
Operations Framework API
Comprehensive AE + Partner Success Operations Framework for aggressive B2B ARR execution

Complete API access to:
- Lead Routing Engine
- Pipeline Management System  
- Success Playbooks
- Sales Enablement Tools
- Performance Dashboards
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
import logging

from models.database import get_db
from middleware.auth import require_auth, require_admin, User
from services.lead_routing_engine import (
    lead_routing_engine, Lead, LeadSegment, Territory, LeadSource, 
    LeadStage, AssignmentType
)
from services.pipeline_management_system import (
    pipeline_management_system, Deal, DealStage, DealHealth
)
from services.success_playbooks import (
    success_playbooks_engine, PlaybookType, PlaybookTrigger, 
    CustomerHealthStatus
)
from services.sales_enablement_tools import (
    sales_enablement_toolkit, CompetitorType, ContractType
)
from services.performance_dashboards import (
    performance_dashboard_system, PerformanceMetric, TimeRange as DashboardTimeRange
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/operations",
    tags=["Operations Framework"],
    responses={
        500: {"description": "Internal server error"}
    }
)

# ==================== LEAD ROUTING ENDPOINTS ====================

@router.post("/leads/route",
    summary="Route new lead to appropriate sales rep",
    description="Automatically route lead based on segment, territory, ACV, and rep availability")
async def route_lead(
    lead_data: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Route incoming lead to appropriate sales rep"""
    try:
        lead, assigned_rep, routing_reason = lead_routing_engine.route_lead(lead_data)
        
        logger.info(f"🎯 Lead routed by {user.user_id}: {lead.organization_name} → {assigned_rep.name}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "lead": {
                "lead_id": lead.lead_id,
                "organization_name": lead.organization_name,
                "segment": lead.segment.value,
                "territory": lead.territory.value,
                "estimated_acv": float(lead.estimated_acv),
                "urgency_score": lead.urgency_score,
                "fit_score": lead.fit_score
            },
            "assignment": {
                "rep_id": assigned_rep.rep_id,
                "rep_name": assigned_rep.name,
                "role": assigned_rep.role.value,
                "routing_reason": routing_reason
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to route lead: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to route lead: {str(e)}")

@router.get("/leads/routing-analytics",
    summary="Get lead routing analytics and performance",
    description="Comprehensive analytics on lead routing effectiveness and rep performance")
async def get_routing_analytics(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get comprehensive routing analytics"""
    try:
        analytics = lead_routing_engine.get_routing_analytics()
        
        logger.info(f"📊 Routing analytics requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get routing analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routing analytics: {str(e)}")

@router.post("/leads/{lead_id}/reassign",
    summary="Reassign lead to different sales rep",
    description="Manual reassignment of lead with reason tracking")
async def reassign_lead(
    lead_id: str,
    new_rep_id: str = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_admin())
):
    """Reassign lead to different sales rep"""
    try:
        lead = lead_routing_engine.reassign_lead(lead_id, new_rep_id, reason)
        
        logger.warning(f"🔄 Lead reassigned by admin {user.user_id}: {lead_id} → {new_rep_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "lead": {
                "lead_id": lead.lead_id,
                "organization_name": lead.organization_name,
                "assigned_to": lead.assigned_to,
                "reason": reason
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to reassign lead: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== PIPELINE MANAGEMENT ENDPOINTS ====================

@router.post("/pipeline/deals",
    summary="Create deal from qualified lead",
    description="Convert qualified lead into deal in pipeline management system")
async def create_deal(
    deal_data: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Create new deal from qualified lead"""
    try:
        # Create mock lead object for deal creation
        from services.lead_routing_engine import Lead
        lead = Lead(
            lead_id=deal_data['lead_id'],
            organization_name=deal_data['organization_name'],
            contact_name=deal_data['contact_name'],
            contact_email=deal_data['contact_email'],
            contact_phone=deal_data.get('contact_phone'),
            segment=LeadSegment(deal_data['segment']),
            territory=Territory(deal_data['territory']),
            estimated_acv=Decimal(str(deal_data['estimated_acv'])),
            employee_count=deal_data.get('employee_count'),
            annual_budget=Decimal(str(deal_data['annual_budget'])) if deal_data.get('annual_budget') else None,
            source=LeadSource(deal_data['source']),
            stage=LeadStage(deal_data['stage']),
            urgency_score=deal_data['urgency_score'],
            fit_score=deal_data['fit_score'],
            created_at=datetime.utcnow()
        )
        
        deal = pipeline_management_system.create_deal_from_lead(
            lead=lead,
            owner_id=deal_data['owner_id'],
            owner_name=deal_data['owner_name']
        )
        
        logger.info(f"💼 Deal created by {user.user_id}: {deal.organization_name} (${deal.estimated_acv:,.0f})")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "deal": {
                "deal_id": deal.deal_id,
                "organization_name": deal.organization_name,
                "stage": deal.stage.value,
                "estimated_acv": float(deal.estimated_acv),
                "probability": deal.probability,
                "close_date": deal.close_date.isoformat(),
                "owner_name": deal.owner_name
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create deal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create deal: {str(e)}")

@router.post("/pipeline/deals/{deal_id}/advance",
    summary="Advance deal to next stage",
    description="Move deal through pipeline stages with validation")
async def advance_deal_stage(
    deal_id: str,
    new_stage: str = Body(..., embed=True),
    notes: str = Body("", embed=True),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Advance deal to next stage"""
    try:
        deal = pipeline_management_system.advance_deal_stage(
            deal_id=deal_id,
            new_stage=DealStage(new_stage),
            notes=notes
        )
        
        logger.info(f"📈 Deal advanced by {user.user_id}: {deal.organization_name} → {new_stage}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "deal": {
                "deal_id": deal.deal_id,
                "organization_name": deal.organization_name,
                "stage": deal.stage.value,
                "probability": deal.probability,
                "weighted_value": float(deal.weighted_value),
                "health": deal.health.value
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to advance deal: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pipeline/deals/{deal_id}/activities",
    summary="Add activity to deal",
    description="Record sales activity (call, demo, meeting, etc.) for deal")
async def add_deal_activity(
    deal_id: str,
    activity_data: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Add activity to deal"""
    try:
        activity = pipeline_management_system.add_deal_activity(deal_id, activity_data)
        
        logger.info(f"✅ Activity added by {user.user_id}: {activity.activity_type} for deal {deal_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "activity": {
                "activity_id": activity.activity_id,
                "activity_type": activity.activity_type,
                "description": activity.description,
                "performed_by": activity.performed_by,
                "performed_at": activity.performed_at.isoformat(),
                "outcome": activity.outcome
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to add activity: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pipeline/metrics",
    summary="Get pipeline performance metrics",
    description="Comprehensive pipeline analytics and health metrics")
async def get_pipeline_metrics(
    owner_id: Optional[str] = Query(None, description="Filter by deal owner"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get pipeline performance metrics"""
    try:
        metrics = pipeline_management_system.get_pipeline_metrics(owner_id)
        
        logger.info(f"📊 Pipeline metrics requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_deals": metrics.total_deals,
                "total_pipeline_value": float(metrics.total_pipeline_value),
                "weighted_pipeline_value": float(metrics.weighted_pipeline_value),
                "stage_distribution": {k.value: v for k, v in metrics.stage_distribution.items()},
                "healthy_deals": metrics.healthy_deals,
                "at_risk_deals": metrics.at_risk_deals,
                "stalled_deals": metrics.stalled_deals,
                "avg_sales_cycle": metrics.avg_sales_cycle
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get pipeline metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipeline metrics: {str(e)}")

@router.get("/pipeline/forecast",
    summary="Get revenue forecast based on pipeline",
    description="Generate revenue forecast for specified time period")
async def get_deal_forecast(
    time_period_days: int = Query(90, description="Forecast period in days"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get revenue forecast based on pipeline"""
    try:
        forecast = pipeline_management_system.get_deal_forecast(time_period_days)
        
        logger.info(f"📈 Forecast requested by {user.user_id} for {time_period_days} days")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "forecast": forecast
        }
        
    except Exception as e:
        logger.error(f"Failed to get forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

# ==================== SUCCESS PLAYBOOKS ENDPOINTS ====================

@router.post("/playbooks/trigger",
    summary="Trigger playbook for customer",
    description="Initiate success playbook (onboarding, expansion, retention, escalation)")
async def trigger_playbook(
    playbook_data: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Trigger playbook execution for customer"""
    try:
        execution = success_playbooks_engine.trigger_playbook(
            customer_id=playbook_data['customer_id'],
            template_id=playbook_data['template_id'],
            assigned_to=playbook_data['assigned_to'],
            trigger_reason=playbook_data.get('trigger_reason', '')
        )
        
        logger.info(f"🎯 Playbook triggered by {user.user_id}: {execution.playbook_name}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "execution": {
                "execution_id": execution.execution_id,
                "playbook_name": execution.playbook_name,
                "customer_id": execution.customer_id,
                "assigned_to": execution.assigned_to,
                "total_steps": execution.total_steps,
                "expected_completion": execution.expected_completion.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger playbook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/playbooks/{execution_id}/steps/{step_number}/complete",
    summary="Complete playbook step",
    description="Mark playbook step as completed with notes")
async def complete_playbook_step(
    execution_id: str,
    step_number: int,
    completion_notes: str = Body("", embed=True),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Complete playbook step"""
    try:
        execution = success_playbooks_engine.complete_step(execution_id, step_number, completion_notes)
        
        logger.info(f"✅ Playbook step completed by {user.user_id}: Step {step_number}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "execution": {
                "execution_id": execution.execution_id,
                "progress_percentage": execution.progress_percentage,
                "completed_steps": execution.completed_steps,
                "current_step": execution.current_step,
                "status": execution.status.value
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to complete step: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/playbooks/health-score",
    summary="Calculate customer health score",
    description="Calculate comprehensive customer health score and risk assessment")
async def calculate_customer_health(
    health_data: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Calculate customer health score"""
    try:
        health_score = success_playbooks_engine.calculate_customer_health(
            customer_id=health_data['customer_id'],
            usage_data=health_data
        )
        
        logger.info(f"📊 Health score calculated by {user.user_id}: {health_score.organization_name} | Score: {health_score.overall_score}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": {
                "customer_id": health_score.customer_id,
                "organization_name": health_score.organization_name,
                "overall_score": health_score.overall_score,
                "health_status": health_score.health_status.value,
                "usage_score": health_score.usage_score,
                "engagement_score": health_score.engagement_score,
                "value_realization_score": health_score.value_realization_score,
                "support_satisfaction": health_score.support_satisfaction,
                "risk_factors": health_score.risk_factors,
                "recommended_actions": health_score.recommended_actions,
                "playbook_recommendations": health_score.playbook_recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate health score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate health score: {str(e)}")

@router.get("/playbooks/analytics",
    summary="Get playbook performance analytics",
    description="Analytics on playbook effectiveness and customer health")
async def get_playbook_analytics(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get playbook performance analytics"""
    try:
        analytics = success_playbooks_engine.get_playbook_analytics()
        
        logger.info(f"📊 Playbook analytics requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get playbook analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve playbook analytics: {str(e)}")

# ==================== SALES ENABLEMENT ENDPOINTS ====================

@router.post("/enablement/roi-calculator",
    summary="Calculate ROI for prospect",
    description="Generate ROI calculation for value-based selling")
async def calculate_roi(
    prospect_data: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Calculate ROI for prospect value demonstration"""
    try:
        roi_calculation = sales_enablement_toolkit.calculate_roi(prospect_data)
        
        logger.info(f"💰 ROI calculated by {user.user_id}: {roi_calculation.prospect_name} | ROI: {roi_calculation.roi_percentage:.1f}%")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "roi_calculation": {
                "calculation_id": roi_calculation.calculation_id,
                "prospect_name": roi_calculation.prospect_name,
                "segment": roi_calculation.segment,
                "total_annual_value": float(roi_calculation.total_annual_value),
                "annual_platform_cost": float(roi_calculation.annual_platform_cost),
                "net_annual_benefit": float(roi_calculation.net_annual_benefit),
                "roi_percentage": roi_calculation.roi_percentage,
                "payback_months": roi_calculation.payback_months,
                "annual_time_savings_hours": roi_calculation.annual_time_savings_hours,
                "annual_cost_savings": float(roi_calculation.annual_cost_savings)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate ROI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate ROI: {str(e)}")

@router.get("/enablement/battle-cards/{competitor_name}",
    summary="Get competitive battle card",
    description="Retrieve battle card for specific competitor")
async def get_battle_card(
    competitor_name: str,
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get battle card for specific competitor"""
    try:
        battle_card = sales_enablement_toolkit.get_battle_card(competitor_name)
        
        if not battle_card:
            raise HTTPException(status_code=404, detail=f"Battle card not found for competitor: {competitor_name}")
        
        logger.info(f"⚔️ Battle card accessed by {user.user_id}: {battle_card.competitor_name}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "battle_card": {
                "competitor_name": battle_card.competitor_name,
                "competitor_type": battle_card.competitor_type.value,
                "market_position": battle_card.market_position,
                "key_strengths": battle_card.key_strengths,
                "key_weaknesses": battle_card.key_weaknesses,
                "our_advantages": battle_card.our_advantages,
                "differentiation_points": battle_card.differentiation_points,
                "win_strategies": battle_card.win_strategies,
                "objections_responses": battle_card.objections_responses,
                "pricing_comparison": battle_card.pricing_comparison,
                "negotiation_tactics": battle_card.negotiation_tactics
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get battle card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve battle card: {str(e)}")

@router.get("/enablement/pricing-guidance",
    summary="Get pricing guidance",
    description="Get pricing guidelines for segment and tier")
async def get_pricing_guidance(
    segment: str = Query(..., description="Customer segment"),
    tier: str = Query(..., description="Pricing tier"),
    deal_size: Optional[float] = Query(None, description="Deal size for volume discounts"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get pricing guidance for specific segment and tier"""
    try:
        deal_size_decimal = Decimal(str(deal_size)) if deal_size else None
        pricing_guidance = sales_enablement_toolkit.get_pricing_guidance(segment, tier, deal_size_decimal)
        
        if not pricing_guidance:
            raise HTTPException(status_code=404, detail=f"Pricing guidance not found for {segment} {tier}")
        
        logger.info(f"💰 Pricing guidance accessed by {user.user_id}: {segment} {tier}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "pricing_guidance": {
                "segment": pricing_guidance.segment,
                "tier": pricing_guidance.tier,
                "list_price": float(pricing_guidance.list_price),
                "standard_discount_range": pricing_guidance.standard_discount_range,
                "minimum_acceptable_price": float(pricing_guidance.minimum_acceptable_price),
                "volume_discount_tiers": pricing_guidance.volume_discount_tiers,
                "payment_terms": pricing_guidance.payment_terms,
                "pilot_pricing": float(pricing_guidance.pilot_pricing) if pricing_guidance.pilot_pricing else None,
                "nonprofit_discount": pricing_guidance.nonprofit_discount,
                "multi_year_discount": pricing_guidance.multi_year_discount
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing guidance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pricing guidance: {str(e)}")

@router.post("/enablement/contract-generator",
    summary="Generate contract from template",
    description="Generate contract using template with populated data")
async def generate_contract(
    contract_request: Dict[str, Any] = Body(...),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Generate contract from template"""
    try:
        contract_text = sales_enablement_toolkit.generate_contract(
            template_id=contract_request['template_id'],
            contract_data=contract_request['contract_data']
        )
        
        logger.info(f"📄 Contract generated by {user.user_id}: {contract_request['template_id']}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "contract": {
                "template_id": contract_request['template_id'],
                "contract_text": contract_text,
                "generated_by": user.user_id
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate contract: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/enablement/negotiation-strategy",
    summary="Get negotiation strategy",
    description="Get comprehensive negotiation strategy for deal")
async def get_negotiation_strategy(
    competitor: str = Query(..., description="Main competitor"),
    segment: str = Query(..., description="Customer segment"),
    deal_value: float = Query(..., description="Deal value"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get comprehensive negotiation strategy"""
    try:
        strategy = sales_enablement_toolkit.get_negotiation_strategy(
            competitor=competitor,
            segment=segment,
            deal_value=Decimal(str(deal_value))
        )
        
        logger.info(f"🎯 Negotiation strategy requested by {user.user_id}: {competitor} | ${deal_value:,.0f}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": strategy
        }
        
    except Exception as e:
        logger.error(f"Failed to get negotiation strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate negotiation strategy: {str(e)}")

# ==================== PERFORMANCE DASHBOARD ENDPOINTS ====================

@router.get("/performance/scorecard/{rep_id}",
    summary="Get individual performance scorecard",
    description="Comprehensive individual rep performance scorecard and KPIs")
async def get_individual_scorecard(
    rep_id: str,
    time_period: str = Query("MTD", description="Time period: MTD, QTD, YTD"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get individual performance scorecard"""
    try:
        # Convert time period string to enum
        time_range = DashboardTimeRange(time_period.lower())
        scorecard = performance_dashboard_system.generate_individual_scorecard(rep_id, time_range)
        
        logger.info(f"📊 Scorecard requested by {user.user_id}: {scorecard.rep_name}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scorecard": {
                "rep_id": scorecard.rep_id,
                "rep_name": scorecard.rep_name,
                "role": scorecard.role.value,
                "time_period": scorecard.time_period.value,
                "overall_score": scorecard.overall_score,
                "quota_score": scorecard.quota_score,
                "activity_score": scorecard.activity_score,
                "pipeline_score": scorecard.pipeline_score,
                "quota_metrics": {
                    "ytd_attainment": scorecard.quota_metrics.ytd_attainment,
                    "qtd_attainment": scorecard.quota_metrics.qtd_attainment,
                    "mtd_attainment": scorecard.quota_metrics.mtd_attainment,
                    "pipeline_coverage": scorecard.quota_metrics.pipeline_coverage,
                    "annual_quota": float(scorecard.quota_metrics.annual_quota),
                    "ytd_closed": float(scorecard.quota_metrics.ytd_closed)
                },
                "activity_metrics": {
                    "calls_made": scorecard.activity_metrics.calls_made,
                    "call_connect_rate": scorecard.activity_metrics.call_connect_rate,
                    "demos_completed": scorecard.activity_metrics.demos_completed,
                    "demo_show_rate": scorecard.activity_metrics.demo_show_rate,
                    "proposals_sent": scorecard.activity_metrics.proposals_sent,
                    "proposal_acceptance_rate": scorecard.activity_metrics.proposal_acceptance_rate
                },
                "improvement_areas": scorecard.improvement_areas,
                "action_items": scorecard.action_items
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get scorecard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scorecard: {str(e)}")

@router.get("/performance/team-performance",
    summary="Get team performance analytics",
    description="Team-level performance analytics and distribution")
async def get_team_performance(
    team_name: str = Query("Sales Team", description="Team name"),
    time_period: str = Query("QTD", description="Time period: MTD, QTD, YTD"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get team performance analytics"""
    try:
        time_range = DashboardTimeRange(time_period.lower())
        team_performance = performance_dashboard_system.generate_team_performance(team_name, time_range)
        
        logger.info(f"📊 Team performance requested by {user.user_id}: {team_name}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "team_performance": {
                "team_name": team_performance.team_name,
                "time_period": team_performance.time_period.value,
                "total_reps": team_performance.total_reps,
                "team_attainment": team_performance.team_attainment,
                "team_quota": float(team_performance.team_quota),
                "team_closed": float(team_performance.team_closed),
                "total_pipeline": float(team_performance.total_pipeline),
                "reps_above_quota": team_performance.reps_above_quota,
                "reps_at_quota": team_performance.reps_at_quota,
                "reps_below_quota": team_performance.reps_below_quota,
                "average_activity_score": team_performance.average_activity_score
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get team performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve team performance: {str(e)}")

@router.get("/performance/quota-leaderboard",
    summary="Get quota attainment leaderboard",
    description="Quota attainment leaderboard with rankings")
async def get_quota_leaderboard(
    time_period: str = Query("QTD", description="Time period: MTD, QTD, YTD"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get quota attainment leaderboard"""
    try:
        time_range = DashboardTimeRange(time_period.lower())
        leaderboard = performance_dashboard_system.get_quota_leaderboard(time_range)
        
        logger.info(f"🏆 Quota leaderboard requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "leaderboard": leaderboard
        }
        
    except Exception as e:
        logger.error(f"Failed to get quota leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quota leaderboard: {str(e)}")

@router.get("/performance/activity-leaderboard",
    summary="Get activity performance leaderboard",
    description="Activity-based performance leaderboard")
async def get_activity_leaderboard(
    time_period: str = Query("MTD", description="Time period: MTD, QTD, YTD"),
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """Get activity performance leaderboard"""
    try:
        time_range = DashboardTimeRange(time_period.lower())
        leaderboard = performance_dashboard_system.get_activity_leaderboard(time_range)
        
        logger.info(f"⚡ Activity leaderboard requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "leaderboard": leaderboard
        }
        
    except Exception as e:
        logger.error(f"Failed to get activity leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve activity leaderboard: {str(e)}")

@router.get("/performance/executive-dashboard",
    summary="Get executive dashboard",
    description="High-level executive dashboard with key metrics")
async def get_executive_dashboard(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="admin"))
):
    """Get executive dashboard"""
    try:
        dashboard = performance_dashboard_system.get_executive_dashboard()
        
        logger.info(f"👔 Executive dashboard requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dashboard": dashboard
        }
        
    except Exception as e:
        logger.error(f"Failed to get executive dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve executive dashboard: {str(e)}")

# ==================== UNIFIED OPERATIONS ANALYTICS ====================

@router.get("/analytics/unified-operations",
    summary="Get unified operations analytics",
    description="Comprehensive analytics across all operations framework components")
async def get_unified_operations_analytics(
    request_id: str = Depends(lambda: f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"),
    user: User = Depends(require_auth(min_role="admin"))
):
    """Get unified operations analytics across all components"""
    try:
        # Gather analytics from all components
        routing_analytics = lead_routing_engine.get_routing_analytics()
        pipeline_metrics = pipeline_management_system.get_pipeline_metrics()
        playbook_analytics = success_playbooks_engine.get_playbook_analytics()
        enablement_analytics = sales_enablement_toolkit.get_enablement_analytics()
        executive_dashboard = performance_dashboard_system.get_executive_dashboard()
        
        unified_analytics = {
            "operations_summary": {
                "total_leads_routed": routing_analytics["summary"]["total_providers_in_funnel"],
                "total_deals_in_pipeline": pipeline_metrics.total_deals,
                "active_playbooks": playbook_analytics["summary"]["total_executions"],
                "total_team_quota": executive_dashboard["executive_summary"]["total_team_quota"],
                "overall_attainment": executive_dashboard["executive_summary"]["overall_attainment"]
            },
            "lead_routing": {
                "summary": routing_analytics["summary"],
                "rep_performance": routing_analytics["rep_performance"]
            },
            "pipeline": {
                "total_deals": pipeline_metrics.total_deals,
                "total_pipeline_value": float(pipeline_metrics.total_pipeline_value),
                "weighted_pipeline_value": float(pipeline_metrics.weighted_pipeline_value),
                "healthy_deals": pipeline_metrics.healthy_deals,
                "at_risk_deals": pipeline_metrics.at_risk_deals
            },
            "playbooks": {
                "summary": playbook_analytics["summary"],
                "customer_health": playbook_analytics["customer_health"]
            },
            "enablement": {
                "usage_summary": enablement_analytics["usage_summary"],
                "roi_analytics": enablement_analytics["roi_analytics"]
            },
            "performance": {
                "executive_summary": executive_dashboard["executive_summary"],
                "team_composition": executive_dashboard["team_composition"],
                "performance_distribution": executive_dashboard["performance_distribution"]
            }
        }
        
        logger.info(f"📊 Unified operations analytics requested by {user.user_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "unified_analytics": unified_analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get unified analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve unified analytics: {str(e)}")