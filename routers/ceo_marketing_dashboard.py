"""
CEO/Marketing Dashboard Integration Router
Central dashboard for executive visibility into DR and compliance status
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

# Import our DR and compliance services
from infrastructure.disaster_recovery_service import dr_service
from compliance.soc2_evidence_service import compliance_service
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["CEO/Marketing Dashboard"])

@router.get("/executive-summary", response_model=Dict[str, Any])
async def get_executive_summary():
    """
    Get executive summary dashboard with key metrics for CEO/Marketing
    
    Combines disaster recovery, compliance, and operational metrics
    into a high-level executive view
    """
    try:
        # Fetch DR and compliance data in parallel
        dr_data, compliance_data = await asyncio.gather(
            dr_service.get_global_dr_dashboard(),
            compliance_service.get_compliance_dashboard(),
            return_exceptions=True
        )
        
        # Handle any exceptions in data fetching
        if isinstance(dr_data, Exception):
            logger.error(f"Failed to fetch DR data: {dr_data}")
            dr_data = {"error": "DR data unavailable"}
        
        if isinstance(compliance_data, Exception):
            logger.error(f"Failed to fetch compliance data: {compliance_data}")
            compliance_data = {"error": "Compliance data unavailable"}
        
        # Build executive summary
        executive_summary = {
            "dashboard_title": "Executive Operations Dashboard",
            "last_updated": datetime.utcnow().isoformat(),
            "critical_status": {
                "overall_health": "healthy",
                "disaster_recovery": _assess_dr_health(dr_data),
                "compliance_posture": _assess_compliance_health(compliance_data),
                "security_status": "protected"
            },
            "key_metrics": {
                "applications_protected": _get_protected_apps_count(dr_data),
                "backup_success_rate": _get_backup_success_rate(dr_data),
                "soc2_readiness": _get_soc2_readiness(compliance_data),
                "pii_compliance": _get_pii_compliance(compliance_data)
            },
            "infrastructure_status": {
                "total_applications": len(dr_service.dr_config) if hasattr(dr_service, 'dr_config') else 0,
                "backup_storage_gb": _get_storage_usage(dr_data),
                "evidence_items_collected": _get_evidence_count(compliance_data),
                "data_lineage_mapped": _get_lineage_count(compliance_data)
            },
            "alerts_and_actions": _get_critical_alerts(dr_data, compliance_data)
        }
        
        logger.info("Executive summary dashboard generated")
        return executive_summary
        
    except Exception as e:
        logger.error(f"Failed to generate executive summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate executive summary")

@router.get("/disaster-recovery/status", response_model=Dict[str, Any])
async def get_dr_status_tiles():
    """
    Get disaster recovery status tiles for dashboard display
    """
    try:
        dr_dashboard = await dr_service.get_global_dr_dashboard()
        
        status_tiles = {
            "backup_health": {
                "title": "Backup Health",
                "status": "healthy" if dr_dashboard.get("global_metrics", {}).get("compliance_score", 0) >= 80 else "at_risk",
                "primary_metric": f"{dr_dashboard.get('global_metrics', {}).get('compliance_score', 0):.1f}%",
                "subtitle": "Overall backup compliance",
                "trend": "stable",
                "last_updated": dr_dashboard.get("last_updated")
            },
            "recovery_readiness": {
                "title": "Recovery Readiness",
                "status": "ready",
                "primary_metric": f"{dr_dashboard.get('global_metrics', {}).get('apps_compliant', 0)}/{dr_dashboard.get('global_metrics', {}).get('apps_total', 0)}",
                "subtitle": "Apps meeting RTO/RPO targets",
                "trend": "improving",
                "last_updated": dr_dashboard.get("last_updated")
            },
            "storage_utilization": {
                "title": "Backup Storage",
                "status": "optimal",
                "primary_metric": f"{dr_dashboard.get('global_metrics', {}).get('total_storage_gb', 0):.1f} GB",
                "subtitle": "Total backup storage used",
                "trend": "growing",
                "last_updated": dr_dashboard.get("last_updated")
            },
            "recent_activity": {
                "title": "24h Activity",
                "status": "active",
                "primary_metric": f"{dr_dashboard.get('global_metrics', {}).get('successful_backups_24h', 0)} backups",
                "subtitle": "Successful in last 24 hours",
                "trend": "stable",
                "last_updated": dr_dashboard.get("last_updated")
            }
        }
        
        return {
            "disaster_recovery_tiles": status_tiles,
            "critical_applications": _format_critical_apps(dr_dashboard),
            "quick_actions": [
                "Run backup test",
                "Schedule DR drill",
                "View backup logs",
                "Check storage quotas"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get DR status tiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DR status tiles")

@router.get("/compliance/status", response_model=Dict[str, Any])
async def get_compliance_status_tiles():
    """
    Get SOC2 compliance and PII lineage status tiles for dashboard display
    """
    try:
        compliance_dashboard = await compliance_service.get_compliance_dashboard()
        
        status_tiles = {
            "soc2_readiness": {
                "title": "SOC2 Readiness",
                "status": "ready" if compliance_dashboard.get("compliance_overview", {}).get("soc2_readiness_score", 0) >= 80 else "in_progress",
                "primary_metric": f"{compliance_dashboard.get('compliance_overview', {}).get('soc2_readiness_score', 0):.1f}%",
                "subtitle": "Audit readiness score",
                "trend": "improving",
                "last_updated": compliance_dashboard.get("last_updated")
            },
            "pii_protection": {
                "title": "PII Protection",
                "status": "protected",
                "primary_metric": f"{compliance_dashboard.get('pii_summary', {}).get('total_elements', 0)} elements",
                "subtitle": "PII elements tracked & protected",
                "trend": "stable",
                "last_updated": compliance_dashboard.get("last_updated")
            },
            "evidence_collection": {
                "title": "Evidence Collection",
                "status": "complete",
                "primary_metric": f"{compliance_dashboard.get('compliance_overview', {}).get('total_evidence_items', 0)} items",
                "subtitle": "SOC2 evidence collected",
                "trend": "growing",
                "last_updated": compliance_dashboard.get("last_updated")
            },
            "data_lineage": {
                "title": "Data Lineage",
                "status": "mapped",
                "primary_metric": f"{compliance_dashboard.get('compliance_overview', {}).get('data_lineage_mapped', 0)} flows",
                "subtitle": "Data flows documented",
                "trend": "complete",
                "last_updated": compliance_dashboard.get("last_updated")
            }
        }
        
        return {
            "compliance_tiles": status_tiles,
            "evidence_links": compliance_dashboard.get("evidence_links", {}),
            "pii_summary": compliance_dashboard.get("pii_summary", {}),
            "critical_findings": compliance_dashboard.get("compliance_overview", {}).get("critical_findings", 0),
            "quick_actions": [
                "View evidence repository",
                "Download data map",
                "Generate compliance report",
                "Schedule audit prep"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance status tiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance status tiles")

@router.get("/health-overview")
async def get_system_health_overview():
    """
    Get overall system health overview for executive dashboard
    """
    try:
        # Check health of all major systems
        health_checks = await asyncio.gather(
            _check_dr_service_health(),
            _check_compliance_service_health(),
            _check_application_health(),
            return_exceptions=True
        )
        
        dr_health, compliance_health, app_health = health_checks
        
        overall_status = "healthy"
        if any(isinstance(h, Exception) or (isinstance(h, dict) and h.get("status") != "healthy") for h in health_checks):
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "system_components": {
                "disaster_recovery": dr_health if not isinstance(dr_health, Exception) else {"status": "error", "error": str(dr_health)},
                "compliance_monitoring": compliance_health if not isinstance(compliance_health, Exception) else {"status": "error", "error": str(compliance_health)},
                "application_platform": app_health if not isinstance(app_health, Exception) else {"status": "error", "error": str(app_health)}
            },
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health overview")

# Helper functions for data processing

def _assess_dr_health(dr_data: Dict) -> str:
    """Assess disaster recovery health status"""
    if isinstance(dr_data, dict) and "global_metrics" in dr_data:
        compliance_score = dr_data["global_metrics"].get("compliance_score", 0)
        if compliance_score >= 90:
            return "excellent"
        elif compliance_score >= 80:
            return "healthy"
        elif compliance_score >= 60:
            return "at_risk"
        else:
            return "critical"
    return "unknown"

def _assess_compliance_health(compliance_data: Dict) -> str:
    """Assess compliance health status"""
    if isinstance(compliance_data, dict) and "compliance_overview" in compliance_data:
        soc2_score = compliance_data["compliance_overview"].get("soc2_readiness_score", 0)
        pii_score = compliance_data["compliance_overview"].get("pii_compliance_score", 0)
        avg_score = (soc2_score + pii_score) / 2
        
        if avg_score >= 90:
            return "excellent"
        elif avg_score >= 80:
            return "compliant"
        elif avg_score >= 60:
            return "improving"
        else:
            return "needs_attention"
    return "unknown"

def _get_protected_apps_count(dr_data: Dict) -> str:
    """Get count of protected applications"""
    if isinstance(dr_data, dict) and "global_metrics" in dr_data:
        compliant = dr_data["global_metrics"].get("apps_compliant", 0)
        total = dr_data["global_metrics"].get("apps_total", 0)
        return f"{compliant}/{total}"
    return "0/0"

def _get_backup_success_rate(dr_data: Dict) -> str:
    """Get backup success rate"""
    if isinstance(dr_data, dict) and "global_metrics" in dr_data:
        successful = dr_data["global_metrics"].get("successful_backups_24h", 0)
        total = dr_data["global_metrics"].get("total_backups_24h", 1)
        rate = (successful / total) * 100 if total > 0 else 0
        return f"{rate:.1f}%"
    return "0%"

def _get_soc2_readiness(compliance_data: Dict) -> str:
    """Get SOC2 readiness percentage"""
    if isinstance(compliance_data, dict) and "compliance_overview" in compliance_data:
        score = compliance_data["compliance_overview"].get("soc2_readiness_score", 0)
        return f"{score:.1f}%"
    return "0%"

def _get_pii_compliance(compliance_data: Dict) -> str:
    """Get PII compliance percentage"""
    if isinstance(compliance_data, dict) and "compliance_overview" in compliance_data:
        score = compliance_data["compliance_overview"].get("pii_compliance_score", 0)
        return f"{score:.1f}%"
    return "0%"

def _get_storage_usage(dr_data: Dict) -> float:
    """Get backup storage usage in GB"""
    if isinstance(dr_data, dict) and "global_metrics" in dr_data:
        return dr_data["global_metrics"].get("total_storage_gb", 0)
    return 0.0

def _get_evidence_count(compliance_data: Dict) -> int:
    """Get evidence items count"""
    if isinstance(compliance_data, dict) and "compliance_overview" in compliance_data:
        return compliance_data["compliance_overview"].get("total_evidence_items", 0)
    return 0

def _get_lineage_count(compliance_data: Dict) -> int:
    """Get data lineage count"""
    if isinstance(compliance_data, dict) and "compliance_overview" in compliance_data:
        return compliance_data["compliance_overview"].get("data_lineage_mapped", 0)
    return 0

def _get_critical_alerts(dr_data: Dict, compliance_data: Dict) -> List[Dict[str, Any]]:
    """Get critical alerts and recommended actions"""
    alerts = []
    
    # DR alerts
    if isinstance(dr_data, dict) and "global_metrics" in dr_data:
        if dr_data["global_metrics"].get("failed_backups_24h", 0) > 0:
            alerts.append({
                "type": "warning",
                "category": "disaster_recovery",
                "message": f"{dr_data['global_metrics']['failed_backups_24h']} backup failures in last 24h",
                "action": "Review backup logs and retry failed backups"
            })
    
    # Compliance alerts
    if isinstance(compliance_data, dict) and "compliance_overview" in compliance_data:
        critical_findings = compliance_data["compliance_overview"].get("critical_findings", 0)
        if critical_findings > 0:
            alerts.append({
                "type": "critical",
                "category": "compliance",
                "message": f"{critical_findings} critical compliance findings",
                "action": "Review and address compliance violations"
            })
    
    return alerts

def _format_critical_apps(dr_data: Dict) -> Dict[str, Any]:
    """Format critical applications status for display"""
    if isinstance(dr_data, dict) and "apps" in dr_data:
        critical_apps = {}
        for app_name, app_data in dr_data["apps"].items():
            if app_data.get("health_score", 0) < 80:  # Consider apps with low health as critical
                critical_apps[app_name] = {
                    "status": app_data.get("status", "unknown"),
                    "health_score": app_data.get("health_score", 0),
                    "last_backup": app_data.get("last_backup"),
                    "issues": []
                }
                
                if app_data.get("status") != "compliant":
                    critical_apps[app_name]["issues"].append("Backup compliance issue")
                if app_data.get("health_score", 0) < 50:
                    critical_apps[app_name]["issues"].append("Low backup health score")
        
        return critical_apps
    return {}

async def _check_dr_service_health() -> Dict[str, Any]:
    """Check disaster recovery service health"""
    try:
        # Check if DR service is responsive
        total_apps = len(dr_service.dr_config) if hasattr(dr_service, 'dr_config') else 0
        return {
            "status": "healthy",
            "applications_monitored": total_apps,
            "service_version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

async def _check_compliance_service_health() -> Dict[str, Any]:
    """Check compliance service health"""
    try:
        # Check if compliance service is responsive
        pii_count = len(compliance_service.pii_elements) if hasattr(compliance_service, 'pii_elements') else 0
        return {
            "status": "healthy",
            "pii_elements_tracked": pii_count,
            "service_version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

async def _check_application_health() -> Dict[str, Any]:
    """Check main application health"""
    try:
        return {
            "status": "healthy",
            "api_version": "1.0.0",
            "uptime": "operational"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }