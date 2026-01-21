"""
Providers Router - CRUD operations for B2B providers
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from models.database import get_db
from server.v2.dataservice.models import DataServiceProvider, ProviderStatus
from server.v2.dataservice.policies import filter_ferpa_fields, get_ferpa_policy

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    segment: str = Field(..., pattern="^(university|foundation|corporate|government)$")
    contact_email: EmailStr
    institutional_domain: str = Field(..., min_length=1, max_length=255)
    is_ferpa_covered: bool = True
    monthly_fee: float = Field(default=0.0, ge=0)
    extra_data: Optional[dict] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[ProviderStatus] = None
    contact_email: Optional[EmailStr] = None
    is_ferpa_covered: Optional[bool] = None
    dpa_signed: Optional[bool] = None
    dpa_signed_date: Optional[datetime] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    monthly_fee: Optional[float] = Field(None, ge=0)
    extra_data: Optional[dict] = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    segment: str
    status: str
    contact_email: Optional[str] = None
    institutional_domain: Optional[str] = None
    is_ferpa_covered: Optional[bool] = None
    dpa_signed: Optional[bool] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


def validate_idempotency_key(x_idempotency_key: str = Header(..., alias="X-Idempotency-Key")):
    if not x_idempotency_key or len(x_idempotency_key) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Idempotency-Key header required and must be at least 16 characters"
        )
    return x_idempotency_key


def provider_to_dict(provider: DataServiceProvider) -> dict:
    return {
        "id": str(provider.id),
        "name": provider.name,
        "segment": provider.segment,
        "status": provider.status.value if provider.status else None,
        "contact_email": provider.contact_email,
        "institutional_domain": provider.institutional_domain,
        "is_ferpa_covered": provider.is_ferpa_covered,
        "dpa_signed": provider.dpa_signed,
        "dpa_signed_date": provider.dpa_signed_date.isoformat() if provider.dpa_signed_date else None,
        "contract_start_date": provider.contract_start_date,
        "contract_end_date": provider.contract_end_date,
        "monthly_fee": provider.monthly_fee,
        "extra_data": provider.extra_data,
        "created_at": provider.created_at,
        "updated_at": provider.updated_at,
    }


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="admin", alias="X-User-Role"),
):
    policy = get_ferpa_policy(x_user_role)
    if not policy.role.value in ["admin", "system", "school_official"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    existing = db.query(DataServiceProvider).filter(
        DataServiceProvider.name == provider_data.name,
        DataServiceProvider.is_deleted == False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider with this name already exists"
        )
    
    new_provider = DataServiceProvider(
        name=provider_data.name,
        segment=provider_data.segment,
        contact_email=provider_data.contact_email,
        institutional_domain=provider_data.institutional_domain,
        is_ferpa_covered=provider_data.is_ferpa_covered,
        monthly_fee=provider_data.monthly_fee,
        extra_data=provider_data.extra_data,
        status=ProviderStatus.INVITED,
    )
    
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    
    provider_dict = provider_to_dict(new_provider)
    filtered = filter_ferpa_fields("DataServiceProvider", provider_dict, x_user_role, new_provider.is_ferpa_covered)
    
    return ProviderResponse(**{k: v for k, v in filtered.items() if k in ProviderResponse.model_fields})


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    try:
        pid = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider ID format")
    
    provider = db.query(DataServiceProvider).filter(
        DataServiceProvider.id == pid,
        DataServiceProvider.is_deleted == False
    ).first()
    
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    provider_dict = provider_to_dict(provider)
    filtered = filter_ferpa_fields("DataServiceProvider", provider_dict, x_user_role, provider.is_ferpa_covered)
    
    return ProviderResponse(**{k: v for k, v in filtered.items() if k in ProviderResponse.model_fields})


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
    segment: Optional[str] = Query(None),
    status_filter: Optional[ProviderStatus] = Query(None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(DataServiceProvider).filter(DataServiceProvider.is_deleted == False)
    
    if segment:
        query = query.filter(DataServiceProvider.segment == segment)
    if status_filter:
        query = query.filter(DataServiceProvider.status == status_filter)
    
    providers = query.order_by(DataServiceProvider.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for provider in providers:
        provider_dict = provider_to_dict(provider)
        filtered = filter_ferpa_fields("DataServiceProvider", provider_dict, x_user_role, provider.is_ferpa_covered)
        result.append(ProviderResponse(**{k: v for k, v in filtered.items() if k in ProviderResponse.model_fields}))
    
    return result


@router.patch("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    provider_data: ProviderUpdate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="admin", alias="X-User-Role"),
):
    policy = get_ferpa_policy(x_user_role)
    if not policy.role.value in ["admin", "system", "school_official"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    try:
        pid = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider ID format")
    
    provider = db.query(DataServiceProvider).filter(
        DataServiceProvider.id == pid,
        DataServiceProvider.is_deleted == False
    ).first()
    
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    update_data = provider_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(provider, field):
            setattr(provider, field, value)
    
    provider.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(provider)
    
    provider_dict = provider_to_dict(provider)
    filtered = filter_ferpa_fields("DataServiceProvider", provider_dict, x_user_role, provider.is_ferpa_covered)
    
    return ProviderResponse(**{k: v for k, v in filtered.items() if k in ProviderResponse.model_fields})


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="admin", alias="X-User-Role"),
):
    policy = get_ferpa_policy(x_user_role)
    if not policy.role.value in ["admin", "system"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    try:
        pid = uuid.UUID(provider_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider ID format")
    
    provider = db.query(DataServiceProvider).filter(DataServiceProvider.id == pid).first()
    
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    provider.is_deleted = True
    provider.deleted_at = datetime.utcnow()
    provider.updated_at = datetime.utcnow()
    
    db.commit()
