# Agent Bridge Integration - FastAPI Scholarship API

The Scholarship Discovery & Search API now includes **Agent Bridge** functionality for integration with the Auto Command Center orchestration system. This enables task-based coordination across multiple services while preserving all existing API functionality.

## Overview

The Agent Bridge transforms the Scholarship API into a **satellite agent** that can:
- Receive and execute tasks from the Command Center
- Register capabilities and maintain heartbeat connectivity  
- Publish events for system-wide coordination
- Participate in multi-service workflows

## Environment Variables

### Required for Command Center Integration

```bash
# Command Center Configuration
COMMAND_CENTER_URL=https://auto-com-center-jamarrlmayes.replit.app
SHARED_SECRET=<shared_secret_string>
AGENT_NAME=scholarship_api
AGENT_ID=scholarship_api  
AGENT_BASE_URL=https://your-scholarship-api.replit.app

# JWT Configuration (for inter-service auth)
JWT_ISSUER=auto-com-center
JWT_AUDIENCE=scholar-sync-agents
```

### Optional Agent Settings

```bash
# Agent Identity (defaults provided)
AGENT_NAME=scholarship_api
AGENT_ID=scholarship_api
```

## Agent Bridge Endpoints

### Core Agent Endpoints

#### `POST /agent/task`
Receives tasks from Command Center for execution.

**Request Headers:**
- `Authorization: Bearer <jwt_token>`
- `X-Agent-Id: scholarship_api`
- `X-Trace-Id: <trace_id>`

**Request Body:**
```json
{
  "task_id": "task_12345abc",
  "action": "scholarship_api.search",
  "payload": {
    "query": "STEM scholarships",
    "filters": {
      "min_amount": 5000,
      "fields_of_study": ["engineering"]
    },
    "pagination": {"page": 1, "size": 10}
  },
  "reply_to": "https://command-center.com/orchestrator/tasks/task_12345abc/callback",
  "trace_id": "trace_67890def",
  "requested_by": "user_operations"
}
```

**Response:** `202 Accepted` with immediate acknowledgment

#### `GET /agent/capabilities`
Returns agent capabilities and status.

**Response:**
```json
{
  "agent_id": "scholarship_api",
  "name": "Scholarship Discovery & Search API",
  "capabilities": [
    "scholarship_api.search",
    "scholarship_api.eligibility_check",
    "scholarship_api.recommendations"
  ],
  "version": "1.0.0",
  "health": "healthy"
}
```

#### `GET /agent/health`
Agent health check with orchestrator context.

**Response:**
```json
{
  "status": "healthy",
  "agent_id": "scholarship_api",
  "agent_name": "scholarship_api",
  "version": "1.0.0",
  "command_center_configured": true,
  "shared_secret_configured": true,
  "capabilities": ["scholarship_api.search", "..."]
}
```

#### `POST /agent/register`
Handles registration requests from Command Center (JWT protected).

#### `POST /agent/events` 
Receives internal events for forwarding to Command Center (optional).

## Supported Actions

### `scholarship_api.search`
Executes scholarship search using existing search functionality.

**Task Payload:**
```json
{
  "query": "engineering scholarships",
  "filters": {
    "min_amount": 1000,
    "fields_of_study": ["engineering"],
    "min_gpa": 3.0,
    "scholarship_types": ["merit_based"],
    "states": ["CA", "NY"],
    "citizenship": "US"
  },
  "pagination": {
    "page": 1,
    "size": 20
  }
}
```

**Result:**
```json
{
  "items": [
    {
      "id": "sch_001",
      "name": "National Merit Engineering Scholarship",
      "amount": 15000,
      "organization": "Engineering Excellence Foundation"
    }
  ],
  "total": 25,
  "took_ms": 45,
  "page": 1,
  "page_size": 20
}
```

### `scholarship_api.eligibility_check` (Planned)
Individual or bulk eligibility analysis.

### `scholarship_api.recommendations` (Planned)
Generate scholarship recommendations for user profiles.

## Security

### JWT Authentication
- Uses `HS256` algorithm with shared secret
- Required headers: `Authorization: Bearer <token>`, `X-Agent-Id`
- Token validation includes issuer/audience verification
- 5-minute token expiry for security

### Rate Limiting
- Task endpoint: 5 requests/minute
- Event endpoint: 10 requests/minute
- Integrated with existing rate limiting system

### Request Validation
- Strict Pydantic schemas for all task payloads
- Input sanitization and size limits
- Structured error responses with trace IDs

## Operational Behavior

### Startup Registration
- Automatically registers with Command Center on startup
- Sends heartbeat every 60 seconds to maintain connectivity
- Graceful fallback if Command Center unavailable

### Task Execution
1. **Receive Task:** Accept task with 202 status
2. **Acknowledge:** Send `accepted` status to Command Center
3. **Execute:** Process task asynchronously using existing services
4. **Report:** Send result/error back to Command Center
5. **Events:** Publish execution events for monitoring

### Event Publishing
- Task lifecycle events (received, started, completed, failed)
- Search execution metrics
- Error conditions and recovery

### Error Handling
- Failed tasks return structured error responses
- Retry logic handled by Command Center
- Graceful degradation when Command Center unavailable

## Integration Examples

### Command Center Task Dispatch
```bash
# Dispatch search task
curl -X POST https://command-center.com/orchestrator/tasks/dispatch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "action": "scholarship_api.search",
    "payload": {
      "query": "STEM scholarships",
      "filters": {"min_amount": 5000},
      "pagination": {"page": 1, "size": 10}
    },
    "requested_by": "user_dashboard"
  }'
```

### Direct Agent Task (Testing)
```bash
# Send task directly to agent (requires JWT)
curl -X POST http://localhost:5000/agent/task \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Agent-Id: scholarship_api" \
  -d '{
    "task_id": "test_123",
    "action": "scholarship_api.search", 
    "payload": {
      "query": "engineering",
      "filters": {},
      "pagination": {"page": 1, "size": 5}
    },
    "reply_to": "https://example.com/callback",
    "trace_id": "trace_456",
    "requested_by": "test_user"
  }'
```

## Workflow Integration

The Agent Bridge enables complex multi-service workflows:

1. **Search → Match → Generate**
   - `scholarship_api.search` → returns scholarships
   - `student_pilot.match_scholarships` → analyzes fit
   - `auto_page_maker.generate_page` → creates landing page

2. **Analysis → Outreach → Compliance**
   - `scholarship_api.eligibility_check` → validates eligibility
   - `scholarship_sage.outreach_chat` → initiates contact
   - `scholarship_agent.compliance_check` → ensures compliance

## Deployment Considerations

### Development
- Command Center integration optional (graceful fallback)
- All existing endpoints remain unchanged
- Agent Bridge adds orchestration capabilities

### Production  
- Configure `SHARED_SECRET` and `COMMAND_CENTER_URL`
- Ensure JWT settings match Command Center configuration
- Monitor agent registration and heartbeat status
- Set appropriate rate limits for task execution

### Monitoring
- Agent health: `GET /agent/health`
- Task status via Command Center: `GET /orchestrator/tasks/{task_id}`
- Event logs: `GET /orchestrator/events`
- Metrics: Standard `/metrics` endpoint includes agent stats

## Backward Compatibility

**✅ Full Backward Compatibility**
- All existing API endpoints unchanged
- No impact on current functionality
- Agent Bridge is additive enhancement
- Can be disabled by omitting environment variables

The Scholarship API continues to function independently while gaining orchestration superpowers when integrated with the Command Center ecosystem.

---

**Status:** ✅ Agent Bridge implemented and ready for Command Center integration
**Version:** 1.0.0 with orchestration support
**Last Updated:** August 18, 2025