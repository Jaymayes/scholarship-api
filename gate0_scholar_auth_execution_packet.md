# Gate 0 Execution Packet: scholar_auth
**Service**: scholar_auth  
**DRI**: Auth DRI + SRE  
**Deadline**: Nov 14 10:00 MST  
**Gate**: Gate 0 - Security Foundation  

---

## Executive Summary

Implement OAuth2 client credentials with RS256/JWKS for service-to-service authentication. This is BLOCKING for all other services' auth validation.

**Success Criteria**:
- ✅ RS256 key pair generated and stored securely
- ✅ JWKS endpoint operational at `/.well-known/jwks.json`
- ✅ Service token issuance endpoint functional
- ✅ Token validation reference implementation provided
- ✅ CORS locked to frontend origins only
- ✅ Boot-time validation enforced

---

## I. RS256 Key Pair Generation

### Step 1: Generate Keys (One-Time Setup)

```bash
# Generate private key (4096-bit RSA)
openssl genrsa -out private.pem 4096

# Extract public key
openssl rsa -in private.pem -pubout -out public.pem

# Verify key pair
openssl rsa -in private.pem -check
```

### Step 2: Store in Replit Secrets

**Add to Replit Secrets** (do NOT commit to Git):
```bash
# Copy private key content
cat private.pem | tr '\n' '|'  # Use | as delimiter
# Set as: JWT_PRIVATE_KEY

# Copy public key content
cat public.pem | tr '\n' '|'
# Set as: JWT_PUBLIC_KEY
```

**Add Environment Variables**:
```bash
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ISSUER=https://scholar-auth-jamarrlmayes.replit.app
JWT_AUDIENCE=scholarai-services
SERVICE_NAME=scholar_auth
ENVIRONMENT=production

# Frontend origins for CORS
FRONTEND_ORIGINS=https://student-pilot-jamarrlmayes.replit.app,https://provider-register-jamarrlmayes.replit.app
```

### Step 3: Load Keys in Application

```python
# config/jwt_config.py
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class JWTConfig:
    def __init__(self):
        # Load private key
        private_key_pem = os.getenv("JWT_PRIVATE_KEY", "").replace("|", "\n")
        if not private_key_pem:
            raise RuntimeError("FATAL: JWT_PRIVATE_KEY not configured")
        
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Load public key
        public_key_pem = os.getenv("JWT_PUBLIC_KEY", "").replace("|", "\n")
        if not public_key_pem:
            raise RuntimeError("FATAL: JWT_PUBLIC_KEY not configured")
        
        self.public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        self.algorithm = os.getenv("JWT_ALGORITHM", "RS256")
        self.access_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.refresh_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.issuer = os.getenv("JWT_ISSUER")
        self.audience = os.getenv("JWT_AUDIENCE")

jwt_config = JWTConfig()
```

---

## II. JWKS Endpoint Implementation

### Step 1: Install Dependencies

```bash
pip install python-jose[cryptography] pyjwt cryptography
```

### Step 2: Create JWKS Generator

```python
# services/jwks_service.py
from jose import jwk
from typing import Dict, List
import hashlib
import json

class JWKSService:
    def __init__(self, public_key):
        self.public_key = public_key
        self._jwks_cache = None
    
    def generate_jwks(self) -> Dict[str, List[Dict]]:
        """Generate JWKS from public key"""
        if self._jwks_cache:
            return self._jwks_cache
        
        # Convert public key to JWK format
        public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create key ID (kid) from key hash
        kid = hashlib.sha256(public_key_pem).hexdigest()[:16]
        
        # Generate JWK
        public_jwk = jwk.construct(public_key_pem, algorithm="RS256")
        public_jwk_dict = public_jwk.to_dict()
        public_jwk_dict["kid"] = kid
        public_jwk_dict["use"] = "sig"
        public_jwk_dict["alg"] = "RS256"
        
        self._jwks_cache = {
            "keys": [public_jwk_dict]
        }
        
        return self._jwks_cache

jwks_service = JWKSService(jwt_config.public_key)
```

### Step 3: Create JWKS Endpoint

```python
# routers/well_known.py
from fastapi import APIRouter
from services.jwks_service import jwks_service

router = APIRouter(prefix="/.well-known", tags=["well-known"])

@router.get("/jwks.json")
async def get_jwks():
    """
    JSON Web Key Set endpoint for token verification.
    Consumed by all other services to validate JWTs.
    """
    return jwks_service.generate_jwks()
```

### Step 4: Register Router

```python
# main.py
from routers import well_known

app.include_router(well_known.router)
```

---

## III. Service Token Issuance

### Step 1: Create Service Credentials Store

**For now, use environment variables** (upgrade to database later):

```bash
# In Replit Secrets, add service credentials
SERVICE_CREDENTIALS='{"scholarship_api":"secret1","scholarship_sage":"secret2","scholarship_agent":"secret3","auto_com_center":"secret4","auto_page_maker":"secret5"}'
```

### Step 2: Create Token Service

```python
# services/token_service.py
import jwt
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import secrets
from config.jwt_config import jwt_config

class TokenService:
    def __init__(self):
        # Load service credentials
        creds_json = os.getenv("SERVICE_CREDENTIALS", "{}")
        self.service_credentials = json.loads(creds_json)
    
    def verify_service_credentials(self, client_id: str, client_secret: str) -> bool:
        """Verify service credentials"""
        expected_secret = self.service_credentials.get(client_id)
        if not expected_secret:
            return False
        
        # Constant-time comparison
        return secrets.compare_digest(client_secret, expected_secret)
    
    def issue_service_token(
        self,
        client_id: str,
        scopes: List[str] = None
    ) -> Dict[str, any]:
        """Issue access token for service"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=jwt_config.access_expire_minutes)
        
        # Build claims
        claims = {
            "iss": jwt_config.issuer,
            "aud": jwt_config.audience,
            "sub": f"service:{client_id}",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "roles": ["service"],
            "permissions": scopes or ["api.read", "api.write"],
            "jti": secrets.token_urlsafe(16)
        }
        
        # Sign token
        token = jwt.encode(
            claims,
            jwt_config.private_key,
            algorithm=jwt_config.algorithm
        )
        
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": jwt_config.access_expire_minutes * 60,
            "scope": " ".join(scopes or [])
        }
    
    def issue_user_token(
        self,
        user_id: str,
        email: str,
        roles: List[str],
        permissions: List[str]
    ) -> Dict[str, any]:
        """Issue access token for user"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=jwt_config.access_expire_minutes)
        
        claims = {
            "iss": jwt_config.issuer,
            "aud": "scholarai-web",
            "sub": f"user:{user_id}",
            "email": email,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "roles": roles,
            "permissions": permissions,
            "jti": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(
            claims,
            jwt_config.private_key,
            algorithm=jwt_config.algorithm
        )
        
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": jwt_config.access_expire_minutes * 60
        }

token_service = TokenService()
```

### Step 3: Create Token Issuance Endpoint

```python
# routers/auth.py
from fastapi import APIRouter, HTTPException, Form, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from services.token_service import token_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBasic()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: Optional[str] = None

@router.post("/token/service", response_model=TokenResponse)
async def service_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(default="")
):
    """
    OAuth2 client credentials endpoint for service-to-service auth.
    
    Example:
        POST /auth/token/service
        Content-Type: application/x-www-form-urlencoded
        
        grant_type=client_credentials
        &client_id=scholarship_api
        &client_secret=secret1
        &scope=api.read api.write
    """
    # Validate grant type
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unsupported_grant_type"
        )
    
    # Verify credentials
    if not token_service.verify_service_credentials(client_id, client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_client"
        )
    
    # Parse scopes
    scopes = scope.split() if scope else None
    
    # Issue token
    token_data = token_service.issue_service_token(client_id, scopes)
    
    return TokenResponse(**token_data)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scholar_auth"}
```

---

## IV. CORS Configuration

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Scholar Auth Service")

# CRITICAL: Load from environment, NEVER use wildcards
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "").split(",")

if not FRONTEND_ORIGINS or FRONTEND_ORIGINS == [""]:
    raise RuntimeError("FATAL: FRONTEND_ORIGINS must be configured")

if "*" in FRONTEND_ORIGINS:
    raise RuntimeError("FATAL: Wildcard origins not allowed in production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=3600
)
```

---

## V. Boot-Time Validation

```python
# config/validator.py
import os

class ConfigValidator:
    REQUIRED_VARS = [
        "SERVICE_NAME",
        "ENVIRONMENT",
        "JWT_PRIVATE_KEY",
        "JWT_PUBLIC_KEY",
        "JWT_ALGORITHM",
        "JWT_ISSUER",
        "JWT_AUDIENCE",
        "FRONTEND_ORIGINS",
        "SERVICE_CREDENTIALS"
    ]
    
    @classmethod
    def validate(cls):
        """Validate configuration at startup"""
        missing = [var for var in cls.REQUIRED_VARS if not os.getenv(var)]
        
        if missing:
            raise RuntimeError(
                f"FATAL: Missing required environment variables: {missing}\n"
                f"Configure these in Replit Secrets before starting."
            )
        
        # Validate CORS
        origins = os.getenv("FRONTEND_ORIGINS", "")
        if "*" in origins:
            raise RuntimeError("FATAL: Wildcard CORS origins not allowed")
        
        # Validate JWT algorithm
        if os.getenv("JWT_ALGORITHM") != "RS256":
            raise RuntimeError("FATAL: Only RS256 algorithm supported")
        
        print("✅ scholar_auth configuration validated")

# In main.py startup
@app.on_event("startup")
async def startup_validation():
    ConfigValidator.validate()
```

---

## VI. Testing & Validation

### Test 1: JWKS Endpoint

```bash
# Should return valid JWKS
curl https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json

# Expected response:
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "abc123...",
      "alg": "RS256",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

### Test 2: Service Token Issuance

```bash
# Request service token
curl -X POST https://scholar-auth-jamarrlmayes.replit.app/auth/token/service \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=scholarship_api" \
  -d "client_secret=secret1" \
  -d "scope=api.read api.write"

# Expected response:
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "scope": "api.read api.write"
}
```

### Test 3: Token Validation

```bash
# Decode token at jwt.io and verify:
# - iss: https://scholar-auth-jamarrlmayes.replit.app
# - aud: scholarai-services
# - sub: service:scholarship_api
# - roles: ["service"]
# - permissions: ["api.read", "api.write"]
# - exp: future timestamp
```

### Test 4: CORS Preflight

```bash
# Test CORS from student_pilot origin
curl -X OPTIONS https://scholar-auth-jamarrlmayes.replit.app/auth/token/service \
  -H "Origin: https://student-pilot-jamarrlmayes.replit.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

# Should return:
# Access-Control-Allow-Origin: https://student-pilot-jamarrlmayes.replit.app
# Access-Control-Allow-Methods: POST, GET, ...
# Access-Control-Allow-Headers: Content-Type, ...
```

---

## VII. Integration Guide for Other Services

Provide this to other DRIs:

```python
# Example: How scholarship_api validates tokens

# 1. Install dependencies
# pip install python-jose[cryptography] httpx

# 2. Add to config
JWKS_URL = "https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json"
JWT_ISSUER = "https://scholar-auth-jamarrlmayes.replit.app"
JWT_AUDIENCE = "scholarai-services"

# 3. Create validator (see Integration Standards Blueprint Section III.A.2)

# 4. Add middleware
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        claims = jwt_validator.validate_token(credentials.credentials)
        
        if "service" not in claims.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service role required"
            )
        
        return claims
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

# 5. Protect endpoints
@router.post("/internal/sync")
async def sync_data(claims: dict = Depends(verify_service_token)):
    # Only accessible with valid service token
    pass
```

---

## VIII. Acceptance Criteria

Gate 0 PASSES if:

- [ ] ✅ RS256 keys generated and stored in Replit Secrets
- [ ] ✅ JWKS endpoint returns valid JWK Set
- [ ] ✅ Service token endpoint issues valid JWT
- [ ] ✅ Token contains correct claims (iss, aud, sub, roles, permissions, exp)
- [ ] ✅ CORS configured with explicit frontend origins only
- [ ] ✅ Boot-time validation enforces all required env vars
- [ ] ✅ Health check endpoint operational
- [ ] ✅ No secrets in code or logs
- [ ] ✅ Integration guide provided to other DRIs

---

## IX. Deliverables for Gate 0 Review

Submit by Nov 14 10:00 MST:

1. **Evidence Package**:
   - Screenshot of JWKS endpoint response
   - Screenshot of token issuance response
   - Decoded JWT showing claims
   - CORS preflight test results

2. **Configuration Snapshot**:
   - List of configured Replit Secrets (names only, no values)
   - Boot validation log output

3. **Integration Documentation**:
   - Token validation example code
   - Service credential rotation procedure

---

## X. Escalation Path

**Blockers**:
- Key generation issues → Contact: SRE Team
- Replit Secrets access → Contact: DevOps
- JWKS format questions → Reference: Integration Standards Blueprint Section III
- Gate 0 slippage → Escalate to: Agent3 (Integration Lead) → CEO

**Timeline**:
- Escalate within 4 hours of identifying blocker
- Provide: service name, blocker description, attempted mitigations

---

**End of Gate 0 Execution Packet: scholar_auth**
