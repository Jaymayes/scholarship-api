# SEO Schema ZodError Hotfix - Phase 6

## Summary
Fixed topics field validation in Pydantic schemas to prevent crashes when malformed data is sent to SEO-related endpoints.

## Date
2026-01-20

## Issue
SEO endpoints could crash if malformed `topics` arrays were sent in request payloads (e.g., non-string elements, missing field causing None type errors).

## Root Cause
The `topics` field was not defined in the search request schemas, which could cause validation errors or crashes when clients sent unexpected topic data to SEO-related search endpoints.

## Fix Applied

### 1. Added `topics` field to `StrictSearchRequest` (schemas/strict_validation.py)
```python
topics: list[str] = Field(default_factory=list, max_items=50, description="SEO topics filter - Phase 6 hotfix")

@field_validator('topics', mode='before')
@classmethod
def validate_topics(cls, v: list | None) -> list:
    """Validate topics array - Phase 6 SEO Schema hotfix to prevent crashes"""
    if v is None:
        return []
    if not isinstance(v, list):
        raise ValueError("topics must be an array of strings")
    result = []
    for item in v:
        if not isinstance(item, str):
            raise ValueError(f"topics array must contain only strings, got {type(item).__name__}")
        if len(item) > 200:
            raise ValueError(f"topic string too long (max 200 chars): {item[:50]}...")
        result.append(item.strip())
    return result
```

### 2. Added `topics` field to `SearchRequest` (routers/search.py)
```python
topics: list[str] = []
```

### 3. Added `topics` field to `HybridSearchRequest` (routers/search.py)
```python
topics: list[str] = []
```

## Error Handling
The existing `validation_exception_handler` in `middleware/error_handling.py` already:
- Returns HTTP 422 JSON response for validation errors
- Includes field-specific error messages
- Logs the error with trace ID for debugging
- Never crashes the route - returns structured error response

Example error response for malformed topics:
```json
{
  "trace_id": "abc-123",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "body.topics": {
          "message": "topics array must contain only strings, got int",
          "type": "value_error"
        }
      }
    }
  },
  "status": 422
}
```

## Testing Verification
The fix ensures:
1. Empty topics array defaults to `[]` - no crash
2. Null/None topics converts to `[]` - no crash  
3. Non-array topics returns 422 with friendly error
4. Non-string elements in topics array returns 422 with friendly error
5. String topics longer than 200 chars returns 422 with friendly error

## Files Modified
- `schemas/strict_validation.py` - Added topics field with validator
- `routers/search.py` - Added topics field to SearchRequest and HybridSearchRequest

## Related
- Phase 6 SEO Enhancement Engine
- Scholarship API search endpoints
- Pydantic validation error handling
