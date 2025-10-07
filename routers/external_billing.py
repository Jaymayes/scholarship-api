"""
External Billing API
Secure endpoints for external billing apps to grant credits and record fee payments
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from config.settings import get_settings
from models.external_billing import (
    CreditGrantRequest,
    ExternalBillingResponse,
    ProviderFeePaymentRequest,
)
from services.external_billing_service import (
    ExternalBillingService,
    IdempotencyError,
    SignatureValidationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing/external", tags=["External Billing"])
settings = get_settings()

external_billing_service = ExternalBillingService()

def get_monetization_service():
    """Get the canonical monetization service instance"""
    from routers.monetization import monetization_service
    return monetization_service


def verify_service_key(authorization: str = Header(...)) -> bool:
    """
    Verify Bearer token from external billing app
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If invalid
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]
    
    expected_key = getattr(settings, 'external_billing_api_key', 'dev-api-key-change-in-production')
    
    if token != expected_key:
        raise HTTPException(status_code=401, detail="Invalid service key")
    
    return True


@router.post("/credit-grant", response_model=ExternalBillingResponse)
async def grant_credits_external(
    request_data: CreditGrantRequest,
    _authorized: bool = Depends(verify_service_key)
) -> ExternalBillingResponse:
    """
    Grant credits to user after successful external payment
    
    **Security:**
    - Requires Bearer token authentication
    - HMAC signature validation
    - Timestamp expiry check (5 minutes)
    - Idempotent by external_tx_id
    
    **Request:**
    ```json
    {
        "user_id": "user123",
        "credits": 100.0,
        "amount_usd": 9.99,
        "external_tx_id": "txn_abc123",
        "source_app": "student_billing_app",
        "signature": "hmac_sha256_hex",
        "timestamp": 1234567890,
        "metadata": {}
    }
    ```
    
    **Analytics Events Emitted:**
    - PaymentCompletedExternal
    - CreditBalanceUpdated
    """
    try:
        if not settings.payments_external_enabled:
            raise HTTPException(
                status_code=503,
                detail="External billing is disabled"
            )
        
        if settings.payments_external_test_mode:
            logger.warning("External billing in TEST MODE - no credits granted")
            return ExternalBillingResponse(
                success=True,
                grant_id="test-mode",
                message="Test mode - no credits granted",
                credits_granted=0,
                new_balance=0
            )
        
        monetization_service = get_monetization_service()
        
        grant, new_balance = await external_billing_service.grant_credits(
            request_data,
            monetization_service.credit_balances
        )
        
        return ExternalBillingResponse(
            success=True,
            grant_id=grant.id,
            message=f"Granted {request_data.credits} credits",
            credits_granted=request_data.credits,
            new_balance=new_balance
        )
        
    except SignatureValidationError as e:
        logger.error(f"Signature validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except IdempotencyError as e:
        grant = await external_billing_service.get_grant_by_external_id(
            request_data.external_tx_id
        )
        if grant:
            return ExternalBillingResponse(
                success=True,
                grant_id=grant.id,
                message="Transaction already processed (idempotent)",
                credits_granted=grant.credits,
                new_balance=monetization_service.credit_balances[grant.user_id].available_credits
            )
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to grant credits: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to grant credits")


@router.post("/provider-fee-paid", response_model=ExternalBillingResponse)
async def record_provider_fee_external(
    request_data: ProviderFeePaymentRequest,
    _authorized: bool = Depends(verify_service_key)
) -> ExternalBillingResponse:
    """
    Record provider fee payment (3% platform fee) from external billing
    
    **Security:**
    - Requires Bearer token authentication  
    - HMAC signature validation
    - Timestamp expiry check (5 minutes)
    - Idempotent by external_tx_id
    
    **Request:**
    ```json
    {
        "provider_id": "provider123",
        "amount_usd": 150.00,
        "period_start": "2025-10-01T00:00:00Z",
        "period_end": "2025-10-31T23:59:59Z",
        "external_tx_id": "fee_xyz789",
        "signature": "hmac_sha256_hex",
        "timestamp": 1234567890,
        "metadata": {}
    }
    ```
    
    **Analytics Events Emitted:**
    - ProviderFeePaidExternal
    """
    try:
        if not settings.payments_external_enabled:
            raise HTTPException(
                status_code=503,
                detail="External billing is disabled"
            )
        
        if settings.payments_external_test_mode:
            logger.warning("External billing in TEST MODE - fee not recorded")
            return ExternalBillingResponse(
                success=True,
                payment_id="test-mode",
                message="Test mode - fee not recorded"
            )
        
        payment = await external_billing_service.record_provider_fee_payment(
            request_data
        )
        
        return ExternalBillingResponse(
            success=True,
            payment_id=payment.id,
            message=f"Recorded ${request_data.amount_usd} fee payment"
        )
        
    except SignatureValidationError as e:
        logger.error(f"Signature validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except IdempotencyError as e:
        payment = await external_billing_service.get_provider_payment_by_external_id(
            request_data.external_tx_id
        )
        if payment:
            return ExternalBillingResponse(
                success=True,
                payment_id=payment.id,
                message="Fee payment already recorded (idempotent)"
            )
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to record provider fee: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record provider fee")


@router.get("/analytics-events", include_in_schema=False)
async def get_external_billing_events(
    _authorized: bool = Depends(verify_service_key)
) -> dict:
    """
    Get external billing analytics events (admin/testing only)
    
    Returns PaymentCompletedExternal, ProviderFeePaidExternal, CreditBalanceUpdated events
    """
    return {
        "events": external_billing_service.analytics_events,
        "total_events": len(external_billing_service.analytics_events),
        "total_grants": len(external_billing_service.credit_grants),
        "total_provider_payments": len(external_billing_service.provider_payments)
    }
