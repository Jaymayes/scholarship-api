"""
Strict input validation schemas to prevent gaps and ensure robustness
Addresses QA findings about input validation vulnerabilities
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class StrictBaseModel(BaseModel):
    """Base model with strict validation - no extra fields allowed"""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StrictInteractionRequest(StrictBaseModel):
    """Strict validation for interaction logging requests"""
    type: str = Field(..., min_length=1, max_length=50, pattern="^[a-z_]+$")
    scholarship_id: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator('type')
    @classmethod
    def validate_interaction_type(cls, v: str) -> str:
        """Validate interaction type against allowed values"""
        allowed_types = {'view', 'save', 'apply', 'dismiss', 'share', 'click'}
        if v not in allowed_types:
            raise ValueError(f"Invalid interaction type: {v}. Must be one of: {allowed_types}")
        return v


class StrictSearchRequest(StrictBaseModel):
    """Strict validation for search requests with size limits"""
    query: Optional[str] = Field(None, max_length=1000)
    fields_of_study: List[str] = Field(default_factory=list, max_items=20)
    min_amount: Optional[float] = Field(None, ge=0, le=1000000)
    max_amount: Optional[float] = Field(None, ge=0, le=1000000)
    scholarship_types: List[str] = Field(default_factory=list, max_items=10)
    states: List[str] = Field(default_factory=list, max_items=60)  # All US states + territories
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    citizenship: Optional[str] = Field(None, max_length=100)
    deadline_after: Optional[str] = Field(None)
    deadline_before: Optional[str] = Field(None)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0, le=10000)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: Optional[str]) -> Optional[str]:
        """Validate search query for dangerous content"""
        if v is None:
            return v
        
        # Check for SQL injection patterns
        dangerous_patterns = [
            'drop table', 'delete from', 'update set', 'insert into',
            'alter table', 'truncate', 'create table', '--', ';'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Query contains potentially dangerous content: {pattern}")
        
        return v


class StrictEligibilityRequest(StrictBaseModel):
    """Strict validation for eligibility check requests"""
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    grade_level: Optional[str] = Field(None, max_length=50)
    field_of_study: Optional[str] = Field(None, max_length=100)
    citizenship: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    financial_need: Optional[bool] = Field(None)
    
    @field_validator('grade_level')
    @classmethod
    def validate_grade_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate grade level against allowed values"""
        if v is None:
            return v
        
        allowed_levels = {
            'freshman', 'sophomore', 'junior', 'senior', 
            'graduate', 'postgraduate', 'high_school'
        }
        
        if v.lower() not in allowed_levels:
            raise ValueError(f"Invalid grade level: {v}. Must be one of: {allowed_levels}")
        
        return v


class StrictHealthRequest(StrictBaseModel):
    """Strict validation for health check requests"""
    check_type: Optional[str] = Field("basic", max_length=50)
    include_details: bool = Field(False)
    
    @field_validator('check_type')
    @classmethod
    def validate_check_type(cls, v: str) -> str:
        """Validate health check type"""
        allowed_types = {'basic', 'detailed', 'minimal'}
        if v not in allowed_types:
            raise ValueError(f"Invalid check type: {v}. Must be one of: {allowed_types}")
        return v