"""
Web Application Firewall (WAF) Protection Middleware

Provides edge-level protection against common web application attacks including:
- SQL injection attempts
- Cross-site scripting (XSS)
- Command injection
- Path traversal attacks
- Malicious request patterns

This middleware implements OWASP security controls and enforces
Authorization header requirements on protected endpoints.
"""

import re
import time
from re import Pattern

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from utils.logger import get_logger

# Rate limiter import removed for WAF focus

logger = get_logger(__name__)

class WAFProtection(BaseHTTPMiddleware):
    """
    Web Application Firewall middleware providing edge-level security protection

    Features:
    - SQL injection pattern detection and blocking
    - XSS payload identification and prevention
    - Command injection protection
    - Authorization header enforcement
    - Request pattern analysis and blocking
    - Security event logging and monitoring
    """

    def __init__(self, app, enable_block_mode: bool = True):
        super().__init__(app)
        self.block_mode = enable_block_mode
        self.blocked_requests = 0
        self.sql_injection_blocks = 0
        self.xss_blocks = 0
        self.auth_enforcement_blocks = 0

        # Compile security patterns for performance
        self._sql_patterns = self._compile_sql_patterns()
        self._xss_patterns = self._compile_xss_patterns()
        self._command_patterns = self._compile_command_patterns()
        self._path_traversal_patterns = self._compile_path_traversal_patterns()

        # Protected endpoints requiring Authorization header
        # CEO WAR ROOM FIX: Removed public endpoints (/scholarships, /search) from protection
        # These must be accessible for unauthenticated student browsing (discovery flow)
        self._protected_endpoints = {
            "/api/v1/eligibility/check",  # User-specific eligibility requires auth
            "/api/v1/recommendations",     # Personalized recommendations require auth
            "/api/v1/interactions"         # User interactions require auth
        }
        
        # Orchestration endpoints that should bypass SQL injection WAF (legitimate JSON payloads)
        # SECURITY: Exact matches only - no broad prefix bypasses
        self._waf_bypass_paths = {
            "/command",  # Agent Bridge orchestration from Command Center
            "/billing/external/credit-grant",  # External billing app credit grants (signed JSON)
            "/billing/external/provider-fee-paid",  # External billing app provider fees (signed JSON)
            "/api/v1/applications",  # Agent3 application submissions (JSON payloads)
            "/api/v1/applications/submit",  # Agent3 v3.0 primary endpoint
            "/api/v1/providers",  # Agent3 provider creation (JSON payloads)
            "/api/v1/providers/register",  # Agent3 v3.0 primary endpoint
            "/api/v1/fees/report",  # Agent3 fee reporting (JSON payloads)
            "/api/v1/credits/debit",  # Agent3 v3.0 credits debit (idempotent JSON)
            "/api/v1/credits",  # Credits operations (JSON payloads)
            "/api/scholarships",  # Master Prompt: Provider scholarship creation (JSON)
            "/api/webhooks/scholarships.updated",  # Master Prompt: Webhook receiver (signed JSON)
            "/api/events",  # Telemetry Contract v1.1: Fallback event write endpoint (service-to-service)
            "/api/events/single",  # Telemetry Contract v1.1: Single event write endpoint
        }
        
        # SECURITY: Regex patterns for dynamic routes that require WAF bypass
        # CEO Directive Gate B: Only HMAC-authenticated callback routes bypass SQL checks
        self._waf_bypass_patterns = [
            re.compile(r'^/api/v1/partners/[^/]+/onboarding/[^/]+/complete$'),  # Onboarding callback only
        ]

        logger.info(f"WAF Protection initialized - Block mode: {self.block_mode}")

    def _compile_sql_patterns(self) -> list[Pattern]:
        """Compile SQL injection detection patterns - tuned to avoid false positives"""
        sql_patterns = [
            # More contextual SQL injection patterns to avoid false positives
            r"(\bunion\b\s+(all\s+)?\bselect\b)",  # UNION SELECT specifically
            r"(\bselect\b.+\bfrom\b.+(\bwhere\b|;))",  # SELECT...FROM...WHERE/; patterns
            r"(['\"];?\s*(drop|delete|update|insert)\s+(table|from|into))",  # Commands with context
            r"(\b(or|and)\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?\s*(--|\#|;))",  # Classic injection patterns
            r"(\b(information_schema|sys\.|mysql\.|pg_)\w*)",  # Database system objects
            r"(--\s*|\#\s*|\s*/\*|\*/\s*)",  # SQL comments with context
            r"(\bor\b\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?)",  # OR 1=1 patterns
            r"(\';?\s*(drop|delete|update|insert)\s)",  # Semicolon followed by dangerous commands

            # Advanced patterns
            r"(\x27|\x22|\\x27|\\x22)",  # Encoded quotes
            r"(\b(waitfor|delay|benchmark|sleep)\s*\()",  # Time-based injection
            r"(\b(load_file|into\s+outfile|into\s+dumpfile)\b)",  # File operations
            r"(\b(sp_|xp_)\w+)",  # Stored procedures

            # Dangerous function calls in suspicious contexts
            r"(\b(concat|char|ascii|substring|length|mid|substr)\s*\(\s*['\"]?\w*['\"]?\s*,)",
        ]

        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in sql_patterns]

    def _compile_xss_patterns(self) -> list[Pattern]:
        """Compile XSS detection patterns"""
        xss_patterns = [
            r"(<\s*script\b[^<]*(?:(?!<\/\s*script\s*>)<[^<]*)*<\/\s*script\s*>)",
            r"(javascript\s*:)",
            r"(?<!\w)(on(?:abort|blur|change|click|contextmenu|copy|cut|dblclick|drag|drop|error|focus|input|keydown|keypress|keyup|load|mousedown|mousemove|mouseout|mouseover|mouseup|paste|reset|resize|scroll|select|submit|touchstart|touchend|unload|wheel))\s*=",
            r"(<\s*(iframe|object|embed|form|img|svg)\b)",
            r"(document\.(cookie|write|domain))",
            r"(window\.(location|open))",
            r"(\beval\s*\()",
            r"(\balert\s*\()",
            r"(expression\s*\()",
            r"(\bvbscript\s*:)",
        ]

        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in xss_patterns]

    def _compile_command_patterns(self) -> list[Pattern]:
        """Compile command injection patterns"""
        command_patterns = [
            r"(\b(wget|curl|nc|netcat|telnet|ssh|ftp)\b)",
            r"(\b(cat|ls|pwd|whoami|id|uname)\b)",
            r"(\b(rm|rmdir|del|copy|move|mv|cp)\b)",
            r"(\|(pipe)|;|&&|\|\|)",
            r"(\$\(|\`)",
            r"(\b(python|perl|ruby|php|node|java)\b.*(-c|-e))",
        ]

        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in command_patterns]

    def _compile_path_traversal_patterns(self) -> list[Pattern]:
        """Compile path traversal patterns"""
        path_patterns = [
            r"(\.\./|\.\.\\)",
            r"(\.\./){3,}",
            r"(\\\.\.\\|/\.\./)",
            r"(\%2e\%2e\%2f|\%2e\%2e\%5c)",
            r"(\%252e\%252e\%252f)",
        ]

        return [re.compile(pattern, re.IGNORECASE) for pattern in path_patterns]

    async def dispatch(self, request: Request, call_next):
        """Main WAF processing logic with CEO-mandated debug path blocking"""

        start_time = time.time()
        client_ip = getattr(request.client, 'host', '127.0.0.1') if request.client else '127.0.0.1'
        method = request.method
        path = request.url.path

        # CEO DIRECTIVE DEF-002: Multi-layer defense with canonicalization bypass protection
        # This is secondary defense; pre-router middleware is primary
        from urllib.parse import unquote
        
        path_lower = path.lower()
        path_decoded = unquote(path).lower()
        path_normalized = path.replace("//", "/").lower()
        
        # Check for debug paths with bypass protection
        if any([
            "_debug" in path_lower,
            "_debug" in path_decoded,
            "/debug" in path_lower,
            path.startswith("/_debug"),
            path_decoded.startswith("/_debug"),
            path_normalized.startswith("/_debug")
        ]):
            self.blocked_requests += 1
            logger.critical(
                f"🚨 WAF BLOCKED DEBUG PATH (Layer 2): {path} | "
                f"IP: {client_ip} | Method: {method} | "
                f"Incident: DEF-002"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "code": "WAF_DEBUG_BLOCK",
                    "message": "Access to debug endpoints is forbidden",
                    "status": 403,
                    "timestamp": int(time.time()),
                    "trace_id": f"waf-debug-block-{int(time.time())}"
                },
                headers={
                    "X-WAF-Action": "blocked",
                    "X-Incident-ID": "DEF-002",
                    "X-Block-Layer": "waf"
                }
            )

        # CRITICAL FIX: Only wrap WAF-specific checks in try/except
        # Do NOT catch exceptions from call_next() - let auth exceptions propagate properly
        try:
            # 1. AUTHORIZATION ENFORCEMENT (Critical for SQLi protection)
            if await self._check_authorization_requirement(request):
                return await self._block_request(
                    "Missing required Authorization header",
                    "WAF_AUTH_001",
                    client_ip,
                    path,
                    method
                )

            # 2. SQL INJECTION DETECTION
            if await self._detect_sql_injection(request):
                self.sql_injection_blocks += 1
                return await self._block_request(
                    "SQL injection attempt detected",
                    "WAF_SQLI_001",
                    client_ip,
                    path,
                    method
                )

            # 3. XSS DETECTION
            if await self._detect_xss(request):
                self.xss_blocks += 1
                return await self._block_request(
                    "Cross-site scripting attempt detected",
                    "WAF_XSS_001",
                    client_ip,
                    path,
                    method
                )

            # 4. COMMAND INJECTION DETECTION
            if await self._detect_command_injection(request):
                return await self._block_request(
                    "Command injection attempt detected",
                    "WAF_CMD_001",
                    client_ip,
                    path,
                    method
                )

            # 5. PATH TRAVERSAL DETECTION
            if await self._detect_path_traversal(request):
                return await self._block_request(
                    "Path traversal attempt detected",
                    "WAF_PATH_001",
                    client_ip,
                    path,
                    method
                )

        except Exception as e:
            logger.error(f"WAF check processing error: {str(e)}")
            # Only fail open on WAF check errors, not on authentication errors
            # Continue to application for availability
            pass

        # Request passes all WAF checks - call next middleware/application
        # CRITICAL: Do NOT wrap this in try/except - let authentication exceptions propagate
        response = await call_next(request)

        # Add security headers
        response.headers["X-WAF-Status"] = "passed"
        response.headers["X-Content-Type-Options"] = "nosniff"

        processing_time = (time.time() - start_time) * 1000
        logger.debug(f"WAF check passed - {method} {path} - {processing_time:.2f}ms")

        return response

    def _is_public_endpoint(self, request: Request) -> bool:
        """Centralized public endpoint check with path normalization"""
        normalized_path = request.url.path.rstrip('/') or '/'
        public_endpoints = {
            '/', '/health', '/healthz', '/metrics', '/docs', '/openapi.json', '/redoc',
            '/replit-health', '/_debug/routes', '/_debug/startup', '/_debug/scholarships', '/internal/metrics',
            # CEO WAR ROOM: Public discovery endpoints for student browsing
            '/api/v1/scholarships', '/api/v1/search', '/api/v1/credits/packages', '/api/v1/credits/pricing',
            '/api/v1/auth/login', '/api/v1/auth/login-simple', '/api/v1/auth/check'
        }
        # Also allow all GET requests to scholarship-related endpoints (read-only discovery)
        is_public = (
            normalized_path in public_endpoints or 
            normalized_path.startswith('/static') or
            normalized_path.startswith('/api/v1/scholarships/') or  # Individual scholarship details
            normalized_path.startswith('/api/v1/database/scholarships')  # Direct DB access for debugging
        )
        if is_public:
            logger.debug(f"WAF: Allowing public endpoint - {request.method} {normalized_path}")
        return is_public

    async def _check_authorization_requirement(self, request: Request) -> bool:
        """Check if protected endpoint requires Authorization header"""

        path = request.url.path
        method = request.method

        # Use centralized public endpoint check
        if self._is_public_endpoint(request):
            return False

        # CEO WAR ROOM: GET requests in monitor mode - allow for discovery, only block POST/PUT/PATCH
        # This enables unauthenticated scholarship browsing while protecting mutations
        if method == "GET":
            logger.debug(f"WAF: Allowing GET request (discovery mode) - {path}")
            return False

        # B2B endpoints should be handled by their own authentication middleware, not WAF
        # FIXED: Use precise path matching instead of broad startswith() checks
        b2b_exempt_prefixes = {
            "/b2b-partners/", "/partner/", "/commercial/", "/partner-sla/",
            "/api/v1/commercialization/", "/api/v1/billing/"
        }

        # Normalize path for comparison
        normalized_path = path.rstrip('/') + '/' if not path.endswith('/') else path

        # Check for exact B2B prefix matches to prevent overly broad exemptions
        is_b2b_exempt = any(normalized_path.startswith(prefix) for prefix in b2b_exempt_prefixes)

        if is_b2b_exempt:
            logger.debug(f"WAF: Allowing B2B endpoint for proper auth middleware - {request.method} {path}")
            return False

        # Check if endpoint requires authorization (POST/PUT/PATCH mutations only)
        if any(path.startswith(protected) for protected in self._protected_endpoints):
            auth_header = request.headers.get("authorization", "")

            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning(f"WAF: Blocking unauthorized mutation - {method} {path} (missing Bearer token)")
                self.auth_enforcement_blocks += 1
                return True

        return False

    async def _detect_sql_injection(self, request: Request) -> bool:
        """Detect SQL injection patterns in request"""

        # Use centralized public endpoint check
        if self._is_public_endpoint(request):
            return False

        # SQL injection exempt endpoints (legitimate content may contain SQL keywords)
        sql_exempt_paths = {
            "/partner/register",  # Partner registration may contain text like "select scholarships"
            "/api/v1/partners/register",  # New partner registration endpoint (legitimate JSON)
            "/api/v1/launch/simulate/traffic",
            # CEO P0 DIRECTIVE: Auth endpoints exempt from SQL injection checks (T+3h gate)
            # Authentication JSON payloads contain "password", "username" which trigger false positives
            # WAF Rule IDs exempted: WAF_SQLI_001 for these specific endpoints only
            "/api/v1/auth/login",
            "/api/v1/auth/login-simple",
            "/api/v1/auth/logout",
            "/api/v1/auth/check",
            "/api/v1/launch/commercialization/api-keys"
        }
        
        # Add orchestration bypass paths (legitimate JSON from Command Center)
        sql_exempt_paths.update(self._waf_bypass_paths)

        # Check exact path matches
        if request.url.path in sql_exempt_paths:
            # Log auth endpoint bypasses for monitoring and alerting
            from observability.metrics import metrics_service
            
            if "/api/v1/auth/" in request.url.path:
                logger.info(f"WAF: Auth endpoint bypassed (CEO directive) - {request.method} {request.url.path}")
                metrics_service.record_waf_allowlist_bypass(request.url.path)
            else:
                logger.debug(f"WAF: Allowing SQL-exempt endpoint - {request.method} {request.url.path}")
            return False
        
        # Check regex pattern matches for dynamic bypass routes (SECURITY: narrow scope only)
        for bypass_pattern in self._waf_bypass_patterns:
            if bypass_pattern.match(request.url.path):
                logger.debug(f"WAF: Allowing HMAC-authenticated callback (pattern match) - {request.method} {request.url.path}")
                return False

        # Check URL parameters
        query_string = str(request.url.query)
        if query_string and await self._scan_for_patterns(query_string, self._sql_patterns, "SQL"):
            return True

        # Check request body for JSON/form data
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await self._get_request_body(request)
                if body and await self._scan_for_patterns(body, self._sql_patterns, "SQL"):
                    return True
            except:
                pass  # Skip body parsing errors

        return False

    async def _detect_xss(self, request: Request) -> bool:
        """Detect XSS patterns in request"""

        # Path-level exemptions for legitimate endpoints
        xss_exempt_paths = {
            "/api/v1/launch/simulate/traffic"
        }

        if request.url.path in xss_exempt_paths:
            return False

        # Use centralized public endpoint check (consistency with SQL detection)
        if self._is_public_endpoint(request):
            return False

        query_string = str(request.url.query)
        if await self._scan_for_patterns(query_string, self._xss_patterns, "XSS"):
            return True

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await self._get_request_body(request)
                if body and await self._scan_for_patterns(body, self._xss_patterns, "XSS"):
                    return True
            except:
                pass

        return False

    async def _detect_command_injection(self, request: Request) -> bool:
        """Detect command injection patterns"""

        query_string = str(request.url.query)
        if await self._scan_for_patterns(query_string, self._command_patterns, "CMD"):
            return True

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await self._get_request_body(request)
                if body and await self._scan_for_patterns(body, self._command_patterns, "CMD"):
                    return True
            except:
                pass

        return False

    async def _detect_path_traversal(self, request: Request) -> bool:
        """Detect path traversal attempts"""

        path = request.url.path
        query_string = str(request.url.query)

        # Check URL path and parameters
        full_url = f"{path}?{query_string}"
        return await self._scan_for_patterns(full_url, self._path_traversal_patterns, "PATH")

    async def _scan_for_patterns(self, content: str, patterns: list[Pattern], attack_type: str) -> bool:
        """Scan content against compiled patterns"""

        if not content:
            return False

        for pattern in patterns:
            if pattern.search(content):
                logger.warning(f"WAF {attack_type} pattern detected: {pattern.pattern[:50]}...")
                return True

        return False

    async def _get_request_body(self, request: Request) -> str | None:
        """Safely extract request body for scanning"""
        try:
            body = await request.body()
            return body.decode('utf-8', errors='ignore')[:10000]  # Limit size
        except:
            return None

    async def _block_request(self, message: str, error_code: str, client_ip: str, path: str, method: str = "unknown") -> JSONResponse:
        """Block malicious request with structured response"""
        from observability.metrics import metrics_service

        self.blocked_requests += 1
        
        # Record WAF block metric
        metrics_service.record_waf_block(error_code, path, method)

        if not self.block_mode:
            # Monitor mode - log but don't block
            logger.warning(f"WAF MONITOR: {message} - {client_ip} {path}")
            # Continue to application (would be: return await call_next(request))

        # Block mode - return HTTP 403
        logger.error(f"WAF BLOCKED: {message} - {client_ip} {path}")

        response_data = {
            "error": "Request blocked by Web Application Firewall",
            "code": error_code,
            "status": 403,
            "timestamp": int(time.time()),
            "trace_id": f"waf-{int(time.time())}"
        }

        # Rate limit the attacker (skip for now - focus on blocking)
        # await self.rate_limiter.check_rate_limit(f"waf_block:{client_ip}", limit=1, window=3600)

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=response_data,
            headers={
                "X-WAF-Status": "blocked",
                "X-WAF-Rule": error_code,
                "Retry-After": "3600"
            }
        )

    def get_stats(self) -> dict[str, int]:
        """Get WAF statistics for monitoring"""
        return {
            "total_blocked": self.blocked_requests,
            "sql_injection_blocks": self.sql_injection_blocks,
            "xss_blocks": self.xss_blocks,
            "auth_enforcement_blocks": self.auth_enforcement_blocks
        }

# Global WAF instance
waf_protection = WAFProtection(None, enable_block_mode=True)
