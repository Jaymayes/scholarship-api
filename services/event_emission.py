"""
Event Emission Service
Fire-and-forget business event emission with error capture and circuit breaker
"""
import logging
import asyncio
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from models.business_events import BusinessEvent

logger = logging.getLogger(__name__)


class EventEmissionService:
    """
    Service for emitting business events to the central event store
    
    Features:
    - Fire-and-forget: Never blocks request paths
    - Error capture: Logs failures without raising exceptions
    - Circuit breaker: Disables emission if database unavailable
    - Async processing: Background task execution
    """
    
    def __init__(self):
        self.enabled = True
        self.failure_count = 0
        self.max_failures = 10
        self.circuit_open = False
        
        # Create async engine for event emission
        database_url = os.getenv("DATABASE_URL", "")
        if database_url.startswith("postgresql://"):
            # Convert to async driver
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.engine = create_async_engine(
            database_url,
            pool_size=2,  # Small pool for background events
            max_overflow=0,
            pool_pre_ping=True,
            echo=False
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def emit(self, event: BusinessEvent) -> bool:
        """
        Emit a business event (fire-and-forget)
        
        Args:
            event: BusinessEvent instance to emit
            
        Returns:
            bool: True if emission succeeded, False otherwise
        """
        if not self.enabled or self.circuit_open:
            logger.warning(f"Event emission disabled or circuit open: {event.event_name}")
            return False
        
        try:
            # Run in background task to avoid blocking
            asyncio.create_task(self._emit_async(event))
            return True
        except Exception as e:
            logger.error(f"Failed to create emission task for {event.event_name}: {e}")
            return False
    
    async def _emit_async(self, event: BusinessEvent):
        """Internal async emission with error handling"""
        try:
            async with self.async_session_maker() as session:
                # Insert event into business_events table
                query = text("""
                    INSERT INTO business_events 
                    (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
                    VALUES 
                    (:request_id, :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, :properties)
                """)
                
                await session.execute(query, {
                    "request_id": str(event.request_id),
                    "app": event.app,
                    "env": event.env,
                    "event_name": event.event_name,
                    "ts": event.ts,
                    "actor_type": event.actor_type,
                    "actor_id": event.actor_id,
                    "session_id": event.session_id,
                    "org_id": event.org_id,
                    "properties": event.properties
                })
                
                await session.commit()
                
                # Reset failure count on success
                self.failure_count = 0
                
                logger.info(f"✅ Event emitted: {event.event_name} (actor={event.actor_type}, id={event.actor_id})")
                
        except Exception as e:
            self.failure_count += 1
            logger.error(f"❌ Event emission failed ({self.failure_count}/{self.max_failures}): {event.event_name} - {e}")
            
            # Open circuit breaker if too many failures
            if self.failure_count >= self.max_failures:
                self.circuit_open = True
                logger.critical(f"🔴 Event emission circuit breaker OPEN - too many failures ({self.failure_count})")
    
    def emit_sync(self, event: BusinessEvent) -> bool:
        """
        Synchronous wrapper for emit (creates event loop if needed)
        
        Use this in synchronous contexts (non-async routes)
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule task
                asyncio.create_task(self._emit_async(event))
            else:
                # If no loop, run in new loop
                loop.run_until_complete(self._emit_async(event))
            return True
        except Exception as e:
            logger.error(f"Sync emission failed for {event.event_name}: {e}")
            return False
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (for admin/ops)"""
        self.circuit_open = False
        self.failure_count = 0
        logger.info("🔄 Event emission circuit breaker RESET")
    
    def get_status(self) -> dict:
        """Get current emission service status"""
        return {
            "enabled": self.enabled,
            "circuit_open": self.circuit_open,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures
        }


# Global event emission service
event_emission_service = EventEmissionService()


# Convenience functions for common events
async def emit_scholarship_viewed(
    scholarship_id: str,
    source: str,
    match_score: Optional[float] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Emit scholarship_viewed event"""
    from models.business_events import create_scholarship_viewed_event
    
    event = create_scholarship_viewed_event(
        scholarship_id=scholarship_id,
        source=source,
        match_score=match_score,
        actor_id=actor_id,
        session_id=session_id
    )
    
    await event_emission_service.emit(event)


async def emit_scholarship_saved(
    scholarship_id: str,
    match_score: Optional[float] = None,
    eligibility_score: Optional[float] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Emit scholarship_saved event"""
    from models.business_events import create_scholarship_saved_event
    
    event = create_scholarship_saved_event(
        scholarship_id=scholarship_id,
        match_score=match_score,
        eligibility_score=eligibility_score,
        actor_id=actor_id,
        session_id=session_id
    )
    
    await event_emission_service.emit(event)


async def emit_match_generated(
    student_id: str,
    num_matches: int,
    match_quality_avg: float,
    processing_time_ms: float
):
    """Emit match_generated event"""
    from models.business_events import create_match_generated_event
    
    event = create_match_generated_event(
        student_id=student_id,
        num_matches=num_matches,
        match_quality_avg=match_quality_avg,
        processing_time_ms=processing_time_ms
    )
    
    await event_emission_service.emit(event)


async def emit_application_started(
    scholarship_id: str,
    time_since_save_hours: Optional[float] = None,
    credit_cost: Optional[int] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Emit application_started event"""
    from models.business_events import create_application_started_event
    
    event = create_application_started_event(
        scholarship_id=scholarship_id,
        time_since_save_hours=time_since_save_hours,
        credit_cost=credit_cost,
        actor_id=actor_id,
        session_id=session_id
    )
    
    await event_emission_service.emit(event)


async def emit_application_submitted(
    scholarship_id: str,
    application_time_minutes: float,
    credit_spent: Optional[int] = None,
    revenue_usd: Optional[float] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Emit application_submitted event"""
    from models.business_events import create_application_submitted_event
    
    event = create_application_submitted_event(
        scholarship_id=scholarship_id,
        application_time_minutes=application_time_minutes,
        credit_spent=credit_spent,
        revenue_usd=revenue_usd,
        actor_id=actor_id,
        session_id=session_id
    )
    
    await event_emission_service.emit(event)
