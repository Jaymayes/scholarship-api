# API Security Guide

## Overview
This document outlines the security controls and authentication mechanisms implemented in the Scholarship Discovery & Search API.

## Authentication

### JWT Bearer Token Authentication
- **Endpoint**: `POST /api/v1/auth/login-simple`
- **Method**: JSON-based login
- **Token Type**: JWT (JSON Web Tokens)
- **Expiration**: 30 minutes (configurable)

### Test User Accounts
```
Admin User:
- Username: admin
- Password: admin123
- Roles: admin
- Scopes: scholarships:read, scholarships:write, analytics:read, analytics:write

Partner User:
- Username: partner  
- Password: partner123
- Roles: partner
- Scopes: scholarships:read, scholarships:write, analytics:read

Read-Only User:
- Username: readonly
- Password: readonly123  
- Roles: read-only
- Scopes: scholarships:read
```

## Authorization

### Role-Based Access Control (RBAC)
- **Admin**: Full access to all endpoints
- **Partner**: Read/write access to scholarships, read access to analytics
- **Read-Only**: Read-only access to scholarships

### Scope-Based Permissions
- `scholarships:read` - View scholarship data
- `scholarships:write` - Create/update scholarship data  
- `analytics:read` - View analytics data
- `analytics:write` - Modify analytics data

## Rate Limiting

### Public Endpoints
- **Limit**: 60 requests per minute
- **Scope**: IP-based for unauthenticated users

### Authenticated Endpoints  
- **Limit**: 300 requests per minute
- **Scope**: User-based for authenticated users

### Admin Endpoints
- **Limit**: 1000 requests per minute
- **Scope**: Admin users only

### Special Operations
- **Bulk Operations**: 10 requests per minute
- **Search Operations**: 120 requests per minute

## Error Handling

### Standardized Error Responses
All errors return a standardized format:
```json
{
  "trace_id": "uuid",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "timestamp": 1629123456.789
  },
  "status": 400
}
```

### Error Codes
- `AUTHENTICATION_REQUIRED` (401) - Missing or invalid authentication
- `INSUFFICIENT_PERMISSIONS` (403) - Valid auth but insufficient permissions
- `RATE_LIMIT_EXCEEDED` (429) - Rate limit exceeded
- `VALIDATION_ERROR` (422) - Request validation failed
- `NOT_FOUND` (404) - Resource not found
- `INTERNAL_ERROR` (500) - Server error

## Security Headers

### Trace ID
- Every response includes `X-Trace-ID` header for request tracking
- Useful for debugging and security monitoring

### Rate Limit Headers
When rate limits are approached or exceeded:
- `Retry-After`: Seconds until retry allowed
- `X-RateLimit-Limit`: Current rate limit
- `X-RateLimit-Reset`: When limit resets

## Usage Examples

### Login and Token Usage
```bash
# Login to get token
TOKEN=$(curl -s -X POST "http://localhost:5000/api/v1/auth/login-simple" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  jq -r .access_token)

# Use token for authenticated requests
curl "http://localhost:5000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Access protected scholarship endpoints
curl "http://localhost:5000/api/v1/scholarships" \
  -H "Authorization: Bearer $TOKEN"
```

### Error Handling Example
```bash
# Attempt access without authentication
curl "http://localhost:5000/api/v1/auth/me"
# Returns 401 with standardized error format
```

## Development vs Production

### Development Settings
- Permissive CORS origins (`["*"]`)
- Debug mode enabled
- Lower rate limits for testing
- Mock user database

### Production Considerations
- Configure strict CORS origins
- Set secure JWT secret key via `JWT_SECRET_KEY` environment variable
- Configure Redis for distributed rate limiting
- Implement real user database
- Enable comprehensive logging and monitoring
- Use HTTPS/TLS encryption

## Environment Variables

### Required for Production
```bash
ENVIRONMENT=production
JWT_SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
```

### Optional Configuration
```bash
# API Configuration
API_TITLE="Your API Title"
API_VERSION="1.0.0"
HOST=0.0.0.0
PORT=5000

# CORS Configuration  
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_PUBLIC=100/minute
RATE_LIMIT_AUTHENTICATED=500/minute
RATE_LIMIT_ADMIN=2000/minute

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Security Checklist

### ✅ Implemented
- [x] JWT-based authentication
- [x] Role-based access control (RBAC)
- [x] Scope-based permissions
- [x] Rate limiting with user/IP differentiation
- [x] Standardized error handling
- [x] Request tracing for security monitoring
- [x] Input validation
- [x] CORS configuration

### 🔄 Recommended for Production
- [ ] Replace mock user database with real authentication system
- [ ] Implement password hashing with strong algorithms
- [ ] Add refresh token mechanism
- [ ] Configure secure session management
- [ ] Implement comprehensive audit logging
- [ ] Add API versioning strategy
- [ ] Set up monitoring and alerting
- [ ] Configure HTTPS/TLS encryption
- [ ] Implement IP whitelisting for admin endpoints
- [ ] Add request/response sanitization

## Support

For security issues or questions, refer to the API documentation at `/docs` or contact the development team.