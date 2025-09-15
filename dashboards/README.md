# Grafana Dashboard Configuration

This directory contains Grafana dashboard configuration for the Scholarship Discovery API production monitoring.

## Dashboard Components

### SLI/SLO Monitoring Dashboard
- **File**: `grafana-dashboard.json`
- **Dashboard ID**: `scholarship-api-dashboard`
- **Purpose**: Production SLI/SLO monitoring with burn-rate alerting integration

### Key Panels

#### 1. HTTP Request Latency
- **Metric**: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- **SLO**: ≤120ms P95 latency
- **Threshold**: Red line at 0.12s (120ms)
- **Shows**: P95 and P50 latency percentiles

#### 2. HTTP Error Rate  
- **Metric**: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`
- **SLO**: <0.1% 5xx error rate
- **Threshold**: Red line at 0.001 (0.1%)
- **Shows**: 5xx and 4xx error rates separately

#### 3. Active Scholarships Total
- **Metric**: `active_scholarships_total`
- **Purpose**: Business metric tracking scholarship inventory
- **Type**: Custom Prometheus collector (scrape-time)

#### 4. System Saturation
- **Metrics**: 
  - Rate limit hit rate (percentage of requests being rate limited)
  - OpenAI API request rate (external service request pressure)
- **Purpose**: Monitor system pressure signals and external service utilization
- **Unit**: Percentage for rate limit hits, requests/sec for API rate

#### 5. HTTP Request Rate
- **Metric**: `rate(http_requests_total[5m])`
- **Purpose**: Traffic monitoring and capacity planning
- **Breakdown**: By method and endpoint

#### 6. Service Availability
- **Metric**: `avg_over_time(up[5m])`
- **SLO**: ≥99.9% availability
- **Purpose**: Overall service health monitoring

## Deployment Instructions

### Docker Compose Integration
```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - ./dashboards/grafana-dashboard.json:/var/lib/grafana/dashboards/scholarship-api.json
      - ./dashboards/grafana-provisioning.yml:/etc/grafana/provisioning/dashboards/dashboards.yml
      - ./dashboards/datasource.yml:/etc/grafana/provisioning/datasources/prometheus.yml

# Security Best Practices for Production:
# 1. Generate strong admin password: export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
# 2. Never commit passwords to version control
# 3. Use TLS/HTTPS for production endpoints
# 4. Configure proper authentication and authorization
# 5. Restrict network access to monitoring stack
```

### Manual Installation
1. Copy `grafana-dashboard.json` to `/var/lib/grafana/dashboards/`
2. Copy `grafana-provisioning.yml` to `/etc/grafana/provisioning/dashboards/`
3. Copy `datasource.yml` to `/etc/grafana/provisioning/datasources/`
4. Restart Grafana service
5. Access dashboard at: `http://grafana:3000/d/scholarship-api-dashboard`

### Kubernetes Deployment
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
data:
  scholarship-api.json: |
    # Content of grafana-dashboard.json
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-provisioning
data:
  dashboards.yml: |
    # Content of grafana-provisioning.yml
```

## SLO Integration

This dashboard integrates with the burn-rate alert rules defined in `monitoring/production-alerts.yaml`:

### Fast Burn Alerts (1h/6h windows)
- **Availability**: 14.4× error budget consumption  
- **Latency**: 72% violations over 1 hour
- **Error Rate**: 1.44% 5xx rate over 1 hour

### Slow Burn Alerts (6h/24h windows)  
- **Availability**: 6× error budget consumption
- **Latency**: 30% violations over 6 hours
- **Error Rate**: 0.6% 5xx rate over 6 hours

## Customization

### Adding New Panels
1. Edit `grafana-dashboard.json` 
2. Add new panel object to `panels` array
3. Configure datasource, metrics, and visualization
4. Update provisioning to reload dashboard

### Alerting Integration
- Grafana alerting rules can reference dashboard panels
- Use templated queries from dashboard for consistency
- Configure notification channels (Slack, PagerDuty, email)

### Business Metrics
Add custom business metrics by:
1. Instrumenting application code with Prometheus metrics
2. Adding corresponding panels to dashboard
3. Setting appropriate thresholds and alerting

## Monitoring Stack Architecture

```
Application → Prometheus → Grafana Dashboard
     ↓            ↓            ↓
  Metrics     Time Series   Visualization
Collection   Database      & Alerting
```

## Performance Considerations

- **Refresh Rate**: 30 seconds (configurable)
- **Time Range**: Default 1 hour (adjustable)
- **Query Optimization**: Uses rate() and histogram_quantile() for efficient aggregation
- **Data Retention**: Follows Prometheus retention policy (typically 15 days)

## Troubleshooting

### Dashboard Not Loading
1. Check Grafana logs: `docker logs grafana`
2. Verify provisioning configuration
3. Ensure dashboard JSON is valid
4. Check datasource connectivity

### Metrics Not Appearing
1. Verify Prometheus is scraping metrics: `http://prometheus:9090/targets`
2. Check metric names match dashboard queries
3. Confirm time range encompasses data availability
4. Validate PromQL query syntax

### Alert Rules Not Firing
1. Check alert rule evaluation: `http://prometheus:9090/alerts`
2. Verify alert expressions against dashboard queries
3. Confirm notification channel configuration
4. Test alert conditions with manual queries

## References

- [Grafana Dashboard JSON Model](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [SRE Workbook - SLI/SLO Implementation](https://sre.google/workbook/implementing-slos/)