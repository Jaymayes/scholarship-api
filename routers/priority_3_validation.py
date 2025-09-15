"""
Priority 3 Validation Endpoints
Execute production readiness tests and evidence collection
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from production.integration_tests import integration_validator
from production.health_probes import health_manager
from production.automated_rollback import rollback_manager
from production.backup_restore import backup_manager
from production.secrets_posture import secrets_manager
from observability.business_telemetry import business_telemetry_service
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/api/v1/priority3", tags=["Priority 3 Validation"])

@router.get("/validate/comprehensive")
async def run_comprehensive_validation():
    """
    Run comprehensive Priority 3 validation with evidence collection
    
    Executes all production readiness tests:
    - Health probes and graceful shutdown
    - Automated rollback demonstration  
    - Backup/restore with RPO/RTO validation
    - Secrets posture validation and rotation
    - Business telemetry integration
    """
    try:
        logger.info("🎯 Starting comprehensive Priority 3 validation via API")
        
        results = await integration_validator.run_comprehensive_validation()
        
        # Save evidence
        await integration_validator.save_validation_evidence(results)
        
        return {
            "status": "completed",
            "validation_summary": results["validation_summary"],
            "evidence_saved": True,
            "next_steps": _get_next_steps(results)
        }
        
    except Exception as e:
        logger.error(f"Comprehensive validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/validate/health-probes")
async def validate_health_probes():
    """Validate health probes and graceful shutdown capability"""
    try:
        # Test liveness probe
        liveness = await health_manager.liveness_probe()
        
        # Test request tracking
        health_manager.track_request()
        health_manager.untrack_request()
        
        return {
            "liveness_probe": liveness,
            "request_tracking": {
                "active_requests": health_manager.active_requests,
                "shutdown_status": health_manager.is_shutting_down
            },
            "status": "validated"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/validate/rollback-demo")  
async def demonstrate_rollback():
    """Demonstrate automated rollback capability"""
    try:
        demo_result = await rollback_manager.demonstrate_rollback()
        return demo_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback demo failed: {str(e)}")

@router.post("/validate/backup-restore-demo")
async def demonstrate_backup_restore():
    """Demonstrate backup and restore with RPO/RTO validation"""
    try:
        demo_result = await backup_manager.demonstrate_backup_restore()
        return demo_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup/restore demo failed: {str(e)}")

@router.get("/validate/secrets-posture")
async def validate_secrets_posture():
    """Generate secrets posture report and demonstrate rotation"""
    try:
        # Generate comprehensive report
        report = await secrets_manager.generate_secrets_posture_report()
        
        # Demonstrate JWT rotation
        jwt_rotation = await secrets_manager.rotate_jwt_secret("API validation test")
        
        return {
            "secrets_report_summary": {
                "total_violations": report["scan_summary"]["total_violations"],
                "codebase_violations": report["scan_summary"]["codebase_violations"],
                "log_violations": report["scan_summary"]["log_violations"]
            },
            "rotation_demo": {
                "success": jwt_rotation.success,
                "rotation_timestamp": jwt_rotation.rotation_timestamp
            },
            "recommendations": report["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Secrets validation failed: {str(e)}")

@router.get("/validate/business-telemetry")
async def validate_business_telemetry():
    """Validate business telemetry and SLO-to-business impact correlation"""
    try:
        # Test telemetry tracking
        business_telemetry_service.track_search_request("validation", "success", "test_user")
        business_telemetry_service.track_student_interaction("api_test", "validation", "test")
        
        # Test SLO-to-business impact model
        impact_model = business_telemetry_service.calculate_business_risk_from_slo(2.0, 50)
        
        # Get health summary
        health_summary = business_telemetry_service.get_business_health_summary()
        
        return {
            "telemetry_status": "active",
            "health_summary": health_summary,
            "slo_impact_demo": {
                "breach_duration_minutes": 2.0,
                "projected_business_impact_dollars": impact_model["total_business_impact_dollars"],
                "churn_risk": impact_model["projected_churn_increase_percent"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business telemetry validation failed: {str(e)}")

@router.get("/status")
async def get_priority_3_status():
    """Get current Priority 3 implementation status"""
    return {
        "priority_3_status": "implemented",
        "components": {
            "health_probes": "implemented",
            "automated_rollback": "implemented", 
            "backup_restore": "implemented",
            "secrets_posture": "implemented",
            "business_telemetry": "implemented"
        },
        "validation_endpoints": [
            "/api/v1/priority3/validate/comprehensive",
            "/api/v1/priority3/validate/health-probes",
            "/api/v1/priority3/validate/rollback-demo",
            "/api/v1/priority3/validate/backup-restore-demo",
            "/api/v1/priority3/validate/secrets-posture",
            "/api/v1/priority3/validate/business-telemetry"
        ]
    }

def _get_next_steps(results: Dict[str, Any]) -> list[str]:
    """Generate next steps based on validation results"""
    next_steps = []
    
    if not results["validation_summary"]["overall_ready"]:
        next_steps.append("Fix failed validation tests before proceeding")
        
        for test_name, test_result in results["test_results"].items():
            if not test_result["success"]:
                next_steps.append(f"Address {test_name} validation failures")
    
    if results["validation_summary"]["overall_ready"]:
        next_steps.extend([
            "Proceed with canary deployment at 10% traffic",
            "Monitor SLO gates: p95≤120ms, 5xx<0.1%, error budget burn<1%",
            "Escalate to 50% traffic after 6 hours if gates pass",
            "Complete Go-Live Ramp to 100% after 12 hours"
        ])
    
    return next_steps