"""
Environment-specific Configuration Management
Using pydantic-settings for type-safe configuration
"""

import os
from typing import List, Optional, Annotated
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
    
    # Server Configuration
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(5000, alias="PORT")
    reload: bool = Field(True, alias="RELOAD")
    
    # Security Configuration
    jwt_secret_key: str = Field("your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS Configuration - Environment-specific
    cors_allowed_origins: str = Field(
        default="",
        alias="CORS_ALLOWED_ORIGINS",
        description="Comma-separated list of allowed origins for production"
    )
    cors_allow_credentials: bool = Field(True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(["GET", "POST", "PUT", "DELETE", "OPTIONS"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(["*"], alias="CORS_ALLOW_HEADERS")
    
    @property
    def get_cors_origins(self) -> List[str]:
        """Get environment-appropriate CORS origins"""
        if self.environment == Environment.PRODUCTION:
            # In production, require explicit whitelist
            if self.cors_allowed_origins:
                return [origin.strip() for origin in self.cors_allowed_origins.split(",")]
            else:
                # Fail safe - log warning and return empty list to prevent wildcard
                import logging
                logging.warning("Production environment detected but no CORS_ALLOWED_ORIGINS configured")
                return []
        else:
            # Development/staging - allow localhost origins plus any specified
            dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"]
            if self.cors_allowed_origins:
                custom_origins = [origin.strip() for origin in self.cors_allowed_origins.split(",")]
                return dev_origins + custom_origins
            return ["*"]  # Fallback for development
    
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
    
    @property
    def get_rate_limit_per_minute(self) -> int:
        """Get environment-appropriate rate limit per minute"""
        if self.rate_limit_per_minute > 0:
            return self.rate_limit_per_minute
        
        # Default limits based on environment
        if self.environment == Environment.PRODUCTION:
            return 100
        else:  # Development/staging
            return 200
    
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