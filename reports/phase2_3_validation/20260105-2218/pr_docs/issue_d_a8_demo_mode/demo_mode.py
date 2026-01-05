"""
A8 Demo Mode Implementation
File: routes/tiles.py (partial)

Implements Demo Mode toggle for safe visualization of test/simulated data.
"""
import os
from enum import Enum
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Query, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/tiles", tags=["tiles"])

# Feature flag
DEMO_MODE_ENABLED = os.getenv("DEMO_MODE_ENABLED", "false").lower() == "true"

class ViewMode(str, Enum):
    LIVE = "live"
    DEMO = "demo"
    ALL = "all"  # Admin only

class RevenueData(BaseModel):
    mode: str
    label: str
    total_revenue_usd: float
    transaction_count: int
    data: List[dict]
    warning: Optional[str] = None

def get_mode_filter(mode: ViewMode) -> tuple:
    """
    Return SQL filter and display label based on mode.
    
    CRITICAL: Live mode MUST exclude test data to prevent pollution.
    """
    if mode == ViewMode.DEMO:
        # Demo mode: show ONLY test/simulated data
        sql_filter = """
            (namespace = 'simulated_audit' 
             OR stripe_mode = 'test'
             OR payload->>'simulated' = 'true')
        """
        label = "⚠️ DEMO MODE - Simulated Data Only"
        warning = "This data is for demonstration purposes only"
        
    elif mode == ViewMode.ALL:
        # All mode: show everything (admin debugging only)
        sql_filter = "1=1"
        label = "⚠️ ALL DATA - Includes Test & Live"
        warning = "Admin view - includes test data"
        
    else:  # LIVE (default)
        # Live mode: EXCLUDE all test data
        sql_filter = """
            (stripe_mode = 'live' OR stripe_mode IS NULL)
            AND (namespace IS NULL OR namespace NOT LIKE 'simulated%')
            AND (payload->>'simulated' IS NULL OR payload->>'simulated' != 'true')
        """
        label = "Live Data"
        warning = None
    
    return sql_filter, label, warning

@router.get("/revenue", response_model=RevenueData)
async def get_revenue_tile(
    mode: ViewMode = Query(ViewMode.LIVE, description="View mode: live, demo, or all"),
    db: Session = Depends(get_db)
):
    """
    Get revenue tile data with mode-based filtering.
    
    - **live** (default): Production data only, test data excluded
    - **demo**: Simulated/test data only, clearly labeled
    - **all**: All data (admin only)
    """
    sql_filter, label, warning = get_mode_filter(mode)
    
    # Query revenue events with filter
    query = f"""
        SELECT 
            id,
            event_type,
            payload->>'amount_cents' as amount_cents,
            payload->>'currency' as currency,
            payload->>'stripe_mode' as stripe_mode,
            payload->>'namespace' as namespace,
            occurred_at
        FROM events
        WHERE event_type IN ('PaymentSuccess', 'fee_captured', 'payment_succeeded')
        AND {sql_filter}
        ORDER BY occurred_at DESC
        LIMIT 100
    """
    
    result = db.execute(query)
    rows = result.fetchall()
    
    # Calculate totals
    total_cents = sum(
        int(row.amount_cents or 0) 
        for row in rows 
        if row.amount_cents
    )
    
    return RevenueData(
        mode=mode.value,
        label=label,
        total_revenue_usd=total_cents / 100,
        transaction_count=len(rows),
        data=[
            {
                "id": str(row.id),
                "type": row.event_type,
                "amount_usd": int(row.amount_cents or 0) / 100,
                "currency": row.currency or "USD",
                "stripe_mode": row.stripe_mode,
                "namespace": row.namespace,
                "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None
            }
            for row in rows
        ],
        warning=warning
    )

@router.get("/revenue/summary")
async def revenue_summary(
    mode: ViewMode = Query(ViewMode.LIVE),
    db: Session = Depends(get_db)
):
    """Quick summary for dashboard tile"""
    sql_filter, label, warning = get_mode_filter(mode)
    
    query = f"""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM((payload->>'amount_cents')::int), 0) as total_cents
        FROM events
        WHERE event_type IN ('PaymentSuccess', 'fee_captured', 'payment_succeeded')
        AND {sql_filter}
    """
    
    result = db.execute(query).fetchone()
    
    return {
        "mode": mode.value,
        "label": label,
        "total_usd": (result.total_cents or 0) / 100,
        "count": result.count or 0,
        "warning": warning,
        "demo_mode_global": DEMO_MODE_ENABLED
    }

# Config endpoint for UI state
@router.get("/config/demo-mode")
async def get_demo_mode_config():
    """Get current demo mode configuration"""
    return {
        "enabled": DEMO_MODE_ENABLED,
        "description": "Demo mode shows simulated/test data with clear labels"
    }
