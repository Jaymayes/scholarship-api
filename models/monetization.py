# AI Scholarship Playbook - Monetization Models
# Credit system and B2B marketplace implementation

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from decimal import Decimal

class CreditTransactionType(str, Enum):
    """Types of credit transactions"""
    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"
    EXPIRY = "expiry"  # Won't be used since credits never expire
    ADMIN_ADJUSTMENT = "admin_adjustment"

class AIOperationType(str, Enum):
    """Types of AI operations that consume credits"""
    SEARCH_ENHANCEMENT = "search_enhancement"
    SCHOLARSHIP_SUMMARY = "scholarship_summary"
    ESSAY_BRAINSTORM = "essay_brainstorm"
    ESSAY_REVIEW = "essay_review"
    ESSAY_IMPROVE = "essay_improve"
    DOCUMENT_OCR = "document_ocr"
    DOCUMENT_ANALYSIS = "document_analysis"
    PREDICTIVE_MATCHING = "predictive_matching"
    PROFILE_ANALYSIS = "profile_analysis"
    APPLICATION_ASSISTANCE = "application_assistance"

class CreditPackage(BaseModel):
    """Credit purchase packages"""
    package_id: str
    name: str
    credit_amount: int
    price_usd: Decimal
    price_per_credit: Decimal
    bonus_credits: int = 0
    
    # Package details
    recommended_for: str  # "light users", "heavy users", etc.
    estimated_operations: int  # How many AI operations this covers
    savings_percentage: Optional[float] = None  # vs smallest package
    
    # Promotional
    is_promotional: bool = False
    promotion_expires: Optional[datetime] = None

class TokenUsageEstimate(BaseModel):
    """Estimate of token usage for AI operations"""
    operation_type: AIOperationType
    estimated_input_tokens: int
    estimated_output_tokens: int
    total_estimated_tokens: int
    
    # Cost calculation (4x markup)
    openai_cost_usd: Decimal
    our_price_usd: Decimal
    markup_percentage: float = 400.0  # 4x markup
    
    # User-friendly pricing
    credits_required: int
    operation_description: str

class CreditUsageRecord(BaseModel):
    """Record of credit usage"""
    transaction_id: str
    user_id: str
    operation_type: AIOperationType
    credits_used: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Operation details
    operation_description: str
    operation_metadata: Dict[str, Any] = {}
    
    # Token tracking
    actual_input_tokens: Optional[int] = None
    actual_output_tokens: Optional[int] = None
    actual_total_tokens: Optional[int] = None
    
    # Cost tracking
    actual_openai_cost: Optional[Decimal] = None
    charged_amount: Decimal

class UserCreditAccount(BaseModel):
    """User's credit account status"""
    user_id: str
    current_balance: int
    total_purchased: int = 0
    total_used: int = 0
    total_bonus_received: int = 0
    
    # Account history
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_purchase: Optional[datetime] = None
    last_usage: Optional[datetime] = None
    
    # Usage patterns
    favorite_operations: List[AIOperationType] = []
    monthly_usage_trend: Dict[str, int] = {}  # month -> credits used
    
class CreditPurchaseRequest(BaseModel):
    """Request to purchase credits"""
    package_id: str
    payment_method_id: str
    promotional_code: Optional[str] = None
    
class CreditPurchaseResponse(BaseModel):
    """Response after credit purchase"""
    transaction_id: str
    credits_added: int
    bonus_credits: int = 0
    new_balance: int
    amount_charged_usd: Decimal
    payment_status: str  # succeeded, failed, pending
    
class OperationCostEstimateRequest(BaseModel):
    """Request to estimate cost of an AI operation"""
    operation_type: AIOperationType
    operation_parameters: Dict[str, Any] = {}
    
class OperationCostEstimateResponse(BaseModel):
    """Response with operation cost estimate"""
    operation_type: AIOperationType
    estimated_credits: int
    estimated_cost_usd: Decimal
    confidence_level: str  # high, medium, low
    
    # User guidance
    operation_description: str
    typical_range_credits: tuple  # (min, max) credits
    factors_affecting_cost: List[str] = []

# B2B Marketplace Models

class PartnerTier(str, Enum):
    """Partner tier levels"""
    BRONZE = "bronze"
    SILVER = "silver" 
    GOLD = "gold"
    PLATINUM = "platinum"
    ENTERPRISE = "enterprise"

class ScholarshipListingType(str, Enum):
    """Types of scholarship listings"""
    BASIC = "basic"              # Standard listing
    FEATURED = "featured"        # Featured placement
    SPONSORED = "sponsored"      # Promoted in search results
    EXCLUSIVE = "exclusive"      # Only on our platform

class PartnerAccount(BaseModel):
    """B2B partner account"""
    partner_id: str
    organization_name: str
    contact_email: str
    contact_name: str
    website_url: Optional[str] = None
    
    # Account details
    tier: PartnerTier = PartnerTier.BRONZE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_verified: bool = False
    is_active: bool = True
    
    # Billing information
    billing_contact: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    tax_id: Optional[str] = None
    
    # Platform usage
    total_scholarships_posted: int = 0
    total_applications_received: int = 0
    total_amount_awarded: Decimal = Decimal('0.00')

class ScholarshipListing(BaseModel):
    """B2B scholarship listing"""
    listing_id: str
    partner_id: str
    scholarship_id: str  # Links to main scholarship record
    
    # Listing details
    listing_type: ScholarshipListingType
    featured_until: Optional[datetime] = None
    listing_fee_paid: Decimal
    
    # Performance tracking
    views: int = 0
    applications_started: int = 0
    applications_completed: int = 0
    conversion_rate: float = 0.0
    
    # Dates
    listed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class PartnerAnalytics(BaseModel):
    """Analytics for B2B partners"""
    partner_id: str
    period_start: datetime
    period_end: datetime
    
    # Application metrics
    total_applications: int
    qualified_applications: int
    application_quality_score: float = Field(ge=0.0, le=1.0)
    
    # Engagement metrics
    total_views: int
    click_through_rate: float = Field(ge=0.0, le=1.0)
    application_conversion_rate: float = Field(ge=0.0, le=1.0)
    
    # Candidate quality
    avg_applicant_gpa: Optional[float] = None
    top_applicant_majors: List[str] = []
    geographic_distribution: Dict[str, int] = {}
    
    # ROI metrics
    cost_per_application: Decimal
    cost_per_qualified_application: Decimal
    estimated_award_efficiency: Optional[float] = None

class RecruitmentRequest(BaseModel):
    """Recruitment-as-a-service request"""
    partner_id: str
    target_criteria: Dict[str, Any]
    budget_range: tuple  # (min, max) budget
    timeline: int  # days
    preferred_candidate_count: int
    
    # Recruitment specifics
    recruitment_type: str  # active_sourcing, targeted_promotion, etc.
    message_template: Optional[str] = None
    additional_requirements: List[str] = []

class RecruitmentCampaign(BaseModel):
    """Active recruitment campaign"""
    campaign_id: str
    partner_id: str
    scholarship_id: str
    
    # Campaign details
    campaign_name: str
    target_criteria: Dict[str, Any]
    budget_allocated: Decimal
    budget_spent: Decimal = Decimal('0.00')
    
    # Performance
    candidates_identified: int = 0
    candidates_contacted: int = 0
    candidates_applied: int = 0
    
    # Timeline
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ends_at: datetime
    is_active: bool = True

class PartnerDashboardData(BaseModel):
    """Data for partner dashboard"""
    partner_id: str
    current_month_metrics: PartnerAnalytics
    
    # Active listings
    active_listings: List[ScholarshipListing] = []
    pending_approvals: int = 0
    
    # Recent activity
    recent_applications: List[Dict[str, Any]] = []
    upcoming_deadlines: List[Dict[str, Any]] = []
    
    # Financial summary
    current_month_spending: Decimal
    remaining_budget: Optional[Decimal] = None
    next_invoice_amount: Decimal
    
    # Recommendations
    performance_insights: List[str] = []
    optimization_suggestions: List[str] = []