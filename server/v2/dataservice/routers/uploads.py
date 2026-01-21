"""
Uploads Router - File upload metadata management
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import get_db
from server.v2.dataservice.models import (
    DataServiceUpload,
    DataServiceEvent,
    DataServiceUser,
    UploadStatus,
    EventType,
)
from server.v2.dataservice.policies import filter_ferpa_fields, get_ferpa_policy

router = APIRouter(prefix="/uploads", tags=["uploads"])


ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


class UploadCreate(BaseModel):
    owner_id: str
    filename: str = Field(..., min_length=1, max_length=500)
    mime_type: str = Field(..., min_length=1, max_length=100)
    size_bytes: int = Field(..., ge=1)
    is_ferpa_covered: bool = False
    checksum_sha256: Optional[str] = Field(None, min_length=64, max_length=64)
    extra_data: Optional[dict] = None


class UploadUpdate(BaseModel):
    status: Optional[UploadStatus] = None
    storage_path: Optional[str] = None
    processing_error: Optional[str] = None
    extra_data: Optional[dict] = None


class UploadResponse(BaseModel):
    id: str
    owner_id: Optional[str] = None
    filename: str
    mime_type: str
    size_bytes: int
    is_ferpa_covered: Optional[bool] = None
    status: str
    storage_path: Optional[str] = None
    checksum_sha256: Optional[str] = None
    processed_at: Optional[datetime] = None
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


def upload_to_dict(upload: DataServiceUpload) -> dict:
    return {
        "id": str(upload.id),
        "owner_id": str(upload.owner_id) if upload.owner_id else None,
        "filename": upload.filename,
        "mime_type": upload.mime_type,
        "size_bytes": upload.size_bytes,
        "is_ferpa_covered": upload.is_ferpa_covered,
        "status": upload.status.value if upload.status else None,
        "storage_path": upload.storage_path,
        "checksum_sha256": upload.checksum_sha256,
        "processed_at": upload.processed_at,
        "processing_error": upload.processing_error,
        "extra_data": upload.extra_data,
        "created_at": upload.created_at,
        "updated_at": upload.updated_at,
    }


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    upload_data: UploadCreate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    if upload_data.mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mime type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    if upload_data.size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({MAX_FILE_SIZE_BYTES} bytes)"
        )
    
    try:
        owner_uuid = uuid.UUID(upload_data.owner_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid owner_id format")
    
    owner = db.query(DataServiceUser).filter(
        DataServiceUser.id == owner_uuid,
        DataServiceUser.is_deleted == False
    ).first()
    
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found")
    
    new_upload = DataServiceUpload(
        owner_id=owner_uuid,
        filename=upload_data.filename,
        mime_type=upload_data.mime_type,
        size_bytes=upload_data.size_bytes,
        is_ferpa_covered=upload_data.is_ferpa_covered,
        checksum_sha256=upload_data.checksum_sha256,
        extra_data=upload_data.extra_data,
        status=UploadStatus.PENDING,
    )
    
    db.add(new_upload)
    db.flush()
    
    event = DataServiceEvent(
        event_type=EventType.UPLOAD_CREATED,
        user_id=owner_uuid,
        entity_type="DataServiceUpload",
        entity_id=new_upload.id,
        action="create",
        changes={"filename": upload_data.filename, "size_bytes": upload_data.size_bytes},
        is_ferpa_access=upload_data.is_ferpa_covered,
    )
    db.add(event)
    db.commit()
    db.refresh(new_upload)
    
    upload_dict = upload_to_dict(new_upload)
    filtered = filter_ferpa_fields("DataServiceUpload", upload_dict, x_user_role, new_upload.is_ferpa_covered)
    
    return UploadResponse(**{k: v for k, v in filtered.items() if k in UploadResponse.model_fields})


@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    try:
        uid = uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload ID format")
    
    upload = db.query(DataServiceUpload).filter(
        DataServiceUpload.id == uid,
        DataServiceUpload.is_deleted == False
    ).first()
    
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    
    upload_dict = upload_to_dict(upload)
    filtered = filter_ferpa_fields("DataServiceUpload", upload_dict, x_user_role, upload.is_ferpa_covered)
    
    return UploadResponse(**{k: v for k, v in filtered.items() if k in UploadResponse.model_fields})


@router.get("", response_model=list[UploadResponse])
async def list_uploads(
    db: Session = Depends(get_db),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
    owner_id: Optional[str] = Query(None),
    status_filter: Optional[UploadStatus] = Query(None, alias="status"),
    is_ferpa_covered: Optional[bool] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(DataServiceUpload).filter(DataServiceUpload.is_deleted == False)
    
    if owner_id:
        try:
            owner_uuid = uuid.UUID(owner_id)
            query = query.filter(DataServiceUpload.owner_id == owner_uuid)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid owner_id format")
    
    if status_filter:
        query = query.filter(DataServiceUpload.status == status_filter)
    
    if is_ferpa_covered is not None:
        query = query.filter(DataServiceUpload.is_ferpa_covered == is_ferpa_covered)
    
    uploads = query.order_by(DataServiceUpload.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for upload in uploads:
        upload_dict = upload_to_dict(upload)
        filtered = filter_ferpa_fields("DataServiceUpload", upload_dict, x_user_role, upload.is_ferpa_covered)
        result.append(UploadResponse(**{k: v for k, v in filtered.items() if k in UploadResponse.model_fields}))
    
    return result


@router.patch("/{upload_id}", response_model=UploadResponse)
async def update_upload(
    upload_id: str,
    upload_data: UploadUpdate,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    try:
        uid = uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload ID format")
    
    upload = db.query(DataServiceUpload).filter(
        DataServiceUpload.id == uid,
        DataServiceUpload.is_deleted == False
    ).first()
    
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    
    update_data = upload_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(upload, field):
            setattr(upload, field, value)
    
    if upload_data.status == UploadStatus.COMPLETED:
        upload.processed_at = datetime.utcnow()
        
        event = DataServiceEvent(
            event_type=EventType.UPLOAD_PROCESSED,
            user_id=upload.owner_id,
            entity_type="DataServiceUpload",
            entity_id=upload.id,
            action="process_complete",
            is_ferpa_access=upload.is_ferpa_covered,
        )
        db.add(event)
    
    upload.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(upload)
    
    upload_dict = upload_to_dict(upload)
    filtered = filter_ferpa_fields("DataServiceUpload", upload_dict, x_user_role, upload.is_ferpa_covered)
    
    return UploadResponse(**{k: v for k, v in filtered.items() if k in UploadResponse.model_fields})


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(validate_idempotency_key),
    x_user_role: str = Header(default="consumer", alias="X-User-Role"),
):
    try:
        uid = uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload ID format")
    
    upload = db.query(DataServiceUpload).filter(DataServiceUpload.id == uid).first()
    
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    
    upload.is_deleted = True
    upload.deleted_at = datetime.utcnow()
    upload.status = UploadStatus.DELETED
    upload.updated_at = datetime.utcnow()
    
    db.commit()
