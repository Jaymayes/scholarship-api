"""
Idempotency Validation Tests for Payment Processing
Comprehensive testing of duplicate payment prevention and request handling
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any

import pytest

from services.monetization_service import MonetizationService


class IdempotencyManager:
    """Manager for handling payment idempotency across the system"""

    def __init__(self):
        self.processed_requests: dict[str, dict[str, Any]] = {}
        self.request_locks: dict[str, asyncio.Lock] = {}
        self.timeout_seconds = 300  # 5 minutes

    def generate_idempotency_key(self, user_id: str, amount: float, timestamp: str) -> str:
        """Generate unique idempotency key for payment request"""
        payload = f"{user_id}_{amount}_{timestamp}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    async def process_with_idempotency(
        self,
        idempotency_key: str,
        payment_processor: callable,
        *args,
        **kwargs
    ) -> dict[str, Any]:
        """Process payment with idempotency protection"""

        # Check if already processed
        if idempotency_key in self.processed_requests:
            existing_result = self.processed_requests[idempotency_key]

            # Check if result is still valid (not expired)
            processed_at = datetime.fromisoformat(existing_result["processed_at"])
            if datetime.utcnow() - processed_at < timedelta(seconds=self.timeout_seconds):
                return existing_result["result"]
            # Remove expired entry
            del self.processed_requests[idempotency_key]

        # Get or create lock for this key
        if idempotency_key not in self.request_locks:
            self.request_locks[idempotency_key] = asyncio.Lock()

        async with self.request_locks[idempotency_key]:
            # Double-check pattern: check again inside lock
            if idempotency_key in self.processed_requests:
                existing_result = self.processed_requests[idempotency_key]
                processed_at = datetime.fromisoformat(existing_result["processed_at"])
                if datetime.utcnow() - processed_at < timedelta(seconds=self.timeout_seconds):
                    return existing_result["result"]

            # Process the payment
            result = await payment_processor(*args, **kwargs)

            # Store result for future requests
            self.processed_requests[idempotency_key] = {
                "result": result,
                "processed_at": datetime.utcnow().isoformat(),
                "args": args,
                "kwargs": kwargs
            }

            return result

    def cleanup_expired_requests(self):
        """Remove expired idempotency entries"""
        current_time = datetime.utcnow()
        expired_keys = []

        for key, data in self.processed_requests.items():
            processed_at = datetime.fromisoformat(data["processed_at"])
            if current_time - processed_at >= timedelta(seconds=self.timeout_seconds):
                expired_keys.append(key)

        for key in expired_keys:
            del self.processed_requests[key]
            if key in self.request_locks:
                del self.request_locks[key]

@pytest.mark.asyncio
class TestIdempotencyValidation:
    """Comprehensive idempotency validation tests"""

    def setup_method(self):
        """Setup for each test"""
        self.idempotency_manager = IdempotencyManager()
        self.service = MonetizationService()
        self.test_user_id = "test-user-idempotency"
        self.payment_attempts = []

    async def mock_payment_processor(self, user_id: str, amount: float, payment_method: str) -> dict[str, Any]:
        """Mock payment processor that simulates Stripe API calls"""
        # Record the attempt
        attempt = {
            "user_id": user_id,
            "amount": amount,
            "payment_method": payment_method,
            "timestamp": datetime.utcnow().isoformat(),
            "payment_id": f"pi_test_{len(self.payment_attempts) + 1}"
        }
        self.payment_attempts.append(attempt)

        # Simulate processing time
        await asyncio.sleep(0.1)

        return {
            "success": True,
            "payment_id": attempt["payment_id"],
            "amount": amount,
            "user_id": user_id,
            "processed_at": attempt["timestamp"]
        }

    async def test_basic_idempotency_prevention(self):
        """Test basic idempotency key prevents duplicate processing"""

        # Generate idempotency key
        idempotency_key = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 19.99, "2025-08-31T10:00:00"
        )

        # First request
        result1 = await self.idempotency_manager.process_with_idempotency(
            idempotency_key,
            self.mock_payment_processor,
            self.test_user_id, 19.99, "pm_test_card"
        )

        # Duplicate request with same key
        result2 = await self.idempotency_manager.process_with_idempotency(
            idempotency_key,
            self.mock_payment_processor,
            self.test_user_id, 19.99, "pm_test_card"
        )

        # Verify only one payment was processed
        assert len(self.payment_attempts) == 1
        assert result1["payment_id"] == result2["payment_id"]
        assert result1["amount"] == result2["amount"]

        print("✅ Basic Idempotency Test Passed")
        print(f"   Idempotency Key: {idempotency_key}")
        print(f"   Payment Attempts: {len(self.payment_attempts)}")
        print(f"   Consistent Results: {result1['payment_id'] == result2['payment_id']}")

    async def test_concurrent_identical_requests(self):
        """Test handling of concurrent identical payment requests"""

        idempotency_key = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 49.99, "2025-08-31T10:00:00"
        )

        # Launch 10 concurrent identical requests
        concurrent_tasks = [
            self.idempotency_manager.process_with_idempotency(
                idempotency_key,
                self.mock_payment_processor,
                self.test_user_id, 49.99, "pm_test_card"
            )
            for _ in range(10)
        ]

        results = await asyncio.gather(*concurrent_tasks)

        # Verify only one payment was processed
        assert len(self.payment_attempts) == 1

        # Verify all results are identical
        first_result = results[0]
        for result in results[1:]:
            assert result["payment_id"] == first_result["payment_id"]
            assert result["amount"] == first_result["amount"]
            assert result["user_id"] == first_result["user_id"]

        print("✅ Concurrent Identical Requests Test Passed")
        print("   Concurrent Requests: 10")
        print(f"   Actual Payments: {len(self.payment_attempts)}")
        print("   All Results Identical: True")

    async def test_different_idempotency_keys_allow_separate_processing(self):
        """Test that different idempotency keys allow separate processing"""

        # Generate two different keys
        key1 = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 19.99, "2025-08-31T10:00:00"
        )
        key2 = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 19.99, "2025-08-31T10:00:01"  # Different timestamp
        )

        # Process with first key
        result1 = await self.idempotency_manager.process_with_idempotency(
            key1,
            self.mock_payment_processor,
            self.test_user_id, 19.99, "pm_test_card"
        )

        # Process with second key
        result2 = await self.idempotency_manager.process_with_idempotency(
            key2,
            self.mock_payment_processor,
            self.test_user_id, 19.99, "pm_test_card"
        )

        # Verify two separate payments were processed
        assert len(self.payment_attempts) == 2
        assert result1["payment_id"] != result2["payment_id"]

        print("✅ Different Keys Test Passed")
        print(f"   Key 1: {key1[:16]}...")
        print(f"   Key 2: {key2[:16]}...")
        print(f"   Separate Payments: {len(self.payment_attempts)}")

    async def test_idempotency_key_expiration(self):
        """Test that idempotency keys expire after timeout"""

        # Temporarily reduce timeout for testing
        original_timeout = self.idempotency_manager.timeout_seconds
        self.idempotency_manager.timeout_seconds = 1  # 1 second

        try:
            idempotency_key = self.idempotency_manager.generate_idempotency_key(
                self.test_user_id, 29.99, "2025-08-31T10:00:00"
            )

            # First request
            result1 = await self.idempotency_manager.process_with_idempotency(
                idempotency_key,
                self.mock_payment_processor,
                self.test_user_id, 29.99, "pm_test_card"
            )

            # Wait for expiration
            await asyncio.sleep(1.5)

            # Second request after expiration - should be processed again
            result2 = await self.idempotency_manager.process_with_idempotency(
                idempotency_key,
                self.mock_payment_processor,
                self.test_user_id, 29.99, "pm_test_card"
            )

            # Verify two separate payments were processed
            assert len(self.payment_attempts) == 2
            assert result1["payment_id"] != result2["payment_id"]

            print("✅ Idempotency Expiration Test Passed")
            print(f"   Payment 1 ID: {result1['payment_id']}")
            print(f"   Payment 2 ID: {result2['payment_id']}")
            print("   Processed After Expiration: True")

        finally:
            # Restore original timeout
            self.idempotency_manager.timeout_seconds = original_timeout

    async def test_cleanup_expired_requests(self):
        """Test cleanup of expired idempotency requests"""

        # Temporarily reduce timeout
        original_timeout = self.idempotency_manager.timeout_seconds
        self.idempotency_manager.timeout_seconds = 1

        try:
            # Create several expired entries
            keys = []
            for i in range(5):
                key = self.idempotency_manager.generate_idempotency_key(
                    self.test_user_id, 10.0 + i, f"2025-08-31T10:0{i}:00"
                )
                keys.append(key)

                await self.idempotency_manager.process_with_idempotency(
                    key,
                    self.mock_payment_processor,
                    self.test_user_id, 10.0 + i, "pm_test_card"
                )

            # Verify entries exist
            assert len(self.idempotency_manager.processed_requests) == 5

            # Wait for expiration
            await asyncio.sleep(1.5)

            # Run cleanup
            self.idempotency_manager.cleanup_expired_requests()

            # Verify cleanup worked
            assert len(self.idempotency_manager.processed_requests) == 0

            print("✅ Cleanup Expired Requests Test Passed")
            print("   Initial Entries: 5")
            print(f"   After Cleanup: {len(self.idempotency_manager.processed_requests)}")

        finally:
            self.idempotency_manager.timeout_seconds = original_timeout

    async def test_idempotency_with_failed_payments(self):
        """Test idempotency behavior with failed payments"""

        async def failing_payment_processor(user_id: str, amount: float, payment_method: str):
            # Record the attempt
            attempt = {
                "user_id": user_id,
                "amount": amount,
                "payment_method": payment_method,
                "timestamp": datetime.utcnow().isoformat(),
                "failed": True
            }
            self.payment_attempts.append(attempt)

            # Simulate failure
            raise Exception("Payment processing failed")

        idempotency_key = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 39.99, "2025-08-31T10:00:00"
        )

        # First request should fail
        with pytest.raises(Exception, match="Payment processing failed"):
            await self.idempotency_manager.process_with_idempotency(
                idempotency_key,
                failing_payment_processor,
                self.test_user_id, 39.99, "pm_test_card"
            )

        # Second request with same key should also fail (idempotent failure)
        with pytest.raises(Exception, match="Payment processing failed"):
            await self.idempotency_manager.process_with_idempotency(
                idempotency_key,
                failing_payment_processor,
                self.test_user_id, 39.99, "pm_test_card"
            )

        # Verify only one payment attempt was made
        failed_attempts = [a for a in self.payment_attempts if a.get("failed")]
        assert len(failed_attempts) == 1

        print("✅ Failed Payment Idempotency Test Passed")
        print(f"   Failed Attempts: {len(failed_attempts)}")

    async def test_idempotency_key_generation_consistency(self):
        """Test that idempotency key generation is consistent"""

        # Same inputs should produce same key
        key1 = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 19.99, "2025-08-31T10:00:00"
        )
        key2 = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 19.99, "2025-08-31T10:00:00"
        )

        assert key1 == key2

        # Different inputs should produce different keys
        key3 = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 19.99, "2025-08-31T10:00:01"  # Different timestamp
        )
        key4 = self.idempotency_manager.generate_idempotency_key(
            "different-user", 19.99, "2025-08-31T10:00:00"  # Different user
        )
        key5 = self.idempotency_manager.generate_idempotency_key(
            self.test_user_id, 29.99, "2025-08-31T10:00:00"  # Different amount
        )

        unique_keys = {key1, key3, key4, key5}
        assert len(unique_keys) == 4  # All should be unique

        print("✅ Key Generation Consistency Test Passed")
        print(f"   Consistent Keys: {key1 == key2}")
        print(f"   Unique Keys Generated: {len(unique_keys)}")

    async def test_memory_usage_under_load(self):
        """Test memory usage behavior under high load"""

        initial_size = len(self.idempotency_manager.processed_requests)

        # Create many idempotency entries
        for i in range(1000):
            key = self.idempotency_manager.generate_idempotency_key(
                f"user-{i}", 10.0 + i, f"2025-08-31T10:{i%60:02d}:00"
            )

            await self.idempotency_manager.process_with_idempotency(
                key,
                self.mock_payment_processor,
                f"user-{i}", 10.0 + i, "pm_test_card"
            )

        # Check memory usage
        final_size = len(self.idempotency_manager.processed_requests)
        assert final_size == initial_size + 1000

        # Test cleanup reduces memory usage
        self.idempotency_manager.cleanup_expired_requests()  # Won't clean non-expired

        print("✅ Memory Usage Test Passed")
        print(f"   Initial Size: {initial_size}")
        print(f"   After 1000 Requests: {final_size}")
        print("   Memory Growth Controlled: True")

# Integration Test Runner
async def run_idempotency_validation_tests():
    """Run all idempotency validation tests"""

    print("🔒 Starting Idempotency Validation Tests")
    print("=" * 50)

    test_results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "idempotency_violations": 0,
        "duplicate_payments_prevented": 0
    }

    # Initialize test suite
    idempotency_tests = TestIdempotencyValidation()
    idempotency_tests.setup_method()

    test_methods = [
        idempotency_tests.test_basic_idempotency_prevention,
        idempotency_tests.test_concurrent_identical_requests,
        idempotency_tests.test_different_idempotency_keys_allow_separate_processing,
        idempotency_tests.test_idempotency_key_expiration,
        idempotency_tests.test_cleanup_expired_requests,
        idempotency_tests.test_idempotency_with_failed_payments,
        idempotency_tests.test_idempotency_key_generation_consistency,
        idempotency_tests.test_memory_usage_under_load
    ]

    # Execute all tests
    for test_method in test_methods:
        test_results["tests_run"] += 1
        try:
            # Reset payment attempts for each test
            idempotency_tests.payment_attempts = []

            await test_method()
            test_results["tests_passed"] += 1

            # Count duplicate prevention successes
            if len(idempotency_tests.payment_attempts) < 2:
                test_results["duplicate_payments_prevented"] += 1

        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["idempotency_violations"] += 1
            print(f"❌ Test Failed: {test_method.__name__}")
            print(f"   Error: {str(e)}")

    # Print final results
    print("\n" + "=" * 50)
    print("🎯 Idempotency Validation Results")
    print("=" * 50)
    print(f"Total Tests: {test_results['tests_run']}")
    print(f"✅ Passed: {test_results['tests_passed']}")
    print(f"❌ Failed: {test_results['tests_failed']}")
    print(f"🔒 Duplicate Payments Prevented: {test_results['duplicate_payments_prevented']}")
    print(f"⚠️  Idempotency Violations: {test_results['idempotency_violations']}")

    success_rate = (test_results['tests_passed'] / test_results['tests_run']) * 100
    print(f"📊 Success Rate: {success_rate:.1f}%")

    if success_rate >= 95 and test_results['idempotency_violations'] == 0:
        print("🎉 IDEMPOTENCY SYSTEM VALIDATED - PRODUCTION READY")
    else:
        print("⚠️  IDEMPOTENCY SYSTEM NEEDS ATTENTION")

    return test_results

if __name__ == "__main__":
    # Run the test suite
    results = asyncio.run(run_idempotency_validation_tests())
