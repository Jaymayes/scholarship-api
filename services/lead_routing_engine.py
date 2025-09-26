"""
Lead Routing Engine
Automated lead assignment for aggressive B2B ARR execution

Features:
- Segment-based routing (University/Foundation/Corporate)
- Geography-based territory assignment
- ACV potential-based AE assignment
- Deal stage routing (AE vs Partner Success)
- Workload balancing and territory optimization
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)

class LeadSource(Enum):
    """Lead generation sources"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    REFERRAL = "referral"
    PARTNER = "partner"
    EVENT = "event"
    CONTENT = "content"
    PAID = "paid"

class LeadSegment(Enum):
    """Lead market segments"""
    UNIVERSITY = "university"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"

class LeadStage(Enum):
    """Lead progression stages"""
    MQL = "mql"  # Marketing Qualified Lead
    SQL = "sql"  # Sales Qualified Lead
    DEMO = "demo"  # Demo scheduled/completed
    PILOT = "pilot"  # Pilot program active
    CONTRACT = "contract"  # Contract negotiation
    PAID = "paid"  # Converted to paid tier

class AssignmentType(Enum):
    """Assignment type for routing decision"""
    AE = "account_executive"  # High-touch sales
    PARTNER_SUCCESS = "partner_success"  # Self-serve + support
    ENTERPRISE = "enterprise"  # Large deal specialist

class Territory(Enum):
    """Geographic territories"""
    NORTHEAST = "northeast"
    SOUTHEAST = "southeast"
    MIDWEST = "midwest"
    SOUTHWEST = "southwest"
    WEST = "west"
    CANADA = "canada"
    INTERNATIONAL = "international"

@dataclass
class Lead:
    """Lead record for routing"""
    lead_id: str
    organization_name: str
    contact_name: str
    contact_email: str
    contact_phone: str | None

    # Routing criteria
    segment: LeadSegment
    territory: Territory
    estimated_acv: Decimal
    employee_count: int | None
    annual_budget: Decimal | None

    # Lead details
    source: LeadSource
    stage: LeadStage
    urgency_score: int  # 1-10 scale
    fit_score: int  # 1-10 scale (ideal customer profile)

    # Assignment
    assigned_to: str | None = None
    assignment_type: AssignmentType | None = None
    assigned_at: datetime | None = None

    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime | None = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        pass  # Notes list is now handled by field(default_factory=list)

@dataclass
class SalesRep:
    """Sales representative for assignment"""
    rep_id: str
    name: str
    email: str
    role: AssignmentType

    # Territory and specialization
    territories: list[Territory]
    segments: list[LeadSegment]
    max_acv: Decimal | None = None
    min_acv: Decimal | None = None

    # Capacity management
    current_leads: int = 0
    max_leads: int = 50
    quota_attainment: float = 0.0  # Percentage

    # Performance metrics
    conversion_rate: float = 0.0
    avg_deal_size: Decimal = Decimal('0')
    avg_sales_cycle: int = 90  # days

    # Availability
    active: bool = True
    vacation_until: datetime | None = None

@dataclass
class RoutingRule:
    """Lead routing rule definition"""
    rule_id: str
    name: str
    description: str
    priority: int  # Lower number = higher priority

    # Conditions
    segments: list[LeadSegment]
    territories: list[Territory]
    assignment_type: AssignmentType  # Moved before default fields

    # Optional conditions
    min_acv: Decimal | None = None
    max_acv: Decimal | None = None
    min_urgency: int | None = None
    min_fit_score: int | None = None
    sources: list[LeadSource] = field(default_factory=list)
    specific_reps: list[str] = field(default_factory=list)  # If empty, use round-robin
    active: bool = True

    def __post_init__(self):
        pass  # Lists are now handled by field(default_factory=list)

class LeadRoutingEngine:
    """
    Comprehensive Lead Routing Engine for B2B Sales Operations

    Automatically assigns leads based on:
    - Market segment and territory
    - ACV potential and deal complexity
    - Rep specialization and capacity
    - Performance-based routing
    """

    def __init__(self):
        # In-memory storage for MVP (would be database in production)
        self.leads: dict[str, Lead] = {}
        self.sales_reps: dict[str, SalesRep] = {}
        self.routing_rules: list[RoutingRule] = []

        # Initialize default sales team and routing rules
        self._initialize_sales_team()
        self._initialize_routing_rules()

        logger.info("🎯 Lead Routing Engine initialized")
        logger.info(f"👥 Sales team: {len(self.sales_reps)} reps")
        logger.info(f"📋 Routing rules: {len(self.routing_rules)} rules")

    def _initialize_sales_team(self):
        """Initialize sales team with territories and specializations"""

        # Account Executives for high-touch enterprise deals
        self.sales_reps["ae_001"] = SalesRep(
            rep_id="ae_001",
            name="Sarah Chen",
            email="sarah.chen@company.com",
            role=AssignmentType.AE,
            territories=[Territory.NORTHEAST, Territory.SOUTHEAST],
            segments=[LeadSegment.UNIVERSITY, LeadSegment.FOUNDATION],
            min_acv=Decimal('15000'),
            max_acv=Decimal('100000'),
            max_leads=30,
            conversion_rate=0.25,
            avg_deal_size=Decimal('35000'),
            avg_sales_cycle=75
        )

        self.sales_reps["ae_002"] = SalesRep(
            rep_id="ae_002",
            name="Marcus Rodriguez",
            email="marcus.rodriguez@company.com",
            role=AssignmentType.AE,
            territories=[Territory.MIDWEST, Territory.SOUTHWEST],
            segments=[LeadSegment.CORPORATE, LeadSegment.NONPROFIT],
            min_acv=Decimal('20000'),
            max_acv=Decimal('150000'),
            max_leads=25,
            conversion_rate=0.30,
            avg_deal_size=Decimal('45000'),
            avg_sales_cycle=85
        )

        self.sales_reps["ae_003"] = SalesRep(
            rep_id="ae_003",
            name="Jennifer Park",
            email="jennifer.park@company.com",
            role=AssignmentType.AE,
            territories=[Territory.WEST, Territory.CANADA],
            segments=[LeadSegment.UNIVERSITY, LeadSegment.CORPORATE],
            min_acv=Decimal('25000'),
            max_acv=Decimal('200000'),
            max_leads=20,
            conversion_rate=0.35,
            avg_deal_size=Decimal('55000'),
            avg_sales_cycle=95
        )

        # Enterprise AE for large deals
        self.sales_reps["enterprise_001"] = SalesRep(
            rep_id="enterprise_001",
            name="David Kim",
            email="david.kim@company.com",
            role=AssignmentType.ENTERPRISE,
            territories=[Territory.NORTHEAST, Territory.WEST, Territory.INTERNATIONAL],
            segments=[LeadSegment.UNIVERSITY, LeadSegment.FOUNDATION, LeadSegment.CORPORATE],
            min_acv=Decimal('100000'),
            max_leads=10,
            conversion_rate=0.40,
            avg_deal_size=Decimal('250000'),
            avg_sales_cycle=150
        )

        # Partner Success for self-serve and expansion
        self.sales_reps["ps_001"] = SalesRep(
            rep_id="ps_001",
            name="Amanda Foster",
            email="amanda.foster@company.com",
            role=AssignmentType.PARTNER_SUCCESS,
            territories=[Territory.NORTHEAST, Territory.SOUTHEAST, Territory.MIDWEST],
            segments=[LeadSegment.FOUNDATION, LeadSegment.NONPROFIT],
            max_acv=Decimal('25000'),
            max_leads=75,
            conversion_rate=0.45,
            avg_deal_size=Decimal('12000'),
            avg_sales_cycle=45
        )

        self.sales_reps["ps_002"] = SalesRep(
            rep_id="ps_002",
            name="Carlos Silva",
            email="carlos.silva@company.com",
            role=AssignmentType.PARTNER_SUCCESS,
            territories=[Territory.SOUTHWEST, Territory.WEST, Territory.CANADA],
            segments=[LeadSegment.CORPORATE, LeadSegment.GOVERNMENT],
            max_acv=Decimal('30000'),
            max_leads=60,
            conversion_rate=0.40,
            avg_deal_size=Decimal('15000'),
            avg_sales_cycle=50
        )

    def _initialize_routing_rules(self):
        """Initialize lead routing rules with priority order"""

        # Rule 1: Enterprise deals (>$100k ACV) → Enterprise AE
        self.routing_rules.append(RoutingRule(
            rule_id="enterprise_high_acv",
            name="Enterprise High ACV",
            description="Route high-value deals (>$100k ACV) to Enterprise AE",
            priority=1,
            segments=[LeadSegment.UNIVERSITY, LeadSegment.FOUNDATION, LeadSegment.CORPORATE],
            territories=list(Territory),
            min_acv=Decimal('100000'),
            assignment_type=AssignmentType.ENTERPRISE,
            specific_reps=["enterprise_001"]
        ))

        # Rule 2: High urgency university leads → Specialized AE
        self.routing_rules.append(RoutingRule(
            rule_id="urgent_university",
            name="Urgent University Leads",
            description="Route urgent university leads to specialized AE",
            priority=2,
            segments=[LeadSegment.UNIVERSITY],
            territories=list(Territory),
            min_acv=Decimal('15000'),
            min_urgency=8,
            min_fit_score=7,
            assignment_type=AssignmentType.AE
        ))

        # Rule 3: Mid-market corporate deals ($20k-$100k) → Corporate AE
        self.routing_rules.append(RoutingRule(
            rule_id="midmarket_corporate",
            name="Mid-Market Corporate",
            description="Route mid-market corporate deals to specialized AE",
            priority=3,
            segments=[LeadSegment.CORPORATE],
            territories=list(Territory),
            min_acv=Decimal('20000'),
            max_acv=Decimal('99999'),
            assignment_type=AssignmentType.AE
        ))

        # Rule 4: Foundation leads with high fit → Foundation specialist
        self.routing_rules.append(RoutingRule(
            rule_id="foundation_specialist",
            name="Foundation Specialist",
            description="Route foundation leads to foundation specialist",
            priority=4,
            segments=[LeadSegment.FOUNDATION],
            territories=list(Territory),
            min_acv=Decimal('10000'),
            min_fit_score=6,
            assignment_type=AssignmentType.AE
        ))

        # Rule 5: Small deals and self-serve → Partner Success
        self.routing_rules.append(RoutingRule(
            rule_id="self_serve_small",
            name="Self-Serve Small Deals",
            description="Route small deals to Partner Success for self-serve",
            priority=5,
            segments=list(LeadSegment),
            territories=list(Territory),
            max_acv=Decimal('25000'),
            assignment_type=AssignmentType.PARTNER_SUCCESS
        ))

        # Rule 6: Default fallback → Round-robin AE assignment
        self.routing_rules.append(RoutingRule(
            rule_id="default_fallback",
            name="Default Fallback",
            description="Default round-robin assignment for unmatched leads",
            priority=10,
            segments=list(LeadSegment),
            territories=list(Territory),
            assignment_type=AssignmentType.AE
        ))

    def route_lead(self, lead_data: dict[str, Any]) -> tuple[Lead, SalesRep, str]:
        """
        Route incoming lead to appropriate sales rep

        Returns: (Lead, assigned_rep, routing_reason)
        """
        try:
            # Create lead record
            lead = Lead(
                lead_id=lead_data.get('lead_id', str(uuid.uuid4())),
                organization_name=lead_data['organization_name'],
                contact_name=lead_data['contact_name'],
                contact_email=lead_data['contact_email'],
                contact_phone=lead_data.get('contact_phone'),
                segment=LeadSegment(lead_data['segment']),
                territory=Territory(lead_data['territory']),
                estimated_acv=Decimal(str(lead_data['estimated_acv'])),
                employee_count=lead_data.get('employee_count'),
                annual_budget=Decimal(str(lead_data['annual_budget'])) if lead_data.get('annual_budget') else None,
                source=LeadSource(lead_data['source']),
                stage=LeadStage(lead_data['stage']),
                urgency_score=lead_data['urgency_score'],
                fit_score=lead_data['fit_score'],
                created_at=datetime.utcnow()
            )

            # Find matching routing rule
            assigned_rep, routing_reason = self._find_best_assignment(lead)

            # Assign lead
            if assigned_rep:
                lead.assigned_to = assigned_rep.rep_id
                lead.assignment_type = assigned_rep.role
                lead.assigned_at = datetime.utcnow()

                # Update rep's lead count
                assigned_rep.current_leads += 1

                # Store lead
                self.leads[lead.lead_id] = lead

                logger.info(f"🎯 Lead routed: {lead.organization_name} → {assigned_rep.name} ({routing_reason})")
                logger.info(f"💰 ACV: ${lead.estimated_acv:,.0f} | Segment: {lead.segment.value} | Territory: {lead.territory.value}")

                return lead, assigned_rep, routing_reason
            raise ValueError("No available sales rep found for assignment")

        except Exception as e:
            logger.error(f"Failed to route lead: {str(e)}")
            raise

    def _find_best_assignment(self, lead: Lead) -> tuple[SalesRep | None, str]:
        """Find the best sales rep assignment for a lead"""

        # Sort routing rules by priority
        sorted_rules = sorted(self.routing_rules, key=lambda r: r.priority)

        for rule in sorted_rules:
            if not rule.active:
                continue

            # Check if lead matches rule conditions
            if self._lead_matches_rule(lead, rule):
                # Find available rep for this rule
                rep = self._find_available_rep(lead, rule)
                if rep:
                    return rep, f"Rule: {rule.name}"

        return None, "No matching rule found"

    def _lead_matches_rule(self, lead: Lead, rule: RoutingRule) -> bool:
        """Check if lead matches routing rule conditions"""

        # Check segment
        if rule.segments and lead.segment not in rule.segments:
            return False

        # Check territory
        if rule.territories and lead.territory not in rule.territories:
            return False

        # Check ACV range
        if rule.min_acv and lead.estimated_acv < rule.min_acv:
            return False
        if rule.max_acv and lead.estimated_acv > rule.max_acv:
            return False

        # Check urgency
        if rule.min_urgency and lead.urgency_score < rule.min_urgency:
            return False

        # Check fit score
        if rule.min_fit_score and lead.fit_score < rule.min_fit_score:
            return False

        # Check source
        return not (rule.sources and lead.source not in rule.sources)

    def _find_available_rep(self, lead: Lead, rule: RoutingRule) -> SalesRep | None:
        """Find available sales rep matching rule criteria"""

        # Get eligible reps
        eligible_reps = []

        if rule.specific_reps:
            # Use specific reps if defined
            eligible_reps = [self.sales_reps[rep_id] for rep_id in rule.specific_reps
                           if rep_id in self.sales_reps]
        else:
            # Find reps matching assignment type and other criteria
            for rep in self.sales_reps.values():
                if (rep.role == rule.assignment_type and
                    self._rep_can_handle_lead(rep, lead)):
                    eligible_reps.append(rep)

        if not eligible_reps:
            return None

        # Filter by availability and capacity
        available_reps = [rep for rep in eligible_reps if self._rep_is_available(rep)]

        if not available_reps:
            # If no fully available reps, use least loaded
            available_reps = eligible_reps

        # Select best rep using round-robin with performance weighting
        return self._select_best_rep(available_reps, lead)

    def _rep_can_handle_lead(self, rep: SalesRep, lead: Lead) -> bool:
        """Check if rep can handle the specific lead"""

        # Check territory coverage
        if rep.territories and lead.territory not in rep.territories:
            return False

        # Check segment specialization
        if rep.segments and lead.segment not in rep.segments:
            return False

        # Check ACV range
        if rep.min_acv and lead.estimated_acv < rep.min_acv:
            return False
        return not (rep.max_acv and lead.estimated_acv > rep.max_acv)

    def _rep_is_available(self, rep: SalesRep) -> bool:
        """Check if rep is available for new assignments"""

        # Check if active
        if not rep.active:
            return False

        # Check vacation status
        if rep.vacation_until and rep.vacation_until > datetime.utcnow():
            return False

        # Check capacity
        return not rep.current_leads >= rep.max_leads

    def _select_best_rep(self, reps: list[SalesRep], lead: Lead) -> SalesRep:
        """Select the best rep from available options"""

        # Score reps based on performance and capacity
        scored_reps = []

        for rep in reps:
            # Base score from performance metrics
            performance_score = (rep.conversion_rate * 0.4 +
                               (rep.quota_attainment / 100) * 0.3 +
                               (1 - rep.current_leads / rep.max_leads) * 0.3)

            # Bonus for segment/territory specialization
            specialization_bonus = 0
            if rep.segments and lead.segment in rep.segments:
                specialization_bonus += 0.1
            if rep.territories and lead.territory in rep.territories:
                specialization_bonus += 0.1

            total_score = performance_score + specialization_bonus
            scored_reps.append((rep, total_score))

        # Sort by score (highest first)
        scored_reps.sort(key=lambda x: x[1], reverse=True)

        return scored_reps[0][0]

    def reassign_lead(self, lead_id: str, new_rep_id: str, reason: str) -> Lead:
        """Reassign lead to different sales rep"""
        try:
            lead = self.leads.get(lead_id)
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            new_rep = self.sales_reps.get(new_rep_id)
            if not new_rep:
                raise ValueError(f"Sales rep {new_rep_id} not found")

            # Update old rep's count
            if lead.assigned_to:
                old_rep = self.sales_reps.get(lead.assigned_to)
                if old_rep:
                    old_rep.current_leads = max(0, old_rep.current_leads - 1)

            # Assign to new rep
            lead.assigned_to = new_rep.rep_id
            lead.assignment_type = new_rep.role
            lead.assigned_at = datetime.utcnow()
            lead.notes.append(f"Reassigned to {new_rep.name}: {reason}")

            # Update new rep's count
            new_rep.current_leads += 1

            logger.info(f"🔄 Lead reassigned: {lead.organization_name} → {new_rep.name} ({reason})")
            return lead

        except Exception as e:
            logger.error(f"Failed to reassign lead: {str(e)}")
            raise

    def get_routing_analytics(self) -> dict[str, Any]:
        """Get comprehensive routing analytics"""
        try:
            total_leads = len(self.leads)
            assigned_leads = len([l for l in self.leads.values() if l.assigned_to])

            # Lead distribution by segment
            segment_distribution = {}
            for segment in LeadSegment:
                count = len([l for l in self.leads.values() if l.segment == segment])
                segment_distribution[segment.value] = count

            # Lead distribution by assignment type
            assignment_distribution = {}
            for assignment_type in AssignmentType:
                count = len([l for l in self.leads.values() if l.assignment_type == assignment_type])
                assignment_distribution[assignment_type.value] = count

            # Rep performance metrics
            rep_metrics = {}
            for rep in self.sales_reps.values():
                rep_leads = [l for l in self.leads.values() if l.assigned_to == rep.rep_id]
                total_acv = sum(l.estimated_acv for l in rep_leads)

                rep_metrics[rep.rep_id] = {
                    "name": rep.name,
                    "role": rep.role.value,
                    "current_leads": rep.current_leads,
                    "capacity_utilization": rep.current_leads / rep.max_leads,
                    "total_pipeline_acv": float(total_acv),
                    "avg_acv_per_lead": float(total_acv / max(len(rep_leads), 1)),
                    "conversion_rate": rep.conversion_rate,
                    "quota_attainment": rep.quota_attainment
                }

            # Territory distribution
            territory_distribution = {}
            for territory in Territory:
                count = len([l for l in self.leads.values() if l.territory == territory])
                territory_distribution[territory.value] = count

            return {
                "summary": {
                    "total_leads": total_leads,
                    "assigned_leads": assigned_leads,
                    "assignment_rate": assigned_leads / max(total_leads, 1),
                    "avg_acv": float(sum(l.estimated_acv for l in self.leads.values()) / max(total_leads, 1)),
                    "total_pipeline_value": float(sum(l.estimated_acv for l in self.leads.values()))
                },
                "distributions": {
                    "by_segment": segment_distribution,
                    "by_assignment_type": assignment_distribution,
                    "by_territory": territory_distribution
                },
                "rep_performance": rep_metrics,
                "routing_rules": len([r for r in self.routing_rules if r.active]),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate routing analytics: {str(e)}")
            raise

    def update_rep_performance(self, rep_id: str, performance_data: dict[str, Any]):
        """Update sales rep performance metrics"""
        try:
            rep = self.sales_reps.get(rep_id)
            if not rep:
                raise ValueError(f"Sales rep {rep_id} not found")

            # Update performance metrics
            if 'conversion_rate' in performance_data:
                rep.conversion_rate = performance_data['conversion_rate']
            if 'quota_attainment' in performance_data:
                rep.quota_attainment = performance_data['quota_attainment']
            if 'avg_deal_size' in performance_data:
                rep.avg_deal_size = Decimal(str(performance_data['avg_deal_size']))
            if 'avg_sales_cycle' in performance_data:
                rep.avg_sales_cycle = performance_data['avg_sales_cycle']

            logger.info(f"📊 Updated performance metrics for {rep.name}")

        except Exception as e:
            logger.error(f"Failed to update rep performance: {str(e)}")
            raise


# Global service instance
lead_routing_engine = LeadRoutingEngine()
