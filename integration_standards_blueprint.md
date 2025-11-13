# Scholar AI Advisor - Integration Standards & Config Blueprint
**Version**: 1.0  
**Date**: 2025-11-13  
**Owner**: Agent3 (Integration Lead)  
**Authority**: CEO Directive 2025-11-13

---

## I. Executive Summary

This blueprint defines mandatory standards for all 8 Scholar AI Advisor microservices to ensure secure, observable, and reliable integration. All services MUST comply with these standards to pass Go/No-Go gates.

**Non-Negotiables**:
- ✅ 100% environment-variable configuration (zero hardcoded URLs)
- ✅ OAuth2 client credentials with RS256/JWKS for service-to-service auth
- ✅ Strict CORS allowlisting
- ✅ Structured logging with correlation IDs
- ✅ P95 ≤ 120ms, error rate ≤ 1%, 99.9% uptime SLO

---

## II. Service Inventory & Base URLs

All services MUST store these as environment variables:

### A. Required Environment Variables (All Services)

```bash
# Service Discovery - ALL services must have these
AUTH_API_BASE_URL=https://scholar-auth-jamarrlmayes.replit.app
SCHOLARSHIP_API_BASE_URL=https://scholarship-api-jamarrlmayes.replit.app
SAGE_API_BASE_URL=https://scholarship-sage-jamarrlmayes.replit.app
AGENT_API_BASE_URL=https://scholarship-agent-jamarrlmayes.replit.app
AUTO_COM_CENTER_BASE_URL=https://auto-com-center-jamarrlmayes.replit.app
AUTO_PAGE_MAKER_BASE_URL=https://auto-page-maker-jamarrlmayes.replit.app
STUDENT_PILOT_BASE_URL=https://student-pilot-jamarrlmayes.replit.app
PROVIDER_REGISTER_BASE_URL=https://provider-register-jamarrlmayes.replit.app

# Frontend Origins (Backend services only)
FRONTEND_ORIGINS=https://student-pilot-jamarrlmayes.replit.app,https://provider-register-jamarrlmayes.replit.app

# Service Identity
SERVICE_NAME=<service-name>  # e.g., "scholarship_api"
ENVIRONMENT=production  # or development, staging
```

### B. Service-Specific Variables

**scholar_auth**:
```bash
JWT_PRIVATE_KEY_PATH=/path/to/private.pem  # RS256 private key
JWT_PUBLIC_KEY_PATH=/path/to/public.pem    # RS256 public key
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWKS_CACHE_TTL_SECONDS=3600
```

**All Backend Services** (consuming auth):
```bash
JWKS_URL=https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json
JWT_ISSUER=https://scholar-auth-jamarrlmayes.replit.app
JWT_AUDIENCE=scholarai-services  # or service-specific
```

**Services with Database**:
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

**Services with Redis** (for caching/sessions):
```bash
REDIS_URL=redis://host:port/db
REDIS_TTL_SECONDS=300
```

**auto_com_center**:
```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=<secret>
SMS_PROVIDER_API_KEY=<secret>
```

---

## III. Authentication & Authorization Standards

### A. Service-to-Service Authentication (OAuth2 Client Credentials)

**Implementation Required By**: Gate 0 (Nov 14 10:00)

#### 1. scholar_auth Responsibilities

**MUST Provide**:
- RS256 key pair generation and secure storage
- JWKS endpoint at `/.well-known/jwks.json`
- Token issuance endpoint: `POST /auth/token/service`

**Token Request Format**:
```http
POST /auth/token/service
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=<service-name>
&client_secret=<service-secret>
&scope=<requested-scopes>
```

**Token Response**:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "scope": "api.read api.write"
}
```

**JWT Claims (Service Tokens)**:
```json
{
  "iss": "https://scholar-auth-jamarrlmayes.replit.app",
  "aud": "scholarai-services",
  "sub": "service:scholarship_api",
  "roles": ["service"],
  "permissions": ["api.read", "api.write"],
  "jti": "<unique-token-id>",
  "iat": 1699900000,
  "exp": 1699900900
}
```

#### 2. Consuming Service Responsibilities

**MUST Implement**:
- JWKS fetching with caching (min 1 hour TTL)
- JWT signature validation using RS256
- Claims validation (iss, aud, exp, roles)
- Token refresh before expiry
- Circuit breaker for auth failures

**Reference Implementation** (Python/FastAPI):
```python
from jose import jwt, jwk
from jose.exceptions import JWTError
import httpx
from functools import lru_cache
from datetime import datetime, timedelta

class JWTValidator:
    def __init__(self, jwks_url: str, issuer: str, audience: str):
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self._jwks_cache = None
        self._cache_expiry = None
    
    @property
    def jwks(self):
        """Cached JWKS with 1-hour TTL"""
        if self._cache_expiry and datetime.utcnow() < self._cache_expiry:
            return self._jwks_cache
        
        try:
            response = httpx.get(self.jwks_url, timeout=5.0)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._cache_expiry = datetime.utcnow() + timedelta(hours=1)
            return self._jwks_cache
        except Exception as e:
            # Fail open if JWKS unavailable (or fail closed for critical services)
            raise RuntimeError(f"JWKS fetch failed: {e}")
    
    def validate_token(self, token: str) -> dict:
        """Validate JWT and return claims"""
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
                raise ValueError(f"No matching key found for kid: {kid}")
            
            # Verify signature using the specific key
            claims = jwt.decode(
                token,
                matching_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # Additional validation (jose already checks exp, but being explicit)
            if claims.get("exp", 0) < datetime.utcnow().timestamp():
                raise ValueError("Token expired")
            
            return claims
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")
```

**Middleware Pattern**:
```python
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """FastAPI dependency for service auth"""
    try:
        claims = jwt_validator.validate_token(credentials.credentials)
        
        # Enforce service role
        if "service" not in claims.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service role required"
            )
        
        return claims
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

# Usage in routes
@router.post("/internal/sync")
async def sync_data(claims: dict = Depends(verify_service_token)):
    service_id = claims["sub"]
    # Process request...
```

### B. User Authentication (Students, Providers, Admins)

**JWT Claims (User Tokens)**:
```json
{
  "iss": "https://scholar-auth-jamarrlmayes.replit.app",
  "aud": "scholarai-web",
  "sub": "user:uuid-here",
  "email": "student@example.com",
  "roles": ["student"],
  "permissions": ["profile.read", "profile.write", "scholarships.search"],
  "jti": "<unique-token-id>",
  "iat": 1699900000,
  "exp": 1699900900
}
```

**Roles**:
- `student`: Student users
- `provider`: Scholarship providers
- `admin`: Platform administrators
- `staff`: Internal staff
- `service`: Service-to-service accounts

**Permissions** (examples):
- `profile.read`, `profile.write`
- `scholarships.search`, `scholarships.apply`
- `provider.scholarships.create`, `provider.scholarships.edit`
- `admin.users.manage`, `admin.analytics.view`

### C. RBAC Enforcement Pattern

```python
def require_permissions(*required_perms: str):
    """Decorator for permission-based access control"""
    async def permission_checker(claims: dict = Depends(verify_token)):
        user_perms = set(claims.get("permissions", []))
        
        if not all(perm in user_perms for perm in required_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {required_perms}"
            )
        
        return claims
    
    return Depends(permission_checker)

# Usage
@router.post("/scholarships")
async def create_scholarship(
    data: ScholarshipCreate,
    claims: dict = require_permissions("provider.scholarships.create")
):
    # Only users with provider role + create permission can access
    pass
```

---

## IV. CORS Configuration Standards

### Backend Services (All APIs)

**MUST Configure**:
```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Load from environment
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,  # NEVER use ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=3600  # Cache preflight for 1 hour
)
```

**Validation**:
- ❌ FAIL if `FRONTEND_ORIGINS` not set
- ❌ FAIL if contains wildcard `*`
- ✅ PASS only if explicit frontend URLs listed

---

## V. Observability Standards

### A. Structured Logging

**Required Fields** (all log entries):
```json
{
  "timestamp": "2025-11-13T12:34:56.789Z",
  "level": "INFO",
  "service": "scholarship_api",
  "environment": "production",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "7f3c8a2d",
  "user_id": "user:uuid-here",
  "request_method": "POST",
  "request_path": "/scholarships",
  "status_code": 201,
  "latency_ms": 45,
  "message": "Scholarship created successfully",
  "error_code": null,
  "error_stack": null
}
```

**Log Levels**:
- `DEBUG`: Development debugging (not in production)
- `INFO`: Normal operations, business events
- `WARNING`: Degraded performance, fallbacks activated
- `ERROR`: Operation failures, exceptions
- `CRITICAL`: Service unavailable, data corruption

**Python Implementation**:
```python
import logging
import json
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar('trace_id', default=None)

class StructuredLogger:
    def __init__(self, service_name: str, environment: str):
        self.service = service_name
        self.environment = environment
        self.logger = logging.getLogger(service_name)
    
    def _build_log(self, level: str, message: str, **extra):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service,
            "environment": self.environment,
            "trace_id": trace_id_var.get(),
            "message": message,
            **extra
        })
    
    def info(self, message: str, **extra):
        self.logger.info(self._build_log("INFO", message, **extra))
    
    def error(self, message: str, exc_info=None, **extra):
        log_data = {"message": message, **extra}
        if exc_info:
            log_data["error_stack"] = str(exc_info)
        self.logger.error(self._build_log("ERROR", message, **log_data))
```

### B. Request ID Propagation

**Middleware** (all services):
```python
import uuid
from fastapi import Request

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    # Extract or generate trace ID
    trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id_var.set(trace_id)
    
    # Add to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = trace_id
    
    return response
```

**Inter-Service Calls**:
```python
async def call_other_service(url: str, **kwargs):
    """Helper that propagates trace ID"""
    headers = kwargs.get("headers", {})
    headers["X-Request-ID"] = trace_id_var.get()
    kwargs["headers"] = headers
    
    return await httpx.get(url, **kwargs)
```

### C. Health Check Standards

**Required Endpoints** (all services):

```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str
    dependencies: Dict[str, str]  # {"db": "healthy", "redis": "degraded"}

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Lightweight health check"""
    dependencies = {}
    overall_status = "healthy"
    
    # Check database
    try:
        await db.execute("SELECT 1")
        dependencies["database"] = "healthy"
    except Exception as e:
        dependencies["database"] = "unhealthy"
        overall_status = "degraded"
    
    # Check Redis (if applicable)
    try:
        await redis.ping()
        dependencies["redis"] = "healthy"
    except Exception:
        dependencies["redis"] = "unhealthy"
        # Redis failure might be degraded, not critical
    
    # Check auth service (for non-auth services)
    try:
        response = await httpx.get(
            f"{os.getenv('AUTH_API_BASE_URL')}/health",
            timeout=2.0
        )
        dependencies["auth_service"] = "healthy" if response.status_code == 200 else "degraded"
    except Exception:
        dependencies["auth_service"] = "unhealthy"
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=os.getenv("APP_VERSION", "unknown"),
        dependencies=dependencies
    )

@router.get("/health/liveness")
async def liveness():
    """Kubernetes liveness probe - fast check"""
    return {"status": "alive"}

@router.get("/health/readiness")
async def readiness():
    """Kubernetes readiness probe - dependency checks"""
    # Similar to /health but fail faster
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")
```

---

## VI. Boot-Time Validation

**Required for All Services**:

```python
import os
from typing import List

class ConfigValidator:
    """Validates required configuration at startup"""
    
    REQUIRED_VARS = [
        "SERVICE_NAME",
        "ENVIRONMENT",
        "AUTH_API_BASE_URL",
        "SCHOLARSHIP_API_BASE_URL",
        # Add service-specific vars
    ]
    
    @classmethod
    def validate(cls):
        """Validate configuration - fail fast on missing vars"""
        missing = []
        
        for var in cls.REQUIRED_VARS:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise RuntimeError(
                f"FATAL: Missing required environment variables: {missing}\n"
                f"Service cannot start. Please configure these in Replit Secrets."
            )
        
        # Validate CORS (backend services only)
        if os.getenv("SERVICE_TYPE") == "backend":
            origins = os.getenv("FRONTEND_ORIGINS", "")
            if not origins or "*" in origins:
                raise RuntimeError(
                    "FATAL: FRONTEND_ORIGINS must be explicitly set and not contain wildcards"
                )
        
        # Validate JWT config (non-auth services)
        if os.getenv("SERVICE_NAME") != "scholar_auth":
            if not os.getenv("JWKS_URL"):
                raise RuntimeError("FATAL: JWKS_URL required for auth validation")
        
        print(f"✅ Configuration validated for {os.getenv('SERVICE_NAME')}")

# In main.py
if __name__ == "__main__":
    # Validate BEFORE starting server
    ConfigValidator.validate()
    
    uvicorn.run("main:app", host="0.0.0.0", port=5000)
```

---

## VII. Error Response Standards

**Standard Error Envelope** (all APIs):

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorDetail(BaseModel):
    code: str  # Machine-readable error code
    message: str  # Human-readable message
    details: Optional[Dict[str, Any]] = None  # Additional context
    trace_id: Optional[str] = None

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[Dict[str, Any]] = None  # Pagination, etc.

# Error codes (standardized across all services)
ERROR_CODES = {
    "VALIDATION_ERROR": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}
```

**Exception Handler**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured errors"""
    
    trace_id = trace_id_var.get()
    
    # Log the error
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        trace_id=trace_id,
        path=request.url.path,
        method=request.method
    )
    
    # Return structured error
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                trace_id=trace_id
            )
        ).dict()
    )
```

---

## VIII. Security Requirements

### A. Secret Management

**MUST**:
- ✅ Store ALL secrets in Replit Secrets
- ✅ Never log secrets (implement PII redaction)
- ✅ Rotate service secrets quarterly
- ✅ Use different secrets per environment

**MUST NOT**:
- ❌ Hardcode secrets in code
- ❌ Commit secrets to Git
- ❌ Use default/insecure fallback values
- ❌ Share secrets across services (except shared auth secrets)

### B. Input Validation

**All Endpoints MUST**:
- Validate all inputs using Pydantic models
- Sanitize user-provided content
- Enforce max request sizes
- Rate limit write-heavy endpoints

### C. Security Headers

```python
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## IX. Performance Requirements

**SLOs (All Services)**:
- P95 latency ≤ 120ms (lightweight read endpoints)
- P99 latency ≤ 500ms
- Error rate ≤ 1%
- Uptime ≥ 99.9%

**Implementation**:
- Connection pooling for databases
- Caching for frequently accessed data
- Timeouts on all external calls (default: 5s)
- Circuit breakers for downstream failures
- Async/await for I/O operations

---

## X. Testing Standards

**Required Test Coverage**:
- Unit tests: ≥ 80% for critical services (scholar_auth, scholarship_api)
- Integration tests: All service-to-service flows
- E2E tests: Complete user journeys (Student, Provider)
- Security tests: Auth flows, RBAC, CORS

**Test Evidence Required for Each Gate**:
- Test reports with pass/fail status
- Coverage reports
- Performance test results (P95/P99 latencies)
- Security scan results

---

## XI. Compliance Checklist

Use this checklist for gate reviews:

### Configuration
- [ ] All inter-service URLs from environment variables
- [ ] No hardcoded URLs in codebase
- [ ] Boot-time validation implemented
- [ ] Secrets stored in Replit Secrets only

### Authentication & Authorization
- [ ] JWT validation using JWKS
- [ ] RS256 signature verification
- [ ] RBAC enforcement on protected endpoints
- [ ] Service-to-service auth implemented

### CORS
- [ ] Explicit frontend origins only
- [ ] No wildcard origins
- [ ] Credentials allowed where needed
- [ ] Standard headers configured

### Observability
- [ ] Structured JSON logging
- [ ] Correlation IDs propagated
- [ ] Health checks implemented
- [ ] Error responses standardized

### Security
- [ ] All secrets in Replit Secrets
- [ ] No secret logging
- [ ] Input validation on all endpoints
- [ ] Security headers configured
- [ ] Rate limiting on auth/write endpoints

### Performance
- [ ] P95 ≤ 120ms measured
- [ ] Connection pooling enabled
- [ ] Timeouts configured
- [ ] Circuit breakers implemented

---

## XII. Gate Readiness Criteria

### Gate 0 (Nov 14 10:00)
- [ ] scholar_auth: OAuth2 RS256/JWKS operational
- [ ] auto_com_center: Env-based URL templates
- [ ] All services: Boot-time validation

### Gate 1 (Nov 14 16:00)
- [ ] All services: JWT validation stable
- [ ] Health checks deployed
- [ ] RBAC claims finalized
- [ ] HA configuration (scholar_auth, scholarship_api)

### Gate 2 (Nov 15 12:00)
- [ ] All services: Environment-only config
- [ ] APIs integrated
- [ ] Frontends: Graceful error handling
- [ ] Initial notifications wired

### Gate 3 (Nov 16 16:00)
- [ ] E2E tests passing (Student + Provider journeys)
- [ ] Sage quality/performance validated
- [ ] Agent + com_center integration tests passing

### Gate 4 (Nov 17 17:00)
- [ ] War room sign-off
- [ ] Rollback plan verified
- [ ] All gate criteria met

### Gate 5 (Nov 18 10:00)
- [ ] Staged rollout ready
- [ ] Automated rollback configured
- [ ] Monitoring/alerting active

---

## XIII. Contact & Escalation

**Integration Lead**: Agent3  
**War Room Schedule**: Twice daily (10:00 MST, 16:00 MST)  
**Escalation**: CEO (gate slippage, critical blockers)

**DRI Responsibilities**:
- Implement standards in assigned service
- Report gate readiness status
- Escalate blockers within 4 hours
- Provide evidence for gate reviews

---

**End of Integration Standards & Config Blueprint v1.0**
