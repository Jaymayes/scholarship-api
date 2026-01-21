"""
Users Router - CRUD operations for DataService users
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from models.database import get_db
from server.v2.dataservice.models import DataServiceUser, DataServiceEvent, UserStatus, EventType
from server.v2.dataservice.policies import filter_ferpa_fields, get_ferpa_policy

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    role: str = Field(default="consumer", pattern="^(consumer|school_official|admin)$")
    is_ferpa_covered: bool = False
    profile_data: Optional[dict] = None
    preferences: Optional[dict] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    status: Optional[UserStatus] = None
    is_ferpa_covered: Optional[bool] = None
    profile_data: Optional[dict] = None
    preferences: Optional[dict] = None


class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    status: str
    role: Optional[str] = None
    is_ferpa_covered: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def validate_idempotency_key(x_idempotency_key: str = Header(..., alias="X-Idempotency-Key")):
    if not x_idempotency_key or len(x_idempotency_key) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Idempotency-Key header required and must be at least 16 characters"
        )
    return x_idempotency_key


def user_to_dict(user: DataServiceUser) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status.value if user.status else None,
        "role": user.role,
        "is_ferpa_covered": user.is_ferpa_covered,
        "ferpa_consent_date": user.ferpa_consent_date.isoformat() if user.ferpa_consent_date else None,
        "profile_data": user.profile_data,
        "preferences": user.preferences,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "login_count": user.login_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    existing = db.query(DataServiceUser).filter(DataServiceUser.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    new_user = DataServiceUser(
        email=user_data.email,
        display_name=user_data.display_name,
        role=user_data.role,
        is_ferpa_covered=user_data.is_ferpa_covered,
        profile_data=user_data.profile_data,
        preferences=user_data.preferences,
        status=UserStatus.PENDING_VERIFICATION,
    )
    
    db.add(new_user)
    db.flush()
    
    event = DataServiceEvent(
        event_type=EventType.USER_CREATED,
        user_id=new_user.id,
        entity_type="DataServiceUser",
        entity_id=new_user.id,
        action="create",
        changes={"email": user_data.email},
        is_ferpa_access=user_data.is_ferpa_covered,
    )
    db.add(event)
    db.commit()
    db.refresh(new_user)
    
    user_dict = user_to_dict(new_user)
    filtered = filter_ferpa_fields("DataServiceUser", user_dict, x_user_role, new_user.is_ferpa_covered)
    
    return UserResponse(**{k: v for k, v in filtered.items() if k in UserResponse.model_fields})


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    user = db.query(DataServiceUser).filter(
        DataServiceUser.id == uid,
        DataServiceUser.is_deleted == False
    ).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_dict = user_to_dict(user)
    filtered = filter_ferpa_fields("DataServiceUser", user_dict, x_user_role, user.is_ferpa_covered)
    
    return UserResponse(**{k: v for k, v in filtered.items() if k in UserResponse.model_fields})


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
    status_filter: Optional[UserStatus] = Query(None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(DataServiceUser).filter(DataServiceUser.is_deleted == False)
    
    if status_filter:
        query = query.filter(DataServiceUser.status == status_filter)
    
    users = query.order_by(DataServiceUser.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for user in users:
        user_dict = user_to_dict(user)
        filtered = filter_ferpa_fields("DataServiceUser", user_dict, x_user_role, user.is_ferpa_covered)
        result.append(UserResponse(**{k: v for k, v in filtered.items() if k in UserResponse.model_fields}))
    
    return result


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    user = db.query(DataServiceUser).filter(
        DataServiceUser.id == uid,
        DataServiceUser.is_deleted == False
    ).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    changes = {}
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(user, field):
            old_value = getattr(user, field)
            setattr(user, field, value)
            changes[field] = {"old": str(old_value), "new": str(value)}
    
    user.updated_at = datetime.utcnow()
    
    event = DataServiceEvent(
        event_type=EventType.USER_UPDATED,
        user_id=user.id,
        entity_type="DataServiceUser",
        entity_id=user.id,
        action="update",
        changes=changes,
        is_ferpa_access=user.is_ferpa_covered,
    )
    db.add(event)
    db.commit()
    db.refresh(user)
    
    user_dict = user_to_dict(user)
    filtered = filter_ferpa_fields("DataServiceUser", user_dict, x_user_role, user.is_ferpa_covered)
    
    return UserResponse(**{k: v for k, v in filtered.items() if k in UserResponse.model_fields})


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="admin", alias="X-User-Role"),
):
    policy = get_ferpa_policy(x_user_role)
    if not policy.role.value in ["admin", "system"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    
    user = db.query(DataServiceUser).filter(DataServiceUser.id == uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    
    db.commit()
