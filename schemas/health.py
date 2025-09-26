"""
Pydantic models for health check endpoints - QA-006 fix
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ServiceStatus(str, Enum):
    """Individual service status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"
    CONFIGURED = "configured"

class BasicHealthResponse(BaseModel):
    """Basic health check response"""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="Health status")
    timestamp: int = Field(description="Unix timestamp")
    environment: str | None = Field(None, description="Environment name")

class DatabaseHealthResponse(BaseModel):
    """Database health check response"""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="Health status")
    database: str = Field(description="Database connection status")
    type: str | None = Field(None, description="Database type")
    timestamp: int = Field(description="Unix timestamp")
    note: str | None = Field(None, description="Additional notes")

class ServiceInfo(BaseModel):
    """Individual service information"""
    model_config = ConfigDict(extra="forbid")

    status: ServiceStatus = Field(description="Service status")
    backend: str | None = Field(None, description="Backend information")
    type: str | None = Field(None, description="Service type")
    note: str | None = Field(None, description="Additional notes")
    error: str | None = Field(None, description="Error message if unhealthy")

class ServicesHealthResponse(BaseModel):
    """Comprehensive services health check response"""
    model_config = ConfigDict(extra="forbid")

    status: HealthStatus = Field(description="Overall health status")
    services: dict[str, ServiceInfo] = Field(description="Individual service statuses")
    timestamp: int = Field(description="Unix timestamp")
    environment: str = Field(description="Environment name")

# Debug endpoint models (development only)
class CorsConfig(BaseModel):
    """CORS configuration info"""
    origins_count: int | str = Field(description="Number of origins or 'wildcard'")
    wildcard_enabled: bool = Field(description="Whether wildcard is enabled")
    replit_origin_detected: bool = Field(description="Whether Replit origin detected")

class RateLimitConfig(BaseModel):
    """Rate limiting configuration info"""
    backend_type: str = Field(description="Rate limit backend type")
    per_minute_limit: int = Field(description="Rate limit per minute")
    enabled: bool = Field(description="Whether rate limiting is enabled")

class DatabaseConfig(BaseModel):
    """Database configuration info"""
    type: str = Field(description="Database type")
    configured: bool = Field(description="Whether database is configured")

class JwtConfig(BaseModel):
    """JWT configuration info"""
    algorithm: str = Field(description="JWT algorithm")
    secret_configured: bool = Field(description="Whether JWT secret is configured")
    secret_length: int = Field(description="JWT secret length")

class FeatureConfig(BaseModel):
    """Feature flags configuration"""
    analytics: bool = Field(description="Analytics enabled")
    metrics: bool = Field(description="Metrics enabled")
    tracing: bool = Field(description="Tracing enabled")

class ReplitEnvConfig(BaseModel):
    """Replit environment configuration"""
    repl_id: str = Field(description="Repl ID")
    repl_owner: str = Field(description="Repl owner")
    port: str = Field(description="Port configuration")

class DebugConfigResponse(BaseModel):
    """Debug configuration response (development only)"""
    model_config = ConfigDict(extra="forbid")

    environment: str = Field(description="Current environment")
    debug_mode: bool = Field(description="Debug mode enabled")
    cors: CorsConfig = Field(description="CORS configuration")
    rate_limiting: RateLimitConfig = Field(description="Rate limiting configuration")
    database: DatabaseConfig = Field(description="Database configuration")
    jwt: JwtConfig = Field(description="JWT configuration")
    features: FeatureConfig = Field(description="Feature flags")
    replit_env: ReplitEnvConfig = Field(description="Replit environment")
