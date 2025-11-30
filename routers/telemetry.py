"""
Telemetry Router - Command Center Integration
Implements Telemetry Contract v1.1 endpoints for ecosystem-wide event collection and stats
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from pydantic import BaseModel, Field
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text

from models.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TelemetryEvent(BaseModel):
    """Telemetry event schema per Contract v1.1"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Event type from catalog")
    ts_utc: datetime = Field(default_factory=datetime.utcnow)
    app_id: str = Field(..., description="Source app identifier")
    env: Literal["prod", "staging", "dev"] = Field(default="prod")
    version: Optional[str] = None
    session_id: Optional[str] = None
    user_id_hash: Optional[str] = None
    account_id: Optional[str] = None
    actor_type: Optional[Literal["student", "provider", "system"]] = None
    request_id: Optional[str] = None
    source_ip_masked: Optional[str] = None
    coppa_flag: bool = False
    ferpa_flag: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)


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


@router.post("/events", response_model=EventWriteResponse, tags=["Telemetry"])
async def write_events(
    batch: TelemetryEventBatch,
    request: Request,
    db=Depends(get_db)
):
    """
    Fallback telemetry event write endpoint (Contract v1.1)
    
    Primary: POST https://scholarship-sage-jamarrlmayes.replit.app/api/analytics/events
    Fallback: POST https://scholarship-api-jamarrlmayes.replit.app/api/events (this endpoint)
    
    Accepts batches of events from any ecosystem app and persists to business_events table.
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
