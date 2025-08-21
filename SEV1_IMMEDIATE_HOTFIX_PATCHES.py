#!/usr/bin/env python3
"""
SEV-1 SECURITY INCIDENT - IMMEDIATE HOTFIX PATCHES
Critical patches to address JWT bypass and SQL injection vulnerabilities
"""

# PATCH 1: JWT VALIDATION ENFORCEMENT
# File: routers/scholarships.py
# Problem: Lines 43-44 bypass JWT validation when PUBLIC_READ_ENDPOINTS is enabled
PATCH_1_LOCATION = "routers/scholarships.py:42-44"
PATCH_1_VULNERABLE_CODE = """
    # QA-004 fix: Require authentication unless PUBLIC_READ_ENDPOINTS is enabled
    current_user: Optional[dict] = Depends(get_current_user) if not settings.public_read_endpoints else None
"""

PATCH_1_SECURE_CODE = """
    # SECURITY FIX: Always require authentication - remove feature flag bypass
    current_user: dict = Depends(require_auth(min_role="user"))
"""

# PATCH 2: JWT DECODE VALIDATION
# File: middleware/auth.py  
# Problem: Lines 129-162 accept invalid JWT tokens without proper validation
PATCH_2_LOCATION = "middleware/auth.py:129-162"
PATCH_2_VULNERABLE_CODE = """
def decode_token(token: str) -> Optional[TokenData]:
    \"\"\"Decode and validate a JWT token with rotation support\"\"\"
    if not token or not isinstance(token, str):
        return None
        
    # Try current key first
    keys_to_try = [get_jwt_secret_key()] + get_jwt_previous_keys()
    
    for secret_key in keys_to_try:
        if not secret_key:  # Skip empty keys
            continue
            
        try:
            payload = jwt.decode(token, secret_key, algorithms=[get_jwt_algorithm()])
            # ... rest of decode logic
        except (JWTError, ValueError, KeyError):
            continue
    
    return None
"""

PATCH_2_SECURE_CODE = """
def decode_token(token: str) -> Optional[TokenData]:
    \"\"\"Decode and validate a JWT token with strict security\"\"\"
    if not token or not isinstance(token, str) or len(token.strip()) == 0:
        return None
        
    # Security: Reject tokens with 'none' algorithm
    try:
        header = jwt.get_unverified_header(token)
        if header.get('alg', '').lower() in ['none', 'null', '']:
            return None
    except Exception:
        return None
        
    # Security: Ensure token has proper structure (header.payload.signature)
    token_parts = token.split('.')
    if len(token_parts) != 3 or not all(part.strip() for part in token_parts):
        return None
        
    # Try current key first with strict validation
    keys_to_try = [get_jwt_secret_key()] + get_jwt_previous_keys()
    
    for secret_key in keys_to_try:
        if not secret_key or len(secret_key.strip()) < 32:  # Minimum key length
            continue
            
        try:
            # SECURITY: Pin algorithm, require exp/iat/nbf validation
            payload = jwt.decode(
                token, 
                secret_key, 
                algorithms=[get_jwt_algorithm()],
                options={
                    "require_exp": True,
                    "require_iat": True, 
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_signature": True
                },
                leeway=10  # Max 10 seconds clock skew
            )
            
            # Extract and validate required fields with strict type checking
            user_id = payload.get("sub")
            if not user_id or not isinstance(user_id, str) or len(user_id.strip()) == 0:
                continue
                
            # Security: Validate issuer and audience if configured  
            if hasattr(settings, 'jwt_issuer') and settings.jwt_issuer:
                if payload.get("iss") != settings.jwt_issuer:
                    continue
            if hasattr(settings, 'jwt_audience') and settings.jwt_audience:
                if payload.get("aud") != settings.jwt_audience:
                    continue
                
            roles = payload.get("roles", [])
            scopes = payload.get("scopes", [])
            
            # Ensure roles and scopes are lists of strings
            if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
                roles = []
            if not isinstance(scopes, list) or not all(isinstance(s, str) for s in scopes):
                scopes = []
                
            return TokenData(user_id=user_id, roles=roles, scopes=scopes)
        except (JWTError, ValueError, KeyError, TypeError) as e:
            # Log security events for monitoring
            import logging
            logging.warning(f"JWT validation failed: {type(e).__name__}")
            continue
    
    return None
"""

# PATCH 3: SQL INJECTION PREVENTION
# File: services/eligibility_service.py or wherever field_of_study parameter is processed
PATCH_3_LOCATION = "Query parameter processing - field_of_study input"
PATCH_3_VULNERABLE_CODE = """
# Any direct string interpolation into SQL queries like:
# query = f"SELECT * FROM table WHERE field = '{user_input}'"
# or similar string concatenation
"""

PATCH_3_SECURE_CODE = """
# SECURITY: Use parameterized queries only
from enum import Enum

class FieldOfStudyEnum(str, Enum):
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

def validate_field_of_study(field: str) -> Optional[str]:
    \"\"\"Strict whitelist validation for field_of_study parameter\"\"\"
    try:
        validated = FieldOfStudyEnum(field.lower().strip())
        return validated.value
    except (ValueError, AttributeError):
        return None

# In endpoint handlers:
def process_eligibility_check(field_of_study: str):
    # SECURITY: Strict input validation
    clean_field = validate_field_of_study(field_of_study)
    if not clean_field:
        raise HTTPException(status_code=400, detail="Invalid field of study")
    
    # Use only parameterized queries - example with SQLAlchemy:
    # result = db.execute(text("SELECT * FROM table WHERE field = :field"), {"field": clean_field})
"""

# PATCH 4: CORS LOCKDOWN
# File: config/settings.py
PATCH_4_LOCATION = "config/settings.py:183-189" 
PATCH_4_VULNERABLE_CODE = """
            # Development/staging: Conservative allowlist instead of wildcard
            dev_origins = [
                "http://localhost:3000", 
                "http://127.0.0.1:3000", 
                "http://localhost:5000",
                "http://localhost:8000",
                "http://localhost:8080"
            ]
"""

PATCH_4_SECURE_CODE = """
            # Development: Minimal allowlist - remove localhost:3000 
            dev_origins = [
                "http://127.0.0.1:5000",  # Only local app server
                "http://localhost:5000"   # Only local app server  
            ]
            # Remove all other localhost ports for security
"""

# WAF RULES FOR IMMEDIATE DEPLOYMENT
WAF_RULES = {
    "sql_injection_block": {
        "rule_type": "managed_rule_set",
        "rule_set": "AWSManagedRulesSQLiRuleSet", 
        "action": "BLOCK",
        "priority": 1
    },
    "auth_header_requirement": {
        "rule_type": "custom",
        "conditions": [
            {
                "field": "uri", 
                "operator": "begins_with",
                "value": "/api/v1/"
            },
            {
                "field": "uri",
                "operator": "not_equals", 
                "value": "/api/v1/health"
            },
            {
                "field": "header",
                "name": "authorization",
                "operator": "not_exists"
            }
        ],
        "action": "BLOCK",
        "priority": 2
    },
    "cors_origin_whitelist": {
        "rule_type": "custom",
        "conditions": [
            {
                "field": "method",
                "operator": "equals",
                "value": "OPTIONS"
            },
            {
                "field": "header",
                "name": "origin", 
                "operator": "not_in",
                "values": ["https://yourdomain.com", "https://app.yourdomain.com"]
            }
        ],
        "action": "BLOCK", 
        "priority": 3
    }
}

# KUBERNETES/DEPLOYMENT PATCHES
DEPLOYMENT_CONFIG_PATCHES = {
    "environment_variables": {
        "PUBLIC_READ_ENDPOINTS": "false",  # CRITICAL: Disable bypass
        "JWT_REQUIRE_SIGNATURE": "true", 
        "JWT_ALGORITHM": "RS256",  # Upgrade from HS256
        "STRICT_CORS": "true",
        "SQL_INJECTION_PROTECTION": "true"
    },
    "health_check_path": "/healthz",  # Not /api/v1/ to avoid auth
    "resource_limits": {
        "memory": "512Mi",
        "cpu": "500m"
    }
}

if __name__ == "__main__":
    print("SEV-1 SECURITY PATCHES - DEPLOYMENT READY")
    print("=" * 50)
    print("Apply these patches immediately:")
    print(f"1. {PATCH_1_LOCATION}")
    print(f"2. {PATCH_2_LOCATION}")  
    print(f"3. {PATCH_3_LOCATION}")
    print(f"4. {PATCH_4_LOCATION}")
    print("\nDeploy WAF rules before code deployment.")
    print("Set environment variables to disable vulnerable features.")