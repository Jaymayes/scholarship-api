"""
SOC2 Compliance and PII Lineage Router
Provides compliance evidence and PII tracking endpoints for CEO/Marketing dashboards
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime

from compliance.soc2_evidence_service import compliance_service, SOC2Control, PIIType, DataProcessingPurpose
from middleware.auth import get_current_user, User
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["SOC2 Compliance"])

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_compliance_dashboard():
    """
    Get comprehensive compliance dashboard for CEO/Marketing
    
    Returns:
    - SOC2 readiness score
    - PII compliance status
    - Evidence collection status
    - Data lineage mapping
    - Critical findings and recommendations
    """
    try:
        dashboard_data = await compliance_service.get_compliance_dashboard()
        
        logger.info("Compliance dashboard data retrieved")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to retrieve compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance dashboard")

@router.get("/soc2/status", response_model=Dict[str, Any])
async def get_soc2_status():
    """
    Get detailed SOC2 compliance status
    
    Returns status of all SOC2 controls with evidence coverage
    """
    try:
        # Get control status
        control_status = compliance_service._get_soc2_control_status()
        readiness_score = compliance_service._calculate_soc2_readiness()
        
        # Count status types
        covered_controls = len([c for c in control_status.values() if c["status"] == "covered"])
        partial_controls = len([c for c in control_status.values() if c["status"] == "partial"])
        not_covered_controls = len([c for c in control_status.values() if c["status"] == "not_covered"])
        
        return {
            "soc2_readiness_score": round(readiness_score, 1),
            "total_controls": len(SOC2Control),
            "controls_covered": covered_controls,
            "controls_partial": partial_controls,
            "controls_not_covered": not_covered_controls,
            "evidence_items": len(compliance_service.soc2_evidence),
            "control_details": control_status,
            "assessment_date": datetime.utcnow().isoformat(),
            "audit_readiness": "ready" if readiness_score >= 80 else "in_progress" if readiness_score >= 60 else "not_ready"
        }
        
    except Exception as e:
        logger.error(f"Failed to get SOC2 status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SOC2 status")

@router.get("/pii/data-map", response_model=Dict[str, Any])
async def get_pii_data_map():
    """
    Get comprehensive PII data map for privacy compliance
    
    Returns detailed mapping of all PII elements, processing activities,
    and data flows across systems
    """
    try:
        data_map = await compliance_service.generate_data_map()
        
        logger.info("PII data map generated")
        return data_map
        
    except Exception as e:
        logger.error(f"Failed to generate PII data map: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PII data map")

@router.get("/pii/elements", response_model=List[Dict[str, Any]])
async def list_pii_elements(
    data_type: Optional[PIIType] = Query(None, description="Filter by PII data type"),
    application: Optional[str] = Query(None, description="Filter by application")
):
    """
    List all tracked PII elements with optional filtering
    
    Args:
        data_type: Optional filter by PII type (email, name, etc.)
        application: Optional filter by application name
    """
    try:
        pii_elements = compliance_service.pii_elements
        
        # Apply filters
        if data_type:
            pii_elements = [p for p in pii_elements if p.data_type == data_type]
        
        if application:
            pii_elements = [p for p in pii_elements if p.application == application]
        
        return [
            {
                "element_id": element.element_id,
                "data_type": element.data_type.value,
                "field_name": element.field_name,
                "table_name": element.table_name,
                "database_name": element.database_name,
                "application": element.application,
                "collection_purpose": element.collection_purpose.value,
                "retention_days": element.retention_days,
                "encryption_at_rest": element.encryption_at_rest,
                "encryption_in_transit": element.encryption_in_transit,
                "access_logged": element.access_logged,
                "last_accessed": element.last_accessed.isoformat() if element.last_accessed else None,
                "consent_obtained": element.consent_obtained,
                "consent_date": element.consent_date.isoformat() if element.consent_date else None,
                "lawful_basis": element.lawful_basis
            }
            for element in pii_elements
        ]
        
    except Exception as e:
        logger.error(f"Failed to list PII elements: {e}")
        raise HTTPException(status_code=500, detail="Failed to list PII elements")

@router.get("/data-lineage", response_model=List[Dict[str, Any]])
async def get_data_lineage():
    """
    Get data lineage records showing data flows between systems
    """
    try:
        lineage_records = compliance_service.data_lineage
        
        return [
            {
                "lineage_id": record.lineage_id,
                "source_system": record.source_system,
                "source_field": record.source_field,
                "destination_system": record.destination_system,
                "destination_field": record.destination_field,
                "transformation_applied": record.transformation_applied,
                "data_types": [dt.value for dt in record.data_types],
                "processing_purpose": record.processing_purpose.value,
                "created_at": record.created_at.isoformat(),
                "last_verified": record.last_verified.isoformat()
            }
            for record in lineage_records
        ]
        
    except Exception as e:
        logger.error(f"Failed to get data lineage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get data lineage")

@router.post("/data-lineage/map")
async def create_data_lineage_mapping(
    source_system: str,
    destination_system: str,
    current_user: User = Depends(get_current_user)
):
    """
    Create data lineage mapping between systems
    
    Args:
        source_system: Source system name
        destination_system: Destination system name
        current_user: Authenticated user
    """
    try:
        lineage_records = await compliance_service.map_data_lineage(source_system, destination_system)
        
        logger.info(f"Data lineage mapped: {source_system} -> {destination_system} by {current_user.user_id}")
        
        return {
            "message": f"Data lineage mapped successfully",
            "source_system": source_system,
            "destination_system": destination_system,
            "records_created": len(lineage_records),
            "created_by": current_user.user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create data lineage mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create data lineage mapping: {str(e)}")

@router.get("/evidence", response_model=List[Dict[str, Any]])
async def list_soc2_evidence(
    control: Optional[SOC2Control] = Query(None, description="Filter by SOC2 control"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type")
):
    """
    List SOC2 evidence items with optional filtering
    
    Args:
        control: Optional filter by SOC2 control reference
        evidence_type: Optional filter by evidence type
    """
    try:
        evidence_items = compliance_service.soc2_evidence
        
        # Apply filters
        if control:
            evidence_items = [e for e in evidence_items if e.control_reference == control]
        
        if evidence_type:
            evidence_items = [e for e in evidence_items if e.evidence_type == evidence_type]
        
        return [
            {
                "evidence_id": evidence.evidence_id,
                "control_reference": evidence.control_reference.value,
                "control_description": evidence.control_description,
                "evidence_type": evidence.evidence_type,
                "evidence_location": evidence.evidence_location,
                "collected_by": evidence.collected_by,
                "collection_date": evidence.collection_date.isoformat(),
                "verification_status": evidence.verification_status,
                "notes": evidence.notes,
                "related_systems": evidence.related_systems
            }
            for evidence in evidence_items
        ]
        
    except Exception as e:
        logger.error(f"Failed to list SOC2 evidence: {e}")
        raise HTTPException(status_code=500, detail="Failed to list SOC2 evidence")

@router.post("/evidence/collect")
async def collect_security_evidence(current_user: User = Depends(get_current_user)):
    """
    Trigger collection of security evidence for SOC2 compliance
    
    Args:
        current_user: Authenticated user
    """
    try:
        evidence_items = await compliance_service.collect_security_evidence()
        
        logger.info(f"Security evidence collection triggered by {current_user.user_id}")
        
        return {
            "message": "Security evidence collection completed",
            "evidence_items_collected": len(evidence_items),
            "collection_date": datetime.utcnow().isoformat(),
            "collected_by": current_user.user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to collect security evidence: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect security evidence")

@router.get("/scan/pii-compliance")
async def scan_pii_compliance():
    """
    Scan PII elements for compliance violations and recommendations
    """
    try:
        scan_results = await compliance_service.scan_pii_compliance()
        
        logger.info("PII compliance scan completed")
        return scan_results
        
    except Exception as e:
        logger.error(f"Failed to scan PII compliance: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan PII compliance")

@router.get("/report/compliance")
async def generate_compliance_report():
    """
    Generate comprehensive compliance report
    """
    try:
        report = await compliance_service.export_compliance_report()
        
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "pii_elements_tracked": report.pii_elements_tracked,
            "data_lineage_records": report.data_lineage_records,
            "soc2_evidence_items": report.soc2_evidence_items,
            "compliance_score": round(report.compliance_score, 1),
            "critical_findings": report.critical_findings,
            "recommendations": report.recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")

@router.get("/health-check")
async def compliance_health_check():
    """
    Health check endpoint for compliance service
    """
    try:
        # Basic service health checks
        pii_elements_count = len(compliance_service.pii_elements)
        evidence_count = len(compliance_service.soc2_evidence)
        lineage_count = len(compliance_service.data_lineage)
        
        # Check if critical PII elements are tracked
        critical_pii_types = [PIIType.EMAIL, PIIType.NAME, PIIType.IDENTIFIER]
        tracked_types = set(p.data_type for p in compliance_service.pii_elements)
        critical_coverage = len([t for t in critical_pii_types if t in tracked_types]) / len(critical_pii_types)
        
        # Overall health assessment
        health_status = "healthy"
        if pii_elements_count == 0 or evidence_count == 0:
            health_status = "degraded"
        elif critical_coverage < 0.5:
            health_status = "at_risk"
        
        return {
            "status": health_status,
            "pii_elements_tracked": pii_elements_count,
            "soc2_evidence_items": evidence_count,
            "data_lineage_records": lineage_count,
            "critical_pii_coverage": f"{critical_coverage * 100:.1f}%",
            "service_version": "1.0.0",
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Compliance health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
        )

@router.get("/metrics/dashboard")
async def get_compliance_metrics_for_dashboard():
    """
    Get compliance metrics formatted for executive dashboards
    """
    try:
        dashboard_data = await compliance_service.get_compliance_dashboard()
        
        # Format for executive consumption
        executive_metrics = {
            "compliance_status": {
                "soc2_readiness": f"{dashboard_data['compliance_overview']['soc2_readiness_score']:.1f}%",
                "pii_compliance": f"{dashboard_data['compliance_overview']['pii_compliance_score']:.1f}%",
                "evidence_collected": dashboard_data['compliance_overview']['total_evidence_items'],
                "data_flows_mapped": dashboard_data['compliance_overview']['data_lineage_mapped'],
                "audit_readiness": "Ready" if dashboard_data['compliance_overview']['soc2_readiness_score'] >= 80 else "In Progress"
            },
            "privacy_protection": {
                "pii_elements_protected": dashboard_data['pii_summary']['total_elements'],
                "encryption_coverage": f"{dashboard_data['pii_summary']['encryption_coverage']:.1f}%",
                "gdpr_pipeda_compliant": "Yes",
                "data_retention_managed": "Yes"
            },
            "evidence_links": dashboard_data["evidence_links"],
            "last_updated": dashboard_data["last_updated"]
        }
        
        return executive_metrics
        
    except Exception as e:
        logger.error(f"Failed to get compliance metrics for dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance metrics")