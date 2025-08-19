# Production Deployment Guide - Agent Bridge Integration

## Pre-Deployment Checklist

### ✅ Environment Configuration

**Required Environment Variables:**
```bash
# Command Center Integration
COMMAND_CENTER_URL=https://auto-com-center-jamarrlmayes.replit.app
SHARED_SECRET=<rotate-via-secrets-manager>
AGENT_BASE_URL=https://scholarship-api-jamarrlmayes.replit.app

# JWT Security Configuration
JWT_ISSUER=auto-com-center
JWT_AUDIENCE=scholar-sync-agents

# Production Security
ENVIRONMENT=production
CORS_ALLOWED_ORIGINS=https://auto-com-center-jamarrlmayes.replit.app
PUBLIC_READ_ENDPOINTS=false  # Require auth for all endpoints

# Optional Enhancements
REDIS_URL=redis://production-redis:6379  # For production rate limiting
DATABASE_URL=postgresql://production-db  # Production database
```

### ✅ Security Hardening

**Network Security:**
- [ ] Allowlist Command Center egress IPs to Agent Bridge URL
- [ ] Enforce HTTPS/TLS with HSTS headers
- [ ] Set minimum TLS version 1.2+
- [ ] Configure proper firewall rules

**JWT Security:**
- [ ] Implement jti cache for replay protection (production only)
- [ ] Set up secret rotation plan with overlapping acceptance windows
- [ ] Consider migrating to JWKS (RS256/ES256) for enhanced security
- [ ] Enable strict claim validation (exp, nbf, iat, jti, iss, aud)

**Rate Limiting:**
- [ ] Configure Redis backend for production rate limiting
- [ ] Set per-issuer and per-IP limits on `/agent/*` endpoints
- [ ] Enable idempotency keys for `POST /agent/task`

### ✅ Monitoring & Observability

**SLOs and Alerts:**
```yaml
# Service Level Objectives
agent_availability: 99.9%
agent_health_p95: < 200ms
agent_capabilities_p95: < 300ms  
task_enqueue_p95: < 500ms
task_acceptance_rate: > 99%

# Critical Alerts
- JWT authentication failure rate > 1%
- Task failure rate > 1%
- Agent health check failures
- Command Center unreachability > 2 minutes
- Task queue depth > 100
- P95 latency above thresholds
```

**Structured Logging:**
```json
{
  "timestamp": "2025-08-19T12:00:00Z",
  "level": "INFO",
  "task_id": "task-12345",
  "correlation_id": "corr-67890", 
  "action": "scholarship_api.search",
  "status": "succeeded",
  "duration_ms": 245,
  "requested_by": "command_center",
  "agent_id": "scholarship_api"
}
```

**Dashboards:**
- Tasks received/succeeded/failed per minute
- Task execution latency (p50, p95, p99)
- In-flight task count
- JWT authentication success/failure rates
- Agent health status across instances
- Event delivery success rates to Command Center

## Deployment Scenarios

### Scenario 1: Canary Deployment

**Phase 1: Limited Orchestration (5% traffic)**
```bash
# Enable orchestration for small subset
ORCHESTRATION_ENABLED=true
ORCHESTRATION_TRAFFIC_PERCENTAGE=5
COMMAND_CENTER_URL=https://staging-acc.replit.app  # Start with staging
```

**Validation:**
- Monitor error rates < 0.1%
- P95 latency within thresholds
- No impact on core API performance
- Successful task execution and callbacks

**Phase 2: Production Ramp (25% → 50% → 100%)**
- Gradual traffic increase with monitoring at each step
- Switch to production Command Center URL
- Full feature enablement

### Scenario 2: Blue-Green Deployment

**Blue Environment (Current):**
- All existing API traffic
- No orchestration features

**Green Environment (New):**
- Full Agent Bridge integration
- Command Center connectivity
- Production configuration

**Cutover Process:**
1. Deploy green environment with Agent Bridge
2. Test orchestration endpoints in isolation
3. Switch DNS/load balancer to green
4. Monitor for 30 minutes
5. Decommission blue environment

### Scenario 3: Progressive Enhancement

**Step 1: Deploy with Orchestration Disabled**
```bash
# Orchestration off by default
COMMAND_CENTER_URL=""  # Empty disables orchestration
SHARED_SECRET=""
```

**Step 2: Enable Health and Capabilities**
```bash
# Enable discovery endpoints only
AGENT_HEALTH_ENABLED=true
AGENT_CAPABILITIES_ENABLED=true
```

**Step 3: Enable Full Orchestration**
```bash
# Full Command Center integration
COMMAND_CENTER_URL=https://auto-com-center-jamarrlmayes.replit.app
SHARED_SECRET=<production-secret>
```

## Production Testing

### Smoke Tests (Post-Deploy)

**Quick Validation Script:**
```bash
#!/bin/bash
BASE_URL="https://scholarship-api-jamarrlmayes.replit.app"
JWT_TOKEN="<production-jwt-token>"

# Test 1: Health Check
curl -f "$BASE_URL/agent/health" || exit 1

# Test 2: Capabilities (with auth)
curl -f -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/agent/capabilities" || exit 1

# Test 3: Core API Unchanged  
curl -f "$BASE_URL/api/v1/search?q=test&limit=1" || exit 1

# Test 4: Task Submission
curl -f -X POST "$BASE_URL/agent/task" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"smoke-test","action":"scholarship_api.search","payload":{"query":"test","filters":{},"pagination":{"page":1,"size":1}},"reply_to":"https://example.com/callback","trace_id":"smoke-trace","requested_by":"deployment_test"}' || exit 1

echo "✅ Smoke tests passed"
```

### Load Testing

**Newman CI Integration:**
```bash
# Run Postman collection via Newman
newman run production_postman_collection.json \
  --environment production_environment.json \
  --reporters cli,junit \
  --timeout-request 30000 \
  --bail
```

**k6 Production Test:**
```bash
# Run production load test
SHARED_SECRET="$PRODUCTION_SECRET" \
BASE_URL="https://scholarship-api-jamarrlmayes.replit.app" \
k6 run k6_production_test.js \
  --out json=results.json
```

## Rollback Strategy

### Quick Rollback (Emergency)

**Option 1: Disable Orchestration**
```bash
# Emergency disable via environment variable
COMMAND_CENTER_URL=""
SHARED_SECRET=""
# Restart application
```

**Option 2: Traffic Routing**
```bash
# Route traffic back to previous version
# Update load balancer or DNS
```

**Option 3: Container Rollback**
```bash
# Rollback to previous container image
# Kubernetes example:
kubectl rollout undo deployment/scholarship-api
```

### Graceful Rollback

1. **Drain in-flight tasks** (wait for completion)
2. **Disable new task acceptance** 
3. **Switch traffic to previous version**
4. **Verify core API functionality**
5. **Monitor for stability**

## Operational Procedures

### Secret Rotation

**Shared Secret Rotation:**
```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update both services with overlapping acceptance
# Command Center: Accept both old and new
# Agent Bridge: Accept both old and new

# 3. Wait for propagation (5 minutes)
sleep 300

# 4. Switch Command Center to issue new tokens only
# 5. Wait for old tokens to expire (5 minutes)  
sleep 300

# 6. Remove old secret from both services
```

### Scaling Considerations

**Horizontal Scaling:**
- Agent Bridge is stateless (scales horizontally)
- No shared state between instances
- Load balancer health checks on `/agent/health`

**Vertical Scaling:**
- Monitor memory usage for task queues
- CPU utilization during task execution
- Database connection pool sizing

## Troubleshooting Guide

### Common Issues

**JWT Authentication Failures:**
```bash
# Check token claims
echo "$JWT_TOKEN" | base64 -d | jq .

# Verify shared secret configuration
curl -v -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/agent/capabilities"
```

**Task Execution Failures:**
```bash
# Check application logs
grep "task_id" application.log | grep "ERROR"

# Monitor task queue depth
curl "$BASE_URL/metrics" | grep task_queue_depth
```

**Command Center Connectivity:**
```bash
# Test outbound connectivity
curl -v "$COMMAND_CENTER_URL/health"

# Check DNS resolution
nslookup auto-com-center-jamarrlmayes.replit.app
```

**Performance Issues:**
```bash
# Check response times
curl -w "@curl-format.txt" "$BASE_URL/agent/health"

# Monitor resource usage
top -p $(pgrep -f "python.*main.py")
```

### Health Check Integration

**Load Balancer Configuration:**
```yaml
health_check:
  path: /agent/health
  interval: 10s
  timeout: 5s
  healthy_threshold: 2
  unhealthy_threshold: 3
```

**Kubernetes Probes:**
```yaml
livenessProbe:
  httpGet:
    path: /agent/health
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /agent/capabilities
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Success Metrics

### Key Performance Indicators

**Functional Metrics:**
- Task acceptance rate: > 99%
- Task success rate: > 95%
- API availability: > 99.9%
- JWT validation success: > 99%

**Performance Metrics:**
- Agent health P95: < 200ms
- Task submission P95: < 500ms
- Core API P95: < 2000ms (unchanged)
- Event delivery P95: < 1000ms

**Business Metrics:**
- Orchestrated workflow completion rate
- Multi-service task execution latency
- Error rate reduction through orchestration
- Developer productivity improvement

---

**Production Readiness Status:** ✅ **READY**

The Scholarship API with Agent Bridge integration is production-ready with comprehensive monitoring, security hardening, and operational procedures in place.

**Next Steps:**
1. Choose deployment scenario based on risk tolerance
2. Configure production environment variables
3. Set up monitoring and alerting
4. Execute deployment plan
5. Run post-deployment validation
6. Monitor production metrics