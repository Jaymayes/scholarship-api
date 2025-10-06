"""
Synthetic Monitoring - Health check monitors with alerting
"""

import time
import asyncio
import httpx
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("synthetic_monitors")


class SyntheticMonitor:
    """Base class for synthetic monitors"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.results = []
        self.alert_threshold = 0.95
    
    async def check(self) -> dict:
        """Run health check - to be implemented by subclasses"""
        raise NotImplementedError
    
    def record_result(self, success: bool, latency_ms: float, details: dict = None):
        """Record check result"""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "latency_ms": latency_ms,
            "details": details or {}
        }
        self.results.append(result)
        
        if len(self.results) > 100:
            self.results = self.results[-100:]
        
        return result
    
    def get_success_rate(self, window_size: int = 20) -> float:
        """Calculate success rate over last N checks"""
        if not self.results:
            return 1.0
        
        recent = self.results[-window_size:]
        successes = sum(1 for r in recent if r["success"])
        return successes / len(recent)
    
    def should_alert(self) -> bool:
        """Check if success rate below threshold"""
        return self.get_success_rate() < self.alert_threshold


class HealthCheckMonitor(SyntheticMonitor):
    """Monitor: Health endpoint"""
    
    def __init__(self, base_url: str):
        super().__init__("Health Check", base_url)
        self.endpoint = "/health"
        self.expected_latency_ms = 50
    
    async def check(self) -> dict:
        start = time.time()
        success = False
        details = {}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}{self.endpoint}")
                latency_ms = (time.time() - start) * 1000
                
                success = response.status_code == 200
                details = {
                    "status_code": response.status_code,
                    "latency_ok": latency_ms < self.expected_latency_ms
                }
                
                result = self.record_result(success, latency_ms, details)
                
                if not success:
                    logger.warning(f"❌ {self.name} FAILED: {response.status_code}")
                elif latency_ms > self.expected_latency_ms:
                    logger.warning(f"⚠️ {self.name} SLOW: {latency_ms:.2f}ms (expected <{self.expected_latency_ms}ms)")
                else:
                    logger.info(f"✅ {self.name} OK: {latency_ms:.2f}ms")
                
                return result
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            details = {"error": str(e)}
            logger.error(f"❌ {self.name} ERROR: {str(e)}")
            return self.record_result(False, latency_ms, details)


class AuthLoginMonitor(SyntheticMonitor):
    """Monitor: Login endpoint"""
    
    def __init__(self, base_url: str, username: str, password: str):
        super().__init__("Auth Login", base_url)
        self.endpoint = "/api/v1/auth/login-simple"
        self.username = username
        self.password = password
        self.expected_latency_ms = 200
    
    async def check(self) -> dict:
        start = time.time()
        success = False
        details = {}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}{self.endpoint}",
                    json={"username": self.username, "password": self.password}
                )
                latency_ms = (time.time() - start) * 1000
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    token = data.get("access_token")
                    details = {
                        "status_code": response.status_code,
                        "token_received": bool(token),
                        "latency_ok": latency_ms < self.expected_latency_ms
                    }
                else:
                    details = {"status_code": response.status_code}
                
                result = self.record_result(success, latency_ms, details)
                
                if not success:
                    logger.warning(f"❌ {self.name} FAILED: {response.status_code}")
                elif latency_ms > self.expected_latency_ms:
                    logger.warning(f"⚠️ {self.name} SLOW: {latency_ms:.2f}ms")
                else:
                    logger.info(f"✅ {self.name} OK: {latency_ms:.2f}ms, token: {bool(token)}")
                
                return result
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            details = {"error": str(e)}
            logger.error(f"❌ {self.name} ERROR: {str(e)}")
            return self.record_result(False, latency_ms, details)


class AuthenticatedSearchMonitor(SyntheticMonitor):
    """Monitor: Authenticated search endpoint"""
    
    def __init__(self, base_url: str, token_provider):
        super().__init__("Authenticated Search", base_url)
        self.endpoint = "/api/v1/search"
        self.token_provider = token_provider
        self.expected_latency_ms = 300
    
    async def check(self) -> dict:
        start = time.time()
        success = False
        details = {}
        
        try:
            token = await self.token_provider()
            if not token:
                logger.error(f"❌ {self.name} FAILED: No auth token")
                return self.record_result(False, 0, {"error": "No auth token"})
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}{self.endpoint}",
                    params={"query": "test"},
                    headers={"Authorization": f"Bearer {token}"}
                )
                latency_ms = (time.time() - start) * 1000
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    details = {
                        "status_code": response.status_code,
                        "results_count": len(data.get("results", [])),
                        "latency_ok": latency_ms < self.expected_latency_ms
                    }
                else:
                    details = {"status_code": response.status_code}
                
                result = self.record_result(success, latency_ms, details)
                
                if not success:
                    logger.warning(f"❌ {self.name} FAILED: {response.status_code}")
                elif latency_ms > self.expected_latency_ms:
                    logger.warning(f"⚠️ {self.name} SLOW: {latency_ms:.2f}ms (expected <{self.expected_latency_ms}ms)")
                else:
                    logger.info(f"✅ {self.name} OK: {latency_ms:.2f}ms, {details.get('results_count', 0)} results")
                
                return result
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            details = {"error": str(e)}
            logger.error(f"❌ {self.name} ERROR: {str(e)}")
            return self.record_result(False, latency_ms, details)


class SyntheticMonitoringService:
    """Service to manage all synthetic monitors"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.monitors = []
        self.running = False
        self.login_token = None
    
    def setup_monitors(self, username: str, password: str):
        """Setup all monitoring checks"""
        self.monitors = [
            HealthCheckMonitor(self.base_url),
            AuthLoginMonitor(self.base_url, username, password)
        ]
        
        async def get_login_token():
            if self.monitors and len(self.monitors) > 1:
                login_monitor = self.monitors[1]
                if login_monitor.results:
                    latest = login_monitor.results[-1]
                    if latest.get("success") and latest.get("details", {}).get("token_received"):
                        return self.login_token
            return None
        
        self.monitors.append(
            AuthenticatedSearchMonitor(self.base_url, get_login_token)
        )
    
    async def run_all_checks(self):
        """Run all monitor checks"""
        results = []
        for monitor in self.monitors:
            result = await monitor.check()
            results.append({
                "monitor": monitor.name,
                **result
            })
        
        alerts = []
        for monitor in self.monitors:
            if monitor.should_alert():
                alerts.append({
                    "monitor": monitor.name,
                    "success_rate": monitor.get_success_rate(),
                    "threshold": monitor.alert_threshold
                })
        
        return {"checks": results, "alerts": alerts}
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring loop"""
        self.running = True
        logger.info(f"🔄 Starting synthetic monitoring (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                results = await self.run_all_checks()
                
                if results["alerts"]:
                    logger.warning(f"⚠️ ALERTS: {len(results['alerts'])} monitors below threshold")
                    for alert in results["alerts"]:
                        logger.warning(f"  - {alert['monitor']}: {alert['success_rate']*100:.1f}% (threshold: {alert['threshold']*100:.1f}%)")
                
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop monitoring loop"""
        self.running = False
        logger.info("🛑 Stopped synthetic monitoring")


monitoring_service = SyntheticMonitoringService("http://localhost:5000")
