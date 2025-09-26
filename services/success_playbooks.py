"""
Success Playbooks Engine
Comprehensive playbooks for partner onboarding, expansion, retention, and escalation

Features:
- Automated onboarding sequences for new partners
- Expansion playbooks for upselling and cross-selling
- Retention strategies and health monitoring
- Escalation procedures for at-risk accounts
- Playbook automation and task orchestration
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)

class PlaybookType(Enum):
    """Types of success playbooks"""
    ONBOARDING = "onboarding"
    EXPANSION = "expansion"
    RETENTION = "retention"
    ESCALATION = "escalation"
    RENEWAL = "renewal"
    WIN_BACK = "win_back"

class PlaybookTrigger(Enum):
    """Triggers that activate playbooks"""
    NEW_CUSTOMER = "new_customer"
    USAGE_MILESTONE = "usage_milestone"
    LOW_ENGAGEMENT = "low_engagement"
    EXPANSION_OPPORTUNITY = "expansion_opportunity"
    RENEWAL_DUE = "renewal_due"
    CHURN_RISK = "churn_risk"
    SUPPORT_ESCALATION = "support_escalation"
    MANUAL = "manual"

class PlaybookStepType(Enum):
    """Types of playbook steps"""
    EMAIL = "email"
    CALL = "call"
    TASK = "task"
    MEETING = "meeting"
    DOCUMENT = "document"
    TRAINING = "training"
    CHECK_IN = "check_in"
    WAIT = "wait"

class PlaybookStatus(Enum):
    """Playbook execution status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class CustomerHealthStatus(Enum):
    """Customer health status levels"""
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    CHURNED = "churned"

@dataclass
class PlaybookStep:
    """Individual step within a playbook"""
    step_id: str
    step_number: int
    title: str
    description: str
    step_type: PlaybookStepType

    # Execution details
    assigned_to: str  # Role or specific person
    estimated_duration: int  # minutes
    due_days_from_start: int  # Days from playbook start

    # Content and templates
    email_template: str | None = None
    call_script: str | None = None
    task_instructions: str | None = None
    success_criteria: list[str] = field(default_factory=list)

    # Automation
    auto_execute: bool = False
    depends_on: list[str] = field(default_factory=list)  # Previous step IDs

    # Status tracking
    completed: bool = False
    completed_at: datetime | None = None
    completion_notes: str | None = None

@dataclass
class PlaybookTemplate:
    """Template definition for a success playbook"""
    template_id: str
    name: str
    description: str
    playbook_type: PlaybookType
    target_segment: str  # university, foundation, corporate, all

    # Trigger configuration
    triggers: list[PlaybookTrigger]
    trigger_conditions: dict[str, Any] = field(default_factory=dict)

    # Steps and flow
    steps: list[PlaybookStep] = field(default_factory=list)
    estimated_duration_days: int = 30

    # Success metrics
    success_metrics: list[str] = field(default_factory=list)
    kpis: dict[str, str] = field(default_factory=dict)

    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True

@dataclass
class PlaybookExecution:
    """Active execution of a playbook for a specific customer"""
    execution_id: str
    customer_id: str
    template_id: str
    playbook_name: str

    # Execution details
    status: PlaybookStatus
    started_at: datetime
    assigned_to: str  # CSM or AE responsible

    # Progress tracking
    current_step: int = 0
    completed_steps: int = 0
    total_steps: int = 0
    progress_percentage: float = 0.0

    # Timeline
    expected_completion: datetime = field(default_factory=datetime.utcnow)
    actual_completion: datetime | None = None

    # Step executions
    step_executions: list[dict[str, Any]] = field(default_factory=list)

    # Outcomes and notes
    success_achieved: bool = False
    completion_notes: str | None = None
    next_playbook: str | None = None

@dataclass
class CustomerHealthScore:
    """Customer health scoring and risk assessment"""
    customer_id: str
    organization_name: str

    # Health components
    usage_score: int = 0          # 0-100 based on platform usage
    engagement_score: int = 0     # 0-100 based on interactions
    value_realization_score: int = 0  # 0-100 based on outcomes
    support_satisfaction: int = 0 # 0-100 based on support interactions

    # Overall health
    overall_score: int = 0        # 0-100 weighted average
    health_status: CustomerHealthStatus = CustomerHealthStatus.HEALTHY

    # Risk factors
    risk_factors: list[str] = field(default_factory=list)

    # Recommendations
    recommended_actions: list[str] = field(default_factory=list)
    playbook_recommendations: list[str] = field(default_factory=list)

    # Timeline
    last_calculated: datetime = field(default_factory=datetime.utcnow)
    next_check: datetime = field(default_factory=datetime.utcnow)

class SuccessPlaybooksEngine:
    """
    Comprehensive Success Playbooks Engine

    Manages automated and guided playbooks for:
    - Customer onboarding and activation
    - Expansion and upselling opportunities
    - Retention and health monitoring
    - Escalation and recovery procedures
    """

    def __init__(self):
        # In-memory storage for MVP (would be database in production)
        self.playbook_templates: dict[str, PlaybookTemplate] = {}
        self.active_executions: dict[str, PlaybookExecution] = {}
        self.customer_health: dict[str, CustomerHealthScore] = {}

        # Initialize default playbook templates
        self._initialize_onboarding_playbooks()
        self._initialize_expansion_playbooks()
        self._initialize_retention_playbooks()
        self._initialize_escalation_playbooks()

        logger.info("🎯 Success Playbooks Engine initialized")
        logger.info(f"📚 Playbook templates: {len(self.playbook_templates)}")

    def _initialize_onboarding_playbooks(self):
        """Initialize onboarding playbook templates"""

        # University Onboarding Playbook
        university_onboarding = PlaybookTemplate(
            template_id="univ_onboarding_v1",
            name="University Partner Onboarding",
            description="Comprehensive onboarding for university partners to drive quick time-to-value",
            playbook_type=PlaybookType.ONBOARDING,
            target_segment="university",
            triggers=[PlaybookTrigger.NEW_CUSTOMER],
            estimated_duration_days=45,
            success_metrics=["first_listing_published", "first_application_received", "setup_completed"],
            kpis={
                "time_to_first_listing": "≤ 7 days",
                "time_to_first_application": "≤ 14 days",
                "onboarding_completion": "≤ 30 days"
            }
        )

        # Add onboarding steps
        university_onboarding.steps = [
            PlaybookStep(
                step_id="welcome_call",
                step_number=1,
                title="Welcome Call & Kickoff",
                description="Initial welcome call to introduce team and set expectations",
                step_type=PlaybookStepType.CALL,
                assigned_to="customer_success_manager",
                estimated_duration=60,
                due_days_from_start=1,
                call_script="Welcome to our scholarship platform! Let's get you set up for success...",
                success_criteria=["Introductions completed", "Expectations set", "Next steps scheduled"]
            ),
            PlaybookStep(
                step_id="platform_training",
                step_number=2,
                title="Platform Training Session",
                description="Comprehensive training on platform features and scholarship management",
                step_type=PlaybookStepType.TRAINING,
                assigned_to="customer_success_manager",
                estimated_duration=90,
                due_days_from_start=3,
                depends_on=["welcome_call"],
                success_criteria=["Training completed", "Account setup verified", "First scholarship drafted"]
            ),
            PlaybookStep(
                step_id="first_listing",
                step_number=3,
                title="First Scholarship Listing",
                description="Support creation and publication of first scholarship listing",
                step_type=PlaybookStepType.TASK,
                assigned_to="customer_success_manager",
                estimated_duration=45,
                due_days_from_start=7,
                depends_on=["platform_training"],
                task_instructions="Guide partner through creating their first scholarship listing with optimization tips",
                success_criteria=["First listing published", "SEO optimized", "Application process tested"]
            ),
            PlaybookStep(
                step_id="week_1_checkin",
                step_number=4,
                title="Week 1 Check-in",
                description="Check progress and address any issues or questions",
                step_type=PlaybookStepType.CHECK_IN,
                assigned_to="customer_success_manager",
                estimated_duration=30,
                due_days_from_start=7,
                success_criteria=["Issues addressed", "Progress confirmed", "Next steps planned"]
            ),
            PlaybookStep(
                step_id="optimization_session",
                step_number=5,
                title="Scholarship Optimization Session",
                description="Review performance and optimize listings for better results",
                step_type=PlaybookStepType.MEETING,
                assigned_to="customer_success_manager",
                estimated_duration=60,
                due_days_from_start=21,
                success_criteria=["Performance reviewed", "Optimizations implemented", "Best practices shared"]
            ),
            PlaybookStep(
                step_id="30_day_review",
                step_number=6,
                title="30-Day Success Review",
                description="Comprehensive review of first month performance and planning",
                step_type=PlaybookStepType.MEETING,
                assigned_to="customer_success_manager",
                estimated_duration=45,
                due_days_from_start=30,
                success_criteria=["KPIs reviewed", "Success celebrated", "Future roadmap planned"]
            )
        ]

        self.playbook_templates[university_onboarding.template_id] = university_onboarding

        # Foundation Onboarding Playbook (similar structure, different focus)
        foundation_onboarding = PlaybookTemplate(
            template_id="found_onboarding_v1",
            name="Foundation Partner Onboarding",
            description="Tailored onboarding for foundation partners focusing on impact measurement",
            playbook_type=PlaybookType.ONBOARDING,
            target_segment="foundation",
            triggers=[PlaybookTrigger.NEW_CUSTOMER],
            estimated_duration_days=30,
            success_metrics=["impact_tracking_setup", "first_award_cycle", "reporting_configured"]
        )

        # Simplified step creation for foundation
        foundation_onboarding.steps = [
            PlaybookStep("found_welcome", 1, "Foundation Welcome Call", "Specialized welcome for foundation partners", PlaybookStepType.CALL, "customer_success_manager", 60, 1),
            PlaybookStep("impact_setup", 2, "Impact Measurement Setup", "Configure impact tracking and reporting", PlaybookStepType.TRAINING, "customer_success_manager", 90, 3),
            PlaybookStep("first_award", 3, "First Award Cycle", "Support through first award cycle", PlaybookStepType.TASK, "customer_success_manager", 60, 7),
            PlaybookStep("reporting_config", 4, "Reporting Configuration", "Set up custom reporting dashboards", PlaybookStepType.TRAINING, "customer_success_manager", 45, 14)
        ]

        self.playbook_templates[foundation_onboarding.template_id] = foundation_onboarding

    def _initialize_expansion_playbooks(self):
        """Initialize expansion and upselling playbook templates"""

        # Upselling Playbook
        expansion_playbook = PlaybookTemplate(
            template_id="expansion_upsell_v1",
            name="Expansion & Upselling Playbook",
            description="Systematic approach to identify and execute expansion opportunities",
            playbook_type=PlaybookType.EXPANSION,
            target_segment="all",
            triggers=[PlaybookTrigger.USAGE_MILESTONE, PlaybookTrigger.EXPANSION_OPPORTUNITY],
            estimated_duration_days=60,
            success_metrics=["expansion_qualified", "proposal_sent", "contract_signed"],
            trigger_conditions={
                "usage_milestone": {"scholarships_published": 5, "applications_received": 50},
                "expansion_opportunity": {"engagement_score": 80, "satisfaction_score": 85}
            }
        )

        expansion_playbook.steps = [
            PlaybookStep(
                step_id="expansion_analysis",
                step_number=1,
                title="Expansion Opportunity Analysis",
                description="Analyze usage patterns and identify specific expansion opportunities",
                step_type=PlaybookStepType.TASK,
                assigned_to="account_executive",
                estimated_duration=90,
                due_days_from_start=3,
                task_instructions="Review customer usage data, success metrics, and identify specific expansion areas",
                success_criteria=["Opportunities identified", "Business case developed", "ROI calculated"]
            ),
            PlaybookStep(
                step_id="expansion_call",
                step_number=2,
                title="Expansion Discovery Call",
                description="Conduct discovery call to understand growth plans and needs",
                step_type=PlaybookStepType.CALL,
                assigned_to="account_executive",
                estimated_duration=60,
                due_days_from_start=7,
                depends_on=["expansion_analysis"],
                call_script="I've been reviewing your success with our platform and wanted to explore how we can support your growth...",
                success_criteria=["Needs understood", "Growth plans identified", "Interest confirmed"]
            ),
            PlaybookStep(
                step_id="expansion_proposal",
                step_number=3,
                title="Expansion Proposal Development",
                description="Create customized expansion proposal with ROI analysis",
                step_type=PlaybookStepType.DOCUMENT,
                assigned_to="account_executive",
                estimated_duration=120,
                due_days_from_start=14,
                depends_on=["expansion_call"],
                success_criteria=["Proposal completed", "ROI documented", "Pricing finalized"]
            ),
            PlaybookStep(
                step_id="proposal_presentation",
                step_number=4,
                title="Proposal Presentation",
                description="Present expansion proposal to stakeholder team",
                step_type=PlaybookStepType.MEETING,
                assigned_to="account_executive",
                estimated_duration=90,
                due_days_from_start=21,
                depends_on=["expansion_proposal"],
                success_criteria=["Proposal presented", "Questions addressed", "Next steps defined"]
            ),
            PlaybookStep(
                step_id="contract_negotiation",
                step_number=5,
                title="Contract Negotiation",
                description="Negotiate contract terms and finalize expansion agreement",
                step_type=PlaybookStepType.TASK,
                assigned_to="account_executive",
                estimated_duration=180,
                due_days_from_start=45,
                depends_on=["proposal_presentation"],
                success_criteria=["Terms agreed", "Contract signed", "Implementation scheduled"]
            )
        ]

        self.playbook_templates[expansion_playbook.template_id] = expansion_playbook

    def _initialize_retention_playbooks(self):
        """Initialize retention and health monitoring playbooks"""

        # Low Engagement Recovery
        low_engagement_playbook = PlaybookTemplate(
            template_id="low_engagement_recovery_v1",
            name="Low Engagement Recovery",
            description="Re-engage partners with declining usage or satisfaction",
            playbook_type=PlaybookType.RETENTION,
            target_segment="all",
            triggers=[PlaybookTrigger.LOW_ENGAGEMENT],
            estimated_duration_days=30,
            success_metrics=["engagement_restored", "satisfaction_improved", "usage_increased"],
            trigger_conditions={
                "low_engagement": {"login_frequency": "<5/month", "support_tickets": ">3", "satisfaction": "<7"}
            }
        )

        low_engagement_playbook.steps = [
            PlaybookStep(
                step_id="engagement_assessment",
                step_number=1,
                title="Engagement Assessment",
                description="Analyze engagement patterns and identify root causes",
                step_type=PlaybookStepType.TASK,
                assigned_to="customer_success_manager",
                estimated_duration=60,
                due_days_from_start=1,
                success_criteria=["Root causes identified", "Usage patterns analyzed", "Action plan created"]
            ),
            PlaybookStep(
                step_id="reach_out_call",
                step_number=2,
                title="Proactive Outreach Call",
                description="Proactive call to understand challenges and offer support",
                step_type=PlaybookStepType.CALL,
                assigned_to="customer_success_manager",
                estimated_duration=45,
                due_days_from_start=3,
                depends_on=["engagement_assessment"],
                call_script="I noticed some changes in your platform usage and wanted to check in to see how we can better support you...",
                success_criteria=["Challenges understood", "Support offered", "Next steps agreed"]
            ),
            PlaybookStep(
                step_id="additional_training",
                step_number=3,
                title="Additional Training Session",
                description="Provide additional training on underutilized features",
                step_type=PlaybookStepType.TRAINING,
                assigned_to="customer_success_manager",
                estimated_duration=60,
                due_days_from_start=7,
                depends_on=["reach_out_call"],
                success_criteria=["Training completed", "Features demonstrated", "Usage improved"]
            ),
            PlaybookStep(
                step_id="weekly_checkins",
                step_number=4,
                title="Weekly Check-ins (4 weeks)",
                description="Weekly check-ins to monitor progress and provide support",
                step_type=PlaybookStepType.CHECK_IN,
                assigned_to="customer_success_manager",
                estimated_duration=30,
                due_days_from_start=14,
                depends_on=["additional_training"],
                success_criteria=["Progress monitored", "Issues addressed", "Engagement restored"]
            )
        ]

        self.playbook_templates[low_engagement_playbook.template_id] = low_engagement_playbook

    def _initialize_escalation_playbooks(self):
        """Initialize escalation and recovery playbooks"""

        # Churn Risk Escalation
        churn_risk_playbook = PlaybookTemplate(
            template_id="churn_risk_escalation_v1",
            name="Churn Risk Escalation",
            description="Emergency escalation for customers at high risk of churning",
            playbook_type=PlaybookType.ESCALATION,
            target_segment="all",
            triggers=[PlaybookTrigger.CHURN_RISK, PlaybookTrigger.SUPPORT_ESCALATION],
            estimated_duration_days=14,
            success_metrics=["escalation_resolved", "satisfaction_restored", "retention_secured"],
            trigger_conditions={
                "churn_risk": {"health_score": "<30", "satisfaction": "<5", "usage_decline": ">50%"}
            }
        )

        churn_risk_playbook.steps = [
            PlaybookStep(
                step_id="immediate_escalation",
                step_number=1,
                title="Immediate Escalation",
                description="Immediate escalation to senior management and account team",
                step_type=PlaybookStepType.TASK,
                assigned_to="customer_success_director",
                estimated_duration=30,
                due_days_from_start=0,  # Same day
                auto_execute=True,
                success_criteria=["Team notified", "Escalation documented", "Response plan activated"]
            ),
            PlaybookStep(
                step_id="emergency_call",
                step_number=2,
                title="Emergency Leadership Call",
                description="Emergency call with customer leadership to understand issues",
                step_type=PlaybookStepType.CALL,
                assigned_to="customer_success_director",
                estimated_duration=60,
                due_days_from_start=1,
                depends_on=["immediate_escalation"],
                call_script="We value your partnership highly and want to address any concerns immediately...",
                success_criteria=["Issues understood", "Commitment to resolve", "Action plan agreed"]
            ),
            PlaybookStep(
                step_id="recovery_plan",
                step_number=3,
                title="Recovery Plan Development",
                description="Develop comprehensive recovery plan with timeline",
                step_type=PlaybookStepType.TASK,
                assigned_to="customer_success_director",
                estimated_duration=120,
                due_days_from_start=2,
                depends_on=["emergency_call"],
                success_criteria=["Recovery plan created", "Resources allocated", "Timeline established"]
            ),
            PlaybookStep(
                step_id="daily_updates",
                step_number=4,
                title="Daily Progress Updates",
                description="Daily updates to customer on recovery progress",
                step_type=PlaybookStepType.EMAIL,
                assigned_to="customer_success_manager",
                estimated_duration=15,
                due_days_from_start=3,
                depends_on=["recovery_plan"],
                email_template="Daily recovery update: Here's our progress on addressing your concerns...",
                success_criteria=["Updates sent", "Progress documented", "Customer informed"]
            ),
            PlaybookStep(
                step_id="resolution_confirmation",
                step_number=5,
                title="Resolution Confirmation",
                description="Confirm resolution and commitment to continued partnership",
                step_type=PlaybookStepType.MEETING,
                assigned_to="customer_success_director",
                estimated_duration=60,
                due_days_from_start=14,
                depends_on=["daily_updates"],
                success_criteria=["Resolution confirmed", "Satisfaction restored", "Future partnership secured"]
            )
        ]

        self.playbook_templates[churn_risk_playbook.template_id] = churn_risk_playbook

    def trigger_playbook(self, customer_id: str, template_id: str, assigned_to: str, trigger_reason: str = "") -> PlaybookExecution:
        """Trigger playbook execution for a customer"""
        try:
            template = self.playbook_templates.get(template_id)
            if not template:
                raise ValueError(f"Playbook template {template_id} not found")

            # Create playbook execution
            execution = PlaybookExecution(
                execution_id=str(uuid.uuid4()),
                customer_id=customer_id,
                template_id=template_id,
                playbook_name=template.name,
                status=PlaybookStatus.ACTIVE,
                started_at=datetime.utcnow(),
                assigned_to=assigned_to,
                total_steps=len(template.steps),
                expected_completion=datetime.utcnow() + timedelta(days=template.estimated_duration_days)
            )

            # Initialize step executions
            for step in template.steps:
                step_execution = {
                    "step_id": step.step_id,
                    "step_number": step.step_number,
                    "title": step.title,
                    "assigned_to": step.assigned_to,
                    "due_date": (execution.started_at + timedelta(days=step.due_days_from_start)).isoformat(),
                    "status": "pending",
                    "auto_execute": step.auto_execute,
                    "depends_on": step.depends_on
                }
                execution.step_executions.append(step_execution)

            # Auto-execute immediate steps
            self._execute_auto_steps(execution, template)

            # Store execution
            self.active_executions[execution.execution_id] = execution

            logger.info(f"🎯 Playbook triggered: {template.name} for customer {customer_id}")
            logger.info(f"📋 {len(template.steps)} steps scheduled | Expected completion: {execution.expected_completion.strftime('%Y-%m-%d')}")

            return execution

        except Exception as e:
            logger.error(f"Failed to trigger playbook: {str(e)}")
            raise

    def _execute_auto_steps(self, execution: PlaybookExecution, template: PlaybookTemplate):
        """Execute steps that are marked for auto-execution"""
        for i, step in enumerate(template.steps):
            if step.auto_execute and step.due_days_from_start == 0:
                self._execute_step(execution, i, "Auto-executed")

    def complete_step(self, execution_id: str, step_number: int, completion_notes: str = "") -> PlaybookExecution:
        """Mark a playbook step as completed"""
        try:
            execution = self.active_executions.get(execution_id)
            if not execution:
                raise ValueError(f"Playbook execution {execution_id} not found")

            if step_number < 1 or step_number > len(execution.step_executions):
                raise ValueError(f"Invalid step number: {step_number}")

            step_execution = execution.step_executions[step_number - 1]

            # Mark step as completed
            step_execution["status"] = "completed"
            step_execution["completed_at"] = datetime.utcnow().isoformat()
            step_execution["completion_notes"] = completion_notes

            # Update execution progress
            execution.completed_steps += 1
            execution.progress_percentage = (execution.completed_steps / execution.total_steps) * 100

            # Update current step to next pending step
            execution.current_step = self._find_next_pending_step(execution)

            # Check if playbook is completed
            if execution.completed_steps == execution.total_steps:
                execution.status = PlaybookStatus.COMPLETED
                execution.actual_completion = datetime.utcnow()
                execution.success_achieved = True

                # Recommend next playbook
                execution.next_playbook = self._recommend_next_playbook(execution)

            logger.info(f"✅ Step completed: {step_execution['title']} | Progress: {execution.progress_percentage:.1f}%")
            return execution

        except Exception as e:
            logger.error(f"Failed to complete playbook step: {str(e)}")
            raise

    def _execute_step(self, execution: PlaybookExecution, step_index: int, notes: str):
        """Execute a playbook step"""
        step_execution = execution.step_executions[step_index]
        step_execution["status"] = "completed"
        step_execution["completed_at"] = datetime.utcnow().isoformat()
        step_execution["completion_notes"] = notes
        execution.completed_steps += 1

    def _find_next_pending_step(self, execution: PlaybookExecution) -> int:
        """Find the next pending step in the playbook"""
        for i, step in enumerate(execution.step_executions):
            if step["status"] == "pending":
                return i + 1
        return execution.total_steps  # All steps completed

    def _recommend_next_playbook(self, execution: PlaybookExecution) -> str | None:
        """Recommend next playbook based on completed playbook"""
        template = self.playbook_templates.get(execution.template_id)
        if not template:
            return None

        # Playbook progression logic
        if template.playbook_type == PlaybookType.ONBOARDING:
            # After onboarding, recommend expansion playbook
            return "expansion_upsell_v1"
        if template.playbook_type == PlaybookType.EXPANSION:
            # After expansion, no automatic next playbook
            return None
        if template.playbook_type == PlaybookType.RETENTION:
            # After retention, monitor for expansion
            return "expansion_upsell_v1"

        return None

    def calculate_customer_health(self, customer_id: str, usage_data: dict[str, Any]) -> CustomerHealthScore:
        """Calculate comprehensive customer health score"""
        try:
            # Extract health indicators from usage data
            logins_last_month = usage_data.get('logins_last_month', 0)
            scholarships_published = usage_data.get('scholarships_published', 0)
            applications_received = usage_data.get('applications_received', 0)
            support_tickets = usage_data.get('support_tickets', 0)
            last_login_days = usage_data.get('last_login_days', 0)
            satisfaction_score = usage_data.get('satisfaction_score', 5)  # 1-10 scale

            # Calculate component scores (0-100 scale)
            usage_score = min(100, (logins_last_month * 5) + (scholarships_published * 10))
            engagement_score = min(100, max(0, 100 - (last_login_days * 5)))
            value_realization_score = min(100, applications_received * 2)
            support_satisfaction = min(100, max(0, (satisfaction_score * 10) - (support_tickets * 10)))

            # Calculate weighted overall score
            overall_score = int(
                (usage_score * 0.3) +
                (engagement_score * 0.25) +
                (value_realization_score * 0.25) +
                (support_satisfaction * 0.2)
            )

            # Determine health status
            if overall_score >= 75:
                health_status = CustomerHealthStatus.HEALTHY
            elif overall_score >= 50:
                health_status = CustomerHealthStatus.AT_RISK
            elif overall_score >= 25:
                health_status = CustomerHealthStatus.CRITICAL
            else:
                health_status = CustomerHealthStatus.CHURNED

            # Identify risk factors
            risk_factors = []
            if last_login_days > 14:
                risk_factors.append("No recent login activity")
            if support_tickets > 3:
                risk_factors.append("High support ticket volume")
            if satisfaction_score < 6:
                risk_factors.append("Low satisfaction score")
            if applications_received == 0:
                risk_factors.append("No applications received")

            # Generate recommendations
            recommended_actions = []
            playbook_recommendations = []

            if health_status == CustomerHealthStatus.AT_RISK:
                recommended_actions.append("Schedule check-in call")
                recommended_actions.append("Review usage patterns")
                playbook_recommendations.append("low_engagement_recovery_v1")
            elif health_status == CustomerHealthStatus.CRITICAL:
                recommended_actions.append("Immediate escalation")
                recommended_actions.append("Emergency intervention")
                playbook_recommendations.append("churn_risk_escalation_v1")
            elif health_status == CustomerHealthStatus.HEALTHY and overall_score > 80:
                recommended_actions.append("Explore expansion opportunities")
                playbook_recommendations.append("expansion_upsell_v1")

            health_score = CustomerHealthScore(
                customer_id=customer_id,
                organization_name=usage_data.get('organization_name', 'Unknown'),
                usage_score=usage_score,
                engagement_score=engagement_score,
                value_realization_score=value_realization_score,
                support_satisfaction=support_satisfaction,
                overall_score=overall_score,
                health_status=health_status,
                risk_factors=risk_factors,
                recommended_actions=recommended_actions,
                playbook_recommendations=playbook_recommendations,
                next_check=datetime.utcnow() + timedelta(days=7)
            )

            # Store health score
            self.customer_health[customer_id] = health_score

            logger.info(f"📊 Health calculated: {health_score.organization_name} | Score: {overall_score} | Status: {health_status.value}")
            return health_score

        except Exception as e:
            logger.error(f"Failed to calculate customer health: {str(e)}")
            raise

    def get_playbook_analytics(self) -> dict[str, Any]:
        """Get comprehensive playbook performance analytics"""
        try:
            total_executions = len(self.active_executions)
            completed_executions = len([e for e in self.active_executions.values()
                                      if e.status == PlaybookStatus.COMPLETED])

            # Playbook type distribution
            type_distribution = {}
            for template in self.playbook_templates.values():
                type_name = template.playbook_type.value
                type_distribution[type_name] = type_distribution.get(type_name, 0) + 1

            # Success rates by playbook type
            success_rates = {}
            for pb_type in PlaybookType:
                type_executions = [e for e in self.active_executions.values()
                                 if self.playbook_templates.get(e.template_id, {}).playbook_type == pb_type]
                successful = [e for e in type_executions if e.success_achieved]

                if type_executions:
                    success_rates[pb_type.value] = len(successful) / len(type_executions)
                else:
                    success_rates[pb_type.value] = 0

            # Average completion times
            completed = [e for e in self.active_executions.values()
                        if e.status == PlaybookStatus.COMPLETED and e.actual_completion]
            avg_completion_days = 0
            if completed:
                total_days = sum((e.actual_completion - e.started_at).days for e in completed)
                avg_completion_days = total_days / len(completed)

            # Health distribution
            health_distribution = {}
            for health in CustomerHealthStatus:
                count = len([h for h in self.customer_health.values()
                           if h.health_status == health])
                health_distribution[health.value] = count

            return {
                "summary": {
                    "total_executions": total_executions,
                    "completed_executions": completed_executions,
                    "completion_rate": completed_executions / max(total_executions, 1),
                    "avg_completion_days": avg_completion_days,
                    "total_customers_monitored": len(self.customer_health)
                },
                "playbook_performance": {
                    "template_count": len(self.playbook_templates),
                    "type_distribution": type_distribution,
                    "success_rates": success_rates
                },
                "customer_health": {
                    "health_distribution": health_distribution,
                    "avg_health_score": sum(h.overall_score for h in self.customer_health.values()) / max(len(self.customer_health), 1)
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate playbook analytics: {str(e)}")
            raise


# Global service instance
success_playbooks_engine = SuccessPlaybooksEngine()
