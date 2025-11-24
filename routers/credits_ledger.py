"""
Credits Ledger Router
Implements master prompt spec for POST /api/v1/credits/credit, POST /api/v1/credits/debit, GET /api/v1/credits/balance
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db
from services.credit_ledger_service import credit_ledger_service
from middleware.auth import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Credits Ledger"], prefix="/api/v1/credits")

# Request/Response Models

class CreditRequest(BaseModel):
    user_id: str
    amount: float
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DebitRequest(BaseModel):
    user_id: str
    amount: float
    purpose: str
    metadata: Optional[Dict[str, Any]] = None

class CreditResponse(BaseModel):
    id: str
    user_id: str
    delta: float
    balance: float
    reason: Optional[str] = None
    created_at: str

class DebitResponse(BaseModel):
    id: str
    user_id: str
    delta: float
    balance: float
    purpose: str
    created_at: str

class BalanceResponse(BaseModel):
    user_id: str
    balance: float
    updated_at: str

# Endpoints

@router.post("/credit", response_model=CreditResponse, status_code=201)
async def credit_user_endpoint(
    request_data: CreditRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Grant credits to a user account (admin/system/provider only)
    
    **Authorization**: Requires JWT with role ∈ {admin, system, provider}
    
    **Headers**:
    - Authorization: Bearer <JWT>
    - Idempotency-Key: <UUIDv4> (required)
    
    **Body**:
    ```json
    {
        "user_id": "string",
        "amount": number,
        "reason": "string (optional)",
        "metadata": object (optional)
    }
    ```
    
    **Response 201**:
    ```json
    {
        "id": "string",
        "user_id": "string",
        "delta": number (positive),
        "balance": number,
        "reason": "string",
        "created_at": "ISO8601 timestamp"
    }
    ```
    
    **Errors**:
    - 400: Invalid request
    - 401: No/invalid JWT
    - 403: Insufficient role
    - 409: Duplicate idempotency key (in-flight or completed)
    - 422: Amount <= 0
    """
    # Authorization: Only admin, system, or provider can credit
    user_roles = [r.lower() for r in current_user.roles] if current_user.roles else []
    allowed_roles = ["admin", "system", "provider"]
    
    if not any(role in allowed_roles for role in user_roles):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient role: requires one of {allowed_roles}, has {user_roles}"
        )
    
    # Use the first matching role as the created_by_role
    created_by_role = next((role for role in user_roles if role in allowed_roles), "unknown")
    
    result = credit_ledger_service.credit_user(
        db=db,
        user_id=request_data.user_id,
        amount=request_data.amount,
        reason=request_data.reason,
        idempotency_key=idempotency_key,
        created_by_role=created_by_role,
        metadata=request_data.metadata
    )
    
    return CreditResponse(**result)

@router.post("/debit", response_model=DebitResponse, status_code=201)
async def debit_user_endpoint(
    request_data: DebitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Debit credits from a user account
    
    **Authorization**: 
    - admin/system can debit any user
    - student can only debit their own user_id
    
    **Headers**:
    - Authorization: Bearer <JWT>
    - Idempotency-Key: <UUIDv4> (required)
    
    **Body**:
    ```json
    {
        "user_id": "string",
        "amount": number,
        "purpose": "string (required)",
        "metadata": object (optional)
    }
    ```
    
    **Response 201**:
    ```json
    {
        "id": "string",
        "user_id": "string",
        "delta": number (negative),
        "balance": number,
        "purpose": "string",
        "created_at": "ISO8601 timestamp"
    }
    ```
    
    **Errors**:
    - 400: Invalid request
    - 401: No/invalid JWT
    - 403: Student trying to debit another user
    - 409: Insufficient balance or duplicate idempotency key
    - 422: Amount <= 0
    """
    # Authorization: admin/system can debit any user, student can only debit self
    user_roles = [r.lower() for r in current_user.roles] if current_user.roles else []
    is_admin_or_system = any(role in ["admin", "system"] for role in user_roles)
    
    if not is_admin_or_system and request_data.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Students can only debit their own account"
        )
    
    # Use the first matching role as the created_by_role
    created_by_role = user_roles[0] if user_roles else "unknown"
    
    result = credit_ledger_service.debit_user(
        db=db,
        user_id=request_data.user_id,
        amount=request_data.amount,
        purpose=request_data.purpose,
        idempotency_key=idempotency_key,
        created_by_role=created_by_role,
        metadata=request_data.metadata
    )
    
    return DebitResponse(**result)

@router.get("/balance", response_model=BalanceResponse, status_code=200)
async def get_balance_endpoint(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user credit balance
    
    **Authorization**:
    - student can only view their own balance
    - admin/system can view any user's balance
    
    **Query Parameters**:
    - user_id: string (required)
    
    **Response 200**:
    ```json
    {
        "user_id": "string",
        "balance": number,
        "updated_at": "ISO8601 timestamp"
    }
    ```
    
    **Errors**:
    - 401: No/invalid JWT
    - 403: Student trying to view another user's balance
    """
    # Authorization: students can only view their own balance
    user_roles = [r.lower() for r in current_user.roles] if current_user.roles else []
    is_admin_or_system = any(role in ["admin", "system"] for role in user_roles)
    
    if not is_admin_or_system and user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Students can only view their own balance"
        )
    
    result = credit_ledger_service.get_balance(
        db=db,
        user_id=user_id
    )
    
    return BalanceResponse(**result)
