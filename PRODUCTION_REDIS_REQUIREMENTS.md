# Production Redis Requirements - 100% Promotion Blocker

**Date:** 2025-08-21  
**Status:** ⚠️ REQUIRED FOR 100% PROMOTION  
**Current:** Development in-memory fallback

---

## 🚫 **100% Promotion Blocker Status**

### **Critical Requirements for Final Promotion:**
- **Production Redis:** HA/Sentinel/Cluster deployment
- **Security:** TLS + AUTH + at-rest encryption
- **Performance:** P95 <10ms latency from app pods
- **Validation:** Cross-pod persistence and failover testing

---

## 🏗️ **Platform Requirements**

### **Infrastructure Configuration:**
```yaml
# Production Redis Cluster Configuration
redis:
  mode: "cluster"  # or "sentinel" for HA
  nodes: 3  # minimum for HA
  tls:
    enabled: true
    cert_file: "/etc/redis/tls/redis.crt"
    key_file: "/etc/redis/tls/redis.key"
    ca_file: "/etc/redis/tls/ca.crt"
  auth:
    enabled: true
    password: "${REDIS_PASSWORD}"  # from secrets manager
  encryption:
    at_rest: true
    in_transit: true
```

### **Network Requirements:**
- **Low Latency:** P95 <10ms from app pods to Redis
- **Network Policies:** Restrict access to app pods only
- **Connection Pooling:** Max connections configured per pod
- **Firewall Rules:** Redis port (6379/6380) restricted

---

## ⚙️ **Application Configuration**

### **Environment Variables Required:**
```bash
# Production Redis Configuration
REDIS_URL="rediss://prod-redis-cluster.internal:6380"
REDIS_PASSWORD="${REDIS_AUTH_TOKEN}"
REDIS_TLS_CERT_FILE="/etc/tls/redis-client.crt"
REDIS_TLS_KEY_FILE="/etc/tls/redis-client.key"
REDIS_TLS_CA_FILE="/etc/tls/redis-ca.crt"

# Connection Configuration
REDIS_CONNECT_TIMEOUT="100"  # milliseconds
REDIS_READ_TIMEOUT="200"     # milliseconds
REDIS_POOL_SIZE="20"         # connections per pod
REDIS_MAX_CONNECTIONS="100"  # total pool limit

# Rate Limiting Configuration
RATE_LIMIT_DEFAULT="100"     # default requests per minute
TRUSTED_PROXIES="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
ENVIRONMENT="production"
```

### **Per-Endpoint Rate Limits:**
```bash
# Endpoint-Specific Limits (requests per minute)
RATE_LIMIT_SEARCH="60"              # /api/v1/search
RATE_LIMIT_SCHOLARSHIPS="60"        # /api/v1/scholarships
RATE_LIMIT_RECOMMENDATIONS="30"     # /api/v1/recommendations
RATE_LIMIT_ELIGIBILITY_CHECK="30"   # /api/v1/eligibility/check
RATE_LIMIT_ANALYTICS="100"          # /api/v1/analytics/*
RATE_LIMIT_INTERACTIONS="120"       # /api/v1/interactions

# Exempt Endpoints (no rate limiting)
# /healthz, /readyz, /docs, /openapi.json, /metrics
```

### **Redis Configuration:**
```bash
# Memory and Eviction
REDIS_MEMORY_POLICY="allkeys-lru"
REDIS_MAX_MEMORY="2gb"
REDIS_TTL_RATE_LIMIT="3600"  # 1 hour TTL for rate limit keys

# Connection Pool Settings
REDIS_POOL_UTILIZATION_THRESHOLD="80"  # max 80% utilization
REDIS_CONNECTION_IDLE_TIMEOUT="300"    # 5 minutes
REDIS_CONNECTION_MAX_AGE="1800"        # 30 minutes
```

---

## 🧪 **Validation Requirements**

### **Endpoint Coverage Testing:**
```bash
# Test commands for each endpoint
curl -i -H "Authorization: Bearer <token>" \
  https://api.prod.com/api/v1/search | grep -i "ratelimit"

curl -i -H "Authorization: Bearer <token>" \
  https://api.prod.com/api/v1/scholarships | grep -i "retry-after"

curl -i -H "Authorization: Bearer <token>" \
  https://api.prod.com/api/v1/recommendations | grep -i "ratelimit"

curl -i -H "Authorization: Bearer <token>" \
  https://api.prod.com/api/v1/eligibility/check | grep -i "ratelimit"
```

### **Required Headers on Responses:**
- **200 OK Responses:**
  - `X-RateLimit-Limit: 60`
  - `X-RateLimit-Remaining: 45`
  - `X-RateLimit-Reset: 1692123456`

- **429 Too Many Requests:**
  - `Retry-After: 60`
  - `X-RateLimit-Limit: 60`
  - `X-RateLimit-Remaining: 0`
  - `X-RateLimit-Reset: 1692123456`

### **Cross-Pod Persistence Test:**
```bash
# 1. Send burst of requests to trigger rate limiting
seq 1 100 | xargs -I {} -P 20 curl -s -o /dev/null \
  -w "%{http_code}\n" https://api.prod.com/api/v1/search

# 2. Restart one canary pod
kubectl delete pod <canary-pod-name>

# 3. Immediately repeat burst - should still see 429s
seq 1 100 | xargs -I {} -P 20 curl -s -o /dev/null \
  -w "%{http_code}\n" https://api.prod.com/api/v1/search

# Expected: 429s persist (Redis-backed, not in-memory)
```

---

## 🔄 **Failover Testing Requirements**

### **Redis Failover Drill:**
1. **Trigger Failover:** Brief primary Redis node restart/failover
2. **Expected Behavior:** 
   - App continues with minimal impact
   - Edge rate limits still protect endpoints
   - `limiter_redis_errors` remains 0
   - No 5xx error spikes during failover

### **Failover Validation Commands:**
```bash
# Before failover - establish baseline
curl -s -w "%{http_code}" https://api.prod.com/api/v1/search

# During failover - monitor graceful degradation
for i in {1..60}; do
  curl -s -w "%{http_code} " https://api.prod.com/api/v1/search
  sleep 1
done

# After failover - confirm full functionality
curl -i https://api.prod.com/api/v1/search | grep -i "ratelimit"
```

---

## 📊 **Monitoring and Alerting**

### **Required Metrics:**
- **Redis Performance:**
  - `redis_latency_p95` <10ms
  - `redis_pool_utilization` <80%
  - `redis_connections_active` / `redis_connections_max`
  - `redis_memory_usage` / `redis_memory_max`

- **Rate Limiting:**
  - `rate_limit_rejected_total` by endpoint
  - `limiter_redis_errors` (should be 0)
  - `rate_limit_cache_hits` / `rate_limit_cache_total`

### **Alert Thresholds:**
- **Critical:** `limiter_redis_errors` >0 for 5+ minutes
- **Warning:** `redis_latency_p95` >10ms for 10+ minutes
- **Warning:** `redis_pool_utilization` >85% for 5+ minutes
- **Critical:** Redis failover taking >30 seconds

---

## ✅ **Go/No-Go Criteria for 100% Promotion**

### **Must Pass Before 100%:**
1. **✅ 6-12 hours at 25-50%** with all gates green
2. **⚠️ Production Redis** configured and validated
3. **⚠️ Overall 429s ≤1%** (excluding testers)
4. **⚠️ limiter_redis_errors = 0** sustained
5. **✅ P95 ≤220ms** (P99 stable)
6. **✅ 5xx ≤0.5%**, DB pool <75%
7. **✅ OpenAI fallback <5%**
8. **✅ CORS hardened** (no wildcard)
9. **⚠️ JWT replay protection** verified
10. **⚠️ Cross-pod persistence** confirmed

### **Current Status:**
- **6/10 criteria met** (green items above)
- **4 blockers remaining** (production Redis, validation, JWT integration)

---

## 🚀 **Final 100% Promotion Plan**

### **After Redis Validation Passes:**
1. **Validate endpoint coverage** with correct headers
2. **Hold green for ≥2 hours** at 50%
3. **Execute final promotion:**
   - Helm: `--set canary.enabled=false --set image.tag=vX.Y.Z`
   - Argo: `kubectl argo rollouts promote scholarship-api`
   - Ingress: Remove canary or set weight=100

### **Post-100% Monitoring (48 hours):**
- **Game Day Testing:** Pod kills, Redis failover, OpenAI throttling
- **Graceful Degradation:** Confirm alerts and fallback behavior
- **Performance Validation:** Sustained metrics within targets

---

**🎯 STATUS: REDIS PRODUCTION CONFIGURATION REQUIRED**  
**⚠️ BLOCKER: 100% promotion pending Redis validation**  
**📊 CURRENT: 25-50% canary monitoring active**