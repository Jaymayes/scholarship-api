# AI Scholarship Playbook - Monetization API Endpoints
# Credit system with transparent pricing and B2C revenue

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from middleware.auth import User, require_auth
from middleware.rate_limiting import search_rate_limit as rate_limit
from models.monetization import (
    CREDIT_PACKAGES,
    STARTER_CREDIT_GRANT,
    CreditBalance,
    CreditPackage,
    CreditTransaction,
    UserCreditSummary,
)
from services.monetization_service import (
    CreditInsufficientError,
    MonetizationService,
    SpendLimitExceededError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/credits", tags=["Monetization"])

# Initialize monetization service
monetization_service = MonetizationService()

class PurchaseCreditsRequest(BaseModel):
    package_id: str
    payment_method_id: str

class PurchaseCreditsResponse(BaseModel):
    success: bool
    transaction_id: str
    new_balance: float
    credits_purchased: int
    bonus_credits: int
    total_cost_usd: float

class CreditUsageRequest(BaseModel):
    feature: str
    operation_id: str
    estimated_tokens: int

class CreditUsageResponse(BaseModel):
    success: bool
    credits_consumed: float
    remaining_balance: float
    operation_id: str

@router.get("/packages")
@rate_limit()
async def get_credit_packages(request: Request) -> list[CreditPackage]:
    """Get available credit packages for purchase"""
    return CREDIT_PACKAGES

@router.get("/balance")
@rate_limit()
async def get_credit_balance(
    request: Request,
    current_user: User = Depends(require_auth())
) -> CreditBalance:
    """Get user's current credit balance"""
    try:
        return await monetization_service.initialize_user_credits(current_user.user_id)
    except Exception as e:
        logger.error(f"Failed to get credit balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credit balance")

@router.get("/summary")
@rate_limit()
async def get_credit_summary(
    request: Request,
    current_user: User = Depends(require_auth())
) -> UserCreditSummary:
    """Get comprehensive credit overview and usage history"""
    try:
        return await monetization_service.get_user_credit_summary(current_user.user_id)
    except Exception as e:
        logger.error(f"Failed to get credit summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credit summary")

@router.post("/purchase")
@rate_limit()
async def purchase_credits(
    request: Request,
    request_data: PurchaseCreditsRequest,
    current_user: User = Depends(require_auth())
) -> PurchaseCreditsResponse:
    """Purchase credit package with payment processing"""
    try:
        # Find the package
        package = next((p for p in CREDIT_PACKAGES if p.package_id == request_data.package_id), None)
        if not package:
            raise HTTPException(status_code=400, detail="Invalid credit package")

        # Process purchase
        transaction, balance = await monetization_service.purchase_credits(
            user_id=current_user.user_id,
            package_id=request_data.package_id,
            payment_method_id=request_data.payment_method_id
        )

        return PurchaseCreditsResponse(
            success=True,
            transaction_id=transaction.transaction_id,
            new_balance=balance.available_credits,
            credits_purchased=package.credits,
            bonus_credits=package.bonus_credits,
            total_cost_usd=package.price_usd
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Credit purchase failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Credit purchase failed")

@router.post("/consume")
@rate_limit()
async def consume_credits(
    request: Request,
    request_data: CreditUsageRequest,
    current_user: User = Depends(require_auth())
) -> CreditUsageResponse:
    """Consume credits for AI feature usage"""
    try:
        # Reserve credits for operation
        usage_event = await monetization_service.consume_credits(
            user_id=current_user.user_id,
            feature=request_data.feature,
            token_count=request_data.estimated_tokens,
            operation_id=request_data.operation_id
        )

        # Get updated balance
        balance = await monetization_service.initialize_user_credits(current_user.user_id)

        return CreditUsageResponse(
            success=usage_event.success,
            credits_consumed=usage_event.credits_consumed,
            remaining_balance=balance.available_credits,
            operation_id=usage_event.operation_id
        )

    except CreditInsufficientError as e:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "Insufficient credits",
                "required": e.required,
                "available": e.available,
                "suggested_package": "starter"  # Could be dynamic
            }
        )
    except SpendLimitExceededError as e:
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail={
                "error": f"{e.limit_type} spending limit exceeded",
                "limit": e.limit,
                "current": e.current
            }
        )
    except Exception as e:
        logger.error(f"Credit consumption failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to consume credits")

@router.post("/confirm/{operation_id}")
@rate_limit()
async def confirm_credit_consumption(
    request: Request,
    operation_id: str,
    actual_tokens: int,
    current_user: User = Depends(require_auth())
) -> CreditTransaction:
    """Confirm credit consumption after successful AI operation"""
    try:
        return await monetization_service.confirm_credit_consumption(
            user_id=current_user.user_id,
            operation_id=operation_id,
            actual_token_count=actual_tokens
        )

    except Exception as e:
        logger.error(f"Failed to confirm credit consumption: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to confirm credit usage")

@router.get("/pricing")
@rate_limit()
async def get_transparent_pricing(request: Request):
    """Get transparent credit pricing information"""
    return {
        "base_openai_cost_per_1k_tokens": 0.002,
        "markup_multiplier": 4.0,
        "credit_cost_per_1k_tokens": 0.008,
        "starter_credits_granted": STARTER_CREDIT_GRANT,
        "transparency_note": "Credits are priced at 4x OpenAI cost to support platform development and features",
        "feature_costs": {
            "Magic Onboarding": "2.5 credits per conversation turn",
            "Document Processing": "5.0 credits per document",
            "Predictive Matching": "3.0 credits per matching request",
            "Essay Coach": "4.0-4.5 credits per session",
            "AI Search": "1.5 credits per search"
        }
    }

@router.get("/metrics", include_in_schema=False)
async def get_monetization_metrics(
    request: Request,
    current_user: User = Depends(require_auth())
):
    """Get B2C monetization KPIs (admin only)"""
    try:
        # In production, would check for admin role
        return await monetization_service.get_monetization_metrics()
    except Exception as e:
        logger.error(f"Failed to get monetization metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
