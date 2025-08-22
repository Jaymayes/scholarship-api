# AI Scholarship Playbook - B2B Partner Portal API
# Self-serve partner onboarding and marketplace management

from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging

from models.b2b_partner import (
    Partner, PartnerScholarship, PartnerAnalytics, PartnerOnboardingStep,
    PartnerSupportTicket, PartnerType, PartnerStatus
)
from services.b2b_partner_service import B2BPartnerService
from services.openai_service import OpenAIService
from middleware.rate_limiting import search_rate_limit as rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/partners", tags=["B2B Partners"])

# Initialize partner service
openai_service = OpenAIService()
partner_service = B2BPartnerService(openai_service)

# Request/Response Models
class PartnerRegistrationRequest(BaseModel):
    organization_name: str
    partner_type: PartnerType
    primary_contact_name: str
    primary_contact_email: EmailStr
    primary_contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    tax_id: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"

class PartnerRegistrationResponse(BaseModel):
    success: bool
    partner_id: str
    organization_name: str
    status: PartnerStatus
    onboarding_steps: List[PartnerOnboardingStep]
    next_step: str
    portal_url: str

class ScholarshipListingRequest(BaseModel):
    title: str
    description: str
    award_amount: float
    number_of_awards: int = 1
    application_deadline: str  # ISO format datetime
    min_gpa: Optional[float] = None
    citizenship_requirements: List[str] = []
    field_of_study: List[str] = []
    required_documents: List[str] = []
    essay_required: bool = False
    essay_prompts: List[str] = []
    application_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None

class SupportTicketRequest(BaseModel):
    subject: str
    description: str
    priority: str = "medium"
    category: str = "general"

class OnboardingStepRequest(BaseModel):
    step_data: Dict[str, Any]

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
) -> List[PartnerOnboardingStep]:
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
    step_request: OnboardingStepRequest
) -> PartnerOnboardingStep:
    """Complete specific onboarding step"""
    try:
        completed_step = await partner_service.complete_onboarding_step(
            partner_id, step_id, step_request.step_data
        )
        return completed_step
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to complete onboarding step: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding step"
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
        analytics = await partner_service.get_partner_analytics(partner_id, period_days)
        return analytics
        
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
        
        scholarship = await partner_service.create_scholarship_listing(
            partner_id, listing_dict
        )
        return scholarship
        
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
) -> List[PartnerScholarship]:
    """Get all scholarships for partner"""
    try:
        scholarships = partner_service.get_partner_scholarships(partner_id)
        return scholarships
        
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
        ticket = await partner_service.create_support_ticket(
            partner_id, ticket_data.model_dump()
        )
        return ticket
        
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
        
        resources = {
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
        
        return resources
        
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
        metrics = await partner_service.get_marketplace_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get marketplace metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve marketplace metrics"
        )