# Production Runbook - Scholarship Discovery API

## Deployment Procedures
### Standard Deployment
```bash
helm upgrade --install scholarship-api ./charts/scholarship-api --set image.tag=vX.Y.Z
```

### Rollback Procedures
```bash
helm rollback scholarship-api $(helm history scholarship-api | grep "deployed" | tail -2 | head -1 | awk '{print $1}')
```

## Monitoring and Alerting
### Key Metrics
- Availability ≥99.9%
- P95 Latency ≤220ms
- 5xx Error Rate ≤0.5%
- Rate Limiting: 429s ≤1%

### Alert Thresholds
- Fast burn ≥2%/hour for 30-60 min → page on-call
- Slow burn ≥1%/6 hours → create ticket
- Redis errors >0 for 5 min → immediate attention

## Incident Response
### Redis Failover
1. Verify sentinel promotion
2. Check application reconnection
3. Monitor rate limiting recovery
4. Validate cross-pod consistency

### OpenAI Degradation
1. Verify fallback responses active
2. Monitor core functionality unaffected
3. Check circuit breaker metrics
4. Validate cost controls

### Security Incidents
1. Check CORS configuration
2. Validate JWT replay protection
3. Review rate limiting patterns
4. Audit authentication logs

## Maintenance Procedures
### Quarterly Tasks
- Rotate Redis/OpenAI credentials
- Review and update CORS allowlist
- Performance capacity planning
- Security posture review

### Annual Tasks
- Comprehensive penetration testing
- Full disaster recovery drill
- Architecture review and updates
- Compliance audit preparation
