"""
B2B Provider Acquisition Engine
Executive directive: Fast, repeatable onboarding with measurable activation metrics
30-60-90 day plan: Pipeline → Pilots → Paid tiers with B2B revenue dominance
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import json
import hmac
import os
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from models.database import ProviderDB, ScholarshipListingDB, SessionLocal, create_tables
from config.settings import settings

logger = logging.getLogger(__name__)

class ProviderSegment(Enum):
    """3 core provider segments with specific value propositions"""
    UNIVERSITY = "university"           # Admissions/Financial Aid
    FOUNDATION = "foundation"           # Non-profits/Foundations  
    CORPORATE = "corporate"             # CSR/Lenders

class ProviderStatus(Enum):
    """B2B funnel stages for KPI tracking"""
    INVITED = "invited"                 # Initial outreach
    MEETING = "meeting"                # Meeting scheduled
    PILOT_ACCEPTED = "pilot_accepted"  # 60-90 day pilot agreed
    FIRST_LISTING = "first_listing"    # First scholarship published
    FIRST_APPLICATION = "first_application"  # First student application
    PAID_PLAN = "paid_plan"           # Converted to paid tier

@dataclass
class ProviderProfile:
    """Institutional provider profile for self-service onboarding"""
    provider_id: str
    name: str
    segment: ProviderSegment
    status: ProviderStatus
    contact_email: str
    institutional_domain: str
    
    # Onboarding metrics (KPI tracking)
    created_at: datetime = field(default_factory=datetime.utcnow)
    time_to_first_listing: Optional[timedelta] = None
    time_to_first_application: Optional[timedelta] = None
    first_listing_date: Optional[datetime] = None
    first_application_date: Optional[datetime] = None
    
    # Account details
    api_key: Optional[str] = None
    listings_count: int = 0
    applications_received: int = 0
    
    # Contract/compliance
    dpa_signed: bool = False
    dpa_signed_date: Optional[datetime] = None
    pilot_start_date: Optional[datetime] = None
    pilot_end_date: Optional[datetime] = None
    
    # Business metrics
    monthly_fee: float = 0.0
    revenue_generated: float = 0.0

@dataclass 
class ScholarshipListing:
    """Provider scholarship listing with templated metadata"""
    listing_id: str
    provider_id: str
    title: str
    amount: float
    deadline: datetime
    description: str
    requirements: List[str]
    application_url: str
    
    # Metadata for matching
    field_of_study: List[str] = field(default_factory=list)
    gpa_requirement: Optional[float] = None
    citizenship_required: Optional[str] = None
    
    # Performance tracking
    views: int = 0
    applications: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

class B2BProviderAcquisitionService:
    """
    Core service for B2B Provider Acquisition with 30-60-90 plan execution
    Focus: Fast onboarding, measurable activation, revenue growth
    Uses database persistence instead of in-memory storage
    """
    
    def __init__(self):
        # KPI targets from plan
        self.target_providers_30_days = 10
        self.target_time_to_first_listing_days = 7
        self.target_time_to_first_application_days = 14
        self.target_pilot_acceptance_rate = 0.5  # 20 meetings → 10 pilots
        
        # Ensure database tables exist
        try:
            create_tables()
            logger.info("🗄️  Database tables verified/created")
        except Exception as e:
            logger.warning(f"Database table creation issue (may already exist): {e}")
        
        logger.info("🏢 B2B Provider Acquisition service initialized with database persistence")
        logger.info(f"🎯 Targets: {self.target_providers_30_days} providers, {self.target_time_to_first_listing_days}d TTL, {self.target_time_to_first_application_days}d TTA")
    
    def get_db_session(self) -> Session:
        """Get database session for operations"""
        return SessionLocal()
    
    @property
    def providers(self) -> Dict[str, ProviderProfile]:
        """Backward compatibility property - maps database to old dict interface"""
        db = self.get_db_session()
        try:
            provider_records = db.query(ProviderDB).filter(ProviderDB.is_active == True).all()
            result = {}
            for record in provider_records:
                profile = self._db_to_provider_profile(record)
                result[record.provider_id] = profile
            return result
        finally:
            db.close()
    
    def _db_to_provider_profile(self, record: ProviderDB) -> ProviderProfile:
        """Convert database record to ProviderProfile dataclass"""
        # Calculate time metrics
        time_to_first_listing = None
        time_to_first_application = None
        
        if record.first_listing_date:
            time_to_first_listing = record.first_listing_date - record.created_at
        if record.first_application_date:
            time_to_first_application = record.first_application_date - record.created_at
        
        return ProviderProfile(
            provider_id=record.provider_id,
            name=record.name,
            segment=ProviderSegment(record.segment),
            status=ProviderStatus(record.status),
            contact_email=record.contact_email,
            institutional_domain=record.institutional_domain,
            created_at=record.created_at,
            time_to_first_listing=time_to_first_listing,
            time_to_first_application=time_to_first_application,
            first_listing_date=record.first_listing_date,
            first_application_date=record.first_application_date,
            api_key=record.api_key_prefix if record.api_key_prefix else None,  # Show prefix only
            listings_count=record.listings_count,
            applications_received=record.applications_received,
            dpa_signed=record.dpa_signed,
            dpa_signed_date=record.dpa_signed_date,
            pilot_start_date=record.pilot_start_date,
            pilot_end_date=record.pilot_end_date,
            monthly_fee=record.monthly_fee,
            revenue_generated=record.revenue_generated
        )

    def get_segment_value_proposition(self, segment: ProviderSegment) -> Dict[str, Any]:
        """Segment-specific value propositions from executive plan"""
        value_props = {
            ProviderSegment.UNIVERSITY: {
                "headline": "Lower Student Acquisition Cost Through High-Intent Matching",
                "benefits": [
                    "Engage high-intent students matched to your aid programs",
                    "Direct recruitment via our provider dashboard", 
                    "Reduce admissions marketing spend with targeted reach",
                    "Access to predictive matching for qualified applicants"
                ],
                "proof_points": [
                    "85% match accuracy with our eligibility engine",
                    "Average 40% reduction in unqualified applications",
                    "Direct pipeline to 36K+ monthly active students"
                ],
                "cta": "Start your pilot and reduce acquisition costs immediately"
            },
            ProviderSegment.FOUNDATION: {
                "headline": "Increase Qualified Applicant Volume & Address Unclaimed Funds",
                "benefits": [
                    "Increase qualified applicant volume and fit",
                    "Reduce admin overhead through structured listings",
                    "Address the $1B+ unclaimed scholarship funds problem",
                    "Automated eligibility filtering saves review time"
                ],
                "proof_points": [
                    "Average 3x increase in qualified applications",
                    "60% reduction in administrative review time", 
                    "Access to underserved student populations"
                ],
                "cta": "Join our pilot to maximize your scholarship impact"
            },
            ProviderSegment.CORPORATE: {
                "headline": "Targeted CSR Impact & Ethical Talent Pipeline Access",
                "benefits": [
                    "Targeted CSR with measurable education impact",
                    "Ethical, compliant reach to financing-focused students",
                    "Build talent pipeline for internships/hiring",
                    "Brand visibility in high-intent student moments"
                ],
                "proof_points": [
                    "100% FERPA/CCPA compliant student engagement",
                    "Direct access to students solving college financing",
                    "Transparent ROI tracking for CSR programs"
                ],
                "cta": "Launch your CSR pilot with immediate compliance"
            }
        }
        return value_props[segment]

    def generate_provider_api_key(self, provider_id: str) -> str:
        """Generate cryptographically secure API key for provider"""
        # Format: pvd_<8_chars>_<32_secure_chars>
        prefix = f"pvd_{provider_id[:8]}"
        secure_suffix = secrets.token_urlsafe(32)[:32]
        return f"{prefix}_{secure_suffix}"
    
    def hash_api_key(self, api_key: str) -> tuple[str, str]:
        """Hash API key using PBKDF2 with salt. Returns (hash, prefix)"""
        # Extract prefix for identification
        if '_' in api_key:
            prefix = '_'.join(api_key.split('_')[:2])  # pvd_xxxxxxxx
        else:
            prefix = api_key[:12]
            
        # Generate salt and hash
        salt = secrets.token_bytes(32)
        key_hash = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt, 100000)
        
        # Combine salt and hash
        combined_hash = salt.hex() + '$' + key_hash.hex()
        return combined_hash, prefix
    
    def verify_api_key(self, provided_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash using constant-time comparison"""
        try:
            # Parse stored hash (format: salt$hash)
            salt_hex, stored_key_hash = stored_hash.split('$', 1)
            salt = bytes.fromhex(salt_hex)
            
            # Compute hash of provided key with same salt
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_key.encode(), salt, 100000)
            
            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(provided_hash.hex(), stored_key_hash)
        except (ValueError, TypeError):
            return False
    
    def get_provider_api_key_for_display(self, provider_id: str) -> Optional[str]:
        """Securely retrieve API key for display in credentials endpoint.
        Returns the full key one time only for security.
        """
        db = self.get_db_session()
        try:
            # Get provider from database
            provider_record = db.query(ProviderDB).filter(
                ProviderDB.provider_id == provider_id,
                ProviderDB.is_active == True
            ).first()
            
            if not provider_record or not provider_record.api_key_hash:
                return None
                
            # For security, we can't recover the original key from the hash
            # In a production system, you would store the key temporarily during creation
            # or regenerate it when needed. For now, return a secure message.
            return f"API key exists (prefix: {provider_record.api_key_prefix}) - regenerate to view full key"
            
        except Exception as e:
            logger.error(f"Error retrieving API key for provider {provider_id}: {e}")
            return None
        finally:
            db.close()
    
    def regenerate_provider_api_key(self, provider_id: str) -> Optional[str]:
        """Regenerate API key for provider and return the new key once"""
        db = self.get_db_session()
        try:
            # Get provider from database
            provider_record = db.query(ProviderDB).filter(
                ProviderDB.provider_id == provider_id,
                ProviderDB.is_active == True
            ).first()
            
            if not provider_record:
                return None
                
            # Generate new API key
            new_api_key = self.generate_provider_api_key(provider_id)
            new_hash, new_prefix = self.hash_api_key(new_api_key)
            
            # Update database
            provider_record.api_key_hash = new_hash
            provider_record.api_key_prefix = new_prefix
            provider_record.api_key_created_at = datetime.utcnow()
            provider_record.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"🔑 API key regenerated for provider {provider_id}")
            return new_api_key
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error regenerating API key for provider {provider_id}: {e}")
            return None
        finally:
            db.close()

    def register_provider(self, name: str, segment: ProviderSegment, 
                         contact_email: str, institutional_domain: str) -> ProviderProfile:
        """Self-service provider registration with database persistence"""
        
        # Generate provider ID
        provider_id = f"prv_{segment.value}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        api_key = self.generate_provider_api_key(provider_id)
        
        # Hash the API key for secure storage
        api_key_hash, api_key_prefix = self.hash_api_key(api_key)
        
        db = self.get_db_session()
        try:
            # Create database record with hashed key
            db_provider = ProviderDB(
                provider_id=provider_id,
                name=name,
                segment=segment.value,
                status=ProviderStatus.INVITED.value,
                contact_email=contact_email,
                institutional_domain=institutional_domain,
                api_key_hash=api_key_hash,
                api_key_prefix=api_key_prefix,
                api_key_created_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(db_provider)
            db.commit()
            db.refresh(db_provider)
            
            # Convert to profile for return
            profile = self._db_to_provider_profile(db_provider)
            
            logger.info(f"✅ Provider registered to database: {name} ({segment.value}) - {provider_id}")
            return profile
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"❌ Provider registration failed (duplicate?): {name} - {e}")
            raise ValueError(f"Provider registration failed: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Database error during provider registration: {e}")
            raise ValueError(f"Database error: {str(e)}")
        finally:
            db.close()

    def advance_provider_status(self, provider_id: str, new_status: ProviderStatus) -> Dict[str, Any]:
        """Advance provider through B2B funnel with KPI tracking"""
        if provider_id not in self.providers:
            raise ValueError(f"Provider {provider_id} not found")
            
        provider = self.providers[provider_id]
        old_status = provider.status
        provider.status = new_status
        
        # Track time-to-value metrics
        now = datetime.utcnow()
        
        if new_status == ProviderStatus.FIRST_LISTING:
            provider.first_listing_date = now
            provider.time_to_first_listing = now - provider.created_at
            
        elif new_status == ProviderStatus.FIRST_APPLICATION:
            provider.first_application_date = now
            if provider.first_listing_date:
                provider.time_to_first_application = now - provider.created_at
                
        logger.info(f"📈 Provider {provider_id} advanced: {old_status.value} → {new_status.value}")
        
        return {
            "provider_id": provider_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "time_to_first_listing_days": provider.time_to_first_listing.days if provider.time_to_first_listing else None,
            "time_to_first_application_days": provider.time_to_first_application.days if provider.time_to_first_application else None
        }

    def create_scholarship_listing(self, provider_id: str, title: str, amount: float,
                                 deadline: datetime, description: str, requirements: List[str],
                                 application_url: str, **kwargs) -> ScholarshipListing:
        """Provider creates scholarship listing with templated metadata"""
        
        if provider_id not in self.providers:
            raise ValueError(f"Provider {provider_id} not found")
            
        # Generate listing ID
        listing_id = f"lst_{provider_id}_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        
        listing = ScholarshipListing(
            listing_id=listing_id,
            provider_id=provider_id,
            title=title,
            amount=amount,
            deadline=deadline,
            description=description,
            requirements=requirements,
            application_url=application_url,
            field_of_study=kwargs.get('field_of_study', []),
            gpa_requirement=kwargs.get('gpa_requirement'),
            citizenship_required=kwargs.get('citizenship_required')
        )
        
        self.listings[listing_id] = listing
        
        # Update provider metrics
        provider = self.providers[provider_id]
        provider.listings_count += 1
        
        # Advance to first listing if this is their first
        if provider.listings_count == 1 and provider.status in [ProviderStatus.INVITED, ProviderStatus.MEETING, ProviderStatus.PILOT_ACCEPTED]:
            self.advance_provider_status(provider_id, ProviderStatus.FIRST_LISTING)
            
        logger.info(f"📝 Listing created: {title} by {provider_id} (${amount:,.2f})")
        return listing

    def get_onboarding_metrics(self) -> Dict[str, Any]:
        """Get comprehensive onboarding and activation metrics"""
        
        providers_by_status = {}
        for status in ProviderStatus:
            providers_by_status[status.value] = len([p for p in self.providers.values() if p.status == status])
            
        # Calculate averages
        ttl_values = [p.time_to_first_listing.days for p in self.providers.values() if p.time_to_first_listing]
        tta_values = [p.time_to_first_application.days for p in self.providers.values() if p.time_to_first_application]
        
        avg_ttl = sum(ttl_values) / len(ttl_values) if ttl_values else None
        avg_tta = sum(tta_values) / len(tta_values) if tta_values else None
        
        return {
            "total_providers": len(self.providers),
            "providers_by_status": providers_by_status,
            "total_listings": len(self.listings),
            "average_time_to_first_listing_days": avg_ttl,
            "average_time_to_first_application_days": avg_tta,
            "target_ttl_days": self.target_time_to_first_listing_days,
            "target_tta_days": self.target_time_to_first_application_days,
            "ttl_target_met": avg_ttl <= self.target_time_to_first_listing_days if avg_ttl else None,
            "tta_target_met": avg_tta <= self.target_time_to_first_application_days if avg_tta else None,
            "conversion_rates": {
                "invited_to_meeting": self._calculate_conversion_rate(ProviderStatus.INVITED, ProviderStatus.MEETING),
                "meeting_to_pilot": self._calculate_conversion_rate(ProviderStatus.MEETING, ProviderStatus.PILOT_ACCEPTED),
                "pilot_to_listing": self._calculate_conversion_rate(ProviderStatus.PILOT_ACCEPTED, ProviderStatus.FIRST_LISTING),
                "listing_to_application": self._calculate_conversion_rate(ProviderStatus.FIRST_LISTING, ProviderStatus.FIRST_APPLICATION),
                "application_to_paid": self._calculate_conversion_rate(ProviderStatus.FIRST_APPLICATION, ProviderStatus.PAID_PLAN)
            }
        }

    def _calculate_conversion_rate(self, from_status: ProviderStatus, to_status: ProviderStatus) -> Optional[float]:
        """Calculate conversion rate between funnel stages"""
        from_count = len([p for p in self.providers.values() 
                         if p.status.value >= from_status.value])
        to_count = len([p for p in self.providers.values() 
                       if p.status.value >= to_status.value])
        
        if from_count == 0:
            return None
        return to_count / from_count

    def get_weekly_provider_report(self) -> Dict[str, Any]:
        """Weekly 'Provider Engine' report for executive tracking"""
        metrics = self.get_onboarding_metrics()
        
        # Pipeline health
        pipeline_counts = metrics["providers_by_status"]
        
        # Revenue calculations
        total_revenue = sum(p.revenue_generated for p in self.providers.values())
        paid_providers = len([p for p in self.providers.values() if p.status == ProviderStatus.PAID_PLAN])
        avg_revenue_per_provider = total_revenue / paid_providers if paid_providers > 0 else 0
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "executive_summary": {
                "total_providers": metrics["total_providers"],
                "active_listings": metrics["total_listings"], 
                "b2b_revenue": total_revenue,
                "avg_revenue_per_provider": avg_revenue_per_provider,
                "target_progress": f"{metrics['total_providers']}/{self.target_providers_30_days}"
            },
            "pipeline_health": pipeline_counts,
            "activation_metrics": {
                "avg_time_to_first_listing": metrics["average_time_to_first_listing_days"],
                "avg_time_to_first_application": metrics["average_time_to_first_application_days"],
                "ttl_target_status": "✅ Met" if metrics["ttl_target_met"] else "❌ Behind",
                "tta_target_status": "✅ Met" if metrics["tta_target_met"] else "❌ Behind"
            },
            "conversion_funnel": metrics["conversion_rates"],
            "next_actions": self._get_report_recommendations(metrics)
        }
    
    def _get_report_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations from metrics"""
        recommendations = []
        
        if metrics["total_providers"] < self.target_providers_30_days:
            recommendations.append(f"Accelerate outreach: {self.target_providers_30_days - metrics['total_providers']} providers needed for target")
            
        if metrics["average_time_to_first_listing_days"] and metrics["average_time_to_first_listing_days"] > self.target_time_to_first_listing_days:
            recommendations.append("Optimize onboarding flow: TTL exceeding 7-day target")
            
        if metrics["conversion_rates"]["meeting_to_pilot"] and metrics["conversion_rates"]["meeting_to_pilot"] < 0.5:
            recommendations.append("Improve pilot offer: conversion below 50% target")
            
        if not recommendations:
            recommendations.append("All metrics on track - maintain current execution")
            
        return recommendations

# Global service instance
b2b_service = B2BProviderAcquisitionService()

logger.info("🏢 B2B Provider Acquisition service loaded - Ready for 30-60-90 execution")