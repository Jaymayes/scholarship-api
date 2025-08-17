from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FieldOfStudy(str, Enum):
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    BUSINESS = "business"
    ARTS = "arts"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    EDUCATION = "education"
    LAW = "law"
    SOCIAL_SCIENCES = "social_sciences"
    OTHER = "other"

class ScholarshipType(str, Enum):
    MERIT_BASED = "merit_based"
    NEED_BASED = "need_based"
    ATHLETIC = "athletic"
    MINORITY = "minority"
    ACADEMIC_ACHIEVEMENT = "academic_achievement"
    COMMUNITY_SERVICE = "community_service"

class EligibilityCriteria(BaseModel):
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Minimum GPA required")
    max_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Maximum GPA allowed")
    grade_levels: List[str] = Field(default=[], description="Eligible grade levels")
    citizenship_required: Optional[str] = Field(None, description="Required citizenship")
    residency_states: List[str] = Field(default=[], description="Eligible US states")
    fields_of_study: List[FieldOfStudy] = Field(default=[], description="Eligible fields of study")
    min_age: Optional[int] = Field(None, ge=0, description="Minimum age requirement")
    max_age: Optional[int] = Field(None, ge=0, description="Maximum age requirement")
    financial_need: Optional[bool] = Field(None, description="Financial need requirement")
    essay_required: bool = Field(False, description="Whether essay is required")
    recommendation_letters: int = Field(0, description="Number of recommendation letters required")
    
    @validator('max_gpa')
    def validate_gpa_range(cls, v, values):
        if v is not None and 'min_gpa' in values and values['min_gpa'] is not None:
            if v < values['min_gpa']:
                raise ValueError('max_gpa must be greater than or equal to min_gpa')
        return v

class Scholarship(BaseModel):
    id: str = Field(..., description="Unique scholarship identifier")
    name: str = Field(..., description="Scholarship name")
    organization: str = Field(..., description="Sponsoring organization")
    description: str = Field(..., description="Detailed scholarship description")
    amount: float = Field(..., ge=0, description="Scholarship amount in USD")
    max_awards: int = Field(..., ge=1, description="Maximum number of awards available")
    application_deadline: datetime = Field(..., description="Application deadline")
    notification_date: Optional[datetime] = Field(None, description="Winners notification date")
    scholarship_type: ScholarshipType = Field(..., description="Type of scholarship")
    eligibility_criteria: EligibilityCriteria = Field(..., description="Eligibility requirements")
    application_url: str = Field(..., description="URL to apply for scholarship")
    contact_email: Optional[str] = Field(None, description="Contact email for inquiries")
    website_url: Optional[str] = Field(None, description="Organization website")
    renewable: bool = Field(False, description="Whether scholarship is renewable")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class ScholarshipSummary(BaseModel):
    """Simplified scholarship model for search results"""
    id: str
    name: str
    organization: str
    amount: float
    application_deadline: datetime
    scholarship_type: ScholarshipType
    description: str = Field(..., max_length=200)

class SearchFilters(BaseModel):
    """Search and filter criteria"""
    keyword: Optional[str] = Field(None, description="Search keyword")
    fields_of_study: List[FieldOfStudy] = Field(default=[], description="Filter by fields of study")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum scholarship amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum scholarship amount")
    scholarship_types: List[ScholarshipType] = Field(default=[], description="Filter by scholarship types")
    states: List[str] = Field(default=[], description="Filter by US states")
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Minimum GPA filter")
    citizenship: Optional[str] = Field(None, description="Citizenship requirement")
    deadline_after: Optional[datetime] = Field(None, description="Deadlines after this date")
    deadline_before: Optional[datetime] = Field(None, description="Deadlines before this date")
    limit: int = Field(20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")

class SearchResponse(BaseModel):
    """Search results response"""
    scholarships: List[ScholarshipSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
