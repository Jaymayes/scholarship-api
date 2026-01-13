"""
DocumentHub (document-hub-v2)
Purpose: Secure upload ingress; publishes DocumentUploaded events to Orchestrator.
Protocol: AGENT3_HANDSHAKE v30
"""
import os
import time
import uuid
import httpx
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PORT = int(os.environ.get("PORT", 5000))
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "")
API_KEY = os.environ.get("DOCUMENTHUB_API_KEY", "")
START_TIME = time.time()
VERSION = "2.0.0"

app = FastAPI(title="DocumentHub (document-hub-v2)", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UploadResponse(BaseModel):
    document_id: str
    mime: str
    size: int
    user_id: str
    uploaded_at: datetime


class HealthResponse(BaseModel):
    service: str
    version: str
    uptime_s: float
    status: str


class WebhookTestResponse(BaseModel):
    status: str
    message: str
    event_id: str


async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        return True
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


async def emit_document_uploaded(document_id: str, user_id: str, mime: str, size: int):
    """Fire-and-forget event to Orchestrator with retry and backoff."""
    if not ORCHESTRATOR_URL:
        return
    
    event = {
        "event_type": "DocumentUploaded",
        "document_id": document_id,
        "user_id": user_id,
        "mime": mime,
        "size": size,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    delays = [0.5, 1.0, 2.0]
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, delay in enumerate(delays):
            try:
                response = await client.post(
                    f"{ORCHESTRATOR_URL}/events/document_uploaded",
                    json=event,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    return
            except Exception:
                pass
            if i < len(delays) - 1:
                await asyncio.sleep(delay)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service="document-hub-v2",
        version=VERSION,
        uptime_s=round(time.time() - START_TIME, 2),
        status="healthy"
    )


@app.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    x_api_key: str = Header(None)
):
    await verify_api_key(x_api_key)
    
    contents = await file.read()
    document_id = str(uuid.uuid4())
    mime = file.content_type or "application/octet-stream"
    size = len(contents)
    
    await emit_document_uploaded(document_id, user_id, mime, size)
    
    return UploadResponse(
        document_id=document_id,
        mime=mime,
        size=size,
        user_id=user_id,
        uploaded_at=datetime.utcnow()
    )


@app.post("/webhooks/test", response_model=WebhookTestResponse)
async def webhooks_test(x_api_key: str = Header(None)):
    await verify_api_key(x_api_key)
    event_id = str(uuid.uuid4())
    return WebhookTestResponse(
        status="ok",
        message="Webhook test successful",
        event_id=event_id
    )


if __name__ == "__main__":
    import asyncio
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
