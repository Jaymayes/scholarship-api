"""
DataService V2 Sprint-2 Models
SQLAlchemy ORM models for the V2 DataService
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship, validates

from models.database import Base


class UserStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class ProviderStatus(str, PyEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class UploadStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class AccountType(str, PyEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class EventType(str, PyEnum):
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    PROVIDER_ONBOARDED = "provider_onboarded"
    UPLOAD_CREATED = "upload_created"
    UPLOAD_PROCESSED = "upload_processed"
    LEDGER_CREATED = "ledger_created"
    LEDGER_VALIDATED = "ledger_validated"
    FERPA_ACCESS = "ferpa_access"
    AUDIT_LOG = "audit_log"


class AuditMixin:
    """Mixin providing standard audit trail fields"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), nullable=True)


class DataServiceUser(Base, AuditMixin):
    """User model for DataService V2"""
    __tablename__ = "ds_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False)
    role = Column(String(50), default="consumer", nullable=False)
    
    is_ferpa_covered = Column(Boolean, default=False, nullable=False)
    ferpa_consent_date = Column(DateTime, nullable=True)
    
    profile_data = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True)
    
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)

    uploads = relationship("DataServiceUpload", back_populates="owner", lazy="dynamic")
    events = relationship("DataServiceEvent", back_populates="user", lazy="dynamic")

    __table_args__ = (
        Index("ix_ds_users_email_status", "email", "status"),
        Index("ix_ds_users_role", "role"),
    )


class DataServiceProvider(Base, AuditMixin):
    """Provider model for B2B partners"""
    __tablename__ = "ds_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    segment = Column(String(50), nullable=False)
    status = Column(Enum(ProviderStatus), default=ProviderStatus.INVITED, nullable=False)
    
    contact_email = Column(String(255), nullable=False)
    institutional_domain = Column(String(255), nullable=False)
    
    api_key_hash = Column(String(255), nullable=True, unique=True)
    api_key_prefix = Column(String(20), nullable=True, index=True)
    api_key_created_at = Column(DateTime, nullable=True)
    api_key_last_used_at = Column(DateTime, nullable=True)
    
    is_ferpa_covered = Column(Boolean, default=True, nullable=False)
    dpa_signed = Column(Boolean, default=False, nullable=False)
    dpa_signed_date = Column(DateTime, nullable=True)
    
    contract_start_date = Column(DateTime, nullable=True)
    contract_end_date = Column(DateTime, nullable=True)
    monthly_fee = Column(Float, default=0.0, nullable=False)
    
    extra_data = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_ds_providers_segment_status", "segment", "status"),
    )


class DataServiceUpload(Base, AuditMixin):
    """Upload model for file metadata tracking"""
    __tablename__ = "ds_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("ds_users.id"), nullable=False, index=True)
    
    filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    
    is_ferpa_covered = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(UploadStatus), default=UploadStatus.PENDING, nullable=False)
    
    storage_path = Column(String(1000), nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    extra_data = Column(JSON, nullable=True)

    owner = relationship("DataServiceUser", back_populates="uploads")

    __table_args__ = (
        Index("ix_ds_uploads_owner_status", "owner_id", "status"),
        Index("ix_ds_uploads_ferpa", "is_ferpa_covered"),
        CheckConstraint("size_bytes >= 0", name="ck_ds_uploads_size_positive"),
    )


class DataServiceLedger(Base, AuditMixin):
    """Ledger model for double-entry accounting"""
    __tablename__ = "ds_ledgers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    description = Column(Text, nullable=True)
    reference_type = Column(String(100), nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    
    validated_at = Column(DateTime, nullable=True)
    is_balanced = Column(Boolean, default=False, nullable=False)
    
    extra_data = Column(JSON, nullable=True)

    entries = relationship("DataServiceLedgerEntry", back_populates="ledger", lazy="joined", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ds_ledgers_validated", "validated_at"),
        Index("ix_ds_ledgers_reference", "reference_type", "reference_id"),
    )


class DataServiceLedgerEntry(Base):
    """Ledger entry for double-entry accounting (debit positive, credit negative)"""
    __tablename__ = "ds_ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ds_ledgers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    account_type = Column(Enum(AccountType), nullable=False)
    account_code = Column(String(50), nullable=False, index=True)
    account_name = Column(String(255), nullable=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ledger = relationship("DataServiceLedger", back_populates="entries")

    __table_args__ = (
        Index("ix_ds_ledger_entries_account", "account_type", "account_code"),
    )

    @validates("amount")
    def validate_amount(self, key, value):
        if value == 0:
            raise ValueError("Ledger entry amount cannot be zero")
        return value


class DataServiceEvent(Base):
    """Event model for audit trail and event sourcing"""
    __tablename__ = "ds_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("ds_users.id"), nullable=True, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    action = Column(String(50), nullable=False)
    changes = Column(JSON, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    is_ferpa_access = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    extra_data = Column(JSON, nullable=True)

    user = relationship("DataServiceUser", back_populates="events")

    __table_args__ = (
        Index("ix_ds_events_entity", "entity_type", "entity_id"),
        Index("ix_ds_events_created", "created_at"),
        Index("ix_ds_events_ferpa", "is_ferpa_access", "created_at"),
    )


__all__ = [
    "UserStatus",
    "ProviderStatus", 
    "UploadStatus",
    "AccountType",
    "EventType",
    "AuditMixin",
    "DataServiceUser",
    "DataServiceProvider",
    "DataServiceUpload",
    "DataServiceLedger",
    "DataServiceLedgerEntry",
    "DataServiceEvent",
]
