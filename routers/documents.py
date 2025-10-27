# Document Hub API Router
# "Upload once, use many" - OCR/NLP document processing

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from middleware.auth import User, require_auth
from middleware.rate_limiting import search_rate_limit as rate_limit
from models.document_hub import (
    AIDocumentProcessingResult,
    BulkDocumentAnalysis,
    DocumentRetrievalResponse,
    DocumentType,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from services.document_hub_service import DocumentHubService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["Document Hub"])

# Initialize services
openai_service = OpenAIService()
document_service = DocumentHubService(openai_service=openai_service)


class DocumentListResponse(BaseModel):
    """List of user documents"""
    documents: List[AIDocumentProcessingResult]
    total_count: int


@router.post("/upload", response_model=DocumentUploadResponse)
@rate_limit()
async def upload_document(
    request: Request,
    file_name: str,
    document_type: DocumentType,
    file_size: int,
    current_user: User = Depends(require_auth())
) -> DocumentUploadResponse:
    """
    Upload and initiate processing of a document
    
    **Document Types:**
    - TRANSCRIPT: Academic transcripts
    - ESSAY: Application essays
    - RECOMMENDATION: Letters of recommendation
    - TEST_SCORES: SAT/ACT/AP scores
    - AWARDS: Awards and honors documentation
    - RESUME: Student resume/CV
    - OTHER: Other supporting documents
    
    **Processing Flow:**
    1. Upload document (returns document_id)
    2. System performs OCR text extraction
    3. AI analyzes and structures data
    4. Status changes from UPLOADED → PROCESSING → READY
    
    **Usage:** "Upload once, use many" - extracted data auto-fills applications
    """
    try:
        upload_request = DocumentUploadRequest(
            file_name=file_name,
            document_type=document_type,
            file_size=file_size
        )
        
        response = await document_service.upload_document(
            user_id=current_user.user_id,
            request=upload_request
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.get("/{document_id}", response_model=AIDocumentProcessingResult)
@rate_limit()
async def get_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(require_auth())
) -> AIDocumentProcessingResult:
    """
    Get document processing status and extracted data
    
    **Status:**
    - UPLOADED: Document received, queued for processing
    - PROCESSING: OCR and AI analysis in progress
    - OCR_COMPLETE: Text extraction done, AI analysis pending
    - READY: Fully processed and ready to use
    - FAILED: Processing failed (see error details)
    
    **Returns:** Extracted text, structured data, confidence scores
    """
    try:
        if document_id not in document_service.processed_documents:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = document_service.processed_documents[document_id]
        
        # Verify ownership
        user_docs = document_service.user_documents.get(current_user.user_id, [])
        if document_id not in user_docs:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.get("/user/me", response_model=DocumentListResponse)
@rate_limit()
async def list_user_documents(
    request: Request,
    current_user: User = Depends(require_auth())
) -> DocumentListResponse:
    """
    List all documents for current user
    
    **Returns:** All uploaded documents with processing status
    **Ordered by:** Most recent first
    """
    try:
        user_doc_ids = document_service.user_documents.get(current_user.user_id, [])
        
        documents = [
            document_service.processed_documents[doc_id]
            for doc_id in user_doc_ids
            if doc_id in document_service.processed_documents
        ]
        
        # Sort by processing time (most recent first)
        documents.sort(key=lambda d: d.processed_at or datetime.min, reverse=True)
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Failed to list user documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit()
async def delete_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(require_auth())
):
    """
    Delete a document permanently
    
    **Warning:** This action cannot be undone
    """
    try:
        # Verify ownership
        user_docs = document_service.user_documents.get(current_user.user_id, [])
        if document_id not in user_docs:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from storage
        document_service.user_documents[current_user.user_id].remove(document_id)
        if document_id in document_service.processed_documents:
            del document_service.processed_documents[document_id]
        
        logger.info(f"Deleted document {document_id} for user {current_user.user_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/bulk-analyze", response_model=BulkDocumentAnalysis)
@rate_limit()
async def bulk_analyze_documents(
    request: Request,
    document_ids: List[str],
    current_user: User = Depends(require_auth())
) -> BulkDocumentAnalysis:
    """
    Analyze multiple documents for scholarship applications
    
    **Use Case:** Get holistic profile view from all uploaded documents
    **Returns:** 
    - Combined profile strength score
    - Top scholarship matches based on all documents
    - Missing information gaps
    """
    try:
        # Verify ownership of all documents
        user_docs = document_service.user_documents.get(current_user.user_id, [])
        unauthorized = [doc_id for doc_id in document_ids if doc_id not in user_docs]
        
        if unauthorized:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to documents: {unauthorized}"
            )
        
        # Get documents
        documents = []
        for doc_id in document_ids:
            if doc_id in document_service.processed_documents:
                documents.append(document_service.processed_documents[doc_id])
        
        if not documents:
            raise HTTPException(status_code=400, detail="No valid documents found")
        
        # Perform bulk analysis
        analysis = await document_service.analyze_user_documents(current_user.user_id)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk analysis failed")
