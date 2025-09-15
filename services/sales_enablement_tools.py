"""
Sales Enablement Tools
Comprehensive toolkit for AE and Partner Success teams to accelerate B2B sales cycles

Features:
- ROI calculators for value-based selling
- Competitive battle cards and positioning
- Dynamic pricing guidelines and negotiation strategies
- Contract templates and legal frameworks
- Sales collateral and presentation tools
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

from utils.logger import get_logger

logger = get_logger(__name__)

class CompetitorType(Enum):
    """Types of competitive threats"""
    DIRECT = "direct"           # Direct scholarship platform competitors
    INDIRECT = "indirect"       # Adjacent solutions (CRM, marketing)
    INTERNAL = "internal"       # Internal/manual processes
    LEGACY = "legacy"          # Legacy systems being replaced

class ROIMetric(Enum):
    """ROI calculation metrics"""
    TIME_SAVINGS = "time_savings"
    COST_REDUCTION = "cost_reduction"
    EFFICIENCY_GAIN = "efficiency_gain"
    REVENUE_INCREASE = "revenue_increase"
    QUALITY_IMPROVEMENT = "quality_improvement"

class ContractType(Enum):
    """Contract template types"""
    PILOT = "pilot"
    ANNUAL = "annual"
    MULTI_YEAR = "multi_year"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"

@dataclass
class ROICalculation:
    """ROI calculation for prospect value demonstration"""
    calculation_id: str
    prospect_name: str
    segment: str  # university, foundation, corporate
    
    # Current state inputs
    annual_scholarship_budget: Decimal
    scholarships_managed: int
    staff_hours_per_month: int
    hourly_rate: Decimal
    application_volume: int
    
    # Solution impact
    time_savings_percentage: float  # 0-100%
    efficiency_gain_percentage: float  # 0-100%
    application_increase_percentage: float  # 0-100%
    cost_reduction_percentage: float  # 0-100%
    
    # ROI calculations
    annual_time_savings_hours: float = 0
    annual_cost_savings: Decimal = field(default_factory=lambda: Decimal('0'))
    annual_efficiency_value: Decimal = field(default_factory=lambda: Decimal('0'))
    total_annual_value: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # Investment
    annual_platform_cost: Decimal = field(default_factory=lambda: Decimal('0'))
    implementation_cost: Decimal = field(default_factory=lambda: Decimal('0'))
    total_investment: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # ROI metrics
    net_annual_benefit: Decimal = field(default_factory=lambda: Decimal('0'))
    roi_percentage: float = 0
    payback_months: float = 0
    
    # Presentation data
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    presentation_notes: str = ""

@dataclass
class BattleCard:
    """Competitive battle card for sales positioning"""
    card_id: str
    competitor_name: str
    competitor_type: CompetitorType
    
    # Competitor overview
    market_position: str
    target_segments: List[str]
    pricing_model: str
    key_strengths: List[str]
    key_weaknesses: List[str]
    
    # Competitive positioning
    our_advantages: List[str]
    differentiation_points: List[str]
    win_strategies: List[str]
    
    # Common objections and responses
    objections_responses: Dict[str, str] = field(default_factory=dict)
    
    # Proof points and references
    competitive_wins: List[str] = field(default_factory=list)
    case_studies: List[str] = field(default_factory=list)
    
    # Pricing and negotiation
    pricing_comparison: Dict[str, Any] = field(default_factory=dict)
    negotiation_tactics: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = ""
    usage_count: int = 0

@dataclass
class PricingGuideline:
    """Dynamic pricing guidelines for negotiation"""
    guideline_id: str
    segment: str  # university, foundation, corporate
    tier: str     # listings_promotion, recruitment_dashboard, analytics
    
    # Pricing structure
    list_price: Decimal
    standard_discount_range: Tuple[float, float]  # (min%, max%)
    volume_discount_tiers: Dict[int, float] = field(default_factory=dict)
    
    # Negotiation parameters
    minimum_acceptable_price: Decimal = field(default_factory=lambda: Decimal('0'))
    approval_required_below: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # Value-based pricing factors
    value_multipliers: Dict[str, float] = field(default_factory=dict)
    competitive_positioning: Dict[str, Decimal] = field(default_factory=dict)
    
    # Contract terms
    payment_terms: List[str] = field(default_factory=list)
    contract_length_options: List[int] = field(default_factory=list)  # months
    renewal_terms: str = ""
    
    # Special considerations
    pilot_pricing: Optional[Decimal] = None
    nonprofit_discount: Optional[float] = None
    multi_year_discount: Optional[float] = None
    
    # Metadata
    effective_date: datetime = field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None
    approval_level: str = "standard"  # standard, manager, director

@dataclass
class ContractTemplate:
    """Legal contract templates for different deal types"""
    template_id: str
    template_name: str
    contract_type: ContractType
    target_segment: str
    
    # Template content
    template_text: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    
    # Legal terms
    standard_terms: Dict[str, str] = field(default_factory=dict)
    negotiable_terms: List[str] = field(default_factory=list)
    non_negotiable_terms: List[str] = field(default_factory=list)
    
    # Pricing integration
    pricing_sections: List[str] = field(default_factory=list)
    discount_clauses: List[str] = field(default_factory=list)
    
    # Approval workflow
    approval_required: bool = True
    approver_roles: List[str] = field(default_factory=list)
    
    # Version control
    version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.utcnow)
    legal_review_date: Optional[datetime] = None

class SalesEnablementToolkit:
    """
    Comprehensive Sales Enablement Toolkit
    
    Provides sales teams with:
    - Dynamic ROI calculators for value demonstration
    - Competitive battle cards and positioning
    - Pricing guidelines and negotiation strategies
    - Contract templates and legal frameworks
    """
    
    def __init__(self):
        # In-memory storage for MVP (would be database in production)
        self.roi_calculations: Dict[str, ROICalculation] = {}
        self.battle_cards: Dict[str, BattleCard] = {}
        self.pricing_guidelines: Dict[str, PricingGuideline] = {}
        self.contract_templates: Dict[str, ContractTemplate] = {}
        
        # Initialize default content
        self._initialize_battle_cards()
        self._initialize_pricing_guidelines()
        self._initialize_contract_templates()
        
        logger.info("🛠️ Sales Enablement Toolkit initialized")
        logger.info(f"⚔️ Battle cards: {len(self.battle_cards)}")
        logger.info(f"💰 Pricing guidelines: {len(self.pricing_guidelines)}")
        logger.info(f"📄 Contract templates: {len(self.contract_templates)}")
    
    def _initialize_battle_cards(self):
        """Initialize competitive battle cards"""
        
        # Competitor 1: Generic Scholarship Platform
        generic_platform = BattleCard(
            card_id="comp_generic_platform",
            competitor_name="Generic Scholarship Platform",
            competitor_type=CompetitorType.DIRECT,
            market_position="Mid-market general scholarship platform",
            target_segments=["university", "foundation"],
            pricing_model="Per-listing pricing with basic analytics",
            key_strengths=[
                "Lower entry-level pricing",
                "Simple setup process",
                "Basic scholarship management"
            ],
            key_weaknesses=[
                "Limited analytics and reporting",
                "No predictive matching capabilities",
                "Minimal customization options",
                "Basic support infrastructure",
                "No B2B partner marketplace features"
            ],
            our_advantages=[
                "Advanced AI-powered matching algorithm",
                "Comprehensive analytics and ROI tracking",
                "B2B partner marketplace with network effects",
                "Enterprise-grade security and compliance",
                "Dedicated customer success management"
            ],
            differentiation_points=[
                "Predictive student matching increases application quality by 40%",
                "B2B marketplace drives organic growth and reduces CAC",
                "Enterprise analytics provide actionable insights for program optimization",
                "White-label options for institutional branding"
            ],
            win_strategies=[
                "Demonstrate ROI through advanced analytics and matching",
                "Highlight marketplace network effects and partnership opportunities",
                "Emphasize enterprise security and compliance capabilities",
                "Show superior customer success and support model"
            ],
            objections_responses={
                "Too expensive": "Our platform delivers 3-5x ROI through improved matching efficiency and reduced administrative overhead. The advanced features pay for themselves through better outcomes.",
                "Too complex": "We provide comprehensive onboarding and dedicated customer success support. Most clients are fully operational within 2 weeks with ongoing guidance.",
                "Happy with current solution": "Let's discuss the specific challenges and growth goals. Our clients typically see 40% improvement in application quality and 60% reduction in administrative time."
            },
            competitive_wins=[
                "Won $150k university deal by demonstrating superior analytics",
                "Displaced competitor at major foundation through marketplace value",
                "Converted enterprise client with compliance and security capabilities"
            ],
            pricing_comparison={
                "their_entry_price": "$299/month",
                "our_comparable_price": "$499/month",
                "value_justification": "67% price premium justified by 3x ROI and advanced features"
            },
            negotiation_tactics=[
                "Focus on total cost of ownership and efficiency gains",
                "Highlight unique marketplace and network benefits",
                "Offer pilot program to demonstrate value",
                "Bundle analytics package for comprehensive solution"
            ]
        )
        
        self.battle_cards[generic_platform.card_id] = generic_platform
        
        # Competitor 2: Legacy CRM/Manual Process
        legacy_crm = BattleCard(
            card_id="comp_legacy_manual",
            competitor_name="Legacy CRM / Manual Process",
            competitor_type=CompetitorType.INTERNAL,
            market_position="Internal manual processes or basic CRM",
            target_segments=["all"],
            pricing_model="Internal staff time and basic software licenses",
            key_strengths=[
                "No additional software costs",
                "Complete control over process",
                "Familiar to existing staff"
            ],
            key_weaknesses=[
                "Extremely time-intensive and manual",
                "No analytics or optimization capabilities",
                "High error rates and inconsistency",
                "No scalability for growth",
                "No student matching or discovery features"
            ],
            our_advantages=[
                "Automated workflows reduce manual work by 70%",
                "AI-powered matching improves application quality",
                "Real-time analytics and reporting",
                "Scalable infrastructure for growth",
                "Professional scholarship marketplace presence"
            ],
            differentiation_points=[
                "Transform from reactive to proactive scholarship management",
                "Professional online presence increases application volume",
                "Analytics provide insights impossible with manual tracking",
                "Automation frees staff for strategic work"
            ],
            win_strategies=[
                "Calculate time savings and opportunity cost of manual processes",
                "Demonstrate professional presence and branding benefits",
                "Show analytics insights that enable program optimization",
                "Emphasize scalability for organizational growth"
            ],
            objections_responses={
                "Current process works fine": "While it may work, are you maximizing your impact? Our platform typically increases qualified applications by 50% while reducing administrative time by 70%.",
                "Too much change": "We handle the transition with dedicated support. Most of the setup is automated, and staff training takes just a few hours.",
                "Budget constraints": "The efficiency gains typically pay for the platform within 3 months. We can also start with a pilot to demonstrate value."
            }
        )
        
        self.battle_cards[legacy_crm.card_id] = legacy_crm
    
    def _initialize_pricing_guidelines(self):
        """Initialize pricing guidelines for different segments and tiers"""
        
        # University segment - Listings + Promotion tier
        univ_listings = PricingGuideline(
            guideline_id="univ_listings_pricing",
            segment="university",
            tier="listings_promotion",
            list_price=Decimal('499'),
            standard_discount_range=(10.0, 20.0),  # 10-20% standard discount
            volume_discount_tiers={
                5: 5.0,   # 5+ scholarships = 5% additional discount
                10: 10.0, # 10+ scholarships = 10% additional discount
                20: 15.0  # 20+ scholarships = 15% additional discount
            },
            minimum_acceptable_price=Decimal('349'),  # 30% max discount
            approval_required_below=Decimal('399'),   # Manager approval below 20%
            value_multipliers={
                "high_volume_scholarships": 1.2,
                "premium_branding": 1.1,
                "analytics_focus": 1.15
            },
            payment_terms=["Net 30", "Quarterly in advance", "Annual in advance"],
            contract_length_options=[12, 24, 36],
            pilot_pricing=Decimal('299'),  # 40% discount for pilot
            nonprofit_discount=15.0,       # 15% for verified nonprofits
            multi_year_discount=10.0       # 10% for 2+ year agreements
        )
        
        self.pricing_guidelines[univ_listings.guideline_id] = univ_listings
        
        # Foundation segment - Recruitment Dashboard tier
        found_dashboard = PricingGuideline(
            guideline_id="found_dashboard_pricing",
            segment="foundation",
            tier="recruitment_dashboard",
            list_price=Decimal('1499'),
            standard_discount_range=(5.0, 15.0),
            volume_discount_tiers={
                3: 5.0,
                10: 10.0,
                25: 20.0
            },
            minimum_acceptable_price=Decimal('1049'),  # 30% max discount
            approval_required_below=Decimal('1274'),   # Manager approval below 15%
            competitive_positioning={
                "vs_generic_platform": Decimal('899'),    # Competitor pricing
                "vs_manual_process": Decimal('0')         # Internal cost
            },
            payment_terms=["Net 30", "Quarterly in advance", "Annual in advance"],
            nonprofit_discount=10.0,
            multi_year_discount=15.0
        )
        
        self.pricing_guidelines[found_dashboard.guideline_id] = found_dashboard
        
        # Corporate segment - Enterprise Analytics tier
        corp_analytics = PricingGuideline(
            guideline_id="corp_analytics_pricing",
            segment="corporate",
            tier="anonymized_analytics",
            list_price=Decimal('2999'),
            standard_discount_range=(0.0, 10.0),  # Less discounting for enterprise
            volume_discount_tiers={
                5: 5.0,
                15: 10.0,
                50: 15.0
            },
            minimum_acceptable_price=Decimal('2399'),  # 20% max discount
            approval_required_below=Decimal('2699'),   # Director approval below 10%
            value_multipliers={
                "enterprise_compliance": 1.3,
                "white_label": 1.25,
                "api_access": 1.2,
                "dedicated_support": 1.15
            },
            payment_terms=["Net 30", "Quarterly in advance", "Annual in advance"],
            contract_length_options=[12, 24, 36, 60],
            multi_year_discount=20.0,  # Higher discount for enterprise multi-year
            approval_level="director"
        )
        
        self.pricing_guidelines[corp_analytics.guideline_id] = corp_analytics
    
    def _initialize_contract_templates(self):
        """Initialize contract templates for different deal types"""
        
        # Pilot Agreement Template
        pilot_template = ContractTemplate(
            template_id="pilot_agreement_v1",
            template_name="Pilot Program Agreement",
            contract_type=ContractType.PILOT,
            target_segment="all",
            template_text="""
PILOT PROGRAM AGREEMENT

This Pilot Program Agreement ("Agreement") is entered into between [CUSTOMER_NAME] ("Customer") and Scholarship Discovery Platform, Inc. ("Provider") on [DATE].

PILOT TERMS:
- Duration: [PILOT_DURATION] months
- Start Date: [START_DATE]
- End Date: [END_DATE]
- Pilot Scope: [PILOT_SCOPE]

SUCCESS CRITERIA:
[SUCCESS_CRITERIA]

PRICING:
- Pilot Fee: $[PILOT_PRICE]
- Payment Terms: [PAYMENT_TERMS]

CONVERSION TERMS:
- Conversion Deadline: [CONVERSION_DEADLINE]
- Full Contract Terms: [FULL_CONTRACT_TERMS]
- Pilot Credit: $[PILOT_CREDIT] toward full contract

TERMINATION:
Either party may terminate with [TERMINATION_NOTICE] days notice.

[STANDARD_LEGAL_TERMS]
            """,
            required_fields=[
                "CUSTOMER_NAME", "DATE", "PILOT_DURATION", "START_DATE", 
                "END_DATE", "PILOT_SCOPE", "SUCCESS_CRITERIA", "PILOT_PRICE"
            ],
            optional_fields=[
                "PAYMENT_TERMS", "CONVERSION_DEADLINE", "PILOT_CREDIT"
            ],
            standard_terms={
                "pilot_duration": "3 months",
                "termination_notice": "30 days",
                "payment_terms": "Net 30"
            },
            negotiable_terms=[
                "pilot_duration", "success_criteria", "pilot_price", "conversion_terms"
            ],
            non_negotiable_terms=[
                "intellectual_property", "data_security", "liability_limitations"
            ],
            approver_roles=["sales_manager"]
        )
        
        self.contract_templates[pilot_template.template_id] = pilot_template
        
        # Annual Service Agreement Template
        annual_template = ContractTemplate(
            template_id="annual_service_agreement_v1",
            template_name="Annual Service Agreement",
            contract_type=ContractType.ANNUAL,
            target_segment="all",
            template_text="""
ANNUAL SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into between [CUSTOMER_NAME] ("Customer") and Scholarship Discovery Platform, Inc. ("Provider") on [DATE].

SERVICE DETAILS:
- Service Tier: [SERVICE_TIER]
- Contract Term: [CONTRACT_TERM] months
- Start Date: [START_DATE]
- End Date: [END_DATE]

PRICING AND PAYMENT:
- Annual Fee: $[ANNUAL_FEE]
- Payment Schedule: [PAYMENT_SCHEDULE]
- Discount Applied: [DISCOUNT_PERCENTAGE]%

SERVICES INCLUDED:
[SERVICES_INCLUDED]

SUPPORT LEVEL:
[SUPPORT_LEVEL]

RENEWAL TERMS:
[RENEWAL_TERMS]

[STANDARD_LEGAL_TERMS]
            """,
            required_fields=[
                "CUSTOMER_NAME", "DATE", "SERVICE_TIER", "CONTRACT_TERM",
                "START_DATE", "END_DATE", "ANNUAL_FEE", "SERVICES_INCLUDED"
            ],
            standard_terms={
                "contract_term": "12 months",
                "payment_schedule": "Annual in advance",
                "renewal_terms": "Auto-renew unless 60 days notice"
            },
            negotiable_terms=[
                "payment_schedule", "discount_percentage", "support_level", "renewal_terms"
            ],
            approver_roles=["sales_manager", "legal"]
        )
        
        self.contract_templates[annual_template.template_id] = annual_template
        
        # Enterprise Agreement Template
        enterprise_template = ContractTemplate(
            template_id="enterprise_agreement_v1",
            template_name="Enterprise Service Agreement",
            contract_type=ContractType.ENTERPRISE,
            target_segment="corporate",
            template_text="""
ENTERPRISE SERVICE AGREEMENT

This Enterprise Service Agreement ("Agreement") is entered into between [CUSTOMER_NAME] ("Customer") and Scholarship Discovery Platform, Inc. ("Provider") on [DATE].

ENTERPRISE SERVICES:
- Service Package: [SERVICE_PACKAGE]
- Contract Term: [CONTRACT_TERM] months
- Dedicated Support: [DEDICATED_SUPPORT]
- SLA Commitments: [SLA_COMMITMENTS]

PRICING:
- Annual Fee: $[ANNUAL_FEE]
- Implementation Fee: $[IMPLEMENTATION_FEE]
- Payment Terms: [PAYMENT_TERMS]

CUSTOM FEATURES:
[CUSTOM_FEATURES]

SECURITY AND COMPLIANCE:
[SECURITY_COMPLIANCE]

TERMINATION:
[TERMINATION_CLAUSE]

[ENTERPRISE_LEGAL_TERMS]
            """,
            required_fields=[
                "CUSTOMER_NAME", "DATE", "SERVICE_PACKAGE", "CONTRACT_TERM",
                "ANNUAL_FEE", "SLA_COMMITMENTS", "SECURITY_COMPLIANCE"
            ],
            standard_terms={
                "contract_term": "24 months",
                "dedicated_support": "Named CSM",
                "sla_commitments": "99.9% uptime, <4hr response"
            },
            non_negotiable_terms=[
                "security_standards", "data_protection", "audit_rights"
            ],
            approver_roles=["sales_director", "legal", "security"]
        )
        
        self.contract_templates[enterprise_template.template_id] = enterprise_template
    
    def calculate_roi(self, prospect_data: Dict[str, Any]) -> ROICalculation:
        """Calculate ROI for prospect value demonstration"""
        try:
            calculation = ROICalculation(
                calculation_id=str(uuid.uuid4()),
                prospect_name=prospect_data['prospect_name'],
                segment=prospect_data['segment'],
                annual_scholarship_budget=Decimal(str(prospect_data['annual_scholarship_budget'])),
                scholarships_managed=prospect_data['scholarships_managed'],
                staff_hours_per_month=prospect_data['staff_hours_per_month'],
                hourly_rate=Decimal(str(prospect_data['hourly_rate'])),
                application_volume=prospect_data['application_volume'],
                time_savings_percentage=prospect_data.get('time_savings_percentage', 60.0),
                efficiency_gain_percentage=prospect_data.get('efficiency_gain_percentage', 40.0),
                application_increase_percentage=prospect_data.get('application_increase_percentage', 25.0),
                cost_reduction_percentage=prospect_data.get('cost_reduction_percentage', 30.0),
                annual_platform_cost=Decimal(str(prospect_data['annual_platform_cost'])),
                implementation_cost=Decimal(str(prospect_data.get('implementation_cost', 5000))),
                created_by=prospect_data.get('created_by', 'sales_rep')
            )
            
            # Calculate time savings
            monthly_hours_saved = (calculation.staff_hours_per_month * 
                                 calculation.time_savings_percentage / 100)
            calculation.annual_time_savings_hours = monthly_hours_saved * 12
            
            # Calculate cost savings
            annual_labor_cost = calculation.staff_hours_per_month * 12 * calculation.hourly_rate
            calculation.annual_cost_savings = (annual_labor_cost * 
                                            calculation.cost_reduction_percentage / 100)
            
            # Calculate efficiency value (improved outcomes)
            current_efficiency_value = calculation.annual_scholarship_budget * Decimal('0.1')  # 10% efficiency baseline
            calculation.annual_efficiency_value = (current_efficiency_value * 
                                                 Decimal(str(calculation.efficiency_gain_percentage / 100)))
            
            # Total annual value
            time_savings_value = Decimal(str(calculation.annual_time_savings_hours)) * calculation.hourly_rate
            calculation.total_annual_value = (calculation.annual_cost_savings + 
                                           calculation.annual_efficiency_value + 
                                           time_savings_value)
            
            # Total investment
            calculation.total_investment = (calculation.annual_platform_cost + 
                                         calculation.implementation_cost)
            
            # ROI calculations
            calculation.net_annual_benefit = calculation.total_annual_value - calculation.annual_platform_cost
            
            if calculation.total_investment > 0:
                calculation.roi_percentage = float(
                    (calculation.net_annual_benefit / calculation.total_investment) * 100
                )
                calculation.payback_months = float(
                    (calculation.total_investment / (calculation.net_annual_benefit / 12))
                )
            
            # Store calculation
            self.roi_calculations[calculation.calculation_id] = calculation
            
            logger.info(f"💰 ROI calculated: {calculation.prospect_name} | ROI: {calculation.roi_percentage:.1f}% | Payback: {calculation.payback_months:.1f} months")
            return calculation
            
        except Exception as e:
            logger.error(f"Failed to calculate ROI: {str(e)}")
            raise
    
    def get_battle_card(self, competitor_name: str) -> Optional[BattleCard]:
        """Get battle card for specific competitor"""
        for card in self.battle_cards.values():
            if competitor_name.lower() in card.competitor_name.lower():
                card.usage_count += 1
                logger.info(f"⚔️ Battle card accessed: {card.competitor_name}")
                return card
        return None
    
    def get_pricing_guidance(self, segment: str, tier: str, deal_size: Optional[Decimal] = None) -> Optional[PricingGuideline]:
        """Get pricing guidance for specific segment and tier"""
        guideline_key = f"{segment}_{tier}_pricing"
        guideline = self.pricing_guidelines.get(guideline_key)
        
        if guideline and deal_size:
            # Apply volume discounts if applicable
            additional_discount = 0.0
            for volume_threshold, discount in sorted(guideline.volume_discount_tiers.items()):
                if deal_size >= volume_threshold:
                    additional_discount = discount
            
            logger.info(f"💰 Pricing guidance: {segment} {tier} | Additional discount: {additional_discount}%")
        
        return guideline
    
    def generate_contract(self, template_id: str, contract_data: Dict[str, Any]) -> str:
        """Generate contract from template with filled data"""
        try:
            template = self.contract_templates.get(template_id)
            if not template:
                raise ValueError(f"Contract template {template_id} not found")
            
            # Start with template text
            contract_text = template.template_text
            
            # Replace required fields
            for field in template.required_fields:
                value = contract_data.get(field, f"[{field}]")
                contract_text = contract_text.replace(f"[{field}]", str(value))
            
            # Replace optional fields if provided
            for field in template.optional_fields:
                if field in contract_data:
                    contract_text = contract_text.replace(f"[{field}]", str(contract_data[field]))
            
            # Apply standard terms for any remaining placeholders
            for term, default_value in template.standard_terms.items():
                placeholder = f"[{term.upper()}]"
                if placeholder in contract_text:
                    contract_text = contract_text.replace(placeholder, default_value)
            
            logger.info(f"📄 Contract generated: {template.template_name}")
            return contract_text
            
        except Exception as e:
            logger.error(f"Failed to generate contract: {str(e)}")
            raise
    
    def get_negotiation_strategy(self, competitor: str, segment: str, deal_value: Decimal) -> Dict[str, Any]:
        """Get comprehensive negotiation strategy"""
        try:
            strategy = {
                "competitive_positioning": {},
                "pricing_strategy": {},
                "value_propositions": [],
                "negotiation_tactics": [],
                "risk_mitigation": []
            }
            
            # Get battle card for competitive positioning
            battle_card = self.get_battle_card(competitor)
            if battle_card:
                strategy["competitive_positioning"] = {
                    "our_advantages": battle_card.our_advantages,
                    "their_weaknesses": battle_card.key_weaknesses,
                    "differentiation": battle_card.differentiation_points,
                    "objection_responses": battle_card.objections_responses
                }
                strategy["negotiation_tactics"].extend(battle_card.negotiation_tactics)
            
            # Get pricing guidance
            pricing_guidelines = list(self.pricing_guidelines.values())
            relevant_pricing = [p for p in pricing_guidelines if p.segment == segment]
            
            if relevant_pricing:
                pricing = relevant_pricing[0]
                strategy["pricing_strategy"] = {
                    "list_price": float(pricing.list_price),
                    "discount_range": pricing.standard_discount_range,
                    "minimum_price": float(pricing.minimum_acceptable_price),
                    "volume_discounts": pricing.volume_discount_tiers,
                    "special_offers": {
                        "pilot_pricing": float(pricing.pilot_pricing) if pricing.pilot_pricing else None,
                        "nonprofit_discount": pricing.nonprofit_discount,
                        "multi_year_discount": pricing.multi_year_discount
                    }
                }
            
            # Standard value propositions by segment
            value_props = {
                "university": [
                    "Increase qualified applications by 40% through AI matching",
                    "Reduce administrative overhead by 60%",
                    "Professional scholarship marketplace presence",
                    "Real-time analytics and reporting"
                ],
                "foundation": [
                    "Streamline scholarship program management",
                    "Enhanced impact measurement and reporting",
                    "Improved donor engagement through analytics",
                    "Professional grant application portal"
                ],
                "corporate": [
                    "Enterprise-grade security and compliance",
                    "White-label customization options",
                    "API access for system integration",
                    "Dedicated customer success management"
                ]
            }
            
            strategy["value_propositions"] = value_props.get(segment, value_props["university"])
            
            # Risk mitigation strategies
            strategy["risk_mitigation"] = [
                "Offer pilot program to demonstrate value",
                "Provide ROI guarantee with performance metrics",
                "Include implementation support and training",
                "Flexible contract terms and renewal options",
                "Reference customers in similar segment"
            ]
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to generate negotiation strategy: {str(e)}")
            raise
    
    def get_enablement_analytics(self) -> Dict[str, Any]:
        """Get sales enablement usage and effectiveness analytics"""
        try:
            total_roi_calculations = len(self.roi_calculations)
            total_battle_card_usage = sum(card.usage_count for card in self.battle_cards.values())
            
            # ROI calculation statistics
            if self.roi_calculations:
                roi_values = [calc.roi_percentage for calc in self.roi_calculations.values()]
                avg_roi = sum(roi_values) / len(roi_values)
                payback_values = [calc.payback_months for calc in self.roi_calculations.values()]
                avg_payback = sum(payback_values) / len(payback_values)
            else:
                avg_roi = 0
                avg_payback = 0
            
            # Battle card usage by competitor
            competitor_usage = {}
            for card in self.battle_cards.values():
                competitor_usage[card.competitor_name] = card.usage_count
            
            # Segment analysis
            segment_roi = {}
            for calc in self.roi_calculations.values():
                if calc.segment not in segment_roi:
                    segment_roi[calc.segment] = []
                segment_roi[calc.segment].append(calc.roi_percentage)
            
            # Calculate segment averages
            segment_averages = {}
            for segment, rois in segment_roi.items():
                segment_averages[segment] = sum(rois) / len(rois) if rois else 0
            
            return {
                "usage_summary": {
                    "total_roi_calculations": total_roi_calculations,
                    "total_battle_card_usage": total_battle_card_usage,
                    "active_pricing_guidelines": len(self.pricing_guidelines),
                    "available_contract_templates": len(self.contract_templates)
                },
                "roi_analytics": {
                    "average_roi_percentage": avg_roi,
                    "average_payback_months": avg_payback,
                    "segment_averages": segment_averages
                },
                "competitive_analytics": {
                    "competitor_mentions": competitor_usage,
                    "most_used_battle_card": max(competitor_usage.items(), key=lambda x: x[1])[0] if competitor_usage else None
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate enablement analytics: {str(e)}")
            raise


# Global service instance
sales_enablement_toolkit = SalesEnablementToolkit()