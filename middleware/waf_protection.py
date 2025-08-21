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
import json
import time
from typing import Dict, List, Set, Optional, Pattern
from fastapi import Request, HTTPException, status
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
        self._protected_endpoints = {
            "/api/v1/scholarships",
            "/api/v1/search", 
            "/api/v1/eligibility",
            "/api/v1/recommendations",
            "/api/v1/interactions"
        }
        
        logger.info(f"WAF Protection initialized - Block mode: {self.block_mode}")
    
    def _compile_sql_patterns(self) -> List[Pattern]:
        """Compile SQL injection detection patterns"""
        sql_patterns = [
            # Classic SQL injection patterns
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(\b(or|and)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(['\"];?\s*(drop|delete|update|insert)\s)",
            r"(\b(concat|char|ascii|substring|length|mid|substr)\s*\()",
            r"(\b(information_schema|sys\.|mysql\.|pg_)\w*)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bor\b\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?)",
            r"(\bunion\b\s+(all\s+)?select)",
            r"(\bselect\b.+\bfrom\b.+\bwhere\b)",
            
            # Advanced SQL injection patterns  
            r"(\x27|\x22|\\x27|\\x22)",  # Encoded quotes
            r"(\b(waitfor|delay|benchmark|sleep)\s*\()",
            r"(\b(load_file|into\s+outfile|into\s+dumpfile)\b)",
            r"(\b(grant|revoke|privilege)\b)",
            r"(\b(sp_|xp_)\w+)",  # Stored procedures
        ]
        
        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in sql_patterns]
    
    def _compile_xss_patterns(self) -> List[Pattern]:
        """Compile XSS detection patterns"""
        xss_patterns = [
            r"(<\s*script\b[^<]*(?:(?!<\/\s*script\s*>)<[^<]*)*<\/\s*script\s*>)",
            r"(javascript\s*:)",
            r"(on\w+\s*=)",
            r"(<\s*(iframe|object|embed|form|img|svg)\b)",
            r"(document\.(cookie|write|domain))",
            r"(window\.(location|open))",
            r"(\beval\s*\()",
            r"(\balert\s*\()",
            r"(expression\s*\()",
            r"(\bvbscript\s*:)",
        ]
        
        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in xss_patterns]
    
    def _compile_command_patterns(self) -> List[Pattern]:
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
    
    def _compile_path_traversal_patterns(self) -> List[Pattern]:
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
        """Main WAF processing logic"""
        
        start_time = time.time()
        client_ip = getattr(request.client, 'host', '127.0.0.1') if request.client else '127.0.0.1'
        method = request.method
        path = request.url.path
        
        try:
            # 1. AUTHORIZATION ENFORCEMENT (Critical for SQLi protection)
            if await self._check_authorization_requirement(request):
                return await self._block_request(
                    "Missing required Authorization header",
                    "WAF_AUTH_001",
                    client_ip,
                    path
                )
            
            # 2. SQL INJECTION DETECTION
            if await self._detect_sql_injection(request):
                self.sql_injection_blocks += 1
                return await self._block_request(
                    "SQL injection attempt detected",
                    "WAF_SQLI_001", 
                    client_ip,
                    path
                )
            
            # 3. XSS DETECTION
            if await self._detect_xss(request):
                self.xss_blocks += 1
                return await self._block_request(
                    "Cross-site scripting attempt detected",
                    "WAF_XSS_001",
                    client_ip, 
                    path
                )
            
            # 4. COMMAND INJECTION DETECTION
            if await self._detect_command_injection(request):
                return await self._block_request(
                    "Command injection attempt detected", 
                    "WAF_CMD_001",
                    client_ip,
                    path
                )
            
            # 5. PATH TRAVERSAL DETECTION
            if await self._detect_path_traversal(request):
                return await self._block_request(
                    "Path traversal attempt detected",
                    "WAF_PATH_001", 
                    client_ip,
                    path
                )
            
            # Request passes all WAF checks
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-WAF-Status"] = "passed"
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"WAF check passed - {method} {path} - {processing_time:.2f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"WAF processing error: {str(e)}")
            # Fail open for availability, but log security event
            response = await call_next(request)
            response.headers["X-WAF-Status"] = "error" 
            return response
    
    async def _check_authorization_requirement(self, request: Request) -> bool:
        """Check if protected endpoint requires Authorization header"""
        
        path = request.url.path
        method = request.method
        
        # Skip health checks and public endpoints
        public_endpoints = {"/", "/health", "/metrics", "/docs", "/openapi.json", "/replit-health"}
        if path in public_endpoints or path.startswith("/static"):
            return False
        
        # Check if endpoint requires authorization
        if any(path.startswith(protected) for protected in self._protected_endpoints):
            auth_header = request.headers.get("authorization", "")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning(f"Authorization required but missing - {method} {path}")
                self.auth_enforcement_blocks += 1
                return True
        
        return False
    
    async def _detect_sql_injection(self, request: Request) -> bool:
        """Detect SQL injection patterns in request"""
        
        # Skip SQLi detection for health/public endpoints
        path = request.url.path
        public_endpoints = {"/", "/health", "/metrics", "/docs", "/openapi.json", "/replit-health"}
        if path in public_endpoints or path.startswith("/static"):
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
    
    async def _scan_for_patterns(self, content: str, patterns: List[Pattern], attack_type: str) -> bool:
        """Scan content against compiled patterns"""
        
        if not content:
            return False
        
        for pattern in patterns:
            if pattern.search(content):
                logger.warning(f"WAF {attack_type} pattern detected: {pattern.pattern[:50]}...")
                return True
        
        return False
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Safely extract request body for scanning"""
        try:
            body = await request.body()
            return body.decode('utf-8', errors='ignore')[:10000]  # Limit size
        except:
            return None
    
    async def _block_request(self, message: str, error_code: str, client_ip: str, path: str) -> JSONResponse:
        """Block malicious request with structured response"""
        
        self.blocked_requests += 1
        
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
    
    def get_stats(self) -> Dict[str, int]:
        """Get WAF statistics for monitoring"""
        return {
            "total_blocked": self.blocked_requests,
            "sql_injection_blocks": self.sql_injection_blocks,
            "xss_blocks": self.xss_blocks,
            "auth_enforcement_blocks": self.auth_enforcement_blocks
        }

# Global WAF instance
waf_protection = WAFProtection(None, enable_block_mode=True)