"""
Ledgers Router - Double-entry accounting ledger management
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from server.v2.dataservice.models import (
    DataServiceLedger,
    DataServiceLedgerEntry,
    DataServiceEvent,
    AccountType,
    EventType,
)

router = APIRouter(prefix="/ledgers", tags=["ledgers"])


class LedgerEntryCreate(BaseModel):
    account_type: AccountType
    account_code: str = Field(..., min_length=1, max_length=50)
    account_name: Optional[str] = Field(None, max_length=255)
    amount: float = Field(..., description="Debit positive, credit negative")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: Optional[str] = None
    extra_data: Optional[dict] = None

    @model_validator(mode="after")
    def validate_non_zero_amount(self):
        if self.amount == 0:
            raise ValueError("Ledger entry amount cannot be zero")
        return self


class LedgerCreate(BaseModel):
    trace_id: Optional[str] = None
    description: Optional[str] = None
    reference_type: Optional[str] = Field(None, max_length=100)
    reference_id: Optional[str] = None
    entries: list[LedgerEntryCreate] = Field(..., min_length=2)
    extra_data: Optional[dict] = None

    @model_validator(mode="after")
    def validate_zero_sum(self):
        total = sum(entry.amount for entry in self.entries)
        if abs(total) > 0.0001:  # Floating point tolerance
            raise ValueError(f"Ledger entries must sum to zero (balance). Current sum: {total}")
        return self


class LedgerEntryResponse(BaseModel):
    id: str
    ledger_id: str
    account_type: str
    account_code: str
    account_name: Optional[str] = None
    amount: float
    currency: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LedgerResponse(BaseModel):
    id: str
    trace_id: str
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    validated_at: Optional[datetime] = None
    is_balanced: bool
    entries: list[LedgerEntryResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class ReconcileResponse(BaseModel):
    trace_id: str
    ledger_count: int
    total_debits: float
    total_credits: float
    net_balance: float
    is_balanced: bool
    ledgers: list[LedgerResponse]


def validate_idempotency_key(x_idempotency_key: str = Header(..., alias="X-Idempotency-Key")):
    if not x_idempotency_key or len(x_idempotency_key) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Idempotency-Key header required and must be at least 16 characters"
        )
    return x_idempotency_key


def entry_to_response(entry: DataServiceLedgerEntry) -> LedgerEntryResponse:
    return LedgerEntryResponse(
        id=str(entry.id),
        ledger_id=str(entry.ledger_id),
        account_type=entry.account_type.value if entry.account_type else None,
        account_code=entry.account_code,
        account_name=entry.account_name,
        amount=entry.amount,
        currency=entry.currency,
        description=entry.description,
        created_at=entry.created_at,
    )


def ledger_to_response(ledger: DataServiceLedger) -> LedgerResponse:
    return LedgerResponse(
        id=str(ledger.id),
        trace_id=str(ledger.trace_id),
        description=ledger.description,
        reference_type=ledger.reference_type,
        reference_id=str(ledger.reference_id) if ledger.reference_id else None,
        validated_at=ledger.validated_at,
        is_balanced=ledger.is_balanced,
        entries=[entry_to_response(e) for e in ledger.entries],
        created_at=ledger.created_at,
    )


@router.post("", response_model=LedgerResponse, status_code=status.HTTP_201_CREATED)
async def create_ledger(
    ledger_data: LedgerCreate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="system", alias="X-User-Role"),
):
    if ledger_data.trace_id:
        try:
            trace_uuid = uuid.UUID(ledger_data.trace_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trace_id format")
        
        existing = db.query(DataServiceLedger).filter(DataServiceLedger.trace_id == trace_uuid).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ledger with this trace_id already exists"
            )
    else:
        trace_uuid = uuid.uuid4()
    
    ref_uuid = None
    if ledger_data.reference_id:
        try:
            ref_uuid = uuid.UUID(ledger_data.reference_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reference_id format")
    
    total = sum(entry.amount for entry in ledger_data.entries)
    is_balanced = abs(total) < 0.0001
    
    new_ledger = DataServiceLedger(
        trace_id=trace_uuid,
        description=ledger_data.description,
        reference_type=ledger_data.reference_type,
        reference_id=ref_uuid,
        is_balanced=is_balanced,
        validated_at=datetime.utcnow() if is_balanced else None,
        extra_data=ledger_data.extra_data,
    )
    
    db.add(new_ledger)
    db.flush()
    
    for entry_data in ledger_data.entries:
        entry = DataServiceLedgerEntry(
            ledger_id=new_ledger.id,
            account_type=entry_data.account_type,
            account_code=entry_data.account_code,
            account_name=entry_data.account_name,
            amount=entry_data.amount,
            currency=entry_data.currency,
            description=entry_data.description,
            extra_data=entry_data.extra_data,
        )
        db.add(entry)
    
    event = DataServiceEvent(
        event_type=EventType.LEDGER_CREATED,
        entity_type="DataServiceLedger",
        entity_id=new_ledger.id,
        action="create",
        changes={
            "trace_id": str(trace_uuid),
            "entry_count": len(ledger_data.entries),
            "is_balanced": is_balanced,
        },
    )
    db.add(event)
    
    if is_balanced:
        validate_event = DataServiceEvent(
            event_type=EventType.LEDGER_VALIDATED,
            entity_type="DataServiceLedger",
            entity_id=new_ledger.id,
            action="validate",
            changes={"validated_at": datetime.utcnow().isoformat()},
        )
        db.add(validate_event)
    
    db.commit()
    db.refresh(new_ledger)
    
    return ledger_to_response(new_ledger)


@router.get("/reconcile", response_model=ReconcileResponse)
async def reconcile_ledger(
    trace_id: str = Query(..., description="Trace ID to reconcile"),
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="system", alias="X-User-Role"),
):
    try:
        trace_uuid = uuid.UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trace_id format")
    
    ledgers = db.query(DataServiceLedger).filter(
        DataServiceLedger.trace_id == trace_uuid,
        DataServiceLedger.is_deleted == False
    ).all()
    
    if not ledgers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ledgers found for this trace_id")
    
    all_entries = []
    for ledger in ledgers:
        all_entries.extend(ledger.entries)
    
    total_debits = sum(e.amount for e in all_entries if e.amount > 0)
    total_credits = abs(sum(e.amount for e in all_entries if e.amount < 0))
    net_balance = sum(e.amount for e in all_entries)
    is_balanced = abs(net_balance) < 0.0001
    
    return ReconcileResponse(
        trace_id=str(trace_uuid),
        ledger_count=len(ledgers),
        total_debits=total_debits,
        total_credits=total_credits,
        net_balance=net_balance,
        is_balanced=is_balanced,
        ledgers=[ledger_to_response(l) for l in ledgers],
    )


@router.get("/{ledger_id}", response_model=LedgerResponse)
async def get_ledger(
    ledger_id: str,
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="system", alias="X-User-Role"),
):
    try:
        lid = uuid.UUID(ledger_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ledger ID format")
    
    ledger = db.query(DataServiceLedger).filter(
        DataServiceLedger.id == lid,
        DataServiceLedger.is_deleted == False
    ).first()
    
    if not ledger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found")
    
    return ledger_to_response(ledger)


@router.get("", response_model=list[LedgerResponse])
async def list_ledgers(
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="system", alias="X-User-Role"),
    reference_type: Optional[str] = Query(None),
    reference_id: Optional[str] = Query(None),
    is_balanced: Optional[bool] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(DataServiceLedger).filter(DataServiceLedger.is_deleted == False)
    
    if reference_type:
        query = query.filter(DataServiceLedger.reference_type == reference_type)
    
    if reference_id:
        try:
            ref_uuid = uuid.UUID(reference_id)
            query = query.filter(DataServiceLedger.reference_id == ref_uuid)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reference_id format")
    
    if is_balanced is not None:
        query = query.filter(DataServiceLedger.is_balanced == is_balanced)
    
    ledgers = query.order_by(DataServiceLedger.created_at.desc()).offset(offset).limit(limit).all()
    
    return [ledger_to_response(l) for l in ledgers]


@router.post("/{ledger_id}/validate", response_model=LedgerResponse)
async def validate_ledger(
    ledger_id: str,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="system", alias="X-User-Role"),
):
    try:
        lid = uuid.UUID(ledger_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ledger ID format")
    
    ledger = db.query(DataServiceLedger).filter(
        DataServiceLedger.id == lid,
        DataServiceLedger.is_deleted == False
    ).first()
    
    if not ledger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found")
    
    total = sum(e.amount for e in ledger.entries)
    is_balanced = abs(total) < 0.0001
    
    if not is_balanced:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ledger is not balanced. Net amount: {total}"
        )
    
    ledger.is_balanced = True
    ledger.validated_at = datetime.utcnow()
    ledger.updated_at = datetime.utcnow()
    
    event = DataServiceEvent(
        event_type=EventType.LEDGER_VALIDATED,
        entity_type="DataServiceLedger",
        entity_id=ledger.id,
        action="validate",
        changes={"validated_at": ledger.validated_at.isoformat()},
    )
    db.add(event)
    
    db.commit()
    db.refresh(ledger)
    
    return ledger_to_response(ledger)
