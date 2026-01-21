"""
Onboarding Orchestrator - First-Upload Flow Service

Implements the signup → upload → score flow with A8 telemetry integration.

Flow Sequence:
1. start_signup() → create guest user → emit GuestCreated
2. handle_upload() → store document → emit DocumentUploaded  
3. process_document() → NLP scoring (stub) → persist score → emit DocumentScored

Protocol: A8 Telemetry v3.5.1
- All events include X-Trace-Id header
- X-Idempotency-Key on all side effects
- Exponential backoff with max 3 attempts for event emission
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class FlowStatus(str, Enum):
    INITIATED = "initiated"
    GUEST_CREATED = "guest_created"
    UPLOAD_PENDING = "upload_pending"
    UPLOAD_COMPLETE = "upload_complete"
    SCORING_IN_PROGRESS = "scoring_in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class OnboardingFlow:
    trace_id: str
    status: FlowStatus
    guest_id: Optional[str] = None
    document_id: Optional[str] = None
    implicit_fit_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class OnboardingOrchestrator:
    """
    Orchestrates the First-Upload onboarding flow with A8 telemetry.
    
    Methods:
    - start_signup(): Create guest user and emit GuestCreated event
    - handle_upload(): Process document upload and emit DocumentUploaded event
    - process_document(): NLP scoring (stub) and emit DocumentScored event
    """
    
    A8_TELEMETRY_ENDPOINT = "/api/analytics/events"
    A8_FALLBACK_ENDPOINT = "/telemetry/ingest"
    MAX_RETRY_ATTEMPTS = 3
    BASE_BACKOFF_SECONDS = 0.5
    
    def __init__(self, base_url: str = "https://scholarship-api-jamarrlmayes.replit.app"):
        self.base_url = base_url
        self.flows: Dict[str, OnboardingFlow] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    def _generate_trace_id(self) -> str:
        return f"onb-{uuid.uuid4()}"
    
    def _generate_idempotency_key(self, trace_id: str, event_name: str) -> str:
        return f"{trace_id}-{event_name}-{uuid.uuid4()}"
    
    async def _emit_event_with_retry(
        self,
        event_name: str,
        trace_id: str,
        properties: Dict[str, Any],
        actor_type: str = "user"
    ) -> bool:
        """
        Emit event to A8 telemetry with exponential backoff retry.
        
        Args:
            event_name: GuestCreated, DocumentUploaded, or DocumentScored
            trace_id: Flow trace ID for correlation
            properties: Event-specific properties
            actor_type: user or system
            
        Returns:
            bool: True if event was successfully emitted
        """
        idempotency_key = self._generate_idempotency_key(trace_id, event_name)
        
        single_event = {
            "app": "onboarding_orchestrator",
            "env": "prod",
            "event_name": event_name,
            "event_type": event_name,
            "ts": datetime.utcnow().isoformat() + "Z",
            "actor_type": actor_type,
            "request_id": idempotency_key,
            "properties": properties
        }
        
        event_payload = {
            "events": [single_event]
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": trace_id,
            "X-Idempotency-Key": idempotency_key,
            "x-scholar-protocol": "v3.5.1",
            "x-event-id": idempotency_key,
            "x-app-label": "onboarding_orchestrator",
            "x-app-base-url": self.base_url,
            "x-sent-at": datetime.utcnow().isoformat() + "Z"
        }
        
        client = await self._get_http_client()
        last_error = None
        
        for attempt in range(self.MAX_RETRY_ATTEMPTS):
            try:
                backoff = self.BASE_BACKOFF_SECONDS * (2 ** attempt)
                
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{self.MAX_RETRY_ATTEMPTS} for {event_name} after {backoff}s backoff")
                    await asyncio.sleep(backoff)
                
                url = f"{self.base_url}{self.A8_TELEMETRY_ENDPOINT}"
                response = await client.post(url, json=event_payload, headers=headers)
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"✅ Event emitted: {event_name} trace_id={trace_id}")
                    return True
                
                if response.status_code == 404:
                    url = f"{self.base_url}{self.A8_FALLBACK_ENDPOINT}"
                    response = await client.post(url, json=event_payload, headers=headers)
                    
                    if response.status_code in (200, 201, 202):
                        logger.info(f"✅ Event emitted via fallback: {event_name} trace_id={trace_id}")
                        return True
                
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Event emission failed: {last_error}")
                
            except httpx.RequestError as e:
                last_error = str(e)
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
        
        logger.error(f"❌ Event emission failed after {self.MAX_RETRY_ATTEMPTS} attempts: {event_name} - {last_error}")
        return False
    
    async def start_signup(self, email: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> OnboardingFlow:
        """
        Start the onboarding flow by creating a guest user.
        
        Args:
            email: Optional email for the guest user
            metadata: Optional metadata for the guest
            
        Returns:
            OnboardingFlow: The initiated flow with trace_id and guest_id
        """
        trace_id = self._generate_trace_id()
        guest_id = f"guest-{uuid.uuid4()}"
        
        flow = OnboardingFlow(
            trace_id=trace_id,
            status=FlowStatus.INITIATED,
            guest_id=guest_id
        )
        
        self.flows[trace_id] = flow
        
        event_properties = {
            "guest_id": guest_id,
            "email_provided": email is not None,
            "metadata": metadata or {},
            "flow_trace_id": trace_id,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        asyncio.create_task(self._emit_event_with_retry(
            event_name="GuestCreated",
            trace_id=trace_id,
            properties=event_properties,
            actor_type="system"
        ))
        
        flow.status = FlowStatus.GUEST_CREATED
        flow.updated_at = datetime.utcnow()
        self.flows[trace_id] = flow
        
        logger.info(f"Onboarding started: trace_id={trace_id} guest_id={guest_id} status={flow.status}")
        return flow
    
    async def handle_upload(
        self,
        trace_id: str,
        document_content: bytes,
        filename: str,
        content_type: str = "application/pdf"
    ) -> OnboardingFlow:
        """
        Handle document upload for the onboarding flow.
        
        Args:
            trace_id: The flow trace ID from start_signup()
            document_content: Raw document bytes
            filename: Original filename
            content_type: MIME type of the document
            
        Returns:
            OnboardingFlow: Updated flow with document_id
        """
        flow = self.flows.get(trace_id)
        if not flow:
            raise ValueError(f"No onboarding flow found for trace_id: {trace_id}")
        
        if flow.status == FlowStatus.FAILED:
            raise ValueError(f"Cannot upload to failed flow: {trace_id}")
        
        flow.status = FlowStatus.UPLOAD_PENDING
        document_id = f"doc-{uuid.uuid4()}"
        flow.document_id = document_id
        
        event_properties = {
            "document_id": document_id,
            "guest_id": flow.guest_id,
            "filename": filename,
            "content_type": content_type,
            "file_size_bytes": len(document_content),
            "flow_trace_id": trace_id,
            "uploaded_at": datetime.utcnow().isoformat() + "Z"
        }
        
        asyncio.create_task(self._emit_event_with_retry(
            event_name="DocumentUploaded",
            trace_id=trace_id,
            properties=event_properties,
            actor_type="user"
        ))
        
        flow.status = FlowStatus.UPLOAD_COMPLETE
        flow.updated_at = datetime.utcnow()
        self.flows[trace_id] = flow
        
        logger.info(f"Upload handled: trace_id={trace_id} document_id={document_id} status={flow.status}")
        return flow
    
    async def process_document(self, trace_id: str) -> OnboardingFlow:
        """
        Process document with NLP scoring (stub) and emit DocumentScored event.
        
        Args:
            trace_id: The flow trace ID
            
        Returns:
            OnboardingFlow: Updated flow with implicit_fit_score
        """
        flow = self.flows.get(trace_id)
        if not flow:
            raise ValueError(f"No onboarding flow found for trace_id: {trace_id}")
        
        if flow.status != FlowStatus.UPLOAD_COMPLETE:
            raise ValueError(f"Cannot process document in status: {flow.status}")
        
        if not flow.document_id:
            raise ValueError(f"No document_id for flow: {trace_id}")
        
        flow.status = FlowStatus.SCORING_IN_PROGRESS
        flow.updated_at = datetime.utcnow()
        
        implicit_fit_score = await self._nlp_score_stub(flow.document_id)
        flow.implicit_fit_score = implicit_fit_score
        
        event_properties = {
            "document_id": flow.document_id,
            "guest_id": flow.guest_id,
            "implicit_fit_score": implicit_fit_score,
            "flow_trace_id": trace_id,
            "scoring_model": "nlp_stub_v1",
            "scored_at": datetime.utcnow().isoformat() + "Z"
        }
        
        asyncio.create_task(self._emit_event_with_retry(
            event_name="DocumentScored",
            trace_id=trace_id,
            properties=event_properties,
            actor_type="system"
        ))
        
        flow.status = FlowStatus.COMPLETED
        flow.updated_at = datetime.utcnow()
        self.flows[trace_id] = flow
        
        logger.info(f"Document processed: trace_id={trace_id} score={implicit_fit_score} status={flow.status}")
        return flow
    
    async def _nlp_score_stub(self, document_id: str) -> float:
        """
        NLP scoring stub - returns a mock implicit fit score.
        
        This is a placeholder for the actual NLP scoring service.
        See nlp_scoring_contract.md for the full interface contract.
        
        Args:
            document_id: The document to score
            
        Returns:
            float: Implicit fit score between 0.0 and 1.0
        """
        await asyncio.sleep(0.1)
        
        import hashlib
        hash_val = int(hashlib.md5(document_id.encode()).hexdigest()[:8], 16)
        score = 0.5 + (hash_val % 50) / 100.0
        
        return round(score, 4)
    
    def get_flow_status(self, trace_id: str) -> Optional[OnboardingFlow]:
        """
        Get the current status of an onboarding flow.
        
        Args:
            trace_id: The flow trace ID
            
        Returns:
            OnboardingFlow or None if not found
        """
        return self.flows.get(trace_id)
    
    def to_dict(self, flow: OnboardingFlow) -> Dict[str, Any]:
        """Convert OnboardingFlow to dictionary for API response."""
        return {
            "trace_id": flow.trace_id,
            "status": flow.status.value,
            "guest_id": flow.guest_id,
            "document_id": flow.document_id,
            "implicit_fit_score": flow.implicit_fit_score,
            "created_at": flow.created_at.isoformat() + "Z",
            "updated_at": flow.updated_at.isoformat() + "Z",
            "error_message": flow.error_message
        }


onboarding_orchestrator = OnboardingOrchestrator()
