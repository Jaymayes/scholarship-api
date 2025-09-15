# API Error Schema Reference - Priority 2 Day 2

## Unified Error Envelope

All API error responses follow a standardized JSON schema for consistency and predictability.

### Standard Error Format

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error description",
  "correlation_id": "uuid-for-tracking",
  "status": 400,
  "timestamp": 1640995200,
  "details": {
    "additional": "context-specific data"
  }
}
```

### Field Definitions

- **`code`** (string, required): Machine-readable error code for programmatic handling
- **`message`** (string, required): Human-readable description suitable for user display
- **`correlation_id`** (string, required): Unique identifier for request tracing and debugging
- **`status`** (integer, required): HTTP status code for the error
- **`timestamp`** (integer, required): Unix timestamp when the error occurred
- **`details`** (object, optional): Additional context-specific error data

## HTTP Status Code Semantics

### 400 vs 422 - Request Errors
- **400 Bad Request**: Syntactic issues with the request (malformed JSON, invalid URL parameters)
- **422 Unprocessable Entity**: Valid JSON with semantic/validation errors (missing required fields, invalid field values)

### 401 vs 403 - Authentication and Authorization  
- **401 Unauthorized**: No authentication provided or invalid credentials
- **403 Forbidden**: Valid authentication but insufficient permissions for the resource

### Other Status Codes
- **404 Not Found**: Unknown route or resource identifier
- **405 Method Not Allowed**: Valid route but unsupported HTTP method
- **409 Conflict**: Request conflicts with current resource state
- **429 Too Many Requests**: Rate limit exceeded (includes `Retry-After` header)
- **5xx Server Errors**: Never leak internal details, always include `correlation_id`

## Error Code Examples

### Authentication Errors (401)
```json
{
  "code": "UNAUTHORIZED",
  "message": "Authentication required",
  "correlation_id": "abc123-def456-ghi789",
  "status": 401,
  "timestamp": 1640995200
}
```

### Validation Errors (422)
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "correlation_id": "abc123-def456-ghi789", 
  "status": 422,
  "timestamp": 1640995200,
  "details": {
    "fields": [
      {
        "field": "email",
        "message": "field required",
        "value": null
      },
      {
        "field": "age",
        "message": "ensure this value is greater than or equal to 18",
        "value": 15
      }
    ]
  }
}
```

### Permission Errors (403)
```json
{
  "code": "FORBIDDEN",
  "message": "Insufficient permissions for this resource",
  "correlation_id": "abc123-def456-ghi789",
  "status": 403,
  "timestamp": 1640995200,
  "details": {
    "required_permission": "scholarship:read",
    "user_permissions": ["profile:read"]
  }
}
```

### Rate Limiting Errors (429)
```json
{
  "code": "RATE_LIMITED", 
  "message": "Rate limit exceeded: 5 requests per minute",
  "correlation_id": "abc123-def456-ghi789",
  "status": 429,
  "timestamp": 1640995200,
  "details": {
    "retry_after_seconds": 60,
    "limit": 5,
    "window": "1 minute"
  }
}
```

### Not Found Errors (404)
```json
{
  "code": "NOT_FOUND",
  "message": "Scholarship not found: sch_12345",
  "correlation_id": "abc123-def456-ghi789", 
  "status": 404,
  "timestamp": 1640995200,
  "details": {
    "resource": "scholarship",
    "identifier": "sch_12345"
  }
}
```

### Conflict Errors (409)
```json
{
  "code": "CONFLICT",
  "message": "Resource already exists with this identifier",
  "correlation_id": "abc123-def456-ghi789",
  "status": 409, 
  "timestamp": 1640995200,
  "details": {
    "conflicting_field": "email",
    "existing_resource_id": "user_98765"
  }
}
```

### Server Errors (500)
```json
{
  "code": "INTERNAL_ERROR",
  "message": "An internal server error occurred",
  "correlation_id": "abc123-def456-ghi789",
  "status": 500,
  "timestamp": 1640995200
}
```

## Client Implementation Guide

### Error Handling Best Practices

1. **Always check the `code` field** for programmatic error handling
2. **Use `message` for user-friendly error display** 
3. **Include `correlation_id` in support requests** for faster debugging
4. **Parse `details` for context-specific error data** (validation fields, retry timing)

### Example Client Code

```javascript
// JavaScript/TypeScript example
async function handleApiResponse(response) {
  if (!response.ok) {
    const error = await response.json();
    
    switch (error.code) {
      case 'VALIDATION_ERROR':
        // Handle field validation errors
        displayFieldErrors(error.details.fields);
        break;
        
      case 'RATE_LIMITED':
        // Handle rate limiting with retry
        const retryAfter = error.details.retry_after_seconds;
        setTimeout(() => retryRequest(), retryAfter * 1000);
        break;
        
      case 'UNAUTHORIZED':
        // Redirect to login
        redirectToLogin();
        break;
        
      default:
        // Generic error handling
        console.error(`API Error: ${error.message}`, error.correlation_id);
        showGenericError(error.message);
    }
  }
}
```

## Testing and Validation

All error responses are validated through contract tests to ensure schema consistency. Any deviation from this format should be reported as a bug.

### Schema Drift Detection

The CI pipeline includes automated schema validation that will fail builds if error responses don't conform to this specification.

### Correlation ID Tracking

Every error includes a `correlation_id` that can be used to trace the request through logs and monitoring systems for debugging purposes.