"""
Environment-specific Configuration Management
Using pydantic-settings for type-safe configuration
"""

import os
import secrets
import logging
from typing import List, Optional, Annotated, Set
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

class Environment(str, Enum):
    LOCAL = "local"
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
    """Application settings with environment-specific overrides"""
    
    # Environment
    environment: Environment = Field(Environment.LOCAL, alias="ENVIRONMENT")
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
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")), alias="PORT")  # Replit dynamic port
    reload: bool = Field(True, alias="RELOAD")
    
    # Security Configuration - JWT
    jwt_secret_key: Optional[str] = Field(None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_previous_secret_keys: str = Field("", alias="JWT_PREVIOUS_SECRET_KEYS")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Banned default secrets that cannot be used in production
    BANNED_DEFAULT_SECRETS: Set[str] = {
        "your-secret-key-change-in-production",
        "secret", 
        "dev",
        "development",
        "test",
        "changeme",
        "default"
    }
    
    # CORS Configuration - Environment-specific
    cors_allowed_origins: str = Field(
        default="",
        alias="CORS_ALLOWED_ORIGINS",
        description="Comma-separated list of allowed origins for production"
    )
    cors_allow_credentials: bool = Field(True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        ["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
        alias="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(
        ["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization"],
        alias="CORS_ALLOW_HEADERS"
    )
    cors_max_age: int = Field(600, alias="CORS_MAX_AGE")  # 10 minutes
    
    @property
    def get_cors_origins(self) -> List[str]:
        """Get environment-appropriate CORS origins with production safety"""
        if self.environment == Environment.PRODUCTION:
            # Production: MUST have explicit whitelist, no wildcards allowed
            if not self.cors_allowed_origins:
                import logging
                logging.critical(
                    "PRODUCTION SECURITY ERROR: CORS_ALLOWED_ORIGINS not configured. "
                    "This could allow any origin to access your API!"
                )
                # Fail safe: return empty list to block all CORS requests
                return []
            
            origins = [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
            if "*" in origins:
                import logging
                logging.critical(
                    "PRODUCTION SECURITY ERROR: Wildcard (*) origin detected in production. "
                    "This is a security vulnerability!"
                )
                # Remove wildcard for production safety
                origins = [o for o in origins if o != "*"]
            
            return origins
        else:
            # Development/staging: Allow localhost + Replit origins + custom origins
            dev_origins = [
                "http://localhost:3000", 
                "http://127.0.0.1:3000", 
                "http://localhost:5000",
                "http://localhost:8000",
                # Replit preview origins - development only
                "https://*.replit.dev",
                "https://*.repl.co"
            ]
            
            # Add dynamic Replit origin detection
            replit_id = os.getenv("REPL_ID")
            replit_owner = os.getenv("REPL_OWNER") 
            if replit_id and replit_owner:
                replit_origin = f"https://{replit_id}.{replit_owner}.repl.co"
                dev_origins.append(replit_origin)
                
            if self.cors_allowed_origins:
                custom_origins = [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
                return dev_origins + custom_origins
            return ["*"]  # Only allowed in development
    
    @property
    def get_cors_config(self) -> dict:
        """Get complete CORS configuration"""
        return {
            "allow_origins": self.get_cors_origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers,
            "max_age": self.cors_max_age
        }
    
    # Database Configuration
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    database_echo: bool = Field(False, alias="DATABASE_ECHO")
    database_pool_size: int = Field(5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(10, alias="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")
    redis_timeout: int = Field(5, alias="REDIS_TIMEOUT")
    
    # Rate Limiting Configuration - Environment-specific
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")
    rate_limit_backend_url: str = Field("redis://localhost:6379/0", alias="RATE_LIMIT_BACKEND_URL")
    rate_limit_per_minute: int = Field(0, alias="RATE_LIMIT_PER_MINUTE")  # 0 = use defaults
    
    # Healthcheck endpoint exemption
    rate_limit_exempt_paths: List[str] = Field(
        ["/health", "/readiness", "/metrics"],
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
            Environment.LOCAL: 300
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
        if self.environment in [Environment.LOCAL, Environment.DEVELOPMENT]:
            return f"{base_limit * 2}/minute"
        return self.rate_limit_search
    
    @property
    def get_eligibility_rate_limit(self) -> str:
        """Get environment-appropriate eligibility rate limit"""
        base_limit = int(self.rate_limit_eligibility.split('/')[0])
        if self.environment in [Environment.LOCAL, Environment.DEVELOPMENT]:
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
    
    # Analytics Configuration
    analytics_enabled: bool = Field(True, alias="ANALYTICS_ENABLED")
    analytics_retention_days: int = Field(90, alias="ANALYTICS_RETENTION_DAYS")
    
    # Search Configuration
    search_default_limit: int = Field(20, alias="SEARCH_DEFAULT_LIMIT")
    search_max_limit: int = Field(100, alias="SEARCH_MAX_LIMIT")
    
    # Cache Configuration
    cache_enabled: bool = Field(True, alias="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(300, alias="CACHE_TTL_SECONDS")  # 5 minutes
    
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
        """Validate JWT secret key in production"""
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment in [Environment.LOCAL, Environment.DEVELOPMENT]
    
    @property
    def should_enable_hsts(self) -> bool:
        """Check if HSTS should be enabled based on environment"""
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
        self._validate_production_security()
    
    def _setup_jwt_secret(self):
        """Setup JWT secret with environment-specific defaults"""
        if not self.jwt_secret_key:
            if self.environment == Environment.PRODUCTION:
                # Production MUST have an explicit secret
                pass  # Will be handled in validation
            else:
                # Development: generate ephemeral key
                self.jwt_secret_key = secrets.token_urlsafe(64)
                logger = logging.getLogger(__name__)
                logger.info(f"Generated ephemeral JWT secret for {self.environment} (length: {len(self.jwt_secret_key)})")
    
    def _validate_production_security(self):
        """Validate security configuration for production environment"""
        if self.environment == Environment.PRODUCTION:
            if not self.jwt_secret_key:
                raise RuntimeError(
                    "PRODUCTION SECURITY ERROR: JWT_SECRET_KEY environment variable is required in production. "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            
            if self.jwt_secret_key in self.BANNED_DEFAULT_SECRETS:
                raise RuntimeError(
                    f"PRODUCTION SECURITY ERROR: JWT secret cannot be a default/banned value in production. "
                    f"Current secret matches banned pattern. Generate a secure key with: "
                    f"python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            
            if len(self.jwt_secret_key) < 32:
                raise RuntimeError(
                    "PRODUCTION SECURITY ERROR: JWT secret must be at least 32 characters long in production. "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
    
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