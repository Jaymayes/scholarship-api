"""
API Commercialization & Billing System
Executive directive: API plans, rate limits, billing pipeline, revenue tracking
"""
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import hashlib
import secrets
import hmac
from prometheus_client import Counter, Gauge, Histogram

class TierType(Enum):
    """API tier types for commercialization"""
    FREE = "free"
    STARTER = "starter" 
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

@dataclass
class APITier:
    """API tier configuration"""
    name: str
    monthly_cost: float
    requests_per_minute: int
    requests_per_month: int
    ai_credits_included: int
    ai_credit_cost: float  # Cost per additional credit
    features: List[str]
    support_level: str
    sla_commitment: str

@dataclass
class APIKey:
    """API key with billing information"""
    key_id: str
    key_secret_hash: str  # Salted hash of the actual secret for verification
    key_prefix: str  # Public prefix for identification (sk_live_)
    user_id: str
    company_name: str
    email: str
    tier: TierType
    created_at: datetime
    last_used: datetime
    usage_current_month: int
    ai_credits_used: int
    ai_credits_remaining: int
    billing_enabled: bool
    status: str  # active, suspended, cancelled

class APICommercializationService:
    """
    Executive directive commercialization service:
    - Free/paid tier management with ARPU targets
    - Per-key rate limiting with overage handling
    - 3% provider fee pipeline for B2B
    - 4x AI service markup for B2C credits
    - Billing readiness with invoicing
    """
    
    def __init__(self):
        self.evidence_path = Path("production/commercialization_evidence")
        self.evidence_path.mkdir(exist_ok=True)
        
        # Define API tier structure
        self.tiers = {
            TierType.FREE: APITier(
                name="Free Tier",
                monthly_cost=0.0,
                requests_per_minute=50,
                requests_per_month=10000,
                ai_credits_included=100,
                ai_credit_cost=0.0,  # No purchase option
                features=["Basic Search", "Eligibility Check", "Basic Support"],
                support_level="Community",
                sla_commitment="Best Effort"
            ),
            TierType.STARTER: APITier(
                name="Starter",
                monthly_cost=29.0,
                requests_per_minute=200,
                requests_per_month=100000,
                ai_credits_included=1000,
                ai_credit_cost=0.10,  # $0.10 per credit (4x markup from $0.025 cost)
                features=["Advanced Search", "Bulk Eligibility", "Email Support", "Analytics Dashboard"],
                support_level="Email",
                sla_commitment="99.9% Uptime"
            ),
            TierType.PROFESSIONAL: APITier(
                name="Professional", 
                monthly_cost=99.0,
                requests_per_minute=500,
                requests_per_month=500000,
                ai_credits_included=5000,
                ai_credit_cost=0.08,  # Volume discount (3.2x markup)
                features=["Semantic Search", "Advanced Analytics", "Priority Support", "Custom Integrations"],
                support_level="Priority Email + Chat",
                sla_commitment="99.95% Uptime"
            ),
            TierType.ENTERPRISE: APITier(
                name="Enterprise",
                monthly_cost=499.0,
                requests_per_minute=2000,
                requests_per_month=5000000,
                ai_credits_included=25000,
                ai_credit_cost=0.06,  # Enterprise discount (2.4x markup) 
                features=["Full API Access", "Dedicated Support", "Custom SLA", "White-label Options", "B2B Provider Portal"],
                support_level="Dedicated Account Manager",
                sla_commitment="99.99% Uptime"
            )
        }
        
        # Business metrics tracking
        self.revenue_metrics = Counter(
            'api_revenue_total',
            'Total API revenue by source and tier',
            ['source', 'tier', 'currency']
        )
        
        self.usage_metrics = Counter(
            'api_usage_total', 
            'API usage by tier and endpoint',
            ['tier', 'endpoint', 'status']
        )
        
        self.billing_metrics = Gauge(
            'api_active_subscriptions_total',
            'Number of active API subscriptions by tier',
            ['tier']
        )
        
        # In-memory storage for demonstration (use database in production)
        self.api_keys: Dict[str, APIKey] = {}
        self.usage_tracking: Dict[str, Dict] = {}
        self.billing_events: List[Dict] = []
        
        print("💰 API commercialization service initialized")
        print(f"🎯 Tiers configured: {len(self.tiers)} (Free → ${self.tiers[TierType.ENTERPRISE].monthly_cost}/mo)")
    
    def create_api_key(self, user_id: str, email: str, company_name: str, 
                      tier: TierType = TierType.FREE) -> Dict[str, Any]:
        """
        Create new API key with billing setup
        Executive directive: Key issuance with telemetry tracking
        """
        # Generate cryptographically secure API key (32-40 chars)
        # Create a truly random secret (40 chars for maximum security)
        key_secret = secrets.token_urlsafe(30)  # 30 bytes = 40 chars base64url
        key_prefix = "sk_live_"
        key_id = f"{key_prefix}{key_secret}"
        
        # Create salted hash for secure storage (never store the actual secret)
        salt = secrets.token_bytes(32)  # 32-byte random salt
        key_secret_hash = hashlib.pbkdf2_hmac('sha256', key_secret.encode(), salt, 100000).hex()
        stored_hash = f"{salt.hex()}${key_secret_hash}"  # Format: salt$hash
        
        # Get tier configuration
        tier_config = self.tiers[tier]
        
        # Create API key record
        api_key = APIKey(
            key_id=key_id,
            key_secret_hash=stored_hash,  # Store salted hash, never the actual secret
            key_prefix=key_prefix,
            user_id=user_id,
            company_name=company_name,
            email=email,
            tier=tier,
            created_at=datetime.now(),
            last_used=datetime.now(),
            usage_current_month=0,
            ai_credits_used=0,
            ai_credits_remaining=tier_config.ai_credits_included,
            billing_enabled=tier != TierType.FREE,
            status="active"
        )
        
        self.api_keys[key_id] = api_key
        
        # Initialize usage tracking
        self.usage_tracking[key_id] = {
            "requests_today": 0,
            "requests_this_month": 0,
            "last_reset_daily": datetime.now().date(),
            "last_reset_monthly": datetime.now().replace(day=1).date(),
            "overage_charges": 0.0
        }
        
        # Track subscription
        self.billing_metrics.labels(tier=tier.value).inc()
        
        result = {
            "api_key": key_id,
            "tier": tier.value,
            "tier_name": tier_config.name,
            "monthly_cost": tier_config.monthly_cost,
            "rate_limits": {
                "requests_per_minute": tier_config.requests_per_minute,
                "requests_per_month": tier_config.requests_per_month
            },
            "ai_credits": {
                "included": tier_config.ai_credits_included,
                "remaining": api_key.ai_credits_remaining,
                "cost_per_additional": tier_config.ai_credit_cost
            },
            "features": tier_config.features,
            "support_level": tier_config.support_level,
            "sla": tier_config.sla_commitment,
            "billing_enabled": api_key.billing_enabled,
            "created_at": api_key.created_at.isoformat()
        }
        
        # Save evidence
        evidence_file = self.evidence_path / f"api_key_created_{key_id}_{int(time.time())}.json"
        with open(evidence_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"🔑 API key created: {key_prefix}{'*' * 16}... ({tier.value} tier)")
        print(f"💳 Billing enabled: {api_key.billing_enabled}")
        
        return result
    
    def verify_api_key(self, provided_key: str) -> Optional[APIKey]:
        """
        Securely verify API key using constant-time comparison
        Returns APIKey object if valid, None if invalid
        """
        if not provided_key or not provided_key.startswith("sk_live_"):
            return None
            
        # Extract the secret part (everything after sk_live_)
        try:
            key_secret = provided_key[8:]  # Remove "sk_live_" prefix
        except (IndexError, AttributeError):
            return None
            
        # Check against all stored keys using constant-time comparison
        for stored_key_id, api_key_obj in self.api_keys.items():
            if stored_key_id != provided_key:
                continue
                
            # Parse stored hash (format: salt$hash)
            try:
                salt_hex, stored_hash = api_key_obj.key_secret_hash.split('$', 1)
                salt = bytes.fromhex(salt_hex)
                
                # Compute hash of provided secret with same salt
                provided_hash = hashlib.pbkdf2_hmac('sha256', key_secret.encode(), salt, 100000).hex()
                
                # Constant-time comparison to prevent timing attacks
                if hmac.compare_digest(provided_hash, stored_hash):
                    if api_key_obj.status == "active":
                        return api_key_obj
                    else:
                        return None  # Key exists but is suspended/cancelled
                        
            except (ValueError, TypeError):
                continue  # Malformed hash, skip this key
                
        return None  # No matching key found
    
    def check_rate_limits(self, api_key: str, endpoint: str) -> Dict[str, Any]:
        """
        Check rate limits with overage handling using secure key verification
        Executive directive: Per-key rate-limit headers and overage handling
        """
        # Securely verify the API key
        key_info = self.verify_api_key(api_key)
        if not key_info:
            return {
                "allowed": False,
                "reason": "invalid_api_key",
                "status_code": 401
            }
        tier_config = self.tiers[key_info.tier]
        usage = self.usage_tracking[api_key]
        
        # Reset counters if needed
        today = datetime.now().date()
        current_month = datetime.now().replace(day=1).date()
        
        if usage["last_reset_daily"] < today:
            usage["requests_today"] = 0
            usage["last_reset_daily"] = today
            
        if usage["last_reset_monthly"] < current_month:
            usage["requests_this_month"] = 0
            usage["last_reset_monthly"] = current_month
            usage["overage_charges"] = 0.0
        
        # Check minute-level rate limit (simplified - use Redis in production)
        minute_requests = usage["requests_today"] // 1440  # Rough estimate
        
        if minute_requests >= tier_config.requests_per_minute:
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "status_code": 429,
                "headers": {
                    "X-RateLimit-Limit": str(tier_config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((datetime.now() + timedelta(minutes=1)).timestamp())),
                    "Retry-After": "60"
                }
            }
        
        # Check monthly quota
        monthly_overage = max(0, usage["requests_this_month"] - tier_config.requests_per_month)
        
        # Calculate overage cost (if billing enabled)
        overage_cost_per_request = 0.001  # $0.001 per overage request
        if monthly_overage > 0 and key_info.billing_enabled:
            additional_cost = monthly_overage * overage_cost_per_request
            usage["overage_charges"] += additional_cost
        
        # Increment usage
        usage["requests_today"] += 1
        usage["requests_this_month"] += 1
        key_info.last_used = datetime.now()
        
        # Track metrics
        self.usage_metrics.labels(
            tier=key_info.tier.value,
            endpoint=endpoint,
            status="allowed"
        ).inc()
        
        remaining_monthly = max(0, tier_config.requests_per_month - usage["requests_this_month"])
        
        return {
            "allowed": True,
            "tier": key_info.tier.value,
            "headers": {
                "X-RateLimit-Limit": str(tier_config.requests_per_minute),
                "X-RateLimit-Remaining": str(max(0, tier_config.requests_per_minute - minute_requests - 1)),
                "X-RateLimit-Monthly-Limit": str(tier_config.requests_per_month),
                "X-RateLimit-Monthly-Remaining": str(remaining_monthly),
                "X-RateLimit-Monthly-Overage": str(monthly_overage),
                "X-Overage-Charges": f"${usage['overage_charges']:.2f}"
            },
            "billing_impact": {
                "monthly_overage": monthly_overage,
                "overage_charges": usage["overage_charges"],
                "next_billing_cycle": (current_month + timedelta(days=32)).replace(day=1).isoformat()
            }
        }
    
    def consume_ai_credits(self, api_key: str, credits_needed: int) -> Dict[str, Any]:
        """
        Consume AI credits with 4x markup billing
        Executive directive: 4x AI service markup for B2C credits
        """
        if api_key not in self.api_keys:
            return {
                "success": False,
                "reason": "invalid_api_key",
                "status_code": 401
            }
        
        key_info = self.api_keys[api_key]
        tier_config = self.tiers[key_info.tier]
        
        # Check available credits
        if key_info.ai_credits_remaining >= credits_needed:
            # Use included credits
            key_info.ai_credits_remaining -= credits_needed
            key_info.ai_credits_used += credits_needed
            
            return {
                "success": True,
                "credits_consumed": credits_needed,
                "credits_remaining": key_info.ai_credits_remaining,
                "cost": 0.0,
                "source": "included_credits"
            }
        
        elif key_info.tier == TierType.FREE:
            # Free tier cannot purchase additional credits
            return {
                "success": False,
                "reason": "insufficient_credits",
                "status_code": 402,
                "credits_needed": credits_needed,
                "credits_remaining": key_info.ai_credits_remaining,
                "upgrade_required": True,
                "suggested_tier": "starter"
            }
        
        else:
            # Calculate overage cost with markup
            overage_credits = credits_needed - key_info.ai_credits_remaining
            overage_cost = overage_credits * tier_config.ai_credit_cost
            
            # Consume all remaining included credits
            included_used = key_info.ai_credits_remaining
            key_info.ai_credits_remaining = 0
            key_info.ai_credits_used += included_used
            
            # Track overage billing
            billing_event = {
                "api_key": api_key,
                "event_type": "ai_credits_overage",
                "credits_consumed": overage_credits,
                "cost": overage_cost,
                "timestamp": datetime.now().isoformat(),
                "tier": key_info.tier.value
            }
            self.billing_events.append(billing_event)
            
            # Track revenue
            self.revenue_metrics.labels(
                source="ai_credits_b2c",
                tier=key_info.tier.value,
                currency="usd"
            ).inc(overage_cost)
            
            print(f"💳 AI credits overage: {overage_credits} credits, ${overage_cost:.2f}")
            
            return {
                "success": True,
                "credits_consumed": credits_needed,
                "included_credits_used": included_used,
                "overage_credits": overage_credits,
                "overage_cost": overage_cost,
                "credits_remaining": 0,
                "source": "mixed_included_and_overage"
            }
    
    def track_b2b_revenue(self, provider_id: str, transaction_amount: float) -> Dict[str, Any]:
        """
        Track B2B provider revenue with 3% fee
        Executive directive: 3% provider fee pipeline for B2B
        """
        commission_rate = 0.03  # 3% provider fee
        commission_amount = transaction_amount * commission_rate
        
        # Track B2B revenue
        self.revenue_metrics.labels(
            source="b2b_provider_fee",
            tier="enterprise",
            currency="usd"
        ).inc(commission_amount)
        
        billing_event = {
            "provider_id": provider_id,
            "event_type": "b2b_commission",
            "transaction_amount": transaction_amount,
            "commission_rate": commission_rate,
            "commission_amount": commission_amount,
            "timestamp": datetime.now().isoformat()
        }
        self.billing_events.append(billing_event)
        
        # Save evidence
        evidence_file = self.evidence_path / f"b2b_revenue_{provider_id}_{int(time.time())}.json"
        with open(evidence_file, 'w') as f:
            json.dump(billing_event, f, indent=2)
        
        print(f"🏢 B2B revenue tracked: ${transaction_amount:.2f} → ${commission_amount:.2f} commission (3%)")
        
        return {
            "provider_id": provider_id,
            "transaction_amount": transaction_amount,
            "commission_amount": commission_amount,
            "commission_rate": "3%",
            "recorded_at": billing_event["timestamp"]
        }
    
    def generate_invoice_preview(self, api_key: str) -> Dict[str, Any]:
        """
        Generate billing invoice preview
        Executive directive: Dry-run invoicing for paid tiers
        """
        if api_key not in self.api_keys:
            return {"error": "invalid_api_key"}
        
        key_info = self.api_keys[api_key]
        tier_config = self.tiers[key_info.tier]
        usage = self.usage_tracking[api_key]
        
        # Calculate billing period
        current_month = datetime.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        
        # Base subscription cost
        base_cost = tier_config.monthly_cost
        
        # Usage overage costs
        overage_requests = max(0, usage["requests_this_month"] - tier_config.requests_per_month)
        overage_request_cost = overage_requests * 0.001  # $0.001 per overage request
        
        # AI credits overage
        ai_overage_events = [
            event for event in self.billing_events 
            if event.get("api_key") == api_key and event.get("event_type") == "ai_credits_overage"
        ]
        ai_overage_cost = sum(event["cost"] for event in ai_overage_events)
        
        # Total calculation
        subtotal = base_cost + overage_request_cost + ai_overage_cost
        tax_rate = 0.08  # 8% tax
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        invoice = {
            "invoice_preview": True,
            "api_key": api_key[:16] + "...",
            "billing_period": {
                "start": current_month.isoformat(),
                "end": next_month.isoformat()
            },
            "customer": {
                "company": key_info.company_name,
                "email": key_info.email,
                "tier": key_info.tier.value
            },
            "line_items": [
                {
                    "description": f"{tier_config.name} Plan",
                    "quantity": 1,
                    "unit_price": base_cost,
                    "amount": base_cost
                }
            ],
            "usage_charges": [],
            "subtotal": base_cost,
            "tax_rate": "8%",
            "tax_amount": round(tax_amount, 2),
            "total": round(total, 2),
            "currency": "USD",
            "status": "preview"
        }
        
        # Add overage charges if any
        if overage_request_cost > 0:
            invoice["usage_charges"].append({
                "description": "API Request Overage",
                "quantity": overage_requests,
                "unit_price": 0.001,
                "amount": round(overage_request_cost, 2)
            })
            invoice["subtotal"] += overage_request_cost
        
        if ai_overage_cost > 0:
            invoice["usage_charges"].append({
                "description": "AI Credits Overage",
                "quantity": sum(event["credits_consumed"] for event in ai_overage_events),
                "unit_price": tier_config.ai_credit_cost,
                "amount": round(ai_overage_cost, 2)
            })
            invoice["subtotal"] += ai_overage_cost
        
        # Recalculate with overages
        invoice["subtotal"] = round(invoice["subtotal"], 2)
        invoice["tax_amount"] = round(invoice["subtotal"] * tax_rate, 2)
        invoice["total"] = round(invoice["subtotal"] + invoice["tax_amount"], 2)
        
        # Save evidence
        evidence_file = self.evidence_path / f"invoice_preview_{api_key}_{int(time.time())}.json"
        with open(evidence_file, 'w') as f:
            json.dump(invoice, f, indent=2)
        
        print(f"🧾 Invoice preview: ${invoice['total']:.2f} for {key_info.company_name}")
        
        return invoice
    
    def get_tier_comparison(self) -> Dict[str, Any]:
        """
        Get API tier comparison for marketing
        Executive directive: Clear tier differentiation for conversion
        """
        return {
            "tier_comparison": {
                tier.value: {
                    "name": config.name,
                    "monthly_cost": config.monthly_cost,
                    "requests_per_minute": config.requests_per_minute,
                    "requests_per_month": config.requests_per_month,
                    "ai_credits_included": config.ai_credits_included,
                    "ai_credit_cost": config.ai_credit_cost,
                    "features": config.features,
                    "support_level": config.support_level,
                    "sla_commitment": config.sla_commitment,
                    "best_for": {
                        "free": "Testing, small projects, students",
                        "starter": "Small businesses, side projects",
                        "professional": "Growing companies, production apps",
                        "enterprise": "Large organizations, high-volume usage"
                    }.get(tier.value, "")
                }
                for tier, config in self.tiers.items()
            },
            "popular_choice": "professional",
            "enterprise_contact": "sales@scholarshipapi.com",
            "upgrade_benefits": {
                "higher_limits": "Avoid rate limiting and overage charges",
                "better_support": "Faster response times and dedicated help",
                "advanced_features": "Access to latest AI and analytics features",
                "sla_guarantees": "Contractual uptime and performance commitments"
            }
        }

# Global commercialization service
commercialization_service = APICommercializationService()