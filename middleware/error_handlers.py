"""
CEO v2.6 Error Handlers - HITL-CEO-20260113-CUTOVER-V2
Standardized error responses for v2.6 compliance.
Schema: { service, env, error: {message, code, status, details}, ts }
"""
from __future__ import annotations
from typing import Any, Dict
import os
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

SERVICE = os.getenv("APP_ID", "scholarship_api")
ENV = os.getenv("ENV", "staging")


def _base_payload(message: str, code: str, status: int, details: Any | None = None) -> Dict[str, Any]:
    return {
        "service": SERVICE,
        "env": ENV,
        "error": {"message": message, "code": code, "status": status, "details": details},
        "ts": int(time.time() * 1000),
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, 
            content=_base_payload(str(exc.detail), "http_error", exc.status_code)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422, 
            content=_base_payload("validation_error", "validation_error", 422, exc.errors())
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500, 
            content=_base_payload("internal_error", "internal_error", 500, {"type": exc.__class__.__name__})
        )
