# Production Deployment Guide

## Overview

This FastAPI Scholarship Discovery & Search API is now production-ready with enterprise-grade containerization, security hardening, and comprehensive deployment validation.

## 🚀 Quick Start

### 1. Environment Configuration

Copy the example environment file and configure for production:

```bash
cp .env.example .env
```

**Required Production Settings:**

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database (Required)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Security (Required - Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))")
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-at-least-64-characters-long

# Host Security (Required)
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
TRUSTED_PROXY_IPS=172.16.0.0/12,192.168.0.0/16

# CORS (Required)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Rate Limiting (Required)
RATE_LIMIT_BACKEND_URL=redis://localhost:6379/0
```

### 2. Production Validation

Run the pre-deployment checklist:

```bash
python scripts/pre_deploy_checklist.py
```

### 3. Container Deployment

#### Using Docker Compose (Recommended)

```bash
# Start the full stack
docker-compose up -d

# Check health
curl http://localhost:8000/healthz
```

#### Using Docker

```bash
# Build production image
docker build -t scholarship-api .

# Run with environment
docker run -d \
  --name scholarship-api \
  -p 8000:8000 \
  --env-file .env \
  scholarship-api
```

### 4. Deployment Verification

```bash
# Verify deployment
python scripts/deployment_verification.py

# Check specific endpoint
API_BASE_URL=http://localhost:8000 python scripts/deployment_verification.py
```

## 🏗️ Architecture

### Container Stack

- **Multi-stage Dockerfile**: Optimized build with separate builder and runtime stages
- **Non-root execution**: Security-hardened container with dedicated user
- **Health checks**: Built-in container health monitoring
- **Graceful shutdown**: Proper signal handling and resource cleanup

### Production Middleware

1. **DocsProtectionMiddleware**: Blocks API documentation in production
2. **TrustedHostMiddleware**: Validates Host header against whitelist
3. **ForwardedHeadersMiddleware**: Safely processes X-Forwarded-* headers
4. **DatabaseSessionMiddleware**: Production-grade database connection management
5. **SecurityHeadersMiddleware**: Comprehensive security headers

### Security Features

- **Environment-aware validation**: Strict production requirements
- **JWT secret validation**: Rejects weak/default secrets
- **Host header protection**: Prevents Host header attacks
- **CORS enforcement**: Strict origin validation in production
- **Rate limiting**: Redis-backed with fallback support
- **Security headers**: HSTS, CSP, XSS protection
- **Request validation**: Size limits and input sanitization

## 🔧 Configuration

### Environment-Specific Behavior

| Setting | Development | Production |
|---------|-------------|------------|
| Debug Mode | Enabled | Disabled |
| API Docs | Enabled | Disabled (configurable) |
| CORS | Wildcard allowed | Strict whitelist required |
| JWT Secret | Auto-generated | Must be provided |
| Rate Limiting | In-memory fallback | Redis required |
| Security Headers | Basic | Full hardening |

### Health Endpoints

- **`/healthz`**: Liveness probe (application running)
- **`/health/services`**: Readiness probe (dependencies available)
- **`/health/database`**: Database connectivity check

## 🚦 CI/CD Pipeline

### GitHub Actions Workflow

The included `.github/workflows/ci-cd.yml` provides:

1. **Lint and Test**: Ruff, mypy, pytest
2. **Security Scan**: Bandit, Safety
3. **Container Build**: Multi-stage Docker build
4. **Deployment**: Automated staging/production deployment

### Pipeline Stages

```mermaid
graph LR
    A[Code Push] --> B[Lint & Test]
    B --> C[Security Scan] 
    C --> D[Build Container]
    D --> E[Deploy Staging]
    E --> F[Deploy Production]
```

## 📊 Monitoring

### Metrics

- **Prometheus endpoint**: `/metrics`
- **Request metrics**: Latency, throughput, error rates
- **Application metrics**: Database connections, rate limiting

### Observability

- **Structured logging**: JSON format with trace IDs
- **Request tracing**: OpenTelemetry integration
- **Error tracking**: Sentry support (optional)

## 🔒 Security Hardening

### Production Validation

The application enforces these requirements in production:

1. **JWT Secret**: Minimum 64 characters, no defaults
2. **Database**: PostgreSQL connection required
3. **CORS**: Explicit origin whitelist (no wildcards)
4. **Hosts**: Allowed hosts must be configured
5. **Rate Limiting**: Redis backend or explicit disable
6. **Documentation**: Disabled by default

### Security Headers

```http
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

## 🚢 Deployment Options

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scholarship-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scholarship-api
  template:
    spec:
      containers:
      - name: scholarship-api
        image: scholarship-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
        readinessProbe:
          httpGet:
            path: /health/services
            port: 8000
```

### Docker Swarm

```yaml
version: '3.8'
services:
  api:
    image: scholarship-api:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔍 Troubleshooting

### Common Issues

1. **Startup fails with validation errors**
   ```bash
   # Check configuration
   python scripts/pre_deploy_checklist.py
   ```

2. **Database connection issues**
   ```bash
   # Test database connectivity
   curl http://localhost:8000/health/database
   ```

3. **Rate limiting not working**
   ```bash
   # Check Redis connectivity
   redis-cli ping
   ```

### Debug Endpoints

- **`/_debug/config`**: Configuration diagnostics (development only)
- **`/health/services`**: Detailed service status

## 📋 Pre-Deployment Checklist

- [ ] Environment set to `production`
- [ ] Debug mode disabled
- [ ] JWT secret configured (≥64 chars)
- [ ] Database URL configured
- [ ] CORS origins whitelisted
- [ ] Allowed hosts configured
- [ ] Rate limiting backend available
- [ ] API docs disabled (recommended)
- [ ] Security headers enabled
- [ ] Container builds successfully
- [ ] Health checks pass
- [ ] Deployment verification passes

## 🎯 Performance Tuning

### Gunicorn Configuration

```python
# gunicorn_conf.py
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
graceful_timeout = 30
max_requests = 2000
max_requests_jitter = 200
```

### Database Optimization

- Connection pooling: 5 connections + 10 overflow
- Pre-ping enabled for connection validation
- Connection recycling every 5 minutes

### Redis Configuration

- Connection pooling for rate limiting
- Graceful fallback to in-memory mode
- Automatic retry logic

## 📖 Additional Resources

- [API Documentation](http://localhost:8000/docs) (development only)
- [Security Best Practices](FINAL_SECURITY_REPORT.md)
- [QA Analysis](COMPREHENSIVE_QA_ANALYSIS_REPORT.md)
- [Environment Configuration](.env.example)