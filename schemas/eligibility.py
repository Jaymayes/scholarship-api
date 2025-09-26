"""
Strict eligibility validation schemas
Enhanced input validation with proper constraints and enums
"""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class GradeLevelEnum(str, Enum):
    """Valid grade levels"""
    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    DOCTORAL = "doctoral"
    POST_DOCTORAL = "post_doctoral"

class CitizenshipEnum(str, Enum):
    """Valid citizenship statuses"""
    US = "US"
    PERMANENT_RESIDENT = "permanent_resident"
    INTERNATIONAL = "international"

class FieldOfStudyEnum(str, Enum):
    """Valid fields of study"""
    ENGINEERING = "engineering"
    COMPUTER_SCIENCE = "computer_science"
    BUSINESS = "business"
    MEDICINE = "medicine"
    NURSING = "nursing"
    EDUCATION = "education"
    ARTS = "arts"
    SCIENCES = "sciences"
    MATHEMATICS = "mathematics"
    PSYCHOLOGY = "psychology"
    SOCIAL_WORK = "social_work"
    LAW = "law"
    OTHER = "other"

class StateEnum(str, Enum):
    """Valid US states and territories"""
    AL = "AL"
    AK = "AK"
    AZ = "AZ"
    AR = "AR"
    CA = "CA"
    CO = "CO"
    CT = "CT"
    DE = "DE"
    FL = "FL"
    GA = "GA"
    HI = "HI"
    ID = "ID"
    IL = "IL"
    IN = "IN"
    IA = "IA"
    KS = "KS"
    KY = "KY"
    LA = "LA"
    ME = "ME"
    MD = "MD"
    MA = "MA"
    MI = "MI"
    MN = "MN"
    MS = "MS"
    MO = "MO"
    MT = "MT"
    NE = "NE"
    NV = "NV"
    NH = "NH"
    NJ = "NJ"
    NM = "NM"
    NY = "NY"
    NC = "NC"
    ND = "ND"
    OH = "OH"
    OK = "OK"
    OR = "OR"
    PA = "PA"
    RI = "RI"
    SC = "SC"
    SD = "SD"
    TN = "TN"
    TX = "TX"
    UT = "UT"
    VT = "VT"
    VA = "VA"
    WA = "WA"
    WV = "WV"
    WI = "WI"
    WY = "WY"
    DC = "DC"

class EligibilityCheckRequest(BaseModel):
    """Strict eligibility check request with proper validation"""

    gpa: Annotated[float, Field(ge=0.0, le=4.0)] | None = Field(
        None,
        description="GPA on 4.0 scale (0.0-4.0), or null if not available"
    )

    grade_level: GradeLevelEnum | None = Field(
        None,
        description="Current education level"
    )

    field_of_study: FieldOfStudyEnum | None = Field(
        None,
        description="Primary field of study or intended major"
    )

    citizenship: CitizenshipEnum | None = Field(
        None,
        description="Citizenship or residency status"
    )

    state_of_residence: StateEnum | None = Field(
        None,
        description="US state of legal residence"
    )

    age: int | None = Field(
        None,
        ge=13,
        le=120,
        description="Age in years (13-120)"
    )

    annual_income: float | None = Field(
        None,
        ge=0,
        description="Annual household income in USD"
    )

    financial_need: bool | None = Field(
        None,
        description="Whether applicant demonstrates financial need"
    )

    credits_completed: int | None = Field(
        None,
        ge=0,
        le=300,
        description="Number of academic credits completed (0-300)"
    )

    scholarship_ids: list[str] | None = Field(
        None,
        description="Specific scholarship IDs to check (optional)"
    )

    @model_validator(mode='after')
    def validate_gpa_constraints(self):
        """Ensure GPA constraints are met when provided"""
        if self.gpa is not None and (self.gpa < 0.0 or self.gpa > 4.0):
            raise ValueError('GPA must be between 0.0 and 4.0 when provided')
        return self

    @field_validator('age')
    @classmethod
    def validate_age(cls, v):
        if v is not None and (v < 13 or v > 120):
            raise ValueError('Age must be between 13 and 120')
        return v

    @field_validator('annual_income')
    @classmethod
    def validate_income(cls, v):
        if v is not None and v < 0:
            raise ValueError('Annual income cannot be negative')
        return v

    @field_validator('credits_completed')
    @classmethod
    def validate_credits(cls, v):
        if v is not None and (v < 0 or v > 300):
            raise ValueError('Credits completed must be between 0 and 300')
        return v

    @field_validator('scholarship_ids')
    @classmethod
    def validate_scholarship_ids(cls, v):
        if v is not None:
            if len(v) == 0:
                raise ValueError('scholarship_ids cannot be empty list')
            if len(v) > 50:
                raise ValueError('Maximum 50 scholarship IDs allowed per request')
            for scholarship_id in v:
                if not scholarship_id.strip():
                    raise ValueError('scholarship_ids cannot contain empty strings')
        return v

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "gpa": 3.5,
                "grade_level": "undergraduate",
                "field_of_study": "engineering",
                "citizenship": "US",
                "state_of_residence": "CA",
                "age": 20,
                "annual_income": 50000,
                "financial_need": True,
                "credits_completed": 60
            }
        }
