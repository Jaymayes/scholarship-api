# Observability API: Expose dashboards and metrics via REST endpoints

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/observability", tags=["Observability"])


@router.get("/latency-dashboard")
async def get_latency_dashboard():
    """
    Daily Ops: Latency dashboard snapshot
    P50/P95/P99 by endpoint group, error rate, slow queries
    """
    from observability.latency_dashboard import get_daily_ops_snapshot
    
    snapshot = get_daily_ops_snapshot()
    return JSONResponse(content=snapshot)


@router.get("/kpi-report")
async def get_kpi_report(period_hours: int = 24):
    """
    KPI/Reporting: Usage and conversion metrics
    Quick-wins/stretch endpoints, application starts, credit consumption, revenue impact
    """
    from observability.kpi_reporting import get_kpi_report
    
    report = get_kpi_report(period_hours)
    return JSONResponse(content=report)


@router.get("/health-summary")
async def get_health_summary():
    """
    Quick health summary for daily operations
    Combines latency, error rate, and critical metrics
    """
    from observability.latency_dashboard import get_daily_ops_snapshot
    
    snapshot = get_daily_ops_snapshot()
    
    summary = {
        "status": "healthy" if snapshot["error_rate"] < 1.0 else "degraded",
        "error_rate": snapshot["error_rate"],
        "p95_overall": snapshot["overall"]["p95"],
        "p95_target": 120.0,
        "p95_compliance": snapshot["overall"]["p95"] <= 120.0,
        "slow_queries_count": len(snapshot["slow_queries"]),
        "timestamp": snapshot["timestamp"]
    }
    
    return JSONResponse(content=summary)
