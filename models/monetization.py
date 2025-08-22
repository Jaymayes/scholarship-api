# AI Scholarship Playbook - Monetization Models
# Credit system with transparent pricing and B2C revenue generation

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class CreditTransactionType(str, Enum):
    PURCHASE = "purchase"
    CONSUMPTION = "consumption"
    BONUS = "bonus"
    REFUND = "refund"
    STARTER_GRANT = "starter_grant"

class CreditPackage(BaseModel):
    """Credit package options for purchase"""
    package_id: str
    name: str
    credits: int
    price_usd: float
    per_credit_cost: float
    bonus_credits: int = 0
    popular: bool = False
    description: str

class CreditBalance(BaseModel):
    """User's current credit balance"""
    user_id: str
    total_credits: float
    available_credits: float
    reserved_credits: float = 0  # For pending operations
    last_updated: datetime

class CreditTransaction(BaseModel):
    """Individual credit transaction record"""
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_type: CreditTransactionType
    amount: float
    description: str
    feature_used: Optional[str] = None
    token_count: Optional[int] = None
    cost_basis: Optional[float] = None  # Actual OpenAI cost
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CreditUsageEvent(BaseModel):
    """Event tracking for credit consumption"""
    user_id: str
    feature: str
    credits_consumed: float
    token_count: int
    operation_id: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SpendGuardrail(BaseModel):
    """User spending limits and controls"""
    user_id: str
    daily_limit: Optional[float] = 50.0  # Credits per day
    monthly_limit: Optional[float] = 500.0  # Credits per month
    per_session_limit: Optional[float] = 25.0  # Credits per session
    auto_purchase_enabled: bool = False
    low_balance_threshold: float = 10.0
    notifications_enabled: bool = True

class CreditPricing(BaseModel):
    """Transparent credit pricing model"""
    base_cost_per_1k_tokens: float = 0.002  # OpenAI GPT-4 pricing
    markup_multiplier: float = 4.0  # 4x markup
    credit_per_1k_tokens: float = 0.008  # Will be computed
    
    def model_post_init(self, __context):
        self.credit_per_1k_tokens = self.base_cost_per_1k_tokens * self.markup_multiplier

class UserCreditSummary(BaseModel):
    """Comprehensive user credit overview"""
    user_id: str
    current_balance: CreditBalance
    recent_transactions: List[CreditTransaction]
    monthly_usage: float
    daily_usage: float
    guardrails: SpendGuardrail
    estimated_monthly_spend: float
    savings_vs_pay_per_use: float

class CreditAttachmentMetrics(BaseModel):
    """B2C monetization KPIs"""
    credit_attach_rate: float  # % users who purchase credits
    pay_conversion_rate: float  # % users who convert to paid
    arppu: float  # Average Revenue Per Paying User
    unit_cost_to_serve: float  # Cost per active user
    ltv_cac_ratio: Optional[float] = None

# Standard credit packages
STARTER_CREDIT_GRANT = 50.0  # Free credits on onboarding
CREDIT_PACKAGES = [
    CreditPackage(
        package_id="starter",
        name="Starter Pack",
        credits=100,
        price_usd=9.99,
        per_credit_cost=0.0999,
        description="Perfect for exploring scholarships and trying AI features"
    ),
    CreditPackage(
        package_id="student",
        name="Student Pack",
        credits=300,
        price_usd=24.99,
        per_credit_cost=0.0833,
        bonus_credits=25,
        popular=True,
        description="Most popular - covers full scholarship search and applications"
    ),
    CreditPackage(
        package_id="power",
        name="Power User",
        credits=750,
        price_usd=54.99,
        per_credit_cost=0.0733,
        bonus_credits=100,
        description="For intensive users - document processing and essay assistance"
    ),
    CreditPackage(
        package_id="unlimited",
        name="Unlimited Monthly",
        credits=2000,
        price_usd=99.99,
        per_credit_cost=0.0500,
        bonus_credits=500,
        description="Monthly unlimited for power users and counselors"
    )
]

# Feature credit costs (based on token usage)
FEATURE_CREDIT_COSTS = {
    "magic_onboarding_conversation": 2.5,  # Per conversation turn
    "document_ocr_processing": 5.0,  # Per document
    "predictive_matching": 3.0,  # Per matching request
    "essay_coach_brainstorm": 4.0,  # Per brainstorming session
    "essay_coach_structure": 3.5,  # Per structure suggestion
    "essay_coach_refine": 4.5,  # Per refinement pass
    "scholarship_search_ai": 1.5,  # Per AI-enhanced search
    "application_prefill": 2.0,  # Per application pre-fill
    "recommendation_explanation": 1.0,  # Per "why matched" explanation
    "trend_analysis": 6.0,  # Per trend report
    "custom_insights": 8.0,  # Per custom analysis
}