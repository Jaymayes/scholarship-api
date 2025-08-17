from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from models.scholarship import FieldOfStudy

class UserProfile(BaseModel):
    """User profile for eligibility checking"""
    id: Optional[str] = Field(None, description="User identifier")
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Grade Point Average")
    grade_level: Optional[str] = Field(None, description="Current grade level")
    field_of_study: Optional[FieldOfStudy] = Field(None, description="Field of study")
    citizenship: Optional[str] = Field(None, description="Citizenship status")
    state_of_residence: Optional[str] = Field(None, description="State of residence")
    age: Optional[int] = Field(None, ge=0, description="User age")
    financial_need: Optional[bool] = Field(None, description="Has financial need")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EligibilityCheck(BaseModel):
    """Request model for eligibility checking"""
    user_profile: UserProfile
    scholarship_id: str = Field(..., description="Scholarship ID to check eligibility for")

class EligibilityResult(BaseModel):
    """Result of eligibility check"""
    scholarship_id: str
    eligible: bool
    reasons: List[str] = Field(default=[], description="Reasons for eligibility/ineligibility")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Eligibility match score")

class UserInteraction(BaseModel):
    """User interaction tracking"""
    user_id: Optional[str] = Field(None, description="User identifier")
    action: str = Field(..., description="Action performed")
    scholarship_id: Optional[str] = Field(None, description="Related scholarship ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default={}, description="Additional interaction data")

class RecommendationRequest(BaseModel):
    """Request for scholarship recommendations"""
    user_profile: UserProfile
    limit: int = Field(10, ge=1, le=50, description="Number of recommendations")
    include_ineligible: bool = Field(False, description="Include potentially ineligible scholarships")
