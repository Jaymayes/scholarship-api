# AI Scholarship Playbook - B2B Partner Service
# Self-serve partner portal and marketplace management

import asyncio
import re
from datetime import datetime, timedelta
from typing import Any

from models.b2b_partner import (
    DEFAULT_ONBOARDING_STEPS,
    SUPPORT_TIERS,
    Partner,
    PartnerAnalytics,
    PartnerOnboardingStep,
    PartnerScholarship,
    PartnerStatus,
    PartnerSupportTicket,
    PartnerType,
    VerificationStatus,
)
from services.openai_service import OpenAIService
from utils.logger import get_logger

logger = get_logger(__name__)

class PartnerVerificationService:
    """Service for automated partner verification"""

    @staticmethod
    async def verify_tax_id(tax_id: str, organization_name: str) -> bool:
        """Verify organization tax ID (stubbed for MVP)"""
        # In production, would integrate with IRS or third-party verification
        if not tax_id or len(tax_id) < 9:
            return False

        # Basic format validation
        ein_pattern = r'^\d{2}-\d{7}$'
        return bool(re.match(ein_pattern, tax_id))

    @staticmethod
    async def verify_nonprofit_status(tax_id: str) -> bool | None:
        """Verify nonprofit status via external API"""
        # In production, would check IRS nonprofit database
        await asyncio.sleep(0.1)  # Simulate API call
        return True  # Assume verified for MVP

    @staticmethod
    async def verify_domain_ownership(email: str, website_url: str) -> bool:
        """Verify email domain matches organization website"""
        if not website_url or not email:
            return False

        try:
            email_domain = email.split('@')[1].lower()
            website_domain = website_url.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].lower()

            return email_domain == website_domain or email_domain in website_domain
        except:
            return False

class B2BPartnerService:
    """Main service for B2B partner management"""

    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.verification_service = PartnerVerificationService()

        # In-memory storage for MVP (would be database in production)
        self.partners: dict[str, Partner] = {}
        self.scholarships: dict[str, PartnerScholarship] = {}
        self.onboarding_steps: dict[str, list[PartnerOnboardingStep]] = {}
        self.support_tickets: dict[str, PartnerSupportTicket] = {}

    async def register_partner(self, partner_data: dict[str, Any]) -> tuple[Partner, list[PartnerOnboardingStep]]:
        """Register new partner and initialize onboarding"""
        try:
            # Create partner record
            partner = Partner(**partner_data)

            # Perform initial verification checks
            if partner.tax_id:
                tax_valid = await self.verification_service.verify_tax_id(
                    partner.tax_id, partner.organization_name
                )
                if not tax_valid:
                    partner.verification_status = VerificationStatus.REQUIRES_REVIEW

            # Check domain ownership if website provided
            if partner.website_url:
                domain_valid = await self.verification_service.verify_domain_ownership(
                    partner.primary_contact_email, partner.website_url
                )
                if not domain_valid:
                    partner.verification_status = VerificationStatus.REQUIRES_REVIEW

            # Create onboarding steps
            onboarding_steps = []
            for i, step_template in enumerate(DEFAULT_ONBOARDING_STEPS):
                step = PartnerOnboardingStep(
                    step_id=f"{partner.partner_id}_step_{i+1}",
                    partner_id=partner.partner_id,
                    step_name=step_template["step_name"],
                    step_description=step_template["step_description"],
                    order_index=step_template["order_index"],
                    required=step_template["required"],
                    validation_rules=step_template["validation_rules"]
                )
                onboarding_steps.append(step)

            # Store data
            self.partners[partner.partner_id] = partner
            self.onboarding_steps[partner.partner_id] = onboarding_steps

            logger.info(f"Registered new partner: {partner.organization_name} ({partner.partner_id})")
            return partner, onboarding_steps

        except Exception as e:
            logger.error(f"Failed to register partner: {str(e)}")
            raise

    async def complete_onboarding_step(
        self,
        partner_id: str,
        step_id: str,
        step_data: dict[str, Any]
    ) -> PartnerOnboardingStep:
        """Mark onboarding step as complete"""
        try:
            steps = self.onboarding_steps.get(partner_id, [])
            step = next((s for s in steps if s.step_id == step_id), None)

            if not step:
                raise ValueError(f"Onboarding step {step_id} not found")

            # Validate step completion
            validation_passed = await self._validate_step_completion(step, step_data)

            if validation_passed:
                step.completed = True
                step.completed_at = datetime.utcnow()
                step.step_data = step_data

                # Check if all required steps are complete
                await self._check_onboarding_completion(partner_id)

                logger.info(f"Completed onboarding step {step.step_name} for partner {partner_id}")
            else:
                raise ValueError(f"Step validation failed for {step.step_name}")

            return step

        except Exception as e:
            logger.error(f"Failed to complete onboarding step: {str(e)}")
            raise

    async def create_scholarship_listing(
        self,
        partner_id: str,
        scholarship_data: dict[str, Any]
    ) -> PartnerScholarship:
        """Create new scholarship listing"""
        try:
            # Verify partner exists and is active
            partner = self.partners.get(partner_id)
            if not partner or partner.status != PartnerStatus.ACTIVE:
                raise ValueError("Partner not found or not active")

            # Create scholarship listing
            scholarship_data["partner_id"] = partner_id
            scholarship_data["created_by"] = partner.primary_contact_email

            scholarship = PartnerScholarship(**scholarship_data)

            # Validate scholarship data
            await self._validate_scholarship_data(scholarship)

            # Store scholarship
            self.scholarships[scholarship.listing_id] = scholarship

            logger.info(f"Created scholarship listing: {scholarship.title} ({scholarship.listing_id})")
            return scholarship

        except Exception as e:
            logger.error(f"Failed to create scholarship listing: {str(e)}")
            raise

    async def get_partner_analytics(
        self,
        partner_id: str,
        period_days: int = 30
    ) -> PartnerAnalytics:
        """Generate analytics for partner dashboard"""
        try:
            partner = self.partners.get(partner_id)
            if not partner:
                raise ValueError("Partner not found")

            # Get partner scholarships
            partner_scholarships = [
                s for s in self.scholarships.values()
                if s.partner_id == partner_id
            ]

            # Calculate analytics
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)

            total_views = sum(s.view_count for s in partner_scholarships)
            total_applications = sum(s.application_count for s in partner_scholarships)

            # Calculate conversion rates
            view_to_application_rate = (
                total_applications / total_views if total_views > 0 else 0
            )

            # Get top performing listings
            top_listings = sorted(
                partner_scholarships,
                key=lambda s: s.application_count,
                reverse=True
            )[:5]

            top_listings_data = []
            for listing in top_listings:
                top_listings_data.append({
                    "title": listing.title,
                    "views": listing.view_count,
                    "applications": listing.application_count,
                    "conversion_rate": listing.application_count / max(listing.view_count, 1),
                    "deadline": listing.application_deadline.isoformat()
                })

            return PartnerAnalytics(
                partner_id=partner_id,
                period_start=period_start,
                period_end=period_end,
                total_listings=len(partner_scholarships),
                active_listings=len([s for s in partner_scholarships if s.published]),
                total_views=total_views,
                total_applications=total_applications,
                view_to_application_rate=view_to_application_rate,
                top_listings=top_listings_data
            )


        except Exception as e:
            logger.error(f"Failed to generate partner analytics: {str(e)}")
            raise

    async def create_support_ticket(
        self,
        partner_id: str,
        ticket_data: dict[str, Any]
    ) -> PartnerSupportTicket:
        """Create support ticket for partner"""
        try:
            partner = self.partners.get(partner_id)
            if not partner:
                raise ValueError("Partner not found")

            ticket_data["partner_id"] = partner_id
            ticket_data["created_by"] = partner.primary_contact_email

            ticket = PartnerSupportTicket(**ticket_data)

            # Auto-assign based on category and support tier
            support_tier = "pilot" if partner.pilot_program else "standard"
            ticket.assigned_to = await self._assign_support_ticket(ticket, support_tier)

            self.support_tickets[ticket.ticket_id] = ticket

            logger.info(f"Created support ticket: {ticket.subject} ({ticket.ticket_id})")
            return ticket

        except Exception as e:
            logger.error(f"Failed to create support ticket: {str(e)}")
            raise

    async def get_marketplace_metrics(self) -> dict[str, Any]:
        """Get overall B2B marketplace metrics"""
        try:
            total_partners = len(self.partners)
            active_partners = len([p for p in self.partners.values() if p.status == PartnerStatus.ACTIVE])
            total_listings = len(self.scholarships)
            published_listings = len([s for s in self.scholarships.values() if s.published])

            # Calculate partner distribution by type
            partner_type_distribution = {}
            for partner_type in PartnerType:
                count = len([p for p in self.partners.values() if p.partner_type == partner_type])
                partner_type_distribution[partner_type.value] = count

            # Calculate onboarding completion rates
            completed_onboarding = 0
            for _partner_id, steps in self.onboarding_steps.items():
                required_steps = [s for s in steps if s.required]
                completed_required = [s for s in required_steps if s.completed]
                if len(completed_required) == len(required_steps):
                    completed_onboarding += 1

            onboarding_completion_rate = (
                completed_onboarding / max(total_partners, 1)
            )

            return {
                "total_partners": total_partners,
                "active_partners": active_partners,
                "activation_rate": active_partners / max(total_partners, 1),
                "total_listings": total_listings,
                "published_listings": published_listings,
                "publishing_rate": published_listings / max(total_listings, 1),
                "partner_type_distribution": partner_type_distribution,
                "onboarding_completion_rate": onboarding_completion_rate,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get marketplace metrics: {str(e)}")
            raise

    async def _validate_step_completion(
        self,
        step: PartnerOnboardingStep,
        step_data: dict[str, Any]
    ) -> bool:
        """Validate onboarding step completion"""

        for rule in step.validation_rules:
            if rule == "required_fields":
                required_fields = ["organization_name", "primary_contact_email", "tax_id"]
                if not all(field in step_data and step_data[field] for field in required_fields):
                    return False

            elif rule == "email_format":
                email = step_data.get("primary_contact_email", "")
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                    return False

            elif rule == "agreement_acknowledged":
                if not step_data.get("agreement_acknowledged"):
                    return False

            elif rule == "listing_complete":
                required_listing_fields = ["title", "description", "award_amount", "application_deadline"]
                if not all(field in step_data and step_data[field] for field in required_listing_fields):
                    return False

        return True

    async def _validate_scholarship_data(self, scholarship: PartnerScholarship) -> bool:
        """Validate scholarship listing data"""

        # Check required fields
        if not all([scholarship.title, scholarship.description, scholarship.award_amount]):
            raise ValueError("Missing required scholarship fields")

        # Validate deadline is in future
        if scholarship.application_deadline <= datetime.utcnow():
            raise ValueError("Application deadline must be in the future")

        # Validate award amount
        if scholarship.award_amount <= 0:
            raise ValueError("Award amount must be positive")

        return True

    async def _check_onboarding_completion(self, partner_id: str):
        """Check if partner has completed required onboarding steps"""
        steps = self.onboarding_steps.get(partner_id, [])
        required_steps = [s for s in steps if s.required]
        completed_required = [s for s in required_steps if s.completed]

        if len(completed_required) == len(required_steps):
            # Mark partner as active
            partner = self.partners[partner_id]
            partner.status = PartnerStatus.ACTIVE
            partner.updated_at = datetime.utcnow()

            logger.info(f"Partner {partner_id} completed onboarding and is now active")

    async def _assign_support_ticket(self, ticket: PartnerSupportTicket, support_tier: str) -> str | None:
        """Auto-assign support ticket based on tier and category"""

        # In production, would have actual support agent assignment logic
        tier_config = SUPPORT_TIERS.get(support_tier, SUPPORT_TIERS["standard"])

        if tier_config["dedicated_support"]:
            return "dedicated_support_agent"
        return "general_support_queue"

    def get_partner_by_id(self, partner_id: str) -> Partner | None:
        """Get partner by ID"""
        return self.partners.get(partner_id)

    def get_partner_scholarships(self, partner_id: str) -> list[PartnerScholarship]:
        """Get all scholarships for a partner"""
        return [s for s in self.scholarships.values() if s.partner_id == partner_id]

    def get_partner_onboarding_steps(self, partner_id: str) -> list[PartnerOnboardingStep]:
        """Get onboarding steps for partner"""
        return self.onboarding_steps.get(partner_id, [])
