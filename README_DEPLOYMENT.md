# Deployment Guide - Replit Deployment

## Overview

This FastAPI Scholarship Discovery & Search API is deployment-ready for Replit Deployments with proper health checks, port binding, and production security configurations.

## Required Environment Variables

Set these variables in Replit Deployment environment settings:

### Production Environment
```bash
# Core Configuration
ENVIRONMENT=production
PORT=<will_be_set_by_deployment>  # Replit sets this automatically

# Security (REQUIRED for production)
JWT_SECRET_KEY=<generate_strong_64+_character_secret>
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://api.your-domain.com
ALLOWED_HOSTS=your-app-name.your-username.replit.app,your-custom-domain.com

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:port/database

# Rate Limiting (RECOMMENDED)
RATE_LIMIT_BACKEND_URL=redis://your-redis-host:6379/0

# Optional Security Enhancements
TRUSTED_PROXY_IPS=["127.0.0.1","::1"]
```

### Environment Variable Details

- **`ENVIRONMENT=production`**: Enables strict security validation and production optimizations
- **`JWT_SECRET_KEY`**: Must be 64+ characters, cryptographically secure random string
- **`CORS_ALLOWED_ORIGINS`**: Comma-separated list of allowed frontend domains (NO wildcards in production)
- **`ALLOWED_HOSTS`**: Comma-separated list of allowed host headers for security
- **`DATABASE_URL`**: PostgreSQL connection string for persistent data storage
- **`RATE_LIMIT_BACKEND_URL`**: Redis URL for distributed rate limiting (falls back to in-memory if unavailable)

## Deployment Configuration

### Start Command
```bash
./start.sh
```

**Alternative (if script not preferred):**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
```

### Health Check Configuration

| Setting | Value |
|---------|--------|
| **Health Check Path** | `/healthz` (preferred) or `/health` |
| **Method** | `GET` |
| **Expected Status** | `200 OK` |
| **Timeout** | `10 seconds` |
| **Interval** | `30 seconds` |
| **Response Format** | `{"status": "healthy"}` |

### Port Configuration

- **Development**: Uses `PORT=5000` (Replit default)
- **Production Deployment**: Uses `$PORT` environment variable (set automatically by Replit)
- **Binding**: Always binds to `0.0.0.0` for accessibility
- **Proxy Headers**: Enabled with `--proxy-headers` and `--forwarded-allow-ips="*"`

## Security Features

### Production Security Controls
- **CORS Whitelist**: Strict origin validation (no wildcards with credentials)
- **JWT Authentication**: Required for protected endpoints
- **Rate Limiting**: Configurable per-minute limits with Redis backend
- **Request Size Limits**: Body (1MB) and URL (2KB) size restrictions
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Trusted Host Validation**: Prevents Host header attacks

### Development vs Production
- **Development**: Flexible CORS, wildcard origins allowed, debug endpoints enabled
- **Production**: Strict validation, explicit whitelists required, debug endpoints disabled

## API Endpoints

### Core Endpoints
- **Root**: `GET /` - API information and navigation
- **Health Check**: `GET /healthz` - Minimal health probe (deployment preferred)
- **Extended Health**: `GET /health` - Health check with trace ID
- **API Documentation**: `GET /docs` - OpenAPI/Swagger UI
- **Search**: `GET /api/v1/search?q=<query>` - Scholarship search

### Health Check Responses

**`/healthz` (Deployment Health Check):**
```json
{"status": "healthy"}
```

**`/health` (Extended Health Check):**
```json
{
  "status": "healthy",
  "trace_id": "uuid4-string"
}
```

**`/` (Root API Info):**
```json
{
  "status": "active",
  "message": "Scholarship Discovery & Search API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "search": "/api/v1/search?q=<query>",
    "documentation": "/docs"
  }
}
```

## Verification Commands

After successful deployment, verify with these commands:

```bash
# Set your deployment URL
DEPLOY_URL="https://your-app.your-username.replit.app"

# Health Check
curl -si "$DEPLOY_URL/healthz"
# Expected: HTTP/1.1 200 OK

# Root Endpoint
curl -si "$DEPLOY_URL/"
# Expected: HTTP/1.1 200 OK with JSON

# CORS Preflight (replace with your frontend domain)
curl -si -X OPTIONS "$DEPLOY_URL/api/v1/search" \
  -H "Origin: https://your-frontend.com" \
  -H "Access-Control-Request-Method: GET"
# Expected: 200 OK with Access-Control-Allow-Origin header

# Search Functionality
curl -si "$DEPLOY_URL/api/v1/search?q=engineering"
# Expected: 200 OK with scholarship results
```

## Troubleshooting

### Common Deployment Issues

1. **Health Check Fails**: Ensure `/healthz` returns 200 OK
2. **App Won't Start**: Check start command uses `uvicorn main:app`
3. **CORS Errors**: Verify `CORS_ALLOWED_ORIGINS` includes your frontend domain
4. **Database Errors**: Confirm `DATABASE_URL` is set and accessible
5. **Port Binding Issues**: Ensure start command uses `--port $PORT`

### Debug Information

In development, access `/_debug/config` for sanitized configuration info:
```bash
curl -s "http://localhost:5000/_debug/config" | jq
```

**Note**: Debug endpoint is disabled in production for security.

## Security Best Practices

1. **JWT Secret**: Use cryptographically secure random 64+ character string
2. **CORS Origins**: Never use wildcards (`*`) in production with credentials
3. **HTTPS Only**: Ensure deployment serves over HTTPS (handled by Replit)
4. **Environment Secrets**: Store all secrets in deployment environment variables
5. **Rate Limiting**: Configure Redis backend for production rate limiting
6. **Host Validation**: Include all legitimate domains in `ALLOWED_HOSTS`

## Support

For deployment issues:
1. Check Replit Deployment logs for startup errors
2. Verify all required environment variables are set
3. Test health endpoints return 200 OK
4. Confirm start command is correct
5. Review CORS and allowed hosts configuration