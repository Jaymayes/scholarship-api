"""
Privacy-by-Default Enforcement Module

CEO Directive: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1
Provides age detection, privacy policy enforcement, and middleware for COPPA/CCPA compliance.
"""

from server.v2.privacy.age_detector import AgeDetector, PrivacyProfile, AgeRange, DetectionMethod
from server.v2.privacy.policy import PrivacyMode, PrivacyPolicy, get_privacy_policy
from server.v2.privacy.middleware import PrivacyEnforcementMiddleware, get_privacy_context

__all__ = [
    "AgeDetector",
    "PrivacyProfile",
    "AgeRange",
    "DetectionMethod",
    "PrivacyMode",
    "PrivacyPolicy",
    "get_privacy_policy",
    "PrivacyEnforcementMiddleware",
    "get_privacy_context",
]
