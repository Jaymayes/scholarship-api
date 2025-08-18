"""
Orchestrator schemas for Agent Bridge integration
Defines Task, Result, and Event models for Command Center communication
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    """Task execution status"""
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress" 
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EventType(str, Enum):
    """Event types for Command Center"""
    TASK_RECEIVED = "task_received"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    SEARCH_EXECUTED = "search_executed"
    ERROR_OCCURRED = "error_occurred"


class TaskResources(BaseModel):
    """Task execution resources and constraints"""
    priority: int = Field(default=1, ge=1, le=10, description="Task priority (1-10)")
    timeout_ms: int = Field(default=30000, ge=1000, le=300000, description="Task timeout in milliseconds")
    retry: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")


class Task(BaseModel):
    """Incoming task from Command Center"""
    task_id: str = Field(..., description="Unique task identifier")
    action: str = Field(..., description="Action to execute (e.g., scholarship_api.search)")
    payload: Dict[str, Any] = Field(..., description="Task payload with action-specific data")
    reply_to: str = Field(..., description="Command Center callback URL")
    trace_id: str = Field(..., description="Request tracing identifier")
    requested_by: str = Field(..., description="Identity of request originator")
    resources: Optional[TaskResources] = Field(default_factory=TaskResources, description="Task execution resources")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "task_12345abc",
                "action": "scholarship_api.search",
                "payload": {
                    "query": "STEM scholarships",
                    "filters": {
                        "min_amount": 5000,
                        "fields_of_study": ["engineering", "computer_science"]
                    },
                    "pagination": {"page": 1, "size": 10}
                },
                "reply_to": "https://command-center.com/orchestrator/tasks/task_12345abc/callback",
                "trace_id": "trace_67890def",
                "requested_by": "user_operations",
                "resources": {
                    "priority": 3,
                    "timeout_ms": 15000,
                    "retry": 2
                }
            }
        }
    }


class TaskError(BaseModel):
    """Task execution error details"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class TaskResult(BaseModel):
    """Task execution result sent back to Command Center"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Task execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[TaskError] = Field(None, description="Error details if failed")
    trace_id: str = Field(..., description="Request tracing identifier")
    execution_time_ms: Optional[int] = Field(None, description="Task execution duration")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "task_12345abc",
                "status": "succeeded",
                "result": {
                    "items": [{"id": "sch_001", "name": "STEM Excellence Award"}],
                    "total": 15,
                    "took_ms": 45
                },
                "error": None,
                "trace_id": "trace_67890def",
                "execution_time_ms": 1250
            }
        }
    }


class Event(BaseModel):
    """Event message sent to Command Center"""
    event_id: str = Field(..., description="Unique event identifier")
    type: EventType = Field(..., description="Event type")
    source: str = Field(..., description="Event source (agent name)")
    data: Dict[str, Any] = Field(..., description="Event data")
    time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    trace_id: Optional[str] = Field(None, description="Associated trace ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "evt_789xyz",
                "type": "search_executed",
                "source": "scholarship_api",
                "data": {
                    "query": "STEM scholarships",
                    "results_count": 15,
                    "execution_time_ms": 1250
                },
                "time": "2025-08-18T22:45:00Z",
                "trace_id": "trace_67890def"
            }
        }
    }


class AgentCapabilities(BaseModel):
    """Agent capabilities and status"""
    agent_id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    capabilities: List[str] = Field(..., description="List of supported actions")
    version: str = Field(..., description="Agent version")
    health: str = Field(default="healthy", description="Agent health status")
    last_seen: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last activity timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "agent_id": "scholarship_api",
                "name": "Scholarship Discovery & Search API",
                "capabilities": [
                    "scholarship_api.search",
                    "scholarship_api.eligibility_check",
                    "scholarship_api.recommendations"
                ],
                "version": "1.0.0",
                "health": "healthy",
                "last_seen": "2025-08-18T22:45:00Z"
            }
        }
    }


class HeartbeatRequest(BaseModel):
    """Heartbeat registration request"""
    agent_id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    base_url: str = Field(..., description="Agent base URL")
    capabilities: List[str] = Field(..., description="Supported actions")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Heartbeat timestamp")


class SearchTaskPayload(BaseModel):
    """Payload schema for scholarship_api.search action"""
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    pagination: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"page": 1, "size": 10}, description="Pagination parameters")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "engineering scholarships",
                "filters": {
                    "min_amount": 1000,
                    "fields_of_study": ["engineering"],
                    "min_gpa": 3.0
                },
                "pagination": {
                    "page": 1,
                    "size": 20
                }
            }
        }
    }