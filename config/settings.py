"""
Environment-specific Configuration Management
Using pydantic-settings for type-safe configuration
"""

import os
import secrets
import logging
from typing import List, Optional, Annotated, Set, ClassVar
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):
    """
    Application settings with strict production validation
    Provides secure defaults for development, enforces requirements for production
    """
    
    # Security constants
    BANNED_DEFAULT_SECRETS: ClassVar[Set[str]] = {
        "your-secret-key-change-in-production",
        "secret", "dev", "development", "test", "changeme", "default"
    }
    
    # Environment - defaults to development to avoid production validation issues
    environment: Environment = Field(Environment.DEVELOPMENT, alias="ENVIRONMENT")
    strict_config_validation: Optional[bool] = Field(None, alias="STRICT_CONFIG_VALIDATION")
    debug: bool = Field(True, alias="DEBUG")
    
    # API Configuration
    api_title: str = Field("Scholarship Discovery & Search API", alias="API_TITLE")
    api_version: str = Field("1.0.0", alias="API_VERSION")
    api_description: str = Field(
        "A comprehensive API for scholarship discovery with advanced search and eligibility checking",
        alias="API_DESCRIPTION"
    )
    
    # Server Configuration - Replit compatible
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "5000")), alias="PORT")  # Replit uses port 5000
    reload: bool = Field(True, alias="RELOAD")
    
    # Security Configuration - JWT with production validation
    jwt_secret_key: Optional[str] = Field(None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_previous_secret_keys: str = Field("", alias="JWT_PREVIOUS_SECRET_KEYS")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES", gt=0)
    
    # Production security requirements - fix parsing issues with proper JSON parsing
    allowed_hosts: List[str] = Field(
        default_factory=lambda: [
            "localhost", "127.0.0.1", 
            "*.replit.app", "*.replit.dev", "*.repl.co",
            # Dynamic Replit development domains pattern
            "*.picard.replit.dev", "*.kirk.replit.dev", "*.spock.replit.dev"
        ],
        alias="ALLOWED_HOSTS"
    )
    trusted_proxy_ips: List[str] = Field(default_factory=list, alias="TRUSTED_PROXY_IPS")
    
    @field_validator('allowed_hosts', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str):
            if v.strip() == "":
                return []
            # Try to parse as JSON first
            try:
                import json
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                # Fallback to comma-separated values
                return [host.strip() for host in v.split(',') if host.strip()]
        return v if isinstance(v, list) else []
    
    @field_validator('trusted_proxy_ips', mode='before') 
    @classmethod
    def parse_trusted_proxy_ips(cls, v):
        """Parse trusted proxy IPs from string or list"""
        if isinstance(v, str):
            if v.strip() == "":
                return []
            # Try to parse as JSON first
            try:
                import json
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                # Fallback to comma-separated values
                return [ip.strip() for ip in v.split(',') if ip.strip()]
        return v if isinstance(v, list) else []
    enable_docs: Optional[bool] = Field(None, alias="ENABLE_DOCS")
    
    # Feature flag for public read endpoints (authentication bypass)
    public_read_endpoints: bool = Field(True, alias="PUBLIC_READ_ENDPOINTS")  # Default to True for dev
    
    # Agent Orchestration Configuration
    command_center_url: Optional[str] = Field(None, alias="COMMAND_CENTER_URL")
    agent_shared_secret: Optional[str] = Field(None, alias="SHARED_SECRET") 
    agent_name: str = Field("scholarship_api", alias="AGENT_NAME")
    agent_id: str = Field("scholarship_api", alias="AGENT_ID")
    agent_base_url: Optional[str] = Field(None, alias="AGENT_BASE_URL")
    jwt_issuer: str = Field("auto-com-center", alias="JWT_ISSUER")
    jwt_audience: str = Field("scholar-sync-agents", alias="JWT_AUDIENCE")
    
    # Agent Bridge feature flags
    orchestration_enabled: bool = Field(True, alias="ORCHESTRATION_ENABLED")
    orchestration_traffic_percentage: int = Field(100, alias="ORCHESTRATION_TRAFFIC_PERCENTAGE")
    agent_health_enabled: bool = Field(True, alias="AGENT_HEALTH_ENABLED")
    agent_capabilities_enabled: bool = Field(True, alias="AGENT_CAPABILITIES_ENABLED")
    
    # Production security enhancements
    jwt_clock_skew_seconds: int = Field(10, alias="JWT_CLOCK_SKEW_SECONDS")
    jwt_require_jti: bool = Field(True, alias="JWT_REQUIRE_JTI")
    agent_rate_limit_per_minute: int = Field(50, alias="AGENT_RATE_LIMIT_PER_MINUTE")
    
    # Rate limiting backend requirements (production-aware)  
    disable_rate_limit_backend: bool = Field(False, alias="DISABLE_RATE_LIMIT_BACKEND")
    
    # CORS Configuration - QA FIX: Replace wildcard with allowlist
    cors_allowed_origins: str = Field(
        default="",
        alias="ALLOWED_ORIGINS",
        description="Comma-separated list of allowed origins for production"
    )
    cors_allow_credentials: bool = Field(False, alias="ALLOW_CREDENTIALS")  # QA FIX: Default false
    cors_allow_methods: List[str] = Field(
        ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], 
        alias="ALLOWED_METHODS"
    )
    cors_allow_headers: List[str] = Field(
        ["Authorization", "Content-Type", "Accept", "X-Request-Id"],
        alias="ALLOWED_HEADERS"
    )
    cors_max_age: int = Field(600, alias="MAX_AGE")  # 10 minutes
    
    @property
    def get_cors_origins(self) -> List[str]:
        """Get environment-appropriate CORS origins with production safety - QA FIX"""
        if self.environment == Environment.PRODUCTION:
            # Production: MUST have explicit whitelist, no wildcards allowed
            if not self.cors_allowed_origins:
                import logging
                logging.critical(
                    "PRODUCTION SECURITY ERROR: CORS_ALLOWED_ORIGINS not configured. "
                    "This could allow any origin to access your API!"
                )
                # Production safe defaults - replace with actual domains
                return [
                    "https://app.yourdomain.com",
                    "https://admin.yourdomain.com"
                ]
            
            origins = [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
            if "*" in origins:
                import logging
                logging.critical(
                    "PRODUCTION SECURITY ERROR: Wildcard (*) origin detected in production. "
                    "This is a security vulnerability!"
                )
                # Remove wildcard for production safety
                origins = [o for o in origins if o != "*"]
            
            return origins if origins else [
                "https://app.yourdomain.com",
                "https://admin.yourdomain.com"
            ]
        else:
            # Development/staging: Conservative allowlist instead of wildcard
            dev_origins = [
                "http://localhost:3000", 
                "http://127.0.0.1:3000", 
                "http://localhost:5000",
                "http://localhost:8000",
                "http://localhost:8080"
            ]
            
            # Add dynamic Replit origin detection
            replit_id = os.getenv("REPL_ID")
            replit_owner = os.getenv("REPL_OWNER") 
            if replit_id and replit_owner:
                replit_origin = f"https://{replit_id}.{replit_owner}.repl.co"
                dev_origins.append(replit_origin)
                
            # Add Replit webview domain
            if os.getenv("REPLIT_DEPLOYMENT"):
                webview_domain = f"https://{replit_id}--{replit_owner}.repl.co"
                dev_origins.append(webview_domain)
                
            if self.cors_allowed_origins:
                custom_origins = [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
                dev_origins.extend(custom_origins)
                
            return dev_origins
    
    @property
    def get_cors_config(self) -> dict:
        """Get complete CORS configuration - QA FIX"""
        origins = self.get_cors_origins
        return {
            "allow_origins": origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers,
            "max_age": self.cors_max_age,
            # QA FIX: Ensure Vary header is set for security
            "expose_headers": ["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
        }
    
    # Database Configuration
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    database_echo: bool = Field(False, alias="DATABASE_ECHO")
    database_pool_size: int = Field(5, alias="DATABASE_POOL_SIZE", gt=0)
    database_max_overflow: int = Field(10, alias="DATABASE_MAX_OVERFLOW", ge=0)
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")
    redis_timeout: int = Field(5, alias="REDIS_TIMEOUT")
    
    # Rate Limiting Configuration - Environment-specific
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")
    rate_limit_backend_url: str = Field("redis://localhost:6379/0", alias="RATE_LIMIT_BACKEND_URL")
    rate_limit_per_minute: int = Field(0, alias="RATE_LIMIT_PER_MINUTE")  # 0 = use defaults
    
    # Health check endpoint exemption for deployment probes
    rate_limit_exempt_paths: List[str] = Field(
        ["/health", "/healthz", "/readiness", "/metrics", "/"],
        alias="RATE_LIMIT_EXEMPT_PATHS"
    )
    
    @property
    def get_rate_limit_per_minute(self) -> int:
        """Get environment-appropriate rate limit per minute"""
        if self.rate_limit_per_minute > 0:
            return self.rate_limit_per_minute
        
        # Environment-specific defaults
        return {
            Environment.PRODUCTION: 100,
            Environment.STAGING: 150,
            Environment.DEVELOPMENT: 200,

        }.get(self.environment, 200)
    
    @property
    def get_rate_limit_config(self) -> dict:
        """Get complete rate limiting configuration"""
        return {
            "enabled": self.rate_limit_enabled,
            "backend_url": self.rate_limit_backend_url,
            "per_minute": self.get_rate_limit_per_minute,
            "exempt_paths": self.rate_limit_exempt_paths
        }
    
    # Legacy rate limiting fields (keep for backward compatibility)
    rate_limit_search: str = Field("30/minute", alias="RATE_LIMIT_SEARCH")
    rate_limit_eligibility: str = Field("15/minute", alias="RATE_LIMIT_ELIGIBILITY") 
    rate_limit_scholarships: str = Field("60/minute", alias="RATE_LIMIT_SCHOLARSHIPS")
    rate_limit_analytics: str = Field("10/minute", alias="RATE_LIMIT_ANALYTICS")
    
    # Remove problematic field_validator for now - we'll handle environment adjustment in properties
    
    # Environment-aware rate limit properties
    @property 
    def get_search_rate_limit(self) -> str:
        """Get environment-appropriate search rate limit"""
        base_limit = int(self.rate_limit_search.split('/')[0])
        if self.environment == Environment.DEVELOPMENT:
            return f"{base_limit * 2}/minute"
        return self.rate_limit_search
    
    @property
    def get_eligibility_rate_limit(self) -> str:
        """Get environment-appropriate eligibility rate limit"""
        base_limit = int(self.rate_limit_eligibility.split('/')[0])
        if self.environment == Environment.DEVELOPMENT:
            return f"{base_limit * 2}/minute"
        return self.rate_limit_eligibility
    
    @property
    def get_backend_url(self) -> str:
        """Get rate limiting backend URL"""
        return self.rate_limit_backend_url
    
    # Logging Configuration
    log_level: LogLevel = Field(LogLevel.INFO, alias="LOG_LEVEL")
    log_format: str = Field("json", alias="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(None, alias="LOG_FILE")
    
    # Analytics Configuration with validation  
    analytics_enabled: bool = Field(True, alias="ANALYTICS_ENABLED")
    analytics_retention_days: int = Field(90, alias="ANALYTICS_RETENTION_DAYS", gt=0)
    
    # Search Configuration with validation
    search_default_limit: int = Field(20, alias="SEARCH_DEFAULT_LIMIT", gt=0, le=100)
    search_max_limit: int = Field(100, alias="SEARCH_MAX_LIMIT", gt=0, le=1000)
    
    # Cache Configuration with validation
    cache_enabled: bool = Field(True, alias="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(300, alias="CACHE_TTL_SECONDS", gt=0)  # 5 minutes
    
    # External Services
    notification_service_url: Optional[str] = Field(None, alias="NOTIFICATION_SERVICE_URL")
    email_service_api_key: Optional[str] = Field(None, alias="EMAIL_SERVICE_API_KEY")
    
    # Monitoring Configuration
    metrics_enabled: bool = Field(True, alias="METRICS_ENABLED")
    tracing_enabled: bool = Field(False, alias="TRACING_ENABLED")
    tracing_endpoint: Optional[str] = Field(None, alias="TRACING_ENDPOINT")
    
    # Feature Flags
    feature_recommendations: bool = Field(True, alias="FEATURE_RECOMMENDATIONS")
    feature_analytics: bool = Field(True, alias="FEATURE_ANALYTICS")
    feature_bulk_operations: bool = Field(True, alias="FEATURE_BULK_OPERATIONS")
    
    # Request/Response Size and URL Length Limits
    max_request_size_bytes: int = Field(
        1048576,  # 1 MiB
        alias="MAX_REQUEST_SIZE_BYTES",
        description="Maximum request body size in bytes"
    )
    max_url_length: int = Field(
        2048,
        alias="MAX_URL_LENGTH", 
        description="Maximum URL length (path + query) in characters"
    )
    
    # Legacy field for backward compatibility
    max_request_body_bytes: int = Field(
        1048576,  # 1 MiB
        alias="MAX_REQUEST_BODY_BYTES",
        description="Maximum request body size in bytes (legacy)"
    )
    
    # Security Headers Configuration
    enable_hsts: bool = Field(
        False,
        alias="ENABLE_HSTS",
        description="Enable HSTS header (only in production with HTTPS)"
    )
    hsts_max_age: int = Field(
        63072000,  # 2 years
        alias="HSTS_MAX_AGE",
        description="HSTS max-age in seconds"
    )
    hsts_include_subdomains: bool = Field(
        True,
        alias="HSTS_INCLUDE_SUBDOMAINS"
    )
    hsts_preload: bool = Field(
        True,
        alias="HSTS_PRELOAD"
    )
    
    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from comma-separated string"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers from comma-separated string"""
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v, info):
        """Validate JWT secret key with production requirements"""
        if not v:
            return v  # Will be handled in model_post_init
        
        # Check against banned defaults - QA-002 fix
        banned_secrets = {
            "your-secret-key-change-in-production",
            "secret", 
            "dev",
            "development", 
            "test",
            "changeme",
            "default"
        }
        
        if v.lower() in banned_secrets:
            raise ValueError(f"JWT secret key is a banned default value and cannot be used in production")
        
        return v
    
    def model_post_init(self, __context):
        """Production validation after model initialization"""
        # Auto-generate JWT secret if not provided in development
        if not self.jwt_secret_key and self.is_development:
            import secrets
            self.jwt_secret_key = secrets.token_urlsafe(64)
            import logging
            logging.info("Generated ephemeral JWT secret for development")
        
        if self.environment == Environment.PRODUCTION:
            self._validate_production_config()
    
    def _validate_production_config(self):
        """Validate production-specific requirements"""
        errors = []
        
        # JWT Secret validation
        if not self.jwt_secret_key:
            errors.append("JWT_SECRET_KEY is required in production")
        elif len(self.jwt_secret_key) < 64:
            errors.append("JWT_SECRET_KEY must be at least 64 characters in production")
        
        # Database validation
        if not self.database_url:
            errors.append("DATABASE_URL is required in production")
        
        # Rate limiting backend validation
        if not self.rate_limit_backend_url and not self.disable_rate_limit_backend:
            errors.append(
                "RATE_LIMIT_BACKEND_URL is required in production, or set DISABLE_RATE_LIMIT_BACKEND=true"
            )
        
        # CORS validation
        if not self.cors_allowed_origins:
            errors.append("CORS_ALLOWED_ORIGINS must be configured in production")
        
        # Allowed hosts validation
        if not self.allowed_hosts:
            errors.append("ALLOWED_HOSTS must be configured in production")
        
        # Trusted proxy IPs validation for forwarded headers
        if not self.trusted_proxy_ips:
            import logging
            logging.warning(
                "TRUSTED_PROXY_IPS not configured. Forwarded headers will not be trusted."
            )
        
        if errors:
            error_msg = "Production configuration validation failed:\n" + "\n".join(f"- {err}" for err in errors)
            import logging
            logging.critical("Production startup blocked due to configuration errors")
            raise ValueError(error_msg)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def should_enforce_strict_validation(self) -> bool:
        """Determine if strict configuration validation should be enforced"""
        if self.strict_config_validation is not None:
            return self.strict_config_validation
        # Default: only enforce in production
        return self.environment == Environment.PRODUCTION
    
    @property
    def should_enable_docs(self) -> bool:
        """Determine if API docs should be enabled"""
        if self.enable_docs is not None:
            return self.enable_docs
        # Default: enable in development, disable in production
        return self.is_development
    
    @property
    def should_enable_hsts(self) -> bool:
        """Determine if HSTS should be enabled"""
        # Only enable HSTS in production (assumes HTTPS termination)
        return self.environment == Environment.PRODUCTION and self.enable_hsts
    

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_jwt_secret()
        # Only validate if in production or explicitly enabled
        if self.should_enforce_strict_validation:
            self._validate_production_security()
    
    def _setup_jwt_secret(self):
        """Setup JWT secret with environment-specific defaults"""
        if not self.jwt_secret_key:
            if self.should_enforce_strict_validation:
                # Strict mode: MUST have an explicit secret
                pass  # Will be handled in validation
            else:
                # Development: generate ephemeral key with warning
                self.jwt_secret_key = secrets.token_urlsafe(64)
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"⚠️  Using generated JWT secret for {self.environment} environment. "
                    f"Set JWT_SECRET_KEY environment variable for production."
                )
    
    def validate(self) -> None:
        """Validate configuration with aggregated error reporting"""
        if not self.should_enforce_strict_validation:
            return
        
        errors = []
        
        # JWT Secret validation
        if not self.jwt_secret_key:
            errors.append("JWT_SECRET_KEY must be configured")
        elif self.jwt_secret_key in self.BANNED_DEFAULT_SECRETS:
            errors.append("JWT_SECRET_KEY cannot be a default/banned value")
        elif len(self.jwt_secret_key) < 64:
            errors.append("JWT_SECRET_KEY must be at least 64 characters in production")
        
        # CORS validation  
        if not self.cors_allowed_origins or self.cors_allowed_origins.strip() == "":
            errors.append("CORS_ALLOWED_ORIGINS must be configured in production")
        elif self.cors_allowed_origins == "*" and self.cors_allow_credentials:
            errors.append("CORS wildcard origin cannot be used with credentials")
        
        # Host validation
        if not self.allowed_hosts:
            errors.append("ALLOWED_HOSTS must be configured in production")
        
        # Database validation
        if not self.database_url or self.database_url == "sqlite:///dev.db":
            errors.append("DATABASE_URL must be configured for production")
        
        # Numeric configuration validation
        if self.access_token_expire_minutes <= 0:
            errors.append("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        if self.database_pool_size <= 0:
            errors.append("DATABASE_POOL_SIZE must be positive")
        if self.database_max_overflow < 0:
            errors.append("DATABASE_MAX_OVERFLOW cannot be negative")
        
        if errors:
            error_msg = "Invalid configuration:\n" + "\n".join(f"- {err}" for err in errors)
            raise RuntimeError(error_msg)
    
    def _validate_production_security(self):
        """Legacy method - calls new validate method"""
        self.validate()
    
    @property
    def get_jwt_secret_key(self) -> str:
        """Get the JWT secret key securely"""
        if not self.jwt_secret_key:
            raise RuntimeError("JWT secret key not configured")
        return self.jwt_secret_key
    
    @property
    def get_jwt_previous_keys(self) -> List[str]:
        """Get previous JWT keys for token rotation support"""
        if not self.jwt_previous_secret_keys:
            return []
        return [key.strip() for key in self.jwt_previous_secret_keys.split(",") if key.strip()]
    
    @property  
    def get_rate_limiter_info(self) -> str:
        """Get rate limiter diagnostic info for startup logging"""
        try:
            # Test Redis connectivity
            import redis
            r = redis.from_url(self.rate_limit_backend_url, socket_timeout=1)
            r.ping()
            return f"Redis backend ({self.rate_limit_backend_url})"
        except:
            return "in-memory fallback (Redis unavailable)"
    
    @property
    def get_database_info(self) -> str:
        """Get database diagnostic info for startup logging"""
        if self.database_url:
            if "postgresql" in self.database_url:
                return "PostgreSQL"
            elif "sqlite" in self.database_url:
                return "SQLite" 
            else:
                return "Database configured"
        elif self.is_development:
            return "SQLite fallback (dev mode)"
        else:
            return "Not configured"

    def log_jwt_config(self):
        """Log JWT configuration status (without exposing secrets)"""
        logger = logging.getLogger(__name__)
        if self.jwt_secret_key:
            logger.info(f"JWT secret configured: ✅ (length: {len(self.jwt_secret_key)}, algorithm: {self.jwt_algorithm})")
        else:
            logger.warning("JWT secret not configured: ❌")
        
        if self.get_jwt_previous_keys:
            logger.info(f"JWT rotation keys configured: {len(self.get_jwt_previous_keys)} previous keys")

# Environment-specific configurations
class LocalSettings(Settings):
    """Local development settings"""
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG
    database_echo: bool = True
    reload: bool = True

class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

class StagingSettings(Settings):
    """Staging environment settings"""
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    cors_origins: List[str] = ["https://staging.scholarship-api.com"]
    rate_limit_enabled: bool = True

class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: LogLevel = LogLevel.WARNING
    reload: bool = False
    cors_origins: List[str] = ["https://scholarship-api.com"]
    rate_limit_enabled: bool = True
    tracing_enabled: bool = True
    enable_hsts: bool = True  # Enable HSTS in production

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "local").lower()
    
    settings_map = {
        "local": LocalSettings,
        "development": DevelopmentSettings,
        "staging": StagingSettings,
        "production": ProductionSettings
    }
    
    settings_class = settings_map.get(env, LocalSettings)
    return settings_class()

# Global settings instance
settings = get_settings()