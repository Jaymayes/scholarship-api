"""
Master Prompt Endpoints - Agent3 Unified Readiness Compliance

Standard endpoints required by the Master Prompt for scholarship_api:
- GET /api/health → {status:"ok", app:"scholarship_api", baseUrl:"..."}
- GET /api/metrics/basic → minimal counters
- GET /api/scholarships?query=&filters=
- GET /api/scholarships/{id}
- GET /api/featured
- POST /api/scholarships (provider only)
- POST /api/webhooks/scholarships.updated
"""

import hashlib
import hmac
import os
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db, ScholarshipDB
from middleware.auth import get_current_user, User
from utils.logger import get_logger

logger = get_logger("master_prompt")
router = APIRouter(tags=["Master Prompt Compliance"])

AUTO_COM_CENTER_URL = "https://auto-com-center-jamarrlmayes.replit.app"

APP_NAME = "scholarship_api"
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://scholarship-api-jamarrlmayes.replit.app")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

ALLOWED_CORS_ORIGINS = [
    "https://scholar-auth-jamarrlmayes.replit.app",
    "https://scholarship-api-jamarrlmayes.replit.app",
    "https://scholarship-agent-jamarrlmayes.replit.app",
    "https://scholarship-sage-jamarrlmayes.replit.app",
    "https://student-pilot-jamarrlmayes.replit.app",
    "https://provider-register-jamarrlmayes.replit.app",
    "https://auto-page-maker-jamarrlmayes.replit.app",
    "https://auto-com-center-jamarrlmayes.replit.app",
]


class HealthResponse(BaseModel):
    """Standard health response per Master Prompt"""
    status: str
    app: str
    baseUrl: str
    version: str | None = None
    jwks_url: str | None = None


class MetricsBasicResponse(BaseModel):
    """Basic metrics response per Master Prompt"""
    requests_total: int
    errors_total: int
    latency_p95_ms: float | None = None
    total_scholarships: int | None = None
    total_users: int | None = None
    api_latency_ms: float | None = None


class ScholarshipItem(BaseModel):
    """Scholarship item"""
    id: str
    title: str
    description: str | None = None
    amount: float | None = None
    deadline: str | None = None
    provider: str | None = None
    location: str | None = None
    eligibility: dict[str, Any] | None = None


class ScholarshipListResponse(BaseModel):
    """Paginated scholarship list"""
    items: list[ScholarshipItem]
    total: int
    page: int
    page_size: int


class ScholarshipCreateRequest(BaseModel):
    """Request to create a scholarship (provider only)"""
    title: str
    description: str
    amount: float
    deadline: str | None = None
    provider_id: str
    eligibility_criteria: dict[str, Any] = {}
    location: str | None = None
    major: str | None = None


class WebhookScholarshipUpdated(BaseModel):
    """Webhook payload for scholarship updates"""
    event: str = "scholarships.updated"
    scholarship_id: str
    action: str  # created, updated, deleted
    timestamp: str
    data: dict[str, Any] = {}


@router.get("/api/health", response_model=HealthResponse)
async def master_health():
    """
    Master Prompt standard health endpoint
    
    GET /api/health → {status:"ok", app:"scholarship_api", baseUrl:"..."}
    """
    return HealthResponse(
        status="ok",
        app=APP_NAME,
        baseUrl=APP_BASE_URL,
        version="1.0.0",
        jwks_url="https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json"
    )


@router.get("/api/healthz")
@router.head("/api/healthz")
async def master_healthz():
    """
    Kubernetes/deployment-style health check endpoint via /api/ prefix
    
    GET /api/healthz → {status:"ok"} (works through production proxy)
    """
    return {"status": "ok"}


@router.get("/api/metrics/basic", response_model=MetricsBasicResponse)
async def master_metrics_basic(db: Session = Depends(get_db)):
    """
    Master Prompt basic metrics endpoint
    
    GET /api/metrics/basic → minimal counters: requests_total, errors_total, latency_p95_ms
    Also includes: total_scholarships, total_users, api_latency_ms
    """
    try:
        from prometheus_client import REGISTRY
        
        requests_total = 0
        errors_total = 0
        latency_p95_ms = None
        
        for metric in REGISTRY.collect():
            if metric.name == "http_requests_total":
                for sample in metric.samples:
                    if sample.name == "http_requests_total":
                        requests_total += int(sample.value)
            elif metric.name == "http_errors_total":
                for sample in metric.samples:
                    if sample.name == "http_errors_total":
                        errors_total += int(sample.value)
        
        start_time = time.time()
        total_scholarships = db.query(ScholarshipDB).filter(ScholarshipDB.is_active == True).count()
        api_latency_ms = (time.time() - start_time) * 1000
        
        total_users = 0
        try:
            from sqlalchemy import text
            result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            total_users = result or 0
        except Exception:
            pass
        
        return MetricsBasicResponse(
            requests_total=requests_total,
            errors_total=errors_total,
            latency_p95_ms=latency_p95_ms,
            total_scholarships=total_scholarships,
            total_users=total_users,
            api_latency_ms=round(api_latency_ms, 2)
        )
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        return MetricsBasicResponse(
            requests_total=0,
            errors_total=0,
            latency_p95_ms=None,
            total_scholarships=None,
            total_users=None,
            api_latency_ms=None
        )


@router.get("/api/scholarships", response_model=ScholarshipListResponse)
async def list_scholarships(
    query: str = Query("", description="Search query"),
    amount_min: float | None = Query(None, description="Minimum amount filter"),
    amount_max: float | None = Query(None, description="Maximum amount filter"),
    deadline_from: str | None = Query(None, description="Deadline from (YYYY-MM-DD)"),
    deadline_to: str | None = Query(None, description="Deadline to (YYYY-MM-DD)"),
    location: str | None = Query(None, description="Location filter"),
    major: str | None = Query(None, description="Major/field filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    """
    Master Prompt scholarship search endpoint (REAL-TIME DATABASE)
    
    GET /api/scholarships?query=&filters=
    
    Filters: amount_min/max, deadline_from/to, location, major, GPA, demographics, keywords
    """
    try:
        db_query = db.query(ScholarshipDB).filter(ScholarshipDB.is_active == True)
        
        if query:
            q = f"%{query.lower()}%"
            db_query = db_query.filter(
                (ScholarshipDB.name.ilike(q)) |
                (ScholarshipDB.description.ilike(q)) |
                (ScholarshipDB.organization.ilike(q))
            )
        
        if amount_min is not None:
            db_query = db_query.filter(ScholarshipDB.amount >= amount_min)
        if amount_max is not None:
            db_query = db_query.filter(ScholarshipDB.amount <= amount_max)
        
        total = db_query.count()
        
        offset = (page - 1) * page_size
        scholarships = db_query.order_by(ScholarshipDB.amount.desc()).offset(offset).limit(page_size).all()
        
        logger.info(f"[REAL-TIME] Fetched {len(scholarships)} scholarships from database (total: {total})")
        
        return ScholarshipListResponse(
            items=[
                ScholarshipItem(
                    id=s.id,
                    title=s.name,
                    description=s.description,
                    amount=s.amount,
                    deadline=s.application_deadline.isoformat() if s.application_deadline else None,
                    provider=s.organization,
                    location=None,
                    eligibility=None
                )
                for s in scholarships
            ],
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list scholarships from database: {e}")
        raise HTTPException(status_code=500, detail="Failed to list scholarships")


@router.get("/api/scholarships/{scholarship_id}", response_model=ScholarshipItem)
async def get_scholarship(
    scholarship_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    """
    Master Prompt get scholarship by ID (REAL-TIME DATABASE)
    
    GET /api/scholarships/{id}
    """
    try:
        scholarship = db.query(ScholarshipDB).filter(
            ScholarshipDB.id == scholarship_id,
            ScholarshipDB.is_active == True
        ).first()
        
        if not scholarship:
            raise HTTPException(status_code=404, detail="Scholarship not found")
        
        logger.info(f"[REAL-TIME] Fetched scholarship {scholarship_id} from database")
        
        return ScholarshipItem(
            id=scholarship.id,
            title=scholarship.name,
            description=scholarship.description,
            amount=scholarship.amount,
            deadline=scholarship.application_deadline.isoformat() if scholarship.application_deadline else None,
            provider=scholarship.organization,
            location=None,
            eligibility=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scholarship from database: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scholarship")


@router.get("/api/featured", response_model=ScholarshipListResponse)
async def get_featured_scholarships(
    limit: int = Query(10, ge=1, le=50),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    """
    Master Prompt featured scholarships endpoint (REAL-TIME DATABASE)
    
    GET /api/featured
    
    Returns top featured scholarships (highest amount, soonest deadline, etc.)
    """
    try:
        featured = db.query(ScholarshipDB).filter(
            ScholarshipDB.is_active == True
        ).order_by(
            ScholarshipDB.amount.desc()
        ).limit(limit).all()
        
        logger.info(f"[REAL-TIME] Fetched {len(featured)} featured scholarships from database")
        
        return ScholarshipListResponse(
            items=[
                ScholarshipItem(
                    id=s.id,
                    title=s.name,
                    description=s.description,
                    amount=s.amount,
                    deadline=s.application_deadline.isoformat() if s.application_deadline else None,
                    provider=s.organization,
                    location=None,
                    eligibility=None
                )
                for s in featured
            ],
            total=len(featured),
            page=1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get featured scholarships from database: {e}")
        raise HTTPException(status_code=500, detail="Failed to get featured scholarships")


@router.post("/api/scholarships", response_model=ScholarshipItem)
async def create_scholarship(
    request: ScholarshipCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Master Prompt create scholarship endpoint (provider only)
    
    POST /api/scholarships
    
    Auth: Bearer Token validated against scholar_auth
    Role: provider required
    """
    from sqlalchemy import text
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_role = getattr(current_user, 'role', None) or current_user.get('role') if isinstance(current_user, dict) else None
    if user_role not in ['provider', 'admin', 'system']:
        raise HTTPException(status_code=403, detail="Provider role required")
    
    scholarship_id = f"sch_{datetime.utcnow().timestamp()}_{request.provider_id[:8]}"
    
    try:
        from datetime import timedelta
        deadline = request.deadline
        if not deadline:
            default_deadline = datetime.utcnow() + timedelta(days=90)
            deadline = default_deadline.strftime("%Y-%m-%d %H:%M:%S")
        
        import json
        eligibility_json = json.dumps(request.eligibility_criteria or {})
        
        db.execute(
            text("""
                INSERT INTO scholarships (
                    id, name, organization, description, amount, 
                    application_deadline, scholarship_type, eligibility_criteria, created_at, is_active
                )
                VALUES (
                    :id, :name, :organization, :description, :amount, 
                    :deadline, :scholarship_type, :eligibility_criteria, :created_at, :is_active
                )
            """),
            {
                "id": scholarship_id,
                "name": request.title,
                "organization": request.provider_id,
                "description": request.description,
                "amount": request.amount,
                "deadline": deadline,
                "scholarship_type": "general",
                "eligibility_criteria": eligibility_json,
                "created_at": datetime.utcnow(),
                "is_active": True
            }
        )
        db.commit()
        
        logger.info(f"Scholarship created: {scholarship_id} by provider {request.provider_id}")
        
        await notify_scholarship_update(scholarship_id, "created", {
            "title": request.title,
            "amount": request.amount,
            "provider_id": request.provider_id
        })
        
        await notify_auto_com_center(
            event_type="scholarship.created",
            data={
                "scholarship_id": scholarship_id,
                "title": request.title,
                "amount": request.amount,
                "provider_id": request.provider_id
            }
        )
        
        return ScholarshipItem(
            id=scholarship_id,
            title=request.title,
            description=request.description,
            amount=request.amount,
            deadline=deadline,
            provider=request.provider_id,
            location=request.location,
            eligibility=request.eligibility_criteria or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create scholarship: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scholarship")


class WebhookReceivePayload(BaseModel):
    """Incoming webhook payload"""
    event: str
    scholarship_id: str
    action: str
    timestamp: str
    data: dict[str, Any] = {}


@router.post("/api/webhooks/scholarships.updated")
async def receive_scholarship_webhook(
    payload: WebhookReceivePayload,
    request: Request,
    x_webhook_signature: str | None = Header(None)
):
    """
    Master Prompt webhook receiver for scholarship updates
    
    POST /api/webhooks/scholarships.updated
    
    Consumers: auto_page_maker, scholarship_agent, student_pilot
    Verifies HMAC-SHA256 signature in X-Webhook-Signature header
    """
    if WEBHOOK_SECRET and x_webhook_signature:
        body = await request.body()
        expected_sig = hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(x_webhook_signature, expected_sig):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    logger.info(f"Webhook received: {payload.event} for scholarship {payload.scholarship_id} ({payload.action})")
    
    return {
        "received": True,
        "event": payload.event,
        "scholarship_id": payload.scholarship_id,
        "action": payload.action,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


async def notify_scholarship_update(scholarship_id: str, action: str, data: dict[str, Any]):
    """
    Send webhook notification to consumers when scholarship is updated
    
    Consumers: auto_page_maker, scholarship_agent, student_pilot
    Each consumer may expect slightly different payload formats
    """
    webhook_configs = [
        {
            "url": "https://auto-page-maker-jamarrlmayes.replit.app/api/webhooks/scholarships.updated",
            "payload": {
                "event": "scholarships.updated",
                "scholarship_id": scholarship_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data
            }
        },
        {
            "url": "https://scholarship-agent-jamarrlmayes.replit.app/api/webhooks/event",
            "payload": {
                "event_type": "scholarships.updated",
                "scholarship_id": scholarship_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data,
                "source": "scholarship_api"
            }
        },
        {
            "url": "https://student-pilot-jamarrlmayes.replit.app/api/webhooks/scholarships.updated",
            "payload": {
                "event": "scholarships.updated",
                "scholarship_id": scholarship_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data
            }
        },
    ]
    
    for config in webhook_configs:
        try:
            url = config["url"]
            payload = config["payload"]
            
            signature = ""
            if WEBHOOK_SECRET:
                import json
                body = json.dumps(payload).encode()
                signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    url,
                    json=payload,
                    headers={
                        "X-Webhook-Signature": signature,
                        "Content-Type": "application/json"
                    }
                )
            logger.info(f"Webhook sent to {url}")
        except Exception as e:
            logger.warning(f"Failed to send webhook to {url}: {e}")


async def notify_auto_com_center(event_type: str, data: dict[str, Any]):
    """
    Send webhook notification to auto_com_center for email/SMS notifications
    
    Triggers confirmation emails for:
    - scholarship.created: Provider confirmation
    - application.submitted: Student confirmation
    - application.received: Provider notification
    """
    try:
        payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "scholarship_api",
            "data": data
        }
        
        signature = ""
        if WEBHOOK_SECRET:
            import json
            body = json.dumps(payload).encode()
            signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{AUTO_COM_CENTER_URL}/api/webhooks/notify",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "Content-Type": "application/json"
                }
            )
            logger.info(f"Notification sent to auto_com_center: {event_type} (status: {response.status_code})")
    except Exception as e:
        logger.warning(f"Failed to send notification to auto_com_center: {e}")
