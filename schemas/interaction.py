"""
Pydantic models for interaction wrapper endpoints - QA-003 fix
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

class InteractionType(str, Enum):
    """Valid interaction types"""
    VIEW = "view"
    SAVE = "save" 
    APPLY = "apply"
    DISMISS = "dismiss"
    SEARCH = "search"
    FILTER = "filter"

class InteractionRequest(BaseModel):
    """Request model for interaction logging"""
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields - security requirement
    
    event_type: InteractionType = Field(
        ..., 
        description="Type of interaction event"
    )
    scholarship_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Scholarship identifier"
    )
    user_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="User identifier"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional interaction metadata"
    )
    search_query: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Search query for search interactions"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Applied filters for filter interactions"
    )
    
    @field_validator("metadata", "filters")
    @classmethod
    def validate_metadata_size(cls, v):
        """Ensure metadata doesn't exceed reasonable size"""
        if v and len(str(v)) > 10000:  # 10KB limit
            raise ValueError("Metadata size too large")
        return v

class BulkInteractionRequest(BaseModel):
    """Request model for bulk interaction logging"""
    model_config = ConfigDict(extra="forbid")
    
    interactions: List[InteractionRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of interactions to log"
    )
    
    @field_validator("interactions")
    @classmethod
    def validate_interactions_list(cls, v):
        """Validate interaction list"""
        if len(v) > 100:
            raise ValueError("Cannot log more than 100 interactions at once")
        return v

class InteractionResponse(BaseModel):
    """Response model for interaction logging"""
    success: bool = Field(description="Whether interaction was logged successfully")
    interaction_id: Optional[str] = Field(None, description="Generated interaction ID")
    message: str = Field(description="Result message")