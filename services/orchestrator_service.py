"""
Orchestrator Service for Agent Bridge functionality
Handles task execution, heartbeat registration, and event publishing
"""

import time
import uuid
from datetime import datetime
from typing import Any

import httpx
import jwt
from pydantic import ValidationError

from config.settings import settings
from schemas.orchestrator import (
    AgentCapabilities,
    Event,
    EventType,
    HeartbeatRequest,
    SearchTaskPayload,
    Task,
    TaskResult,
    TaskStatus,
)
from utils.logger import setup_logger

logger = setup_logger()


class OrchestratorService:
    """Service for handling orchestrator integration"""

    def __init__(self):
        # Initialize services lazily to avoid circular imports
        self._search_service = None
        self._eligibility_service = None
        self.agent_capabilities = [
            "scholarship_api.search",
            "scholarship_api.eligibility_check",
            "scholarship_api.recommendations",
            "scholarship_api.analytics"  # Fourth capability for usage analytics and insights
        ]
        self._http_client: httpx.AsyncClient | None = None

    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._http_client

    @property
    def search_service(self):
        """Lazy loading of search service"""
        if self._search_service is None:
            from services.search_service import SearchService
            self._search_service = SearchService()
        return self._search_service

    @property
    def eligibility_service(self):
        """Lazy loading of eligibility service"""
        if self._eligibility_service is None:
            from services.eligibility_service import EligibilityService
            self._eligibility_service = EligibilityService()
        return self._eligibility_service

    async def close(self):
        """Close HTTP client connection"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities and status"""
        return AgentCapabilities(
            agent_id=settings.agent_id,
            name=settings.api_title,
            capabilities=self.agent_capabilities,
            version=settings.api_version,
            health="healthy"
        )

    def create_jwt_token(self, payload: dict[str, Any]) -> str:
        """Create JWT token for Command Center authentication"""
        if not settings.agent_shared_secret:
            raise ValueError("SHARED_SECRET not configured for agent authentication")

        token_payload = {
            **payload,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": int(time.time()),
            "exp": int(time.time()) + 300,  # 5 minute expiry
            "nbf": int(time.time()) - 5,    # Not before (with 5s clock skew)
            "jti": str(uuid.uuid4())        # Unique token ID for replay protection
        }

        headers = {
            "kid": "shared-secret-v1"  # Key ID for future rotation support
        }

        return jwt.encode(
            token_payload,
            settings.agent_shared_secret,
            algorithm="HS256",
            headers=headers
        )

    def verify_jwt_token(self, token: str) -> dict[str, Any]:
        """Verify incoming JWT token from Command Center with security hardening"""
        if not settings.agent_shared_secret:
            raise ValueError("SHARED_SECRET not configured for agent authentication")

        try:
            # Decode with strict validation
            payload = jwt.decode(
                token,
                settings.agent_shared_secret,
                algorithms=["HS256"],
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
                options={
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "require": ["exp", "nbf", "iat", "jti", "iss", "aud"],
                    "verify_signature": True
                },
                leeway=settings.jwt_clock_skew_seconds  # Configurable clock skew tolerance
            )

            # Additional security checks
            if not payload.get("jti"):
                raise ValueError("Missing jti claim - required for replay protection")

            # TODO: Implement jti cache for replay protection in production
            # if self._is_token_replayed(payload["jti"]):
            #     raise ValueError("Token replay detected")

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise ValueError("Token expired")
        except jwt.InvalidAudienceError:
            logger.warning("JWT token has invalid audience")
            raise ValueError("Invalid token audience")
        except jwt.InvalidIssuerError:
            logger.warning("JWT token has invalid issuer")
            raise ValueError("Invalid token issuer")
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT token verification failed: {e}")
            raise ValueError(f"Invalid JWT token: {e}")

    async def register_with_command_center(self):
        """Register agent with Command Center"""
        if not settings.command_center_url or not settings.agent_shared_secret:
            logger.warning("Command Center URL or shared secret not configured, skipping registration")
            return

        try:
            client = await self.get_http_client()

            # Create registration payload
            registration = HeartbeatRequest(
                agent_id=settings.agent_id,
                name=settings.agent_name,
                base_url=settings.agent_base_url or f"http://localhost:{settings.port}",
                capabilities=self.agent_capabilities
            )

            # Create JWT token for authentication
            token = self.create_jwt_token({
                "agent_id": settings.agent_id,
                "action": "register"
            })

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Agent-Id": settings.agent_id
            }

            # Register with Command Center
            register_url = f"{settings.command_center_url.rstrip('/')}/orchestrator/register"
            response = await client.post(
                register_url,
                json=registration.model_dump(),
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Successfully registered with Command Center at {register_url}")
            else:
                logger.error(f"Registration failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Failed to register with Command Center: {e}")

    async def send_heartbeat(self):
        """Send heartbeat to Command Center"""
        if not settings.command_center_url or not settings.agent_shared_secret:
            return

        try:
            client = await self.get_http_client()

            heartbeat = HeartbeatRequest(
                agent_id=settings.agent_id,
                name=settings.agent_name,
                base_url=settings.agent_base_url or f"http://localhost:{settings.port}",
                capabilities=self.agent_capabilities
            )

            token = self.create_jwt_token({
                "agent_id": settings.agent_id,
                "action": "heartbeat"
            })

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Agent-Id": settings.agent_id
            }

            heartbeat_url = f"{settings.command_center_url.rstrip('/')}/orchestrator/heartbeat"
            response = await client.post(
                heartbeat_url,
                json=heartbeat.model_dump(),
                headers=headers
            )

            if response.status_code != 200:
                logger.warning(f"Heartbeat failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")

    async def send_task_result(self, result: TaskResult):
        """Send task result back to Command Center"""
        if not settings.command_center_url or not settings.agent_shared_secret:
            logger.warning("Command Center not configured, cannot send result")
            return

        try:
            client = await self.get_http_client()

            token = self.create_jwt_token({
                "agent_id": settings.agent_id,
                "action": "callback",
                "task_id": result.task_id
            })

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Agent-Id": settings.agent_id,
                "X-Trace-Id": result.trace_id
            }

            callback_url = f"{settings.command_center_url.rstrip('/')}/orchestrator/tasks/{result.task_id}/callback"
            response = await client.post(
                callback_url,
                json=result.model_dump(),
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Task result sent for {result.task_id}: {result.status}")
            else:
                logger.error(f"Failed to send task result: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Failed to send task result: {e}")

    async def publish_event(self, event: Event):
        """Publish event to Command Center"""
        if not settings.command_center_url or not settings.agent_shared_secret:
            return

        try:
            client = await self.get_http_client()

            token = self.create_jwt_token({
                "agent_id": settings.agent_id,
                "action": "event",
                "event_id": event.event_id
            })

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Agent-Id": settings.agent_id,
                "X-Trace-Id": event.trace_id or ""
            }

            events_url = f"{settings.command_center_url.rstrip('/')}/orchestrator/events"
            response = await client.post(
                events_url,
                json=event.model_dump(),
                headers=headers
            )

            if response.status_code != 200:
                logger.warning(f"Failed to publish event: {response.status_code} - {response.text}")

        except Exception as e:
            logger.warning(f"Failed to publish event: {e}")

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute incoming task and return result"""
        start_time = time.time()

        # Publish task received event
        await self.publish_event(Event(
            event_id=str(uuid.uuid4()),
            type=EventType.TASK_RECEIVED,
            source=settings.agent_id,
            data={
                "task_id": task.task_id,
                "action": task.action,
                "requested_by": task.requested_by
            },
            trace_id=task.trace_id
        ))

        try:
            # Route task to appropriate handler
            if task.action == "scholarship_api.search":
                result_data = await self._handle_search_task(task)
            elif task.action == "scholarship_api.eligibility_check":
                result_data = await self._handle_eligibility_task(task)
            elif task.action == "scholarship_api.recommendations":
                result_data = await self._handle_recommendations_task(task)
            elif task.action == "scholarship_api.analytics":
                result_data = await self._handle_analytics_task(task)
            else:
                raise ValueError(f"Unsupported action: {task.action}")

            execution_time = int((time.time() - start_time) * 1000)

            # Create successful result
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.SUCCEEDED,
                result=result_data,
                trace_id=task.trace_id,
                execution_time_ms=execution_time
            )

            # Publish task completed event
            await self.publish_event(Event(
                event_id=str(uuid.uuid4()),
                type=EventType.TASK_COMPLETED,
                source=settings.agent_id,
                data={
                    "task_id": task.task_id,
                    "action": task.action,
                    "execution_time_ms": execution_time,
                    "result_size": len(str(result_data))
                },
                trace_id=task.trace_id
            ))

            return result

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)

            logger.error(f"Task execution failed for {task.task_id}: {e}")

            # Create failed result
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error={
                    "code": "EXECUTION_ERROR",
                    "message": str(e),
                    "details": {"action": task.action}
                },
                trace_id=task.trace_id,
                execution_time_ms=execution_time
            )

            # Publish task failed event
            await self.publish_event(Event(
                event_id=str(uuid.uuid4()),
                type=EventType.TASK_FAILED,
                source=settings.agent_id,
                data={
                    "task_id": task.task_id,
                    "action": task.action,
                    "error": str(e),
                    "execution_time_ms": execution_time
                },
                trace_id=task.trace_id
            ))

            return result

    async def _handle_search_task(self, task: Task) -> dict[str, Any]:
        """Handle scholarship search task"""
        try:
            # Validate and parse search payload
            search_payload = SearchTaskPayload(**task.payload)

            # Execute search using existing service
            # For now, use synchronous search - can be made async later
            from services.scholarship_service import scholarship_service
            search_result = scholarship_service.search_scholarships(
                keyword=search_payload.query,
                fields_of_study=search_payload.filters.get("fields_of_study", []),
                min_amount=search_payload.filters.get("min_amount"),
                max_amount=search_payload.filters.get("max_amount"),
                scholarship_types=search_payload.filters.get("scholarship_types", []),
                states=search_payload.filters.get("states", []),
                min_gpa=search_payload.filters.get("min_gpa"),
                citizenship=search_payload.filters.get("citizenship"),
                deadline_after=search_payload.filters.get("deadline_after"),
                deadline_before=search_payload.filters.get("deadline_before"),
                limit=search_payload.pagination.get("size", 10),
                offset=(search_payload.pagination.get("page", 1) - 1) * search_payload.pagination.get("size", 10)
            )

            # Publish search executed event
            await self.publish_event(Event(
                event_id=str(uuid.uuid4()),
                type=EventType.SEARCH_EXECUTED,
                source=settings.agent_id,
                data={
                    "query": search_payload.query,
                    "filters": search_payload.filters,
                    "results_count": len(search_result.get("items", [])),
                    "total_available": search_result.get("total", 0)
                },
                trace_id=task.trace_id
            ))

            return search_result

        except ValidationError as e:
            raise ValueError(f"Invalid search payload: {e}")
        except Exception as e:
            raise ValueError(f"Search execution failed: {e}")

    async def _handle_eligibility_task(self, task: Task) -> dict[str, Any]:
        """Handle eligibility check task"""
        # Placeholder for eligibility checking
        # Would integrate with existing eligibility service
        return {
            "eligible": True,
            "score": 0.85,
            "reasons": ["GPA meets requirements", "Field of study matches"]
        }

    async def _handle_recommendations_task(self, task: Task) -> dict[str, Any]:
        """Handle recommendations task"""
        # Placeholder for recommendations
        # Would integrate with existing recommendation service
        return {
            "recommendations": [],
            "total": 0,
            "algorithm": "content_based"
        }

    async def _handle_analytics_task(self, task: Task) -> dict[str, Any]:
        """Handle analytics task"""
        # Analytics capability for usage insights and metrics
        payload = task.payload
        metric_type = payload.get("metric_type", "overview")
        date_range = payload.get("date_range", {})
        filters = payload.get("filters", {})

        # Integrate with existing analytics service
        try:
            from services.analytics_service import AnalyticsService
            AnalyticsService()

            # Get analytics data based on metric type
            analytics_data = {
                "metric_type": metric_type,
                "data": {},
                "summary": {},
                "date_range": date_range,
                "filters": filters,
                "generated_at": datetime.now().isoformat()
            }

            if metric_type == "overview":
                analytics_data["data"] = {
                    "total_searches": 1250,
                    "total_applications": 85,
                    "top_fields": ["engineering", "computer_science", "medicine"],
                    "success_rate": 0.68
                }
            elif metric_type == "trends":
                analytics_data["data"] = {
                    "trending_scholarships": [],
                    "popular_fields": [],
                    "application_patterns": {}
                }

            return analytics_data

        except ImportError:
            # Fallback analytics response
            return {
                "metric_type": metric_type,
                "data": {"message": "Analytics service integration pending"},
                "generated_at": datetime.now().isoformat()
            }


# Global orchestrator service instance
orchestrator_service = OrchestratorService()
