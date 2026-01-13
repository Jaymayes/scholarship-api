"""
Verifier Worker (saa-verifier-v2)
Purpose: Critic workflow for AI outputs. Scaffold for launch.
Protocol: AGENT3_HANDSHAKE v30
"""
import os
import time
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PORT = int(os.environ.get("PORT", 5000))
API_KEY = os.environ.get("VERIFIER_API_KEY", "")
START_TIME = time.time()
VERSION = "2.0.0"

app = FastAPI(title="Verifier Worker (saa-verifier-v2)", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    input: str
    rubric: Dict[str, Any]


class VerifyResponse(BaseModel):
    pass_: bool
    score: float
    reasons: List[str]

    class Config:
        fields = {"pass_": "pass"}


class AutoCorrectRequest(BaseModel):
    input: str
    reasons: List[str]


class AutoCorrectResponse(BaseModel):
    corrected: str
    score: float


class HealthResponse(BaseModel):
    service: str
    version: str
    uptime_s: float
    status: str


async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        return True
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def critic_stub(input_text: str, rubric: Dict[str, Any]) -> VerifyResponse:
    """
    Critic workflow stub.
    Evaluates input against rubric and returns pass/fail with reasons.
    Replaceable with actual AI critic model.
    """
    min_length = rubric.get("min_length", 50)
    required_keywords = rubric.get("required_keywords", [])
    
    reasons = []
    score = 1.0
    
    if len(input_text) < min_length:
        reasons.append(f"Input too short: {len(input_text)} < {min_length}")
        score -= 0.3
    
    for keyword in required_keywords:
        if keyword.lower() not in input_text.lower():
            reasons.append(f"Missing required keyword: {keyword}")
            score -= 0.1
    
    score = max(0.0, score)
    pass_ = score >= 0.7 and len(reasons) == 0
    
    return VerifyResponse(pass_=pass_, score=round(score, 2), reasons=reasons)


def auto_correct_stub(input_text: str, reasons: List[str]) -> AutoCorrectResponse:
    """
    Auto-correction stub.
    Attempts to fix issues identified in reasons.
    Replaceable with actual AI correction model.
    """
    corrected = input_text
    
    for reason in reasons:
        if "too short" in reason.lower():
            corrected += " [Additional content would be added here to meet length requirements.]"
        if "missing required keyword" in reason.lower():
            keyword = reason.split(":")[-1].strip()
            corrected += f" {keyword}"
    
    return AutoCorrectResponse(corrected=corrected, score=0.85)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service="saa-verifier-v2",
        version=VERSION,
        uptime_s=round(time.time() - START_TIME, 2),
        status="healthy"
    )


@app.post("/verify", response_model=VerifyResponse)
async def verify(request: VerifyRequest, x_api_key: str = Header(None)):
    await verify_api_key(x_api_key)
    return critic_stub(request.input, request.rubric)


@app.post("/auto-correct", response_model=AutoCorrectResponse)
async def auto_correct(request: AutoCorrectRequest, x_api_key: str = Header(None)):
    await verify_api_key(x_api_key)
    return auto_correct_stub(request.input, request.reasons)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
