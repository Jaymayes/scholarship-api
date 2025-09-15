"""
Pipeline Management System
Comprehensive deal progression tracking for aggressive B2B ARR execution

Features:
- Deal stage progression: MQL→SQL→Demo→Pilot→Contract→Paid
- Stage-gate criteria and automated validation
- Automated follow-up sequences and task creation
- Pipeline health scoring and risk assessment
- Stage duration tracking and alerts
- Revenue forecasting and quota management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, asdict, field
import json
import uuid

from services.lead_routing_engine import Lead, LeadStage, SalesRep
from utils.logger import get_logger

logger = get_logger(__name__)

class DealStage(Enum):
    """Deal progression stages"""
    MQL = "mql"              # Marketing Qualified Lead
    SQL = "sql"              # Sales Qualified Lead 
    DEMO = "demo"            # Demo scheduled/completed
    PILOT = "pilot"          # Pilot program active
    CONTRACT = "contract"    # Contract negotiation
    PAID = "paid"            # Converted to paid tier
    LOST = "lost"            # Deal lost
    CHURNED = "churned"      # Customer churned

class DealHealth(Enum):
    """Deal health status"""
    HEALTHY = "healthy"      # On track
    AT_RISK = "at_risk"      # Needs attention
    STALLED = "stalled"      # No recent activity
    CRITICAL = "critical"    # High risk of loss

class TaskType(Enum):
    """Follow-up task types"""
    CALL = "call"
    EMAIL = "email"
    DEMO = "demo"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    CHECK_IN = "check_in"
    ESCALATION = "escalation"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class StageGateCriteria:
    """Criteria required to advance to next stage"""
    stage: DealStage
    required_activities: List[str]  # Activities that must be completed
    required_fields: List[str]      # Data fields that must be populated
    min_score: Optional[int] = None # Minimum qualification score
    approval_required: bool = False  # Requires manager approval
    automated_advance: bool = True   # Can auto-advance if criteria met

@dataclass
class DealActivity:
    """Individual activity within a deal"""
    activity_id: str
    deal_id: str
    activity_type: str
    description: str
    performed_by: str
    performed_at: datetime
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    sentiment_score: Optional[int] = None  # 1-10 scale

@dataclass
class FollowUpTask:
    """Automated follow-up task"""
    task_id: str
    deal_id: str
    assigned_to: str
    task_type: TaskType
    title: str
    description: str
    priority: TaskPriority
    due_date: datetime
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Deal:
    """Comprehensive deal record"""
    deal_id: str
    lead_id: str
    organization_name: str
    contact_name: str
    contact_email: str
    
    # Deal details
    stage: DealStage
    health: DealHealth
    estimated_acv: Decimal
    probability: float  # 0-100%
    close_date: datetime
    
    # Assignment
    owner_id: str
    owner_name: str
    
    # Stage history
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    current_stage_entry: datetime = field(default_factory=datetime.utcnow)
    
    # Activities and engagement
    activities: List[DealActivity] = field(default_factory=list)
    last_activity_date: Optional[datetime] = None
    days_since_activity: int = 0
    
    # Qualification scoring
    qualification_score: int = 0  # 0-100 scale
    fit_score: int = 0           # 0-100 scale
    urgency_score: int = 0       # 0-100 scale
    
    # Health indicators
    stage_duration_days: int = 0
    expected_stage_duration: int = 30
    stale_threshold_days: int = 14
    
    # Follow-up management
    pending_tasks: List[FollowUpTask] = field(default_factory=list)
    overdue_tasks: int = 0
    
    # Forecast and reporting
    weighted_value: Decimal = field(default_factory=lambda: Decimal('0'))
    forecast_category: str = "pipeline"  # pipeline, best_case, commit
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    notes: List[str] = field(default_factory=list)

@dataclass
class PipelineMetrics:
    """Pipeline health and performance metrics"""
    total_deals: int = 0
    total_pipeline_value: Decimal = field(default_factory=lambda: Decimal('0'))
    weighted_pipeline_value: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # Stage distribution
    stage_distribution: Dict[DealStage, int] = field(default_factory=dict)
    stage_values: Dict[DealStage, Decimal] = field(default_factory=dict)
    
    # Health metrics
    healthy_deals: int = 0
    at_risk_deals: int = 0
    stalled_deals: int = 0
    critical_deals: int = 0
    
    # Velocity metrics
    avg_stage_duration: Dict[DealStage, float] = field(default_factory=dict)
    avg_sales_cycle: float = 0
    conversion_rates: Dict[DealStage, float] = field(default_factory=dict)
    
    # Activity metrics
    deals_with_recent_activity: int = 0
    avg_activities_per_deal: float = 0
    overdue_tasks: int = 0

class PipelineManagementSystem:
    """
    Comprehensive Pipeline Management System for B2B Sales Operations
    
    Manages deal progression through defined stages with:
    - Automated stage advancement based on criteria
    - Health monitoring and risk identification
    - Follow-up task automation
    - Performance analytics and forecasting
    """
    
    def __init__(self):
        # In-memory storage for MVP (would be database in production)
        self.deals: Dict[str, Deal] = {}
        self.stage_gates: Dict[DealStage, StageGateCriteria] = {}
        self.activities: Dict[str, List[DealActivity]] = {}
        self.tasks: Dict[str, List[FollowUpTask]] = {}
        
        # Initialize stage gate criteria and automation rules
        self._initialize_stage_gates()
        self._initialize_automation_rules()
        
        logger.info("🚀 Pipeline Management System initialized")
        logger.info(f"📊 Stage gates: {len(self.stage_gates)} configured")
    
    def _initialize_stage_gates(self):
        """Initialize stage advancement criteria"""
        
        # MQL → SQL: Lead qualification and initial contact
        self.stage_gates[DealStage.SQL] = StageGateCriteria(
            stage=DealStage.SQL,
            required_activities=["discovery_call", "needs_assessment"],
            required_fields=["budget_range", "decision_timeline", "decision_maker"],
            min_score=60,
            automated_advance=True
        )
        
        # SQL → Demo: Qualified opportunity with demo scheduled
        self.stage_gates[DealStage.DEMO] = StageGateCriteria(
            stage=DealStage.DEMO,
            required_activities=["demo_scheduled"],
            required_fields=["demo_date", "attendees", "use_case"],
            min_score=70,
            automated_advance=True
        )
        
        # Demo → Pilot: Successful demo with pilot agreement
        self.stage_gates[DealStage.PILOT] = StageGateCriteria(
            stage=DealStage.PILOT,
            required_activities=["demo_completed", "pilot_agreement"],
            required_fields=["pilot_start_date", "pilot_scope", "success_criteria"],
            min_score=75,
            automated_advance=False,  # Requires manual verification
            approval_required=True
        )
        
        # Pilot → Contract: Successful pilot with contract negotiation
        self.stage_gates[DealStage.CONTRACT] = StageGateCriteria(
            stage=DealStage.CONTRACT,
            required_activities=["pilot_completed", "contract_sent"],
            required_fields=["contract_value", "contract_terms", "legal_review"],
            min_score=85,
            automated_advance=False,
            approval_required=True
        )
        
        # Contract → Paid: Signed contract and payment received
        self.stage_gates[DealStage.PAID] = StageGateCriteria(
            stage=DealStage.PAID,
            required_activities=["contract_signed", "payment_received"],
            required_fields=["signed_contract_date", "first_payment_date"],
            min_score=90,
            automated_advance=True
        )
    
    def _initialize_automation_rules(self):
        """Initialize automated follow-up rules"""
        # This would contain rules for automatic task creation
        # Based on stage, time elapsed, and activity patterns
        pass
    
    def create_deal_from_lead(self, lead: Lead, owner_id: str, owner_name: str) -> Deal:
        """Create new deal from qualified lead"""
        try:
            deal = Deal(
                deal_id=str(uuid.uuid4()),
                lead_id=lead.lead_id,
                organization_name=lead.organization_name,
                contact_name=lead.contact_name,
                contact_email=lead.contact_email,
                stage=DealStage(lead.stage.value),
                health=DealHealth.HEALTHY,
                estimated_acv=lead.estimated_acv,
                probability=self._calculate_initial_probability(lead.stage, lead.fit_score),
                close_date=datetime.utcnow() + timedelta(days=90),  # Default 90-day close
                owner_id=owner_id,
                owner_name=owner_name,
                qualification_score=lead.fit_score * 10,  # Convert to 100-point scale
                fit_score=lead.fit_score * 10,
                urgency_score=lead.urgency_score * 10
            )
            
            # Add initial stage history
            deal.stage_history.append({
                "stage": deal.stage.value,
                "entered_at": deal.created_at.isoformat(),
                "probability": deal.probability,
                "notes": "Deal created from qualified lead"
            })
            
            # Calculate initial weighted value
            deal.weighted_value = deal.estimated_acv * Decimal(str(deal.probability / 100))
            
            # Store deal
            self.deals[deal.deal_id] = deal
            self.activities[deal.deal_id] = []
            self.tasks[deal.deal_id] = []
            
            # Create initial follow-up tasks
            self._create_initial_tasks(deal)
            
            logger.info(f"💼 Deal created: {deal.organization_name} (${deal.estimated_acv:,.0f} ACV)")
            return deal
            
        except Exception as e:
            logger.error(f"Failed to create deal from lead: {str(e)}")
            raise
    
    def _calculate_initial_probability(self, stage: LeadStage, fit_score: int) -> float:
        """Calculate initial deal probability based on stage and fit"""
        base_probabilities = {
            LeadStage.MQL: 15,
            LeadStage.SQL: 25,
            LeadStage.DEMO: 40,
            LeadStage.PILOT: 60,
            LeadStage.CONTRACT: 80,
            LeadStage.PAID: 100
        }
        
        base_prob = base_probabilities.get(stage, 15)
        
        # Adjust based on fit score (1-10 scale)
        fit_adjustment = (fit_score - 5) * 2  # +/- 10% based on fit
        
        return max(5, min(95, base_prob + fit_adjustment))
    
    def advance_deal_stage(self, deal_id: str, new_stage: DealStage, notes: str = "") -> Deal:
        """Advance deal to next stage with validation"""
        try:
            deal = self.deals.get(deal_id)
            if not deal:
                raise ValueError(f"Deal {deal_id} not found")
            
            # Validate stage progression
            if not self._can_advance_to_stage(deal, new_stage):
                missing_criteria = self._get_missing_criteria(deal, new_stage)
                raise ValueError(f"Cannot advance to {new_stage.value}. Missing: {missing_criteria}")
            
            old_stage = deal.stage
            
            # Update deal stage
            deal.stage = new_stage
            deal.current_stage_entry = datetime.utcnow()
            deal.last_updated = datetime.utcnow()
            
            # Update probability based on new stage
            deal.probability = self._update_probability_for_stage(new_stage, deal.qualification_score)
            deal.weighted_value = deal.estimated_acv * Decimal(str(deal.probability / 100))
            
            # Add to stage history
            deal.stage_history.append({
                "stage": new_stage.value,
                "entered_at": deal.current_stage_entry.isoformat(),
                "probability": deal.probability,
                "notes": notes or f"Advanced from {old_stage.value}"
            })
            
            # Update health status
            deal.health = self._calculate_deal_health(deal)
            
            # Create stage-specific follow-up tasks
            self._create_stage_tasks(deal, new_stage)
            
            logger.info(f"📈 Deal advanced: {deal.organization_name} {old_stage.value} → {new_stage.value}")
            logger.info(f"💰 Probability: {deal.probability}% | Weighted: ${deal.weighted_value:,.0f}")
            
            return deal
            
        except Exception as e:
            logger.error(f"Failed to advance deal stage: {str(e)}")
            raise
    
    def _can_advance_to_stage(self, deal: Deal, target_stage: DealStage) -> bool:
        """Check if deal meets criteria to advance to target stage"""
        
        criteria = self.stage_gates.get(target_stage)
        if not criteria:
            return True  # No specific criteria defined
        
        # Check required activities
        deal_activities = self.activities.get(deal.deal_id, [])
        activity_types = {activity.activity_type for activity in deal_activities}
        
        for required_activity in criteria.required_activities:
            if required_activity not in activity_types:
                return False
        
        # Check qualification score
        if criteria.min_score and deal.qualification_score < criteria.min_score:
            return False
        
        return True
    
    def _get_missing_criteria(self, deal: Deal, target_stage: DealStage) -> List[str]:
        """Get list of missing criteria for stage advancement"""
        
        missing = []
        criteria = self.stage_gates.get(target_stage)
        if not criteria:
            return missing
        
        # Check activities
        deal_activities = self.activities.get(deal.deal_id, [])
        activity_types = {activity.activity_type for activity in deal_activities}
        
        for required_activity in criteria.required_activities:
            if required_activity not in activity_types:
                missing.append(f"Activity: {required_activity}")
        
        # Check score
        if criteria.min_score and deal.qualification_score < criteria.min_score:
            missing.append(f"Qualification score: {deal.qualification_score} < {criteria.min_score}")
        
        return missing
    
    def add_deal_activity(self, deal_id: str, activity_data: Dict[str, Any]) -> DealActivity:
        """Add activity to deal"""
        try:
            deal = self.deals.get(deal_id)
            if not deal:
                raise ValueError(f"Deal {deal_id} not found")
            
            activity = DealActivity(
                activity_id=str(uuid.uuid4()),
                deal_id=deal_id,
                activity_type=activity_data['activity_type'],
                description=activity_data['description'],
                performed_by=activity_data['performed_by'],
                performed_at=activity_data.get('performed_at', datetime.utcnow()),
                outcome=activity_data.get('outcome'),
                next_steps=activity_data.get('next_steps'),
                sentiment_score=activity_data.get('sentiment_score')
            )
            
            # Add to deal activities
            if deal_id not in self.activities:
                self.activities[deal_id] = []
            self.activities[deal_id].append(activity)
            
            # Update deal metadata
            deal.last_activity_date = activity.performed_at
            deal.days_since_activity = 0
            deal.last_updated = datetime.utcnow()
            
            # Update health status
            deal.health = self._calculate_deal_health(deal)
            
            # Check for automatic stage advancement
            if self._should_auto_advance(deal, activity):
                next_stage = self._get_next_stage(deal.stage)
                if next_stage and self._can_advance_to_stage(deal, next_stage):
                    self.advance_deal_stage(deal_id, next_stage, f"Auto-advanced after {activity.activity_type}")
            
            logger.info(f"✅ Activity added: {activity.activity_type} for {deal.organization_name}")
            return activity
            
        except Exception as e:
            logger.error(f"Failed to add deal activity: {str(e)}")
            raise
    
    def _should_auto_advance(self, deal: Deal, activity: DealActivity) -> bool:
        """Check if activity should trigger automatic stage advancement"""
        
        # Define trigger activities for each stage
        advancement_triggers = {
            DealStage.MQL: ["discovery_call", "needs_assessment"],
            DealStage.SQL: ["demo_scheduled"],
            DealStage.DEMO: ["demo_completed", "pilot_agreement"], 
            DealStage.PILOT: ["pilot_completed"],
            DealStage.CONTRACT: ["contract_signed", "payment_received"]
        }
        
        trigger_activities = advancement_triggers.get(deal.stage, [])
        return activity.activity_type in trigger_activities
    
    def _get_next_stage(self, current_stage: DealStage) -> Optional[DealStage]:
        """Get the next logical stage in progression"""
        
        stage_progression = {
            DealStage.MQL: DealStage.SQL,
            DealStage.SQL: DealStage.DEMO,
            DealStage.DEMO: DealStage.PILOT,
            DealStage.PILOT: DealStage.CONTRACT,
            DealStage.CONTRACT: DealStage.PAID
        }
        
        return stage_progression.get(current_stage)
    
    def create_follow_up_task(self, deal_id: str, task_data: Dict[str, Any]) -> FollowUpTask:
        """Create follow-up task for deal"""
        try:
            deal = self.deals.get(deal_id)
            if not deal:
                raise ValueError(f"Deal {deal_id} not found")
            
            task = FollowUpTask(
                task_id=str(uuid.uuid4()),
                deal_id=deal_id,
                assigned_to=task_data['assigned_to'],
                task_type=TaskType(task_data['task_type']),
                title=task_data['title'],
                description=task_data['description'],
                priority=TaskPriority(task_data.get('priority', 'medium')),
                due_date=datetime.fromisoformat(task_data['due_date'])
            )
            
            # Add to deal tasks
            if deal_id not in self.tasks:
                self.tasks[deal_id] = []
            self.tasks[deal_id].append(task)
            
            # Update deal pending tasks
            pending_tasks = [t for t in self.tasks[deal_id] if not t.completed]
            deal.pending_tasks = pending_tasks
            deal.overdue_tasks = len([t for t in pending_tasks if t.due_date < datetime.utcnow()])
            
            logger.info(f"📋 Task created: {task.title} for {deal.organization_name}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create follow-up task: {str(e)}")
            raise
    
    def _create_initial_tasks(self, deal: Deal):
        """Create initial follow-up tasks for new deal"""
        
        if deal.stage == DealStage.MQL:
            # Create discovery call task
            self.create_follow_up_task(deal.deal_id, {
                "assigned_to": deal.owner_id,
                "task_type": "call",
                "title": "Discovery Call",
                "description": f"Conduct discovery call with {deal.contact_name} to understand needs and qualify opportunity",
                "priority": "high",
                "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat()
            })
        
        elif deal.stage == DealStage.SQL:
            # Create demo scheduling task
            self.create_follow_up_task(deal.deal_id, {
                "assigned_to": deal.owner_id,
                "task_type": "demo",
                "title": "Schedule Demo",
                "description": f"Schedule product demonstration with {deal.organization_name}",
                "priority": "high",
                "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat()
            })
    
    def _create_stage_tasks(self, deal: Deal, stage: DealStage):
        """Create stage-specific follow-up tasks"""
        
        task_templates = {
            DealStage.SQL: {
                "task_type": "demo",
                "title": "Schedule Product Demo",
                "description": "Schedule and conduct product demonstration",
                "days_due": 5
            },
            DealStage.DEMO: {
                "task_type": "proposal",
                "title": "Send Pilot Proposal",
                "description": "Send pilot program proposal with success criteria",
                "days_due": 3
            },
            DealStage.PILOT: {
                "task_type": "check_in",
                "title": "Pilot Program Check-in",
                "description": "Check pilot program progress and gather feedback",
                "days_due": 7
            },
            DealStage.CONTRACT: {
                "task_type": "contract",
                "title": "Contract Follow-up",
                "description": "Follow up on contract review and address questions",
                "days_due": 2
            }
        }
        
        template = task_templates.get(stage)
        if template:
            self.create_follow_up_task(deal.deal_id, {
                "assigned_to": deal.owner_id,
                "task_type": template["task_type"],
                "title": template["title"],
                "description": template["description"],
                "priority": "medium",
                "due_date": (datetime.utcnow() + timedelta(days=template["days_due"])).isoformat()
            })
    
    def _calculate_deal_health(self, deal: Deal) -> DealHealth:
        """Calculate deal health based on activity and progression"""
        
        # Calculate days since last activity
        if deal.last_activity_date:
            days_since_activity = (datetime.utcnow() - deal.last_activity_date).days
        else:
            days_since_activity = (datetime.utcnow() - deal.created_at).days
        
        deal.days_since_activity = days_since_activity
        
        # Calculate stage duration
        deal.stage_duration_days = (datetime.utcnow() - deal.current_stage_entry).days
        
        # Health scoring logic
        if days_since_activity > 21:  # No activity for 3+ weeks
            return DealHealth.CRITICAL
        elif days_since_activity > deal.stale_threshold_days:
            return DealHealth.STALLED
        elif deal.stage_duration_days > deal.expected_stage_duration * 1.5:
            return DealHealth.AT_RISK
        elif deal.overdue_tasks > 2:
            return DealHealth.AT_RISK
        else:
            return DealHealth.HEALTHY
    
    def _update_probability_for_stage(self, stage: DealStage, qualification_score: int) -> float:
        """Update deal probability based on stage and qualification"""
        
        base_probabilities = {
            DealStage.MQL: 15,
            DealStage.SQL: 25,
            DealStage.DEMO: 40,
            DealStage.PILOT: 60,
            DealStage.CONTRACT: 80,
            DealStage.PAID: 100,
            DealStage.LOST: 0,
            DealStage.CHURNED: 0
        }
        
        base_prob = base_probabilities.get(stage, 15)
        
        # Adjust based on qualification score (0-100 scale)
        score_adjustment = (qualification_score - 50) * 0.2  # +/- 10% based on score
        
        return max(5, min(95, base_prob + score_adjustment))
    
    def get_pipeline_metrics(self, owner_id: Optional[str] = None) -> PipelineMetrics:
        """Get comprehensive pipeline metrics"""
        try:
            # Filter deals by owner if specified
            relevant_deals = self.deals.values()
            if owner_id:
                relevant_deals = [d for d in relevant_deals if d.owner_id == owner_id]
            
            metrics = PipelineMetrics()
            metrics.total_deals = len(relevant_deals)
            
            if metrics.total_deals == 0:
                return metrics
            
            # Calculate values
            metrics.total_pipeline_value = sum(d.estimated_acv for d in relevant_deals)
            metrics.weighted_pipeline_value = sum(d.weighted_value for d in relevant_deals)
            
            # Stage distribution
            for stage in DealStage:
                stage_deals = [d for d in relevant_deals if d.stage == stage]
                metrics.stage_distribution[stage] = len(stage_deals)
                metrics.stage_values[stage] = sum(d.estimated_acv for d in stage_deals)
            
            # Health metrics
            for deal in relevant_deals:
                if deal.health == DealHealth.HEALTHY:
                    metrics.healthy_deals += 1
                elif deal.health == DealHealth.AT_RISK:
                    metrics.at_risk_deals += 1
                elif deal.health == DealHealth.STALLED:
                    metrics.stalled_deals += 1
                elif deal.health == DealHealth.CRITICAL:
                    metrics.critical_deals += 1
            
            # Activity metrics
            recent_activity_cutoff = datetime.utcnow() - timedelta(days=7)
            metrics.deals_with_recent_activity = len([
                d for d in relevant_deals 
                if d.last_activity_date and d.last_activity_date > recent_activity_cutoff
            ])
            
            total_activities = sum(len(self.activities.get(d.deal_id, [])) for d in relevant_deals)
            metrics.avg_activities_per_deal = total_activities / metrics.total_deals
            
            metrics.overdue_tasks = sum(d.overdue_tasks for d in relevant_deals)
            
            # Velocity metrics (would need historical data for full implementation)
            closed_deals = [d for d in relevant_deals if d.stage in [DealStage.PAID, DealStage.LOST]]
            if closed_deals:
                total_cycle_time = sum((d.last_updated - d.created_at).days for d in closed_deals)
                metrics.avg_sales_cycle = total_cycle_time / len(closed_deals)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to generate pipeline metrics: {str(e)}")
            raise
    
    def get_deal_forecast(self, time_period_days: int = 90) -> Dict[str, Any]:
        """Generate revenue forecast based on pipeline"""
        try:
            forecast_date = datetime.utcnow() + timedelta(days=time_period_days)
            
            # Get deals closing within time period
            forecasted_deals = [
                d for d in self.deals.values() 
                if d.close_date <= forecast_date and d.stage not in [DealStage.LOST, DealStage.CHURNED]
            ]
            
            # Categorize by forecast confidence
            commit_deals = [d for d in forecasted_deals if d.probability >= 80]
            best_case_deals = [d for d in forecasted_deals if 50 <= d.probability < 80]
            pipeline_deals = [d for d in forecasted_deals if d.probability < 50]
            
            forecast = {
                "forecast_period_days": time_period_days,
                "forecast_through_date": forecast_date.isoformat(),
                "commit": {
                    "deal_count": len(commit_deals),
                    "total_value": float(sum(d.estimated_acv for d in commit_deals)),
                    "weighted_value": float(sum(d.weighted_value for d in commit_deals))
                },
                "best_case": {
                    "deal_count": len(best_case_deals),
                    "total_value": float(sum(d.estimated_acv for d in best_case_deals)),
                    "weighted_value": float(sum(d.weighted_value for d in best_case_deals))
                },
                "pipeline": {
                    "deal_count": len(pipeline_deals),
                    "total_value": float(sum(d.estimated_acv for d in pipeline_deals)),
                    "weighted_value": float(sum(d.weighted_value for d in pipeline_deals))
                },
                "total": {
                    "deal_count": len(forecasted_deals),
                    "total_value": float(sum(d.estimated_acv for d in forecasted_deals)),
                    "weighted_value": float(sum(d.weighted_value for d in forecasted_deals))
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate deal forecast: {str(e)}")
            raise


# Global service instance
pipeline_management_system = PipelineManagementSystem()