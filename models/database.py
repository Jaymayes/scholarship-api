"""
Database Models and Configuration
SQLAlchemy ORM models for PostgreSQL integration
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime
from typing import Optional
import os

from config.settings import settings

# Database URL from environment or settings
DATABASE_URL = os.getenv("DATABASE_URL") or settings.database_url

# Create database engine
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow
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