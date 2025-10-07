"""
External Billing Models
Database models for externalized payment processing
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExternalPaymentSource(str, Enum):
    """External billing app sources"""
    STUDENT_BILLING_APP = "student_billing_app"
    PROVIDER_BILLING_APP = "provider_billing_app"
    ADMIN_PORTAL = "admin_portal"
    PARTNER_API = "partner_api"


class ExternalCreditGrant(BaseModel):
    """Record of credit grants from external billing apps"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    credits: float
    amount_usd: float
    external_tx_id: str  # Idempotency key from external system
    source_app: ExternalPaymentSource
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class ExternalProviderFeePayment(BaseModel):
    """Record of provider fee payments from external billing"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    amount_usd: float
    period_start: datetime
    period_end: datetime
    external_tx_id: str  # Idempotency key
    paid_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreditGrantRequest(BaseModel):
    """Request to grant credits from external billing app"""
    user_id: str
    credits: float = Field(gt=0, description="Credits to grant (must be positive)")
    amount_usd: float = Field(ge=0, description="Amount paid in USD")
    external_tx_id: str = Field(min_length=1, description="Unique transaction ID from external system")
    source_app: ExternalPaymentSource
    signature: str = Field(min_length=1, description="HMAC signature for request validation")
    timestamp: int = Field(description="Unix timestamp of request")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderFeePaymentRequest(BaseModel):
    """Request to record provider fee payment from external billing"""
    provider_id: str
    amount_usd: float = Field(gt=0, description="Fee amount in USD")
    period_start: datetime
    period_end: datetime
    external_tx_id: str = Field(min_length=1, description="Unique transaction ID")
    signature: str = Field(min_length=1, description="HMAC signature")
    timestamp: int = Field(description="Unix timestamp of request")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalBillingResponse(BaseModel):
    """Response from external billing endpoints"""
    success: bool
    grant_id: str | None = None
    payment_id: str | None = None
    message: str
    credits_granted: float | None = None
    new_balance: float | None = None
