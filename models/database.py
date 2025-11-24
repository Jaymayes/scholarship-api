"""
Database Models and Configuration
SQLAlchemy ORM models for PostgreSQL integration
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config.settings import settings

# Database URL from environment or settings
DATABASE_URL = os.getenv("DATABASE_URL") or settings.database_url

# Create database engine with SSL hardening and production optimizations
if DATABASE_URL:
    # SSL/TLS hardening configuration
    connect_args = {
        "connect_timeout": 10,
        "application_name": "scholarship_api"
    }
    
    # Production SSL hardening - ALWAYS enforce certificate verification
    if settings.environment.value in ["production", "staging"]:
        ssl_root_cert = os.getenv("SSL_ROOT_CERT")
        
        if ssl_root_cert:
            # CRITICAL SECURITY: Full verification when root cert available
            connect_args.update({
                "sslmode": "verify-full",  # Verify server cert AND hostname
                "sslcert": os.getenv("SSL_CLIENT_CERT"),  # Client certificate (optional mTLS)
                "sslkey": os.getenv("SSL_CLIENT_KEY"),    # Client key (optional mTLS)
                "sslrootcert": ssl_root_cert, # CA certificate
                "sslcrl": os.getenv("SSL_CRL"),           # Certificate revocation list (optional)
                "target_session_attrs": "read-write"      # Ensure we connect to primary
            })
            # Remove None values
            connect_args = {k: v for k, v in connect_args.items() if v is not None}
        else:
            # CRITICAL SECURITY: Use system CA bundle for managed cloud databases
            # Neon uses Let's Encrypt (ISRG Root X1) which is in system trust store
            import logging
            logging.info(
                "Production SSL: Using system CA bundle (/etc/ssl/certs/ca-certificates.crt) "
                "for certificate verification with sslmode=verify-full"
            )
            # verify-full: Full validation (cert + hostname) using system CA bundle
            # Neon/RDS/managed providers have valid public certs in Ubuntu trust store
            connect_args["sslmode"] = "verify-full"
            connect_args["sslrootcert"] = "/etc/ssl/certs/ca-certificates.crt"
    
    engine = create_engine(
        DATABASE_URL,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,   # Recycle connections every hour
        connect_args=connect_args,
        # Connection retry and resilience
        pool_timeout=30,     # Wait up to 30s for connection from pool
        max_identifier_length=63  # PostgreSQL standard
    )
else:
    # Fallback to SQLite for development
    engine = create_engine("sqlite:///./scholarships.db", echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ScholarshipDB(Base):
    """Database model for scholarships"""
    __tablename__ = "scholarships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    organization = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False, index=True)
    max_awards = Column(Integer)
    application_deadline = Column(DateTime, nullable=False, index=True)
    notification_date = Column(DateTime)
    scholarship_type = Column(String(50), nullable=False, index=True)
    application_url = Column(String(500))
    contact_email = Column(String(255))
    renewable = Column(Boolean, default=False)

    # Eligibility criteria as JSON
    eligibility_criteria = Column(JSON, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    interactions = relationship("UserInteractionDB", back_populates="scholarship")

class UserProfileDB(Base):
    """Database model for user profiles"""
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True)
    gpa = Column(Float, index=True)
    grade_level = Column(String(50), index=True)
    field_of_study = Column(String(100), index=True)
    citizenship = Column(String(50), index=True)
    state_of_residence = Column(String(2), index=True)
    age = Column(Integer, index=True)
    financial_need = Column(Boolean, index=True)

    # Additional profile data
    extracurricular_activities = Column(ARRAY(String))
    work_experience = Column(JSON)
    academic_achievements = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    interactions = relationship("UserInteractionDB", back_populates="user_profile")

class UserInteractionDB(Base):
    """Database model for user interactions"""
    __tablename__ = "user_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.id"), nullable=False, index=True)
    scholarship_id = Column(String, ForeignKey("scholarships.id"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)  # viewed, saved, applied, dismissed

    # Interaction context
    search_query = Column(String(500))
    filters_applied = Column(JSON)
    match_score = Column(Float)
    position_in_results = Column(Integer)

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(String(100), index=True)
    source = Column(String(50), index=True)  # search, recommendations, direct

    # Relationships
    user_profile = relationship("UserProfileDB", back_populates="interactions")
    scholarship = relationship("ScholarshipDB", back_populates="interactions")

class OrganizationDB(Base):
    """Database model for scholarship organizations"""
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    website = Column(String(500))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))

    # Organization metadata
    organization_type = Column(String(100))  # foundation, university, corporate, government
    established_year = Column(Integer)
    total_awards_given = Column(Integer, default=0)
    total_amount_awarded = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class SearchAnalyticsDB(Base):
    """Database model for search analytics"""
    __tablename__ = "search_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    search_query = Column(String(500), index=True)
    filters_applied = Column(JSON)
    results_count = Column(Integer, nullable=False)
    user_id = Column(String, index=True)

    # Search performance
    response_time_ms = Column(Float)
    clicked_results = Column(ARRAY(String))  # scholarship IDs that were clicked
    search_quality_score = Column(Float)  # 0.0-1.0 based on user engagement

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(String(100), index=True)
    user_agent = Column(String(500))
    ip_address = Column(String(45))

class ProviderDB(Base):
    """Database model for B2B scholarship providers"""
    __tablename__ = "providers"

    provider_id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    segment = Column(String(20), nullable=False, index=True)  # university, foundation, corporate
    status = Column(String(20), nullable=False, index=True, default="invited")
    contact_email = Column(String(255), nullable=False)
    institutional_domain = Column(String(100), nullable=False)

    # API credentials - store hash for security
    api_key_hash = Column(String(200), unique=True, index=True)
    api_key_prefix = Column(String(20), index=True)  # For identification (pvd_xxxxx)
    api_key_created_at = Column(DateTime)
    api_key_last_used = Column(DateTime)

    # Onboarding metrics
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    first_listing_date = Column(DateTime)
    first_application_date = Column(DateTime)

    # Account details
    listings_count = Column(Integer, default=0)
    applications_received = Column(Integer, default=0)

    # Contract/compliance
    dpa_signed = Column(Boolean, default=False)
    dpa_signed_date = Column(DateTime)
    pilot_start_date = Column(DateTime)
    pilot_end_date = Column(DateTime)

    # Business metrics
    monthly_fee = Column(Float, default=0.0)
    revenue_generated = Column(Float, default=0.0)

    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    listings = relationship("ScholarshipListingDB", back_populates="provider")

class ScholarshipListingDB(Base):
    """Database model for provider scholarship listings"""
    __tablename__ = "scholarship_listings"

    listing_id = Column(String, primary_key=True)
    provider_id = Column(String, ForeignKey("providers.provider_id"), nullable=False, index=True)

    # Basic listing information
    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    deadline = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False)  # List of requirements
    application_url = Column(String(500), nullable=False)

    # Metadata for matching
    field_of_study = Column(JSON)  # List of fields
    gpa_requirement = Column(Float)
    citizenship_required = Column(String(50))

    # Performance tracking
    views = Column(Integer, default=0)
    applications = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    provider = relationship("ProviderDB", back_populates="listings")

class CreditBalanceDB(Base):
    """Database model for user credit balances"""
    __tablename__ = "credit_balances"

    user_id = Column(String, primary_key=True)
    balance = Column(Float, nullable=False, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class CreditLedgerDB(Base):
    """Database model for credit transaction ledger"""
    __tablename__ = "credit_ledger"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    delta = Column(Float, nullable=False)  # Positive for credits, negative for debits
    reason = Column(Text)  # For credit operations
    purpose = Column(Text)  # For debit operations
    metadata = Column(JSON)  # Additional context
    created_by_role = Column(String(50), nullable=False, index=True)  # Role of the user who created the transaction
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

class IdempotencyKeyDB(Base):
    """Database model for idempotency tracking"""
    __tablename__ = "idempotency_keys"

    key = Column(String, primary_key=True)  # The idempotency key from the request
    status = Column(String(20), nullable=False, index=True)  # PROCESSING or COMPLETED
    result_id = Column(String)  # Reference to the credit_ledger.id when COMPLETED
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL 24h

def get_database_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)

# Database dependency for FastAPI
def get_db():
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
