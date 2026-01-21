"""
Privacy Policy Enforcement Module

CEO Directive: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1
CCPA/CPRA compliance with DoNotSell enforcement and privacy mode decisions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from server.v2.privacy.age_detector import PrivacyProfile, AgeRange


class PrivacyMode(str, Enum):
    STANDARD = "standard"
    MINOR = "minor"
    DO_NOT_SELL = "do_not_sell"
    GPC_HONORED = "gpc_honored"
    COPPA = "coppa"


@dataclass
class PrivacyPolicy:
    mode: PrivacyMode
    do_not_sell: bool = False
    do_not_track: bool = False
    disable_advertising_pixels: bool = False
    disable_third_party_tracking: bool = False
    disable_behavioral_targeting: bool = False
    disable_location_tracking: bool = False
    disable_cross_site_tracking: bool = False
    restrict_data_retention: bool = False
    data_retention_days: Optional[int] = None
    require_parental_consent: bool = False
    gpc_honored: bool = False
    headers: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "do_not_sell": self.do_not_sell,
            "do_not_track": self.do_not_track,
            "disable_advertising_pixels": self.disable_advertising_pixels,
            "disable_third_party_tracking": self.disable_third_party_tracking,
            "disable_behavioral_targeting": self.disable_behavioral_targeting,
            "disable_location_tracking": self.disable_location_tracking,
            "disable_cross_site_tracking": self.disable_cross_site_tracking,
            "restrict_data_retention": self.restrict_data_retention,
            "data_retention_days": self.data_retention_days,
            "require_parental_consent": self.require_parental_consent,
            "gpc_honored": self.gpc_honored,
        }
    
    def get_response_headers(self) -> dict:
        headers = {}
        
        headers["X-Privacy-Mode"] = self.mode.value
        
        if self.do_not_sell:
            headers["X-Do-Not-Sell"] = "true"
        
        if self.do_not_track or self.disable_third_party_tracking:
            headers["X-Tracking-Disabled"] = "true"
        
        if self.gpc_honored:
            headers["X-GPC-Honored"] = "true"
        
        if self.require_parental_consent:
            headers["X-Parental-Consent-Required"] = "true"
        
        if self.disable_advertising_pixels:
            headers["X-Ads-Disabled"] = "true"
        
        headers.update(self.headers)
        
        return headers


def get_privacy_policy(
    privacy_profile: Optional[PrivacyProfile] = None,
    gpc_enabled: bool = False,
    dnt_enabled: bool = False,
    user_do_not_sell_preference: bool = False,
) -> PrivacyPolicy:
    is_minor = privacy_profile.is_minor if privacy_profile else False
    age_range = privacy_profile.age_range if privacy_profile else AgeRange.UNKNOWN
    requires_parental_consent = (
        privacy_profile.requires_parental_consent if privacy_profile else False
    )
    
    do_not_sell = (
        is_minor
        or gpc_enabled
        or user_do_not_sell_preference
        or (privacy_profile and privacy_profile.do_not_sell)
    )
    
    if requires_parental_consent or age_range == AgeRange.UNDER_13:
        return PrivacyPolicy(
            mode=PrivacyMode.COPPA,
            do_not_sell=True,
            do_not_track=True,
            disable_advertising_pixels=True,
            disable_third_party_tracking=True,
            disable_behavioral_targeting=True,
            disable_location_tracking=True,
            disable_cross_site_tracking=True,
            restrict_data_retention=True,
            data_retention_days=90,
            require_parental_consent=True,
            gpc_honored=gpc_enabled,
        )
    
    if is_minor:
        return PrivacyPolicy(
            mode=PrivacyMode.MINOR,
            do_not_sell=True,
            do_not_track=True,
            disable_advertising_pixels=True,
            disable_third_party_tracking=True,
            disable_behavioral_targeting=True,
            disable_location_tracking=True,
            disable_cross_site_tracking=True,
            restrict_data_retention=True,
            data_retention_days=90,
            require_parental_consent=False,
            gpc_honored=gpc_enabled,
        )
    
    if gpc_enabled:
        return PrivacyPolicy(
            mode=PrivacyMode.GPC_HONORED,
            do_not_sell=True,
            do_not_track=True,
            disable_advertising_pixels=False,
            disable_third_party_tracking=True,
            disable_behavioral_targeting=True,
            disable_location_tracking=False,
            disable_cross_site_tracking=True,
            restrict_data_retention=False,
            gpc_honored=True,
        )
    
    if user_do_not_sell_preference:
        return PrivacyPolicy(
            mode=PrivacyMode.DO_NOT_SELL,
            do_not_sell=True,
            do_not_track=dnt_enabled,
            disable_advertising_pixels=False,
            disable_third_party_tracking=True,
            disable_behavioral_targeting=True,
            disable_location_tracking=False,
            disable_cross_site_tracking=True,
            restrict_data_retention=False,
            gpc_honored=False,
        )
    
    return PrivacyPolicy(
        mode=PrivacyMode.STANDARD,
        do_not_sell=False,
        do_not_track=dnt_enabled,
        disable_advertising_pixels=False,
        disable_third_party_tracking=False,
        disable_behavioral_targeting=False,
        disable_location_tracking=False,
        disable_cross_site_tracking=False,
        restrict_data_retention=False,
        gpc_honored=False,
    )


def check_gpc_header(headers: dict) -> bool:
    return headers.get("sec-gpc") == "1" or headers.get("Sec-GPC") == "1"


def check_dnt_header(headers: dict) -> bool:
    return headers.get("dnt") == "1" or headers.get("DNT") == "1"
