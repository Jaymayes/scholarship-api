"""
B2B Partner Portal Router
Self-service partner onboarding with 7-day time-to-first-listing target
Segments: Universities, Foundations, Corporates with differentiated value props
"""
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
import logging

from production.b2b_provider_acquisition import (
    b2b_service, 
    ProviderSegment, 
    ProviderStatus,
    ProviderProfile,
    ScholarshipListing
)
from middleware.auth import require_auth, User

router = APIRouter(prefix="/partner", tags=["B2B Partner Portal"])
logger = logging.getLogger(__name__)

# Additional router for b2b-partners endpoints (different prefix)
b2b_router = APIRouter(prefix="/b2b-partners", tags=["B2B Partners"])

@b2b_router.get("/providers", response_model=Dict[str, Any])
async def get_providers_list(
    status: Optional[str] = Query(None, description="Filter by provider status"),
    segment: Optional[str] = Query(None, description="Filter by provider segment"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of providers to return"),
    offset: int = Query(0, ge=0, description="Number of providers to skip"),
    user: User = Depends(require_auth(min_role="partner"))
):
    """
    Get list of B2B partners/providers with filtering and pagination
    Returns comprehensive provider directory for partner management
    """
    try:
        # Filter providers based on query parameters
        providers = []
        total_count = 0
        
        for provider_id, provider in b2b_service.providers.items():
            # Apply filters
            if status and provider.status.value != status:
                continue
            if segment and provider.segment.value != segment:
                continue
                
            total_count += 1
            
            # Apply pagination
            if len(providers) >= limit:
                break
            if total_count <= offset:
                continue
                
            provider_data = {
                "provider_id": provider_id,
                "name": provider.name,
                "segment": provider.segment.value,
                "status": provider.status.value,
                "contact_email": provider.contact_email,
                "institutional_domain": provider.institutional_domain,
                "created_at": provider.created_at.isoformat(),
                "listings_count": provider.listings_count,
                "applications_received": provider.applications_received,
                "revenue_generated": provider.revenue_generated,
                "dpa_signed": provider.dpa_signed,
                "time_to_first_listing_days": provider.time_to_first_listing.days if provider.time_to_first_listing else None,
                "target_met": {
                    "first_listing": provider.time_to_first_listing.days <= b2b_service.target_time_to_first_listing_days if provider.time_to_first_listing else None,
                    "first_application": provider.time_to_first_application.days <= b2b_service.target_time_to_first_application_days if provider.time_to_first_application else None
                }
            }
            providers.append(provider_data)
        
        logger.info(f"📊 Providers list requested by {user.user_id} ({user.roles}) - {len(providers)} providers returned")
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "providers": providers,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "returned": len(providers)
            },
            "summary": {
                "total_providers": len(b2b_service.providers),
                "segments": {
                    "university": len([p for p in b2b_service.providers.values() if p.segment == ProviderSegment.UNIVERSITY]),
                    "foundation": len([p for p in b2b_service.providers.values() if p.segment == ProviderSegment.FOUNDATION]),
                    "corporate": len([p for p in b2b_service.providers.values() if p.segment == ProviderSegment.CORPORATE])
                },
                "status_distribution": {
                    "invited": len([p for p in b2b_service.providers.values() if p.status == ProviderStatus.INVITED]),
                    "meeting": len([p for p in b2b_service.providers.values() if p.status == ProviderStatus.MEETING]),
                    "pilot": len([p for p in b2b_service.providers.values() if p.status == ProviderStatus.PILOT]),
                    "listings_live": len([p for p in b2b_service.providers.values() if p.status == ProviderStatus.FIRST_LISTING]),
                    "first_application": len([p for p in b2b_service.providers.values() if p.status == ProviderStatus.FIRST_APPLICATION]),
                    "paid_plan": len([p for p in b2b_service.providers.values() if p.status == ProviderStatus.PAID_PLAN])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get providers list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve providers list: {str(e)}")

# Request/Response Models
class ProviderRegistrationRequest(BaseModel):
    """Provider registration with institutional validation"""
    name: str = Field(..., min_length=2, max_length=200, description="Institution/Organization name")
    segment: ProviderSegment = Field(..., description="Provider segment: university/foundation/corporate")
    contact_email: EmailStr = Field(..., description="Primary contact email")
    institutional_domain: str = Field(..., description="Institution domain (e.g., harvard.edu)")
    contact_name: str = Field(..., description="Contact person name")
    phone: Optional[str] = Field(None, description="Contact phone number")
    pilot_interest: bool = Field(True, description="Interest in 60-90 day pilot program")

class ProviderRegistrationResponse(BaseModel):
    """Registration response with onboarding next steps"""
    provider_id: str
    name: str
    segment: str
    status: str
    onboarding_url: str
    credentials_url: str
    value_proposition: Dict[str, Any]
    next_steps: List[str]
    pilot_details: Dict[str, Any]
    security_note: str

class ScholarshipListingRequest(BaseModel):
    """Scholarship listing creation with templated fields"""
    title: str = Field(..., min_length=5, max_length=200)
    amount: float = Field(..., gt=0, le=100000, description="Scholarship amount in USD")
    deadline: datetime = Field(..., description="Application deadline")
    description: str = Field(..., min_length=50, max_length=2000)
    requirements: List[str] = Field(..., description="Eligibility requirements")
    application_url: str = Field(..., description="Direct application URL")
    
    # Optional metadata for better matching
    field_of_study: List[str] = Field(default=[], description="Relevant fields of study")
    gpa_requirement: Optional[float] = Field(None, ge=0.0, le=4.0, description="Minimum GPA")
    citizenship_required: Optional[str] = Field(None, description="Citizenship requirement")

class StatusUpdateRequest(BaseModel):
    """Provider status advancement request"""
    new_status: ProviderStatus
    notes: Optional[str] = None

@router.post("/register", response_model=ProviderRegistrationResponse)
async def register_provider(registration: ProviderRegistrationRequest):
    """
    Self-service provider registration with automated setup
    Returns segment-specific value proposition and pilot details
    """
    try:
        # Register provider
        profile = b2b_service.register_provider(
            name=registration.name,
            segment=registration.segment,
            contact_email=registration.contact_email,
            institutional_domain=registration.institutional_domain
        )
        
        # Get segment-specific value proposition
        value_prop = b2b_service.get_segment_value_proposition(registration.segment)
        
        # Generate next steps based on segment
        next_steps = [
            "Complete your institutional profile",
            "Review and sign digital partnership agreement (DPA)",
            "Access your API credentials via the secure credentials endpoint",
            "Create your first scholarship listing using your API key",
            "Configure your provider dashboard",
            f"Target: First listing live within {b2b_service.target_time_to_first_listing_days} days"
        ]
        
        # Pilot program details
        pilot_details = {
            "duration_days": 90,
            "benefits": [
                "Free access to all premium features",
                "Dedicated partner success manager", 
                "Priority customer support",
                "Custom reporting and analytics",
                "No listing fees during pilot"
            ],
            "success_metrics": [
                f"Time-to-first-listing: ≤{b2b_service.target_time_to_first_listing_days} days",
                f"Time-to-first-application: ≤{b2b_service.target_time_to_first_application_days} days",
                "At least 3 active scholarship listings",
                "Minimum 80% provider satisfaction score"
            ]
        }
        
        logger.info(f"✅ Provider registered: {registration.name} ({registration.segment}) - Starting pilot program")
        
        return ProviderRegistrationResponse(
            provider_id=profile.provider_id,
            name=profile.name,
            segment=profile.segment.value,
            status=profile.status.value,
            onboarding_url=f"/partner/onboarding/{profile.provider_id}",
            credentials_url=f"/partner/credentials/{profile.provider_id}",
            value_proposition=value_prop,
            next_steps=next_steps,
            pilot_details=pilot_details,
            security_note="API credentials are available through the secure credentials endpoint after authentication. This ensures your API keys remain protected."
        )
        
    except Exception as e:
        logger.error(f"❌ Provider registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.get("/onboarding/{provider_id}", response_class=HTMLResponse)
async def provider_onboarding_portal(provider_id: str):
    """
    Interactive onboarding portal with progress tracking
    Guides providers through 7-day first listing target
    """
    if provider_id not in b2b_service.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = b2b_service.providers[provider_id]
    value_prop = b2b_service.get_segment_value_proposition(provider.segment)
    
    # Calculate onboarding progress
    days_since_registration = (datetime.utcnow() - provider.created_at).days
    target_days = b2b_service.target_time_to_first_listing_days
    
    progress_items = [
        {
            "step": "Account Created",
            "completed": True,
            "date": provider.created_at.strftime("%Y-%m-%d"),
            "description": "Provider account successfully created"
        },
        {
            "step": "Profile Setup", 
            "completed": provider.status != ProviderStatus.INVITED,
            "date": None,
            "description": "Complete institutional profile and contact details"
        },
        {
            "step": "DPA Signed",
            "completed": provider.dpa_signed,
            "date": provider.dpa_signed_date.strftime("%Y-%m-%d") if provider.dpa_signed_date else None,
            "description": "Digital Partnership Agreement executed"
        },
        {
            "step": "First Listing Created",
            "completed": provider.status in [ProviderStatus.FIRST_LISTING, ProviderStatus.FIRST_APPLICATION, ProviderStatus.PAID_PLAN],
            "date": provider.first_listing_date.strftime("%Y-%m-%d") if provider.first_listing_date else None,
            "description": f"Target: Within {target_days} days of registration"
        }
    ]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Partner Onboarding - {provider.name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8fafc; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
            .header {{ background: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .progress-section {{ background: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .value-prop {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
            .progress-item {{ display: flex; align-items: center; padding: 1rem; border-bottom: 1px solid #e2e8f0; }}
            .progress-item:last-child {{ border-bottom: none; }}
            .status-icon {{ width: 24px; height: 24px; border-radius: 50%; margin-right: 1rem; display: flex; align-items: center; justify-content: center; }}
            .completed {{ background: #10b981; color: white; }}
            .pending {{ background: #6b7280; color: white; }}
            .action-buttons {{ display: flex; gap: 1rem; margin-top: 2rem; }}
            .btn {{ padding: 12px 24px; border: none; border-radius: 6px; font-weight: 500; text-decoration: none; display: inline-block; cursor: pointer; }}
            .btn-primary {{ background: #3b82f6; color: white; }}
            .btn-secondary {{ background: #6b7280; color: white; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem; }}
            .metric-card {{ background: #f1f5f9; padding: 1.5rem; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 2rem; font-weight: bold; color: #1e293b; }}
            .metric-label {{ color: #64748b; font-size: 0.9rem; margin-top: 0.5rem; }}
            .urgency {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
            .success {{ background: #dcfce7; border: 1px solid #16a34a; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 Welcome to the Partner Portal</h1>
                <h2>{provider.name} - {provider.segment.value.title()} Provider</h2>
                <p><strong>Provider ID:</strong> {provider.provider_id}</p>
                <p><strong>Status:</strong> {provider.status.value.replace('_', ' ').title()}</p>
                <p><strong>API Keys:</strong> <a href="/partner/credentials/{provider.provider_id}" class="btn btn-secondary" style="display: inline; padding: 6px 12px; font-size: 0.9rem;">View API Credentials</a></p>
            </div>
            
            <div class="value-prop">
                <h2>{value_prop['headline']}</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 1rem;">
                    <div>
                        <h3>Key Benefits</h3>
                        <ul>
                            {''.join([f'<li>{benefit}</li>' for benefit in value_prop['benefits']])}
                        </ul>
                    </div>
                    <div>
                        <h3>Proof Points</h3>
                        <ul>
                            {''.join([f'<li>{point}</li>' for point in value_prop['proof_points']])}
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="progress-section">
                <h2>📊 Onboarding Progress</h2>
                
                {'<div class="urgency"><strong>⏰ Urgency:</strong> You have ' + str(target_days - days_since_registration) + ' days remaining to meet your first listing target.</div>' if days_since_registration < target_days and not provider.first_listing_date else ''}
                
                {'<div class="success"><strong>🎉 Congratulations!</strong> You met the time-to-first-listing target.</div>' if provider.first_listing_date and provider.time_to_first_listing and provider.time_to_first_listing.days <= target_days else ''}
                
                {''.join([f'''<div class="progress-item">
                    <div class="status-icon {'completed' if item['completed'] else 'pending'}">
                        {'✓' if item['completed'] else str(i+1)}
                    </div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 0.5rem 0;">{item['step']}</h3>
                        <p style="margin: 0; color: #64748b;">{item['description']}</p>
                        {'<small style="color: #10b981;">Completed on ' + item['date'] + '</small>' if item['completed'] and item['date'] else ''}
                    </div>
                </div>''' for i, item in enumerate(progress_items)])}
                
                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-value">{days_since_registration}</div>
                        <div class="metric-label">Days Since Registration</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{provider.listings_count}</div>
                        <div class="metric-label">Scholarship Listings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{provider.applications_received}</div>
                        <div class="metric-label">Applications Received</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{target_days - days_since_registration if days_since_registration < target_days else 0}</div>
                        <div class="metric-label">Days to Target</div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    {'<a href="/partner/dpa/' + provider.provider_id + '" class="btn btn-primary">Sign Partnership Agreement</a>' if not provider.dpa_signed else ''}
                    <a href="/partner/listings/create?provider_id={provider.provider_id}" class="btn btn-primary">Create First Listing</a>
                    <a href="/partner/dashboard/{provider.provider_id}" class="btn btn-secondary">View Dashboard</a>
                    <a href="/devrel/quickstart" class="btn btn-secondary">API Documentation</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@router.get("/credentials/{provider_id}")
async def get_provider_credentials(
    provider_id: str, 
    current_user: User = Depends(require_auth(min_role="partner"))
):
    """
    Secure endpoint to view provider API credentials
    Requires authentication and partner role or higher
    """
    try:
        # Get secure API key info using new method
        api_key_info = b2b_service.get_provider_api_key_for_display(provider_id)
        if not api_key_info:
            raise HTTPException(status_code=404, detail="Provider not found or has no API key")
        
        # Get provider info directly from database
        providers = b2b_service.providers
        if provider_id not in providers:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        provider = providers[provider_id]
        
        # Basic authorization check - more advanced would check if user owns this provider
        logger.info(f"🔐 Credentials accessed for provider {provider_id} by user {current_user.user_id}")
        
        return {
            "provider_id": provider.provider_id,
            "name": provider.name,
            "segment": provider.segment.value,
            "api_key_info": api_key_info,
            "created_at": provider.created_at.isoformat(),
            "status": provider.status.value,
            "security_note": "For security, API keys are hashed and cannot be displayed. Use the regenerate endpoint to get a new key.",
            "regenerate_url": f"/partner/credentials/{provider_id}/regenerate"
        }
        
    except Exception as e:
        logger.error(f"❌ Error accessing credentials for provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unable to retrieve credentials: {str(e)}")

@router.post("/credentials/{provider_id}/regenerate")
async def regenerate_api_key(
    provider_id: str,
    current_user: User = Depends(require_auth(min_role="partner"))
):
    """
    Regenerate API key for provider
    Requires authentication and partner role or higher  
    Returns new API key one time only for security
    """
    try:
        # Use secure regeneration method
        new_api_key = b2b_service.regenerate_provider_api_key(provider_id)
        if not new_api_key:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        logger.warning(f"🔄 API key regenerated for provider {provider_id} by user {current_user.user_id}")
        
        return {
            "provider_id": provider_id,
            "new_api_key": new_api_key,
            "regenerated_at": datetime.utcnow().isoformat(),
            "security_warning": "IMPORTANT: This key is shown once only for security. Save it now - the old API key is now invalid. Update all integrations immediately.",
            "show_once_notice": "This API key will not be displayed again. Store it securely."
        }
        
    except Exception as e:
        logger.error(f"❌ Error regenerating API key for provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unable to regenerate API key: {str(e)}")

@router.get("/dpa/{provider_id}", response_class=HTMLResponse)
async def digital_partnership_agreement(provider_id: str):
    """Digital Partnership Agreement with e-signature capability"""
    if provider_id not in b2b_service.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = b2b_service.providers[provider_id]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digital Partnership Agreement - {provider.name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 2rem; background: white; }}
            .header {{ text-align: center; border-bottom: 2px solid #1e293b; padding-bottom: 1rem; margin-bottom: 2rem; }}
            .agreement {{ line-height: 1.6; color: #374151; }}
            .section {{ margin: 2rem 0; }}
            .signature-section {{ background: #f8fafc; padding: 2rem; border-radius: 8px; margin-top: 3rem; border: 1px solid #e2e8f0; }}
            .btn {{ padding: 12px 24px; background: #10b981; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 1rem; }}
            .btn:hover {{ background: #059669; }}
            .already-signed {{ background: #dcfce7; border: 1px solid #16a34a; padding: 1rem; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SCHOLARSHIP DISCOVERY API</h1>
            <h2>Digital Partnership Agreement</h2>
            <p>Provider: <strong>{provider.name}</strong></p>
            <p>Date: {datetime.utcnow().strftime("%B %d, %Y")}</p>
        </div>
        
        {'<div class="already-signed"><h3>✅ Agreement Already Executed</h3><p>This DPA was signed on ' + (provider.dpa_signed_date.strftime("%B %d, %Y") if provider.dpa_signed_date else "Unknown") + '</p></div>' if provider.dpa_signed else ''}
        
        <div class="agreement">
            <div class="section">
                <h3>1. PARTNERSHIP SCOPE</h3>
                <p>This Digital Partnership Agreement ("Agreement") establishes {provider.name} as an authorized scholarship provider on the Scholarship Discovery API platform, enabling direct access to qualified student applicants through our advanced matching technology.</p>
            </div>
            
            <div class="section">
                <h3>2. DATA PROTECTION & PRIVACY</h3>
                <p><strong>Encryption:</strong> All data transmitted and stored uses AES-256 encryption with TLS 1.3 transport security.</p>
                <p><strong>Least Privilege:</strong> Provider access limited to own listings and anonymized application metrics only.</p>
                <p><strong>PII Protection:</strong> Student personally identifiable information never exposed in analytics or reporting.</p>
                <p><strong>Compliance:</strong> Full FERPA, CCPA, and GDPR compliance with automated audit logging.</p>
            </div>
            
            <div class="section">
                <h3>3. RESPONSIBLE AI COMMITMENTS</h3>
                <p>Our predictive matching system operates with 100% transparency, providing clear explanations for all student-scholarship matches. No algorithmic bias or discriminatory practices are permitted.</p>
            </div>
            
            <div class="section">
                <h3>4. SERVICE LEVEL OBJECTIVES</h3>
                <p><strong>Availability:</strong> 99.95% uptime guarantee with 24/7 monitoring</p>
                <p><strong>Performance:</strong> API responses under 120ms P95 latency</p>
                <p><strong>Support:</strong> Dedicated partner success manager and priority technical support</p>
            </div>
            
            <div class="section">
                <h3>5. PILOT PROGRAM TERMS</h3>
                <p><strong>Duration:</strong> 60-90 day pilot with no platform fees</p>
                <p><strong>Success Metrics:</strong> Time-to-first-listing ≤7 days, time-to-first-application ≤14 days</p>
                <p><strong>Conversion:</strong> Option to convert to paid plan with grandfathered pilot benefits</p>
            </div>
            
            <div class="section">
                <h3>6. MUTUAL COMMITMENTS</h3>
                <p><strong>Provider Commitments:</strong> Maintain accurate scholarship information, respond to qualified applications within 5 business days, provide feedback for platform improvement.</p>
                <p><strong>Platform Commitments:</strong> Deliver qualified student matches, maintain security standards, provide comprehensive analytics and reporting.</p>
            </div>
        </div>
        
        {'<div class="signature-section"><h3>Digital Signature Required</h3><p>By clicking "Execute Agreement", you acknowledge that you have read, understood, and agree to be bound by all terms of this Digital Partnership Agreement.</p><p><strong>Legal Name:</strong> ' + provider.name + '</p><p><strong>Contact Email:</strong> ' + provider.contact_email + '</p><button class="btn" onclick="signAgreement()">Execute Agreement</button></div>' if not provider.dpa_signed else ''}
        
        <script>
            async function signAgreement() {{
                try {{
                    const response = await fetch('/partner/dpa/{provider.provider_id}/sign', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ agreed: true, timestamp: new Date().toISOString() }})
                    }});
                    
                    if (response.ok) {{
                        alert('✅ Agreement successfully executed! Redirecting to onboarding portal...');
                        window.location.href = '/partner/onboarding/{provider.provider_id}';
                    }} else {{
                        alert('❌ Error signing agreement. Please try again.');
                    }}
                }} catch (error) {{
                    alert('❌ Error signing agreement. Please try again.');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html

@router.post("/dpa/{provider_id}/sign")
async def sign_partnership_agreement(provider_id: str, signature_data: Dict[str, Any] = Body(...)):
    """Execute digital partnership agreement with legal timestamp"""
    if provider_id not in b2b_service.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = b2b_service.providers[provider_id]
    
    if provider.dpa_signed:
        raise HTTPException(status_code=400, detail="Agreement already executed")
    
    # Execute DPA
    provider.dpa_signed = True
    provider.dpa_signed_date = datetime.utcnow()
    
    # Advance provider status
    if provider.status == ProviderStatus.INVITED:
        b2b_service.advance_provider_status(provider_id, ProviderStatus.MEETING)
    
    logger.info(f"📝 DPA executed: {provider.name} - {provider_id}")
    
    return {
        "message": "Digital Partnership Agreement successfully executed",
        "provider_id": provider_id,
        "execution_date": provider.dpa_signed_date.isoformat(),
        "status": "executed",
        "next_step": "Create your first scholarship listing"
    }

@router.post("/listings/create", response_model=Dict[str, Any])
async def create_scholarship_listing(
    provider_id: str = Query(..., description="Provider ID"),
    listing: ScholarshipListingRequest = Body(...)
):
    """Create scholarship listing with automated time-to-value tracking"""
    try:
        scholarship = b2b_service.create_scholarship_listing(
            provider_id=provider_id,
            title=listing.title,
            amount=listing.amount,
            deadline=listing.deadline,
            description=listing.description,
            requirements=listing.requirements,
            application_url=listing.application_url,
            field_of_study=listing.field_of_study,
            gpa_requirement=listing.gpa_requirement,
            citizenship_required=listing.citizenship_required
        )
        
        provider = b2b_service.providers[provider_id]
        
        return {
            "message": "Scholarship listing created successfully",
            "listing_id": scholarship.listing_id,
            "provider_id": provider_id,
            "title": scholarship.title,
            "amount": scholarship.amount,
            "time_to_first_listing_days": provider.time_to_first_listing.days if provider.time_to_first_listing else None,
            "target_met": provider.time_to_first_listing.days <= b2b_service.target_time_to_first_listing_days if provider.time_to_first_listing else None,
            "status": provider.status.value,
            "next_steps": [
                "Monitor application analytics in your dashboard",
                "Create additional listings for better student reach",
                "Review predictive matching performance"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Listing creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to create listing: {str(e)}")

@router.get("/dashboard/{provider_id}", response_class=HTMLResponse)
async def provider_dashboard(provider_id: str):
    """Provider analytics dashboard with activation metrics"""
    if provider_id not in b2b_service.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = b2b_service.providers[provider_id]
    provider_listings = [l for l in b2b_service.listings.values() if l.provider_id == provider_id]
    
    # Calculate performance metrics
    total_views = sum(listing.views for listing in provider_listings)
    total_applications = sum(listing.applications for listing in provider_listings)
    conversion_rate = (total_applications / total_views * 100) if total_views > 0 else 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Provider Dashboard - {provider.name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8fafc; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
            .header {{ background: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
            .metric-card {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
            .metric-value {{ font-size: 2.5rem; font-weight: bold; color: #1e293b; margin-bottom: 0.5rem; }}
            .metric-label {{ color: #64748b; font-size: 0.9rem; }}
            .listings-section {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .listing-item {{ border-bottom: 1px solid #e2e8f0; padding: 1.5rem 0; }}
            .listing-item:last-child {{ border-bottom: none; }}
            .success-indicator {{ background: #dcfce7; color: #166534; padding: 0.5rem 1rem; border-radius: 6px; display: inline-block; font-size: 0.875rem; font-weight: 500; }}
            .warning-indicator {{ background: #fef3c7; color: #92400e; padding: 0.5rem 1rem; border-radius: 6px; display: inline-block; font-size: 0.875rem; font-weight: 500; }}
            .btn {{ padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; display: inline-block; margin: 0.5rem 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Provider Dashboard</h1>
                <h2>{provider.name}</h2>
                <p><strong>Status:</strong> {provider.status.value.replace('_', ' ').title()}</p>
                
                {'<div class="success-indicator">🎯 Target Met: Time-to-first-listing = ' + str(provider.time_to_first_listing.days) + ' days</div>' if provider.time_to_first_listing and provider.time_to_first_listing.days <= b2b_service.target_time_to_first_listing_days else ''}
                
                {'<div class="warning-indicator">⏰ Behind Target: ' + str((datetime.utcnow() - provider.created_at).days) + '/' + str(b2b_service.target_time_to_first_listing_days) + ' days elapsed</div>' if not provider.first_listing_date and (datetime.utcnow() - provider.created_at).days >= b2b_service.target_time_to_first_listing_days else ''}
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{provider.listings_count}</div>
                    <div class="metric-label">Active Scholarship Listings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_views}</div>
                    <div class="metric-label">Total Profile Views</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_applications}</div>
                    <div class="metric-label">Applications Received</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{conversion_rate:.1f}%</div>
                    <div class="metric-label">View-to-Application Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{(datetime.utcnow() - provider.created_at).days}</div>
                    <div class="metric-label">Days Since Registration</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${provider.revenue_generated:.2f}</div>
                    <div class="metric-label">Revenue Generated</div>
                </div>
            </div>
            
            <div class="listings-section">
                <h2>📝 Your Scholarship Listings</h2>
                
                {('<p>No listings created yet. <a href="/partner/listings/create?provider_id=' + provider_id + '" class="btn">Create Your First Listing</a></p>') if len(provider_listings) == 0 else ''}
                
                {''.join([f'''<div class="listing-item">
                    <h3>{listing.title}</h3>
                    <p><strong>Amount:</strong> ${listing.amount:,.2f} | <strong>Deadline:</strong> {listing.deadline.strftime("%B %d, %Y")}</p>
                    <p>{listing.description[:150]}{'...' if len(listing.description) > 150 else ''}</p>
                    <p><strong>Performance:</strong> {listing.views} views, {listing.applications} applications</p>
                    <p><strong>Requirements:</strong> {', '.join(listing.requirements[:3])}{'...' if len(listing.requirements) > 3 else ''}</p>
                </div>''' for listing in provider_listings])}
                
                <div style="text-align: center; margin-top: 2rem;">
                    <a href="/partner/listings/create?provider_id={provider_id}" class="btn">+ Create New Listing</a>
                    <a href="/partner/onboarding/{provider_id}" class="btn" style="background: #6b7280;">Back to Onboarding</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@router.get("/status/{provider_id}", response_model=Dict[str, Any])
async def get_provider_status(provider_id: str):
    """Get provider status and activation metrics"""
    if provider_id not in b2b_service.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = b2b_service.providers[provider_id]
    
    return {
        "provider_id": provider_id,
        "name": provider.name,
        "segment": provider.segment.value,
        "status": provider.status.value,
        "created_at": provider.created_at.isoformat(),
        "listings_count": provider.listings_count,
        "applications_received": provider.applications_received,
        "time_to_first_listing_days": provider.time_to_first_listing.days if provider.time_to_first_listing else None,
        "time_to_first_application_days": provider.time_to_first_application.days if provider.time_to_first_application else None,
        "dpa_signed": provider.dpa_signed,
        "revenue_generated": provider.revenue_generated,
        "target_met": {
            "first_listing": provider.time_to_first_listing.days <= b2b_service.target_time_to_first_listing_days if provider.time_to_first_listing else None,
            "first_application": provider.time_to_first_application.days <= b2b_service.target_time_to_first_application_days if provider.time_to_first_application else None
        }
    }

@router.post("/status/{provider_id}/update")
async def update_provider_status(provider_id: str, update: StatusUpdateRequest):
    """Update provider status (for pilot management)"""
    try:
        result = b2b_service.advance_provider_status(provider_id, update.new_status)
        logger.info(f"📈 Status updated: {provider_id} → {update.new_status.value}")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/metrics/onboarding")
async def get_onboarding_metrics():
    """Comprehensive onboarding and activation metrics"""
    metrics = b2b_service.get_onboarding_metrics()
    return {
        "success": True,
        "metrics": metrics,
        "targets": {
            "providers_30_days": b2b_service.target_providers_30_days,
            "time_to_first_listing_days": b2b_service.target_time_to_first_listing_days,
            "time_to_first_application_days": b2b_service.target_time_to_first_application_days,
            "pilot_acceptance_rate": b2b_service.target_pilot_acceptance_rate
        }
    }

@router.get("/report/weekly")
async def get_weekly_provider_report():
    """Weekly 'Provider Engine' report for executive tracking"""
    report = b2b_service.get_weekly_provider_report()
    return {
        "success": True,
        "report": report,
        "report_type": "weekly_provider_engine"
    }

@router.get("/value-propositions")
async def get_segment_value_propositions():
    """Get all segment-specific value propositions for sales enablement"""
    return {
        "success": True,
        "segments": {
            "university": b2b_service.get_segment_value_proposition(ProviderSegment.UNIVERSITY),
            "foundation": b2b_service.get_segment_value_proposition(ProviderSegment.FOUNDATION),
            "corporate": b2b_service.get_segment_value_proposition(ProviderSegment.CORPORATE)
        },
        "targets": {
            "prospects": 30,
            "meetings": 20, 
            "pilots": 10,
            "conversion_rate": "33% prospect-to-meeting, 50% meeting-to-pilot"
        }
    }

logger.info("🏢 B2B Partner Portal router loaded - Self-service onboarding ready")