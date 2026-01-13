"""
Revenue Guardrails - CFO-20260114-STRIPE-LIVE-25

Enforces spending limits per CFO authorization:
- Per-user daily cap: $50
- Global daily cap: $1,500
- Max single charge: $49
- Auto-refund on failure workflow enabled

Phase 3 Provider Payout Limits (staged):
- Per-provider daily cap: $100
- Global provider daily cap: $1,000
- Rolling holdback: 10%
- Auto-pause on >1% refund/dispute rate per provider
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

PROVIDER_DAILY_CAP_CENTS = 10000  # $100
PROVIDER_GLOBAL_DAILY_CAP_CENTS = 100000  # $1,000
PROVIDER_HOLDBACK_PCT = 10  # 10% rolling holdback
PROVIDER_MAX_REFUND_RATE_PCT = 1.0  # Auto-pause threshold

_lock = threading.Lock()
_user_daily_totals: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_global_daily_total: Dict[str, int] = defaultdict(int)

_provider_daily_payouts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_provider_global_daily_payout: Dict[str, int] = defaultdict(int)
_provider_holdback: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_provider_refunds: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_provider_transactions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
_provider_paused: Dict[str, bool] = defaultdict(bool)


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
            "provider_payouts": {
                "mode": "simulation_only" if os.environ.get("CANARY_PHASE", "2") < "3" else "live",
                "per_provider_daily_cap_cents": PROVIDER_DAILY_CAP_CENTS,
                "global_daily_cap_cents": PROVIDER_GLOBAL_DAILY_CAP_CENTS,
                "holdback_pct": PROVIDER_HOLDBACK_PCT,
                "auto_pause_refund_rate_pct": PROVIDER_MAX_REFUND_RATE_PCT,
                "phase3_ready": True
            }
        }


def is_stripe_live_mode() -> bool:
    """Check if Stripe is in LIVE mode (vs TEST)"""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    return stripe_key.startswith("sk_live_")


def get_stripe_mode() -> str:
    """Get current Stripe mode"""
    return "LIVE" if is_stripe_live_mode() else "TEST"


def check_provider_payout_allowed(
    provider_id: str,
    amount_cents: int,
    phase: int = 2
) -> Tuple[bool, Optional[str]]:
    """
    Check if a provider payout is allowed under Phase 3 guardrails.
    
    Phase 2: Simulation only (always returns simulation message)
    Phase 3+: Enforces limits
    """
    if phase < 3:
        return False, "Provider payouts are simulation-only until Phase 3"
    
    date_key = _get_date_key()
    
    with _lock:
        if _provider_paused.get(provider_id, False):
            reason = f"Provider {provider_id} is paused due to high refund/dispute rate"
            logger.warning(f"PROVIDER_PAYOUT_BLOCK: {reason}")
            return False, reason
        
        provider_total = _provider_daily_payouts[provider_id][date_key]
        if provider_total + amount_cents > PROVIDER_DAILY_CAP_CENTS:
            reason = f"Provider daily cap exceeded: ${(provider_total + amount_cents)/100:.2f} > ${PROVIDER_DAILY_CAP_CENTS/100:.2f}"
            logger.warning(f"PROVIDER_PAYOUT_BLOCK: {reason} | provider={provider_id}")
            return False, reason
        
        global_payout = _provider_global_daily_payout[date_key]
        if global_payout + amount_cents > PROVIDER_GLOBAL_DAILY_CAP_CENTS:
            reason = f"Global provider daily cap exceeded: ${(global_payout + amount_cents)/100:.2f} > ${PROVIDER_GLOBAL_DAILY_CAP_CENTS/100:.2f}"
            logger.warning(f"PROVIDER_PAYOUT_BLOCK: {reason} | provider={provider_id}")
            return False, reason
    
    return True, None


def record_provider_payout(provider_id: str, gross_amount_cents: int) -> Dict:
    """
    Record a provider payout with holdback calculation.
    
    Returns dict with net payout and holdback amounts.
    """
    date_key = _get_date_key()
    holdback_cents = int(gross_amount_cents * PROVIDER_HOLDBACK_PCT / 100)
    net_payout_cents = gross_amount_cents - holdback_cents
    
    with _lock:
        _provider_daily_payouts[provider_id][date_key] += net_payout_cents
        _provider_global_daily_payout[date_key] += net_payout_cents
        _provider_holdback[provider_id][date_key] += holdback_cents
        _provider_transactions[provider_id][date_key] += 1
        
        logger.info(
            f"PROVIDER_PAYOUT: provider={provider_id} gross=${gross_amount_cents/100:.2f} "
            f"holdback=${holdback_cents/100:.2f} net=${net_payout_cents/100:.2f}"
        )
    
    return {
        "provider_id": provider_id,
        "gross_cents": gross_amount_cents,
        "holdback_cents": holdback_cents,
        "holdback_pct": PROVIDER_HOLDBACK_PCT,
        "net_payout_cents": net_payout_cents
    }


def record_provider_refund(provider_id: str, amount_cents: int) -> None:
    """Record a refund and check if provider should be auto-paused."""
    date_key = _get_date_key()
    
    with _lock:
        _provider_refunds[provider_id][date_key] += 1
        transactions = _provider_transactions[provider_id][date_key]
        refunds = _provider_refunds[provider_id][date_key]
        
        if transactions > 0:
            refund_rate = (refunds / transactions) * 100
            if refund_rate > PROVIDER_MAX_REFUND_RATE_PCT:
                _provider_paused[provider_id] = True
                logger.warning(
                    f"PROVIDER_AUTO_PAUSE: provider={provider_id} refund_rate={refund_rate:.2f}% "
                    f"threshold={PROVIDER_MAX_REFUND_RATE_PCT}%"
                )
        
        logger.info(f"PROVIDER_REFUND: provider={provider_id} refunds={refunds} transactions={transactions}")


def get_provider_status(provider_id: str) -> Dict:
    """Get provider payout status for monitoring."""
    date_key = _get_date_key()
    
    with _lock:
        daily_payout = _provider_daily_payouts[provider_id][date_key]
        holdback = _provider_holdback[provider_id][date_key]
        transactions = _provider_transactions[provider_id][date_key]
        refunds = _provider_refunds[provider_id][date_key]
        paused = _provider_paused.get(provider_id, False)
        refund_rate = (refunds / transactions * 100) if transactions > 0 else 0.0
        
        return {
            "provider_id": provider_id,
            "date": date_key,
            "daily_payout_cents": daily_payout,
            "daily_cap_cents": PROVIDER_DAILY_CAP_CENTS,
            "remaining_cents": PROVIDER_DAILY_CAP_CENTS - daily_payout,
            "holdback_cents": holdback,
            "holdback_pct": PROVIDER_HOLDBACK_PCT,
            "transactions": transactions,
            "refunds": refunds,
            "refund_rate_pct": round(refund_rate, 2),
            "max_refund_rate_pct": PROVIDER_MAX_REFUND_RATE_PCT,
            "paused": paused
        }


def get_provider_payout_limits_status() -> Dict:
    """Get global provider payout limits status."""
    date_key = _get_date_key()
    
    with _lock:
        global_payout = _provider_global_daily_payout[date_key]
        active_providers = len([p for p in _provider_daily_payouts if _provider_daily_payouts[p][date_key] > 0])
        paused_providers = len([p for p, paused in _provider_paused.items() if paused])
        
        return {
            "date": date_key,
            "global_daily_cap_cents": PROVIDER_GLOBAL_DAILY_CAP_CENTS,
            "global_used_cents": global_payout,
            "global_remaining_cents": PROVIDER_GLOBAL_DAILY_CAP_CENTS - global_payout,
            "per_provider_cap_cents": PROVIDER_DAILY_CAP_CENTS,
            "holdback_pct": PROVIDER_HOLDBACK_PCT,
            "max_refund_rate_pct": PROVIDER_MAX_REFUND_RATE_PCT,
            "active_providers": active_providers,
            "paused_providers": paused_providers,
            "phase3_ready": True
        }


def unpause_provider(provider_id: str, reason: str = "manual_review") -> bool:
    """Manually unpause a provider after review."""
    with _lock:
        if _provider_paused.get(provider_id, False):
            _provider_paused[provider_id] = False
            logger.info(f"PROVIDER_UNPAUSED: provider={provider_id} reason={reason}")
            return True
        return False
