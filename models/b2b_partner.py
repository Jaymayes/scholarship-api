# AI Scholarship Playbook - B2B Partner Models
# Self-serve partner portal and marketplace functionality

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


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
    primary_contact_phone: str | None = None
    website_url: str | None = None

    # Organization Details
    tax_id: str | None = None
    nonprofit_status: bool | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"

    # Verification
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_documents: list[str] = Field(default_factory=list)
    verified_at: datetime | None = None
    verified_by: str | None = None

    # Agreement and Terms
    agreement_signed: bool = False
    agreement_signed_at: datetime | None = None
    terms_version: str | None = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    onboarded_by: str | None = None
    pilot_program: bool = True
    notes: str | None = None

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
    notification_date: datetime | None = None
    award_disbursement_date: datetime | None = None

    # Eligibility Criteria
    min_gpa: float | None = Field(None, ge=0.0, le=4.0)
    max_age: int | None = None
    citizenship_requirements: list[str] = Field(default_factory=list)
    field_of_study: list[str] = Field(default_factory=list)
    geographic_restrictions: list[str] = Field(default_factory=list)
    financial_need_required: bool | None = None

    # Application Requirements
    required_documents: list[str] = Field(default_factory=list)
    essay_required: bool = False
    essay_prompts: list[str] = Field(default_factory=list)
    letters_of_recommendation: int = 0
    interview_required: bool = False

    # Additional Criteria
    community_service_hours: int | None = None
    leadership_experience: bool = False
    first_generation_college: bool | None = None
    underrepresented_minority: bool | None = None

    # Application Process
    application_url: str | None = None
    contact_email: EmailStr | None = None
    additional_instructions: str | None = None

    # Status and Visibility
    published: bool = False
    published_at: datetime | None = None
    expires_at: datetime | None = None

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
    applicant_demographics: dict[str, Any] = Field(default_factory=dict)

    # Top Performing Listings
    top_listings: list[dict[str, Any]] = Field(default_factory=list)

    # Engagement Metrics
    avg_time_on_listing: float | None = None
    bounce_rate: float | None = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)

class PartnerOnboardingStep(BaseModel):
    """Individual step in partner onboarding process"""
    step_id: str
    partner_id: str
    step_name: str
    step_description: str
    completed: bool = False
    completed_at: datetime | None = None
    required: bool = True
    order_index: int

    # Step-specific data
    step_data: dict[str, Any] = Field(default_factory=dict)
    validation_rules: list[str] = Field(default_factory=list)

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
    assigned_to: str | None = None
    assigned_at: datetime | None = None

    # Resolution
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    satisfaction_rating: int | None = Field(None, ge=1, le=5)

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
    ip_address: str | None = None
    user_agent: str | None = None

    # Session Status
    active: bool = True
    expires_at: datetime

    # Activity Tracking
    pages_visited: list[str] = Field(default_factory=list)
    actions_performed: list[str] = Field(default_factory=list)

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
