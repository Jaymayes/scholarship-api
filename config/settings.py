"""
Environment-specific Configuration Management
Using pydantic-settings for type-safe configuration
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
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
    environment: Environment = Field(default=Environment.LOCAL, env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    api_title: str = Field(default="Scholarship Discovery & Search API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    api_description: str = Field(
        default="A comprehensive API for scholarship discovery with advanced search and eligibility checking",
        env="API_DESCRIPTION"
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=5000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
    # Security Configuration
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Database Configuration
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_timeout: int = Field(default=5, env="REDIS_TIMEOUT")
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field(default="1000/hour", env="RATE_LIMIT_DEFAULT")
    rate_limit_public: str = Field(default="60/minute", env="RATE_LIMIT_PUBLIC")
    rate_limit_authenticated: str = Field(default="300/minute", env="RATE_LIMIT_AUTHENTICATED")
    rate_limit_admin: str = Field(default="1000/minute", env="RATE_LIMIT_ADMIN")
    
    # Logging Configuration
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Analytics Configuration
    analytics_enabled: bool = Field(default=True, env="ANALYTICS_ENABLED")
    analytics_retention_days: int = Field(default=90, env="ANALYTICS_RETENTION_DAYS")
    
    # Search Configuration
    search_default_limit: int = Field(default=20, env="SEARCH_DEFAULT_LIMIT")
    search_max_limit: int = Field(default=100, env="SEARCH_MAX_LIMIT")
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")  # 5 minutes
    
    # External Services
    notification_service_url: Optional[str] = Field(default=None, env="NOTIFICATION_SERVICE_URL")
    email_service_api_key: Optional[str] = Field(default=None, env="EMAIL_SERVICE_API_KEY")
    
    # Monitoring Configuration
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    tracing_enabled: bool = Field(default=False, env="TRACING_ENABLED")
    tracing_endpoint: Optional[str] = Field(default=None, env="TRACING_ENDPOINT")
    
    # Feature Flags
    feature_recommendations: bool = Field(default=True, env="FEATURE_RECOMMENDATIONS")
    feature_analytics: bool = Field(default=True, env="FEATURE_ANALYTICS")
    feature_bulk_operations: bool = Field(default=True, env="FEATURE_BULK_OPERATIONS")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("cors_allow_methods", pre=True)
    def parse_cors_methods(cls, v):
        """Parse CORS methods from comma-separated string"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @validator("cors_allow_headers", pre=True)
    def parse_cors_headers(cls, v):
        """Parse CORS headers from comma-separated string"""
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v, values):
        """Validate JWT secret key in production"""
        if values.get("environment") == Environment.PRODUCTION and v == "your-secret-key-change-in-production":
            raise ValueError("JWT secret key must be changed in production")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment in [Environment.LOCAL, Environment.DEVELOPMENT]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

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