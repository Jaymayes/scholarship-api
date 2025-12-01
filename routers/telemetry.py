"""
Telemetry Router - Command Center Integration
Implements Telemetry Contract v1.1 endpoints for ecosystem-wide event collection and stats

Protocol ONE TRUTH (2025-11-30): Added validation error logging and flexible payload handling
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from models.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TelemetryEvent(BaseModel):
    """
    Telemetry event schema per Contract v1.1
    
    Protocol ONE TRUTH: Flexible field handling for satellite compatibility
    - Accepts both snake_case and camelCase field names
    - Auto-generates missing fields with sensible defaults
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Event type from catalog")
    ts_utc: datetime = Field(default_factory=datetime.utcnow)
    app_id: str = Field(..., description="Source app identifier")
    env: str = Field(default="prod")  # Relaxed: accept any string, not just Literal
    version: Optional[str] = None
    session_id: Optional[str] = None
    user_id_hash: Optional[str] = None
    account_id: Optional[str] = None
    actor_type: Optional[str] = None  # Relaxed: accept any string
    request_id: Optional[str] = None
    source_ip_masked: Optional[str] = None
    coppa_flag: bool = False
    ferpa_flag: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"  # Accept extra fields from satellites
        populate_by_name = True  # Accept field aliases


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


def normalize_event_keys(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Protocol ONE TRUTH: Normalize satellite payload keys to expected schema.
    Handles camelCase -> snake_case conversion and common field name variations.
    """
    key_mapping = {
        # camelCase -> snake_case
        "eventType": "event_type",
        "eventId": "event_id",
        "appId": "app_id",
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
        # Common variations
        "type": "event_type",
        "name": "event_type",
        "app": "app_id",
        "source": "app_id",
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


@router.post("/analytics/events/raw", tags=["Telemetry"])
async def write_events_raw(
    request: Request,
    db=Depends(get_db)
):
    """
    Protocol ONE TRUTH: Raw body fallback endpoint for debugging 422 errors.
    
    Accepts ANY JSON payload and attempts to normalize it to the expected schema.
    Logs the raw body for debugging satellite format issues.
    """
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
        logger.error(f"💥 RAW TELEMETRY ERROR: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.post("/events", response_model=EventWriteResponse, tags=["Telemetry"])
@router.post("/analytics/events", response_model=EventWriteResponse, tags=["Telemetry"])
async def write_events(
    batch: TelemetryEventBatch,
    request: Request,
    db=Depends(get_db)
):
    """
    Central telemetry event write endpoint (Contract v1.1)
    
    Dual Routing (CSRF FIX 2025-11-30):
    - Primary: POST /api/analytics/events (what ecosystem apps call)
    - Fallback: POST /api/events (legacy/simple)
    
    Accepts batches of events from any ecosystem app and persists to business_events table.
    S2S Auth: Bearer token from scholar_auth JWKS OR service-to-service token.
    """
    accepted = 0
    failed = 0
    event_ids = []
    
    for event in batch.events:
        try:
            import json
            
            query = text("""
                INSERT INTO business_events 
                (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
                VALUES 
                (:request_id, :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
            """)
            
            db.execute(query, {
                "request_id": event.event_id,
                "app": event.app_id,
                "env": event.env,
                "event_name": event.event_type,
                "ts": event.ts_utc,
                "actor_type": event.actor_type or "system",
                "actor_id": event.user_id_hash,
                "session_id": event.session_id,
                "org_id": event.account_id,
                "properties": json.dumps(event.properties) if event.properties else "{}"
            })
            
            accepted += 1
            event_ids.append(event.event_id)
            
        except Exception as e:
            logger.error(f"Failed to write event {event.event_id}: {e}")
            failed += 1
    
    if accepted > 0:
        db.commit()
    
    logger.info(f"Telemetry batch: accepted={accepted}, failed={failed}")
    
    return EventWriteResponse(
        accepted=accepted,
        failed=failed,
        event_ids=event_ids
    )


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
            "group_by": group,
            "cutoff_utc": cutoff.isoformat(),
            "total_events": total_result or 0,
            "stats": stats,
            "data_source": "postgres",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@router.get("/kpis/today", tags=["Telemetry"])
async def get_kpis_today(db=Depends(get_db)):
    """
    Today's KPI summary for Command Center
    """
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = text("""
            SELECT 
                event_name,
                COUNT(*) as count,
                SUM(CASE WHEN (properties->>'revenue_usd')::numeric IS NOT NULL 
                    THEN (properties->>'revenue_usd')::numeric ELSE 0 END) as revenue
            FROM business_events
            WHERE ts >= :today_start
            GROUP BY event_name
        """)
        
        result = db.execute(query, {"today_start": today_start})
        rows = result.fetchall()
        
        event_counts = {}
        total_revenue = 0.0
        for row in rows:
            event_counts[row[0]] = row[1]
            total_revenue += float(row[2] or 0)
        
        return {
            "date": today_start.date().isoformat(),
            "event_counts": event_counts,
            "total_events": sum(event_counts.values()),
            "revenue_usd": round(total_revenue, 2),
            "data_source": "postgres",
            "generated_at": datetime.utcnow().isoformat()
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


@executive_router.get("/central-stats", tags=["Executive Dashboard"])
async def get_central_stats(
    window: str = Query("1h", description="Time window: 5m, 1h, 24h"),
    db=Depends(get_db)
):
    """
    Protocol ONE TRUTH: Central aggregated stats for Command Center visualization.
    
    This is THE endpoint auto_com_center should consume for the unified ecosystem view.
    Returns stats from ALL 8 apps aggregated in the business_events table.
    
    KPI Tiles included:
    - b2c_funnel: user_signed_up, application_started/submitted, credit_purchased, payment_succeeded
    - b2b_providers: provider_registered, provider_profile_completed, scholarship_published
    - seo_engine: page_published, page_view
    - finance_snapshot: payment_succeeded sums, platform_fee_cents
    - ecosystem_telemetry: app_started, app_heartbeat, event counts
    - slo_health: ops_health, error_rate (if present; otherwise NO_DATA)
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
                SUM(CASE WHEN (properties->>'revenue_usd')::numeric IS NOT NULL 
                    THEN (properties->>'revenue_usd')::numeric ELSE 0 END) as revenue,
                SUM(CASE WHEN (properties->>'amount_cents')::numeric IS NOT NULL 
                    THEN (properties->>'amount_cents')::numeric ELSE 0 END) as amount_cents,
                SUM(CASE WHEN (properties->>'platform_fee_cents')::numeric IS NOT NULL 
                    THEN (properties->>'platform_fee_cents')::numeric ELSE 0 END) as platform_fees
            FROM business_events
            WHERE ts >= :cutoff
              AND event_name IN ('payment_succeeded', 'credit_purchased', 'scholarship_published')
        """)
        
        finance_result = db.execute(finance_query, {"cutoff": cutoff})
        finance_row = finance_result.fetchone()
        
        finance_data = {
            "revenue_usd": round(float(finance_row[0] or 0), 2),
            "amount_cents": int(finance_row[1] or 0),
            "platform_fees_cents": int(finance_row[2] or 0)
        }
        
        kpi_tiles = build_kpi_tiles(event_breakdown, finance_data)
        
        expected_apps = [
            "scholar_auth", "scholarship_api", "scholarship_agent",
            "scholarship_sage", "student_pilot", "provider_register",
            "auto_page_maker", "auto_com_center"
        ]
        reporting_apps = list(apps.keys())
        missing_apps = [a for a in expected_apps if a not in reporting_apps]
        
        return {
            "source": "scholarship_api (THE HEART)",
            "window": window,
            "cutoff_utc": cutoff.isoformat(),
            "ecosystem_health": {
                "total_events": total_events,
                "apps_reporting": len(apps),
                "apps_expected": len(expected_apps),
                "coverage_pct": round(len(apps) / len(expected_apps) * 100, 1),
                "missing_apps": missing_apps
            },
            "kpi_tiles": kpi_tiles,
            "apps": apps,
            "event_breakdown": event_breakdown,
            "data_source": "postgres",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Central stats query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Central stats query failed: {str(e)}")
