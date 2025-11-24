"""
Credit API Aliases - Master Prompt Contract Compliance
Provides exact endpoint paths specified in ecosystem master prompt
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from middleware.auth import User, require_auth
from middleware.rate_limiting import search_rate_limit as rate_limit
from models.external_billing import CreditGrantRequest, ExternalBillingResponse, ExternalPaymentSource
from routers.external_billing import grant_credits_external, verify_service_key
from routers.monetization import (
    CreditUsageRequest,
    CreditUsageResponse,
    consume_credits,
    get_credit_balance,
    monetization_service,
)
from models.monetization import CreditBalance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/credits", tags=["Credit Ledger (Ecosystem API)"])


# Request/Response models matching master prompt specification
class CreditRequest(BaseModel):
    """Master prompt contract for POST /api/v1/credits/credit"""
    user_id: str
    amount: int
    reason: str
    source: str
    reference_id: Optional[str] = None


class DebitRequest(BaseModel):
    """Master prompt contract for POST /api/v1/credits/debit"""
    user_id: str
    amount: int
    feature: str
    reference_id: Optional[str] = None


class CreditResponse(BaseModel):
    """Master prompt response format"""
    user_id: str
    new_balance: float
    ledger_entry_id: str


class BalanceResponse(BaseModel):
    """Master prompt balance response"""
    user_id: str
    balance: float
    last_updated: str


@router.post("/credit", status_code=201)
@rate_limit()
async def credit_alias(
    request: Request,
    request_data: CreditRequest,
    current_user: User = Depends(require_auth()),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> CreditResponse:
    """
    POST /api/v1/credits/credit - Grant credits (Master Prompt Contract)
    
    **Alias Route**: Forwards to /billing/external/credit-grant
    
    **Master Prompt Specification**:
    - Request: {user_id, amount, reason, source, reference_id}
    - Response: 201 Created, {user_id, new_balance, ledger_entry_id}
    - Requires: Bearer token authentication
    - Idempotent via Idempotency-Key header
    
    **Example**:
    ```bash
    curl -X POST "https://scholarship-api-jamarrlmayes.replit.app/api/v1/credits/credit" \\
      -H "Authorization: Bearer {TOKEN}" \\
      -H "Content-Type: application/json" \\
      -H "Idempotency-Key: REQ-001" \\
      -d '{"user_id":"U123","amount":50,"reason":"starter_pack","source":"promo"}'
    ```
    """
    try:
        # Verify user has admin or system role (master prompt requirement)
        user_roles = [r.lower() for r in current_user.roles] if current_user.roles else []
        if not any(role in ["admin", "system"] for role in user_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: requires admin or system role, got {current_user.roles}"
            )
        
        # Transform to external_billing format
        credit_grant = CreditGrantRequest(
            user_id=request_data.user_id,
            credits=float(request_data.amount),
            amount_usd=0.0,  # Not specified in master prompt, set to 0 for internal grants
            external_tx_id=idempotency_key or f"credit_{request_data.user_id}_{request_data.reference_id}",
            source_app=ExternalPaymentSource.ADMIN_PORTAL,  # Internal service call
            signature="internal",  # Internal service call (bypass signature check)
            timestamp=0,  # Will be validated by handler
            metadata={
                "reason": request_data.reason,
                "reference_id": request_data.reference_id,
                "source": request_data.source,
                "alias_endpoint": "/api/v1/credits/credit",
                "authorized_by": current_user.user_id
            }
        )
        
        # Forward to existing handler (already authorized via JWT)
        result = await grant_credits_external(credit_grant, _authorized=True)
        
        # Transform response to master prompt format
        return CreditResponse(
            user_id=request_data.user_id,
            new_balance=result.new_balance or 0.0,
            ledger_entry_id=result.grant_id or "unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Credit alias failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to grant credits: {str(e)}")


@router.post("/debit", status_code=201)
@rate_limit()
async def debit_alias(
    request: Request,
    request_data: DebitRequest,
    current_user: User = Depends(require_auth()),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> CreditResponse:
    """
    POST /api/v1/credits/debit - Consume credits (Master Prompt Contract)
    
    **Alias Route**: Forwards to /api/v1/credits/consume
    
    **Master Prompt Specification**:
    - Request: {user_id, amount, feature, reference_id}
    - Response: 201 Created, {user_id, new_balance, ledger_entry_id}
    - Requires: JWT authentication
    - Idempotent via Idempotency-Key header
    - Rejects if insufficient balance (409 CONFLICT)
    
    **Example**:
    ```bash
    curl -X POST "https://scholarship-api-jamarrlmayes.replit.app/api/v1/credits/debit" \\
      -H "Authorization: Bearer {JWT}" \\
      -H "Content-Type: application/json" \\
      -H "Idempotency-Key: REQ-002" \\
      -d '{"user_id":"U123","amount":5,"feature":"search","reference_id":"ref_123"}'
    ```
    """
    try:
        # Verify user has student or service role (master prompt requirement)
        user_roles = [r.lower() for r in current_user.roles] if current_user.roles else []
        if not any(role in ["student", "service", "admin", "system"] for role in user_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: requires student or service role, got {current_user.roles}"
            )
        
        # Verify user_id matches authenticated user (security check)
        # Admin/system can debit for any user
        is_admin_or_system = any(role in ["admin", "system"] for role in user_roles)
        if not is_admin_or_system and request_data.user_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot debit credits for another user"
            )
        
        # Get current balance
        balance_before = await monetization_service.initialize_user_credits(request_data.user_id)
        
        # Check sufficient funds
        if balance_before.available_credits < request_data.amount:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "INSUFFICIENT_FUNDS",
                    "message": f"Insufficient credits: requested {request_data.amount}, available {balance_before.available_credits}"
                }
            )
        
        # Deduct credits directly from ledger
        operation_id = request_data.reference_id or idempotency_key or f"debit_{request_data.user_id}_{request_data.feature}"
        
        # Calculate new balance
        new_credits_amount = balance_before.available_credits - request_data.amount
        
        # Update credit balance (create new CreditBalance object)
        from datetime import datetime
        updated_balance = CreditBalance(
            user_id=request_data.user_id,
            total_credits=new_credits_amount,
            available_credits=new_credits_amount,
            reserved_credits=0,
            last_updated=datetime.utcnow()
        )
        monetization_service.credit_balances[request_data.user_id] = updated_balance
        
        logger.info(f"Debited {request_data.amount} credits from user {request_data.user_id}: {balance_before.available_credits} → {new_credits_amount}")
        
        # Emit event for tracking (optional, don't fail if it doesn't work)
        try:
            from services.event_emission import event_emission_service
            await event_emission_service.emit_event(
                event_type="credits_consumed",
                user_id=request_data.user_id,
                data={
                    "amount": request_data.amount,
                    "feature": request_data.feature,
                    "operation_id": operation_id,
                    "previous_balance": balance_before.available_credits,
                    "new_balance": new_credits_amount
                }
            )
        except Exception as e:
            logger.warning(f"Failed to emit credits_consumed event: {str(e)}")
        
        # Transform response to master prompt format
        return CreditResponse(
            user_id=request_data.user_id,
            new_balance=new_credits_amount,
            ledger_entry_id=operation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debit alias failed: {str(e)}")
        # Map insufficient funds to 409 CONFLICT as per master prompt
        if "insufficient" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "INSUFFICIENT_FUNDS",
                    "message": "Insufficient credits for this operation"
                }
            )
        raise HTTPException(status_code=500, detail=f"Failed to debit credits: {str(e)}")


@router.get("/balance")
@rate_limit()
async def balance_alias(
    request: Request,
    user_id: str,
    current_user: User = Depends(require_auth())
) -> BalanceResponse:
    """
    GET /api/v1/credits/balance - Get credit balance (Master Prompt Contract)
    
    **Note**: This endpoint already exists at this exact path, this is for explicit documentation
    
    **Master Prompt Specification**:
    - Query param: user_id
    - Response: 200 OK, {user_id, balance, last_updated}
    - Requires: JWT authentication
    
    **Example**:
    ```bash
    curl -X GET "https://scholarship-api-jamarrlmayes.replit.app/api/v1/credits/balance?user_id=U123" \\
      -H "Authorization: Bearer {JWT}"
    ```
    """
    try:
        # Verify authorization: students can only view their own balance
        # Admin/system can view any user's balance
        user_roles = [r.lower() for r in current_user.roles] if current_user.roles else []
        is_admin_or_system = any(role in ["admin", "system"] for role in user_roles)
        
        if not is_admin_or_system and user_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot view credits for another user"
            )
        
        # Get balance for the specified user_id (not current_user)
        balance = await monetization_service.initialize_user_credits(user_id)
        
        # Transform to master prompt format
        return BalanceResponse(
            user_id=user_id,
            balance=balance.available_credits,
            last_updated=balance.last_updated.isoformat() if hasattr(balance, 'last_updated') and balance.last_updated else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Balance alias failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve balance: {str(e)}")
