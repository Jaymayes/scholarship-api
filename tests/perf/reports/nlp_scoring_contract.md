# NLP Scoring Service Interface Contract

## Overview

This document defines the interface contract for the NLP scoring service used in the Onboarding First-Upload flow. The current implementation uses a stub; this contract specifies the expected interface for the production NLP service.

## Service Interface

### Python Abstract Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NLPScoreResult:
    """Result from NLP scoring operation."""
    document_id: str
    implicit_fit_score: float  # 0.0 to 1.0
    confidence: float  # Model confidence 0.0 to 1.0
    model_version: str
    scored_at: datetime
    metadata: Dict[str, Any]


@dataclass
class NLPScoreRequest:
    """Request for NLP scoring."""
    document_id: str
    document_content: bytes
    content_type: str  # MIME type
    context: Optional[Dict[str, Any]] = None


class INLPScoringService(ABC):
    """Interface for NLP scoring service."""
    
    @abstractmethod
    async def score_document(self, request: NLPScoreRequest) -> NLPScoreResult:
        """
        Score a document for implicit scholarship fit.
        
        Args:
            request: NLPScoreRequest containing document data
            
        Returns:
            NLPScoreResult with implicit_fit_score and metadata
            
        Raises:
            NLPScoringError: If scoring fails
            DocumentParseError: If document cannot be parsed
        """
        pass
    
    @abstractmethod
    async def batch_score(self, requests: list[NLPScoreRequest]) -> list[NLPScoreResult]:
        """
        Score multiple documents in batch.
        
        Args:
            requests: List of NLPScoreRequest objects
            
        Returns:
            List of NLPScoreResult objects (same order as requests)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check NLP service health.
        
        Returns:
            Dict with status, model_version, and metrics
        """
        pass
```

## REST API Contract

### POST /api/v1/nlp/score

Score a single document.

**Request:**
```http
POST /api/v1/nlp/score HTTP/1.1
Content-Type: application/json
X-Trace-Id: onb-550e8400-e29b-41d4-a716-446655440000
X-Idempotency-Key: score-123e4567-e89b-12d3-a456-426614174000

{
  "document_id": "doc-789e4567-e89b-12d3-a456-426614174000",
  "content_base64": "base64_encoded_document_content",
  "content_type": "application/pdf",
  "context": {
    "guest_id": "guest-123...",
    "flow_trace_id": "onb-550e8400..."
  }
}
```

**Response (200 OK):**
```json
{
  "document_id": "doc-789e4567-e89b-12d3-a456-426614174000",
  "implicit_fit_score": 0.8542,
  "confidence": 0.92,
  "model_version": "nlp-fit-v2.1.0",
  "scored_at": "2025-01-21T10:31:15.000Z",
  "metadata": {
    "keywords_detected": ["engineering", "scholarship", "gpa"],
    "document_quality_score": 0.95,
    "language": "en",
    "word_count": 1250,
    "processing_time_ms": 342
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "DocumentParseError",
  "message": "Unable to extract text from document",
  "document_id": "doc-789...",
  "details": {
    "content_type": "application/pdf",
    "reason": "PDF is encrypted or corrupted"
  }
}
```

### POST /api/v1/nlp/batch-score

Score multiple documents in batch.

**Request:**
```json
{
  "documents": [
    {
      "document_id": "doc-001",
      "content_base64": "...",
      "content_type": "application/pdf"
    },
    {
      "document_id": "doc-002",
      "content_base64": "...",
      "content_type": "text/plain"
    }
  ],
  "context": {
    "batch_id": "batch-123..."
  }
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "document_id": "doc-001",
      "implicit_fit_score": 0.8542,
      "confidence": 0.92,
      "status": "success"
    },
    {
      "document_id": "doc-002",
      "implicit_fit_score": 0.7231,
      "confidence": 0.88,
      "status": "success"
    }
  ],
  "batch_metadata": {
    "total_documents": 2,
    "successful": 2,
    "failed": 0,
    "total_processing_time_ms": 687
  }
}
```

### GET /api/v1/nlp/health

Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "model_version": "nlp-fit-v2.1.0",
  "model_loaded": true,
  "metrics": {
    "requests_processed_24h": 15420,
    "avg_latency_ms": 285,
    "p99_latency_ms": 520,
    "error_rate": 0.002
  },
  "timestamp": "2025-01-21T10:30:00.000Z"
}
```

## Scoring Model Details

### Implicit Fit Score

The `implicit_fit_score` represents how well a document (resume, essay, transcript) matches scholarship requirements. 

**Score Range:** 0.0 to 1.0

| Score Range | Interpretation |
|-------------|----------------|
| 0.85 - 1.00 | Excellent fit - strong match with scholarship criteria |
| 0.70 - 0.84 | Good fit - moderate match, potential candidate |
| 0.50 - 0.69 | Fair fit - some matching criteria, review needed |
| 0.25 - 0.49 | Weak fit - limited matching criteria |
| 0.00 - 0.24 | Poor fit - minimal or no match |

### Features Extracted

The NLP model extracts and scores the following features:

1. **Academic Indicators**
   - GPA mentions and values
   - Academic achievements
   - Honors and awards
   - Course-related keywords

2. **Financial Indicators**
   - Financial need mentions
   - First-generation student indicators
   - Work experience related to need

3. **Activity Indicators**
   - Extracurricular activities
   - Leadership positions
   - Community service
   - Sports and athletics

4. **Essay Quality** (for essay documents)
   - Writing quality score
   - Topic relevance
   - Personal story elements

## Error Codes

| Code | Error | Description |
|------|-------|-------------|
| `PARSE_ERROR` | DocumentParseError | Cannot extract text from document |
| `UNSUPPORTED_TYPE` | UnsupportedContentType | Content type not supported |
| `TIMEOUT` | ScoringTimeout | Scoring exceeded time limit |
| `MODEL_ERROR` | ModelInferenceError | ML model inference failed |
| `RATE_LIMIT` | RateLimitExceeded | Too many requests |

## Supported Content Types

| MIME Type | Extension | Notes |
|-----------|-----------|-------|
| `application/pdf` | .pdf | Standard PDF documents |
| `application/msword` | .doc | Legacy Word format |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | .docx | Modern Word format |
| `text/plain` | .txt | Plain text |
| `text/rtf` | .rtf | Rich Text Format |

## SLA Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| Single document latency (P50) | < 300ms | For documents < 5MB |
| Single document latency (P99) | < 1000ms | For documents < 5MB |
| Batch latency (10 docs) | < 2000ms | P99 |
| Availability | 99.9% | Monthly |
| Error rate | < 0.5% | Excluding client errors |

## Integration Example

```python
import httpx
from typing import Optional

class NLPScoringClient:
    """Client for NLP scoring service."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def score_document(
        self,
        document_id: str,
        content: bytes,
        content_type: str,
        trace_id: str
    ) -> dict:
        """Score a document for implicit fit."""
        import base64
        
        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": trace_id
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "document_id": document_id,
            "content_base64": base64.b64encode(content).decode(),
            "content_type": content_type
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/nlp/score",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
```

## Stub Implementation

The current OnboardingOrchestrator uses a stub implementation:

```python
async def _nlp_score_stub(self, document_id: str) -> float:
    """
    NLP scoring stub - returns a mock implicit fit score.
    
    Production implementation should call the NLP service endpoint.
    """
    await asyncio.sleep(0.1)  # Simulate processing time
    
    # Generate deterministic score based on document_id
    import hashlib
    hash_val = int(hashlib.md5(document_id.encode()).hexdigest()[:8], 16)
    score = 0.5 + (hash_val % 50) / 100.0  # Range: 0.5 - 0.99
    
    return round(score, 4)
```

To swap to production NLP service, replace the stub with the `NLPScoringClient` implementation.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-21 | Initial contract definition |
