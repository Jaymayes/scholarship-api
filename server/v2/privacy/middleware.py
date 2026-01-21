"""
Privacy Enforcement Middleware for FastAPI

CEO Directive: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1
Detects user age and enforces privacy-by-default policies.
"""

from typing import Optional
import logging

from fastapi import Depends, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from server.v2.privacy.age_detector import AgeDetector, PrivacyProfile, age_detector
from server.v2.privacy.policy import (
    PrivacyMode,
    PrivacyPolicy,
    check_dnt_header,
    check_gpc_header,
    get_privacy_policy,
)


logger = logging.getLogger(__name__)


class PrivacyEnforcementMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, detector: Optional[AgeDetector] = None):
        super().__init__(app)
        self.detector = detector or age_detector
    
    async def dispatch(self, request: Request, call_next) -> Response:
        gpc_enabled = check_gpc_header(dict(request.headers))
        dnt_enabled = check_dnt_header(dict(request.headers))
        
        privacy_profile = await self._detect_age(request)
        
        user_do_not_sell = getattr(request.state, "do_not_sell", False)
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "do_not_sell"):
                user_do_not_sell = user.do_not_sell
        
        policy = get_privacy_policy(
            privacy_profile=privacy_profile,
            gpc_enabled=gpc_enabled,
            dnt_enabled=dnt_enabled,
            user_do_not_sell_preference=user_do_not_sell,
        )
        
        request.state.privacy_profile = privacy_profile
        request.state.privacy_policy = policy
        request.state.is_minor = privacy_profile.is_minor if privacy_profile else False
        request.state.do_not_sell = policy.do_not_sell
        request.state.gpc_honored = gpc_enabled
        
        if privacy_profile:
            logger.debug(
                f"Privacy detection: is_minor={privacy_profile.is_minor}, "
                f"method={privacy_profile.detection_method.value}, "
                f"age_range={privacy_profile.age_range.value}"
            )
        
        response = await call_next(request)
        
        privacy_headers = policy.get_response_headers()
        for header_name, header_value in privacy_headers.items():
            response.headers[header_name] = header_value
        
        if policy.mode == PrivacyMode.MINOR or policy.mode == PrivacyMode.COPPA:
            existing_csp = response.headers.get("Content-Security-Policy", "")
            if not existing_csp or "connect-src" not in existing_csp:
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "connect-src 'self'; "
                    "img-src 'self' data:; "
                    "style-src 'self' 'unsafe-inline'; "
                    "frame-ancestors 'self'"
                )
        
        return response
    
    async def _detect_age(self, request: Request) -> Optional[PrivacyProfile]:
        jwt_claims = None
        if hasattr(request.state, "jwt_claims"):
            jwt_claims = request.state.jwt_claims
        elif hasattr(request.state, "token_data"):
            jwt_claims = request.state.token_data
        elif hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "claims"):
                jwt_claims = user.claims
        
        session_data = None
        if hasattr(request.state, "session"):
            session_data = request.state.session
        
        if hasattr(request.state, "is_minor") and request.state.is_minor:
            from server.v2.privacy.age_detector import AgeRange, DetectionMethod
            return PrivacyProfile(
                is_minor=True,
                age_range=getattr(request.state, "age_range", AgeRange.UNKNOWN),
                detection_method=DetectionMethod.SESSION,
                do_not_sell=True,
            )
        
        explicit_dob = None
        explicit_age = None
        school_level = None
        grade = None
        
        if hasattr(request, "query_params"):
            explicit_dob = request.query_params.get("dob")
            explicit_age = request.query_params.get("age")
            school_level = request.query_params.get("school_level")
            grade = request.query_params.get("grade")
        
        privacy_context = request.headers.get("X-Privacy-Context", "")
        if "minor=true" in privacy_context.lower():
            from server.v2.privacy.age_detector import AgeRange, DetectionMethod
            return PrivacyProfile(
                is_minor=True,
                age_range=AgeRange.UNKNOWN,
                detection_method=DetectionMethod.SESSION,
                do_not_sell=True,
            )
        
        if not any([jwt_claims, session_data, explicit_dob, explicit_age, school_level, grade]):
            return None
        
        user_attestation_age = None
        if explicit_age:
            try:
                user_attestation_age = int(explicit_age)
            except ValueError:
                pass
        
        profile = self.detector.detect(
            dob=explicit_dob,
            school_level=school_level,
            grade=grade,
            jwt_claims=jwt_claims,
            session_data=session_data,
            user_attestation_age=user_attestation_age,
        )
        
        return profile


class PrivacyContext:
    def __init__(
        self,
        privacy_profile: Optional[PrivacyProfile] = None,
        privacy_policy: Optional[PrivacyPolicy] = None,
        is_minor: bool = False,
        do_not_sell: bool = False,
        gpc_honored: bool = False,
    ):
        self.privacy_profile = privacy_profile
        self.privacy_policy = privacy_policy
        self.is_minor = is_minor
        self.do_not_sell = do_not_sell
        self.gpc_honored = gpc_honored
    
    def can_track(self) -> bool:
        if self.privacy_policy:
            return not self.privacy_policy.disable_third_party_tracking
        return not self.is_minor and not self.do_not_sell
    
    def can_show_ads(self) -> bool:
        if self.privacy_policy:
            return not self.privacy_policy.disable_advertising_pixels
        return not self.is_minor
    
    def can_sell_data(self) -> bool:
        return not self.do_not_sell and not self.is_minor
    
    def can_use_behavioral_targeting(self) -> bool:
        if self.privacy_policy:
            return not self.privacy_policy.disable_behavioral_targeting
        return not self.is_minor and not self.gpc_honored
    
    def can_use_location(self) -> bool:
        if self.privacy_policy:
            return not self.privacy_policy.disable_location_tracking
        return not self.is_minor


async def get_privacy_context(request: Request) -> PrivacyContext:
    privacy_profile = getattr(request.state, "privacy_profile", None)
    privacy_policy = getattr(request.state, "privacy_policy", None)
    is_minor = getattr(request.state, "is_minor", False)
    do_not_sell = getattr(request.state, "do_not_sell", False)
    gpc_honored = getattr(request.state, "gpc_honored", False)
    
    return PrivacyContext(
        privacy_profile=privacy_profile,
        privacy_policy=privacy_policy,
        is_minor=is_minor,
        do_not_sell=do_not_sell,
        gpc_honored=gpc_honored,
    )


def require_adult(context: PrivacyContext = Depends(get_privacy_context)):
    from fastapi import HTTPException
    
    if context.is_minor:
        raise HTTPException(
            status_code=403,
            detail="This feature is not available for users under 18",
        )
    return context


def require_no_gpc(context: PrivacyContext = Depends(get_privacy_context)):
    from fastapi import HTTPException
    
    if context.gpc_honored:
        raise HTTPException(
            status_code=403,
            detail="This feature is not available when Global Privacy Control is enabled",
        )
    return context
