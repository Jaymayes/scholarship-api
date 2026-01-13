"""
Revenue Guardrails - CFO-20260114-STRIPE-LIVE-25

Enforces spending limits per CFO authorization:
- Per-user daily cap: $50
- Global daily cap: $1,500
- Max single charge: $49
- Auto-refund on failure workflow enabled
- Provider payouts simulation only until Phase 3
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

USER_DAILY_CAP_CENTS = 5000  # $50
GLOBAL_DAILY_CAP_CENTS = 150000  # $1,500
MAX_SINGLE_CHARGE_CENTS = 4900  # $49

_lock = threading.Lock()
_user_daily_totals: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_global_daily_total: Dict[str, int] = defaultdict(int)


def _get_date_key() -> str:
    """Get current date key for daily tracking"""
    return datetime.utcnow().strftime("%Y-%m-%d")


def check_charge_allowed(
    user_id: str,
    amount_cents: int,
    metadata: Optional[Dict] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if a charge is allowed under revenue guardrails.
    
    Args:
        user_id: User identifier
        amount_cents: Charge amount in cents
        metadata: Optional metadata for logging
    
    Returns:
        Tuple of (allowed: bool, rejection_reason: Optional[str])
    """
    date_key = _get_date_key()
    
    if amount_cents > MAX_SINGLE_CHARGE_CENTS:
        reason = f"Single charge ${amount_cents/100:.2f} exceeds max ${MAX_SINGLE_CHARGE_CENTS/100:.2f}"
        logger.warning(f"GUARDRAIL_BLOCK: {reason} | user={user_id}")
        return False, reason
    
    with _lock:
        user_total = _user_daily_totals[user_id][date_key]
        if user_total + amount_cents > USER_DAILY_CAP_CENTS:
            reason = f"User daily cap exceeded: ${(user_total + amount_cents)/100:.2f} > ${USER_DAILY_CAP_CENTS/100:.2f}"
            logger.warning(f"GUARDRAIL_BLOCK: {reason} | user={user_id}")
            return False, reason
        
        global_total = _global_daily_total[date_key]
        if global_total + amount_cents > GLOBAL_DAILY_CAP_CENTS:
            reason = f"Global daily cap exceeded: ${(global_total + amount_cents)/100:.2f} > ${GLOBAL_DAILY_CAP_CENTS/100:.2f}"
            logger.warning(f"GUARDRAIL_BLOCK: {reason} | user={user_id}")
            return False, reason
    
    logger.info(f"GUARDRAIL_PASS: user={user_id} amount=${amount_cents/100:.2f} user_total=${user_total/100:.2f} global_total=${global_total/100:.2f}")
    return True, None


def record_charge(user_id: str, amount_cents: int) -> None:
    """Record a successful charge against daily limits"""
    date_key = _get_date_key()
    
    with _lock:
        _user_daily_totals[user_id][date_key] += amount_cents
        _global_daily_total[date_key] += amount_cents
        
        logger.info(
            f"GUARDRAIL_RECORD: user={user_id} amount=${amount_cents/100:.2f} "
            f"user_daily=${_user_daily_totals[user_id][date_key]/100:.2f} "
            f"global_daily=${_global_daily_total[date_key]/100:.2f}"
        )


def record_refund(user_id: str, amount_cents: int) -> None:
    """Record a refund to restore limits"""
    date_key = _get_date_key()
    
    with _lock:
        _user_daily_totals[user_id][date_key] = max(0, _user_daily_totals[user_id][date_key] - amount_cents)
        _global_daily_total[date_key] = max(0, _global_daily_total[date_key] - amount_cents)
        
        logger.info(
            f"GUARDRAIL_REFUND: user={user_id} amount=${amount_cents/100:.2f} "
            f"user_daily=${_user_daily_totals[user_id][date_key]/100:.2f} "
            f"global_daily=${_global_daily_total[date_key]/100:.2f}"
        )


def get_limits_status() -> Dict:
    """Get current limits status for monitoring"""
    date_key = _get_date_key()
    
    with _lock:
        global_used = _global_daily_total[date_key]
        user_count = len([u for u in _user_daily_totals if _user_daily_totals[u][date_key] > 0])
        
        return {
            "date": date_key,
            "global_daily_cap_cents": GLOBAL_DAILY_CAP_CENTS,
            "global_used_cents": global_used,
            "global_remaining_cents": GLOBAL_DAILY_CAP_CENTS - global_used,
            "global_utilization_pct": round(global_used / GLOBAL_DAILY_CAP_CENTS * 100, 2),
            "user_daily_cap_cents": USER_DAILY_CAP_CENTS,
            "max_single_charge_cents": MAX_SINGLE_CHARGE_CENTS,
            "active_users_today": user_count,
            "guardrails_active": True,
            "provider_payouts": "simulation_only"
        }


def is_stripe_live_mode() -> bool:
    """Check if Stripe is in LIVE mode (vs TEST)"""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    return stripe_key.startswith("sk_live_")


def get_stripe_mode() -> str:
    """Get current Stripe mode"""
    return "LIVE" if is_stripe_live_mode() else "TEST"
