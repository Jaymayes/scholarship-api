"""
FERPA Policy Implementation
Role-based field filtering for FERPA compliance
"""

from enum import Enum
from typing import Any
from functools import wraps

from fastapi import HTTPException, status


class UserRole(str, Enum):
    CONSUMER = "consumer"
    SCHOOL_OFFICIAL = "school_official"
    ADMIN = "admin"
    SYSTEM = "system"


FERPA_PROTECTED_FIELDS = {
    "DataServiceUser": {
        "consumer": ["id", "display_name", "status", "created_at"],
        "school_official": [
            "id", "email", "display_name", "status", "role",
            "is_ferpa_covered", "ferpa_consent_date",
            "profile_data", "preferences",
            "last_login_at", "login_count",
            "created_at", "updated_at"
        ],
        "admin": "*",
        "system": "*",
    },
    "DataServiceUpload": {
        "consumer": ["id", "filename", "mime_type", "size_bytes", "status", "created_at"],
        "school_official": [
            "id", "owner_id", "filename", "mime_type", "size_bytes",
            "is_ferpa_covered", "status", "processed_at",
            "created_at", "updated_at"
        ],
        "admin": "*",
        "system": "*",
    },
    "DataServiceProvider": {
        "consumer": ["id", "name", "segment", "status"],
        "school_official": [
            "id", "name", "segment", "status",
            "institutional_domain", "is_ferpa_covered",
            "dpa_signed", "contract_start_date", "contract_end_date"
        ],
        "admin": "*",
        "system": "*",
    },
    "DataServiceEvent": {
        "consumer": [],
        "school_official": [
            "id", "event_type", "entity_type", "entity_id",
            "action", "is_ferpa_access", "created_at"
        ],
        "admin": "*",
        "system": "*",
    },
}

FERPA_AUDIT_REQUIRED = [
    "profile_data",
    "preferences",
    "email",
    "ferpa_consent_date",
]


class FERPAPolicy:
    """FERPA compliance policy for field-level access control"""

    def __init__(self, role: UserRole, user_id: str | None = None):
        self.role = role
        self.user_id = user_id

    def get_allowed_fields(self, entity_type: str, is_ferpa_covered: bool = False) -> list[str] | str:
        entity_fields = FERPA_PROTECTED_FIELDS.get(entity_type, {})
        allowed = entity_fields.get(self.role.value, [])
        
        if not is_ferpa_covered or self.role in [UserRole.ADMIN, UserRole.SYSTEM]:
            return allowed
        
        if allowed == "*":
            return allowed
        
        return [f for f in allowed if f not in FERPA_AUDIT_REQUIRED] if self.role == UserRole.CONSUMER else allowed

    def can_access_field(self, entity_type: str, field_name: str, is_ferpa_covered: bool = False) -> bool:
        allowed = self.get_allowed_fields(entity_type, is_ferpa_covered)
        
        if allowed == "*":
            return True
        
        return field_name in allowed

    def filter_entity(self, entity_type: str, data: dict[str, Any], is_ferpa_covered: bool = False) -> dict[str, Any]:
        allowed = self.get_allowed_fields(entity_type, is_ferpa_covered)
        
        if allowed == "*":
            return data
        
        return {k: v for k, v in data.items() if k in allowed}

    def requires_audit(self, field_name: str) -> bool:
        return field_name in FERPA_AUDIT_REQUIRED

    def can_access_ferpa_data(self) -> bool:
        return self.role in [UserRole.SCHOOL_OFFICIAL, UserRole.ADMIN, UserRole.SYSTEM]


def get_ferpa_policy(role: str, user_id: str | None = None) -> FERPAPolicy:
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.CONSUMER
    return FERPAPolicy(role=user_role, user_id=user_id)


def filter_ferpa_fields(
    entity_type: str,
    data: dict[str, Any] | list[dict[str, Any]],
    role: str,
    is_ferpa_covered: bool = False
) -> dict[str, Any] | list[dict[str, Any]]:
    policy = get_ferpa_policy(role)
    
    if isinstance(data, list):
        return [policy.filter_entity(entity_type, item, is_ferpa_covered) for item in data]
    
    return policy.filter_entity(entity_type, data, is_ferpa_covered)


def check_ferpa_access(role: str) -> bool:
    policy = get_ferpa_policy(role)
    return policy.can_access_ferpa_data()


def require_ferpa_access(func):
    """Decorator to require FERPA access for a route handler"""
    @wraps(func)
    async def wrapper(*args, role: str = "consumer", **kwargs):
        if not check_ferpa_access(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FERPA access required for this operation"
            )
        return await func(*args, role=role, **kwargs)
    return wrapper
