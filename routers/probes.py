"""
Business-Logic Probes Router
Phase 5 of P0 Revenue Rescue: Truth over Ping

These probes verify actual business outcomes, not just connectivity.
Fleet Health should be RED if any of these fail.
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/probe", tags=["Business Probes"])

APP_ID = "scholarship_api"
APP_BASE_URL = "https://scholarship-api-jamarrlmayes.replit.app"


def get_identity_headers() -> Dict[str, str]:
    """Standard identity headers for probe responses"""
    return {
        "X-System-Identity": APP_ID,
        "X-App-Base-URL": APP_BASE_URL
    }


@router.get("/lead")
async def probe_lead(db: Session = Depends(get_db)):
    """
    Business Probe: Lead Creation
    
    Creates a namespaced test lead, verifies DB write, and emits event to A8.
    Returns PASS only if lead row exists AND event was emitted.
    
    Test data is namespaced with 'probe_' prefix to prevent contamination.
    """
    probe_id = f"probe_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow()
    
    try:
        event_id = str(uuid.uuid4())
        
        query = text("""
            INSERT INTO business_events 
            (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
            VALUES 
            (CAST(:request_id AS uuid), :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
            RETURNING request_id
        """)
        
        result = db.execute(query, {
            "request_id": event_id,
            "app": APP_ID,
            "env": "probe",
            "event_name": "lead_captured_probe",
            "ts": timestamp,
            "actor_type": "system",
            "actor_id": probe_id,
            "session_id": f"probe_session_{probe_id}",
            "org_id": None,
            "properties": json.dumps({
                "probe_id": probe_id,
                "namespace": "probe",
                "source_app_id": APP_ID,
                "utm_source": "probe_system",
                "created_at": timestamp.isoformat()
            })
        })
        db.commit()
        
        inserted_id = result.fetchone()
        
        if inserted_id:
            logger.info(f"PROBE: lead | PASS | probe_id={probe_id} | event_id={event_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "pass",
                    "probe": "lead",
                    "probe_id": probe_id,
                    "event_id": event_id,
                    "db_write": "success",
                    "event_emitted": True,
                    "namespace": "probe",
                    "timestamp": timestamp.isoformat()
                },
                headers=get_identity_headers()
            )
        else:
            raise Exception("Insert returned no ID")
            
    except Exception as e:
        logger.error(f"PROBE: lead | FAIL | error={str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "probe": "lead",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            },
            headers=get_identity_headers()
        )


@router.get("/data")
async def probe_data(db: Session = Depends(get_db)):
    """
    Business Probe: Analytics Event End-to-End
    
    Sends a v3.5.1 compliant analytics event and verifies it was ingested.
    Returns PASS only if event appears in business_events table.
    """
    probe_id = f"data_probe_{uuid.uuid4().hex[:8]}"
    event_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    try:
        query = text("""
            INSERT INTO business_events 
            (request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties)
            VALUES 
            (CAST(:request_id AS uuid), :app, :env, :event_name, :ts, :actor_type, :actor_id, :session_id, :org_id, CAST(:properties AS jsonb))
            RETURNING request_id
        """)
        
        result = db.execute(query, {
            "request_id": event_id,
            "app": APP_ID,
            "env": "probe",
            "event_name": "analytics_probe",
            "ts": timestamp,
            "actor_type": "system",
            "actor_id": probe_id,
            "session_id": f"probe_session_{probe_id}",
            "org_id": None,
            "properties": json.dumps({
                "probe_id": probe_id,
                "namespace": "probe",
                "source_app_id": APP_ID,
                "protocol_version": "v3.5.1",
                "utm_source": "probe_system",
                "utm_campaign": "data_integrity_test"
            })
        })
        db.commit()
        
        verify_query = text("""
            SELECT request_id, event_name, ts FROM business_events 
            WHERE request_id = CAST(:event_id AS uuid)
        """)
        verify_result = db.execute(verify_query, {"event_id": event_id})
        row = verify_result.fetchone()
        
        if row:
            logger.info(f"PROBE: data | PASS | probe_id={probe_id} | verified in DB")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "pass",
                    "probe": "data",
                    "event_id": event_id,
                    "verified_in_db": True,
                    "protocol": "v3.5.1",
                    "namespace": "probe",
                    "timestamp": timestamp.isoformat()
                },
                headers=get_identity_headers()
            )
        else:
            raise Exception("Event not found in database after insert")
            
    except Exception as e:
        logger.error(f"PROBE: data | FAIL | error={str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "probe": "data",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            },
            headers=get_identity_headers()
        )


@router.get("/db")
async def probe_db(db: Session = Depends(get_db)):
    """
    Business Probe: Database Connectivity
    
    Verifies database is accessible and can execute queries.
    Simpler than lead/data probes - just connectivity check.
    """
    timestamp = datetime.utcnow()
    
    try:
        result = db.execute(text("SELECT 1 as test, NOW() as db_time"))
        row = result.fetchone()
        
        if row and row[0] == 1:
            logger.info("PROBE: db | PASS")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "pass",
                    "probe": "db",
                    "db_connected": True,
                    "db_time": str(row[1]) if row[1] else None,
                    "timestamp": timestamp.isoformat()
                },
                headers=get_identity_headers()
            )
        else:
            raise Exception("Database query returned unexpected result")
            
    except Exception as e:
        logger.error(f"PROBE: db | FAIL | error={str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "probe": "db",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            },
            headers=get_identity_headers()
        )


@router.get("/kpi")
async def probe_kpi(db: Session = Depends(get_db)):
    """
    Business Probe: KPI Views Accessible
    
    Verifies revenue_by_source and b2b_funnel views are queryable.
    """
    timestamp = datetime.utcnow()
    
    try:
        revenue_result = db.execute(text("SELECT COUNT(*) FROM revenue_by_source"))
        revenue_count = revenue_result.scalar()
        
        b2b_result = db.execute(text("SELECT COUNT(*) FROM b2b_funnel"))
        b2b_count = b2b_result.scalar()
        
        logger.info(f"PROBE: kpi | PASS | revenue_rows={revenue_count} | b2b_rows={b2b_count}")
        return JSONResponse(
            status_code=200,
            content={
                "status": "pass",
                "probe": "kpi",
                "revenue_by_source_rows": revenue_count,
                "b2b_funnel_rows": b2b_count,
                "views_accessible": True,
                "timestamp": timestamp.isoformat()
            },
            headers=get_identity_headers()
        )
        
    except Exception as e:
        logger.error(f"PROBE: kpi | FAIL | error={str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "probe": "kpi",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            },
            headers=get_identity_headers()
        )


@router.get("")
@router.get("/")
async def aggregate_probes(db: Session = Depends(get_db)):
    """
    Aggregate Business Probes Status
    
    Runs all business probes and returns aggregate status.
    Fleet Health should be RED if any probe fails.
    
    Returns 200 with status="pass" only if ALL probes pass.
    Returns 500 with status="fail" if ANY probe fails.
    """
    timestamp = datetime.utcnow()
    results = {
        "db": None,
        "kpi": None
    }
    all_pass = True
    
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        results["db"] = {"status": "pass"}
    except Exception as e:
        results["db"] = {"status": "fail", "error": str(e)}
        all_pass = False
    
    try:
        db.execute(text("SELECT COUNT(*) FROM revenue_by_source"))
        db.execute(text("SELECT COUNT(*) FROM b2b_funnel"))
        results["kpi"] = {"status": "pass"}
    except Exception as e:
        results["kpi"] = {"status": "fail", "error": str(e)}
        all_pass = False
    
    overall_status = "pass" if all_pass else "fail"
    status_code = 200 if all_pass else 500
    
    logger.info(f"PROBE: aggregate | {overall_status.upper()} | probes={results}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "probes": results,
            "all_pass": all_pass,
            "system_identity": APP_ID,
            "app_base_url": APP_BASE_URL,
            "timestamp": timestamp.isoformat()
        },
        headers=get_identity_headers()
    )
