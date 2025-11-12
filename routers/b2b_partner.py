# AI Scholarship Playbook - B2B Partner Portal API
# Self-serve partner onboarding and marketplace management

import hashlib
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from middleware.rate_limiting import search_rate_limit as rate_limit
from middleware.service_auth import require_service_auth
from models.b2b_partner import (
    Partner,
    PartnerAnalytics,
    PartnerOnboardingStep,
    PartnerScholarship,
    PartnerStatus,
    PartnerSupportTicket,
    PartnerType,
)
from schemas.provider_callback_contract import (
    IdempotencyRecord,
    OnboardingCallbackErrorResponse,
    OnboardingCallbackPayload,
    OnboardingCallbackResponse,
)
from services.b2b_partner_service import B2BPartnerService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/partners", tags=["B2B Partners"])

# Initialize partner service
openai_service = OpenAIService()
partner_service = B2BPartnerService(openai_service)

# Idempotency store for callback deduplication with TTL (in-memory for now)
# Structure: {idempotency_key: (IdempotencyRecord, expiry_timestamp)}
# TTL: 24 hours (allows retries within reasonable window)
# TODO: Move to persistent storage (Redis/PostgreSQL) for production
from collections import OrderedDict
import time

_idempotency_store: OrderedDict[str, tuple[IdempotencyRecord, float]] = OrderedDict()
_IDEMPOTENCY_TTL_SECONDS = 86400  # 24 hours


def _cleanup_expired_idempotency_records():
    """Remove expired idempotency records from cache"""
    current_time = time.time()
    expired_keys = [
        key for key, (record, expiry) in _idempotency_store.items()
        if current_time > expiry
    ]
    for key in expired_keys:
        del _idempotency_store[key]
    
    if expired_keys:
        logger.debug(f"Idempotency: Cleaned up {len(expired_keys)} expired records")

# Request/Response Models
class PartnerRegistrationRequest(BaseModel):
    organization_name: str
    partner_type: PartnerType
    primary_contact_name: str
    primary_contact_email: EmailStr
    primary_contact_phone: str | None = None
    website_url: str | None = None
    tax_id: str | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"

class PartnerRegistrationResponse(BaseModel):
    success: bool
    partner_id: str
    organization_name: str
    status: PartnerStatus
    onboarding_steps: list[PartnerOnboardingStep]
    next_step: str
    portal_url: str

class ScholarshipListingRequest(BaseModel):
    title: str
    description: str
    award_amount: float
    number_of_awards: int = 1
    application_deadline: str  # ISO format datetime
    min_gpa: float | None = None
    citizenship_requirements: list[str] = []
    field_of_study: list[str] = []
    required_documents: list[str] = []
    essay_required: bool = False
    essay_prompts: list[str] = []
    application_url: str | None = None
    contact_email: EmailStr | None = None

class SupportTicketRequest(BaseModel):
    subject: str
    description: str
    priority: str = "medium"
    category: str = "general"

class OnboardingStepRequest(BaseModel):
    step_data: dict[str, Any]

# Partner Registration and Onboarding Endpoints

@router.post("/register", response_model=PartnerRegistrationResponse)
@rate_limit()
async def register_partner(
    request: Request,
    registration_data: PartnerRegistrationRequest
) -> PartnerRegistrationResponse:
    """Register new B2B partner and initialize onboarding"""
    try:
        partner, onboarding_steps = await partner_service.register_partner(
            registration_data.model_dump()
        )

        # Determine next step
        next_step = next(
            (step.step_name for step in onboarding_steps if not step.completed and step.required),
            "Complete"
        )

        portal_url = f"/partners/portal/{partner.partner_id}"

        return PartnerRegistrationResponse(
            success=True,
            partner_id=partner.partner_id,
            organization_name=partner.organization_name,
            status=partner.status,
            onboarding_steps=onboarding_steps,
            next_step=next_step,
            portal_url=portal_url
        )

    except Exception as e:
        logger.error(f"Partner registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/{partner_id}/onboarding")
@rate_limit()
async def get_onboarding_steps(
    request: Request,
    partner_id: str
) -> list[PartnerOnboardingStep]:
    """Get partner onboarding steps and progress"""
    try:
        steps = partner_service.get_partner_onboarding_steps(partner_id)
        if not steps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found"
            )
        return steps

    except Exception as e:
        logger.error(f"Failed to get onboarding steps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve onboarding steps"
        )

@router.post("/{partner_id}/onboarding/{step_id}/complete")
@rate_limit()
async def complete_onboarding_step(
    request: Request,
    partner_id: str,
    step_id: str,
    callback_payload: OnboardingCallbackPayload,
    auth_result: dict = Depends(require_service_auth)
) -> OnboardingCallbackResponse:
    """
    Complete specific onboarding step
    
    CEO Directive: Gate B - Secure callback from provider_register
    
    This endpoint is called by provider_register when an onboarding step is completed.
    Requires service-to-service authentication (X-Service-Auth header).
    Implements idempotency to handle retries safely.
    
    Args:
        partner_id: Partner identifier
        step_id: Onboarding step identifier
        callback_payload: OnboardingCallbackPayload with step completion data
        auth_result: Service authentication result (injected by dependency)
    
    Returns:
        OnboardingCallbackResponse with completion status
    """
    start_time = datetime.now()
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        # Extract step data
        step_data = callback_payload.step_data
        
        # Idempotency check (includes request_id to prevent replay with modified timestamps)
        idempotency_key = IdempotencyRecord.generate_key(
            partner_id=partner_id,
            step_id=step_id,
            completed_at=step_data.completed_at,
            request_id=request_id
        )
        
        # Cleanup expired idempotency records before checking (prevents memory leaks)
        _cleanup_expired_idempotency_records()
        
        # Check if this callback was already processed
        if idempotency_key in _idempotency_store:
            cached_record, expiry = _idempotency_store[idempotency_key]
            current_time = time.time()
            
            # Check if record is still valid (not expired)
            if current_time <= expiry:
                logger.info(
                    f"🔄 Idempotent callback replay detected | "
                    f"partner_id={partner_id} | "
                    f"step_id={step_id} | "
                    f"request_id={request_id} | "
                    f"original_request_id={cached_record.request_id} | "
                    f"cached_response_returned | "
                    f"ttl_remaining={(expiry - current_time):.0f}s"
                )
                
                # Return cached response
                return OnboardingCallbackResponse(**cached_record.response)
            
            # Expired record, remove and process as new
            del _idempotency_store[idempotency_key]
            logger.debug(f"Idempotency: Removed expired record for key {idempotency_key}")
        
        # Process onboarding step completion
        completed_step = await partner_service.complete_onboarding_step(
            partner_id, step_id, step_data.model_dump()
        )
        
        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Build response
        response = OnboardingCallbackResponse(
            success=True,
            step_id=step_id,
            partner_id=partner_id,
            completed=completed_step.completed,
            completed_at=step_data.completed_at,
            request_id=request_id,
            message=f"Onboarding step '{step_id}' completed successfully"
        )
        
        # Store in idempotency cache with TTL expiry
        idempotency_record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            partner_id=partner_id,
            step_id=step_id,
            completed_at=step_data.completed_at,
            request_id=request_id,
            response=response.model_dump()
        )
        expiry_time = time.time() + _IDEMPOTENCY_TTL_SECONDS
        _idempotency_store[idempotency_key] = (idempotency_record, expiry_time)
        
        logger.debug(
            f"Idempotency: Stored callback result with {_IDEMPOTENCY_TTL_SECONDS}s TTL | "
            f"cache_size={len(_idempotency_store)}"
        )
        
        logger.info(
            f"✅ Onboarding callback processed | "
            f"partner_id={partner_id} | "
            f"step_id={step_id} | "
            f"request_id={request_id} | "
            f"latency={latency_ms:.2f}ms | "
            f"completed_by={step_data.completed_by} | "
            f"source={step_data.metadata.source if step_data.metadata else 'unknown'}"
        )
        
        # Performance SLO check
        if latency_ms > 120:
            logger.warning(
                f"⚠️ Callback latency exceeded P95 SLO | "
                f"latency={latency_ms:.2f}ms | "
                f"target=120ms | "
                f"request_id={request_id}"
            )
        
        return response

    except ValueError as e:
        error_response = OnboardingCallbackErrorResponse(
            error="InvalidStepError",
            reason=str(e),
            step_id=step_id,
            partner_id=partner_id,
            request_id=request_id,
            hint="Verify step_id is valid and matches an onboarding step for this partner"
        )
        
        logger.error(
            f"❌ Invalid onboarding step | "
            f"partner_id={partner_id} | "
            f"step_id={step_id} | "
            f"error={str(e)} | "
            f"request_id={request_id}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response.model_dump()
        )
        
    except Exception as e:
        error_response = OnboardingCallbackErrorResponse(
            error="CallbackProcessingError",
            reason=f"Failed to process onboarding callback: {str(e)}",
            step_id=step_id,
            partner_id=partner_id,
            request_id=request_id,
            hint="Check request payload format and service logs"
        )
        
        logger.error(
            f"❌ Callback processing failed | "
            f"partner_id={partner_id} | "
            f"step_id={step_id} | "
            f"error={str(e)} | "
            f"request_id={request_id}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )

# Partner Portal Management

@router.get("/{partner_id}")
@rate_limit()
async def get_partner_details(
    request: Request,
    partner_id: str
) -> Partner:
    """Get partner details for portal dashboard"""
    try:
        partner = partner_service.get_partner_by_id(partner_id)
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found"
            )
        return partner

    except Exception as e:
        logger.error(f"Failed to get partner details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve partner details"
        )

@router.get("/{partner_id}/analytics")
@rate_limit()
async def get_partner_analytics(
    request: Request,
    partner_id: str,
    period_days: int = 30
) -> PartnerAnalytics:
    """Get partner analytics for dashboard"""
    try:
        return await partner_service.get_partner_analytics(partner_id, period_days)

    except Exception as e:
        logger.error(f"Failed to get partner analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )

# Scholarship Listing Management

@router.post("/{partner_id}/scholarships")
@rate_limit()
async def create_scholarship_listing(
    request: Request,
    partner_id: str,
    listing_data: ScholarshipListingRequest
) -> PartnerScholarship:
    """Create new scholarship listing"""
    try:
        from datetime import datetime

        # Parse datetime string
        listing_dict = listing_data.model_dump()
        listing_dict["application_deadline"] = datetime.fromisoformat(
            listing_data.application_deadline.replace('Z', '+00:00')
        )

        return await partner_service.create_scholarship_listing(
            partner_id, listing_dict
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create scholarship listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scholarship listing"
        )

@router.get("/{partner_id}/scholarships")
@rate_limit()
async def get_partner_scholarships(
    request: Request,
    partner_id: str
) -> list[PartnerScholarship]:
    """Get all scholarships for partner"""
    try:
        return partner_service.get_partner_scholarships(partner_id)

    except Exception as e:
        logger.error(f"Failed to get partner scholarships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scholarships"
        )

@router.put("/{partner_id}/scholarships/{listing_id}/publish")
@rate_limit()
async def publish_scholarship_listing(
    request: Request,
    partner_id: str,
    listing_id: str
) -> dict:
    """Publish scholarship listing to make it visible to students"""
    try:
        # Verify partnership and listing ownership
        partner = partner_service.get_partner_by_id(partner_id)
        if not partner or partner.status != PartnerStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Partner not active or not found"
            )

        # Get and publish listing
        scholarship = partner_service.scholarships.get(listing_id)
        if not scholarship or scholarship.partner_id != partner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scholarship listing not found"
            )

        scholarship.published = True
        scholarship.published_at = datetime.utcnow()

        return {
            "success": True,
            "message": "Scholarship listing published successfully",
            "listing_id": listing_id,
            "published_at": scholarship.published_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish scholarship listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish listing"
        )

# Support and Help

@router.post("/{partner_id}/support/tickets")
@rate_limit()
async def create_support_ticket(
    request: Request,
    partner_id: str,
    ticket_data: SupportTicketRequest
) -> PartnerSupportTicket:
    """Create support ticket"""
    try:
        return await partner_service.create_support_ticket(
            partner_id, ticket_data.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to create support ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support ticket"
        )

@router.get("/{partner_id}/support/resources")
@rate_limit()
async def get_support_resources(
    request: Request,
    partner_id: str
) -> dict:
    """Get support resources and documentation for partner"""
    try:
        partner = partner_service.get_partner_by_id(partner_id)
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found"
            )

        support_tier = "pilot" if partner.pilot_program else "standard"

        return {
            "getting_started": {
                "title": "Getting Started Guide",
                "url": "/docs/partners/getting-started",
                "description": "Complete guide to setting up your partner account"
            },
            "scholarship_creation": {
                "title": "Creating Effective Scholarship Listings",
                "url": "/docs/partners/scholarship-creation",
                "description": "Best practices for writing compelling scholarship descriptions"
            },
            "analytics_guide": {
                "title": "Understanding Your Analytics",
                "url": "/docs/partners/analytics",
                "description": "How to interpret your scholarship performance data"
            },
            "api_documentation": {
                "title": "API Documentation",
                "url": "/docs/partners/api",
                "description": "Technical documentation for API integration"
            },
            "support_tier": support_tier,
            "contact_info": {
                "email": "partners@scholarshipplatform.com",
                "phone": "+1 (555) 123-4567" if support_tier == "pilot" else None,
                "response_time": "24 hours" if support_tier == "pilot" else "48 hours"
            }
        }


    except Exception as e:
        logger.error(f"Failed to get support resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve support resources"
        )

# Admin and Metrics (Internal)

@router.get("/admin/marketplace-metrics", include_in_schema=False)
@rate_limit()
async def get_marketplace_metrics(request: Request) -> dict:
    """Get overall marketplace metrics (admin only)"""
    try:
        return await partner_service.get_marketplace_metrics()

    except Exception as e:
        logger.error(f"Failed to get marketplace metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve marketplace metrics"
        )
