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
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=5  # CEO directive: 5-minute TTL for security
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ISSUER=https://scholar-auth-jamarrlmayes.replit.app
JWT_AUDIENCE=scholarai-services
SERVICE_NAME=scholar_auth
ENVIRONMENT=production

# Frontend origins for CORS
FRONTEND_ORIGINS=https://student-pilot-jamarrlmayes.replit.app,https://provider-register-jamarrlmayes.replit.app

# Key rotation tracking (added for 90-day rotation requirement)
JWT_KEY_ID=key-2025-11-13  # Update when rotating keys
JWT_KEY_ROTATION_DATE=2025-11-13  # Track last rotation
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

## I-A. Key Rotation Runbook (90-Day Cycle with Overlap)

**CEO Requirement**: 90-day key rotation with overlapping validity to prevent service disruption.

### Strategy: Rolling Rotation with Dual-Key Support

During rotation, BOTH old and new keys are active for 24 hours to allow:
- Consuming services to refresh their JWKS cache
- In-flight tokens signed with old key to remain valid
- Zero-downtime transition

### Step 1: Rotation Schedule

**Set Calendar Reminders**:
```
Initial Key: 2025-11-13
Next Rotation: 2026-02-11 (90 days)
Following Rotation: 2026-05-12 (90 days)
```

**Rotation Checklist**:
- [ ] Generate new key pair
- [ ] Add new key to JWKS (dual-key period starts)
- [ ] Update JWT_KEY_ID and start issuing with new key
- [ ] Wait 24 hours (overlap period)
- [ ] Remove old key from JWKS
- [ ] Archive old key securely (for audit/recovery)

### Step 2: Generate New Key (Rotation Day)

```bash
# Generate new key pair with date suffix
openssl genrsa -out private-2026-02-11.pem 4096
openssl rsa -in private-2026-02-11.pem -pubout -out public-2026-02-11.pem

# Verify
openssl rsa -in private-2026-02-11.pem -check
```

### Step 3: Update Replit Secrets (Dual-Key Configuration)

**During 24-Hour Overlap**:
```bash
# Keep old key for validation
JWT_PRIVATE_KEY_OLD=<old-key-content-pipe-delimited>
JWT_PUBLIC_KEY_OLD=<old-public-key-pipe-delimited>
JWT_KEY_ID_OLD=key-2025-11-13

# Add new key for signing
JWT_PRIVATE_KEY=<new-key-content-pipe-delimited>
JWT_PUBLIC_KEY=<new-public-key-pipe-delimited>
JWT_KEY_ID=key-2026-02-11
JWT_KEY_ROTATION_DATE=2026-02-11
```

### Step 4: Update JWKSService for Dual-Key Support

```python
# services/jwks_service.py
from jose import jwk
from typing import Dict, List
import hashlib
import os
from cryptography.hazmat.primitives import serialization

class JWKSService:
    def __init__(self, current_public_key, old_public_key=None):
        self.current_public_key = current_public_key
        self.old_public_key = old_public_key
        self._jwks_cache = None
    
    def generate_jwks(self) -> Dict[str, List[Dict]]:
        """Generate JWKS with current + old keys during rotation"""
        keys = []
        
        # Current key (for new token issuance)
        current_key_pem = self.current_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        current_kid = os.getenv("JWT_KEY_ID", "current")
        current_jwk = jwk.construct(current_key_pem, algorithm="RS256")
        current_jwk_dict = current_jwk.to_dict()
        current_jwk_dict["kid"] = current_kid
        current_jwk_dict["use"] = "sig"
        current_jwk_dict["alg"] = "RS256"
        keys.append(current_jwk_dict)
        
        # Old key (for validation during rotation overlap)
        if self.old_public_key:
            old_key_pem = self.old_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            old_kid = os.getenv("JWT_KEY_ID_OLD")
            if old_kid:
                old_jwk = jwk.construct(old_key_pem, algorithm="RS256")
                old_jwk_dict = old_jwk.to_dict()
                old_jwk_dict["kid"] = old_kid
                old_jwk_dict["use"] = "sig"
                old_jwk_dict["alg"] = "RS256"
                keys.append(old_jwk_dict)
        
        return {"keys": keys}

# Update initialization in config/jwt_config.py
def load_old_key():
    """Load old public key during rotation period"""
    old_key_pem = os.getenv("JWT_PUBLIC_KEY_OLD", "").replace("|", "\n")
    if not old_key_pem or old_key_pem == "\n":
        return None
    
    try:
        return serialization.load_pem_public_key(
            old_key_pem.encode(),
            backend=default_backend()
        )
    except Exception:
        return None

old_public_key = load_old_key()
jwks_service = JWKSService(jwt_config.public_key, old_public_key)
```

### Step 5: Update Token Service to Use New Key

```python
# services/token_service.py
import os

class TokenService:
    # ... existing code ...
    
    def issue_service_token(self, client_id: str, scopes: List[str] = None) -> Dict:
        """Issue token with current key and kid"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=5)  # CEO mandate: 5-min TTL
        
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
        
        # Sign with current key and include kid in header
        kid = os.getenv("JWT_KEY_ID", "current")
        token = jwt.encode(
            claims,
            jwt_config.private_key,
            algorithm="RS256",
            headers={"kid": kid}  # Critical: must match JWKS kid
        )
        
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 300  # 5 minutes
        }
```

### Step 6: Rotation Timeline

**Day 0 (Rotation Day - e.g., 2026-02-11)**:
- 09:00 MST: Generate new key pair
- 09:30 MST: Add new key to Replit Secrets (both keys active)
- 10:00 MST: Deploy updated code with dual-key JWKS
- 10:30 MST: Verify JWKS endpoint returns both keys
- 11:00 MST: Update JWT_KEY_ID to new value (start issuing with new key)
- 11:30 MST: Verify new tokens use new kid
- **24-hour overlap begins**

**Day 1 (Overlap Complete - e.g., 2026-02-12)**:
- 11:00 MST: Remove JWT_PRIVATE_KEY_OLD and JWT_PUBLIC_KEY_OLD from secrets
- 11:30 MST: Deploy code update (JWKS returns only new key)
- 12:00 MST: Verify JWKS endpoint returns single key
- 12:30 MST: Archive old key pair (encrypt and store in secure backup)
- 13:00 MST: Update rotation documentation with completion timestamp

### Step 7: Emergency Rollback Procedure

**If rotation causes issues during overlap period**:

1. **Immediate**: Revert JWT_KEY_ID to old value
   ```bash
   JWT_KEY_ID=key-2025-11-13  # Revert to old
   ```

2. **Within 5 min**: Restart scholar_auth service
   - All new tokens will use old key again
   - Both keys still in JWKS, no service disruption

3. **Within 1 hour**: Investigate issue
   - Check consuming service JWKS cache
   - Verify kid matching logic
   - Review token validation logs

4. **Within 24 hours**: Retry rotation or extend overlap
   - If issue resolved: proceed with rotation
   - If issue persists: keep dual-key for extended period, escalate to CEO

### Step 8: Post-Rotation Validation

**Validation Checklist**:
- [ ] JWKS endpoint returns only new key
- [ ] New tokens issued with new kid
- [ ] Old tokens (if any exist) rejected after overlap
- [ ] All consuming services validating successfully
- [ ] No auth error rate spike (monitor <0.1% threshold)
- [ ] Rotation date documented in war room

### Step 9: Secure Key Archival

**Archive Old Keys** (for audit/compliance):
```bash
# Encrypt old key with AES-256
openssl enc -aes-256-cbc -salt -in private-2025-11-13.pem -out private-2025-11-13.pem.enc -k <passphrase>

# Store encrypted key in secure backup location
# Document: key ID, rotation date, encryption method, backup location
# Retention: 2 years for audit compliance
```

**Archive Metadata** (add to audit log):
```json
{
  "event": "key_rotation",
  "old_key_id": "key-2025-11-13",
  "new_key_id": "key-2026-02-11",
  "rotation_date": "2026-02-11T11:00:00-07:00",
  "overlap_period_hours": 24,
  "archived_key_location": "s3://backups/keys/private-2025-11-13.pem.enc",
  "performed_by": "ops@scholarai.com"
}
```

---

## II. JWKS Endpoint Implementation with Caching

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

### Step 3: Create JWKS Endpoint with Caching Headers

**CEO Requirement**: JWKS caching with Cache-Control, ETag support, 5-min consumer cache, 60-min hard cap.

```python
# routers/well_known.py
from fastapi import APIRouter, Response
from services.jwks_service import jwks_service
import hashlib
import json

router = APIRouter(prefix="/.well-known", tags=["well-known"])

@router.get("/jwks.json")
async def get_jwks(response: Response):
    """
    JSON Web Key Set endpoint for token verification.
    Consumed by all other services to validate JWTs.
    
    Caching Strategy:
    - Cache-Control: public, max-age=300 (5 minutes)
    - ETag: Content hash for change detection
    - Consuming services: 5-min cache, 60-min hard cap with backoff
    """
    jwks_data = jwks_service.generate_jwks()
    
    # Generate ETag from JWKS content for change detection
    content_str = json.dumps(jwks_data, sort_keys=True)
    etag = hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    # Set caching headers
    response.headers["Cache-Control"] = "public, max-age=300, s-maxage=300"  # 5 minutes
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Vary"] = "Accept-Encoding"
    
    # CORS headers handled by middleware, but ensure no sensitive data exposed
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    return jwks_data
```

**Caching Guidance for Consuming Services** (reference Implementation Standards Blueprint):
```python
# In consuming services (scholarship_api, etc.)

class JWTValidator:
    def __init__(self, jwks_url: str, issuer: str, audience: str):
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self._jwks_cache = None
        self._cache_expiry = None
        self._etag = None
    
    @property
    def jwks(self):
        """
        Cached JWKS with 5-minute TTL, 60-minute hard cap.
        Implements backoff + forced refetch when kid changes.
        """
        now = datetime.utcnow()
        
        # Check cache validity (5-minute soft TTL)
        if self._cache_expiry and now < self._cache_expiry and self._jwks_cache:
            return self._jwks_cache
        
        # Hard cap: Force refetch after 60 minutes regardless
        hard_cap = self._cache_expiry and now > (self._cache_expiry + timedelta(minutes=55))
        
        try:
            headers = {}
            if self._etag and not hard_cap:
                headers["If-None-Match"] = self._etag
            
            response = httpx.get(
                self.jwks_url,
                timeout=5.0,
                headers=headers
            )
            
            # ETag match - content unchanged, reuse cache
            if response.status_code == 304:
                self._cache_expiry = now + timedelta(minutes=5)
                return self._jwks_cache
            
            response.raise_for_status()
            
            # Update cache with new JWKS
            self._jwks_cache = response.json()
            self._cache_expiry = now + timedelta(minutes=5)  # 5-min soft TTL
            self._etag = response.headers.get("ETag")
            
            return self._jwks_cache
            
        except httpx.TimeoutException:
            # Backoff: Use stale cache if available
            if self._jwks_cache:
                logger.warning("JWKS fetch timeout, using stale cache")
                self._cache_expiry = now + timedelta(minutes=1)  # Short extension
                return self._jwks_cache
            raise RuntimeError("JWKS unavailable and no cache")
        
        except Exception as e:
            # Circuit breaker: Fail closed after repeated failures
            if self._jwks_cache:
                logger.error(f"JWKS fetch failed: {e}, using stale cache")
                return self._jwks_cache
            raise RuntimeError(f"JWKS fetch failed: {e}")
```

**Key Rotation Detection**:
When consuming services encounter a token with unknown `kid`:
1. Clear JWKS cache immediately
2. Refetch JWKS (should now include new key)
3. Retry validation
4. If still fails, reject token and alert

```python
def validate_token(self, token: str) -> dict:
    """Validate JWT with kid-based key selection and cache invalidation"""
    max_retries = 1
    
    for attempt in range(max_retries + 1):
        try:
            # Get unverified header to extract kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise ValueError("Token missing kid in header")
            
            # Find matching key in JWKS
            jwks_data = self.jwks
            matching_key = None
            
            for key in jwks_data.get("keys", []):
                if key.get("kid") == kid:
                    matching_key = key
                    break
            
            if not matching_key:
                # Key not found - might be new rotation
                if attempt == 0:
                    logger.info(f"Unknown kid {kid}, invalidating cache and retrying")
                    self._jwks_cache = None  # Force refetch
                    self._cache_expiry = None
                    continue  # Retry with fresh JWKS
                else:
                    raise ValueError(f"No matching key found for kid: {kid}")
            
            # Verify signature using the specific key
            claims = jwt.decode(
                token,
                matching_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience
            )
            
            return claims
            
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")
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

## VII-A. Operational Failure Modes & Runbooks

**CEO Requirement**: Failure-mode matrix with alarms and runbooks for production resilience.

### Failure Mode 1: JWKS Endpoint Unavailable

**Symptoms**:
- Consuming services log "JWKS fetch failed"
- Auth validation returns 503 Service Unavailable
- Token validation failures spike

**Root Causes**:
- scholar_auth service down
- Network connectivity issues
- Database overload affecting boot-time key loading

**Detection**:
- Alert: JWKS endpoint returns non-200 for 2 consecutive health checks
- Metric: `jwks_fetch_failure_rate > 0.1%` for 5 minutes
- Threshold: P95 latency > 500ms

**Runbook**:
1. **Immediate** (T+0):
   - Check scholar_auth health endpoint: `/health`
   - Verify scholar_auth service is running
   - Check Replit deployment status

2. **T+2 min**:
   - Review scholar_auth logs for errors
   - Check database connectivity
   - Verify JWT_PRIVATE_KEY and JWT_PUBLIC_KEY in secrets

3. **T+5 min**:
   - If service down: Restart scholar_auth
   - If key loading fails: Verify secret format (pipe-delimited)
   - If database issue: Scale DB or failover

4. **T+10 min**:
   - Validate JWKS endpoint returns 200
   - Test token issuance
   - Monitor consuming service recovery

**Impact**: HIGH - All service-to-service auth blocked

---

### Failure Mode 2: Token Validation Failures After Key Rotation

**Symptoms**:
- Consuming services reject tokens with new `kid`
- 401 Unauthorized spike immediately after rotation
- Logs show "No matching key found for kid: key-YYYY-MM-DD"

**Root Causes**:
- Consuming service JWKS cache not updated
- New key not added to JWKS before switching JWT_KEY_ID
- Clock skew causing validation timing issues

**Detection**:
- Alert: `token_validation_failure_rate > 1%` within 30 min of rotation
- Metric: 401 errors spike correlated with rotation timestamp
- Log pattern: "Unknown kid" errors

**Runbook**:
1. **Immediate** (T+0):
   - Verify JWKS endpoint includes both old and new keys
   - Check JWT_KEY_ID_OLD is set during overlap period
   - Confirm rotation timeline (24-hour overlap)

2. **T+5 min**:
   - Force consuming services to clear JWKS cache:
     - Restart services OR
     - Call cache invalidation endpoint (if implemented)
   - Verify new tokens include correct `kid` in header

3. **T+15 min**:
   - If validation still failing: Rollback JWT_KEY_ID to old value
   - Extend overlap period to 48 hours
   - Investigate consuming service JWKS caching logic

4. **T+1 hour**:
   - If rollback successful: Document root cause
   - Plan retry with longer cache warming period
   - Update rotation procedure if needed

**Impact**: HIGH - Service-to-service auth degraded during rotation

---

### Failure Mode 3: Service Credential Compromise

**Symptoms**:
- Unauthorized API calls from unknown sources
- Audit logs show unexpected service actions
- Token issued to service used outside normal patterns

**Root Causes**:
- Service secret leaked in code or logs
- SERVICE_CREDENTIALS misconfigured with weak secrets
- Man-in-the-middle attack on token exchange

**Detection**:
- Alert: Service token used from unexpected IP range
- Metric: API calls with service token outside business hours
- Pattern: Rapid token refresh from single service (potential replay)

**Runbook**:
1. **Immediate** (T+0 - SECURITY INCIDENT):
   - Identify compromised service credential (client_id)
   - Revoke credential by removing from SERVICE_CREDENTIALS
   - Force redeploy scholar_auth to apply change

2. **T+10 min**:
   - Generate new credential for affected service
   - Securely communicate new secret to service owner
   - Update service's Replit Secrets
   - Restart affected service

3. **T+30 min**:
   - Review audit logs for unauthorized actions
   - Identify data accessed or modified
   - Notify security team and affected parties

4. **T+2 hours**:
   - Conduct post-mortem: How was credential compromised?
   - Implement preventive measures (secret scanning, rotation)
   - Update security documentation

**Impact**: CRITICAL - Potential data breach, unauthorized access

---

### Failure Mode 4: Clock Skew Causing Token Expiry Issues

**Symptoms**:
- Tokens rejected as expired before 5-minute TTL
- Intermittent 401 errors on fresh tokens
- Logs show "Token expired" for recently issued tokens

**Root Causes**:
- Server clocks not synchronized (NTP drift)
- Timezone configuration mismatch
- Consumer service clock ahead of issuer

**Detection**:
- Alert: Token validation failures with `exp` claim within 1 minute of issue time
- Metric: Unexplained 401 rate during normal operations
- Pattern: Errors correlated with specific consuming service

**Runbook**:
1. **Immediate** (T+0):
   - Check server time on scholar_auth: `date -u`
   - Check server time on failing consumer: `date -u`
   - Compare timestamps (should be within 5 seconds)

2. **T+5 min**:
   - If clock skew > 10 seconds:
     - Force NTP sync on affected servers
     - Restart services after time correction
   - Add clock skew tolerance to validation (±30 seconds)

3. **T+15 min**:
   - Implement clock sync monitoring
   - Add drift alerts (>5 seconds from NTP)
   - Document timezone requirements (all services use UTC)

**Impact**: MEDIUM - Service auth degraded, user-facing errors

---

### Failure Mode 5: CORS Preflight Failures Blocking Frontend Auth

**Symptoms**:
- Browser console shows CORS errors
- Frontend cannot call /auth/token/service
- OPTIONS requests return 403 or lack CORS headers

**Root Causes**:
- FRONTEND_ORIGINS not configured or misconfigured
- Wildcard (*) origin rejected by browser for credentials
- Missing OPTIONS handler for CORS preflight

**Detection**:
- Alert: High rate of OPTIONS requests with non-200 status
- Metric: Browser error rate spike from specific origins
- Log pattern: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Runbook**:
1. **Immediate** (T+0):
   - Verify FRONTEND_ORIGINS in scholar_auth secrets
   - Confirm exact match with requesting origin (including https://)
   - Check CORS middleware configuration

2. **T+5 min**:
   - Test CORS preflight manually:
     ```bash
     curl -X OPTIONS https://scholar-auth.../auth/token/service \
       -H "Origin: https://student-pilot..." \
       -H "Access-Control-Request-Method: POST"
     ```
   - Verify response includes Access-Control-Allow-Origin header

3. **T+10 min**:
   - If header missing: Update CORS middleware
   - If origin mismatch: Add correct origin to FRONTEND_ORIGINS
   - Restart scholar_auth service

**Impact**: HIGH - Frontend auth completely blocked

---

### Monitoring & Alerting Configuration

**Required Metrics** (CEO Mandate: Token validation failure rate <0.1%):

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram, Gauge

# Token issuance
tokens_issued_total = Counter(
    'auth_tokens_issued_total',
    'Total tokens issued',
    ['client_id', 'grant_type']
)

# Token validation (in consuming services)
token_validation_total = Counter(
    'auth_token_validation_total',
    'Total token validations',
    ['result']  # success, expired, invalid_signature, missing_kid, etc.
)

# JWKS fetch performance
jwks_fetch_duration = Histogram(
    'auth_jwks_fetch_duration_seconds',
    'JWKS fetch duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

jwks_cache_hits = Counter(
    'auth_jwks_cache_hits_total',
    'JWKS cache hits vs misses',
    ['result']  # hit, miss, stale
)

# Key rotation tracking
active_keys_gauge = Gauge(
    'auth_active_keys',
    'Number of keys in JWKS'
)

rotation_events = Counter(
    'auth_key_rotation_events_total',
    'Key rotation events',
    ['phase']  # start, overlap, complete, rollback
)
```

**Alert Rules**:
```yaml
# alert-rules.yml
groups:
  - name: scholar_auth_alerts
    interval: 1m
    rules:
      - alert: HighTokenValidationFailureRate
        expr: rate(auth_token_validation_total{result!="success"}[5m]) > 0.001  # 0.1%
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Token validation failure rate exceeds 0.1%"
          
      - alert: JWKSEndpointDown
        expr: up{job="scholar_auth", endpoint="jwks"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "JWKS endpoint unavailable"
      
      - alert: ClockSkewDetected
        expr: abs(time() - auth_server_time_seconds) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Clock skew >10 seconds detected"
          
      - alert: UnexpectedKeyRotation
        expr: changes(auth_active_keys[5m]) > 0 AND hour() NOT IN (9,10,11)  # Rotations should be 09:00-11:00 MST
        labels:
          severity: warning
        annotations:
          summary: "Key rotation outside scheduled window"
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
