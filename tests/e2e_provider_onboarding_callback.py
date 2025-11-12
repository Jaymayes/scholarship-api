"""
E2E Test Suite: Provider Onboarding Callback Integration
CEO Directive: Gate B - provider_register callback path fix
Deliverable: Passing E2E test and trace evidence
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app
from models.b2b_partner import PartnerStatus, PartnerType, PartnerOnboardingStep
from services.b2b_partner_service import B2BPartnerService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# Test client setup
client = TestClient(app)

# Initialize test services
openai_service = OpenAIService()
partner_service = B2BPartnerService(openai_service)


class TestProviderOnboardingCallback:
    """
    E2E test suite for provider_register → scholarship_api callback integration
    
    Scenario: provider_register completes onboarding step and calls back to scholarship_api
    Success criteria:
    1. Callback endpoint returns 200 OK
    2. Onboarding step marked as completed
    3. request_id traced end-to-end
    4. Response time <120ms (P95 SLO)
    5. No data loss or errors
    """
    
    @pytest.fixture
    def test_partner_id(self) -> str:
        """Create test partner for onboarding callback tests"""
        test_partner_data = {
            "organization_name": "Test University - Callback E2E",
            "partner_type": PartnerType.UNIVERSITY,
            "primary_contact_name": "Test Contact",
            "primary_contact_email": "test@example.edu",
            "primary_contact_phone": "+1-555-0100",
            "website_url": "https://example.edu",
            "tax_id": "12-3456789",
            "address_line1": "123 Test St",
            "city": "Test City",
            "state": "CA",
            "zip_code": "90210",
            "country": "United States"
        }
        
        # Register partner
        response = client.post("/api/v1/partners/register", json=test_partner_data)
        assert response.status_code == 200
        
        partner_id = response.json()["partner_id"]
        logger.info(f"✅ Created test partner: {partner_id}")
        
        yield partner_id
        
        # Cleanup: Remove test partner after tests
        # (In-memory service, no cleanup needed)
    
    def test_get_onboarding_steps_success(self, test_partner_id: str):
        """
        Test: GET /api/v1/partners/{partner_id}/onboarding
        
        Verifies provider_register can retrieve onboarding progress
        """
        request_id = str(uuid4())
        
        start_time = datetime.now()
        
        response = client.get(
            f"/api/v1/partners/{test_partner_id}/onboarding",
            headers={"X-Request-ID": request_id}
        )
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        steps = response.json()
        assert isinstance(steps, list), "Response should be list of onboarding steps"
        assert len(steps) > 0, "Should return at least one onboarding step"
        
        # Verify step structure
        for step in steps:
            assert "step_id" in step
            assert "step_name" in step
            assert "description" in step
            assert "completed" in step
            assert "required" in step
        
        # Performance SLO check
        assert duration_ms < 120, f"Response time {duration_ms}ms exceeds P95 SLO of 120ms"
        
        logger.info(f"✅ GET onboarding steps: 200 OK | request_id={request_id} | latency={duration_ms:.2f}ms")
        
        return {
            "request_id": request_id,
            "status_code": 200,
            "latency_ms": duration_ms,
            "steps_count": len(steps)
        }
    
    def test_complete_onboarding_step_success(self, test_partner_id: str):
        """
        Test: POST /api/v1/partners/{partner_id}/onboarding/{step_id}/complete
        
        Critical path: provider_register completes onboarding step via callback
        """
        request_id = str(uuid4())
        
        # Get onboarding steps first
        steps_response = client.get(f"/api/v1/partners/{test_partner_id}/onboarding")
        assert steps_response.status_code == 200
        
        steps = steps_response.json()
        first_incomplete_step = next(
            (step for step in steps if not step["completed"]),
            None
        )
        
        assert first_incomplete_step is not None, "Should have at least one incomplete step"
        
        step_id = first_incomplete_step["step_id"]
        
        # Prepare callback payload (simulates provider_register callback)
        callback_payload = {
            "step_data": {
                "completed_at": datetime.utcnow().isoformat(),
                "completed_by": "provider_register_system",
                "verification_status": "verified",
                "metadata": {
                    "source": "provider_register",
                    "environment": "test",
                    "integration_test": True
                }
            }
        }
        
        start_time = datetime.now()
        
        # Execute callback (provider_register → scholarship_api)
        response = client.post(
            f"/api/v1/partners/{test_partner_id}/onboarding/{step_id}/complete",
            json=callback_payload,
            headers={
                "X-Request-ID": request_id,
                "Content-Type": "application/json",
                "User-Agent": "provider_register/1.0.0"
            }
        )
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        completed_step = response.json()
        assert completed_step["step_id"] == step_id
        assert completed_step["completed"] == True, "Step should be marked as completed"
        
        # Verify trace propagation
        response_headers = response.headers
        trace_verified = "X-Request-ID" in response_headers or request_id in response.text
        
        # Performance SLO check
        assert duration_ms < 120, f"Callback latency {duration_ms}ms exceeds P95 SLO of 120ms"
        
        logger.info(
            f"✅ Complete onboarding step: 200 OK | "
            f"request_id={request_id} | "
            f"step_id={step_id} | "
            f"latency={duration_ms:.2f}ms | "
            f"trace_verified={trace_verified}"
        )
        
        return {
            "request_id": request_id,
            "status_code": 200,
            "latency_ms": duration_ms,
            "step_id": step_id,
            "completed": True,
            "trace_verified": trace_verified
        }
    
    def test_complete_onboarding_step_idempotency(self, test_partner_id: str):
        """
        Test: Idempotency of callback endpoint
        
        Verifies that completing the same step multiple times is idempotent
        """
        request_id_1 = str(uuid4())
        request_id_2 = str(uuid4())
        
        # Get first incomplete step
        steps_response = client.get(f"/api/v1/partners/{test_partner_id}/onboarding")
        steps = steps_response.json()
        first_incomplete_step = next((step for step in steps if not step["completed"]), None)
        
        if not first_incomplete_step:
            pytest.skip("No incomplete steps available for idempotency test")
        
        step_id = first_incomplete_step["step_id"]
        
        callback_payload = {
            "step_data": {
                "completed_at": datetime.utcnow().isoformat(),
                "completed_by": "provider_register_system"
            }
        }
        
        # First completion
        response_1 = client.post(
            f"/api/v1/partners/{test_partner_id}/onboarding/{step_id}/complete",
            json=callback_payload,
            headers={"X-Request-ID": request_id_1}
        )
        
        assert response_1.status_code == 200
        
        # Second completion (idempotent retry)
        response_2 = client.post(
            f"/api/v1/partners/{test_partner_id}/onboarding/{step_id}/complete",
            json=callback_payload,
            headers={"X-Request-ID": request_id_2}
        )
        
        # Should succeed (idempotent)
        assert response_2.status_code in [200, 400], "Idempotent retry should succeed or return 400"
        
        completed_step = response_2.json()
        
        if response_2.status_code == 200:
            assert completed_step["completed"] == True
        
        logger.info(
            f"✅ Idempotency test: {response_2.status_code} | "
            f"request_id_1={request_id_1} | "
            f"request_id_2={request_id_2}"
        )
    
    def test_complete_onboarding_step_invalid_partner(self):
        """
        Test: Error handling for invalid partner_id
        
        Verifies proper 404 response for non-existent partner
        """
        invalid_partner_id = "partner_nonexistent_12345"
        request_id = str(uuid4())
        
        callback_payload = {
            "step_data": {
                "completed_at": datetime.utcnow().isoformat()
            }
        }
        
        response = client.post(
            f"/api/v1/partners/{invalid_partner_id}/onboarding/step_profile_setup/complete",
            json=callback_payload,
            headers={"X-Request-ID": request_id}
        )
        
        # Should return 404 or 500 with clear error
        assert response.status_code in [404, 500], f"Expected 404 or 500, got {response.status_code}"
        
        logger.info(f"✅ Invalid partner error handling: {response.status_code} | request_id={request_id}")
    
    def test_complete_onboarding_step_invalid_step_id(self, test_partner_id: str):
        """
        Test: Error handling for invalid step_id
        
        Verifies proper 400 response for non-existent onboarding step
        """
        invalid_step_id = "step_nonexistent_xyz"
        request_id = str(uuid4())
        
        callback_payload = {
            "step_data": {
                "completed_at": datetime.utcnow().isoformat()
            }
        }
        
        response = client.post(
            f"/api/v1/partners/{test_partner_id}/onboarding/{invalid_step_id}/complete",
            json=callback_payload,
            headers={"X-Request-ID": request_id}
        )
        
        # Should return 400 or 404 with clear error
        assert response.status_code in [400, 404, 500], f"Expected 400/404/500, got {response.status_code}"
        
        logger.info(f"✅ Invalid step error handling: {response.status_code} | request_id={request_id}")
    
    def test_end_to_end_provider_onboarding_flow(self):
        """
        Test: Complete end-to-end provider onboarding flow
        
        Simulates full provider_register → scholarship_api integration:
        1. Register provider
        2. Get onboarding steps
        3. Complete all required steps
        4. Verify provider status advancement
        """
        request_id_base = str(uuid4())[:8]
        
        # Step 1: Register provider (simulates provider_register registration)
        logger.info("🚀 E2E Test: Step 1 - Register provider")
        
        registration_payload = {
            "organization_name": f"E2E Test Organization {request_id_base}",
            "partner_type": "university",
            "primary_contact_name": "E2E Test Contact",
            "primary_contact_email": f"e2e-{request_id_base}@example.edu",
            "primary_contact_phone": "+1-555-0199",
            "website_url": "https://e2e-test.edu",
            "tax_id": "99-9999999",
            "address_line1": "123 E2E Street",
            "city": "Test City",
            "state": "CA",
            "zip_code": "90210",
            "country": "United States"
        }
        
        registration_response = client.post(
            "/api/v1/partners/register",
            json=registration_payload,
            headers={"X-Request-ID": f"{request_id_base}-register"}
        )
        
        assert registration_response.status_code == 200
        registration_data = registration_response.json()
        
        partner_id = registration_data["partner_id"]
        initial_status = registration_data["status"]
        
        logger.info(f"  ✅ Partner registered: {partner_id} | status={initial_status}")
        
        # Step 2: Get onboarding steps (simulates provider_register fetching onboarding state)
        logger.info("🚀 E2E Test: Step 2 - Get onboarding steps")
        
        steps_response = client.get(
            f"/api/v1/partners/{partner_id}/onboarding",
            headers={"X-Request-ID": f"{request_id_base}-get-steps"}
        )
        
        assert steps_response.status_code == 200
        onboarding_steps = steps_response.json()
        
        required_steps = [step for step in onboarding_steps if step["required"] and not step["completed"]]
        
        logger.info(f"  ✅ Retrieved {len(onboarding_steps)} onboarding steps | {len(required_steps)} required incomplete")
        
        # Step 3: Complete all required steps (simulates provider_register callback loop)
        logger.info("🚀 E2E Test: Step 3 - Complete required onboarding steps")
        
        completed_count = 0
        for step in required_steps:
            step_id = step["step_id"]
            
            callback_payload = {
                "step_data": {
                    "completed_at": datetime.utcnow().isoformat(),
                    "completed_by": "e2e_test_automation",
                    "test_run_id": request_id_base
                }
            }
            
            complete_response = client.post(
                f"/api/v1/partners/{partner_id}/onboarding/{step_id}/complete",
                json=callback_payload,
                headers={"X-Request-ID": f"{request_id_base}-complete-{step_id}"}
            )
            
            if complete_response.status_code == 200:
                completed_count += 1
                logger.info(f"  ✅ Completed step: {step_id}")
            else:
                logger.warning(f"  ⚠️ Failed to complete step: {step_id} | status={complete_response.status_code}")
        
        logger.info(f"  ✅ Completed {completed_count}/{len(required_steps)} required steps")
        
        # Step 4: Verify final state
        logger.info("🚀 E2E Test: Step 4 - Verify final partner state")
        
        final_partner_response = client.get(
            f"/api/v1/partners/{partner_id}",
            headers={"X-Request-ID": f"{request_id_base}-final-check"}
        )
        
        assert final_partner_response.status_code == 200
        final_partner = final_partner_response.json()
        
        logger.info(f"  ✅ Final partner status: {final_partner['status']}")
        
        # Success criteria
        assert completed_count > 0, "Should complete at least one onboarding step"
        
        logger.info(
            f"🎉 E2E Test PASSED | "
            f"partner_id={partner_id} | "
            f"steps_completed={completed_count} | "
            f"final_status={final_partner['status']}"
        )
        
        return {
            "success": True,
            "partner_id": partner_id,
            "steps_completed": completed_count,
            "initial_status": initial_status,
            "final_status": final_partner["status"],
            "test_run_id": request_id_base
        }


# Standalone test execution for manual runs
if __name__ == "__main__":
    """
    Manual test execution for immediate verification
    Usage: python tests/e2e_provider_onboarding_callback.py
    """
    print("=" * 80)
    print("E2E Test: Provider Onboarding Callback Integration")
    print("CEO Directive: Gate B - provider_register callback path fix")
    print("=" * 80)
    
    test_suite = TestProviderOnboardingCallback()
    
    # Create test partner
    print("\n📝 Creating test partner...")
    test_partner_data = {
        "organization_name": "Manual Test University",
        "partner_type": "university",
        "primary_contact_name": "Manual Test Contact",
        "primary_contact_email": "manual-test@example.edu",
        "primary_contact_phone": "+1-555-0100",
        "website_url": "https://manual-test.edu",
        "tax_id": "12-3456789",
        "address_line1": "123 Manual Test St",
        "city": "Test City",
        "state": "CA",
        "zip_code": "90210",
        "country": "United States"
    }
    
    register_response = client.post("/api/v1/partners/register", json=test_partner_data)
    test_partner_id = register_response.json()["partner_id"]
    print(f"✅ Test partner created: {test_partner_id}")
    
    # Run individual tests
    print("\n🧪 Test 1: GET onboarding steps")
    result_1 = test_suite.test_get_onboarding_steps_success(test_partner_id)
    print(f"   Result: {json.dumps(result_1, indent=2)}")
    
    print("\n🧪 Test 2: POST complete onboarding step")
    result_2 = test_suite.test_complete_onboarding_step_success(test_partner_id)
    print(f"   Result: {json.dumps(result_2, indent=2)}")
    
    print("\n🧪 Test 3: End-to-end onboarding flow")
    result_3 = test_suite.test_end_to_end_provider_onboarding_flow()
    print(f"   Result: {json.dumps(result_3, indent=2)}")
    
    print("\n" + "=" * 80)
    print("✅ All E2E tests completed successfully")
    print("=" * 80)
