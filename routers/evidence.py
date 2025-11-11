"""
Evidence API Router - CEO DIRECTIVE 2025-11-12
Serves evidence files with SHA-256 checksums for executive review
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

# Evidence root directory
EVIDENCE_ROOT = Path(".")

# Evidence file registry (scholarship_api only)
EVIDENCE_FILES = {
    "data_retention_schedule": {
        "title": "Data Retention Schedule (DRAFT)",
        "purpose": "Cross-app data retention policies, DSAR workflows, and compliance mapping",
        "path": "DATA_RETENTION_SCHEDULE_2025-11-14.md",
        "category": "compliance"
    },
    "ceo_evidence_bundle": {
        "title": "CEO Evidence Bundle - Comprehensive",
        "purpose": "Full auditability evidence, DSAR plans, strategic alignment",
        "path": "evidence_root/scholarship_api/CEO_EVIDENCE_BUNDLE_NOV11.md",
        "category": "executive"
    },
    "ceo_executive_response": {
        "title": "CEO Executive Response",
        "purpose": "Response to CEO provisional GO-LIVE READY status",
        "path": "e2e/reports/scholarship_api/CEO_EXECUTIVE_RESPONSE_NOV11.md",
        "category": "executive"
    },
    "ceo_mission_check": {
        "title": "CEO Mission Check Response",
        "purpose": "$10M ARR alignment and cross-cutting compliance status",
        "path": "e2e/reports/scholarship_api/CEO_MISSION_CHECK_NOV11.md",
        "category": "executive"
    },
    "ceo_final_decision": {
        "title": "CEO Final Executive Decision Acknowledgment",
        "purpose": "CEO orders compliance and freeze discipline confirmation",
        "path": "e2e/reports/scholarship_api/CEO_FINAL_EXECUTIVE_DECISION_NOV11.md",
        "category": "executive"
    },
    "ceo_executive_index": {
        "title": "Central Executive Index",
        "purpose": "Quick navigation to all 8 apps and gate tracker",
        "path": "evidence_root/CEO_EXECUTIVE_INDEX.md",
        "category": "navigation"
    },
    "sentry_integration": {
        "title": "Sentry Integration Report",
        "purpose": "Error and performance monitoring implementation details",
        "path": "evidence_root/scholarship_api/SENTRY_INTEGRATION_REPORT.md",
        "category": "observability"
    },
    "production_deployment": {
        "title": "Production Deployment v2.7",
        "purpose": "Deployment configuration and production readiness",
        "path": "evidence_root/scholarship_api/PRODUCTION_DEPLOYMENT_v2_7.md",
        "category": "deployment"
    },
    "client_integration_guide": {
        "title": "Client Integration Guide",
        "purpose": "API-as-a-product documentation for developers",
        "path": "docs/CLIENT_INTEGRATION_GUIDE.md",
        "category": "api_docs"
    },
    "section_v_report": {
        "title": "Section V Status Report (CEO Required Format)",
        "purpose": "Comprehensive go-live readiness report with HTTPS evidence links",
        "path": "CEO_SECTION_V_REPORT_scholarship_api.md",
        "category": "executive"
    },
    "ceo_final_response": {
        "title": "CEO 2-Hour Deadline Response (FINAL)",
        "purpose": "Complete submission meeting all CEO requirements within 2-hour deadline",
        "path": "CEO_FINAL_RESPONSE_2HR_DEADLINE.md",
        "category": "executive"
    }
}


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum for a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"


def get_file_metadata(file_key: str, file_info: Dict) -> Dict:
    """Get metadata for an evidence file"""
    file_path = EVIDENCE_ROOT / file_info["path"]
    
    metadata = {
        "key": file_key,
        "title": file_info["title"],
        "purpose": file_info["purpose"],
        "category": file_info["category"],
        "path": file_info["path"],
        "url": f"/api/evidence/files/{file_key}",
        "exists": file_path.exists(),
        "sha256": None,
        "size_bytes": None,
        "timestamp_utc": None
    }
    
    if file_path.exists():
        try:
            metadata["sha256"] = calculate_sha256(file_path)
            stat = file_path.stat()
            metadata["size_bytes"] = stat.st_size
            metadata["timestamp_utc"] = stat.st_mtime
        except Exception as e:
            metadata["error"] = str(e)
    
    return metadata


@router.get("")
async def list_evidence():
    """
    GET /api/evidence
    
    Returns JSON index of all evidence items with SHA-256 checksums
    CEO requirement: accessible evidence with integrity verification
    """
    evidence_list = []
    
    for file_key, file_info in EVIDENCE_FILES.items():
        metadata = get_file_metadata(file_key, file_info)
        evidence_list.append(metadata)
    
    # Separate into available and pending
    available = [e for e in evidence_list if e["exists"]]
    missing = [e for e in evidence_list if not e["exists"]]
    
    return {
        "application": "scholarship_api",
        "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
        "evidence_api_version": "1.0",
        "generated_utc": None,  # Will be filled by response timestamp
        "total_files": len(evidence_list),
        "available_files": len(available),
        "missing_files": len(missing),
        "categories": {
            "executive": len([e for e in available if e["category"] == "executive"]),
            "compliance": len([e for e in available if e["category"] == "compliance"]),
            "observability": len([e for e in available if e["category"] == "observability"]),
            "deployment": len([e for e in available if e["category"] == "deployment"]),
            "api_docs": len([e for e in available if e["category"] == "api_docs"]),
            "navigation": len([e for e in available if e["category"] == "navigation"])
        },
        "evidence": evidence_list,
        "api_endpoints": {
            "health": "/health",
            "openapi": "/openapi.json",
            "docs": "/docs",
            "metrics": "/metrics"
        },
        "usage": {
            "list_all": "GET /api/evidence",
            "get_file": "GET /api/evidence/files/{key}",
            "verify_checksum": "Compare sha256 field with downloaded file hash"
        }
    }


@router.get("/files/{file_key}")
async def get_evidence_file(file_key: str):
    """
    GET /api/evidence/files/{key}
    
    Download a specific evidence file
    CEO requirement: HTTPS-accessible evidence artifacts
    """
    if file_key not in EVIDENCE_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Evidence file '{file_key}' not found in registry"
        )
    
    file_info = EVIDENCE_FILES[file_key]
    file_path = EVIDENCE_ROOT / file_info["path"]
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Evidence file not yet generated: {file_info['title']}"
        )
    
    # Determine media type
    media_type = "text/markdown" if file_path.suffix == ".md" else "text/plain"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
        headers={
            "X-Evidence-Title": file_info["title"],
            "X-Evidence-Purpose": file_info["purpose"],
            "X-Evidence-SHA256": calculate_sha256(file_path)
        }
    )


@router.get("/categories/{category}")
async def get_evidence_by_category(category: str):
    """
    GET /api/evidence/categories/{category}
    
    List evidence files by category (executive, compliance, observability, etc.)
    """
    filtered = []
    
    for file_key, file_info in EVIDENCE_FILES.items():
        if file_info["category"] == category:
            metadata = get_file_metadata(file_key, file_info)
            filtered.append(metadata)
    
    return {
        "category": category,
        "total_files": len(filtered),
        "available_files": len([e for e in filtered if e["exists"]]),
        "evidence": filtered
    }
