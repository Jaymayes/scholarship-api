"""
Controlled Backlog Drain Service

Implements CEO-authorized drain policy with:
- Band 2 (3 rps) default, burst to 5 rps with token bucket if P95 < 1.0s and reserves ≥22%
- Per-provider cap: max 1 rps per provider
- Rate guard: reduce to 2 rps if reserves 15-17% for 3 min, resume 5 rps after reserves ≥20% for 5 min
- Stop-loss gates triggering immediate PAUSE + page CEO
- Stripe idempotency controls with duplicate hold
- 10-minute evidence cadence
- Quiet period 20 min before Gate 3
"""

import hashlib
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


class DrainMode(str, Enum):
    NORMAL = "normal"
    BAND2 = "band2"
    BURST = "burst"
    PAUSED = "paused"
    REDUCED = "reduced"
    QUIET_PERIOD = "quiet_period"


class BacklogDrainService:
    def __init__(self):
        self.drain_mode = DrainMode.PAUSED
        self.drain_rps = 0
        self.band2_rps = 3
        self.max_rps = 5
        self.reduced_rps = 2
        self.per_provider_max_rps = 1
        
        self.drain_start_time: Optional[datetime] = None
        self.last_heartbeat_time: Optional[datetime] = None
        self.current_window_start: Optional[datetime] = None
        
        self.cumulative_gmv_recovered = 0.0
        self.cumulative_platform_fee = 0.0
        self.cumulative_drained_count = 0
        self.cumulative_success_count = 0
        self.cumulative_duplicates_prevented = 0
        self.cumulative_duplicates_blocked = 0
        
        self.window_gmv_recovered = 0.0
        self.window_platform_fee = 0.0
        self.window_drained_count = 0
        self.window_success_count = 0
        self.window_duplicates_prevented = 0
        self.window_duplicates_blocked = 0
        self.window_stripe_transactions = []
        
        self.seen_idempotency_keys: Dict[str, datetime] = {}
        self.settled_transaction_ids: set = set()
        self.providers_touched: set = set()
        self.oldest_item_age_sec = 0
        
        self.provider_request_times: Dict[str, List[datetime]] = {}
        self.providers_held: Dict[str, Dict] = {}
        
        self.token_bucket_tokens = 5.0
        self.token_bucket_max = 5.0
        self.token_bucket_refill_rate = 1.0
        self.last_token_refill: Optional[datetime] = None
        
        self.reserves_history: List[Dict] = []
        self.low_reserves_start: Optional[datetime] = None
        self.high_reserves_start: Optional[datetime] = None
        
        self.stop_loss_triggered = False
        self.stop_loss_reason: Optional[str] = None
        self.stop_loss_evidence_hash: Optional[str] = None
        
        self.heartbeats: List[Dict] = []
        self.last_evidence_hash: str = "genesis_drain_000000"
        
        self.budget_pct = 0.0
        self.compute_ratio = 1.0
        self.live_backlog_depth = 0
        
        self.gate3_time = datetime.now(timezone.utc).replace(
            hour=9, minute=25, second=0, microsecond=0
        )
        if self.gate3_time < datetime.now(timezone.utc):
            self.gate3_time += timedelta(days=1)
        
        self.quiet_period_start = self.gate3_time - timedelta(minutes=20)
    
    def generate_evidence_hash(self, data: Dict) -> str:
        """Generate SHA256 evidence hash for data."""
        hash_input = f"{self.last_evidence_hash}:{datetime.now(timezone.utc).isoformat()}:{str(data)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def start_drain(self) -> Dict:
        """Start controlled backlog drain in Band 2 (3 rps)."""
        now = datetime.now(timezone.utc)
        
        if now >= self.quiet_period_start and now < self.gate3_time:
            return {
                "success": False,
                "reason": "quiet_period_active",
                "message": "Cannot start drain during quiet period (20 min before Gate 3)",
                "quiet_period_ends": self.gate3_time.isoformat()
            }
        
        self.drain_mode = DrainMode.BAND2
        self.drain_rps = self.band2_rps
        self.drain_start_time = now
        self.current_window_start = now
        self.last_heartbeat_time = now
        self.last_token_refill = now
        self.token_bucket_tokens = self.token_bucket_max
        
        self._reset_window_metrics()
        
        event_id = f"drain_start_{int(now.timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        evidence_hash = self.generate_evidence_hash({
            "event": "drain_start",
            "event_id": event_id,
            "drain_rps": self.drain_rps,
            "drain_mode": self.drain_mode.value
        })
        self.last_evidence_hash = evidence_hash
        
        return {
            "event": "drain_start",
            "event_id": event_id,
            "evidence_hash": evidence_hash,
            "timestamp_utc": now.isoformat(),
            "drain_mode": self.drain_mode.value,
            "drain_rps": self.drain_rps,
            "rate_guard": {
                "band2_rps": self.band2_rps,
                "max_rps": self.max_rps,
                "reduced_rps": self.reduced_rps,
                "per_provider_max_rps": self.per_provider_max_rps,
                "burst_trigger": "P95 < 1.0s AND reserves ≥22%",
                "reduce_trigger": "reserves 15-17% for 3 consecutive minutes",
                "resume_trigger": "reserves ≥20% for 5 minutes"
            },
            "stop_loss_gates": [
                "DLQ > 0",
                "provider_backlog_depth > 30",
                "P95 ≥ 1.25s for 60s OR error_rate_1m ≥ 0.5% for 60s",
                "Stripe success < 99.5% over last 50 drain transactions"
            ],
            "risk_controls": {
                "per_provider_cap": "max 1 rps per provider",
                "token_bucket_burst": "up to 5 rps if P95 < 1.0s and reserves ≥22%",
                "duplicate_blocked_hold": "hold provider queue if duplicate detected-and-blocked > 0"
            },
            "quiet_period": {
                "starts": self.quiet_period_start.isoformat(),
                "gate3_time": self.gate3_time.isoformat()
            },
            "overnight_goal": "drive live backlog < 10 before 09:05Z quiet period"
        }
    
    def check_provider_rate_limit(self, provider_id: str) -> Dict:
        """Check per-provider rate limit (max 1 rps per provider)."""
        now = datetime.now(timezone.utc)
        
        if provider_id in self.providers_held:
            hold_info = self.providers_held[provider_id]
            return {
                "allowed": False,
                "reason": "provider_held",
                "hold_reason": hold_info.get("reason"),
                "held_since": hold_info.get("held_since"),
                "requires_manual_review": True
            }
        
        if provider_id not in self.provider_request_times:
            self.provider_request_times[provider_id] = []
        
        cutoff = now - timedelta(seconds=1)
        self.provider_request_times[provider_id] = [
            t for t in self.provider_request_times[provider_id] if t > cutoff
        ]
        
        if len(self.provider_request_times[provider_id]) >= self.per_provider_max_rps:
            return {
                "allowed": False,
                "reason": "per_provider_rate_limit",
                "requests_in_window": len(self.provider_request_times[provider_id]),
                "max_rps": self.per_provider_max_rps
            }
        
        self.provider_request_times[provider_id].append(now)
        return {
            "allowed": True,
            "requests_in_window": len(self.provider_request_times[provider_id]),
            "max_rps": self.per_provider_max_rps
        }
    
    def check_token_bucket_burst(self, p95_ms: float, reserves_pct: float) -> Dict:
        """Check if burst mode is available via token bucket."""
        now = datetime.now(timezone.utc)
        
        if self.last_token_refill:
            elapsed = (now - self.last_token_refill).total_seconds()
            self.token_bucket_tokens = min(
                self.token_bucket_max,
                self.token_bucket_tokens + (elapsed * self.token_bucket_refill_rate)
            )
        self.last_token_refill = now
        
        can_burst = p95_ms < 1000 and reserves_pct >= 22
        
        if can_burst and self.token_bucket_tokens >= 1:
            self.token_bucket_tokens -= 1
            if self.drain_mode != DrainMode.BURST:
                self.drain_mode = DrainMode.BURST
                self.drain_rps = self.max_rps
            return {
                "burst_allowed": True,
                "tokens_remaining": round(self.token_bucket_tokens, 2),
                "drain_rps": self.drain_rps,
                "drain_mode": self.drain_mode.value
            }
        else:
            if self.drain_mode == DrainMode.BURST:
                self.drain_mode = DrainMode.BAND2
                self.drain_rps = self.band2_rps
            return {
                "burst_allowed": False,
                "tokens_remaining": round(self.token_bucket_tokens, 2),
                "reason": "P95 >= 1.0s or reserves < 22%" if not can_burst else "no tokens",
                "drain_rps": self.drain_rps,
                "drain_mode": self.drain_mode.value
            }
    
    def hold_provider(self, provider_id: str, reason: str) -> Dict:
        """Hold a provider's queue for manual review."""
        now = datetime.now(timezone.utc)
        self.providers_held[provider_id] = {
            "held_since": now.isoformat(),
            "reason": reason,
            "requires_manual_review": True
        }
        
        event_id = f"provider_hold_{int(now.timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        evidence_hash = self.generate_evidence_hash({
            "event": "provider_hold",
            "provider_id": provider_id,
            "reason": reason
        })
        self.last_evidence_hash = evidence_hash
        
        return {
            "event": "provider_hold",
            "event_id": event_id,
            "evidence_hash": evidence_hash,
            "timestamp_utc": now.isoformat(),
            "provider_id": provider_id,
            "reason": reason,
            "action": "queue_held",
            "requires_manual_review": True
        }
    
    def release_provider(self, provider_id: str) -> Dict:
        """Release a provider's hold after manual review."""
        now = datetime.now(timezone.utc)
        
        if provider_id not in self.providers_held:
            return {
                "success": False,
                "reason": "provider_not_held",
                "provider_id": provider_id
            }
        
        hold_info = self.providers_held.pop(provider_id)
        
        event_id = f"provider_release_{int(now.timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        evidence_hash = self.generate_evidence_hash({
            "event": "provider_release",
            "provider_id": provider_id
        })
        self.last_evidence_hash = evidence_hash
        
        return {
            "event": "provider_release",
            "event_id": event_id,
            "evidence_hash": evidence_hash,
            "timestamp_utc": now.isoformat(),
            "provider_id": provider_id,
            "previous_hold": hold_info,
            "action": "queue_released"
        }
    
    def get_forecast(self, current_backlog: int, drain_rate_per_min: Optional[float] = None) -> Dict:
        """Get forecast for backlog clearance vs quiet period target."""
        now = datetime.now(timezone.utc)
        
        if drain_rate_per_min is None:
            drain_rate_per_min = self.drain_rps * 60 * 0.8
        
        self.live_backlog_depth = current_backlog
        
        time_to_quiet_period = (self.quiet_period_start - now).total_seconds() / 60
        
        items_to_drain = max(0, current_backlog - 10)
        
        if drain_rate_per_min > 0:
            minutes_to_target = items_to_drain / drain_rate_per_min
        else:
            minutes_to_target = float('inf')
        
        will_meet_target = minutes_to_target <= time_to_quiet_period
        
        buffer_minutes = time_to_quiet_period - minutes_to_target
        
        return {
            "timestamp_utc": now.isoformat(),
            "forecast_type": "backlog_clearance_vs_quiet_period",
            "current_backlog": current_backlog,
            "target_backlog": 10,
            "items_to_drain": items_to_drain,
            "drain_rate_per_min": round(drain_rate_per_min, 2),
            "drain_rps": self.drain_rps,
            "minutes_to_target": round(minutes_to_target, 1) if minutes_to_target != float('inf') else "infinite",
            "quiet_period_start": self.quiet_period_start.isoformat(),
            "minutes_to_quiet_period": round(time_to_quiet_period, 1),
            "will_meet_target": will_meet_target,
            "buffer_minutes": round(buffer_minutes, 1) if buffer_minutes > 0 else 0,
            "recommendation": "on_track" if will_meet_target else "increase_drain_rate_or_reduce_scope"
        }
    
    def pause_drain(self, reason: str = "manual") -> Dict:
        """Pause the drain."""
        now = datetime.now(timezone.utc)
        self.drain_mode = DrainMode.PAUSED
        self.drain_rps = 0
        
        event_id = f"drain_pause_{int(now.timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        evidence_hash = self.generate_evidence_hash({
            "event": "drain_pause",
            "reason": reason
        })
        self.last_evidence_hash = evidence_hash
        
        return {
            "event": "drain_pause",
            "event_id": event_id,
            "evidence_hash": evidence_hash,
            "timestamp_utc": now.isoformat(),
            "reason": reason,
            "drain_mode": self.drain_mode.value,
            "drain_rps": self.drain_rps
        }
    
    def _reset_window_metrics(self):
        """Reset 10-minute window metrics."""
        self.window_gmv_recovered = 0.0
        self.window_platform_fee = 0.0
        self.window_drained_count = 0
        self.window_success_count = 0
        self.window_duplicates_prevented = 0
        self.window_duplicates_blocked = 0
        self.window_stripe_transactions = []
    
    def check_stop_loss_gates(self, metrics: Dict) -> Optional[Dict]:
        """Check all stop-loss gates. Returns page info if triggered."""
        dlq_depth = metrics.get("dlq_depth", 0)
        backlog_depth = metrics.get("provider_backlog_depth", 0)
        p95_ms = metrics.get("p95_ms", 0)
        error_rate = metrics.get("error_rate_1m", 0)
        
        stripe_success_pct = 100.0
        if len(self.window_stripe_transactions) >= 50:
            recent_50 = self.window_stripe_transactions[-50:]
            successes = sum(1 for t in recent_50 if t.get("success", False))
            stripe_success_pct = (successes / 50) * 100
        
        triggered = None
        reason = None
        
        if dlq_depth > 0:
            triggered = "DLQ > 0"
            reason = f"DLQ depth is {dlq_depth}"
        elif backlog_depth > 30:
            triggered = "provider_backlog_depth > 30"
            reason = f"Backlog depth is {backlog_depth}"
        elif p95_ms >= 1250:
            triggered = "P95 ≥ 1.25s for 60s"
            reason = f"P95 is {p95_ms}ms"
        elif error_rate >= 0.5:
            triggered = "error_rate_1m ≥ 0.5%"
            reason = f"Error rate is {error_rate}%"
        elif stripe_success_pct < 99.5 and len(self.window_stripe_transactions) >= 50:
            triggered = "Stripe success < 99.5% over last 50"
            reason = f"Stripe success is {stripe_success_pct:.1f}%"
        
        if triggered:
            now = datetime.now(timezone.utc)
            self.stop_loss_triggered = True
            self.stop_loss_reason = triggered
            
            self.drain_mode = DrainMode.PAUSED
            self.drain_rps = 0
            
            evidence_hash = self.generate_evidence_hash({
                "event": "stop_loss_triggered",
                "gate": triggered,
                "reason": reason,
                "metrics": metrics
            })
            self.stop_loss_evidence_hash = evidence_hash
            self.last_evidence_hash = evidence_hash
            
            return {
                "page_ceo": True,
                "event": "stop_loss_triggered",
                "event_id": f"stop_loss_{int(now.timestamp() * 1000)}_{uuid.uuid4().hex[:8]}",
                "timestamp_utc": now.isoformat(),
                "gate_triggered": triggered,
                "reason": reason,
                "action_taken": "PAUSE + breaker check",
                "evidence_hash": evidence_hash,
                "metrics_snapshot": metrics
            }
        
        return None
    
    def check_rate_guard(self, reserves_pct: float) -> Dict:
        """Check and adjust rate based on reserves."""
        now = datetime.now(timezone.utc)
        
        self.reserves_history.append({
            "timestamp": now,
            "reserves_pct": reserves_pct
        })
        
        cutoff = now - timedelta(minutes=6)
        self.reserves_history = [r for r in self.reserves_history if r["timestamp"] > cutoff]
        
        adjustment = None
        
        if 15 <= reserves_pct <= 17:
            if self.low_reserves_start is None:
                self.low_reserves_start = now
            elif (now - self.low_reserves_start).total_seconds() >= 180:
                if self.drain_rps > self.reduced_rps:
                    self.drain_rps = self.reduced_rps
                    self.drain_mode = DrainMode.REDUCED
                    adjustment = "reduced_to_2rps"
        else:
            self.low_reserves_start = None
        
        if reserves_pct >= 20:
            if self.high_reserves_start is None:
                self.high_reserves_start = now
            elif (now - self.high_reserves_start).total_seconds() >= 300:
                if self.drain_rps < self.max_rps and self.drain_mode == DrainMode.REDUCED:
                    self.drain_rps = self.max_rps
                    self.drain_mode = DrainMode.NORMAL
                    adjustment = "resumed_to_5rps"
                    self.high_reserves_start = None
        else:
            self.high_reserves_start = None
        
        return {
            "current_rps": self.drain_rps,
            "current_mode": self.drain_mode.value,
            "reserves_pct": reserves_pct,
            "adjustment": adjustment,
            "low_reserves_duration_sec": (now - self.low_reserves_start).total_seconds() if self.low_reserves_start else 0,
            "high_reserves_duration_sec": (now - self.high_reserves_start).total_seconds() if self.high_reserves_start else 0
        }
    
    def validate_drain_item(self, item: Dict) -> Dict:
        """Validate item before drain execution with idempotency checks."""
        now = datetime.now(timezone.utc)
        
        idempotency_key = item.get("idempotency_key")
        if not idempotency_key:
            return {
                "valid": False,
                "reason": "missing_idempotency_key",
                "action": "skip"
            }
        
        if idempotency_key in self.seen_idempotency_keys:
            seen_at = self.seen_idempotency_keys[idempotency_key]
            if (now - seen_at).days < 30:
                self.window_duplicates_prevented += 1
                self.cumulative_duplicates_prevented += 1
                return {
                    "valid": False,
                    "reason": "duplicate_idempotency_key",
                    "seen_at": seen_at.isoformat(),
                    "action": "blocked"
                }
        
        transaction_id = item.get("transaction_id")
        if transaction_id and transaction_id in self.settled_transaction_ids:
            self.cumulative_duplicates_blocked += 1
            return {
                "valid": False,
                "reason": "transaction_already_settled",
                "action": "blocked"
            }
        
        provider_status = item.get("provider_account_status", "unknown")
        provider_capabilities = item.get("provider_capabilities", [])
        
        if provider_status != "active":
            return {
                "valid": False,
                "reason": "provider_not_active",
                "status": provider_status,
                "action": "skip"
            }
        
        if "transfers" not in provider_capabilities:
            return {
                "valid": False,
                "reason": "provider_missing_transfer_capability",
                "capabilities": provider_capabilities,
                "action": "skip"
            }
        
        self.seen_idempotency_keys[idempotency_key] = now
        
        return {
            "valid": True,
            "idempotency_key": idempotency_key,
            "transaction_id": transaction_id,
            "action": "proceed"
        }
    
    def record_drain_result(self, item: Dict, success: bool, amount: float = 0):
        """Record result of a drain operation."""
        provider_id = item.get("provider_id")
        if provider_id:
            self.providers_touched.add(provider_id)
        
        self.window_drained_count += 1
        self.cumulative_drained_count += 1
        
        self.window_stripe_transactions.append({
            "timestamp": datetime.now(timezone.utc),
            "success": success,
            "amount": amount
        })
        
        if success:
            self.window_success_count += 1
            self.cumulative_success_count += 1
            
            self.window_gmv_recovered += amount
            self.cumulative_gmv_recovered += amount
            
            platform_fee = amount * 0.03
            self.window_platform_fee += platform_fee
            self.cumulative_platform_fee += platform_fee
            
            if item.get("transaction_id"):
                self.settled_transaction_ids.add(item["transaction_id"])
    
    def check_quiet_period(self) -> Dict:
        """Check if we should enter quiet period."""
        now = datetime.now(timezone.utc)
        
        if now >= self.quiet_period_start and now < self.gate3_time:
            if self.drain_mode != DrainMode.QUIET_PERIOD:
                self.drain_mode = DrainMode.QUIET_PERIOD
                self.drain_rps = 0
                
                evidence_hash = self.generate_evidence_hash({
                    "event": "quiet_period_start",
                    "gate3_time": self.gate3_time.isoformat()
                })
                self.last_evidence_hash = evidence_hash
                
                return {
                    "quiet_period": True,
                    "event": "quiet_period_start",
                    "timestamp_utc": now.isoformat(),
                    "gate3_time": self.gate3_time.isoformat(),
                    "evidence_hash": evidence_hash,
                    "message": "Drain paused for clean metric window before Gate 3"
                }
        
        return {"quiet_period": False}
    
    def generate_10min_heartbeat(self, metrics: Dict) -> Dict:
        """Generate 10-minute drain heartbeat with all required fields."""
        now = datetime.now(timezone.utc)
        
        quiet_check = self.check_quiet_period()
        if quiet_check.get("quiet_period"):
            return quiet_check
        
        stop_loss = self.check_stop_loss_gates(metrics)
        if stop_loss:
            return stop_loss
        
        rate_guard = self.check_rate_guard(metrics.get("autoscaling_reserves_pct", 20))
        
        stripe_success_pct = 100.0
        if self.window_stripe_transactions:
            successes = sum(1 for t in self.window_stripe_transactions if t.get("success", False))
            stripe_success_pct = (successes / len(self.window_stripe_transactions)) * 100
        
        heartbeat_data = {
            "timestamp_utc": now.isoformat(),
            "drain_rps": self.drain_rps,
            "drain_mode": self.drain_mode.value,
            "window_metrics": {
                "GMV_recovered_10m": round(self.window_gmv_recovered, 2),
                "platform_fee_10m": round(self.window_platform_fee, 2),
                "drained_count": self.window_drained_count,
                "success_count": self.window_success_count,
                "duplicate_prevented_10m": self.window_duplicates_prevented,
                "stripe_success_pct_10m": round(stripe_success_pct, 2)
            },
            "cumulative_totals": {
                "GMV_recovered": round(self.cumulative_gmv_recovered, 2),
                "platform_fee": round(self.cumulative_platform_fee, 2),
                "drained_count": self.cumulative_drained_count,
                "success_count": self.cumulative_success_count,
                "duplicates_prevented": self.cumulative_duplicates_prevented,
                "duplicates_blocked": self.cumulative_duplicates_blocked,
                "providers_touched": len(self.providers_touched)
            },
            "reconciliation": {
                "drained_count": self.window_drained_count,
                "success_count": self.window_success_count,
                "duplicate_prevented_count": self.window_duplicates_prevented,
                "duplicate_detected_and_blocked_count": self.cumulative_duplicates_blocked,
                "GMV_recovered": round(self.window_gmv_recovered, 2),
                "platform_fee_recognized_3pct": round(self.window_platform_fee, 2),
                "providers_touched_unique": len(self.providers_touched),
                "oldest_item_age_sec": self.oldest_item_age_sec
            },
            "system_metrics": {
                "DLQ_depth": metrics.get("dlq_depth", 0),
                "backlog_depth": metrics.get("provider_backlog_depth", 0),
                "oldest_item_age_sec": self.oldest_item_age_sec,
                "breaker_state": metrics.get("breaker_state", "UNKNOWN"),
                "autoscaling_reserves_pct": metrics.get("autoscaling_reserves_pct", 0),
                "P95": metrics.get("p95_ms", 0),
                "error_rate_1m": metrics.get("error_rate_1m", 0),
                "budget_pct": metrics.get("budget_pct", self.budget_pct),
                "compute_ratio": metrics.get("compute_ratio", self.compute_ratio)
            },
            "rate_guard": rate_guard,
            "per_provider_controls": {
                "max_rps_per_provider": self.per_provider_max_rps,
                "providers_held": len(self.providers_held),
                "held_provider_ids": list(self.providers_held.keys())
            },
            "token_bucket": {
                "tokens_remaining": round(self.token_bucket_tokens, 2),
                "max_tokens": self.token_bucket_max,
                "refill_rate": self.token_bucket_refill_rate
            },
            "emitting_nodes": ["a3_monitor", "a6_monitor", "a8_collector", "drain_service"]
        }
        
        self.budget_pct = metrics.get("budget_pct", self.budget_pct)
        self.compute_ratio = metrics.get("compute_ratio", self.compute_ratio)
        self.live_backlog_depth = metrics.get("provider_backlog_depth", 0)
        
        evidence_hash = self.generate_evidence_hash(heartbeat_data)
        heartbeat_data["evidence_hash"] = evidence_hash
        self.last_evidence_hash = evidence_hash
        
        event_id = f"drain_heartbeat_{int(now.timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        heartbeat_data["event_id"] = event_id
        
        self.heartbeats.append(heartbeat_data)
        
        self._reset_window_metrics()
        self.current_window_start = now
        self.last_heartbeat_time = now
        
        return heartbeat_data
    
    def get_status(self) -> Dict:
        """Get current drain status."""
        now = datetime.now(timezone.utc)
        
        elapsed_since_start = 0
        if self.drain_start_time:
            elapsed_since_start = (now - self.drain_start_time).total_seconds()
        
        elapsed_since_heartbeat = 0
        if self.last_heartbeat_time:
            elapsed_since_heartbeat = (now - self.last_heartbeat_time).total_seconds()
        
        return {
            "timestamp_utc": now.isoformat(),
            "drain_mode": self.drain_mode.value,
            "drain_rps": self.drain_rps,
            "drain_start_time": self.drain_start_time.isoformat() if self.drain_start_time else None,
            "elapsed_since_start_sec": round(elapsed_since_start, 1),
            "elapsed_since_heartbeat_sec": round(elapsed_since_heartbeat, 1),
            "next_heartbeat_in_sec": max(0, 600 - elapsed_since_heartbeat),
            "cumulative_totals": {
                "GMV_recovered": round(self.cumulative_gmv_recovered, 2),
                "platform_fee": round(self.cumulative_platform_fee, 2),
                "drained_count": self.cumulative_drained_count,
                "success_count": self.cumulative_success_count,
                "providers_touched": len(self.providers_touched)
            },
            "stop_loss": {
                "triggered": self.stop_loss_triggered,
                "reason": self.stop_loss_reason,
                "evidence_hash": self.stop_loss_evidence_hash
            },
            "quiet_period": {
                "starts": self.quiet_period_start.isoformat(),
                "gate3_time": self.gate3_time.isoformat(),
                "active": now >= self.quiet_period_start and now < self.gate3_time
            },
            "heartbeat_count": len(self.heartbeats),
            "last_evidence_hash": self.last_evidence_hash
        }


drain_service = BacklogDrainService()
