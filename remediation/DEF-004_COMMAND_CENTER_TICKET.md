# DEF-004: Command Center Integration Missing

**Severity:** 🔴 CRITICAL (Operational)  
**Component:** Observability / Command Center  
**Owner:** SRE Lead + DevOps + QA  
**Target:** Day 1-2 (Parallel with other fixes)  
**Status:** 🟡 IN PROGRESS

---

## 📋 PROBLEM STATEMENT

Command Center infrastructure is completely missing - no heartbeat, telemetry, alerting, or remote command capabilities. This violates our 24/7 operational mandate and makes production deployment unsafe. Baseline observability must be live before launch to uphold SLOs and enable incident response.

## 🔬 EVIDENCE

**Missing Environment Variables:**
```bash
❌ COMMAND_CENTER_BASE_URL: Not configured
❌ COMMAND_CENTER_API_KEY: Not configured  
❌ SERVICE_ID: Not configured
```

**Impact:**
- No service health monitoring
- No golden signals dashboard
- No automated alerting
- No incident response capability
- No remote kill-switch
- Cannot validate 99.9% uptime SLO

## 🎯 ACCEPTANCE CRITERIA (Launch Gate - Operability)

**Command Center Live Gate:**
- [ ] **Heartbeat active**: Structured payload every 60s with ACK
- [ ] **Golden signals tracked**: Latency, traffic, errors, saturation
- [ ] **Dashboards live**: Real-time metrics visualization
- [ ] **Runbook-linked alerts**: Automated alerting with action guides
- [ ] **Synthetic monitoring**: Automated health checks from external regions
- [ ] **Remote kill-switch**: Emergency shutdown capability tested
- [ ] **On-call routing**: PagerDuty/Opsgenie integration verified
- [ ] **Distributed rate limiting**: Cross-pod consistency validated

## 🛠️ FIX PLAN

### Phase 1: Infrastructure Provisioning (2 hours)

**1. Choose Observability Stack:**
```bash
# Option A: Prometheus + Grafana (Self-hosted)
# - Prometheus for metrics
# - Grafana for dashboards
# - Alertmanager for alerts

# Option B: Managed Service (RECOMMENDED)
# - DataDog / New Relic / Honeycomb
# - Faster setup, better reliability
# - Built-in alerting and dashboards

# We'll use: Grafana Cloud (Free tier: 10k series, 50GB logs)
```

**2. Provision Services:**
```bash
# Grafana Cloud Setup
# 1. Sign up: https://grafana.com/auth/sign-up/create-user
# 2. Create stack: scholarshipai-prod
# 3. Get credentials:
#    - GRAFANA_INSTANCE_ID=xxxxx
#    - GRAFANA_API_KEY=glc_xxxxx
#    - PROMETHEUS_URL=https://prometheus-xxx.grafana.net/api/prom
#    - LOKI_URL=https://logs-xxx.grafana.net

# Set environment variables
export COMMAND_CENTER_BASE_URL="https://prometheus-xxx.grafana.net"
export COMMAND_CENTER_API_KEY="glc_xxxxx"
export SERVICE_ID="scholarship-api-prod"
export GRAFANA_LOKI_URL="https://logs-xxx.grafana.net"
```

**3. Alternative: Self-Hosted (Docker Compose):**
```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
  
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

volumes:
  prometheus_data:
  grafana_data:
```

### Phase 2: Heartbeat Implementation (3 hours)

```python
# services/command_center.py
import asyncio
import httpx
from datetime import datetime
from config.settings import settings

class CommandCenterClient:
    def __init__(self):
        self.base_url = settings.command_center_base_url
        self.api_key = settings.command_center_api_key
        self.service_id = settings.service_id
        self.heartbeat_interval = 60  # seconds
        self.last_heartbeat_ack = None
    
    async def send_heartbeat(self):
        """Send structured heartbeat to Command Center"""
        payload = {
            "service_id": self.service_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": await self._get_service_status(),
            "version": settings.api_version,
            "region": settings.region or "us-east-1",
            "metrics": {
                "p95_latency_ms": await self._get_p95_latency(),
                "error_rate": await self._get_error_rate(),
                "active_connections": await self._get_active_connections(),
                "cpu_usage_percent": await self._get_cpu_usage(),
                "memory_usage_percent": await self._get_memory_usage()
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/heartbeat",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    ack_data = response.json()
                    self.last_heartbeat_ack = ack_data.get("correlation_id")
                    logger.info(f"Heartbeat ACK: {self.last_heartbeat_ack}")
                    return ack_data
                else:
                    logger.error(f"Heartbeat failed: {response.status_code}")
                    await self._handle_heartbeat_failure()
                    
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
                await self._handle_heartbeat_failure()
    
    async def _handle_heartbeat_failure(self):
        """Handle heartbeat failure with retry/backoff"""
        # Exponential backoff: 5s, 10s, 20s, 40s, 60s (max)
        retry_delays = [5, 10, 20, 40, 60]
        
        for delay in retry_delays:
            await asyncio.sleep(delay)
            try:
                result = await self.send_heartbeat()
                if result:
                    logger.info(f"Heartbeat recovered after {delay}s delay")
                    return
            except Exception as e:
                logger.warning(f"Heartbeat retry failed: {e}")
        
        logger.critical("Heartbeat failed after all retries - triggering alert")
    
    async def heartbeat_loop(self):
        """Continuous heartbeat loop"""
        while True:
            await self.send_heartbeat()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def _get_service_status(self) -> str:
        """Get current service health status"""
        # Check critical dependencies
        db_ok = await check_database_health()
        redis_ok = await check_redis_health()
        
        if db_ok and redis_ok:
            return "healthy"
        elif db_ok:
            return "degraded"  # Redis down but can operate
        else:
            return "unhealthy"  # Database critical
    
    async def _get_p95_latency(self) -> float:
        """Get P95 latency from metrics"""
        from prometheus_client import REGISTRY
        # Calculate P95 from histogram
        return 45.0  # Placeholder - implement from actual metrics
    
    async def _get_error_rate(self) -> float:
        """Get current error rate"""
        # Calculate from error counters
        return 0.05  # Placeholder - 0.05%

# Start heartbeat on application startup
command_center = CommandCenterClient()

@app.on_event("startup")
async def start_heartbeat():
    asyncio.create_task(command_center.heartbeat_loop())
```

### Phase 3: Golden Signals & Dashboards (4 hours)

**Four Golden Signals:**
1. **Latency** - Request/response time
2. **Traffic** - Request volume
3. **Errors** - Error rate
4. **Saturation** - Resource utilization

```python
# metrics/golden_signals.py
from prometheus_client import Histogram, Counter, Gauge

# 1. LATENCY
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0]
)

# 2. TRAFFIC
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 3. ERRORS
errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

# 4. SATURATION
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
db_pool_usage = Gauge('database_pool_usage_percent', 'DB pool utilization')
```

**Grafana Dashboard JSON:**
```json
{
  "dashboard": {
    "title": "ScholarshipAI - Golden Signals",
    "panels": [
      {
        "title": "Request Latency (P50, P95, P99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [120],
                "type": "gt"
              },
              "query": {
                "params": ["P95", "5m", "now"]
              }
            }
          ]
        }
      },
      {
        "title": "Request Rate (RPS)",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_errors_total[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error %"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [0.1],
                "type": "gt"
              }
            }
          ]
        }
      },
      {
        "title": "Resource Saturation",
        "targets": [
          {
            "expr": "system_cpu_usage_percent",
            "legendFormat": "CPU %"
          },
          {
            "expr": "system_memory_usage_percent",
            "legendFormat": "Memory %"
          },
          {
            "expr": "database_pool_usage_percent",
            "legendFormat": "DB Pool %"
          }
        ]
      }
    ]
  }
}
```

### Phase 4: Alerting with Runbooks (3 hours)

```yaml
# alerts/golden_signals.yml
groups:
  - name: golden_signals
    interval: 30s
    rules:
      - alert: HighLatencyP95
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.120
        for: 5m
        labels:
          severity: critical
          component: api
        annotations:
          summary: "P95 latency exceeds 120ms SLO"
          description: "P95 latency is {{ $value }}ms (target: ≤120ms)"
          runbook: "https://runbooks.scholarshipai.com/high-latency"
          dashboard: "https://grafana.scholarshipai.com/d/golden-signals"
      
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.001
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate exceeds 0.1% threshold"
          description: "Error rate is {{ $value | humanizePercentage }}"
          runbook: "https://runbooks.scholarshipai.com/high-error-rate"
      
      - alert: ServiceSaturation
        expr: database_pool_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database pool >80% saturated"
          runbook: "https://runbooks.scholarshipai.com/db-saturation"
      
      - alert: HeartbeatMissing
        expr: up{job="scholarship-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service heartbeat missing"
          description: "No heartbeat received for 2 minutes"
          runbook: "https://runbooks.scholarshipai.com/heartbeat-failure"
```

**PagerDuty Integration:**
```yaml
# alertmanager.yml
route:
  receiver: 'pagerduty'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<PAGERDUTY_SERVICE_KEY>'
        description: '{{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
        details:
          runbook: '{{ .Annotations.runbook }}'
          dashboard: '{{ .Annotations.dashboard }}'
          firing: '{{ range .Alerts }}{{ .Labels.instance }} {{ end }}'
```

### Phase 5: Remote Kill-Switch (2 hours)

```python
# services/remote_commands.py
from fastapi import APIRouter, Header, HTTPException
import hmac
import hashlib

router = APIRouter(prefix="/internal/commands", tags=["Remote Commands"])

class RemoteCommandHandler:
    
    @staticmethod
    def verify_signature(payload: str, signature: str) -> bool:
        """Verify HMAC signature from Command Center"""
        expected = hmac.new(
            settings.command_center_api_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    @router.post("/kill-switch")
    async def kill_switch(
        payload: dict,
        x_signature: str = Header(...),
        x_correlation_id: str = Header(...)
    ):
        """Emergency kill-switch - return 503 for all requests"""
        
        # Verify signature
        if not RemoteCommandHandler.verify_signature(json.dumps(payload), x_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Activate maintenance mode
        await activate_maintenance_mode()
        
        # Log audit trail
        logger.critical(
            "KILL_SWITCH_ACTIVATED",
            extra={
                "correlation_id": x_correlation_id,
                "reason": payload.get("reason"),
                "operator": payload.get("operator"),
                "timestamp": datetime.utcnow()
            }
        )
        
        # Send ACK
        return {
            "status": "acknowledged",
            "correlation_id": x_correlation_id,
            "maintenance_mode": True,
            "signature": sign_response(x_correlation_id)
        }
    
    @router.post("/refresh-cache")
    async def refresh_cache(payload: dict, x_signature: str = Header(...)):
        """Refresh application cache"""
        if not RemoteCommandHandler.verify_signature(json.dumps(payload), x_signature):
            raise HTTPException(status_code=401)
        
        # Clear caches
        await clear_all_caches()
        
        return {"status": "acknowledged", "caches_cleared": True}

# Add to main.py
app.include_router(RemoteCommandHandler.router)
```

## ✅ VERIFICATION CHECKLIST

**Day 1:**
- [ ] Observability stack provisioned (Grafana Cloud or self-hosted)
- [ ] Environment variables configured
- [ ] Heartbeat sending every 60s with ACK
- [ ] Golden signals metrics exported
- [ ] Basic dashboard created

**Day 2:**
- [ ] Runbook-linked alerts configured
- [ ] PagerDuty/Opsgenie integration tested
- [ ] Remote kill-switch tested (dry-run)
- [ ] Synthetic monitoring active (Pingdom/UptimeRobot)
- [ ] On-call rotation configured
- [ ] QA validates alert firing and resolution

## 📊 MONITORING VALIDATION

```bash
# Test heartbeat
curl -X POST https://prometheus-xxx.grafana.net/api/v1/heartbeat \
  -H "Authorization: Bearer ${COMMAND_CENTER_API_KEY}" \
  -d '{
    "service_id": "scholarship-api-prod",
    "status": "healthy",
    "metrics": {"p95_latency_ms": 45}
  }'

# Verify metrics
curl https://scholarship-api-jamarrlmayes.replit.app/metrics

# Test alert firing
# Temporarily spike error rate to trigger alert
```

## 📁 ARTIFACTS

- [ ] Grafana dashboard JSON export
- [ ] Alert rules YAML
- [ ] Heartbeat implementation
- [ ] Remote command handlers
- [ ] Runbook documentation (5 runbooks minimum)
- [ ] On-call rotation schedule

---

**ETA:** Day 1-2 (14 hours total, can parallelize)  
**Risk:** Medium (requires infrastructure coordination)  
**Dependencies:** Budget approval ($2k/month for observability stack)
