"""
Age Detection Module for Privacy-by-Default Enforcement

CEO Directive: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1
Detects user minor status (<18) from multiple sources.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
import re


class DetectionMethod(str, Enum):
    DOB = "dob"
    SCHOOL_GRADE = "school_grade"
    DOCUMENT_EXTRACTION = "document_extraction"
    USER_ATTESTATION = "user_attestation"
    JWT_CLAIMS = "jwt_claims"
    SESSION = "session"
    UNKNOWN = "unknown"


class AgeRange(str, Enum):
    UNDER_13 = "under_13"
    TEEN_13_15 = "teen_13_15"
    TEEN_16_17 = "teen_16_17"
    ADULT = "adult"
    UNKNOWN = "unknown"


@dataclass
class PrivacyProfile:
    is_minor: bool
    age_range: AgeRange
    detection_method: DetectionMethod
    exact_age: Optional[int] = None
    requires_parental_consent: bool = False
    do_not_sell: bool = False
    
    def to_dict(self) -> dict:
        return {
            "is_minor": self.is_minor,
            "age_range": self.age_range.value,
            "detection_method": self.detection_method.value,
            "exact_age": self.exact_age,
            "requires_parental_consent": self.requires_parental_consent,
            "do_not_sell": self.do_not_sell,
        }


GRADE_TO_AGE_MAP = {
    "kindergarten": 5,
    "k": 5,
    "1": 6, "1st": 6, "first": 6, "grade 1": 6,
    "2": 7, "2nd": 7, "second": 7, "grade 2": 7,
    "3": 8, "3rd": 8, "third": 8, "grade 3": 8,
    "4": 9, "4th": 9, "fourth": 9, "grade 4": 9,
    "5": 10, "5th": 10, "fifth": 10, "grade 5": 10,
    "6": 11, "6th": 11, "sixth": 11, "grade 6": 11,
    "7": 12, "7th": 12, "seventh": 12, "grade 7": 12,
    "8": 13, "8th": 13, "eighth": 13, "grade 8": 13,
    "9": 14, "9th": 14, "ninth": 14, "grade 9": 14, "freshman": 14,
    "10": 15, "10th": 15, "tenth": 15, "grade 10": 15, "sophomore": 15,
    "11": 16, "11th": 16, "eleventh": 16, "grade 11": 16, "junior": 16,
    "12": 17, "12th": 17, "twelfth": 17, "grade 12": 17, "senior": 17,
}

HIGH_SCHOOL_KEYWORDS = [
    "high school", "highschool", "secondary", "9th", "10th", "11th", "12th",
    "freshman", "sophomore", "junior", "senior", "grade 9", "grade 10",
    "grade 11", "grade 12"
]

MIDDLE_SCHOOL_KEYWORDS = [
    "middle school", "junior high", "6th", "7th", "8th", "grade 6", "grade 7", "grade 8"
]

ELEMENTARY_SCHOOL_KEYWORDS = [
    "elementary", "primary school", "grade school", "1st", "2nd", "3rd", "4th", "5th",
    "kindergarten"
]


class AgeDetector:
    def __init__(self):
        self.current_date = date.today()
    
    def detect(
        self,
        dob: Optional[date | str] = None,
        school_level: Optional[str] = None,
        grade: Optional[str] = None,
        document_data: Optional[dict] = None,
        jwt_claims: Optional[dict] = None,
        session_data: Optional[dict] = None,
        user_attestation_age: Optional[int] = None,
    ) -> PrivacyProfile:
        if dob:
            return self.from_dob(dob)
        
        if jwt_claims:
            profile = self.from_jwt_claims(jwt_claims)
            if profile:
                return profile
        
        if session_data:
            profile = self.from_session(session_data)
            if profile:
                return profile
        
        if school_level or grade:
            return self.from_school_grade(school_level, grade)
        
        if document_data:
            profile = self.from_document_extraction(document_data)
            if profile:
                return profile
        
        if user_attestation_age is not None:
            return self.from_user_attestation(user_attestation_age)
        
        return PrivacyProfile(
            is_minor=False,
            age_range=AgeRange.UNKNOWN,
            detection_method=DetectionMethod.UNKNOWN,
            do_not_sell=False,
        )
    
    def from_dob(self, dob: date | str) -> PrivacyProfile:
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                try:
                    dob = datetime.fromisoformat(dob.replace("Z", "+00:00")).date()
                except ValueError:
                    return self._unknown_profile()
        
        age = self.calculate_age(dob)
        return self._build_profile(age, DetectionMethod.DOB)
    
    def from_school_grade(
        self, school_level: Optional[str] = None, grade: Optional[str] = None
    ) -> PrivacyProfile:
        estimated_age: Optional[int] = None
        
        if grade:
            grade_lower = grade.lower().strip()
            estimated_age = GRADE_TO_AGE_MAP.get(grade_lower)
        
        if estimated_age is None and school_level:
            school_lower = school_level.lower()
            
            if any(kw in school_lower for kw in HIGH_SCHOOL_KEYWORDS):
                estimated_age = 16
            elif any(kw in school_lower for kw in MIDDLE_SCHOOL_KEYWORDS):
                estimated_age = 13
            elif any(kw in school_lower for kw in ELEMENTARY_SCHOOL_KEYWORDS):
                estimated_age = 10
        
        if estimated_age is not None:
            return self._build_profile(estimated_age, DetectionMethod.SCHOOL_GRADE)
        
        return PrivacyProfile(
            is_minor=True,
            age_range=AgeRange.UNKNOWN,
            detection_method=DetectionMethod.SCHOOL_GRADE,
            do_not_sell=True,
        )
    
    def from_document_extraction(self, document_data: dict) -> Optional[PrivacyProfile]:
        if not document_data:
            return None
        
        dob = document_data.get("date_of_birth") or document_data.get("dob")
        if dob:
            profile = self.from_dob(dob)
            profile.detection_method = DetectionMethod.DOCUMENT_EXTRACTION
            return profile
        
        age = document_data.get("age")
        if age is not None:
            try:
                age = int(age)
                return self._build_profile(age, DetectionMethod.DOCUMENT_EXTRACTION)
            except (ValueError, TypeError):
                pass
        
        grade = document_data.get("grade") or document_data.get("grade_level")
        school = document_data.get("school") or document_data.get("school_name", "")
        
        if grade or school:
            profile = self.from_school_grade(school, grade)
            profile.detection_method = DetectionMethod.DOCUMENT_EXTRACTION
            return profile
        
        return None
    
    def from_jwt_claims(self, claims: dict) -> Optional[PrivacyProfile]:
        if not claims:
            return None
        
        dob = claims.get("birthdate") or claims.get("dob") or claims.get("date_of_birth")
        if dob:
            profile = self.from_dob(dob)
            profile.detection_method = DetectionMethod.JWT_CLAIMS
            return profile
        
        age = claims.get("age")
        if age is not None:
            try:
                age = int(age)
                return self._build_profile(age, DetectionMethod.JWT_CLAIMS)
            except (ValueError, TypeError):
                pass
        
        is_minor = claims.get("is_minor")
        if is_minor is True:
            return PrivacyProfile(
                is_minor=True,
                age_range=AgeRange.UNKNOWN,
                detection_method=DetectionMethod.JWT_CLAIMS,
                do_not_sell=True,
            )
        
        return None
    
    def from_session(self, session_data: dict) -> Optional[PrivacyProfile]:
        if not session_data:
            return None
        
        is_minor = session_data.get("is_minor")
        if is_minor is True:
            age_range_str = session_data.get("age_range", "unknown")
            try:
                age_range = AgeRange(age_range_str)
            except ValueError:
                age_range = AgeRange.UNKNOWN
            
            return PrivacyProfile(
                is_minor=True,
                age_range=age_range,
                detection_method=DetectionMethod.SESSION,
                exact_age=session_data.get("age"),
                requires_parental_consent=age_range == AgeRange.UNDER_13,
                do_not_sell=True,
            )
        
        dob = session_data.get("dob") or session_data.get("date_of_birth")
        if dob:
            profile = self.from_dob(dob)
            profile.detection_method = DetectionMethod.SESSION
            return profile
        
        return None
    
    def from_user_attestation(self, age: int) -> PrivacyProfile:
        return self._build_profile(age, DetectionMethod.USER_ATTESTATION)
    
    def calculate_age(self, dob: date) -> int:
        today = self.current_date
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age
    
    def _build_profile(self, age: int, method: DetectionMethod) -> PrivacyProfile:
        if age < 13:
            age_range = AgeRange.UNDER_13
            requires_consent = True
        elif age < 16:
            age_range = AgeRange.TEEN_13_15
            requires_consent = False
        elif age < 18:
            age_range = AgeRange.TEEN_16_17
            requires_consent = False
        else:
            age_range = AgeRange.ADULT
            requires_consent = False
        
        is_minor = age < 18
        
        return PrivacyProfile(
            is_minor=is_minor,
            age_range=age_range,
            detection_method=method,
            exact_age=age,
            requires_parental_consent=requires_consent,
            do_not_sell=is_minor,
        )
    
    def _unknown_profile(self) -> PrivacyProfile:
        return PrivacyProfile(
            is_minor=False,
            age_range=AgeRange.UNKNOWN,
            detection_method=DetectionMethod.UNKNOWN,
            do_not_sell=False,
        )


age_detector = AgeDetector()
