# Client Integration Guide — scholarship_api

**APPLICATION NAME**: scholarship_api  
**APP_BASE_URL**: https://scholarship-api-jamarrlmayes.replit.app  
**API Version**: 1.0.0  
**Last Updated**: 2025-11-11

---

## OpenAPI Specification

**URL**: https://scholarship-api-jamarrlmayes.replit.app/openapi.json

**Format**: OpenAPI 3.0+  
**Versioned Endpoints**: `/api/v1/*`

---

## Rate Limiting

### **Headers**

All API responses include rate limit information:

```http
X-RateLimit-Limit: 100          # Maximum requests per window
X-RateLimit-Remaining: 95       # Remaining requests in current window
X-RateLimit-Reset: 1699999999   # Unix timestamp when limit resets
```

### **Quota Policy Summary**

**Default Tier** (Free):
- **Limit**: 100 requests per minute
- **Burst**: 20 requests (short-term spike allowance)
- **Scope**: Per IP address or authenticated user

**Professional Tier**:
- **Limit**: 500 requests per minute
- **Burst**: 100 requests
- **Scope**: Per authenticated user

**Enterprise Tier**:
- **Limit**: 2000 requests per minute
- **Burst**: 500 requests
- **Scope**: Per authenticated user
- **Custom**: Contact sales for higher limits

**Rate Limit Backend**: Redis (multi-instance distributed) post DEF-005 (Nov 13, 12:00 UTC)

---

## Error Handling and Retry Strategy

### **HTTP Status Codes**

**429 Too Many Requests**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "request_id": "uuid-here"
  }
}
```
**Response Headers**:
```http
Retry-After: 60                  # Seconds until retry allowed
X-RateLimit-Reset: 1699999999   # Unix timestamp
```

**5xx Server Errors** (500, 502, 503, 504):
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please retry.",
    "request_id": "uuid-here"
  }
}
```

---

## Retry Strategy with Exponential Backoff and Jitter

### **Recommended Client Implementation**

**Retry-Eligible Status Codes**:
- `429` Too Many Requests
- `500` Internal Server Error
- `502` Bad Gateway
- `503` Service Unavailable
- `504` Gateway Timeout

**Non-Retry Status Codes** (Permanent Errors):
- `400` Bad Request
- `401` Unauthorized
- `403` Forbidden
- `404` Not Found
- `422` Unprocessable Entity

### **Exponential Backoff Algorithm**

```python
import random
import time

def retry_with_backoff(func, max_retries=3, base_delay=1.0, max_delay=32.0):
    """
    Retry function with exponential backoff and jitter.
    
    Args:
        func: Function to retry
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 32.0)
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except HTTPError as e:
            # Don't retry on permanent errors
            if e.status_code not in [429, 500, 502, 503, 504]:
                raise
            
            # Last attempt, raise error
            if attempt == max_retries:
                raise
            
            # Calculate backoff with exponential growth
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Add jitter (randomness) to prevent thundering herd
            jitter = random.uniform(0, delay * 0.1)  # 0-10% jitter
            total_delay = delay + jitter
            
            # Honor Retry-After header for 429 responses
            if e.status_code == 429 and 'Retry-After' in e.headers:
                total_delay = max(total_delay, int(e.headers['Retry-After']))
            
            print(f"Retry {attempt + 1}/{max_retries} after {total_delay:.2f}s")
            time.sleep(total_delay)
```

### **JavaScript/TypeScript Example**

```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
  maxDelay: number = 32000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      // Don't retry on permanent errors
      if (error.status && ![429, 500, 502, 503, 504].includes(error.status)) {
        throw error;
      }
      
      // Last attempt, throw error
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Calculate backoff with exponential growth
      let delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
      
      // Add jitter (0-10% randomness)
      const jitter = Math.random() * delay * 0.1;
      delay += jitter;
      
      // Honor Retry-After header for 429 responses
      if (error.status === 429 && error.headers?.['retry-after']) {
        delay = Math.max(delay, parseInt(error.headers['retry-after']) * 1000);
      }
      
      console.log(`Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  throw new Error('Max retries exceeded');
}
```

### **Usage Example**

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://scholarship-api-jamarrlmayes.replit.app',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  }
});

async function searchScholarships(query: string) {
  return retryWithBackoff(
    async () => {
      const response = await apiClient.post('/api/v1/search', { query });
      return response.data;
    },
    3,      // maxRetries
    1000,   // baseDelay (1 second)
    32000   // maxDelay (32 seconds)
  );
}

// Usage
try {
  const results = await searchScholarships('Computer Science');
  console.log(results);
} catch (error) {
  console.error('Failed after retries:', error);
}
```

---

## Best Practices

### **1. Always Check Rate Limit Headers**

```typescript
const response = await apiClient.get('/api/v1/scholarships');

const limit = parseInt(response.headers['x-ratelimit-limit']);
const remaining = parseInt(response.headers['x-ratelimit-remaining']);
const reset = parseInt(response.headers['x-ratelimit-reset']);

console.log(`Rate limit: ${remaining}/${limit} remaining`);
console.log(`Resets at: ${new Date(reset * 1000)}`);

// Proactive throttling when approaching limit
if (remaining < limit * 0.1) {  // Less than 10% remaining
  console.warn('Approaching rate limit, consider throttling requests');
}
```

### **2. Implement Circuit Breaker Pattern**

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  
  constructor(
    private threshold = 5,          // Open circuit after 5 failures
    private timeout = 60000,        // Keep open for 60 seconds
    private halfOpenRequests = 3    // Test with 3 requests when half-open
  ) {}
  
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN';
        console.log('Circuit breaker: HALF_OPEN (testing)');
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }
    
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess() {
    this.failures = 0;
    if (this.state === 'HALF_OPEN') {
      this.state = 'CLOSED';
      console.log('Circuit breaker: CLOSED (recovered)');
    }
  }
  
  private onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
      console.error('Circuit breaker: OPEN (too many failures)');
    }
  }
}

// Usage
const breaker = new CircuitBreaker();
const result = await breaker.execute(() => searchScholarships('STEM'));
```

### **3. Include request_id in Error Logging**

All error responses include a `request_id` for tracing:

```typescript
try {
  const response = await apiClient.get('/api/v1/scholarships/123');
} catch (error) {
  const requestId = error.response?.data?.error?.request_id;
  console.error(`API error (request_id: ${requestId}):`, error.message);
  
  // Include request_id when reporting to support
  reportToSupport({
    error: error.message,
    requestId: requestId,
    timestamp: new Date().toISOString()
  });
}
```

### **4. Implement Request Timeout**

```typescript
const apiClient = axios.create({
  baseURL: 'https://scholarship-api-jamarrlmayes.replit.app',
  timeout: 30000,  // 30 second timeout
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  }
});

// Per-request timeout override
const response = await apiClient.get('/api/v1/search', {
  timeout: 10000  // 10 second timeout for this request
});
```

---

## Rate Limit Quota Policy Summary for DRI Channels

### **student_pilot Integration**

**Recommended Tier**: Professional (500 req/min)

**Typical Usage Patterns**:
- Student dashboard loads: 5-10 requests per session
- Scholarship search: 1-3 requests per query (with pagination)
- Eligibility checks: 1 request per scholarship viewed
- Save/unsave operations: 1 request per action

**Expected Load**:
- Peak: 100 concurrent students
- Requests per student per minute: 5-10
- Total: 500-1000 req/min (requires Professional tier or load balancing)

**Recommendation**: 
- Start with Professional tier (500 req/min)
- Implement client-side caching for repeated scholarship views
- Use pagination efficiently (load 20 results per page)
- Monitor via scholarship_sage daily KPIs

### **provider_register Integration**

**Recommended Tier**: Free (100 req/min initially)

**Typical Usage Patterns**:
- Provider dashboard loads: 3-5 requests per session
- List scholarships: 1 request with pagination
- Create scholarship: 1 request
- Update scholarship: 1 request per edit
- Delete scholarship: 1 request

**Expected Load**:
- Peak: 20 concurrent providers
- Requests per provider per minute: 3-5
- Total: 60-100 req/min (Free tier sufficient initially)

**Recommendation**:
- Start with Free tier (100 req/min)
- Upgrade to Professional (500 req/min) as provider base grows
- Implement client-side caching for scholarship listings
- Batch operations where possible

### **Rate Limit Exceeded Handling**

Both integrations should implement:

1. **Retry with exponential backoff** (see examples above)
2. **Client-side caching** (cache scholarship data for 5-10 minutes)
3. **Request queuing** (queue non-urgent requests during rate limit)
4. **User feedback** ("Loading... please wait" instead of errors)
5. **Monitoring** (track rate limit hits in application logs)

---

## SLO Guarantees

**Uptime**: ≥99.9% (current: 100%)  
**P95 Latency**: ≤120ms (current: 55.6ms, 53.7% headroom)  
**Error Rate**: ≤0.1% (current: 0%)  

**Monitoring**: 
- Real-time: Sentry (10% performance sampling, 100% error capture)
- Dashboards: Accessible to scholarship_sage for cross-app KPI ingestion
- Alerting: Prometheus rules with PagerDuty integration (post-production)

---

## Authentication

All API requests (except `/health` and `/openapi.json`) require JWT authentication:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**Token Provider**: scholar_auth  
**Token Format**: JWT (RS256)  
**JWKS Endpoint**: https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json  
**Token Expiry**: Configurable (default: 1 hour)  
**Refresh**: Via scholar_auth refresh token endpoint

---

## CORS Policy

**Allowed Origins** (Production):
- https://student-pilot-jamarrlmayes.replit.app
- https://provider-register-jamarrlmayes.replit.app
- https://scholarship-sage-jamarrlmayes.replit.app
- https://scholarship-agent-jamarrlmayes.replit.app
- https://auto-page-maker-jamarrlmayes.replit.app
- https://auto-com-center-jamarrlmayes.replit.app
- https://scholar-auth-jamarrlmayes.replit.app

**Development**: Localhost allowed in development mode only

---

## Support and Escalation

**Technical Issues**:
- Include `request_id` from error response
- Check SLO dashboard: [Link to Sentry/Prometheus when available]
- Escalate via DRI channels

**Rate Limit Increases**:
- Contact scholarship_api DRI with:
  - Current usage patterns
  - Expected growth
  - Use case justification
  - Proposed tier (Professional/Enterprise)

**SLA Violations**:
- Automatic rollback within 5 minutes
- Incident report within 15 minutes
- Root cause analysis within 24 hours

---

**Document Version**: 1.0  
**Effective Date**: 2025-11-11  
**Next Review**: Post DEF-005 migration (Nov 13, 12:00 UTC)
