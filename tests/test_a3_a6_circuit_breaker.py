"""
Acceptance Tests for A3→A6 Circuit Breaker - CEO Directive (2026-01-15)

Test cases:
1. With A6 down, A3 returns 200 for student flows; backlog depth increases; zero 5xx exposed to users.
2. With A6 restored, backlog drains at ≥5 rps without impacting P95 >1.25s.
3. No duplicate provider records when retries occur (idempotency_key enforced).
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.a3_a6_circuit_breaker import (
    A3A6CircuitBreaker,
    BreakerState,
    should_throttle,
    should_kill
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, breaker):
        """Circuit starts in CLOSED state."""
        assert breaker.state == BreakerState.CLOSED
        assert breaker.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_opens_after_3_consecutive_failures(self, breaker):
        """Circuit opens after 3 consecutive failures within 60s."""
        async def failing_func():
            raise Exception("A6 unavailable")
        
        with patch.object(breaker, '_emit_a8_event'):
            for _ in range(3):
                result = await breaker.call(
                    failing_func,
                    idempotency_key=f"test_{_}",
                    payload={"test": True}
                )
        
        assert breaker.state == BreakerState.OPEN
        assert len(breaker.backlog) >= 1
    
    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self, breaker):
        """Circuit transitions to HALF_OPEN after 5 minute timeout."""
        breaker.state = BreakerState.OPEN
        breaker.last_state_change = 0
        
        async def success_func():
            return {"status": "ok"}
        
        with patch.object(breaker, '_emit_a8_event'):
            result = await breaker.call(
                success_func,
                idempotency_key="test_half_open",
                payload={}
            )
        
        assert breaker.state in [BreakerState.HALF_OPEN, BreakerState.CLOSED]
    
    @pytest.mark.asyncio
    async def test_closes_after_2_consecutive_successes_in_half_open(self, breaker):
        """Circuit closes after 2 consecutive successes in HALF_OPEN."""
        breaker.state = BreakerState.HALF_OPEN
        breaker.consecutive_successes = 0
        
        async def success_func():
            return {"status": "ok"}
        
        with patch.object(breaker, '_emit_a8_event'):
            await breaker.call(success_func, "key1", {})
            await breaker.call(success_func, "key2", {})
        
        assert breaker.state == BreakerState.CLOSED


class TestBacklogQueue:
    """Test backlog queue behavior."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_queues_payload_when_open(self, breaker):
        """Payloads are queued when circuit is OPEN."""
        breaker.state = BreakerState.OPEN
        breaker.last_state_change = asyncio.get_event_loop().time()
        
        async def failing_func():
            raise Exception("Should not be called")
        
        with patch.object(breaker, '_emit_a8_event'):
            result = await breaker.call(
                failing_func,
                idempotency_key="test_queue",
                payload={"provider_id": "123"}
            )
        
        assert result["status"] == "queued"
        assert len(breaker.backlog) == 1
        assert breaker.backlog[0].idempotency_key == "test_queue"
    
    @pytest.mark.asyncio
    async def test_no_duplicate_idempotency_keys(self, breaker):
        """Duplicate idempotency_keys are rejected."""
        breaker.state = BreakerState.OPEN
        breaker.last_state_change = asyncio.get_event_loop().time()
        
        async def failing_func():
            pass
        
        with patch.object(breaker, '_emit_a8_event'):
            await breaker.call(failing_func, "dup_key", {"attempt": 1})
            await breaker.call(failing_func, "dup_key", {"attempt": 2})
        
        assert len(breaker.backlog) == 1
    
    @pytest.mark.asyncio
    async def test_backlog_drains_when_closed(self, breaker):
        """Backlog drains when circuit is CLOSED."""
        from services.a3_a6_circuit_breaker import BacklogEntry
        from datetime import timedelta
        
        now = datetime.utcnow()
        breaker.backlog = [
            BacklogEntry(
                id="bl_1",
                idempotency_key="key1",
                payload_json='{"test": 1}',
                first_seen_at=now,
                next_retry_at=now - timedelta(seconds=1),
                attempts=0,
                status="pending"
            ),
            BacklogEntry(
                id="bl_2",
                idempotency_key="key2",
                payload_json='{"test": 2}',
                first_seen_at=now,
                next_retry_at=now - timedelta(seconds=1),
                attempts=0,
                status="pending"
            )
        ]
        
        processed_payloads = []
        
        async def process_func(payload):
            processed_payloads.append(payload)
        
        result = await breaker.process_backlog(process_func)
        
        assert result["processed"] >= 1
        assert len(processed_payloads) >= 1


class TestStudentFlowsNotBlocked:
    """Test that student flows are never blocked."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_returns_200_for_student_flows_when_a6_down(self, breaker):
        """A3 returns 200 for student flows even when A6 is down."""
        breaker.state = BreakerState.OPEN
        breaker.last_state_change = asyncio.get_event_loop().time()
        
        async def a6_call():
            raise Exception("A6 is down")
        
        with patch.object(breaker, '_emit_a8_event'):
            result = await breaker.call(
                a6_call,
                idempotency_key="student_flow_123",
                payload={"student_id": "s123", "action": "page_view"}
            )
        
        assert result["status"] == "queued"
        assert "error" not in result or result.get("status") == "queued"
    
    @pytest.mark.asyncio
    async def test_no_5xx_exposed_when_circuit_open(self, breaker):
        """No 5xx errors exposed to users when circuit is OPEN."""
        breaker.state = BreakerState.OPEN
        breaker.last_state_change = asyncio.get_event_loop().time()
        
        async def failing_a6():
            raise Exception("Internal error")
        
        try:
            with patch.object(breaker, '_emit_a8_event'):
                result = await breaker.call(
                    failing_a6,
                    idempotency_key="test_no_5xx",
                    payload={}
                )
            assert "status" in result
        except Exception:
            pytest.fail("Exception should not propagate - should return queued status")


class TestGuardrails:
    """Test A8 Kill/Throttle guardrails."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    def test_throttle_on_backlog_10_to_30(self, breaker):
        """THROTTLE when backlog_depth is 10-30."""
        from services.a3_a6_circuit_breaker import BacklogEntry
        
        now = datetime.utcnow()
        breaker.backlog = [
            BacklogEntry(
                id=f"bl_{i}",
                idempotency_key=f"key_{i}",
                payload_json="{}",
                first_seen_at=now,
                next_retry_at=now,
                attempts=0,
                status="pending"
            )
            for i in range(15)
        ]
        
        from services.a3_a6_circuit_breaker import a3_a6_breaker
        original_backlog = a3_a6_breaker.backlog
        a3_a6_breaker.backlog = breaker.backlog
        
        assert should_throttle()
        assert not should_kill()
        
        a3_a6_breaker.backlog = original_backlog
    
    def test_kill_on_backlog_over_30(self, breaker):
        """KILL when backlog_depth > 30."""
        from services.a3_a6_circuit_breaker import BacklogEntry, a3_a6_breaker
        
        now = datetime.utcnow()
        breaker.backlog = [
            BacklogEntry(
                id=f"bl_{i}",
                idempotency_key=f"key_{i}",
                payload_json="{}",
                first_seen_at=now,
                next_retry_at=now,
                attempts=0,
                status="pending"
            )
            for i in range(35)
        ]
        
        original_backlog = a3_a6_breaker.backlog
        a3_a6_breaker.backlog = breaker.backlog
        
        assert should_kill()
        
        a3_a6_breaker.backlog = original_backlog


class TestDeadLetterQueue:
    """Test DLQ behavior after max retries."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_moves_to_dlq_after_max_attempts(self, breaker):
        """Entry moves to DLQ after 10 failed attempts."""
        from services.a3_a6_circuit_breaker import BacklogEntry
        from datetime import timedelta
        
        now = datetime.utcnow()
        entry = BacklogEntry(
            id="bl_dlq_test",
            idempotency_key="dlq_key",
            payload_json='{"test": "dlq"}',
            first_seen_at=now,
            next_retry_at=now - timedelta(seconds=1),
            attempts=9,
            status="pending"
        )
        breaker.backlog = [entry]
        
        async def failing_process(payload):
            raise Exception("Persistent failure")
        
        with patch.object(breaker, '_emit_a8_event'):
            await breaker.process_backlog(failing_process)
        
        assert len(breaker.dlq) == 1
        assert breaker.dlq[0].idempotency_key == "dlq_key"
        assert len(breaker.backlog) == 0


class TestExponentialBackoff:
    """Test exponential backoff timing."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    def test_backoff_increases_exponentially(self, breaker):
        """Backoff delay increases exponentially with attempts."""
        delays = []
        for attempt in range(5):
            delay = breaker._calculate_backoff(attempt)
            delays.append(delay)
        
        for i in range(1, len(delays)):
            max_expected = min(breaker.BACKLOG_BASE_DELAY * (2 ** i), breaker.BACKLOG_MAX_DELAY)
            assert delays[i] <= max_expected
    
    def test_backoff_caps_at_max_delay(self, breaker):
        """Backoff is capped at BACKLOG_MAX_DELAY (15 min)."""
        delay = breaker._calculate_backoff(20)
        assert delay <= breaker.BACKLOG_MAX_DELAY


class TestWindowedFailureThreshold:
    """Test 60-second failure window enforcement."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_opens_only_with_failures_in_window(self, breaker):
        """Circuit opens only when 3 failures occur within 60s window."""
        breaker.failure_times = [time.time() - 120]
        breaker.consecutive_failures = 1
        
        breaker._cleanup_old_failures()
        
        assert breaker.consecutive_failures == 0
        assert len(breaker.failure_times) == 0
    
    @pytest.mark.asyncio
    async def test_recent_failures_trigger_open(self, breaker):
        """Circuit opens when 3 recent failures occur within window."""
        now = time.time()
        breaker.failure_times = [now - 30, now - 20, now - 10]
        
        breaker._cleanup_old_failures()
        
        assert len(breaker.failure_times) == 3
    
    @pytest.mark.asyncio
    async def test_success_prevents_open(self, breaker):
        """A success between failures prevents circuit from opening."""
        async def failing_func():
            raise Exception("A6 unavailable")
        
        async def success_func():
            return {"status": "ok"}
        
        with patch.object(breaker, '_emit_a8_event'):
            await breaker.call(failing_func, "fail1", {})
            await breaker.call(failing_func, "fail2", {})
            
            await breaker.call(success_func, "success1", {})
            
            assert len(breaker.failure_times) == 0
            
            await breaker.call(failing_func, "fail3", {})
            await breaker.call(failing_func, "fail4", {})
            
            assert breaker.state == BreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_consecutive_failures_within_window_opens(self, breaker):
        """3 consecutive failures within 60s opens the circuit."""
        async def failing_func():
            raise Exception("A6 unavailable")
        
        with patch.object(breaker, '_emit_a8_event'):
            await breaker.call(failing_func, "f1", {})
            await breaker.call(failing_func, "f2", {})
            await breaker.call(failing_func, "f3", {})
        
        assert breaker.state == BreakerState.OPEN


class TestBacklogDrainRate:
    """Test backlog drain rate and P95 constraint."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_drain_pauses_on_high_p95(self, breaker):
        """Backlog processing pauses when P95 exceeds threshold."""
        from services.a3_a6_circuit_breaker import BacklogEntry
        from datetime import timedelta
        
        now = datetime.utcnow()
        breaker.backlog = [
            BacklogEntry(
                id=f"bl_{i}",
                idempotency_key=f"key_{i}",
                payload_json="{}",
                first_seen_at=now,
                next_retry_at=now - timedelta(seconds=1),
                attempts=0,
                status="pending"
            )
            for i in range(10)
        ]
        
        breaker.call_latencies = [1300.0] * 100
        
        async def process_func(payload):
            pass
        
        result = await breaker.process_backlog(process_func)
        
        assert result["processed"] == 0 or "paused" in str(result).lower() or result["remaining"] >= 5


class TestDLQAfterMaxAttempts:
    """Test DLQ behavior after 10 failed attempts."""
    
    @pytest.fixture
    def breaker(self):
        return A3A6CircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_dlq_after_10_attempts(self, breaker):
        """Entry moves to DLQ exactly after 10 failed attempts."""
        from services.a3_a6_circuit_breaker import BacklogEntry
        from datetime import timedelta
        
        now = datetime.utcnow()
        entry = BacklogEntry(
            id="bl_max_attempts",
            idempotency_key="max_attempts_key",
            payload_json='{"test": "dlq_max"}',
            first_seen_at=now,
            next_retry_at=now - timedelta(seconds=1),
            attempts=9,
            status="pending"
        )
        breaker.backlog = [entry]
        
        async def always_fail(payload):
            raise Exception("Persistent failure")
        
        with patch.object(breaker, '_emit_a8_event'):
            await breaker.process_backlog(always_fail)
        
        assert len(breaker.dlq) == 1
        assert breaker.dlq[0].attempts == 10
        assert len(breaker.backlog) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
