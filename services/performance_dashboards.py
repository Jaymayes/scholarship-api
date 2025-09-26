"""
Performance Dashboards System
Comprehensive analytics and reporting for B2B sales operations performance

Features:
- AE/Partner Success individual scorecards and KPIs
- Quota attainment tracking and forecasting
- Pipeline coverage metrics and health indicators
- Activity KPIs (calls, demos, proposals, conversions)
- Real-time management dashboards and alerts
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from services.lead_routing_engine import AssignmentType
from services.pipeline_management_system import Deal, DealStage
from utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceMetric(Enum):
    """Key performance metrics tracked"""
    QUOTA_ATTAINMENT = "quota_attainment"
    PIPELINE_COVERAGE = "pipeline_coverage"
    CONVERSION_RATE = "conversion_rate"
    ACTIVITY_VOLUME = "activity_volume"
    DEAL_VELOCITY = "deal_velocity"
    ACV_PERFORMANCE = "acv_performance"
    CUSTOMER_HEALTH = "customer_health"

class DashboardType(Enum):
    """Types of performance dashboards"""
    INDIVIDUAL_SCORECARD = "individual_scorecard"
    TEAM_PERFORMANCE = "team_performance"
    EXECUTIVE_SUMMARY = "executive_summary"
    PIPELINE_HEALTH = "pipeline_health"
    QUOTA_TRACKING = "quota_tracking"
    ACTIVITY_DASHBOARD = "activity_dashboard"

class TimeRange(Enum):
    """Time ranges for performance analysis"""
    MTD = "month_to_date"
    QTD = "quarter_to_date"
    YTD = "year_to_date"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    CURRENT_QUARTER = "current_quarter"

@dataclass
class QuotaTarget:
    """Quota targets for sales reps"""
    rep_id: str
    rep_name: str
    role: AssignmentType

    # Quota targets
    annual_quota: Decimal
    quarterly_quota: Decimal
    monthly_quota: Decimal

    # Current performance
    ytd_closed: Decimal = field(default_factory=lambda: Decimal('0'))
    qtd_closed: Decimal = field(default_factory=lambda: Decimal('0'))
    mtd_closed: Decimal = field(default_factory=lambda: Decimal('0'))

    # Attainment percentages
    ytd_attainment: float = 0.0
    qtd_attainment: float = 0.0
    mtd_attainment: float = 0.0

    # Pipeline metrics
    pipeline_value: Decimal = field(default_factory=lambda: Decimal('0'))
    pipeline_coverage: float = 0.0  # Pipeline / Remaining quota

    # Forecast
    forecast_commit: Decimal = field(default_factory=lambda: Decimal('0'))
    forecast_best_case: Decimal = field(default_factory=lambda: Decimal('0'))
    projected_attainment: float = 0.0

@dataclass
class ActivityMetrics:
    """Activity-based performance metrics"""
    rep_id: str
    time_period: str  # MTD, QTD, etc.

    # Call activities
    calls_made: int = 0
    calls_connected: int = 0
    call_connect_rate: float = 0.0

    # Demo activities
    demos_scheduled: int = 0
    demos_completed: int = 0
    demo_show_rate: float = 0.0

    # Proposal activities
    proposals_sent: int = 0
    proposals_accepted: int = 0
    proposal_acceptance_rate: float = 0.0

    # Email activities
    emails_sent: int = 0
    email_responses: int = 0
    email_response_rate: float = 0.0

    # Meeting activities
    meetings_scheduled: int = 0
    meetings_completed: int = 0

    # Overall activity score
    activity_score: int = 0  # 0-100 based on activity levels

@dataclass
class ConversionMetrics:
    """Conversion rate metrics through sales funnel"""
    rep_id: str
    time_period: str

    # Lead conversion
    leads_assigned: int = 0
    leads_qualified: int = 0
    lead_qualification_rate: float = 0.0

    # Stage conversions
    mql_to_sql: float = 0.0
    sql_to_demo: float = 0.0
    demo_to_pilot: float = 0.0
    pilot_to_contract: float = 0.0
    contract_to_paid: float = 0.0

    # Overall conversion
    lead_to_customer: float = 0.0
    average_deal_size: Decimal = field(default_factory=lambda: Decimal('0'))
    average_sales_cycle: int = 0  # days

@dataclass
class IndividualScorecard:
    """Comprehensive individual performance scorecard"""
    rep_id: str
    rep_name: str
    role: AssignmentType
    time_period: TimeRange

    # Quota performance
    quota_metrics: QuotaTarget

    # Activity metrics
    activity_metrics: ActivityMetrics

    # Conversion metrics
    conversion_metrics: ConversionMetrics

    # Pipeline health
    total_pipeline_value: Decimal = field(default_factory=lambda: Decimal('0'))
    weighted_pipeline_value: Decimal = field(default_factory=lambda: Decimal('0'))
    healthy_deals: int = 0
    at_risk_deals: int = 0
    stalled_deals: int = 0

    # Performance scores
    overall_score: int = 0  # 0-100 composite score
    quota_score: int = 0
    activity_score: int = 0
    pipeline_score: int = 0

    # Rankings
    team_rank: int | None = None
    percentile_rank: float | None = None

    # Recommendations
    improvement_areas: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)

@dataclass
class TeamPerformance:
    """Team-level performance analytics"""
    team_name: str
    time_period: TimeRange

    # Team composition
    total_reps: int = 0
    ae_count: int = 0
    ps_count: int = 0
    enterprise_count: int = 0

    # Aggregate quota performance
    team_quota: Decimal = field(default_factory=lambda: Decimal('0'))
    team_closed: Decimal = field(default_factory=lambda: Decimal('0'))
    team_attainment: float = 0.0

    # Pipeline metrics
    total_pipeline: Decimal = field(default_factory=lambda: Decimal('0'))
    weighted_pipeline: Decimal = field(default_factory=lambda: Decimal('0'))
    average_deal_size: Decimal = field(default_factory=lambda: Decimal('0'))

    # Performance distribution
    reps_at_quota: int = 0
    reps_above_quota: int = 0
    reps_below_quota: int = 0
    quota_attainment_distribution: list[float] = field(default_factory=list)

    # Activity aggregates
    total_activities: int = 0
    average_activity_score: float = 0.0

    # Health metrics
    healthy_pipeline_percentage: float = 0.0
    risk_deals_count: int = 0

class PerformanceDashboardSystem:
    """
    Comprehensive Performance Dashboard System

    Provides real-time analytics and reporting for:
    - Individual rep scorecards and KPIs
    - Team performance and rankings
    - Quota attainment tracking
    - Pipeline health monitoring
    - Activity-based performance metrics
    """

    def __init__(self):
        # In-memory storage for MVP (would be database in production)
        self.quota_targets: dict[str, QuotaTarget] = {}
        self.activity_data: dict[str, list[ActivityMetrics]] = {}
        self.conversion_data: dict[str, list[ConversionMetrics]] = {}
        self.scorecards: dict[str, IndividualScorecard] = {}

        # Initialize sample quota targets and data
        self._initialize_quota_targets()
        self._initialize_sample_data()

        logger.info("📊 Performance Dashboard System initialized")
        logger.info(f"🎯 Quota targets: {len(self.quota_targets)} reps")

    def _initialize_quota_targets(self):
        """Initialize quota targets for sales team"""

        # Sample AE quota targets (high-touch enterprise deals)
        ae_quotas = [
            ("ae_001", "Sarah Chen", Decimal('480000')),      # $480k annual
            ("ae_002", "Marcus Rodriguez", Decimal('520000')), # $520k annual
            ("ae_003", "Jennifer Park", Decimal('600000')),    # $600k annual
        ]

        for rep_id, name, annual_quota in ae_quotas:
            self.quota_targets[rep_id] = QuotaTarget(
                rep_id=rep_id,
                rep_name=name,
                role=AssignmentType.AE,
                annual_quota=annual_quota,
                quarterly_quota=annual_quota / 4,
                monthly_quota=annual_quota / 12
            )

        # Enterprise AE (higher quota)
        self.quota_targets["enterprise_001"] = QuotaTarget(
            rep_id="enterprise_001",
            rep_name="David Kim",
            role=AssignmentType.ENTERPRISE,
            annual_quota=Decimal('1200000'),  # $1.2M annual
            quarterly_quota=Decimal('300000'),
            monthly_quota=Decimal('100000')
        )

        # Partner Success quotas (expansion and retention focused)
        ps_quotas = [
            ("ps_001", "Amanda Foster", Decimal('240000')),   # $240k annual
            ("ps_002", "Carlos Silva", Decimal('280000')),    # $280k annual
        ]

        for rep_id, name, annual_quota in ps_quotas:
            self.quota_targets[rep_id] = QuotaTarget(
                rep_id=rep_id,
                rep_name=name,
                role=AssignmentType.PARTNER_SUCCESS,
                annual_quota=annual_quota,
                quarterly_quota=annual_quota / 4,
                monthly_quota=annual_quota / 12
            )

    def _initialize_sample_data(self):
        """Initialize sample performance data for demonstration"""

        # Sample activity data for current month
        datetime.utcnow().strftime("%Y-%m")

        sample_activities = {
            "ae_001": ActivityMetrics(
                rep_id="ae_001",
                time_period="MTD",
                calls_made=45,
                calls_connected=23,
                call_connect_rate=51.1,
                demos_scheduled=8,
                demos_completed=7,
                demo_show_rate=87.5,
                proposals_sent=4,
                proposals_accepted=3,
                proposal_acceptance_rate=75.0,
                emails_sent=120,
                email_responses=35,
                email_response_rate=29.2,
                meetings_scheduled=12,
                meetings_completed=11,
                activity_score=82
            ),
            "ae_002": ActivityMetrics(
                rep_id="ae_002",
                time_period="MTD",
                calls_made=52,
                calls_connected=28,
                call_connect_rate=53.8,
                demos_scheduled=10,
                demos_completed=9,
                demo_show_rate=90.0,
                proposals_sent=5,
                proposals_accepted=4,
                proposal_acceptance_rate=80.0,
                emails_sent=140,
                email_responses=42,
                email_response_rate=30.0,
                meetings_scheduled=15,
                meetings_completed=14,
                activity_score=88
            ),
            "ps_001": ActivityMetrics(
                rep_id="ps_001",
                time_period="MTD",
                calls_made=38,
                calls_connected=32,
                call_connect_rate=84.2,
                demos_scheduled=6,
                demos_completed=6,
                demo_show_rate=100.0,
                proposals_sent=8,
                proposals_accepted=7,
                proposal_acceptance_rate=87.5,
                emails_sent=95,
                email_responses=48,
                email_response_rate=50.5,
                meetings_scheduled=20,
                meetings_completed=19,
                activity_score=91
            )
        }

        for rep_id, activity in sample_activities.items():
            if rep_id not in self.activity_data:
                self.activity_data[rep_id] = []
            self.activity_data[rep_id].append(activity)

        # Sample conversion data
        sample_conversions = {
            "ae_001": ConversionMetrics(
                rep_id="ae_001",
                time_period="QTD",
                leads_assigned=25,
                leads_qualified=18,
                lead_qualification_rate=72.0,
                mql_to_sql=75.0,
                sql_to_demo=65.0,
                demo_to_pilot=45.0,
                pilot_to_contract=80.0,
                contract_to_paid=90.0,
                lead_to_customer=18.7,
                average_deal_size=Decimal('35000'),
                average_sales_cycle=85
            ),
            "ae_002": ConversionMetrics(
                rep_id="ae_002",
                time_period="QTD",
                leads_assigned=22,
                leads_qualified=17,
                lead_qualification_rate=77.3,
                mql_to_sql=80.0,
                sql_to_demo=70.0,
                demo_to_pilot=50.0,
                pilot_to_contract=85.0,
                contract_to_paid=95.0,
                lead_to_customer=22.8,
                average_deal_size=Decimal('42000'),
                average_sales_cycle=78
            )
        }

        for rep_id, conversion in sample_conversions.items():
            if rep_id not in self.conversion_data:
                self.conversion_data[rep_id] = []
            self.conversion_data[rep_id].append(conversion)

    def update_quota_performance(self, rep_id: str, closed_deals: list[Deal]):
        """Update quota performance based on closed deals"""
        try:
            quota_target = self.quota_targets.get(rep_id)
            if not quota_target:
                logger.warning(f"No quota target found for rep {rep_id}")
                return

            # Calculate performance for different time periods
            now = datetime.utcnow()
            ytd_start = datetime(now.year, 1, 1)
            qtd_start = datetime(now.year, ((now.month - 1) // 3) * 3 + 1, 1)
            mtd_start = datetime(now.year, now.month, 1)

            # Filter closed deals by time periods
            ytd_deals = [d for d in closed_deals if d.last_updated >= ytd_start and d.stage == DealStage.PAID]
            qtd_deals = [d for d in closed_deals if d.last_updated >= qtd_start and d.stage == DealStage.PAID]
            mtd_deals = [d for d in closed_deals if d.last_updated >= mtd_start and d.stage == DealStage.PAID]

            # Calculate closed revenue
            quota_target.ytd_closed = sum(d.estimated_acv for d in ytd_deals)
            quota_target.qtd_closed = sum(d.estimated_acv for d in qtd_deals)
            quota_target.mtd_closed = sum(d.estimated_acv for d in mtd_deals)

            # Calculate attainment percentages
            quota_target.ytd_attainment = float(quota_target.ytd_closed / quota_target.annual_quota * 100)
            quota_target.qtd_attainment = float(quota_target.qtd_closed / quota_target.quarterly_quota * 100)
            quota_target.mtd_attainment = float(quota_target.mtd_closed / quota_target.monthly_quota * 100)

            logger.info(f"📈 Quota updated: {quota_target.rep_name} | YTD: {quota_target.ytd_attainment:.1f}%")

        except Exception as e:
            logger.error(f"Failed to update quota performance: {str(e)}")
            raise

    def calculate_pipeline_coverage(self, rep_id: str, pipeline_deals: list[Deal]) -> float:
        """Calculate pipeline coverage ratio for rep"""
        try:
            quota_target = self.quota_targets.get(rep_id)
            if not quota_target:
                return 0.0

            # Calculate remaining quota for the year
            remaining_quota = quota_target.annual_quota - quota_target.ytd_closed

            # Calculate weighted pipeline value
            weighted_pipeline = sum(d.weighted_value for d in pipeline_deals)
            quota_target.pipeline_value = sum(d.estimated_acv for d in pipeline_deals)

            # Pipeline coverage = Weighted Pipeline / Remaining Quota
            if remaining_quota > 0:
                coverage = float(weighted_pipeline / remaining_quota)
                quota_target.pipeline_coverage = coverage
                return coverage
            quota_target.pipeline_coverage = 0.0
            return 0.0

        except Exception as e:
            logger.error(f"Failed to calculate pipeline coverage: {str(e)}")
            return 0.0

    def generate_individual_scorecard(self, rep_id: str, time_period: TimeRange = TimeRange.MTD) -> IndividualScorecard:
        """Generate comprehensive individual performance scorecard"""
        try:
            quota_target = self.quota_targets.get(rep_id)
            if not quota_target:
                raise ValueError(f"No quota target found for rep {rep_id}")

            # Get latest activity and conversion metrics
            latest_activity = None
            if rep_id in self.activity_data and self.activity_data[rep_id]:
                latest_activity = self.activity_data[rep_id][-1]
            else:
                # Create default activity metrics
                latest_activity = ActivityMetrics(rep_id=rep_id, time_period=time_period.value)

            latest_conversion = None
            if rep_id in self.conversion_data and self.conversion_data[rep_id]:
                latest_conversion = self.conversion_data[rep_id][-1]
            else:
                # Create default conversion metrics
                latest_conversion = ConversionMetrics(rep_id=rep_id, time_period=time_period.value)

            # Calculate performance scores
            quota_score = min(100, int(quota_target.qtd_attainment))
            activity_score = latest_activity.activity_score

            # Pipeline score based on coverage and health
            pipeline_score = 50  # Default baseline
            if quota_target.pipeline_coverage >= 3.0:
                pipeline_score = 90
            elif quota_target.pipeline_coverage >= 2.0:
                pipeline_score = 75
            elif quota_target.pipeline_coverage >= 1.5:
                pipeline_score = 60

            # Overall composite score
            overall_score = int(
                (quota_score * 0.4) +
                (activity_score * 0.3) +
                (pipeline_score * 0.3)
            )

            # Generate improvement recommendations
            improvement_areas = []
            action_items = []

            if quota_score < 70:
                improvement_areas.append("Quota Attainment")
                action_items.append("Focus on closing pipeline deals in current quarter")

            if latest_activity.call_connect_rate < 50:
                improvement_areas.append("Call Connect Rate")
                action_items.append("Improve call timing and voicemail strategy")

            if latest_activity.demo_show_rate < 80:
                improvement_areas.append("Demo Show Rate")
                action_items.append("Send better demo prep materials and confirmations")

            if quota_target.pipeline_coverage < 2.0:
                improvement_areas.append("Pipeline Coverage")
                action_items.append("Increase prospecting activity to build pipeline")

            scorecard = IndividualScorecard(
                rep_id=rep_id,
                rep_name=quota_target.rep_name,
                role=quota_target.role,
                time_period=time_period,
                quota_metrics=quota_target,
                activity_metrics=latest_activity,
                conversion_metrics=latest_conversion,
                overall_score=overall_score,
                quota_score=quota_score,
                activity_score=activity_score,
                pipeline_score=pipeline_score,
                improvement_areas=improvement_areas,
                action_items=action_items
            )

            # Store scorecard
            self.scorecards[rep_id] = scorecard

            logger.info(f"📊 Scorecard generated: {quota_target.rep_name} | Overall: {overall_score}/100")
            return scorecard

        except Exception as e:
            logger.error(f"Failed to generate scorecard: {str(e)}")
            raise

    def generate_team_performance(self, team_name: str = "Sales Team", time_period: TimeRange = TimeRange.QTD) -> TeamPerformance:
        """Generate team-level performance analytics"""
        try:
            team_quotas = list(self.quota_targets.values())

            if not team_quotas:
                raise ValueError("No quota targets found for team analysis")

            # Team composition
            ae_reps = [q for q in team_quotas if q.role == AssignmentType.AE]
            ps_reps = [q for q in team_quotas if q.role == AssignmentType.PARTNER_SUCCESS]
            enterprise_reps = [q for q in team_quotas if q.role == AssignmentType.ENTERPRISE]

            # Aggregate quota performance
            if time_period == TimeRange.QTD:
                team_quota = sum(q.quarterly_quota for q in team_quotas)
                team_closed = sum(q.qtd_closed for q in team_quotas)
            elif time_period == TimeRange.YTD:
                team_quota = sum(q.annual_quota for q in team_quotas)
                team_closed = sum(q.ytd_closed for q in team_quotas)
            else:  # MTD
                team_quota = sum(q.monthly_quota for q in team_quotas)
                team_closed = sum(q.mtd_closed for q in team_quotas)

            team_attainment = float(team_closed / team_quota * 100) if team_quota > 0 else 0

            # Performance distribution
            attainment_percentages = []
            reps_at_quota = 0
            reps_above_quota = 0
            reps_below_quota = 0

            for quota in team_quotas:
                if time_period == TimeRange.QTD:
                    attainment = quota.qtd_attainment
                elif time_period == TimeRange.YTD:
                    attainment = quota.ytd_attainment
                else:
                    attainment = quota.mtd_attainment

                attainment_percentages.append(attainment)

                if attainment >= 100:
                    reps_above_quota += 1
                elif attainment >= 90:
                    reps_at_quota += 1
                else:
                    reps_below_quota += 1

            # Activity aggregation
            total_activities = 0
            activity_scores = []

            for rep_id in self.activity_data:
                if self.activity_data[rep_id]:
                    latest_activity = self.activity_data[rep_id][-1]
                    total_activities += (
                        latest_activity.calls_made +
                        latest_activity.demos_completed +
                        latest_activity.proposals_sent +
                        latest_activity.meetings_completed
                    )
                    activity_scores.append(latest_activity.activity_score)

            avg_activity_score = sum(activity_scores) / len(activity_scores) if activity_scores else 0

            team_performance = TeamPerformance(
                team_name=team_name,
                time_period=time_period,
                total_reps=len(team_quotas),
                ae_count=len(ae_reps),
                ps_count=len(ps_reps),
                enterprise_count=len(enterprise_reps),
                team_quota=team_quota,
                team_closed=team_closed,
                team_attainment=team_attainment,
                total_pipeline=sum(q.pipeline_value for q in team_quotas),
                reps_at_quota=reps_at_quota,
                reps_above_quota=reps_above_quota,
                reps_below_quota=reps_below_quota,
                quota_attainment_distribution=attainment_percentages,
                total_activities=total_activities,
                average_activity_score=avg_activity_score
            )

            logger.info(f"📊 Team performance: {team_name} | Attainment: {team_attainment:.1f}%")
            return team_performance

        except Exception as e:
            logger.error(f"Failed to generate team performance: {str(e)}")
            raise

    def get_quota_leaderboard(self, time_period: TimeRange = TimeRange.QTD) -> list[dict[str, Any]]:
        """Get quota attainment leaderboard"""
        try:
            leaderboard = []

            for quota in self.quota_targets.values():
                if time_period == TimeRange.QTD:
                    attainment = quota.qtd_attainment
                    closed = quota.qtd_closed
                    target = quota.quarterly_quota
                elif time_period == TimeRange.YTD:
                    attainment = quota.ytd_attainment
                    closed = quota.ytd_closed
                    target = quota.annual_quota
                else:  # MTD
                    attainment = quota.mtd_attainment
                    closed = quota.mtd_closed
                    target = quota.monthly_quota

                leaderboard.append({
                    "rep_id": quota.rep_id,
                    "rep_name": quota.rep_name,
                    "role": quota.role.value,
                    "attainment_percentage": attainment,
                    "closed_revenue": float(closed),
                    "quota_target": float(target),
                    "pipeline_coverage": quota.pipeline_coverage,
                    "gap_to_quota": float(target - closed)
                })

            # Sort by attainment percentage (descending)
            leaderboard.sort(key=lambda x: x["attainment_percentage"], reverse=True)

            # Add rankings
            for i, rep in enumerate(leaderboard):
                rep["rank"] = i + 1
                rep["percentile"] = ((len(leaderboard) - i) / len(leaderboard)) * 100

            return leaderboard

        except Exception as e:
            logger.error(f"Failed to generate quota leaderboard: {str(e)}")
            raise

    def get_activity_leaderboard(self, time_period: TimeRange = TimeRange.MTD) -> list[dict[str, Any]]:
        """Get activity performance leaderboard"""
        try:
            leaderboard = []

            for rep_id, activities in self.activity_data.items():
                if not activities:
                    continue

                latest_activity = activities[-1]
                quota = self.quota_targets.get(rep_id)

                leaderboard.append({
                    "rep_id": rep_id,
                    "rep_name": quota.rep_name if quota else "Unknown",
                    "role": quota.role.value if quota else "Unknown",
                    "activity_score": latest_activity.activity_score,
                    "calls_made": latest_activity.calls_made,
                    "demos_completed": latest_activity.demos_completed,
                    "proposals_sent": latest_activity.proposals_sent,
                    "call_connect_rate": latest_activity.call_connect_rate,
                    "demo_show_rate": latest_activity.demo_show_rate,
                    "proposal_acceptance_rate": latest_activity.proposal_acceptance_rate
                })

            # Sort by activity score (descending)
            leaderboard.sort(key=lambda x: x["activity_score"], reverse=True)

            # Add rankings
            for i, rep in enumerate(leaderboard):
                rep["rank"] = i + 1

            return leaderboard

        except Exception as e:
            logger.error(f"Failed to generate activity leaderboard: {str(e)}")
            raise

    def get_executive_dashboard(self) -> dict[str, Any]:
        """Generate executive-level dashboard summary"""
        try:
            team_performance = self.generate_team_performance()
            quota_leaderboard = self.get_quota_leaderboard()

            # Calculate key metrics
            total_quota = float(team_performance.team_quota)
            total_closed = float(team_performance.team_closed)
            total_pipeline = float(team_performance.total_pipeline)

            # Risk analysis
            at_risk_reps = len([rep for rep in quota_leaderboard if rep["attainment_percentage"] < 70])
            high_performers = len([rep for rep in quota_leaderboard if rep["attainment_percentage"] > 100])

            # Activity insights
            total_team_activities = team_performance.total_activities
            avg_activity_score = team_performance.average_activity_score

            return {
                "executive_summary": {
                    "total_team_quota": total_quota,
                    "total_closed_revenue": total_closed,
                    "overall_attainment": team_performance.team_attainment,
                    "total_pipeline_value": total_pipeline,
                    "pipeline_coverage": (total_pipeline / max(total_quota - total_closed, 1)),
                    "forecast_accuracy": 85.0  # Would calculate from historical data
                },
                "team_composition": {
                    "total_reps": team_performance.total_reps,
                    "ae_count": team_performance.ae_count,
                    "partner_success_count": team_performance.ps_count,
                    "enterprise_count": team_performance.enterprise_count
                },
                "performance_distribution": {
                    "high_performers": high_performers,
                    "on_track_reps": team_performance.reps_at_quota,
                    "at_risk_reps": at_risk_reps,
                    "below_quota_reps": team_performance.reps_below_quota
                },
                "activity_metrics": {
                    "total_team_activities": total_team_activities,
                    "average_activity_score": avg_activity_score,
                    "activity_trend": "increasing"  # Would calculate from time series
                },
                "top_performers": quota_leaderboard[:3],  # Top 3 performers
                "attention_needed": [rep for rep in quota_leaderboard if rep["attainment_percentage"] < 50],
                "generated_at": datetime.utcnow().isoformat()
            }


        except Exception as e:
            logger.error(f"Failed to generate executive dashboard: {str(e)}")
            raise

    def get_pipeline_health_dashboard(self, rep_id: str | None = None) -> dict[str, Any]:
        """Generate pipeline health dashboard"""
        try:
            # This would integrate with pipeline management system
            # For now, creating sample structure

            return {
                "pipeline_overview": {
                    "total_deals": 0,
                    "total_value": 0,
                    "weighted_value": 0,
                    "average_deal_size": 0
                },
                "stage_distribution": {
                    "mql": {"count": 0, "value": 0},
                    "sql": {"count": 0, "value": 0},
                    "demo": {"count": 0, "value": 0},
                    "pilot": {"count": 0, "value": 0},
                    "contract": {"count": 0, "value": 0}
                },
                "health_indicators": {
                    "healthy_deals": 0,
                    "at_risk_deals": 0,
                    "stalled_deals": 0,
                    "critical_deals": 0
                },
                "velocity_metrics": {
                    "average_sales_cycle": 0,
                    "stage_durations": {},
                    "conversion_rates": {}
                },
                "forecast": {
                    "commit_category": 0,
                    "best_case_category": 0,
                    "pipeline_category": 0
                },
                "generated_at": datetime.utcnow().isoformat()
            }


        except Exception as e:
            logger.error(f"Failed to generate pipeline health dashboard: {str(e)}")
            raise


# Global service instance
performance_dashboard_system = PerformanceDashboardSystem()
