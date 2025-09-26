"""
Interaction Model for Analytics and User Behavior Tracking
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from models.database import Base


class InteractionDB(Base):
    """Database model for user interactions and API analytics"""
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)  # root_view, list_scholarships, view_scholarship, search_scholarships
    user_id = Column(String(100), nullable=True, index=True)
    scholarship_id = Column(String(100), nullable=True, index=True)
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    status = Column(Integer, nullable=False)
    trace_id = Column(String(100), nullable=True, index=True)
    request_metadata = Column(JSON, nullable=True)  # Query params, search filters, etc.
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)

    # Indexes for performance
    __table_args__ = (
        Index('ix_interactions_event_created', 'event_type', 'created_at'),
        Index('ix_interactions_scholarship_created', 'scholarship_id', 'created_at'),
        Index('ix_interactions_user_created', 'user_id', 'created_at'),
    )
