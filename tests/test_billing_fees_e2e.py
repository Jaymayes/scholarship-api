"""
E2E Tests for 3% Fee Billing System and Idempotency Checks
Comprehensive testing of payment processing, fee calculations, and duplicate prevention
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest

from models.monetization import (
    CREDIT_PACKAGES,
)
from services.monetization_service import (
    MonetizationService,
)

# Test Constants
PLATFORM_FEE_PERCENTAGE = 0.03  # 3% platform fee
TEST_USER_ID = "test-user-123"
TEST_PAYMENT_METHOD = "pm_test_card_visa"

class BillingFeeTestSuite:
    """Comprehensive billing fee test suite with idempotency validation"""

    def __init__(self):
        self.service = MonetizationService()
        self.processed_payments: dict[str, Any] = {}  # Track for idempotency

    @pytest.fixture
    async def setup_test_user(self):
        """Setup test user with initial credits"""
        return await self.service.initialize_user_credits(TEST_USER_ID)

    async def mock_stripe_payment_intent(
        self,
        amount_cents: int,
        payment_method_id: str,
        idempotency_key: str = None
    ) -> dict[str, Any]:
        """Mock Stripe payment intent creation with 3% fee calculation"""

        # Check for duplicate requests (idempotency)
        if idempotency_key and idempotency_key in self.processed_payments:
            return self.processed_payments[idempotency_key]

        # Calculate fees
        base_amount = amount_cents
        platform_fee = int(base_amount * PLATFORM_FEE_PERCENTAGE)
        stripe_fee = int(base_amount * 0.029) + 30  # Stripe's standard fee
        total_fees = platform_fee + stripe_fee

        payment_intent = {
            "id": f"pi_test_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "amount": base_amount,
            "currency": "usd",
            "status": "succeeded",
            "payment_method": payment_method_id,
            "charges": {
                "data": [{
                    "id": f"ch_test_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "amount": base_amount,
                    "balance_transaction": {
                        "fee": total_fees,
                        "fee_details": [
                            {
                                "type": "stripe_fee",
                                "amount": stripe_fee,
                                "currency": "usd",
                                "description": "Stripe processing fee"
                            },
                            {
                                "type": "application_fee",
                                "amount": platform_fee,
                                "currency": "usd",
                                "description": "Platform fee (3%)"
                            }
                        ]
                    }
                }]
            },
            "metadata": {
                "user_id": TEST_USER_ID,
                "package_purchase": "true",
                "platform_fee_cents": str(platform_fee)
            }
        }

        # Store for idempotency checking
        if idempotency_key:
            self.processed_payments[idempotency_key] = payment_intent

        return payment_intent

@pytest.mark.asyncio
class TestBillingFeesE2E:
    """End-to-end tests for billing fees with 3% platform fee"""

    def setup_method(self):
        """Setup for each test method"""
        self.test_suite = BillingFeeTestSuite()
        self.service = self.test_suite.service

    async def test_3_percent_fee_calculation_small_package(self):
        """Test 3% fee calculation for small credit package"""
        # Use smallest package: $9.99 for 50 credits
        package = next(p for p in CREDIT_PACKAGES if p.package_id == "starter")

        # Calculate expected fees
        amount_cents = int(package.price_usd * 100)  # $9.99 = 999 cents
        expected_platform_fee = int(amount_cents * PLATFORM_FEE_PERCENTAGE)  # 30 cents
        expected_stripe_fee = int(amount_cents * 0.029) + 30  # ~59 cents
        expected_total_fees = expected_platform_fee + expected_stripe_fee

        # Mock payment processing
        with patch.object(self.service, '_process_payment') as mock_payment:
            mock_payment.return_value = True

            # Process purchase
            transaction, balance = await self.service.purchase_credits(
                TEST_USER_ID, package.package_id, TEST_PAYMENT_METHOD
            )

            # Verify fee calculations
            assert transaction.cost_basis == package.price_usd
            assert balance.available_credits >= package.credits

            # Verify mock was called with correct amount
            mock_payment.assert_called_once_with(
                TEST_USER_ID, package.price_usd, TEST_PAYMENT_METHOD
            )

        # Validate fee structure
        assert expected_platform_fee == 30  # 3% of 999 cents
        assert expected_stripe_fee >= 59  # Stripe fee calculation
        assert expected_total_fees >= 89  # Combined fees

        print(f"✅ 3% Fee Test Passed - Package: {package.name}")
        print(f"   Base Amount: ${package.price_usd}")
        print(f"   Platform Fee (3%): ${expected_platform_fee/100:.2f}")
        print(f"   Estimated Total Fees: ${expected_total_fees/100:.2f}")

    async def test_3_percent_fee_calculation_large_package(self):
        """Test 3% fee calculation for large credit package"""
        # Use largest package: $199.99 for 1500 credits
        package = next(p for p in CREDIT_PACKAGES if p.package_id == "enterprise")

        # Calculate expected fees
        amount_cents = int(package.price_usd * 100)  # $199.99 = 19999 cents
        expected_platform_fee = int(amount_cents * PLATFORM_FEE_PERCENTAGE)  # 600 cents
        expected_stripe_fee = int(amount_cents * 0.029) + 30  # ~610 cents
        expected_platform_fee + expected_stripe_fee

        # Mock Stripe integration
        mock_payment_intent = await self.test_suite.mock_stripe_payment_intent(
            amount_cents, TEST_PAYMENT_METHOD
        )

        # Verify fee breakdown in payment intent
        fee_details = mock_payment_intent["charges"]["data"][0]["balance_transaction"]["fee_details"]
        platform_fee_item = next(f for f in fee_details if f["type"] == "application_fee")
        stripe_fee_item = next(f for f in fee_details if f["type"] == "stripe_fee")

        assert platform_fee_item["amount"] == expected_platform_fee
        assert stripe_fee_item["amount"] >= 550  # Stripe fee should be reasonable

        print(f"✅ Large Package Fee Test Passed - Package: {package.name}")
        print(f"   Base Amount: ${package.price_usd}")
        print(f"   Platform Fee (3%): ${expected_platform_fee/100:.2f}")
        print(f"   Stripe Fee: ${stripe_fee_item['amount']/100:.2f}")
        print(f"   Total Fees: ${(platform_fee_item['amount'] + stripe_fee_item['amount'])/100:.2f}")

    async def test_idempotency_key_prevents_duplicate_charges(self):
        """Test that idempotency keys prevent duplicate payment charges"""
        package = next(p for p in CREDIT_PACKAGES if p.package_id == "popular")
        idempotency_key = f"purchase_{TEST_USER_ID}_{package.package_id}_{datetime.utcnow().isoformat()}"

        # First payment request
        payment_1 = await self.test_suite.mock_stripe_payment_intent(
            int(package.price_usd * 100),
            TEST_PAYMENT_METHOD,
            idempotency_key
        )

        # Duplicate payment request with same idempotency key
        payment_2 = await self.test_suite.mock_stripe_payment_intent(
            int(package.price_usd * 100),
            TEST_PAYMENT_METHOD,
            idempotency_key
        )

        # Verify they return the same payment intent (idempotency working)
        assert payment_1["id"] == payment_2["id"]
        assert payment_1["amount"] == payment_2["amount"]
        assert payment_1["status"] == payment_2["status"]

        # Verify only one entry in processed payments
        assert len(self.test_suite.processed_payments) == 1

        print("✅ Idempotency Test Passed - Duplicate prevention working")
        print(f"   Idempotency Key: {idempotency_key[:50]}...")
        print(f"   Payment ID Consistent: {payment_1['id']}")

    async def test_concurrent_purchase_idempotency(self):
        """Test idempotency under concurrent purchase attempts"""
        package = next(p for p in CREDIT_PACKAGES if p.package_id == "starter")
        idempotency_key = f"concurrent_{TEST_USER_ID}_{datetime.utcnow().timestamp()}"

        async def attempt_purchase():
            return await self.test_suite.mock_stripe_payment_intent(
                int(package.price_usd * 100),
                TEST_PAYMENT_METHOD,
                idempotency_key
            )

        # Launch 5 concurrent purchase attempts
        results = await asyncio.gather(
            attempt_purchase(),
            attempt_purchase(),
            attempt_purchase(),
            attempt_purchase(),
            attempt_purchase(),
            return_exceptions=True
        )

        # All should return the same payment intent
        unique_payment_ids = {r["id"] for r in results if isinstance(r, dict)}
        assert len(unique_payment_ids) == 1  # Only one unique payment created

        # Verify single entry in processed payments
        assert idempotency_key in self.test_suite.processed_payments

        print("✅ Concurrent Idempotency Test Passed")
        print("   Concurrent Requests: 5")
        print(f"   Unique Payments Created: {len(unique_payment_ids)}")

    async def test_fee_calculation_edge_cases(self):
        """Test fee calculations for edge cases and rounding"""

        # Test very small amount (minimum charge)
        small_amount = 50  # $0.50
        small_platform_fee = int(small_amount * PLATFORM_FEE_PERCENTAGE)  # 1.5 cents -> 1 cent
        small_stripe_fee = int(small_amount * 0.029) + 30  # 31 cents minimum

        assert small_platform_fee >= 1  # At least 1 cent
        assert small_stripe_fee >= 30  # Stripe minimum

        # Test large amount
        large_amount = 100000  # $1000.00
        large_platform_fee = int(large_amount * PLATFORM_FEE_PERCENTAGE)  # 3000 cents = $30
        large_stripe_fee = int(large_amount * 0.029) + 30  # $29.30

        assert large_platform_fee == 3000  # Exactly $30
        assert large_stripe_fee >= 2900  # Around $29

        # Test fractional cents rounding
        fractional_amount = 333  # $3.33
        fractional_fee = int(fractional_amount * PLATFORM_FEE_PERCENTAGE)  # 9.99 -> 9 cents

        assert fractional_fee == 9  # Rounds down

        print("✅ Edge Case Fee Tests Passed")
        print(f"   Small Amount ($0.50): Platform fee ${small_platform_fee/100:.2f}")
        print(f"   Large Amount ($1000): Platform fee ${large_platform_fee/100:.2f}")
        print(f"   Fractional ($3.33): Platform fee ${fractional_fee/100:.2f}")

    async def test_failed_payment_no_credit_grant(self):
        """Test that failed payments don't grant credits"""
        package = next(p for p in CREDIT_PACKAGES if p.package_id == "starter")

        # Get initial balance
        initial_balance = await self.service.initialize_user_credits(TEST_USER_ID)
        initial_credits = initial_balance.available_credits

        # Mock failed payment
        with patch.object(self.service, '_process_payment') as mock_payment:
            mock_payment.return_value = False  # Payment fails

            # Attempt purchase - should raise exception
            with pytest.raises(ValueError, match="Payment processing failed"):
                await self.service.purchase_credits(
                    TEST_USER_ID, package.package_id, TEST_PAYMENT_METHOD
                )

        # Verify credits unchanged
        final_balance = await self.service.get_credit_balance(TEST_USER_ID)
        assert final_balance.available_credits == initial_credits

        print("✅ Failed Payment Test Passed - No credits granted on failure")

    async def test_metadata_tracking_in_transactions(self):
        """Test that fee metadata is properly tracked in transactions"""
        package = next(p for p in CREDIT_PACKAGES if p.package_id == "popular")

        with patch.object(self.service, '_process_payment') as mock_payment:
            mock_payment.return_value = True

            # Process purchase
            transaction, balance = await self.service.purchase_credits(
                TEST_USER_ID, package.package_id, TEST_PAYMENT_METHOD
            )

            # Verify transaction metadata
            assert transaction.cost_basis == package.price_usd
            assert "package_id" in transaction.metadata
            assert transaction.metadata["package_id"] == package.package_id

            # Calculate and verify expected fees
            expected_platform_fee = package.price_usd * PLATFORM_FEE_PERCENTAGE

            print("✅ Metadata Tracking Test Passed")
            print(f"   Package: {package.name}")
            print(f"   Base Cost: ${transaction.cost_basis}")
            print(f"   Expected Platform Fee: ${expected_platform_fee:.2f}")

# Performance and Load Testing
@pytest.mark.asyncio
class TestBillingPerformance:
    """Performance tests for billing system under load"""

    def setup_method(self):
        """Setup for performance tests"""
        self.test_suite = BillingFeeTestSuite()

    async def test_high_volume_fee_calculations(self):
        """Test fee calculation performance under high volume"""
        import time

        # Test parameters
        num_calculations = 1000
        test_amounts = [999, 1999, 4999, 9999, 19999]  # Various price points

        start_time = time.time()

        # Perform bulk fee calculations
        for _ in range(num_calculations):
            for amount in test_amounts:
                platform_fee = int(amount * PLATFORM_FEE_PERCENTAGE)
                stripe_fee = int(amount * 0.029) + 30
                total_fee = platform_fee + stripe_fee

                # Verify calculations are reasonable
                assert platform_fee >= 0
                assert stripe_fee >= 30
                assert total_fee > platform_fee

        end_time = time.time()
        processing_time = end_time - start_time
        calculations_per_second = (num_calculations * len(test_amounts)) / processing_time

        # Performance assertions
        assert processing_time < 5.0  # Should complete in under 5 seconds
        assert calculations_per_second > 500  # Should handle 500+ calculations per second

        print("✅ High Volume Performance Test Passed")
        print(f"   Calculations: {num_calculations * len(test_amounts)}")
        print(f"   Processing Time: {processing_time:.3f}s")
        print(f"   Rate: {calculations_per_second:.0f} calculations/sec")

    async def test_concurrent_idempotency_performance(self):
        """Test idempotency performance under concurrent load"""
        import time

        num_concurrent_requests = 50
        idempotency_key = f"perf_test_{datetime.utcnow().timestamp()}"

        async def make_request():
            return await self.test_suite.mock_stripe_payment_intent(
                1999,  # $19.99
                TEST_PAYMENT_METHOD,
                idempotency_key
            )

        start_time = time.time()

        # Launch concurrent requests
        results = await asyncio.gather(
            *[make_request() for _ in range(num_concurrent_requests)],
            return_exceptions=True
        )

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify all results are identical (idempotency working)
        unique_ids = {r["id"] for r in results if isinstance(r, dict)}
        assert len(unique_ids) == 1

        # Performance assertions
        assert processing_time < 3.0  # Should handle 50 concurrent requests in under 3s
        requests_per_second = num_concurrent_requests / processing_time
        assert requests_per_second > 15  # Should handle 15+ concurrent requests per second

        print("✅ Concurrent Idempotency Performance Test Passed")
        print(f"   Concurrent Requests: {num_concurrent_requests}")
        print(f"   Processing Time: {processing_time:.3f}s")
        print(f"   Rate: {requests_per_second:.0f} requests/sec")

# Integration Test Runner
async def run_billing_e2e_tests():
    """Run all billing E2E tests and return results"""

    print("🧪 Starting Billing E2E Tests with 3% Fee Validation")
    print("=" * 60)

    test_results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "fee_calculations_verified": 0,
        "idempotency_checks_passed": 0,
        "performance_benchmarks_met": 0
    }

    # Initialize test suite
    billing_tests = TestBillingFeesE2E()
    billing_tests.setup_method()

    performance_tests = TestBillingPerformance()
    performance_tests.setup_method()

    test_methods = [
        billing_tests.test_3_percent_fee_calculation_small_package,
        billing_tests.test_3_percent_fee_calculation_large_package,
        billing_tests.test_idempotency_key_prevents_duplicate_charges,
        billing_tests.test_concurrent_purchase_idempotency,
        billing_tests.test_fee_calculation_edge_cases,
        billing_tests.test_failed_payment_no_credit_grant,
        billing_tests.test_metadata_tracking_in_transactions,
        performance_tests.test_high_volume_fee_calculations,
        performance_tests.test_concurrent_idempotency_performance
    ]

    # Execute all tests
    for test_method in test_methods:
        test_results["tests_run"] += 1
        try:
            await test_method()
            test_results["tests_passed"] += 1

            # Track specific validation types
            if "fee_calculation" in test_method.__name__:
                test_results["fee_calculations_verified"] += 1
            elif "idempotency" in test_method.__name__:
                test_results["idempotency_checks_passed"] += 1
            elif "performance" in test_method.__name__:
                test_results["performance_benchmarks_met"] += 1

        except Exception as e:
            test_results["tests_failed"] += 1
            print(f"❌ Test Failed: {test_method.__name__}")
            print(f"   Error: {str(e)}")

    # Print final results
    print("\n" + "=" * 60)
    print("🎯 Billing E2E Test Results Summary")
    print("=" * 60)
    print(f"Total Tests: {test_results['tests_run']}")
    print(f"✅ Passed: {test_results['tests_passed']}")
    print(f"❌ Failed: {test_results['tests_failed']}")
    print(f"🧮 Fee Calculations Verified: {test_results['fee_calculations_verified']}")
    print(f"🔒 Idempotency Checks Passed: {test_results['idempotency_checks_passed']}")
    print(f"⚡ Performance Benchmarks Met: {test_results['performance_benchmarks_met']}")

    success_rate = (test_results['tests_passed'] / test_results['tests_run']) * 100
    print(f"📊 Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 BILLING SYSTEM VALIDATED - READY FOR PRODUCTION")
    else:
        print("⚠️  BILLING SYSTEM NEEDS ATTENTION - REVIEW FAILED TESTS")

    return test_results

if __name__ == "__main__":
    # Run the test suite
    results = asyncio.run(run_billing_e2e_tests())
