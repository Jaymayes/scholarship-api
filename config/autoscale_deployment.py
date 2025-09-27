"""
Autoscale Deployment Configuration for Staging Soak Test
Executive-mandated capacity planning for 48-72 hour validation
"""

from typing import Dict, Any

class StagingAutoscaleConfig:
    """Autoscale configuration for staging deployment"""
    
    # Deployment Configuration
    DEPLOYMENT_TARGET = "autoscale"
    
    # Autoscaling Parameters
    MIN_REPLICAS = 2  # Minimum for availability during soak
    MAX_REPLICAS = 10  # Handle traffic spikes during validation
    TARGET_CPU_UTILIZATION = 70  # Scale out at 70% CPU
    TARGET_P95_LATENCY_MS = 100  # Scale out if P95 > 100ms
    
    # Traffic Management
    TRAFFIC_SHADOW_PERCENTAGE = 15  # 15% production traffic mirror
    SYNTHETIC_LOAD_ENABLED = True
    LOAD_TEST_RPS = 50  # Requests per second for synthetic load
    
    # Health Check Configuration
    HEALTH_CHECK_PATH = "/health"
    HEALTH_CHECK_INTERVAL = 10  # seconds
    HEALTH_CHECK_TIMEOUT = 5   # seconds
    HEALTH_CHECK_FAILURES_THRESHOLD = 3
    
    # Resource Limits (Per Replica)
    MEMORY_REQUEST = "256Mi"
    MEMORY_LIMIT = "512Mi" 
    CPU_REQUEST = "250m"  # 0.25 CPU cores
    CPU_LIMIT = "500m"    # 0.5 CPU cores
    
    @classmethod
    def get_deployment_config(cls) -> Dict[str, Any]:
        """Get deployment configuration for platform"""
        return {
            "deployment_target": cls.DEPLOYMENT_TARGET,
            "run": ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1"],
            "build": ["pip", "install", "--no-deps", "-r", "requirements.txt"],
            "autoscaling": {
                "enabled": True,
                "min_replicas": cls.MIN_REPLICAS,
                "max_replicas": cls.MAX_REPLICAS,
                "target_cpu_utilization": cls.TARGET_CPU_UTILIZATION,
                "target_latency_p95_ms": cls.TARGET_P95_LATENCY_MS
            },
            "health_check": {
                "path": cls.HEALTH_CHECK_PATH,
                "interval_seconds": cls.HEALTH_CHECK_INTERVAL,
                "timeout_seconds": cls.HEALTH_CHECK_TIMEOUT,
                "failure_threshold": cls.HEALTH_CHECK_FAILURES_THRESHOLD
            },
            "resources": {
                "requests": {
                    "memory": cls.MEMORY_REQUEST,
                    "cpu": cls.CPU_REQUEST
                },
                "limits": {
                    "memory": cls.MEMORY_LIMIT,
                    "cpu": cls.CPU_LIMIT
                }
            }
        }
    
    @classmethod
    def get_load_test_config(cls) -> Dict[str, Any]:
        """Get synthetic load testing configuration"""
        return {
            "enabled": cls.SYNTHETIC_LOAD_ENABLED,
            "target_rps": cls.LOAD_TEST_RPS,
            "duration_hours": 72,  # Full soak duration
            "endpoints": [
                {"path": "/health", "weight": 10},
                {"path": "/api/v1/scholarships", "weight": 40},
                {"path": "/api/v1/search", "weight": 30}, 
                {"path": "/api/v1/eligibility", "weight": 20}
            ],
            "traffic_patterns": [
                {"time": "00:00-08:00", "multiplier": 0.3},  # Low traffic
                {"time": "08:00-17:00", "multiplier": 1.0},  # Normal business hours
                {"time": "17:00-22:00", "multiplier": 0.7},  # Evening
                {"time": "22:00-24:00", "multiplier": 0.4}   # Night
            ]
        }
    
    @classmethod 
    def validate_autoscale_readiness(cls) -> Dict[str, bool]:
        """Validate autoscaling configuration readiness"""
        return {
            "min_replicas_sufficient": cls.MIN_REPLICAS >= 2,
            "max_replicas_adequate": cls.MAX_REPLICAS >= 5,
            "cpu_target_reasonable": 50 <= cls.TARGET_CPU_UTILIZATION <= 80,
            "latency_target_aggressive": cls.TARGET_P95_LATENCY_MS <= 120,
            "health_checks_configured": cls.HEALTH_CHECK_PATH == "/health",
            "resource_limits_set": bool(cls.MEMORY_LIMIT and cls.CPU_LIMIT),
            "load_testing_enabled": cls.SYNTHETIC_LOAD_ENABLED
        }

# Global autoscale configuration
staging_autoscale = StagingAutoscaleConfig()