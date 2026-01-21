"""
Onboarding Router - First-Upload Flow API Endpoints

Endpoints:
- POST /api/v2/onboarding/start - Initiates signup flow
- POST /api/v2/onboarding/upload - Handles document upload
- GET /api/v2/onboarding/status/{trace_id} - Returns flow status
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Request
from pydantic import BaseModel, Field

from .orchestrator import onboarding_orchestrator, FlowStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/onboarding", tags=["Onboarding V2"])


class StartSignupRequest(BaseModel):
    email: Optional[str] = Field(None, description="Optional email for the guest user")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class StartSignupResponse(BaseModel):
    trace_id: str = Field(..., description="Flow trace ID for correlation")
    status: str = Field(..., description="Current flow status")
    guest_id: str = Field(..., description="Created guest user ID")
    created_at: str = Field(..., description="ISO timestamp of creation")
    message: str = Field(..., description="Human-readable status message")


class UploadResponse(BaseModel):
    trace_id: str = Field(..., description="Flow trace ID")
    status: str = Field(..., description="Current flow status")
    document_id: str = Field(..., description="Uploaded document ID")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Human-readable status message")


class FlowStatusResponse(BaseModel):
    trace_id: str = Field(..., description="Flow trace ID")
    status: str = Field(..., description="Current flow status")
    guest_id: Optional[str] = Field(None, description="Guest user ID")
    document_id: Optional[str] = Field(None, description="Document ID if uploaded")
    implicit_fit_score: Optional[float] = Field(None, description="NLP score if processed")
    created_at: str = Field(..., description="Flow creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ProcessDocumentRequest(BaseModel):
    trace_id: str = Field(..., description="Flow trace ID to process")


class ProcessDocumentResponse(BaseModel):
    trace_id: str = Field(..., description="Flow trace ID")
    status: str = Field(..., description="Current flow status")
    document_id: str = Field(..., description="Processed document ID")
    implicit_fit_score: float = Field(..., description="NLP implicit fit score (0.0-1.0)")
    message: str = Field(..., description="Human-readable status message")


@router.post("/start", response_model=StartSignupResponse)
async def start_onboarding(
    request: StartSignupRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Initiate the onboarding signup flow.
    
    Creates a guest user and emits GuestCreated event to A8 telemetry.
    Returns a trace_id for subsequent flow operations.
    """
    try:
        flow = await onboarding_orchestrator.start_signup(
            email=request.email,
            metadata=request.metadata
        )
        
        if flow.status == FlowStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start onboarding: {flow.error_message}"
            )
        
        return StartSignupResponse(
            trace_id=flow.trace_id,
            status=flow.status.value,
            guest_id=flow.guest_id,
            created_at=flow.created_at.isoformat() + "Z",
            message="Onboarding flow initiated successfully. Ready for document upload."
        )
        
    except Exception as e:
        logger.error(f"Error starting onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    trace_id: str = Form(..., description="Flow trace ID from /start"),
    file: UploadFile = File(..., description="Document to upload (PDF, DOC, TXT)"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Handle document upload for the onboarding flow.
    
    Accepts the document, stores it, and emits DocumentUploaded event to A8.
    The trace_id must match an active onboarding flow from /start.
    """
    try:
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        flow = await onboarding_orchestrator.handle_upload(
            trace_id=trace_id,
            document_content=content,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream"
        )
        
        if flow.status == FlowStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process upload: {flow.error_message}"
            )
        
        return UploadResponse(
            trace_id=flow.trace_id,
            status=flow.status.value,
            document_id=flow.document_id,
            filename=file.filename or "unknown",
            file_size_bytes=len(content),
            message="Document uploaded successfully. Ready for processing."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Process uploaded document with NLP scoring.
    
    Runs NLP scoring (stub) on the uploaded document and emits DocumentScored event.
    The document must be uploaded first via /upload endpoint.
    """
    try:
        flow = await onboarding_orchestrator.process_document(request.trace_id)
        
        if flow.status == FlowStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {flow.error_message}"
            )
        
        return ProcessDocumentResponse(
            trace_id=flow.trace_id,
            status=flow.status.value,
            document_id=flow.document_id,
            implicit_fit_score=flow.implicit_fit_score,
            message=f"Document processed successfully. Implicit fit score: {flow.implicit_fit_score}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{trace_id}", response_model=FlowStatusResponse)
async def get_flow_status(trace_id: str):
    """
    Get the current status of an onboarding flow.
    
    Returns the full flow state including guest_id, document_id, and scoring results.
    """
    flow = onboarding_orchestrator.get_flow_status(trace_id)
    
    if not flow:
        raise HTTPException(
            status_code=404,
            detail=f"No onboarding flow found for trace_id: {trace_id}"
        )
    
    return FlowStatusResponse(
        trace_id=flow.trace_id,
        status=flow.status.value,
        guest_id=flow.guest_id,
        document_id=flow.document_id,
        implicit_fit_score=flow.implicit_fit_score,
        created_at=flow.created_at.isoformat() + "Z",
        updated_at=flow.updated_at.isoformat() + "Z",
        error_message=flow.error_message
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for the onboarding service."""
    return {
        "status": "healthy",
        "service": "onboarding_orchestrator",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
