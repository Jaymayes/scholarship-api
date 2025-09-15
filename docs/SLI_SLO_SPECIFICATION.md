# Service Level Indicators (SLI) and Service Level Objectives (SLO) Specification

## 📊 **PRIORITY 1 SLO TARGETS** (24-48 Hours)

This document defines the formal SLI/SLO framework for the Scholarship Discovery & Search API, aligning with our production readiness commitment.

---

## 🎯 **CRITICAL SLOs**

### **1. AVAILABILITY SLO**
- **Target**: ≥99.9% uptime
- **Measurement Window**: 30-day rolling average
- **SLI Definition**: Successful health check responses / Total health check requests
- **Endpoint**: `/health`, `/healthz`
- **Error Budget**: 43.8 minutes downtime per 30 days
- **Alert Threshold**: Fast burn ≥2%/hour, Slow burn ≥1%/6 hours

### **2. LATENCY SLO** 
- **Target**: P95 ≤120ms (tightened from current 220ms)
- **Measurement Window**: 5-minute rolling average
- **SLI Definition**: 95th percentile of all successful HTTP request durations
- **Scope**: All API endpoints excluding `/docs`, `/metrics`
- **Error Budget**: 5% of requests may exceed 120ms
- **Alert Threshold**: P95 >120ms for 10+ minutes

### **3. ERROR RATE SLO**
- **Target**: <0.1% (tightened from current 0.5%)
- **Measurement Window**: 5-minute rolling average  
- **SLI Definition**: 5xx error responses / Total requests
- **Scope**: All user-facing API endpoints
- **Error Budget**: 0.1% of requests may return 5xx errors
- **Alert Threshold**: >0.1% error rate for 5+ minutes

### **4. RATE LIMITING SLO**
- **Target**: <1% traffic receiving 429 responses
- **Measurement Window**: 15-minute rolling average
- **SLI Definition**: 429 responses / Total requests
- **Scope**: All API endpoints with rate limiting
- **Purpose**: Ensure rate limiting doesn't impact legitimate users
- **Alert Threshold**: >1% 429 rate for 15+ minutes

---

## 📈 **SUPPORTING SLIs**

### **Database Performance**
- **DB Connection Pool Utilization**: ≤75%
- **Database Query P95 Latency**: ≤50ms
- **Database Query Error Rate**: <0.01%

### **Dependency Health**
- **OpenAI Service Availability**: ≥99.5%
- **Redis Cache Hit Ratio**: ≥85%
- **Agent Task Success Rate**: ≥99%

### **Business Metrics**
- **Active Scholarships Count**: Real-time tracking
- **Search Success Rate**: ≥99.5%
- **Eligibility Check Success Rate**: ≥99.9%

---

## 🚨 **MULTI-WINDOW SLO BURN ALERTING**

### **Fast Burn (Critical)**
```yaml
threshold: "≥2% error budget consumption per hour"
duration: "30-60 minutes sustained"
action: "Page on-call immediately"
severity: "critical"
escalation: "15-minute escalation policy"
```

### **Slow Burn (Warning)**
```yaml
threshold: "≥1% error budget consumption per 6 hours"  
duration: "Sustained degradation trend"
action: "Create investigation ticket"
severity: "warning"
escalation: "Next business day"
```

---

## 📊 **METRICS INSTRUMENTATION**

### **Prometheus Metrics**
- **http_requests_total**: Counter with labels [method, endpoint, status]
- **http_request_duration_seconds**: Histogram with labels [method, endpoint]
- **database_queries_total**: Counter with labels [query_type, status] 
- **database_query_duration_seconds**: Histogram with labels [query_type]
- **active_scholarships_total**: Gauge (custom collector)
- **rate_limit_rejected_total**: Counter with labels [limit_type]

### **Custom Collectors**
- **ActiveScholarshipsCollector**: Scrape-time computation for real-time accuracy
- **Custom /metrics endpoint**: Unified registry with auto-instrumentation

### **Health Check Endpoints**
- **GET /health**: Comprehensive health with trace_id
- **GET /healthz**: Kubernetes-style minimal health check
- **GET /readiness**: Application readiness for traffic

---

## 🔍 **SLO MONITORING STRATEGY**

### **Real-Time Monitoring**
- **Dashboard**: Grafana dashboards for all SLIs
- **Alerting**: Prometheus AlertManager with PagerDuty integration
- **Tracing**: Distributed tracing with correlation IDs

### **Error Budget Tracking**
- **Monthly Budget**: 99.9% availability = 43.8 minutes downtime
- **Budget Consumption Rate**: Fast/slow burn detection
- **Budget Alerts**: Early warning system for budget depletion

### **Load Testing Integration**
- **k6 Thresholds**: SLO enforcement in CI/CD pipeline
- **Performance Gates**: Block deployments that violate SLOs
- **Continuous Validation**: Scheduled load tests against production

---

## 📋 **SLO REVIEW PROCESS**

### **Weekly Reviews**
- SLO compliance assessment
- Error budget consumption analysis
- Trend identification and capacity planning

### **Monthly Reviews** 
- SLO target adjustment based on business needs
- Performance optimization prioritization
- Incident post-mortem SLO impact analysis

### **Quarterly Reviews**
- SLO strategy alignment with business objectives
- Infrastructure capacity planning
- SLO framework evolution and best practices

---

## 🎯 **PRIORITY 1 ACCEPTANCE CRITERIA**

✅ **Defined**: Comprehensive SLI/SLO specification with precise targets
✅ **Measured**: All metrics instrumented and collecting data
✅ **Monitored**: Multi-window burn alerting configured  
✅ **Validated**: Load testing enforces SLO thresholds
✅ **Actionable**: Clear escalation procedures and runbooks

**TARGET COMPLETION**: 24-48 hours
**STATUS**: ✅ COMPLETE - Formal SLI/SLO framework established