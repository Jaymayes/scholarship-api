# AI Scholarship Playbook - B2B Partner Models
# Self-serve partner portal and marketplace functionality

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class PartnerType(str, Enum):
    FOUNDATION = "foundation"
    CORPORATE = "corporate"
    EDUCATIONAL = "educational"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"

class PartnerStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CHURNED = "churned"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"

class Partner(BaseModel):
    """B2B Partner organization"""
    partner_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_name: str
    partner_type: PartnerType
    status: PartnerStatus = PartnerStatus.PENDING
    
    # Contact Information
    primary_contact_name: str
    primary_contact_email: EmailStr
    primary_contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    
    # Organization Details
    tax_id: Optional[str] = None
    nonprofit_status: Optional[bool] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    
    # Verification
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_documents: List[str] = Field(default_factory=list)
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    
    # Agreement and Terms
    agreement_signed: bool = False
    agreement_signed_at: Optional[datetime] = None
    terms_version: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    onboarded_by: Optional[str] = None
    pilot_program: bool = True
    notes: Optional[str] = None

class PartnerScholarship(BaseModel):
    """Scholarship listing by partner"""
    listing_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    partner_id: str
    
    # Basic Information
    title: str
    description: str
    award_amount: float = Field(..., gt=0)
    number_of_awards: int = Field(1, gt=0)
    
    # Timing
    application_deadline: datetime
    notification_date: Optional[datetime] = None
    award_disbursement_date: Optional[datetime] = None
    
    # Eligibility Criteria
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    max_age: Optional[int] = None
    citizenship_requirements: List[str] = Field(default_factory=list)
    field_of_study: List[str] = Field(default_factory=list)
    geographic_restrictions: List[str] = Field(default_factory=list)
    financial_need_required: Optional[bool] = None
    
    # Application Requirements
    required_documents: List[str] = Field(default_factory=list)
    essay_required: bool = False
    essay_prompts: List[str] = Field(default_factory=list)
    letters_of_recommendation: int = 0
    interview_required: bool = False
    
    # Additional Criteria
    community_service_hours: Optional[int] = None
    leadership_experience: bool = False
    first_generation_college: Optional[bool] = None
    underrepresented_minority: Optional[bool] = None
    
    # Application Process
    application_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    additional_instructions: Optional[str] = None
    
    # Status and Visibility
    published: bool = False
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Analytics
    view_count: int = 0
    application_count: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class PartnerAnalytics(BaseModel):
    """Analytics data for partner dashboard"""
    partner_id: str
    period_start: datetime
    period_end: datetime
    
    # Listing Performance
    total_listings: int
    active_listings: int
    total_views: int
    total_applications: int
    
    # Application Funnel
    view_to_application_rate: float = 0.0
    application_completion_rate: float = 0.0
    
    # Applicant Demographics
    applicant_demographics: Dict[str, Any] = Field(default_factory=dict)
    
    # Top Performing Listings
    top_listings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Engagement Metrics
    avg_time_on_listing: Optional[float] = None
    bounce_rate: Optional[float] = None
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class PartnerOnboardingStep(BaseModel):
    """Individual step in partner onboarding process"""
    step_id: str
    partner_id: str
    step_name: str
    step_description: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    required: bool = True
    order_index: int
    
    # Step-specific data
    step_data: Dict[str, Any] = Field(default_factory=dict)
    validation_rules: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PartnerSupportTicket(BaseModel):
    """Support ticket for partner assistance"""
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    partner_id: str
    
    # Ticket Details
    subject: str
    description: str
    priority: str = "medium"  # low, medium, high, urgent
    category: str  # onboarding, technical, billing, general
    status: str = "open"  # open, in_progress, resolved, closed
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    
    # Resolution
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class PartnerPortalSession(BaseModel):
    """Partner portal login session"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    partner_id: str
    user_email: EmailStr
    
    # Session Details
    login_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Session Status
    active: bool = True
    expires_at: datetime
    
    # Activity Tracking
    pages_visited: List[str] = Field(default_factory=list)
    actions_performed: List[str] = Field(default_factory=list)

# Default onboarding steps for partners
DEFAULT_ONBOARDING_STEPS = [
    {
        "step_name": "Organization Registration",
        "step_description": "Provide basic organization information and contact details",
        "order_index": 1,
        "required": True,
        "validation_rules": ["required_fields", "email_format", "tax_id_format"]
    },
    {
        "step_name": "Document Upload",
        "step_description": "Upload verification documents (501c3, tax documents, etc.)",
        "order_index": 2,
        "required": True,
        "validation_rules": ["document_format", "document_size"]
    },
    {
        "step_name": "Agreement Signature",
        "step_description": "Review and electronically sign partnership agreement",
        "order_index": 3,
        "required": True,
        "validation_rules": ["agreement_acknowledged", "signature_provided"]
    },
    {
        "step_name": "First Scholarship Listing",
        "step_description": "Create your first scholarship listing",
        "order_index": 4,
        "required": True,
        "validation_rules": ["listing_complete", "deadline_future"]
    },
    {
        "step_name": "Portal Training",
        "step_description": "Complete guided tour of partner portal features",
        "order_index": 5,
        "required": False,
        "validation_rules": ["training_completed"]
    },
    {
        "step_name": "Analytics Setup",
        "step_description": "Configure analytics preferences and reporting",
        "order_index": 6,
        "required": False,
        "validation_rules": ["preferences_saved"]
    }
]

# Partner support tiers
SUPPORT_TIERS = {
    "pilot": {
        "name": "Pilot Program",
        "response_time": "24 hours",
        "dedicated_support": True,
        "phone_support": True,
        "training_sessions": True,
        "custom_features": True
    },
    "standard": {
        "name": "Standard",
        "response_time": "48 hours", 
        "dedicated_support": False,
        "phone_support": False,
        "training_sessions": False,
        "custom_features": False
    },
    "premium": {
        "name": "Premium",
        "response_time": "12 hours",
        "dedicated_support": True,
        "phone_support": True,
        "training_sessions": True,
        "custom_features": True
    }
}