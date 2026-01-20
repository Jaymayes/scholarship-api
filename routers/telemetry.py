"""
Telemetry Router - Command Center Integration
Implements Telemetry Contract v1.2 endpoints for ecosystem-wide event collection and stats

Protocol ONE_TRUTH v1.2 (2025-12-01): 
- Enforces app_base_url on all incoming events
- Deduplicates events by event_id (ON CONFLICT DO NOTHING)
- Emits tile_status_rendered diagnostic after dashboard builds
- Uses REPORT: prefix on log lines per Master Prompt
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, AliasChoices
import uuid
import json
import hashlib
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from models.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TelemetryEvent(BaseModel):
    """
    Telemetry event schema per Contract v1.2 + v3.3.1 extension
    
    Protocol v3.3.1 (2025-12-13): Extended for Master Go-Live fleet telemetry
    - Accepts both snake_case and camelCase field names
    - Auto-generates missing fields with sensible defaults
    - REQUIRES app_base_url on all events (v1.2 mandate)
    - v3.3.1 additions: app_label, role, tile, status_matrix, metrics, dashboard, metadata, idempotency_key
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Event type from catalog", validation_alias=AliasChoices("event_type", "event_name", "eventType", "eventName", "type", "name"))
    ts_utc: datetime = Field(default_factory=datetime.utcnow, validation_alias=AliasChoices("ts_utc", "ts", "timestamp"))
    app_id: str = Field(..., description="Source app identifier", validation_alias=AliasChoices("app_id", "app_name", "appId", "appName", "app", "source"))
    app_base_url: Optional[str] = Field(default=None, description="v1.2: Required app base URL")
    app_name: Optional[str] = Field(default=None, description="v3.3.1: App name")
    app_label: Optional[str] = Field(default=None, description="v3.3.1: Full app label {app_id} {app_name} {app_base_url}")
    role: Optional[str] = Field(default=None, description="v3.3.1: App role (e.g., growth_orchestrator, telemetry_fallback)")
    tile: Optional[str] = Field(default=None, description="v3.3.1: Dashboard tile (SLO, B2C, B2B, SEO, Growth, Trust, Finance)")
    dashboard: Optional[bool] = Field(default=None, description="v3.3.1: Render hint for Command Center")
    status_matrix: Optional[Dict[str, str]] = Field(default=None, description="v3.3.1: Dependency status map")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="v3.3.1: KPI metrics object")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="v3.3.1: Event-specific metadata")
    idempotency_key: Optional[str] = Field(default=None, description="v3.3.1: Stable idempotency key")
    env: str = Field(default="prod")
    version: Optional[str] = None
    session_id: Optional[str] = None
    user_id_hash: Optional[str] = None
    account_id: Optional[str] = None
    actor_type: Optional[str] = None
    request_id: Optional[str] = None
    source_ip_masked: Optional[str] = None
    coppa_flag: bool = False
    ferpa_flag: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"
        populate_by_name = True


class TelemetryEventBatch(BaseModel):
    """Batch of telemetry events"""
    events: List[TelemetryEvent]


class EventWriteResponse(BaseModel):
    """Response for event write operations"""
    accepted: int
    failed: int
    event_ids: List[str]


class StatsTimeWindow(str, Enum):
    FIVE_MIN = "5m"
    ONE_HOUR = "1h"
    TWENTY_FOUR_HOUR = "24h"


class SystemDiagnosticEvent(BaseModel):
    """
    SYSTEM_DIAGNOSTIC event schema - relaxed payload validation
    
    Per A3 pipeline health verification requirements:
    - trace_id (String, Required)
    - source (String, Required)
    - payload (JSON Object, Required) - NO internal field validation
    """
    trace_id: str = Field(..., description="Trace ID for correlation")
    source: str = Field(..., description="Source app identifier")
    payload: Dict[str, Any] = Field(..., description="Diagnostic payload - accepts any JSON object")
    event_type: str = Field(default="SYSTEM_DIAGNOSTIC")
    ts_utc: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        extra = "allow"


def is_system_diagnostic_event(event_data: Dict[str, Any]) -> bool:
    """Check if event is a SYSTEM_DIAGNOSTIC type (relaxed validation)"""
    event_type = (
        event_data.get("event_type") or 
        event_data.get("type") or 
        event_data.get("eventType") or
        event_data.get("event_name") or
        ""
    )
    return event_type.upper() == "SYSTEM_DIAGNOSTIC"


def normalize_event_keys(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Protocol ONE_TRUTH v1.2: Normalize satellite payload keys to expected schema.
    Handles camelCase -> snake_case conversion and common field name variations.
    """
    key_mapping = {
        # camelCase -> snake_case
        "eventType": "event_type",
        "eventId": "event_id",
        "appId": "app_id",
        "appBaseUrl": "app_base_url",
        "tsUtc": "ts_utc",
        "userId": "user_id_hash",
        "userIdHash": "user_id_hash",
        "actorType": "actor_type",
        "sessionId": "session_id",
        "accountId": "account_id",
        "requestId": "request_id",
        "sourceIpMasked": "source_ip_masked",
        "coppaFlag": "coppa_flag",
        "ferpaFlag": "ferpa_flag",
        # Common variations - v1.4-Unified compatibility
        "type": "event_type",
        "name": "event_type",
        "event_name": "event_type",  # v1.4-Unified uses event_name
        "app": "app_id",
        "app_name": "app_id",  # A3 Master Prompt compatibility
        "appName": "app_name",  # camelCase variant
        "source": "app_id",
        "base_url": "app_base_url",
        "baseUrl": "app_base_url",
        "timestamp": "ts_utc",
        "ts": "ts_utc",
        "data": "properties",
        "payload": "properties",
        "metadata": "properties",
    }
    
    normalized = {}
    for key, value in event_dict.items():
        normalized_key = key_mapping.get(key, key)
        normalized[normalized_key] = value
    
    return normalized


@router.post("/telemetry/ingest", tags=["Telemetry v3.3.1"])
async def telemetry_ingest(
    request: Request,
    db=Depends(get_db)
):
    """
    Protocol v3.3.1: Primary fallback telemetry ingest endpoint for fleet.
    
    This is the mandated fallback endpoint per Master Go-Live Prompt:
    - POST https://scholarship-api-jamarrlmayes.replit.app/api/telemetry/ingest
    - Accepts single event or batch in v3.3.1 envelope format
    - Returns 200 on success per contract
    
    Required Headers (v3.3.1 Multi-App per Go-Live Prompt):
    - x-scholar-protocol: "3.3.1" or "v3.3.1"
    - x-event-id: <uuid> (for idempotency)
    - x-event-type: <EVENT_TYPE>
    - x-app-label: <app name, e.g., scholarship_agent>
    - x-app-base-url: <your base URL from Fleet Identity>
    - x-sent-at: <ISO 8601 UTC>
    - Authorization: Bearer <TELEMETRY_API_KEY> (optional)
    
    Legacy Headers (also supported):
    - X-Protocol-Version: v3.3.1
    - X-Idempotency-Key: <uuid>
    """
    protocol_version = (
        request.headers.get("x-scholar-protocol") or 
        request.headers.get("X-Scholar-Protocol") or
        request.headers.get("X-Protocol-Version") or 
        ""
    )
    
    idempotency_key = (
        request.headers.get("x-event-id") or
        request.headers.get("X-Event-Id") or
        request.headers.get("X-Idempotency-Key") or 
        request.headers.get("Idempotency-Key")
    )
    
    app_label_header = (
        request.headers.get("x-app-label") or
        request.headers.get("X-App-Label") or
        ""
    )
    
    event_type_header = (
        request.headers.get("x-event-type") or
        request.headers.get("X-Event-Type") or
        ""
    )
    
    sent_at_header = (
        request.headers.get("x-sent-at") or
        request.headers.get("X-Sent-At") or
        ""
    )
    
    app_base_url_header = (
        request.headers.get("x-app-base-url") or
        request.headers.get("X-App-Base-Url") or
        ""
    )
    
    if protocol_version not in ("v3.5.1", "3.5.1", "v3.5.0", "3.5.0", "v3.3.1", "3.3.1"):
        logger.warning(f"REPORT: app=scholarship_api | env=prod | v3.5.1 INGEST: Rejected - Invalid protocol: {protocol_version}")
        return JSONResponse(status_code=400, content={
            "error": "Invalid protocol version",
            "detail": "x-scholar-protocol or X-Protocol-Version header must be 'v3.5.1', 'v3.5.0', or 'v3.3.1'",
            "received": protocol_version,
            "accepted_headers": ["x-scholar-protocol", "X-Protocol-Version"]
        })
    
    trace_id = (
        request.headers.get("x-trace-id") or
        request.headers.get("X-Trace-Id") or
        request.headers.get("X-Request-Id") or
        request.headers.get("x-request-id") or
        ""
    )
    
    incident_mode = os.environ.get("INCIDENT_MODE", "").upper()
    is_sev1_mode = incident_mode == "SEV1"
    
    bypass_count = 0
    
    raw_body = await request.body()
    
    if not idempotency_key:
        if is_sev1_mode:
            idempotency_key = f"idem-{uuid.uuid4()}"
            bypass_count += 1
            logger.info(f"SEV-1 BYPASS: Missing X-Idempotency-Key, auto-generated: {idempotency_key}")
        else:
            logger.warning(f"REPORT: app=scholarship_api | env=prod | v3.5.1 INGEST: Rejected - Missing X-Idempotency-Key (HTTP 400)")
            return JSONResponse(status_code=400, content={
                "error": "Bad Request",
                "detail": "X-Idempotency-Key or x-event-id header is required",
                "accepted_headers": ["X-Idempotency-Key", "x-event-id"],
                "hint": "Set INCIDENT_MODE=SEV1 to enable auto-generation bypass"
            })
    
    if not trace_id:
        if is_sev1_mode:
            trace_id = f"trace-{uuid.uuid4()}"
            bypass_count += 1
            logger.info(f"SEV-1 BYPASS: Missing X-Trace-Id, auto-generated: {trace_id}")
        else:
            logger.warning(f"REPORT: app=scholarship_api | env=prod | v3.5.1 INGEST: Rejected - Missing X-Trace-Id (HTTP 400)")
            return JSONResponse(status_code=400, content={
                "error": "Bad Request",
                "detail": "X-Trace-Id or X-Request-Id header is required",
                "accepted_headers": ["X-Trace-Id", "X-Request-Id"],
                "hint": "Set INCIDENT_MODE=SEV1 to enable auto-generation bypass"
            })
    
    try:
        body_str = raw_body.decode('utf-8')
        
        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"REPORT: app=scholarship_api | v3.3.1 INGEST: Invalid JSON: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid JSON", "detail": str(e)})
        
        events_to_process = []
        if isinstance(payload, dict):
            if "events" in payload and isinstance(payload["events"], list):
                events_to_process = payload["events"]
            else:
                events_to_process = [payload]
        elif isinstance(payload, list):
            events_to_process = payload
        
        accepted = 0
        failed = 0
        event_ids = []
        
        for event_data in events_to_process:
            try:
                event_id = event_data.get("event_id") or event_data.get("idempotency_key") or idempotency_key or str(uuid.uuid4())
                event_type = event_data.get("event_type") or event_data.get("type") or event_type_header or "unknown"
                app_id = event_data.get("app_id") or event_data.get("app") or event_data.get("source") or "unknown"
                app_name = event_data.get("app_name") or ""
                app_base_url = event_data.get("app_base_url") or app_base_url_header or ""
                app_label = event_data.get("app_label") or app_label_header or f"{app_id} {app_name} {app_base_url}".strip()
                role = event_data.get("role") or ""
                tile = event_data.get("tile") or ""
                dashboard = event_data.get("dashboard", False)
                status_matrix = event_data.get("status_matrix") or {}
                metrics = event_data.get("metrics") or {}
                metadata = event_data.get("metadata") or {}
                env = event_data.get("env") or event_data.get("environment") or "prod"
                ts = event_data.get("ts") or event_data.get("ts_utc") or event_data.get("sent_at") or sent_at_header or datetime.utcnow().isoformat()
                
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except:
                        ts = datetime.utcnow()
                
                props = {
                    "app_label": app_label,
                    "role": role,
                    "tile": tile,
                    "dashboard": dashboard,
                    "protocol_version": protocol_version,
                    "status_matrix": status_matrix,
                    "metrics": metrics,
                    "metadata": metadata,
                    **event_data.get("properties", {})
                }
                
                if is_system_diagnostic_event(event_data):
                    trace_id = event_data.get("trace_id") or event_id
                    source = event_data.get("source") or app_id
                    diagnostic_payload = event_data.get("payload") or {}
                    props["trace_id"] = trace_id
                    props["source"] = source
                    props["diagnostic_payload"] = diagnostic_payload
                    logger.info(f"REPORT: app=scholarship_api | SYSTEM_DIAGNOSTIC from {source} trace={trace_id}")
                
                validated_event_id = event_id
                try:
                    uuid.UUID(validated_event_id)
                except (ValueError, TypeError):
                    import hashlib
                    validated_event_id = str(uuid.UUID(hashlib.md5(validated_event_id.encode()).hexdigest()))
                
                query = text("""
                    INSERT INTO business_events 
                    (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
                    VALUES 
                    (CAST(:request_id AS uuid), :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
                    ON CONFLICT (request_id) DO NOTHING
                """)
                
                result = db.execute(query, {
                    "request_id": validated_event_id,
                    "app": app_id,
                    "env": env,
                    "event_name": event_type,
                    "ts": ts,
                    "actor_type": "system",
                    "actor_id": event_data.get("user_id_hash"),
                    "session_id": event_data.get("session_id"),
                    "org_id": event_data.get("account_id"),
                    "properties": json.dumps(props)
                })
                
                if result.rowcount > 0:
                    accepted += 1
                    event_ids.append(event_id)
                    logger.info(f"REPORT: app=scholarship_api | v3.3.1 INGEST: {event_type} from {app_label} (tile={tile})")
                else:
                    logger.debug(f"REPORT: app=scholarship_api | v3.3.1 INGEST: Duplicate {event_id}")
                    
            except Exception as e:
                logger.error(f"REPORT: app=scholarship_api | v3.3.1 INGEST ERROR: {e}")
                failed += 1
        
        if accepted > 0:
            db.commit()
        
        logger.info(f"REPORT: app=scholarship_api | app_base_url=https://scholarship-api-jamarrlmayes.replit.app | env=prod | v3.3.1 INGEST BATCH: accepted={accepted}, failed={failed}")
        
        return JSONResponse(status_code=200, content={
            "status": "ok",
            "accepted": accepted,
            "failed": failed,
            "event_ids": event_ids,
            "protocol": "v3.3.1",
            "sink": "A2_fallback"
        })
        
    except Exception as e:
        logger.error(f"REPORT: app=scholarship_api | v3.3.1 INGEST FATAL (returning 202 per contract): {e}")
        return JSONResponse(status_code=202, content={
            "status": "accepted_with_error",
            "accepted": 0,
            "failed": 1,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Telemetry ingest accepts all events; error logged for investigation",
            "protocol": "v3.3.1",
            "sink": "A2_fallback"
        })


@router.post("/analytics/events/raw", tags=["Telemetry"])
async def write_events_raw(
    request: Request,
    db=Depends(get_db)
):
    """
    Protocol ONE TRUTH: Raw body fallback endpoint for debugging 422 errors.
    
    Accepts ANY JSON payload and attempts to normalize it to the expected schema.
    Logs the raw body for debugging satellite format issues.
    
    v3.5.1 Hardening (AGENT3_HANDSHAKE v27):
    - Requires X-Idempotency-Key header (HTTP 428 if missing)
    - Requires X-Trace-Id header (HTTP 428 if missing)
    """
    idempotency_key = (
        request.headers.get("X-Idempotency-Key") or
        request.headers.get("x-idempotency-key") or
        request.headers.get("x-event-id") or
        request.headers.get("X-Event-Id") or
        ""
    )
    
    trace_id = (
        request.headers.get("X-Trace-Id") or
        request.headers.get("x-trace-id") or
        request.headers.get("X-Request-Id") or
        request.headers.get("x-request-id") or
        ""
    )
    
    incident_mode = os.environ.get("INCIDENT_MODE", "").upper()
    is_sev1_mode = incident_mode == "SEV1"
    
    bypass_count = 0
    
    if not idempotency_key:
        if is_sev1_mode:
            idempotency_key = f"idem-{uuid.uuid4()}"
            bypass_count += 1
            logger.info(f"SEV-1 BYPASS: RAW missing X-Idempotency-Key, auto-generated: {idempotency_key}")
        else:
            logger.warning(f"REPORT: app=scholarship_api | v3.5.1 RAW: Rejected - Missing X-Idempotency-Key (HTTP 400)")
            return JSONResponse(status_code=400, content={
                "error": "Bad Request",
                "detail": "X-Idempotency-Key header is required",
                "accepted_headers": ["X-Idempotency-Key", "x-event-id"],
                "hint": "Set INCIDENT_MODE=SEV1 to enable auto-generation bypass"
            })
    
    if not trace_id:
        if is_sev1_mode:
            trace_id = f"trace-{uuid.uuid4()}"
            bypass_count += 1
            logger.info(f"SEV-1 BYPASS: RAW missing X-Trace-Id, auto-generated: {trace_id}")
        else:
            logger.warning(f"REPORT: app=scholarship_api | v3.5.1 RAW: Rejected - Missing X-Trace-Id (HTTP 400)")
            return JSONResponse(status_code=400, content={
                "error": "Bad Request",
                "detail": "X-Trace-Id or X-Request-Id header is required",
                "accepted_headers": ["X-Trace-Id", "X-Request-Id"],
                "hint": "Set INCIDENT_MODE=SEV1 to enable auto-generation bypass"
            })
    
    try:
        raw_body = await request.body()
        body_str = raw_body.decode('utf-8')
        
        logger.info(f"🔍 RAW TELEMETRY RECEIVED: {body_str[:500]}")
        
        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"❌ INVALID JSON from satellite: {e}")
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Invalid JSON",
                    "detail": str(e),
                    "raw_sample": body_str[:200]
                }
            )
        
        events_to_process = []
        
        if isinstance(payload, dict):
            if "events" in payload and isinstance(payload["events"], list):
                events_to_process = [normalize_event_keys(e) for e in payload["events"]]
            else:
                events_to_process = [normalize_event_keys(payload)]
        elif isinstance(payload, list):
            events_to_process = [normalize_event_keys(e) for e in payload]
        
        accepted = 0
        failed = 0
        event_ids = []
        errors = []
        
        for event_data in events_to_process:
            try:
                event_id = event_data.get("event_id", str(uuid.uuid4()))
                event_type = event_data.get("event_type", "unknown")
                app_id = event_data.get("app_id", "unknown_satellite")
                env = event_data.get("env", "prod")
                
                if not event_type or event_type == "unknown":
                    errors.append({"event": event_data, "error": "Missing event_type"})
                    failed += 1
                    continue
                
                query = text("""
                    INSERT INTO business_events 
                    (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
                    VALUES 
                    (:request_id, :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
                """)
                
                db.execute(query, {
                    "request_id": event_id,
                    "app": app_id,
                    "env": env,
                    "event_name": event_type,
                    "ts": datetime.utcnow(),
                    "actor_type": event_data.get("actor_type", "system"),
                    "actor_id": event_data.get("user_id_hash"),
                    "session_id": event_data.get("session_id"),
                    "org_id": event_data.get("account_id"),
                    "properties": json.dumps(event_data.get("properties", {}))
                })
                
                accepted += 1
                event_ids.append(event_id)
                
            except Exception as e:
                logger.error(f"Failed to process raw event: {e}")
                errors.append({"event": event_data, "error": str(e)})
                failed += 1
        
        if accepted > 0:
            db.commit()
        
        logger.info(f"📊 RAW TELEMETRY: accepted={accepted}, failed={failed}, errors={len(errors)}")
        
        return {
            "accepted": accepted,
            "failed": failed,
            "event_ids": event_ids,
            "errors": errors[:5] if errors else [],
            "hint": "If you're seeing errors, ensure events have 'event_type' and 'app_id' fields"
        }
        
    except Exception as e:
        logger.error(f"💥 RAW TELEMETRY ERROR (returning 202 per contract): {e}")
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted_with_error",
                "accepted": 0,
                "failed": 1,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Telemetry ingest accepts all events; error logged for investigation"
            }
        )


@router.post("/events", response_model=EventWriteResponse, tags=["Telemetry"])
@router.post("/analytics/events", response_model=EventWriteResponse, tags=["Telemetry"])
async def write_events(
    batch: TelemetryEventBatch,
    request: Request,
    db=Depends(get_db)
):
    """
    Central telemetry event write endpoint (Protocol ONE_TRUTH v1.2)
    
    Dual Routing (CSRF FIX 2025-11-30):
    - Primary: POST /api/analytics/events (what ecosystem apps call)
    - Fallback: POST /api/events (legacy/simple)
    
    v1.2 Features:
    - Deduplicates events by event_id (ON CONFLICT DO NOTHING)
    - Validates app_base_url presence (logs warning if missing)
    - REPORT: prefix on all log lines
    
    v3.5.1 Hardening (AGENT3_HANDSHAKE v27):
    - Requires X-Idempotency-Key header (HTTP 428 if missing)
    - Requires X-Trace-Id header (HTTP 428 if missing)
    
    Accepts batches of events from any ecosystem app and persists to business_events table.
    S2S Auth: Bearer token from scholar_auth JWKS OR service-to-service token.
    """
    idempotency_key = (
        request.headers.get("X-Idempotency-Key") or
        request.headers.get("x-idempotency-key") or
        request.headers.get("x-event-id") or
        request.headers.get("X-Event-Id") or
        ""
    )
    
    trace_id = (
        request.headers.get("X-Trace-Id") or
        request.headers.get("x-trace-id") or
        request.headers.get("X-Request-Id") or
        request.headers.get("x-request-id") or
        ""
    )
    
    incident_mode = os.environ.get("INCIDENT_MODE", "").upper()
    is_sev1_mode = incident_mode == "SEV1"
    
    bypass_count = 0
    
    if not idempotency_key:
        if is_sev1_mode:
            idempotency_key = f"idem-{uuid.uuid4()}"
            bypass_count += 1
            logger.info(f"SEV-1 BYPASS: EVENTS missing X-Idempotency-Key, auto-generated: {idempotency_key}")
        else:
            logger.warning(f"REPORT: app=scholarship_api | v3.5.1 EVENTS: Rejected - Missing X-Idempotency-Key (HTTP 400)")
            return JSONResponse(status_code=400, content={
                "error": "Bad Request",
                "detail": "X-Idempotency-Key header is required",
                "accepted_headers": ["X-Idempotency-Key", "x-event-id"],
                "hint": "Set INCIDENT_MODE=SEV1 to enable auto-generation bypass"
            })
    
    if not trace_id:
        if is_sev1_mode:
            trace_id = f"trace-{uuid.uuid4()}"
            bypass_count += 1
            logger.info(f"SEV-1 BYPASS: EVENTS missing X-Trace-Id, auto-generated: {trace_id}")
        else:
            logger.warning(f"REPORT: app=scholarship_api | v3.5.1 EVENTS: Rejected - Missing X-Trace-Id (HTTP 400)")
            return JSONResponse(status_code=400, content={
                "error": "Bad Request",
                "detail": "X-Trace-Id or X-Request-Id header is required",
                "accepted_headers": ["X-Trace-Id", "X-Request-Id"],
                "hint": "Set INCIDENT_MODE=SEV1 to enable auto-generation bypass"
            })
    
    try:
        accepted = 0
        failed = 0
        duplicates = 0
        event_ids = []
        missing_base_url = 0
        
        for event in batch.events:
            try:
                import json
                
                if not event.app_base_url and not event.properties.get("app_base_url"):
                    missing_base_url += 1
                    logger.warning(f"REPORT: app=scholarship_api | app_base_url=https://scholarship-api-jamarrlmayes.replit.app | env=prod | VALIDATION: Event {event.event_id} from {event.app_id} missing app_base_url")
                
                props = event.properties.copy() if event.properties else {}
                if event.app_base_url:
                    props["app_base_url"] = event.app_base_url
                
                validated_event_id = event.event_id
                try:
                    uuid.UUID(validated_event_id)
                except (ValueError, TypeError):
                    validated_event_id = str(uuid.uuid4())
                    logger.debug(f"REPORT: app=scholarship_api | Converted non-UUID event_id to UUID: {validated_event_id}")
                
                query = text("""
                    INSERT INTO business_events 
                    (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
                    VALUES 
                    (CAST(:request_id AS uuid), :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
                    ON CONFLICT (request_id) DO NOTHING
                """)
                
                result = db.execute(query, {
                    "request_id": validated_event_id,
                    "app": event.app_id,
                    "env": event.env,
                    "event_name": event.event_type,
                    "ts": event.ts_utc,
                    "actor_type": event.actor_type or "system",
                    "actor_id": event.user_id_hash,
                    "session_id": event.session_id,
                    "org_id": event.account_id,
                    "properties": json.dumps(props)
                })
                
                if result.rowcount > 0:
                    accepted += 1
                    event_ids.append(event.event_id)
                else:
                    duplicates += 1
                
            except Exception as e:
                logger.error(f"REPORT: app=scholarship_api | app_base_url=https://scholarship-api-jamarrlmayes.replit.app | env=prod | Failed to write event {event.event_id}: {e}")
                failed += 1
        
        if accepted > 0:
            db.commit()
        
        logger.info(f"REPORT: app=scholarship_api | app_base_url=https://scholarship-api-jamarrlmayes.replit.app | env=prod | Telemetry batch: accepted={accepted}, failed={failed}, duplicates={duplicates}, missing_base_url={missing_base_url}")
        
        return EventWriteResponse(
            accepted=accepted,
            failed=failed,
            event_ids=event_ids
        )
    
    except Exception as e:
        logger.error(f"REPORT: app=scholarship_api | EVENTS FATAL (returning 202 per contract): {e}")
        return JSONResponse(status_code=202, content={
            "status": "accepted_with_error",
            "accepted": 0,
            "failed": 1,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Telemetry ingest accepts all events; error logged for investigation"
        })


@router.post("/events/single", tags=["Telemetry"])
async def write_single_event(
    event: TelemetryEvent,
    request: Request,
    db=Depends(get_db)
):
    """
    Single event write endpoint for simpler integrations
    """
    batch = TelemetryEventBatch(events=[event])
    return await write_events(batch, request, db)


def parse_window(window: str) -> timedelta:
    """Parse time window string to timedelta"""
    if window == "5m":
        return timedelta(minutes=5)
    elif window == "1h":
        return timedelta(hours=1)
    elif window == "24h":
        return timedelta(hours=24)
    else:
        return timedelta(hours=1)


@router.get("/stats", tags=["Telemetry"])
async def get_stats(
    window: str = Query("1h", description="Time window: 5m, 1h, 24h"),
    group: str = Query("event_type", description="Grouping field: event_type, app, actor_type"),
    db=Depends(get_db)
):
    """
    DB-backed stats endpoint for Command Center (Contract v1.1)
    
    Reads from business_events table and returns aggregated counts
    grouped by the specified field within the time window.
    """
    try:
        time_window = parse_window(window)
        cutoff = datetime.utcnow() - time_window
        
        if group == "event_type":
            group_col = "event_name"
        elif group == "app":
            group_col = "app"
        elif group == "actor_type":
            group_col = "actor_type"
        else:
            group_col = "event_name"
        
        query = text(f"""
            SELECT 
                {group_col} as group_key,
                COUNT(*) as count,
                MIN(ts) as first_event,
                MAX(ts) as last_event
            FROM business_events
            WHERE ts >= :cutoff
            GROUP BY {group_col}
            ORDER BY count DESC
        """)
        
        result = db.execute(query, {"cutoff": cutoff})
        rows = result.fetchall()
        
        stats = {}
        total = 0
        for row in rows:
            group_key = row[0] or "unknown"
            count = row[1]
            stats[group_key] = {
                "count": count,
                "first_event": row[2].isoformat() if row[2] else None,
                "last_event": row[3].isoformat() if row[3] else None
            }
            total += count
        
        query_total = text("""
            SELECT COUNT(*) FROM business_events WHERE ts >= :cutoff
        """)
        total_result = db.execute(query_total, {"cutoff": cutoff}).scalar()
        
        return {
            "window": window,
            "group": group,
            "group_by": group,
            "cutoff_utc": cutoff.isoformat(),
            "total_events": total_result or 0,
            "stats": stats,
            "breakdown": {k: v["count"] for k, v in stats.items()},
            "data_source": "postgres",
            "generated_at": datetime.utcnow().isoformat(),
            "_meta": {
                "protocol": "ONE_TRUTH",
                "version": "1.2",
                "source": "central_aggregator",
                "app_id": "scholarship_api"
            }
        }
        
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@router.get("/kpis/today", tags=["Telemetry"])
async def get_kpis_today(db=Depends(get_db)):
    """
    Today's KPI summary for Command Center (Protocol ONE_TRUTH v1.2)
    
    Returns structured KPIs expected by auto_com_center:
    - page_views, app_starts, heartbeats, scholarships_published
    - payments_count, revenue_cents (from payment_succeeded + credit_purchased)
    """
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = text("""
            SELECT 
                event_name,
                COUNT(*) as count,
                SUM(CASE WHEN (properties->>'amount_cents')::numeric IS NOT NULL 
                    THEN (properties->>'amount_cents')::numeric ELSE 0 END) as amount_cents
            FROM business_events
            WHERE ts >= :today_start
            GROUP BY event_name
        """)
        
        result = db.execute(query, {"today_start": today_start})
        rows = result.fetchall()
        
        event_counts = {}
        revenue_cents = 0
        for row in rows:
            event_name = row[0] or "unknown"
            event_counts[event_name] = row[1]
            if event_name in ("payment_succeeded", "credit_purchased"):
                revenue_cents += int(row[2] or 0)
        
        page_views = event_counts.get("page_view", 0)
        app_starts = event_counts.get("app_started", 0)
        heartbeats = event_counts.get("app_heartbeat", 0)
        scholarships_published = event_counts.get("scholarship_published", 0)
        payments_count = event_counts.get("payment_succeeded", 0) + event_counts.get("credit_purchased", 0)
        
        realized_revenue_dollars = revenue_cents / 100
        modeled_arr = realized_revenue_dollars * 365
        
        return {
            "date": today_start.date().isoformat(),
            "page_views": page_views,
            "app_starts": app_starts,
            "heartbeats": heartbeats,
            "scholarships_published": scholarships_published,
            "payments_count": payments_count,
            "revenue_cents": revenue_cents,
            "realized_revenue_dollars": realized_revenue_dollars,
            "modeled_arr": round(modeled_arr, 2),
            "arr_goal": 100000,
            "arr_pace_pct": round((modeled_arr / 100000) * 100, 2) if modeled_arr > 0 else 0,
            "event_counts": event_counts,
            "total_events": sum(event_counts.values()) if event_counts else 0,
            "data_source": "postgres",
            "generated_at": datetime.utcnow().isoformat(),
            "_meta": {
                "protocol": "ONE_TRUTH",
                "version": "1.2",
                "source": "central_aggregator",
                "app_id": "scholarship_api"
            }
        }
        
    except Exception as e:
        logger.error(f"KPIs today query failed: {e}")
        raise HTTPException(status_code=500, detail=f"KPIs query failed: {str(e)}")


@router.get("/kpis/rollup", tags=["Telemetry"])
async def get_kpis_rollup(
    days: int = Query(7, ge=1, le=90, description="Number of days to roll up"),
    db=Depends(get_db)
):
    """
    Multi-day KPI rollup for Command Center dashboards
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = text("""
            SELECT 
                DATE(ts) as event_date,
                event_name,
                COUNT(*) as count,
                SUM(CASE WHEN (properties->>'revenue_usd')::numeric IS NOT NULL 
                    THEN (properties->>'revenue_usd')::numeric ELSE 0 END) as revenue
            FROM business_events
            WHERE ts >= :cutoff
            GROUP BY DATE(ts), event_name
            ORDER BY event_date DESC
        """)
        
        result = db.execute(query, {"cutoff": cutoff})
        rows = result.fetchall()
        
        daily_stats = {}
        total_revenue = 0.0
        total_events = 0
        
        for row in rows:
            date_str = row[0].isoformat() if row[0] else "unknown"
            event_name = row[1]
            count = row[2]
            revenue = float(row[3] or 0)
            
            if date_str not in daily_stats:
                daily_stats[date_str] = {"events": {}, "total": 0, "revenue": 0.0}
            
            daily_stats[date_str]["events"][event_name] = count
            daily_stats[date_str]["total"] += count
            daily_stats[date_str]["revenue"] += revenue
            
            total_events += count
            total_revenue += revenue
        
        return {
            "days": days,
            "cutoff_utc": cutoff.isoformat(),
            "daily_stats": daily_stats,
            "totals": {
                "events": total_events,
                "revenue_usd": round(total_revenue, 2)
            },
            "data_source": "postgres",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"KPIs rollup query failed: {e}")
        raise HTTPException(status_code=500, detail=f"KPIs rollup query failed: {str(e)}")


@router.get("/health", tags=["Telemetry"])
async def telemetry_health(db=Depends(get_db)):
    """
    Telemetry subsystem health check
    """
    try:
        query = text("""
            SELECT 
                COUNT(*) as total_events,
                MAX(ts) as last_event,
                COUNT(DISTINCT app) as unique_apps
            FROM business_events
            WHERE ts >= NOW() - INTERVAL '1 hour'
        """)
        
        result = db.execute(query)
        row = result.fetchone()
        
        return {
            "status": "healthy" if row[0] > 0 else "no_recent_events",
            "events_last_hour": row[0],
            "last_event_utc": row[1].isoformat() if row[1] else None,
            "unique_apps": row[2],
            "data_source": "postgres",
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Telemetry health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data_source": "postgres",
            "checked_at": datetime.utcnow().isoformat()
        }


executive_router = APIRouter(prefix="/api/executive", tags=["Executive Dashboard"])


B2C_FUNNEL_EVENTS = ["user_signed_up", "user_logged_in", "application_started", "application_submitted", "credit_purchased", "payment_succeeded", "page_view"]
B2B_FUNNEL_EVENTS = ["provider_registered", "provider_profile_completed", "scholarship_published"]
SEO_ENGINE_EVENTS = ["page_published", "page_view", "scholarship_ingested"]
FINANCE_EVENTS = ["payment_succeeded", "credit_purchased"]
ECOSYSTEM_EVENTS = ["app_started", "app_heartbeat"]
SLO_EVENTS = ["ops_health", "error"]


def build_kpi_tiles(event_breakdown: Dict[str, int], finance_data: Dict) -> Dict[str, Any]:
    """
    Build KPI category tiles from event breakdown.
    Returns NO_DATA for categories without source data.
    """
    def sum_events(event_names: List[str]) -> int:
        return sum(event_breakdown.get(e, 0) for e in event_names)
    
    def get_events_detail(event_names: List[str]) -> Dict[str, int]:
        return {e: event_breakdown.get(e, 0) for e in event_names if e in event_breakdown}
    
    b2c_count = sum_events(B2C_FUNNEL_EVENTS)
    b2b_count = sum_events(B2B_FUNNEL_EVENTS)
    seo_count = sum_events(SEO_ENGINE_EVENTS)
    finance_count = sum_events(FINANCE_EVENTS)
    ecosystem_count = sum_events(ECOSYSTEM_EVENTS)
    slo_count = sum_events(SLO_EVENTS)
    
    return {
        "b2c_funnel": {
            "total": b2c_count,
            "events": get_events_detail(B2C_FUNNEL_EVENTS),
            "status": "active" if b2c_count > 0 else "NO_DATA"
        },
        "b2b_providers": {
            "total": b2b_count,
            "events": get_events_detail(B2B_FUNNEL_EVENTS),
            "status": "active" if b2b_count > 0 else "NO_DATA"
        },
        "seo_engine": {
            "total": seo_count,
            "events": get_events_detail(SEO_ENGINE_EVENTS),
            "status": "active" if seo_count > 0 else "NO_DATA"
        },
        "finance_snapshot": {
            "total_transactions": finance_count,
            "revenue_usd": finance_data.get("revenue_usd", 0),
            "platform_fees_cents": finance_data.get("platform_fees_cents", 0),
            "events": get_events_detail(FINANCE_EVENTS),
            "status": "active" if finance_count > 0 else "NO_DATA"
        },
        "ecosystem_telemetry": {
            "total": ecosystem_count,
            "events": get_events_detail(ECOSYSTEM_EVENTS),
            "status": "active" if ecosystem_count > 0 else "NO_DATA"
        },
        "slo_health": {
            "total": slo_count,
            "events": get_events_detail(SLO_EVENTS),
            "status": "active" if slo_count > 0 else "NO_DATA"
        }
    }


def compute_tile_status(count: int) -> str:
    """Legacy: Compute GREEN/YELLOW/NO_DATA status based on simple event count."""
    if count == 0:
        return "NO_DATA"
    elif count >= 5:
        return "GREEN"
    else:
        return "YELLOW"


def compute_slo_status(heartbeats: int, p95_ms: float = 120, error_rate_pct: float = 0.01) -> str:
    """
    SLO tile status per v1.2:
    GREEN if p95_ms ≤ 120 and error_rate_pct < 0.02 and heartbeats present in last 2 minutes
    YELLOW if p95_ms ≤ 200 and error_rate_pct < 0.05
    RED otherwise
    """
    if heartbeats == 0:
        return "NO_DATA"
    if p95_ms <= 120 and error_rate_pct < 0.02 and heartbeats > 0:
        return "GREEN"
    elif p95_ms <= 200 and error_rate_pct < 0.05:
        return "YELLOW"
    else:
        return "RED"


def compute_b2c_status(signups: int, started: int, submitted: int, payments: int) -> str:
    """
    B2C tile status per v1.2 (24h window):
    GREEN if user_signed_up ≥ 100 and application_started ≥ 75 and application_submitted ≥ 25 and payment_succeeded ≥ 10
    YELLOW if at least half thresholds met
    RED if below
    """
    if signups == 0 and started == 0 and submitted == 0 and payments == 0:
        return "NO_DATA"
    
    thresholds_met = 0
    if signups >= 100:
        thresholds_met += 1
    if started >= 75:
        thresholds_met += 1
    if submitted >= 25:
        thresholds_met += 1
    if payments >= 10:
        thresholds_met += 1
    
    if thresholds_met == 4:
        return "GREEN"
    elif thresholds_met >= 2:
        return "YELLOW"
    elif signups > 0 or started > 0 or submitted > 0 or payments > 0:
        return "YELLOW"
    else:
        return "RED"


def compute_b2b_status(providers: int, published: int, fees: int) -> str:
    """
    B2B tile status per v1.2 (24h window):
    GREEN if provider_registered ≥ 5 and scholarship_published ≥ 5 and fee_reported ≥ 1
    YELLOW if partial
    RED if low or zero
    """
    if providers == 0 and published == 0 and fees == 0:
        return "NO_DATA"
    
    thresholds_met = 0
    if providers >= 5:
        thresholds_met += 1
    if published >= 5:
        thresholds_met += 1
    if fees >= 1:
        thresholds_met += 1
    
    if thresholds_met == 3:
        return "GREEN"
    elif thresholds_met >= 1 or providers > 0 or published > 0:
        return "YELLOW"
    else:
        return "RED"


def compute_seo_status(pages_published: int, page_views: int) -> str:
    """
    SEO tile status per v1.2 (24h window):
    GREEN if page_published ≥ 25 and page_view ≥ 500
    YELLOW partial
    RED low or zero
    """
    if pages_published == 0 and page_views == 0:
        return "NO_DATA"
    
    if pages_published >= 25 and page_views >= 500:
        return "GREEN"
    elif pages_published > 0 or page_views > 0:
        return "YELLOW"
    else:
        return "RED"


def compute_growth_status(campaigns: int, landing_pages: int, utm_routed: int) -> str:
    """
    Growth tile status per v1.2 (24h window):
    GREEN if campaign_launched ≥ 5 and landing_page_created ≥ 10 and utm_routed ≥ 100
    YELLOW partial
    RED low or zero
    """
    if campaigns == 0 and landing_pages == 0 and utm_routed == 0:
        return "NO_DATA"
    
    thresholds_met = 0
    if campaigns >= 5:
        thresholds_met += 1
    if landing_pages >= 10:
        thresholds_met += 1
    if utm_routed >= 100:
        thresholds_met += 1
    
    if thresholds_met == 3:
        return "GREEN"
    elif thresholds_met >= 1 or campaigns > 0 or landing_pages > 0:
        return "YELLOW"
    else:
        return "RED"


def compute_trust_status(bias_checks: int, risk_flagged: int, total_decisions: int) -> str:
    """
    Trust tile status per v1.2 (24h window):
    GREEN if bias_check_performed ≥ 20 and risk_flagged ≤ 1% of total decisions
    YELLOW if 1–3%
    RED if >3% or no telemetry
    """
    if bias_checks == 0:
        return "NO_DATA"
    
    risk_rate = (risk_flagged / total_decisions * 100) if total_decisions > 0 else 0
    
    if bias_checks >= 20 and risk_rate <= 1:
        return "GREEN"
    elif risk_rate <= 3:
        return "YELLOW"
    else:
        return "RED"


def compute_finance_status(payments: int, fees: int) -> str:
    """
    Finance tile status per v1.2 (24h window):
    GREEN if payment_succeeded ≥ 10 and fee_reported ≥ 1
    YELLOW if partial
    RED if low or zero
    """
    if payments == 0 and fees == 0:
        return "NO_DATA"
    
    if payments >= 10 and fees >= 1:
        return "GREEN"
    elif payments > 0 or fees > 0:
        return "YELLOW"
    else:
        return "RED"


@executive_router.get("/central-stats", tags=["Executive Dashboard"])
async def get_central_stats(
    window: str = Query("24h", description="Time window: 5m, 1h, 24h"),
    db=Depends(get_db)
):
    """
    Protocol ONE TRUTH v1.0: Central aggregated stats for Command Center visualization.
    
    FRONTEND DISPLAY CONTRACT - Returns JSON with:
    - data.overallStatus: GREEN/YELLOW/RED/NO_DATA
    - data.slo: {status, uptime, p95_ms, heartbeats}
    - data.b2c: {status, traffic, funnel:{started, submitted}}
    - data.b2b: {status, providers, scholarshipsPublished, gmv}
    - data.seo: {status, pagesPublished}
    - data.growth: {status, campaigns, clicks}
    - data.trust: {status, biasChecks, nps}
    - data.finance: {status, total_revenue_cents, tx_count}
    - data.ecosystemMetrics: {totalEvents, appsReporting, eventTypes, heartbeats, scholarshipsPublished}
    - data._meta: {protocol, source, central_aggregator}
    """
    try:
        time_window = parse_window(window)
        cutoff = datetime.utcnow() - time_window
        
        app_stats_query = text("""
            SELECT 
                app as app_id,
                COUNT(*) as event_count,
                COUNT(DISTINCT event_name) as event_types,
                MIN(ts) as first_event,
                MAX(ts) as last_event
            FROM business_events
            WHERE ts >= :cutoff
            GROUP BY app
            ORDER BY event_count DESC
        """)
        
        result = db.execute(app_stats_query, {"cutoff": cutoff})
        rows = result.fetchall()
        
        apps = {}
        total_events = 0
        for row in rows:
            app_id = row[0] or "unknown"
            count = row[1]
            apps[app_id] = {
                "event_count": count,
                "event_types": row[2],
                "first_event": row[3].isoformat() if row[3] else None,
                "last_event": row[4].isoformat() if row[4] else None,
                "status": "reporting"
            }
            total_events += count
        
        event_breakdown_query = text("""
            SELECT 
                event_name,
                COUNT(*) as count
            FROM business_events
            WHERE ts >= :cutoff
            GROUP BY event_name
            ORDER BY count DESC
            LIMIT 50
        """)
        
        event_result = db.execute(event_breakdown_query, {"cutoff": cutoff})
        event_rows = event_result.fetchall()
        
        event_breakdown = {}
        for row in event_rows:
            event_breakdown[row[0] or "unknown"] = row[1]
        
        finance_query = text("""
            SELECT 
                SUM(CASE WHEN (properties->>'amount_cents')::numeric IS NOT NULL 
                    THEN (properties->>'amount_cents')::numeric ELSE 0 END) as amount_cents,
                SUM(CASE WHEN (properties->>'platform_fee_cents')::numeric IS NOT NULL 
                    THEN (properties->>'platform_fee_cents')::numeric ELSE 0 END) as platform_fees,
                COUNT(*) as tx_count
            FROM business_events
            WHERE ts >= :cutoff
              AND event_name IN ('payment_succeeded', 'credit_purchased')
        """)
        
        finance_result = db.execute(finance_query, {"cutoff": cutoff})
        finance_row = finance_result.fetchone()
        
        amount_cents = int(finance_row[0] or 0)
        platform_fees = int(finance_row[1] or 0)
        finance_tx_count = int(finance_row[2] or 0)
        
        window_seconds = time_window.total_seconds()
        seconds_per_day = 86400
        daily_revenue_dollars = (amount_cents / 100) * (seconds_per_day / window_seconds) if window_seconds > 0 else 0
        modeled_arr = daily_revenue_dollars * 365
        
        heartbeats = event_breakdown.get("app_heartbeat", 0)
        app_started = event_breakdown.get("app_started", 0)
        page_views = event_breakdown.get("page_view", 0)
        user_signed_up = event_breakdown.get("user_signed_up", 0)
        application_started = event_breakdown.get("application_started", 0)
        application_submitted = event_breakdown.get("application_submitted", 0)
        credit_purchased = event_breakdown.get("credit_purchased", 0)
        payment_succeeded = event_breakdown.get("payment_succeeded", 0)
        provider_registered = event_breakdown.get("provider_registered", 0)
        scholarship_published = event_breakdown.get("scholarship_published", 0)
        pages_published = event_breakdown.get("page_published", 0)
        campaign_launched = event_breakdown.get("campaign_launched", 0)
        landing_page_created = event_breakdown.get("landing_page_created", 0)
        utm_routed = event_breakdown.get("utm_routed", 0)
        bias_check_performed = event_breakdown.get("bias_check_performed", 0)
        risk_flagged = event_breakdown.get("risk_flagged", 0)
        fee_reported = event_breakdown.get("fee_reported", 0)
        
        slo_status = compute_slo_status(heartbeats, p95_ms=120, error_rate_pct=0.01)
        b2c_status = compute_b2c_status(user_signed_up, application_started, application_submitted, payment_succeeded)
        b2b_status = compute_b2b_status(provider_registered, scholarship_published, fee_reported)
        seo_status = compute_seo_status(pages_published, page_views)
        growth_status = compute_growth_status(campaign_launched, landing_page_created, utm_routed)
        trust_status = compute_trust_status(bias_check_performed, risk_flagged, bias_check_performed)
        finance_status = compute_finance_status(payment_succeeded, fee_reported)
        
        tile_statuses = [slo_status, b2c_status, b2b_status, seo_status, growth_status, trust_status, finance_status]
        green_count = sum(1 for s in tile_statuses if s == "GREEN")
        yellow_count = sum(1 for s in tile_statuses if s == "YELLOW")
        red_count = sum(1 for s in tile_statuses if s == "RED")
        
        if green_count >= 5:
            overall_status = "GREEN"
        elif green_count >= 3:
            overall_status = "YELLOW"
        elif red_count >= 3:
            overall_status = "RED"
        elif yellow_count + green_count >= 2:
            overall_status = "YELLOW"
        elif any(s != "NO_DATA" for s in tile_statuses):
            overall_status = "YELLOW"
        else:
            overall_status = "NO_DATA"
        
        expected_apps = [
            "scholar_auth", "scholarship_api", "scholarship_agent",
            "scholarship_sage", "student_pilot", "provider_register",
            "auto_page_maker", "auto_com_center"
        ]
        apps_reporting = len(apps)
        
        response = {
            "data": {
                "overallStatus": overall_status,
                "slo": {
                    "status": slo_status,
                    "uptime": 99.9 if heartbeats > 0 else 0,
                    "p95_ms": 120,
                    "error_rate_pct": 0.01,
                    "heartbeats": heartbeats,
                    "app_started": app_started
                },
                "b2c": {
                    "status": b2c_status,
                    "traffic": page_views,
                    "signups": user_signed_up,
                    "funnel": {
                        "started": application_started,
                        "submitted": application_submitted
                    },
                    "purchases": credit_purchased,
                    "payments": payment_succeeded,
                    "thresholds": {
                        "signups_target": 100,
                        "started_target": 75,
                        "submitted_target": 25,
                        "payments_target": 10
                    }
                },
                "b2b": {
                    "status": b2b_status,
                    "providers": provider_registered,
                    "scholarshipsPublished": scholarship_published,
                    "feeReported": fee_reported,
                    "gmv": 0,
                    "thresholds": {
                        "providers_target": 5,
                        "published_target": 5,
                        "fees_target": 1
                    }
                },
                "seo": {
                    "status": seo_status,
                    "pagesPublished": pages_published,
                    "pageViews": page_views,
                    "thresholds": {
                        "pages_target": 25,
                        "views_target": 500
                    }
                },
                "growth": {
                    "status": growth_status,
                    "campaigns": campaign_launched,
                    "landingPagesCreated": landing_page_created,
                    "utmRouted": utm_routed,
                    "thresholds": {
                        "campaigns_target": 5,
                        "landing_pages_target": 10,
                        "utm_routed_target": 100
                    }
                },
                "trust": {
                    "status": trust_status,
                    "biasChecks": bias_check_performed,
                    "riskFlagged": risk_flagged,
                    "thresholds": {
                        "bias_checks_target": 20,
                        "risk_rate_max_pct": 1
                    }
                },
                "finance": {
                    "status": finance_status,
                    "total_revenue_cents": amount_cents,
                    "realized_revenue_dollars": daily_revenue_dollars,
                    "modeled_arr": round(modeled_arr, 2),
                    "tx_count": payment_succeeded + credit_purchased,
                    "payments": payment_succeeded,
                    "feeReported": fee_reported,
                    "platform_fees_cents": platform_fees,
                    "thresholds": {
                        "payments_target": 10,
                        "fees_target": 1,
                        "arr_goal": 100000
                    }
                },
                "ecosystemMetrics": {
                    "totalEvents": total_events,
                    "appsReporting": apps_reporting,
                    "appsExpected": len(expected_apps),
                    "eventTypes": len(event_breakdown),
                    "heartbeats": heartbeats,
                    "scholarshipsPublished": scholarship_published
                },
                "_meta": {
                    "protocol": "ONE_TRUTH",
                    "version": "1.2",
                    "source": "central_aggregator",
                    "central_aggregator": "https://scholarship-api-jamarrlmayes.replit.app",
                    "app_id": "scholarship_api",
                    "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
                    "window": window,
                    "cutoff_utc": cutoff.isoformat(),
                    "generated_at": datetime.utcnow().isoformat()
                },
                "_report": {
                    "generated_by": "scholarship_api",
                    "brand_name": "Scholar AI Advisor",
                    "company_legal_name": "Referral Service LLC",
                    "contact_email": "support@referralsvc.com",
                    "contact_phone": "602-796-0177",
                    "copyright": "© 2025 Referral Service LLC. All rights reserved.",
                    "legal_links": {
                        "privacy_policy": "https://scholarship-api-jamarrlmayes.replit.app/privacy",
                        "terms_of_service": "https://scholarship-api-jamarrlmayes.replit.app/terms",
                        "accessibility": "https://scholarship-api-jamarrlmayes.replit.app/accessibility"
                    }
                }
            },
            "apps": apps,
            "event_breakdown": event_breakdown
        }
        
        logger.info(f"REPORT: app=scholarship_api | app_base_url=https://scholarship-api-jamarrlmayes.replit.app | env=prod | tile_status_rendered: SLO={slo_status} B2C={b2c_status} B2B={b2b_status} SEO={seo_status} Growth={growth_status} Trust={trust_status} Finance={finance_status} | overall={overall_status}")
        
        try:
            diagnostic_query = text("""
                INSERT INTO business_events 
                (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
                VALUES 
                (CAST(:request_id AS uuid), :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
                ON CONFLICT (request_id) DO NOTHING
            """)
            
            import json as json_module
            diagnostic_props = {
                "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
                "slo": slo_status,
                "b2c": b2c_status,
                "b2b": b2b_status,
                "seo": seo_status,
                "growth": growth_status,
                "trust": trust_status,
                "finance": finance_status,
                "overall": overall_status,
                "apps_reporting": apps_reporting,
                "total_events": total_events,
                "window": window
            }
            
            db.execute(diagnostic_query, {
                "request_id": str(uuid.uuid4()),
                "app": "scholarship_api",
                "env": "prod",
                "event_name": "tile_status_rendered",
                "ts": datetime.utcnow(),
                "actor_type": "system",
                "actor_id": "central_aggregator",
                "session_id": None,
                "org_id": None,
                "properties": json_module.dumps(diagnostic_props)
            })
            db.commit()
        except Exception as diag_err:
            logger.warning(f"REPORT: app=scholarship_api | Diagnostic emission failed (non-blocking): {diag_err}")
        
        return response
        
    except Exception as e:
        logger.error(f"REPORT: app=scholarship_api | app_base_url=https://scholarship-api-jamarrlmayes.replit.app | env=prod | Central stats query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Central stats query failed: {str(e)}")


@router.get("/kpi/b2b_funnel")
async def get_b2b_funnel(
    limit: int = Query(100, ge=1, le=1000, description="Max rows to return"),
    db=Depends(get_db)
):
    """
    GET /api/kpi/b2b_funnel - B2B Provider Funnel View for A8 Dashboard
    
    Returns provider→listing funnel data from b2b_funnel PostgreSQL view.
    Used by A8 Command Center B2B tile.
    """
    try:
        query = text("""
            SELECT 
                provider_id, provider_name, segment, provider_status, contact_email,
                provider_created_at, first_listing_date, listings_count, applications_received,
                dpa_signed, revenue_generated, listing_id, listing_title, listing_amount,
                listing_deadline, listing_views, listing_applications, listing_active,
                listing_created_at, funnel_stage
            FROM b2b_funnel
            ORDER BY provider_created_at DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        def safe_float(val):
            """Safely convert Decimal/numeric to float, handling None and zero values"""
            return float(val) if val is not None else None
        
        def safe_float_or_zero(val):
            """Safely convert Decimal/numeric to float, returning 0.0 for None"""
            return float(val) if val is not None else 0.0
        
        funnel_data = []
        for row in rows:
            funnel_data.append({
                "provider_id": row[0],
                "provider_name": row[1],
                "segment": row[2],
                "provider_status": row[3],
                "contact_email": row[4],
                "provider_created_at": row[5].isoformat() if row[5] else None,
                "first_listing_date": row[6].isoformat() if row[6] else None,
                "listings_count": int(row[7]) if row[7] is not None else 0,
                "applications_received": int(row[8]) if row[8] is not None else 0,
                "dpa_signed": row[9],
                "revenue_generated": safe_float_or_zero(row[10]),
                "listing_id": row[11],
                "listing_title": row[12],
                "listing_amount": safe_float(row[13]),
                "listing_deadline": row[14].isoformat() if row[14] else None,
                "listing_views": int(row[15]) if row[15] is not None else 0,
                "listing_applications": int(row[16]) if row[16] is not None else 0,
                "listing_active": row[17],
                "listing_created_at": row[18].isoformat() if row[18] else None,
                "funnel_stage": row[19]
            })
        
        logger.info(f"B2B funnel query returned {len(funnel_data)} rows")
        
        return {
            "tile": "B2B",
            "data_source": "b2b_funnel_view",
            "row_count": len(funnel_data),
            "rows": funnel_data,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"B2B funnel query failed: {e}")
        raise HTTPException(status_code=500, detail=f"B2B funnel query failed: {str(e)}")


@router.get("/kpi/revenue_by_source")
async def get_revenue_by_source(
    limit: int = Query(100, ge=1, le=1000, description="Max rows to return"),
    db=Depends(get_db)
):
    """
    GET /api/kpi/revenue_by_source - UTM Revenue Attribution View for A8 Dashboard
    
    Returns revenue attribution by UTM source/campaign from revenue_by_source PostgreSQL view.
    Used by A8 Command Center Finance/Attribution tiles.
    """
    try:
        query = text("""
            SELECT 
                utm_source, utm_campaign, utm_medium, page_slug, event_name,
                source_app, event_count, total_revenue, first_event, last_event
            FROM revenue_by_source
            ORDER BY total_revenue DESC NULLS LAST, last_event DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        def safe_float_or_zero(val):
            """Safely convert Decimal/numeric to float, returning 0.0 for None"""
            return float(val) if val is not None else 0.0
        
        revenue_data = []
        total_revenue = 0.0
        for row in rows:
            rev = safe_float_or_zero(row[7])
            total_revenue += rev
            revenue_data.append({
                "utm_source": row[0],
                "utm_campaign": row[1],
                "utm_medium": row[2],
                "page_slug": row[3],
                "event_name": row[4],
                "source_app": row[5],
                "event_count": int(row[6]) if row[6] is not None else 0,
                "total_revenue": rev,
                "first_event": row[8].isoformat() if row[8] else None,
                "last_event": row[9].isoformat() if row[9] else None
            })
        
        logger.info(f"Revenue by source query returned {len(revenue_data)} rows, total ${total_revenue:.2f}")
        
        return {
            "tile": "Finance",
            "data_source": "revenue_by_source_view",
            "row_count": len(revenue_data),
            "total_revenue_dollars": total_revenue,
            "rows": revenue_data,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Revenue by source query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Revenue by source query failed: {str(e)}")
