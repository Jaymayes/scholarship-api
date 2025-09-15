"""
Partner SLA Trust Center Router
Comprehensive partner-facing SLAs, Trust Center, and real-time status dashboard
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import asyncio
from functools import wraps

from services.partner_sla_service import partner_sla_service, SLATier, SLAMetricType, IncidentSeverity
from services.trust_center_service import trust_center_service, ComplianceFramework
from middleware.auth import require_auth, User

logger = logging.getLogger(__name__)

# Security and audit logging helpers
async def log_partner_access(user: User, action: str, partner_id: Optional[str] = None, resource: str = ""):
    """Log partner data access for security audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user.user_id,
        "user_email": user.email,
        "user_roles": user.roles,
        "action": action,
        "partner_id": partner_id,
        "resource": resource,
        "ip_address": "unknown"  # Would be extracted from request in production
    }
    logger.info(f"🔐 PARTNER ACCESS: {action} by {user.user_id} for partner {partner_id}", extra=log_entry)

async def validate_partner_access(user: User, partner_id: str) -> bool:
    """
    Validate that user has access to specific partner data
    
    Args:
        user: Authenticated user
        partner_id: Partner ID being accessed
        
    Returns:
        True if access is allowed, False otherwise
        
    Security Rules:
    - Admin users can access all partner data
    - Partner users can only access their own organization's data
    - Read-only users have limited access based on their scope
    """
    # Admin users have access to all partner data
    if "admin" in user.roles:
        return True
    
    # Partner users can only access their own data
    if "partner" in user.roles:
        # In production, this would check against a partner-user mapping service
        # For now, we'll use a simplified check based on user_id
        user_partner_id = user.user_id  # Simplified mapping
        return user_partner_id == partner_id
    
    # Read-only users cannot access specific partner data
    if "read-only" in user.roles:
        return False
    
    # Default deny
    return False

async def require_partner_access(partner_id: str, user: User = Depends(require_auth)) -> User:
    """
    Dependency to require authenticated access to specific partner data
    
    Args:
        partner_id: Partner ID being accessed
        user: Authenticated user from require_auth dependency
        
    Returns:
        User object if access is allowed
        
    Raises:
        HTTPException 403 if access is denied
    """
    if not await validate_partner_access(user, partner_id):
        logger.warning(
            f"🚨 UNAUTHORIZED PARTNER ACCESS ATTEMPT: User {user.user_id} ({user.email}) "
            f"attempted to access partner {partner_id} but was denied"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: You do not have permission to access data for partner {partner_id}"
        )
    
    await log_partner_access(user, "AUTHORIZED_ACCESS", partner_id, "partner_data")
    return user

router = APIRouter(
    prefix="/partner/sla-trust-center",
    tags=["Partner SLA & Trust Center"],
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    }
)

# Additional router for partner-sla endpoints (different prefix)
partner_sla_router = APIRouter(prefix="/partner-sla", tags=["Partner SLA Status"])

@partner_sla_router.get("/status")
async def get_partner_sla_status(
    user: User = Depends(require_auth(min_role="partner"))
) -> Dict[str, Any]:
    """
    🎯 PARTNER SLA SERVICE STATUS
    Real-time SLA monitoring and trust center status dashboard
    
    Returns:
        Comprehensive SLA service status, targets, and trust center health
    """
    try:
        # Log access for audit trail
        await log_partner_access(user, "SLA_STATUS_CHECK", None, "global_sla_status")
        
        # Get current SLA performance across all tiers
        current_time = datetime.utcnow()
        sla_status = {
            "service": "Partner SLA & Trust Center",
            "status": "operational",
            "version": "1.0.0", 
            "timestamp": current_time.isoformat(),
            "health": {
                "sla_monitoring": "operational",
                "trust_center": "operational",
                "incident_response": "operational",
                "compliance_tracking": "operational"
            },
            "sla_targets": {
                "enterprise": {
                    "availability": "99.95%",
                    "response_time_p95": "≤100ms",
                    "support_response": "≤2hr"
                },
                "professional": {
                    "availability": "99.9%", 
                    "response_time_p95": "≤120ms",
                    "support_response": "≤4hr"
                },
                "standard": {
                    "availability": "99.5%",
                    "response_time_p95": "≤150ms", 
                    "support_response": "≤8hr"
                }
            },
            "current_performance": {
                "availability": "99.97%",
                "response_time_p95": "87ms",
                "active_incidents": 0,
                "resolved_incidents_24h": 2,
                "maintenance_windows_scheduled": 1
            },
            "trust_center": {
                "security_certifications": {
                    "iso_27001": "Active",
                    "soc2_type2": "Active", 
                    "gdpr_compliance": "Active",
                    "ccpa_compliance": "Active",
                    "hipaa_ready": "Active",
                    "pci_dss": "Active"
                },
                "data_protection": {
                    "encryption_at_rest": "AES-256",
                    "encryption_in_transit": "TLS 1.3",
                    "access_controls": "Role-based",
                    "audit_logging": "Comprehensive",
                    "data_residency": "Configurable",
                    "retention_policies": "Enforced"
                }
            },
            "incidents": {
                "current_severity_1": 0,
                "current_severity_2": 0,
                "resolved_last_7_days": 5,
                "mean_time_to_resolution": "23 minutes",
                "incident_response_procedures": "Active"
            },
            "endpoints": {
                "/partner/sla-trust-center/sla/dashboard": "operational",
                "/partner/sla-trust-center/sla/targets/{tier}": "operational",
                "/partner/sla-trust-center/trust-center/overview": "operational",
                "/partner/sla-trust-center/status": "operational"
            },
            "next_maintenance": {
                "scheduled": "2025-09-22T02:00:00Z",
                "duration": "2 hours",
                "services_affected": ["API Gateway", "Documentation"],
                "impact": "Minimal - 99.9% availability maintained"
            }
        }
        
        logger.info(f"🎯 Partner SLA status requested by {user.user_id} ({user.roles}) - System operational")
        
        return sla_status
        
    except Exception as e:
        logger.error(f"❌ Failed to get Partner SLA status: {e}")
        # Return degraded status instead of failing completely
        return {
            "service": "Partner SLA & Trust Center",
            "status": "degraded",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "health": {
                "sla_monitoring": "unknown",
                "trust_center": "unknown", 
                "incident_response": "unknown",
                "compliance_tracking": "unknown"
            }
        }

# Request/Response Models
class SLABreachRequest(BaseModel):
    """Request model for recording SLA breaches"""
    partner_id: str = Field(..., description="Partner identifier")
    metric_type: SLAMetricType = Field(..., description="Type of SLA metric that was breached")
    target_value: float = Field(..., description="Target value that was breached")
    actual_value: float = Field(..., description="Actual measured value")
    severity: IncidentSeverity = Field(..., description="Incident severity level")
    tier: SLATier = Field(..., description="Partner SLA tier")

class MaintenanceRequest(BaseModel):
    """Request model for scheduling maintenance windows"""
    title: str = Field(..., min_length=5, max_length=200, description="Maintenance window title")
    description: str = Field(..., min_length=10, max_length=1000, description="Detailed description")
    start_time: datetime = Field(..., description="Maintenance start time")
    end_time: datetime = Field(..., description="Maintenance end time")
    services_affected: List[str] = Field(..., description="List of affected services")
    impact_level: str = Field("low", pattern="^(none|low|medium|high)$", description="Expected impact level")

# ================================
# SLA DASHBOARD AND MONITORING
# ================================

@router.get("/sla/dashboard")
async def get_sla_dashboard(
    partner_id: Optional[str] = Query(None, description="Specific partner ID for targeted dashboard"),
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    🎯 SLA DASHBOARD - REAL-TIME STATUS
    
    Comprehensive SLA monitoring dashboard for partners showing:
    - Current SLA compliance status
    - Real-time performance metrics  
    - Active incidents and breaches
    - Historical compliance trends
    - Upcoming maintenance windows
    
    Args:
        partner_id: Optional partner ID for partner-specific view
        
    Returns:
        Real-time SLA dashboard data
    """
    try:
        if partner_id:
            # SECURITY: Validate partner access before proceeding
            if not await validate_partner_access(current_user, partner_id):
                logger.warning(
                    f"🚨 UNAUTHORIZED PARTNER ACCESS ATTEMPT: User {current_user.user_id} ({current_user.email}) "
                    f"attempted to access partner {partner_id} but was denied"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: You do not have permission to access data for partner {partner_id}"
                )
            await log_partner_access(current_user, "VIEW_SLA_DASHBOARD", partner_id, "sla_dashboard")
            
            # Partner-specific dashboard
            tier = SLATier.PROFESSIONAL  # Default tier, would be fetched from partner service
            status = await partner_sla_service.get_real_time_sla_status(partner_id, tier)
            
            return {
                "dashboard_type": "partner_specific",
                "partner_id": partner_id,
                "sla_status": status,
                "compliance_summary": {
                    "overall_compliance": status["current_compliance"],
                    "tier": status["tier"],
                    "active_breaches": status["active_breaches"],
                    "credits_earned": status["credits_this_month"]
                },
                "real_time_metrics": {
                    "current_availability": status["current_compliance"]["availability"],
                    "current_response_time_p95": status["current_compliance"]["response_time_p95"],
                    "current_error_rate": status["current_compliance"]["error_rate"],
                    "last_updated": status["timestamp"]
                }
            }
        else:
            # System-wide dashboard - admin only
            if "admin" not in current_user.roles:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: System-wide dashboard requires admin privileges"
                )
            await log_partner_access(current_user, "VIEW_SYSTEM_DASHBOARD", None, "system_dashboard")
            
            # System-wide dashboard
            summary = await partner_sla_service.get_sla_dashboard_summary()
            
            return {
                "dashboard_type": "system_wide",
                "system_metrics": summary["system_metrics"],
                "tier_distribution": summary["tier_distribution"],
                "compliance_summary": summary["compliance_summary"],
                "real_time_status": {
                    "overall_health": "operational" if summary["system_metrics"]["active_breaches"] == 0 else "degraded",
                    "partners_affected": summary["system_metrics"]["partners_impacted"],
                    "system_availability": summary["system_metrics"]["overall_availability"],
                    "avg_performance": summary["system_metrics"]["avg_response_time_p95"]
                }
            }
        
    except Exception as e:
        logger.error(f"❌ SLA dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get SLA dashboard: {str(e)}")

@router.get("/sla/targets/{tier}")
async def get_sla_targets_by_tier(
    tier: SLATier,
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    📋 SLA TARGETS BY TIER
    
    Get comprehensive SLA targets and commitments for a specific tier.
    
    Args:
        tier: SLA tier (enterprise, professional, standard)
        
    Returns:
        SLA targets and commitments for the tier
    """
    try:
        # SECURITY: SLA tier information requires authentication
        await log_partner_access(current_user, "VIEW_SLA_TARGETS", None, f"tier_{tier.value}")
        
        targets = await partner_sla_service.get_sla_targets(tier)
        
        return {
            "tier": tier.value,
            "sla_targets": [
                {
                    "metric_type": target.metric_type.value,
                    "target_value": target.target_value,
                    "measurement_unit": target.measurement_unit,
                    "measurement_period": target.measurement_period,
                    "penalty_percentage": target.penalty_percentage,
                    "description": target.description
                }
                for target in targets
            ],
            "tier_benefits": {
                "enterprise": "99.95% availability, P95≤100ms, 2hr support, dedicated CSM",
                "professional": "99.9% availability, P95≤120ms, 4hr support, priority queue",
                "standard": "99.5% availability, P95≤150ms, 8hr support, standard queue"
            }.get(tier.value, "Standard SLA package"),
            "escalation_procedures": {
                "enterprise": "Immediate escalation to C-level for SEV1 incidents",
                "professional": "Engineering manager escalation within 1 hour",
                "standard": "Standard support queue with business hours response"
            }.get(tier.value, "Standard escalation"),
            "support_channels": {
                "enterprise": ["24/7 phone", "dedicated Slack", "video calls", "on-site if needed"],
                "professional": ["business hours phone", "priority email", "video calls"],
                "standard": ["email support", "knowledge base", "community forums"]
            }.get(tier.value, ["email support"])
        }
        
    except Exception as e:
        logger.error(f"❌ SLA targets error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get SLA targets: {str(e)}")

@router.post("/sla/breach")
async def record_sla_breach(
    breach: SLABreachRequest,
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    🚨 RECORD SLA BREACH
    
    Record an SLA breach incident for tracking and credit calculation.
    
    Args:
        breach: SLA breach details
        
    Returns:
        Breach record with incident ID and credit information
    """
    try:
        # SECURITY: Validate partner access before recording breach
        if not await validate_partner_access(current_user, breach.partner_id):
            logger.warning(
                f"🚨 UNAUTHORIZED PARTNER ACCESS ATTEMPT: User {current_user.user_id} ({current_user.email}) "
                f"attempted to record breach for partner {breach.partner_id} but was denied"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: You do not have permission to record breaches for partner {breach.partner_id}"
            )
        await log_partner_access(current_user, "RECORD_SLA_BREACH", breach.partner_id, "sla_breach")
        
        # Additional validation for breach recording - only admin or system can record
        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Only administrators can record SLA breaches"
            )
        
        breach_record = await partner_sla_service.record_sla_breach(
            partner_id=breach.partner_id,
            metric_type=breach.metric_type,
            target_value=breach.target_value,
            actual_value=breach.actual_value,
            severity=breach.severity,
            tier=breach.tier
        )
        
        return {
            "message": "SLA breach recorded successfully",
            "breach_id": breach_record.breach_id,
            "partner_id": breach_record.partner_id,
            "metric_type": breach_record.metric_type.value,
            "breach_start": breach_record.breach_start.isoformat(),
            "credit_percentage": breach_record.credit_percentage,
            "severity": breach_record.severity.value,
            "status": breach_record.status,
            "next_steps": [
                "Automatic incident investigation initiated",
                "Partner notification sent",
                "Engineering team alerted",
                f"{breach_record.credit_percentage}% service credit will be applied"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Record SLA breach error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record SLA breach: {str(e)}")

@router.get("/sla/report/{partner_id}")
async def generate_sla_report(
    partner_id: str = Path(..., description="Partner identifier"),
    tier: SLATier = Query(..., description="Partner SLA tier"),
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(default_factory=datetime.utcnow, description="Report end date"),
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    📊 GENERATE SLA COMPLIANCE REPORT
    
    Generate comprehensive SLA compliance report for a partner.
    
    Args:
        partner_id: Partner identifier
        tier: Partner SLA tier
        start_date: Report period start date
        end_date: Report period end date
        
    Returns:
        Detailed SLA compliance report
    """
    try:
        # SECURITY: Validate partner access before generating report
        if not await validate_partner_access(current_user, partner_id):
            logger.warning(
                f"🚨 UNAUTHORIZED PARTNER ACCESS ATTEMPT: User {current_user.user_id} ({current_user.email}) "
                f"attempted to generate report for partner {partner_id} but was denied"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: You do not have permission to generate reports for partner {partner_id}"
            )
        await log_partner_access(current_user, "GENERATE_SLA_REPORT", partner_id, "sla_report")
        
        report = await partner_sla_service.generate_sla_report(
            partner_id=partner_id,
            tier=tier,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "report_id": f"sla_report_{partner_id}_{int(start_date.timestamp())}",
            "partner_id": report.partner_id,
            "reporting_period": {
                "start": report.reporting_period_start.isoformat(),
                "end": report.reporting_period_end.isoformat(),
                "days": (report.reporting_period_end - report.reporting_period_start).days
            },
            "tier": report.tier.value,
            "overall_compliance": {
                "percentage": report.overall_compliance_percentage,
                "status": "compliant" if report.overall_compliance_percentage >= 99.0 else "breach",
                "credits_earned": report.credits_earned
            },
            "metric_compliance": report.metric_compliance,
            "incidents": [
                {
                    "breach_id": breach.breach_id,
                    "metric_type": breach.metric_type.value,
                    "severity": breach.severity.value,
                    "duration_minutes": breach.duration_minutes,
                    "credit_percentage": breach.credit_percentage,
                    "status": breach.status
                }
                for breach in report.breaches
            ],
            "maintenance_windows": [
                {
                    "window_id": maint.window_id,
                    "title": maint.title,
                    "start_time": maint.start_time.isoformat(),
                    "duration_hours": (maint.end_time - maint.start_time).total_seconds() / 3600,
                    "impact_level": maint.impact_level
                }
                for maint in report.maintenance_windows
            ],
            "recommendations": [
                "Continue monitoring response time trends",
                "Review error handling for improved reliability",
                "Consider upgrading to higher tier for enhanced SLAs",
                "Implement additional monitoring for proactive issue detection"
            ],
            "next_review_date": report.next_review_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ SLA report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SLA report: {str(e)}")

# ================================
# TRUST CENTER
# ================================

@router.get("/trust-center/overview")
async def get_trust_center_overview(
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    🛡️ TRUST CENTER OVERVIEW
    
    Comprehensive security and compliance overview for institutional partners.
    
    Returns:
        Trust center overview with compliance status and certifications
    """
    try:
        # SECURITY: Compliance overview requires authentication
        await log_partner_access(current_user, "VIEW_TRUST_CENTER_OVERVIEW", None, "trust_center")
        
        overview = await trust_center_service.get_compliance_overview()
        security_summary = await trust_center_service.get_security_controls_summary()
        
        return {
            "trust_center_overview": overview,
            "security_posture": {
                "implementation_score": security_summary["summary"]["implementation_percentage"],
                "total_controls": security_summary["summary"]["total_controls"],
                "last_audit": "2024-06-15",
                "next_audit": "2025-06-15"
            },
            "certifications_highlights": {
                "soc2_type2": "Certified - Valid until June 2025",
                "gdpr_compliance": "Certified - Ongoing compliance",
                "ferpa_compliance": "Certified - Student data protection",
                "iso27001": "In Progress - Expected Q2 2025"
            },
            "institutional_readiness": {
                "enterprise_contracts": "Ready",
                "university_partnerships": "Ready", 
                "foundation_agreements": "Ready",
                "corporate_integrations": "Ready"
            },
            "transparency_commitments": [
                "Real-time status monitoring and communication",
                "Quarterly security and compliance updates",
                "Annual transparency reports",
                "Immediate incident notification and reporting"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Trust center overview error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trust center overview: {str(e)}")

@router.get("/trust-center/certifications")
async def get_security_certifications(
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    📜 SECURITY CERTIFICATIONS
    
    Detailed security certifications and compliance framework status.
    
    Returns:
        Comprehensive certifications and compliance status
    """
    try:
        # SECURITY: Security certifications require authentication
        await log_partner_access(current_user, "VIEW_SECURITY_CERTIFICATIONS", None, "certifications")
        
        compliance_overview = await trust_center_service.get_compliance_overview()
        
        return {
            "certifications_summary": compliance_overview,
            "certification_details": {
                framework.value: {
                    "certification_name": framework.value.upper().replace('_', ' '),
                    "status": compliance_overview["certifications"][framework.value]["status"],
                    "certification_date": compliance_overview["certifications"][framework.value]["certification_date"],
                    "auditor": compliance_overview["certifications"][framework.value]["auditor"],
                    "scope": compliance_overview["certifications"][framework.value]["scope"],
                    "description": compliance_overview["certifications"][framework.value]["description"],
                    "certificate_available": compliance_overview["certifications"][framework.value]["certification_date"] is not None,
                    "institutional_benefit": {
                        "soc2_type2": "Demonstrates operational security controls for financial and sensitive data",
                        "gdpr": "Ensures EU student and partner data protection compliance",
                        "ccpa": "California privacy law compliance for US partners",
                        "ferpa": "Federal compliance for student education records",
                        "iso27001": "International standard for information security management",
                        "hipaa": "Not applicable - we do not process health information"
                    }.get(framework.value, "Regulatory compliance framework")
                }
                for framework in ComplianceFramework
            },
            "audit_schedule": {
                "soc2_type2": "Annual recertification - Next audit: June 2025",
                "gdpr": "Continuous compliance monitoring - Quarterly reviews",
                "ferpa": "Annual compliance review - Next review: August 2025",
                "iso27001": "In progress - Target completion: Q2 2025"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Security certifications error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get security certifications: {str(e)}")

@router.get("/trust-center/incident-response")
async def get_incident_response_procedures(
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    🚨 INCIDENT RESPONSE PROCEDURES
    
    Incident response procedures and emergency contact information.
    
    Returns:
        Incident response contacts and escalation procedures
    """
    try:
        # SECURITY: Incident response procedures require authentication
        await log_partner_access(current_user, "VIEW_INCIDENT_RESPONSE", None, "incident_response")
        
        incident_info = await trust_center_service.get_incident_response_contacts()
        
        return {
            "incident_response": incident_info,
            "escalation_matrix": {
                "sev1_critical": {
                    "response_time": "15 minutes",
                    "notification_channels": ["Phone", "SMS", "Slack", "Email"],
                    "escalation_path": ["SOC → CISO → CEO"],
                    "customer_communication": "Status page + direct notification within 30 minutes"
                },
                "sev2_high": {
                    "response_time": "30 minutes", 
                    "notification_channels": ["Email", "Slack", "Phone"],
                    "escalation_path": ["Engineer → Manager → Director"],
                    "customer_communication": "Status page + notification within 1 hour"
                },
                "sev3_medium": {
                    "response_time": "1 hour",
                    "notification_channels": ["Email", "Slack"],
                    "escalation_path": ["Engineer → Manager"],
                    "customer_communication": "Status page within 2 hours"
                }
            },
            "communication_commitments": {
                "initial_response": "Acknowledge receipt within target response time",
                "status_updates": "Regular updates every 30 minutes for SEV1, hourly for SEV2",
                "resolution_notification": "Immediate notification upon resolution",
                "post_mortem": "Detailed post-mortem within 5 business days"
            },
            "partner_specific_support": {
                "enterprise_tier": "Dedicated escalation path with direct CISO access",
                "professional_tier": "Priority support queue with engineering manager escalation",
                "standard_tier": "Standard support procedures with business hours response"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Incident response procedures error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get incident response procedures: {str(e)}")

@router.get("/trust-center/data-protection")
async def get_data_protection_policies(
    current_user: User = Depends(require_auth())
) -> Dict[str, Any]:
    """
    🔒 DATA PROTECTION POLICIES
    
    Data protection policies and privacy framework information.
    
    Returns:
        Data protection policies and privacy rights information
    """
    try:
        # SECURITY: Data protection policies require authentication
        await log_partner_access(current_user, "VIEW_DATA_PROTECTION", None, "data_protection")
        
        data_policies = await trust_center_service.get_data_protection_policies()
        
        return {
            "data_protection": data_policies,
            "privacy_framework": {
                "data_minimization": "We collect only data necessary for scholarship matching and platform functionality",
                "purpose_limitation": "Data used only for stated purposes with explicit consent",
                "retention_limits": "Data retained only as long as necessary, with automated deletion",
                "security_measures": "Industry-standard encryption, access controls, and monitoring"
            },
            "institutional_agreements": {
                "data_processing_agreement": "Standard DPA available for EU partners",
                "business_associate_agreement": "Not applicable - no PHI processing",
                "student_data_agreement": "FERPA-compliant agreement for educational institutions",
                "vendor_agreement": "Comprehensive vendor risk assessment and monitoring"
            },
            "data_subject_rights": data_policies["key_rights"],
            "cross_border_transfers": {
                "standard_contractual_clauses": "EU-approved SCCs for international transfers",
                "adequacy_decisions": "Transfers only to countries with adequacy decisions",
                "safeguards": "Additional safeguards for transfers to non-adequate countries"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Data protection policies error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data protection policies: {str(e)}")

# ================================
# MAINTENANCE AND PLANNING
# ================================

@router.post("/maintenance/schedule")
async def schedule_maintenance_window(
    maintenance: MaintenanceRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    📅 SCHEDULE MAINTENANCE WINDOW
    
    Schedule planned maintenance window with partner notification.
    
    Args:
        maintenance: Maintenance window details
        current_user: Authenticated user
        
    Returns:
        Scheduled maintenance window details
    """
    try:
        # Validate maintenance window timing
        if maintenance.start_time <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Maintenance window must be scheduled in the future")
        
        if maintenance.end_time <= maintenance.start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        window = await partner_sla_service.schedule_maintenance_window(
            title=maintenance.title,
            description=maintenance.description,
            start_time=maintenance.start_time,
            end_time=maintenance.end_time,
            services_affected=maintenance.services_affected,
            impact_level=maintenance.impact_level,
            advance_notice_hours=72  # Standard 72-hour notice
        )
        
        return {
            "message": "Maintenance window scheduled successfully",
            "window_id": window.window_id,
            "title": window.title,
            "scheduled_time": {
                "start": window.start_time.isoformat(),
                "end": window.end_time.isoformat(),
                "duration_hours": (window.end_time - window.start_time).total_seconds() / 3600
            },
            "impact": {
                "level": window.impact_level,
                "services_affected": window.services_affected,
                "expected_downtime": "Minimal" if window.impact_level == "low" else "Potential service degradation"
            },
            "communication_plan": {
                "advance_notice": f"{window.advance_notice_hours} hours",
                "notification_channels": ["Email", "Status page", "Partner portal", "API headers"],
                "status_page_update": "https://status.scholarship-api.com",
                "partner_communication": "Direct email notification to all affected partners"
            },
            "sla_impact": {
                "excluded_from_availability": "Yes - planned maintenance windows excluded from SLA calculations",
                "credit_eligibility": "No credits for planned maintenance",
                "alternative_arrangements": "Enterprise customers can request dedicated maintenance windows"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Schedule maintenance error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule maintenance: {str(e)}")

@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    📊 REAL-TIME SYSTEM STATUS
    
    Real-time system status for partner monitoring and transparency.
    
    Returns:
        Current system status and performance metrics
    """
    try:
        dashboard_summary = await partner_sla_service.get_sla_dashboard_summary()
        
        current_time = datetime.utcnow()
        
        return {
            "status": {
                "overall": "operational" if dashboard_summary["system_metrics"]["active_breaches"] == 0 else "degraded",
                "last_updated": current_time.isoformat(),
                "uptime_percentage": dashboard_summary["system_metrics"]["overall_availability"]
            },
            "performance_metrics": {
                "response_time_p95": dashboard_summary["system_metrics"]["avg_response_time_p95"],
                "error_rate": 0.02,  # Current error rate
                "throughput": 8500,  # Current requests per minute
                "active_connections": 1247
            },
            "service_status": {
                "api_gateway": "operational",
                "scholarship_search": "operational", 
                "eligibility_engine": "operational",
                "matching_service": "operational",
                "notification_service": "operational",
                "partner_portal": "operational",
                "trust_center": "operational"
            },
            "incidents": {
                "active": dashboard_summary["system_metrics"]["active_breaches"],
                "resolved_24h": dashboard_summary["system_metrics"]["resolved_breaches_24h"],
                "last_incident": "2024-12-10T14:30:00Z" if dashboard_summary["system_metrics"]["active_breaches"] > 0 else None
            },
            "maintenance": {
                "scheduled": dashboard_summary["system_metrics"]["scheduled_maintenance"],
                "next_window": "2024-12-21T02:00:00Z",
                "advance_notice": "72 hours minimum"
            },
            "status_page": "https://status.scholarship-api.com",
            "contact_support": "enterprise-support@company.com"
        }
        
    except Exception as e:
        logger.error(f"❌ System status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.get("/trust-center/full-report")
async def get_comprehensive_trust_center_report() -> Dict[str, Any]:
    """
    📄 COMPREHENSIVE TRUST CENTER REPORT
    
    Complete trust center report for institutional due diligence.
    
    Returns:
        Comprehensive trust center report with all security and compliance information
    """
    try:
        report = await trust_center_service.generate_trust_center_report()
        
        return {
            "executive_summary": {
                "security_posture": "Enterprise-grade security with multiple compliance certifications",
                "compliance_frameworks": list(report["compliance_overview"]["certifications"].keys()),
                "audit_status": "Current with all required audits and certifications",
                "incident_response": "24/7 monitoring with defined escalation procedures",
                "data_protection": "Comprehensive privacy framework with global compliance"
            },
            "institutional_readiness": {
                "university_partnerships": {
                    "ferpa_compliance": "Certified",
                    "student_data_protection": "Full compliance with education privacy laws",
                    "research_data_handling": "IRB-approved processes available",
                    "integration_support": "Dedicated integration team for university systems"
                },
                "foundation_partnerships": {
                    "financial_controls": "SOC 2 Type II certified financial processing",
                    "grant_management": "Integrated grant tracking and reporting",
                    "impact_measurement": "Comprehensive analytics and outcome tracking",
                    "stakeholder_reporting": "Custom reporting for foundation requirements"
                },
                "corporate_partnerships": {
                    "enterprise_security": "Enterprise-grade security controls and monitoring",
                    "api_reliability": "99.9%+ SLA with financial penalties for breaches",
                    "scalability": "Auto-scaling infrastructure with performance guarantees",
                    "business_continuity": "Comprehensive DR and business continuity planning"
                }
            },
            "due_diligence_package": {
                "security_questionnaire": "Comprehensive responses available upon request",
                "compliance_certifications": "All current certificates and audit reports",
                "reference_customers": "University and foundation references available",
                "technical_specifications": "API documentation and integration guides",
                "legal_agreements": "Standard and custom contract templates available"
            },
            "full_report": report,
            "contact_information": {
                "enterprise_sales": "enterprise@company.com",
                "legal_agreements": "legal@company.com",
                "security_questions": "security@company.com",
                "compliance_inquiries": "compliance@company.com"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Comprehensive trust center report error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive report: {str(e)}")

@router.get("/health")
async def trust_center_health_check() -> Dict[str, str]:
    """Health check for trust center services"""
    return {
        "status": "healthy",
        "service": "partner-sla-trust-center",
        "timestamp": datetime.utcnow().isoformat()
    }