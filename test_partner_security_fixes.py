#!/usr/bin/env python3
"""
Security Test Suite for Partner SLA Trust Center Fixes
Tests authentication, authorization, and access controls for all partner endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

class SecurityTestSuite:
    """Comprehensive security test suite for Partner SLA Trust Center endpoints"""
    
    def __init__(self):
        self.session = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "details": []
        }
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        logger.info("🔧 Test session initialized")
    
    async def teardown(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
        logger.info("🧹 Test session cleaned up")
    
    async def get_auth_token(self, username: str = "admin", password: str = "admin123") -> Optional[str]:
        """Get authentication token for test user"""
        try:
            login_data = {
                "username": username,
                "password": password
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", data=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    logger.info(f"✅ Authentication successful for user: {username}")
                    return token
                else:
                    logger.error(f"❌ Authentication failed for user: {username} - Status: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Authentication error for user {username}: {e}")
            return None
    
    async def test_unauthorized_access(self, endpoint: str, method: str = "GET", expected_status: int = 401) -> bool:
        """Test that endpoint requires authentication"""
        try:
            method_func = getattr(self.session, method.lower())
            async with method_func(f"{BASE_URL}{endpoint}") as response:
                success = response.status == expected_status
                self.record_test_result(
                    f"Unauthorized access to {endpoint}",
                    success,
                    f"Expected {expected_status}, got {response.status}"
                )
                return success
        except Exception as e:
            self.record_test_result(f"Unauthorized access to {endpoint}", False, f"Error: {e}")
            return False
    
    async def test_authorized_access(self, endpoint: str, token: str, method: str = "GET", expected_status: int = 200, data: Optional[Dict] = None) -> bool:
        """Test authorized access to endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            method_func = getattr(self.session, method.lower())
            
            kwargs = {"headers": headers}
            if data and method.upper() in ["POST", "PUT", "PATCH"]:
                kwargs["json"] = data
            
            async with method_func(f"{BASE_URL}{endpoint}", **kwargs) as response:
                success = response.status == expected_status
                self.record_test_result(
                    f"Authorized access to {endpoint}",
                    success,
                    f"Expected {expected_status}, got {response.status}"
                )
                return success
        except Exception as e:
            self.record_test_result(f"Authorized access to {endpoint}", False, f"Error: {e}")
            return False
    
    async def test_partner_access_control(self, endpoint: str, partner_id: str, user_token: str, should_succeed: bool = True) -> bool:
        """Test partner-specific access control"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            full_endpoint = f"{endpoint}?partner_id={partner_id}" if "?" not in endpoint else f"{endpoint}&partner_id={partner_id}"
            
            async with self.session.get(f"{BASE_URL}{full_endpoint}", headers=headers) as response:
                if should_succeed:
                    success = response.status in [200, 201]
                    message = f"User should have access to partner {partner_id}"
                else:
                    success = response.status == 403
                    message = f"User should NOT have access to partner {partner_id}"
                
                self.record_test_result(
                    f"Partner access control: {endpoint} for partner {partner_id}",
                    success,
                    f"{message} - Status: {response.status}"
                )
                return success
        except Exception as e:
            self.record_test_result(f"Partner access control: {endpoint}", False, f"Error: {e}")
            return False
    
    def record_test_result(self, test_name: str, passed: bool, details: str):
        """Record test result"""
        if passed:
            self.test_results["passed"] += 1
            logger.info(f"✅ PASS: {test_name} - {details}")
        else:
            self.test_results["failed"] += 1
            logger.error(f"❌ FAIL: {test_name} - {details}")
        
        self.test_results["details"].append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def run_comprehensive_security_tests(self):
        """Run all security tests"""
        logger.info("🚀 Starting comprehensive security test suite")
        
        # Test endpoints that should require authentication
        endpoints_to_test = [
            "/partner/sla-trust-center/sla/dashboard",
            "/partner/sla-trust-center/sla/targets/professional",
            "/partner/sla-trust-center/sla/report/partner1",
            "/partner/sla-trust-center/trust-center/overview",
            "/partner/sla-trust-center/trust-center/certifications",
            "/partner/sla-trust-center/trust-center/incident-response",
            "/partner/sla-trust-center/trust-center/data-protection"
        ]
        
        logger.info("🔒 Testing unauthorized access (should be blocked)")
        for endpoint in endpoints_to_test:
            await self.test_unauthorized_access(endpoint)
        
        # Get authentication tokens for different user types
        logger.info("🔑 Getting authentication tokens")
        admin_token = await self.get_auth_token("admin", "admin123")
        partner_token = await self.get_auth_token("partner", "partner123")
        readonly_token = await self.get_auth_token("readonly", "readonly123")
        
        if not all([admin_token, partner_token, readonly_token]):
            logger.error("❌ Failed to get authentication tokens - cannot continue tests")
            return
        
        logger.info("✅ Testing authorized access with valid tokens")
        # Test authorized access for general endpoints
        general_endpoints = [
            "/partner/sla-trust-center/trust-center/overview",
            "/partner/sla-trust-center/trust-center/certifications",
            "/partner/sla-trust-center/trust-center/incident-response",
            "/partner/sla-trust-center/trust-center/data-protection"
        ]
        
        for endpoint in general_endpoints:
            await self.test_authorized_access(endpoint, admin_token)
            await self.test_authorized_access(endpoint, partner_token)
            await self.test_authorized_access(endpoint, readonly_token)
        
        logger.info("🏢 Testing partner-specific access control")
        # Test partner-specific access control
        partner_endpoints = [
            "/partner/sla-trust-center/sla/dashboard",
            "/partner/sla-trust-center/sla/report/partner"
        ]
        
        for endpoint in partner_endpoints:
            # Admin should have access to any partner
            await self.test_partner_access_control(endpoint, "partner", admin_token, should_succeed=True)
            # Partner user should have access to their own data
            await self.test_partner_access_control(endpoint, "partner", partner_token, should_succeed=True)
            # Partner user should NOT have access to other partner's data
            await self.test_partner_access_control(endpoint, "other_partner", partner_token, should_succeed=False)
            # Readonly user should NOT have access to partner-specific data
            await self.test_partner_access_control(endpoint, "partner", readonly_token, should_succeed=False)
        
        logger.info("🔐 Testing system-wide dashboard access (admin only)")
        # Test system-wide dashboard (admin only)
        await self.test_authorized_access("/partner/sla-trust-center/sla/dashboard", admin_token)
        await self.test_authorized_access("/partner/sla-trust-center/sla/dashboard", partner_token, expected_status=403)
        await self.test_authorized_access("/partner/sla-trust-center/sla/dashboard", readonly_token, expected_status=403)
        
        logger.info("🚨 Testing SLA breach recording (admin only)")
        # Test SLA breach recording (admin only)
        breach_data = {
            "partner_id": "admin",
            "metric_type": "availability",
            "target_value": 99.9,
            "actual_value": 99.0,
            "severity": "sev2_high",
            "tier": "professional"
        }
        
        await self.test_authorized_access("/partner/sla-trust-center/sla/breach", admin_token, "POST", 200, breach_data)
        await self.test_authorized_access("/partner/sla-trust-center/sla/breach", partner_token, "POST", 403, breach_data)
        await self.test_authorized_access("/partner/sla-trust-center/sla/breach", readonly_token, "POST", 403, breach_data)
        
        logger.info("📊 Generating test summary")
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "="*80)
        logger.info("🛡️  SECURITY TEST SUITE SUMMARY")
        logger.info("="*80)
        logger.info(f"📊 Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {self.test_results['passed']}")
        logger.info(f"❌ Failed: {self.test_results['failed']}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        logger.info("="*80)
        
        if self.test_results["failed"] == 0:
            logger.info("🎉 ALL SECURITY TESTS PASSED! Authentication and authorization are working correctly.")
        else:
            logger.error("⚠️  SOME TESTS FAILED! Review the failures and fix security issues.")
            
        # Show failed tests
        failed_tests = [detail for detail in self.test_results["details"] if not detail["passed"]]
        if failed_tests:
            logger.error("\n🚨 FAILED TESTS:")
            for test in failed_tests:
                logger.error(f"   - {test['test']}: {test['details']}")

async def main():
    """Run the security test suite"""
    test_suite = SecurityTestSuite()
    
    try:
        await test_suite.setup()
        await test_suite.run_comprehensive_security_tests()
    finally:
        await test_suite.teardown()

if __name__ == "__main__":
    asyncio.run(main())