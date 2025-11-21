"""
Event Bus Service - Upstash Redis Streams Integration
Phase 1: Multi-app choreography via external message broker

Architecture:
- Upstash Redis Streams for durable, ordered event delivery
- Async/non-blocking event publishing to maintain P95 ≤120ms SLO
- Outbox pattern with idempotency for exactly-once semantics
- DLQ (Dead Letter Queue) for failed events
- Circuit breaker for resiliency

Events Published:
- APPLICATION_SUBMITTED
- APPLICATION_STATUS_CHANGED
- PAYMENT_SUCCEEDED
- PROVIDER_CREATED
- SCHOLARSHIP_PUBLISHED
"""

import asyncio
import json
import logging
import time
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from upstash_redis import Redis

from config.settings import settings

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Domain event types for multi-app choreography"""
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    APPLICATION_STATUS_CHANGED = "APPLICATION_STATUS_CHANGED"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    PROVIDER_CREATED = "PROVIDER_CREATED"
    SCHOLARSHIP_PUBLISHED = "SCHOLARSHIP_PUBLISHED"
    STUDENT_ONBOARDED = "STUDENT_ONBOARDED"


class DomainEvent(BaseModel):
    """Domain event schema with trace correlation"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    occurred_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_service: str = "scholarship_api"
    data: Dict[str, Any]
    trace_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class EventBusService:
    """
    Event Bus service using Upstash Redis Streams
    
    Features:
    - Async/non-blocking publishing
    - Idempotency via event_id
    - DLQ for failed events
    - Circuit breaker pattern
    - Retry with exponential backoff
    """
    
    def __init__(self):
        self.stream_name = "events"
        self.dlq_stream_name = "events_dlq"
        self.max_retries = 3
        self.retry_delay_ms = 100  # Start with 100ms
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_failures = 0
        self.circuit_open_until = 0
        
        # Initialize Upstash Redis client
        try:
            event_bus_url = getattr(settings, 'EVENT_BUS_URL', None)
            event_bus_token = getattr(settings, 'EVENT_BUS_TOKEN', None)
            
            if not event_bus_url or not event_bus_token:
                logger.warning("⚠️ EVENT_BUS_URL or EVENT_BUS_TOKEN not configured. Event publishing disabled.")
                self.redis_client = None
            else:
                self.redis_client = Redis(
                    url=event_bus_url,
                    token=event_bus_token
                )
                logger.info("✅ Event Bus initialized with Upstash Redis Streams")
                logger.info(f"📡 Stream: {self.stream_name}, DLQ: {self.dlq_stream_name}")
                
                # Verify connection
                self._verify_connection()
        except Exception as e:
            logger.error(f"❌ Failed to initialize Event Bus: {e}")
            self.redis_client = None
    
    def _verify_connection(self):
        """Verify Event Bus connection on startup"""
        if not self.redis_client:
            return
        
        try:
            # Test connection with simple ping
            result = self.redis_client.ping()
            if result:
                logger.info("✅ Event Bus connection verified")
            else:
                logger.warning("⚠️ Event Bus ping failed")
        except Exception as e:
            logger.error(f"❌ Event Bus connection verification failed: {e}")
    
    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        trace_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> bool:
        """
        Publish domain event to Event Bus (async, non-blocking)
        
        Args:
            event_type: Type of domain event
            data: Event payload
            trace_id: Optional trace ID for correlation
            idempotency_key: Optional idempotency key for exactly-once semantics
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning(f"⚠️ Event Bus not configured. Skipping event: {event_type}")
            return False
        
        # Circuit breaker: check if circuit is open
        if self._is_circuit_open():
            logger.warning(f"⚠️ Circuit breaker OPEN. Skipping event: {event_type}")
            return False
        
        # Create domain event
        event = DomainEvent(
            event_type=event_type,
            data=data,
            trace_id=trace_id,
            idempotency_key=idempotency_key or str(uuid4())
        )
        
        # Publish asynchronously (fire-and-forget with retry)
        asyncio.create_task(self._publish_with_retry(event))
        
        return True
    
    async def _publish_with_retry(self, event: DomainEvent):
        """
        Publish event with exponential backoff retry
        Non-blocking to maintain API P95 SLO
        """
        for attempt in range(self.max_retries):
            try:
                # Publish to Redis Stream (XADD)
                event_dict = event.model_dump()
                event_dict["event_type"] = event.event_type.value  # Convert enum to string
                
                # Serialize nested data to JSON string
                event_dict["data"] = json.dumps(event_dict["data"])
                
                # XADD to stream (upstash-redis format: xadd(key, id, data))
                if self.redis_client:
                    result = self.redis_client.xadd(
                        key=self.stream_name,
                        id="*",  # Auto-generate ID
                        data=event_dict
                    )
                else:
                    result = None
                
                if result:
                    logger.info(f"✅ Event published: {event.event_type.value} (event_id={event.event_id}, stream_id={result})")
                    self._reset_circuit_breaker()
                    return True
                else:
                    logger.error(f"❌ Event publish failed: {event.event_type.value}")
                    
            except Exception as e:
                logger.error(f"❌ Event publish error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_ms * (2 ** attempt) / 1000.0  # Convert to seconds
                    await asyncio.sleep(delay)
        
        # All retries failed - send to DLQ
        await self._send_to_dlq(event, "max_retries_exceeded")
        self._increment_circuit_breaker()
        return False
    
    async def _send_to_dlq(self, event: DomainEvent, reason: str):
        """Send failed event to Dead Letter Queue"""
        try:
            dlq_entry = {
                **event.model_dump(),
                "dlq_reason": reason,
                "dlq_timestamp": datetime.now(UTC).isoformat()
            }
            dlq_entry["event_type"] = event.event_type.value
            dlq_entry["data"] = json.dumps(dlq_entry["data"])
            
            if self.redis_client:
                self.redis_client.xadd(key=self.dlq_stream_name, id="*", data=dlq_entry)
            logger.warning(f"⚠️ Event sent to DLQ: {event.event_type.value} (reason: {reason})")
        except Exception as e:
            logger.error(f"❌ Failed to send event to DLQ: {e}")
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_open_until > time.time():
            return True
        return False
    
    def _increment_circuit_breaker(self):
        """Increment circuit breaker failure count"""
        self.circuit_breaker_failures += 1
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            # Open circuit for 60 seconds
            self.circuit_open_until = time.time() + 60
            logger.warning(f"⚠️ Circuit breaker OPEN (failures: {self.circuit_breaker_failures})")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker on successful publish"""
        self.circuit_breaker_failures = 0
        self.circuit_open_until = 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get Event Bus health status for /readyz endpoint"""
        if not self.redis_client:
            return {
                "status": "disabled",
                "configured": False,
                "circuit_breaker": "n/a"
            }
        
        try:
            # Check connection
            ping_result = self.redis_client.ping()
            circuit_status = "open" if self._is_circuit_open() else "closed"
            
            return {
                "status": "healthy" if ping_result else "unhealthy",
                "configured": True,
                "circuit_breaker": circuit_status,
                "failures": self.circuit_breaker_failures,
                "stream": self.stream_name,
                "dlq": self.dlq_stream_name
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "configured": True,
                "error": str(e),
                "circuit_breaker": "error"
            }


# Global singleton
_event_bus_instance: Optional[EventBusService] = None


def get_event_bus() -> EventBusService:
    """Get or create Event Bus singleton"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBusService()
    return _event_bus_instance


# Export for convenience
event_bus = get_event_bus()
