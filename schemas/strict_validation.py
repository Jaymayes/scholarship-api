"""
Strict input validation schemas to prevent gaps and ensure robustness
Addresses QA findings about input validation vulnerabilities
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseModel(BaseModel):
    """Base model with strict validation - no extra fields allowed"""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StrictInteractionRequest(StrictBaseModel):
    """Strict validation for interaction logging requests"""
    type: str = Field(..., min_length=1, max_length=50, pattern="^[a-z_]+$")
    scholarship_id: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    metadata: dict[str, Any] | None = Field(default=None)

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
    query: str | None = Field(None, max_length=1000)
    fields_of_study: list[str] = Field(default_factory=list, max_items=20)
    min_amount: float | None = Field(None, ge=0, le=1000000)
    max_amount: float | None = Field(None, ge=0, le=1000000)
    scholarship_types: list[str] = Field(default_factory=list, max_items=10)
    states: list[str] = Field(default_factory=list, max_items=60)  # All US states + territories
    min_gpa: float | None = Field(None, ge=0.0, le=4.0)
    citizenship: str | None = Field(None, max_length=100)
    deadline_after: str | None = Field(None)
    deadline_before: str | None = Field(None)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0, le=10000)
    topics: list[str] = Field(default_factory=list, max_items=50, description="SEO topics filter - Phase 6 hotfix")

    @field_validator('topics', mode='before')
    @classmethod
    def validate_topics(cls, v: list | None) -> list:
        """Validate topics array - Phase 6 SEO Schema hotfix to prevent crashes"""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("topics must be an array of strings")
        result = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"topics array must contain only strings, got {type(item).__name__}")
            if len(item) > 200:
                raise ValueError(f"topic string too long (max 200 chars): {item[:50]}...")
            result.append(item.strip())
        return result

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str | None) -> str | None:
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
    gpa: float | None = Field(None, ge=0.0, le=4.0)
    grade_level: str | None = Field(None, max_length=50)
    field_of_study: str | None = Field(None, max_length=100)
    citizenship: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=50)
    financial_need: bool | None = Field(None)

    @field_validator('grade_level')
    @classmethod
    def validate_grade_level(cls, v: str | None) -> str | None:
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
    check_type: str | None = Field("basic", max_length=50)
    include_details: bool = Field(False)

    @field_validator('check_type')
    @classmethod
    def validate_check_type(cls, v: str) -> str:
        """Validate health check type"""
        allowed_types = {'basic', 'detailed', 'minimal'}
        if v not in allowed_types:
            raise ValueError(f"Invalid check type: {v}. Must be one of: {allowed_types}")
        return v
