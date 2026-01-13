"""
OnboardingOrchestrator (onboarding-orchestrator-v2)
Purpose: Drive "First Document Upload" prompt and async processing.
Protocol: AGENT3_HANDSHAKE v30
"""
import os
import time
import uuid
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

PORT = int(os.environ.get("PORT", 5000))
DATASERVICE_URL = os.environ.get("DATASERVICE_URL", "")
DATASERVICE_API_KEY = os.environ.get("DATASERVICE_API_KEY", "")
A8_EVENTS_URL = os.environ.get("A8_EVENTS_URL", "")
START_TIME = time.time()
VERSION = "2.0.0"

app = FastAPI(title="OnboardingOrchestrator (onboarding-orchestrator-v2)", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

activation_store: Dict[str, Dict[str, Any]] = {}


class DocumentUploadedEvent(BaseModel):
    event_type: str
    document_id: str
    user_id: str
    mime: str
    size: int
    timestamp: str


class ActivationStatus(BaseModel):
    user_id: str
    status: str
    features: Optional[Dict[str, Any]] = None
    activated_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    service: str
    version: str
    uptime_s: float
    status: str


class NLPAnalysisResult(BaseModel):
    document_id: str
    mission_fit: float
    theme_keywords: List[str]
    implicit_interests: List[str]
    confidence: float


def nlp_analysis_stub(document_id: str, mime: str) -> NLPAnalysisResult:
    """
    NLP Analysis Stub - Mock implementation.
    Replaceable with actual model later.
    Returns mission/theme "implicit fit" features.
    """
    return NLPAnalysisResult(
        document_id=document_id,
        mission_fit=0.85,
        theme_keywords=["education", "stem", "leadership", "community"],
        implicit_interests=["engineering", "scholarship", "mentorship"],
        confidence=0.78
    )


async def store_features_to_dataservice(user_id: str, features: Dict[str, Any]):
    """Store derived features via DataService API."""
    if not DATASERVICE_URL:
        return
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(
                f"{DATASERVICE_URL}/users/{user_id}/features",
                json=features,
                headers={"X-API-Key": DATASERVICE_API_KEY}
            )
        except Exception:
            pass


async def emit_to_a8(event_type: str, payload: Dict[str, Any]):
    """Emit event to A8 Command Center."""
    if not A8_EVENTS_URL:
        return
    
    event = {
        "event_type": event_type,
        "source_app_id": "orchestrator-v2",
        "payload": payload,
        "ts": int(time.time() * 1000)
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(A8_EVENTS_URL, json=event)
        except Exception:
            pass


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service="onboarding-orchestrator-v2",
        version=VERSION,
        uptime_s=round(time.time() - START_TIME, 2),
        status="healthy"
    )


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding():
    """Render First Upload prompt template."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Scholar AI Advisor</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .upload-box { border: 2px dashed #007bff; border-radius: 10px; padding: 40px; text-align: center; }
            h1 { color: #333; }
            p { color: #666; }
            .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Welcome to Scholar AI Advisor</h1>
        <div class="upload-box">
            <h2>Upload your transcript or past essay</h2>
            <p>Unlock your personalized scholarship dashboard by uploading a document.</p>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept=".pdf,.doc,.docx,.txt" required>
                <br><br>
                <button type="submit" class="btn">Upload and Analyze</button>
            </form>
        </div>
        <footer style="margin-top: 40px; font-size: 12px; color: #999;">
            AI tools are for editing and discovery only; users are responsible for academic integrity.
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/events/document_uploaded")
async def document_uploaded(event: DocumentUploadedEvent):
    """Receive DocumentUploaded event from DocumentHub; queue NLP analysis."""
    analysis = nlp_analysis_stub(event.document_id, event.mime)
    
    features = {
        "document_id": event.document_id,
        "mission_fit": analysis.mission_fit,
        "theme_keywords": analysis.theme_keywords,
        "implicit_interests": analysis.implicit_interests,
        "confidence": analysis.confidence,
        "analyzed_at": datetime.utcnow().isoformat()
    }
    
    activation_store[event.user_id] = {
        "status": "ready",
        "features": features,
        "activated_at": datetime.utcnow()
    }
    
    await store_features_to_dataservice(event.user_id, features)
    
    await emit_to_a8("user_activated", {
        "user_id": event.user_id,
        "document_id": event.document_id,
        "mission_fit": analysis.mission_fit
    })
    
    return {"status": "processed", "document_id": event.document_id}


@app.get("/activation/status", response_model=ActivationStatus)
async def activation_status(user_id: str):
    """Check user activation status."""
    if user_id not in activation_store:
        return ActivationStatus(
            user_id=user_id,
            status="pending",
            features=None,
            activated_at=None
        )
    
    data = activation_store[user_id]
    return ActivationStatus(
        user_id=user_id,
        status=data["status"],
        features=data.get("features"),
        activated_at=data.get("activated_at")
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
