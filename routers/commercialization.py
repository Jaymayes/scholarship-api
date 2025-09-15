"""
API Commercialization Router
Executive directive: API plans, billing, key management endpoints
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from production.api_commercialization import commercialization_service, TierType
from production.status_page import status_service 
from production.release_notes import release_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/billing",
    tags=["commercialization"],
    responses={
        200: {"description": "Success"},
        401: {"description": "Invalid API key"},
        402: {"description": "Payment required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# Status page and docs router
public_router = APIRouter(
    prefix="",
    tags=["public"],
    responses={200: {"description": "Success"}}
)

@router.post("/api-key")
async def create_api_key(
    user_id: str,
    email: str,
    company_name: str,
    tier: str = "free"
) -> Dict[str, Any]:
    """
    🔑 CREATE API KEY WITH BILLING SETUP
    Executive directive: Key issuance with contact email/company tracking
    
    Args:
        user_id: Unique user identifier
        email: Contact email for billing and support
        company_name: Company name for B2B tracking
        tier: API tier (free, starter, professional, enterprise)
    
    Returns:
        API key details with billing information
    """
    try:
        # Validate tier
        try:
            tier_type = TierType(tier.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier '{tier}'. Valid options: free, starter, professional, enterprise"
            )
        
        result = commercialization_service.create_api_key(
            user_id=user_id,
            email=email,
            company_name=company_name,
            tier=tier_type
        )
        
        logger.info(f"🔑 API key created: {result['api_key'][:16]}... for {company_name}")
        
        return {
            "message": "API key created successfully",
            "api_key_details": result,
            "next_steps": [
                "Save your API key securely - it cannot be retrieved later",
                "Review rate limits and usage guidelines",
                "Test API integration with included credits",
                "Monitor usage at /api/v1/billing/usage"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ API key creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@router.get("/tiers")
async def get_tier_comparison() -> Dict[str, Any]:
    """
    💰 GET API TIER COMPARISON
    Executive directive: Clear pricing and feature differentiation
    
    Returns:
        Complete tier comparison with pricing and features
    """
    try:
        comparison = commercialization_service.get_tier_comparison()
        
        return {
            "message": "API tier comparison retrieved successfully",
            "pricing_tiers": comparison,
            "billing_info": {
                "currency": "USD",
                "billing_cycle": "Monthly",
                "overage_policy": "Pay-as-you-go for usage above limits",
                "ai_credits": "4x markup from cost for sustainable pricing",
                "b2b_commission": "3% provider fee for marketplace transactions"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Tier comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tier comparison: {str(e)}")

@router.get("/usage")
async def get_usage_details(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Dict[str, Any]:
    """
    📊 GET API USAGE AND BILLING DETAILS
    Executive directive: Per-key usage tracking and overage transparency
    
    Headers:
        X-API-Key: Your API key for usage lookup
    
    Returns:
        Usage statistics, billing information, and limits
    """
    try:
        if not x_api_key:
            raise HTTPException(
                status_code=401,
                detail="X-API-Key header required for usage lookup"
            )
        
        # Check rate limits to get current usage
        usage_info = commercialization_service.check_rate_limits(x_api_key, "usage_check")
        
        if not usage_info["allowed"] and usage_info.get("reason") == "invalid_api_key":
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # Generate invoice preview
        invoice = commercialization_service.generate_invoice_preview(x_api_key)
        
        return {
            "message": "Usage details retrieved successfully",
            "current_usage": {
                "tier": usage_info["tier"],
                "monthly_remaining": usage_info["headers"]["X-RateLimit-Monthly-Remaining"],
                "monthly_overage": usage_info["headers"]["X-RateLimit-Monthly-Overage"],
                "overage_charges": usage_info["headers"]["X-Overage-Charges"]
            },
            "billing_preview": invoice,
            "rate_limits": {
                "requests_per_minute": usage_info["headers"]["X-RateLimit-Limit"],
                "monthly_quota": usage_info["headers"]["X-RateLimit-Monthly-Limit"]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Usage details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage details: {str(e)}")

@router.post("/ai-credits/consume")
async def consume_ai_credits(
    credits_needed: int,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Dict[str, Any]:
    """
    🤖 CONSUME AI CREDITS WITH BILLING
    Executive directive: 4x AI service markup for B2C credits
    
    Headers:
        X-API-Key: Your API key
    
    Args:
        credits_needed: Number of AI credits to consume
    
    Returns:
        Credit consumption result with billing details
    """
    try:
        if not x_api_key:
            raise HTTPException(
                status_code=401,
                detail="X-API-Key header required"
            )
        
        result = commercialization_service.consume_ai_credits(x_api_key, credits_needed)
        
        if not result["success"]:
            status_code = result.get("status_code", 400)
            raise HTTPException(status_code=status_code, detail=result["reason"])
        
        return {
            "message": "AI credits consumed successfully",
            "credit_details": result,
            "billing_impact": result.get("overage_cost", 0.0) > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI credits consumption error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to consume AI credits: {str(e)}")

@router.post("/b2b/revenue")
async def track_b2b_revenue(
    provider_id: str,
    transaction_amount: float
) -> Dict[str, Any]:
    """
    🏢 TRACK B2B PROVIDER REVENUE
    Executive directive: 3% provider fee pipeline for B2B marketplace
    
    Args:
        provider_id: Provider identifier
        transaction_amount: Transaction amount for commission calculation
    
    Returns:
        Revenue tracking confirmation with commission details
    """
    try:
        result = commercialization_service.track_b2b_revenue(
            provider_id=provider_id,
            transaction_amount=transaction_amount
        )
        
        return {
            "message": "B2B revenue tracked successfully",
            "commission_details": result,
            "marketplace_fee": "3% of transaction amount"
        }
        
    except Exception as e:
        logger.error(f"❌ B2B revenue tracking error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track B2B revenue: {str(e)}")

@router.get("/invoice/preview")
async def get_invoice_preview(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Dict[str, Any]:
    """
    🧾 GET BILLING INVOICE PREVIEW
    Executive directive: Dry-run invoicing for paid tiers
    
    Headers:
        X-API-Key: Your API key
    
    Returns:
        Invoice preview with line items and total
    """
    try:
        if not x_api_key:
            raise HTTPException(
                status_code=401,
                detail="X-API-Key header required"
            )
        
        invoice = commercialization_service.generate_invoice_preview(x_api_key)
        
        if "error" in invoice:
            raise HTTPException(status_code=401, detail=invoice["error"])
        
        return {
            "message": "Invoice preview generated successfully",
            "invoice_preview": invoice,
            "billing_cycle": "Monthly",
            "payment_due": "Due on next billing cycle"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Invoice preview error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate invoice preview: {str(e)}")

# Public endpoints for status page and documentation
@public_router.get("/status", response_class=HTMLResponse)
async def get_status_page():
    """
    📊 PUBLIC STATUS PAGE
    Executive directive: Real-time status page with trust center
    """
    try:
        html_content = status_service.generate_status_page_html()
        return HTMLResponse(content=html_content, status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Status page error: {e}")
        return HTMLResponse(
            content="<h1>Status page temporarily unavailable</h1>", 
            status_code=500
        )

@public_router.get("/status/json")
async def get_status_json():
    """
    📊 STATUS PAGE JSON API
    Executive directive: Machine-readable status for monitoring
    """
    try:
        overall_status = status_service.get_overall_status()
        components = status_service.get_component_details()
        security = status_service.get_security_posture()
        
        return {
            "status_page": overall_status,
            "components": components,
            "security_posture": security,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Status JSON error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status information")

@public_router.get("/release-notes")
async def get_release_notes():
    """
    📝 RELEASE NOTES API
    Executive directive: v1.0.0 release notes with contract lock
    """
    try:
        release_notes = release_service.generate_v100_release_notes()
        
        return {
            "message": "Release notes retrieved successfully",
            "release_notes": release_notes,
            "contract_lock": "24+ month backward compatibility guarantee"
        }
        
    except Exception as e:
        logger.error(f"❌ Release notes error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get release notes")

@public_router.get("/changelog", response_class=HTMLResponse)
async def get_changelog_html():
    """
    📝 CHANGELOG HTML
    Executive directive: User-friendly changelog display
    """
    try:
        changelog_md = release_service.generate_changelog()
        
        # Convert markdown to simple HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Scholarship Discovery API - Changelog</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <pre>{changelog_md}</pre>
</body>
</html>"""
        
        return HTMLResponse(content=html_content, status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Changelog error: {e}")
        return HTMLResponse(
            content="<h1>Changelog temporarily unavailable</h1>",
            status_code=500
        )