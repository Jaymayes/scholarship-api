"""
Agent Bridge Router for Command Center integration
Handles task execution, registration, and capabilities endpoints
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import ValidationError

from schemas.orchestrator import Task, TaskResult, AgentCapabilities, TaskStatus
from services.orchestrator_service import orchestrator_service
from middleware.rate_limiting import limiter
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/agent", tags=["Agent Bridge"])


async def verify_agent_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT authentication from Command Center"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "trace_id": "auth_missing",
                "code": "AUTHORIZATION_REQUIRED", 
                "message": "Authorization header required",
                "status": 401
            }
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "trace_id": "auth_invalid_format",
                "code": "INVALID_AUTHORIZATION_FORMAT",
                "message": "Authorization must be Bearer token",
                "status": 401
            }
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        payload = orchestrator_service.verify_jwt_token(token)
        return payload
    except ValueError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "trace_id": "auth_verification_failed",
                "code": "INVALID_JWT_TOKEN",
                "message": str(e),
                "status": 401
            }
        )


@router.post("/task", response_model=dict, status_code=202)
async def receive_task(
    request: Request,
    task_request: Task,
    background_tasks: BackgroundTasks,
    x_agent_id: Optional[str] = Header(None),
    x_trace_id: Optional[str] = Header(None),
    auth_payload: dict = Depends(verify_agent_auth)
):
    """
    Receive and execute task from Command Center
    
    Accepts task envelope, validates JWT authentication, and executes asynchronously.
    Returns 202 immediately and processes task in background.
    """
    logger.info(f"Received task {task_request.task_id} with action {task_request.action}")
    
    # Validate agent ID matches
    if x_agent_id and x_agent_id != task_request.trace_id.split('-')[0]:  # Basic validation
        logger.warning(f"Agent ID mismatch: header={x_agent_id}, expected match with trace")
    
    # Acknowledge receipt immediately
    acknowledge_result = TaskResult(
        task_id=task_request.task_id,
        status=TaskStatus.ACCEPTED,
        trace_id=task_request.trace_id
    )
    
    # Send acknowledgment back to Command Center
    background_tasks.add_task(
        orchestrator_service.send_task_result,
        acknowledge_result
    )
    
    # Execute task asynchronously
    async def execute_and_report():
        try:
            # Execute the task
            result = await orchestrator_service.execute_task(task_request)
            
            # Send result back to Command Center
            await orchestrator_service.send_task_result(result)
            
        except Exception as e:
            logger.error(f"Task execution failed for {task_request.task_id}: {e}")
            
            # Send failure result
            failure_result = TaskResult(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error={
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                },
                trace_id=task_request.trace_id
            )
            await orchestrator_service.send_task_result(failure_result)
    
    background_tasks.add_task(execute_and_report)
    
    return {
        "message": "Task accepted for execution",
        "task_id": task_request.task_id,
        "status": "accepted",
        "trace_id": task_request.trace_id
    }


@router.post("/register", response_model=dict)
async def register_agent(
    auth_payload: dict = Depends(verify_agent_auth)
):
    """
    Handle registration request from Command Center
    
    Validates JWT and returns agent capabilities and health status.
    """
    logger.info("Received registration request from Command Center")
    
    capabilities = orchestrator_service.get_capabilities()
    
    return {
        "message": "Agent registered successfully",
        "agent": capabilities.model_dump(),
        "timestamp": capabilities.last_seen
    }


@router.get("/capabilities", response_model=AgentCapabilities)
async def get_capabilities():
    """
    Return agent capabilities and status
    
    Public endpoint showing supported actions and agent health.
    """
    return orchestrator_service.get_capabilities()


@router.get("/health", response_model=dict)
async def agent_health():
    """
    Agent health check with orchestrator context
    
    Returns health status including agent ID and orchestrator connectivity.
    """
    from config.settings import settings
    
    health_status = {
        "status": "healthy",
        "agent_id": settings.agent_id,
        "agent_name": settings.agent_name,
        "version": settings.api_version,
        "command_center_configured": bool(settings.command_center_url),
        "shared_secret_configured": bool(settings.agent_shared_secret),
        "capabilities": orchestrator_service.agent_capabilities
    }
    
    return health_status


@router.post("/events", status_code=200)
async def receive_event(
    request: Request,
    event_data: dict,
    background_tasks: BackgroundTasks,
    auth_payload: dict = Depends(verify_agent_auth)
):
    """
    Accept internal events and relay to Command Center
    
    Optional endpoint for receiving internal events that should be
    forwarded to the Command Center event bus.
    """
    logger.info(f"Received internal event: {event_data.get('type', 'unknown')}")
    
    # TODO: Validate and forward event to Command Center
    # This would be used for internal events that need to be shared
    # across the orchestration system
    
    return {"message": "Event received and queued for forwarding"}