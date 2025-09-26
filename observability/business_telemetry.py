"""
Business Telemetry and KPI Instrumentation
Priority 3: Revenue and adoption tracking with SLO-to-business linkage
"""
import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

from utils.logger import setup_logger

logger = setup_logger()

class BusinessTelemetryService:
    """Business KPI tracking and SLO-to-business impact correlation"""

    def __init__(self):
        self.base_labels = ["env", "service", "version"]

        # Core business metrics (prefixed to avoid collisions)
        self.business_search_requests_total = Counter(
            'business_search_requests_total',
            'Total business search requests by type and outcome',
            ['search_type', 'outcome', 'user_type'] + self.base_labels
        )

        self.business_search_results_count = Histogram(
            'business_search_results_count',
            'Distribution of business search result counts',
            ['search_type', 'user_type'] + self.base_labels,
            buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500, 1000]
        )

        self.provider_keys_active = Gauge(
            'provider_keys_active_total',
            'Number of active provider API keys',
            ['provider_type'] + self.base_labels
        )

        self.daily_active_consumer_keys = Gauge(
            'daily_active_consumer_keys',
            'Daily active consumer API keys',
            self.base_labels
        )

        # Student engagement metrics
        self.student_interactions_total = Counter(
            'student_interactions_total',
            'Student interactions by action type',
            ['action', 'scholarship_type', 'user_tier'] + self.base_labels
        )

        self.application_actions_total = Counter(
            'application_actions_total',
            'Application lifecycle actions',
            ['action', 'outcome'] + self.base_labels  # start, submit, abandon
        )

        # Business value metrics
        self.revenue_events_total = Counter(
            'revenue_events_total',
            'Revenue-generating events',
            ['event_type', 'tier', 'amount_bucket'] + self.base_labels
        )

        self.customer_satisfaction_score = Gauge(
            'customer_satisfaction_score',
            'Customer satisfaction score by tier',
            ['customer_tier'] + self.base_labels
        )

        # SLO to business impact correlation
        self.slo_breach_business_impact = Counter(
            'slo_breach_business_impact_total',
            'Business impact events from SLO breaches',
            ['breach_type', 'impact_category', 'severity'] + self.base_labels
        )

        self.churn_risk_score = Gauge(
            'churn_risk_score',
            'Customer churn risk score',
            ['customer_tier', 'risk_category'] + self.base_labels
        )

        # Initialize base labels
        self._set_base_labels()

    def _set_base_labels(self):
        """Set consistent base labels across all metrics"""
        from config.settings import settings

        self.labels = {
            "env": settings.environment.value,
            "service": "scholarship_api",
            "version": settings.api_version
        }

        logger.info(f"📊 Business telemetry initialized with labels: {self.labels}")

    def track_search_request(self, search_type: str, outcome: str, user_type: str = "student"):
        """Track search request with business context"""
        self.business_search_requests_total.labels(
            search_type=search_type,
            outcome=outcome,
            user_type=user_type,
            **self.labels
        ).inc()

        logger.debug(f"📈 Search tracked: {search_type}/{outcome}/{user_type}")

    def track_search_results(self, count: int, search_type: str, user_type: str = "student"):
        """Track search result distribution"""
        self.business_search_results_count.labels(
            search_type=search_type,
            user_type=user_type,
            **self.labels
        ).observe(count)

        logger.debug(f"📊 Search results: {count} for {search_type}/{user_type}")

    def update_active_provider_keys(self, provider_type: str, count: int):
        """Update active provider API keys count"""
        self.provider_keys_active.labels(
            provider_type=provider_type,
            **self.labels
        ).set(count)

        logger.debug(f"🔑 Provider keys updated: {provider_type} = {count}")

    def update_daily_active_consumers(self, count: int):
        """Update daily active consumer keys"""
        self.daily_active_consumer_keys.labels(**self.labels).set(count)
        logger.debug(f"👥 Daily active consumers: {count}")

    def track_student_interaction(self, action: str, scholarship_type: str = "general",
                                 user_tier: str = "free"):
        """Track student engagement actions"""
        self.student_interactions_total.labels(
            action=action,
            scholarship_type=scholarship_type,
            user_tier=user_tier,
            **self.labels
        ).inc()

        logger.debug(f"🎓 Student interaction: {action}/{scholarship_type}/{user_tier}")

    def track_application_action(self, action: str, outcome: str = "success"):
        """Track application lifecycle events"""
        self.application_actions_total.labels(
            action=action,
            outcome=outcome,
            **self.labels
        ).inc()

        logger.debug(f"📝 Application action: {action}/{outcome}")

    def track_revenue_event(self, event_type: str, amount: float, tier: str = "standard"):
        """Track revenue-generating events"""
        # Bucket amounts for privacy
        if amount == 0:
            amount_bucket = "free"
        elif amount <= 10:
            amount_bucket = "0-10"
        elif amount <= 50:
            amount_bucket = "10-50"
        elif amount <= 100:
            amount_bucket = "50-100"
        else:
            amount_bucket = "100+"

        self.revenue_events_total.labels(
            event_type=event_type,
            tier=tier,
            amount_bucket=amount_bucket,
            **self.labels
        ).inc()

        logger.debug(f"💰 Revenue event: {event_type}/{tier}/{amount_bucket}")

    def update_customer_satisfaction(self, score: float, customer_tier: str = "free"):
        """Update customer satisfaction score"""
        self.customer_satisfaction_score.labels(
            customer_tier=customer_tier,
            **self.labels
        ).set(score)

        logger.debug(f"😊 Customer satisfaction: {customer_tier} = {score}")

    def track_slo_breach_impact(self, breach_type: str, impact_category: str,
                               severity: str = "medium"):
        """Track business impact from SLO breaches"""
        self.slo_breach_business_impact.labels(
            breach_type=breach_type,
            impact_category=impact_category,
            severity=severity,
            **self.labels
        ).inc()

        logger.warning(f"⚠️ SLO breach impact: {breach_type}/{impact_category}/{severity}")

    def update_churn_risk(self, risk_score: float, customer_tier: str,
                         risk_category: str = "latency"):
        """Update customer churn risk based on SLO performance"""
        self.churn_risk_score.labels(
            customer_tier=customer_tier,
            risk_category=risk_category,
            **self.labels
        ).set(risk_score)

        logger.debug(f"⚠️ Churn risk: {customer_tier}/{risk_category} = {risk_score}")

    def calculate_business_risk_from_slo(self, slo_breach_duration_minutes: float,
                                        affected_requests: int) -> dict[str, Any]:
        """Calculate projected business impact from SLO breach"""

        # Business impact model (simplified)
        # In production, this would use historical data and ML models

        # Estimated churn rate increase per minute of downtime
        churn_rate_increase_per_minute = 0.001  # 0.1% per minute

        # Estimated CAC (Customer Acquisition Cost)
        average_cac = 50.0  # $50 per customer

        # Current customer base estimate
        estimated_customers = 1000

        # Calculate impact
        projected_churn_increase = slo_breach_duration_minutes * churn_rate_increase_per_minute
        projected_lost_customers = estimated_customers * projected_churn_increase
        projected_cac_waste = projected_lost_customers * average_cac

        # Revenue impact (simplified)
        average_revenue_per_customer = 25.0  # $25 monthly
        projected_revenue_loss = projected_lost_customers * average_revenue_per_customer

        impact = {
            "slo_breach_duration_minutes": slo_breach_duration_minutes,
            "affected_requests": affected_requests,
            "projected_churn_increase_percent": projected_churn_increase * 100,
            "projected_lost_customers": round(projected_lost_customers, 2),
            "projected_cac_waste_dollars": round(projected_cac_waste, 2),
            "projected_revenue_loss_dollars": round(projected_revenue_loss, 2),
            "total_business_impact_dollars": round(projected_cac_waste + projected_revenue_loss, 2)
        }

        # Track the business impact
        severity = "critical" if impact["total_business_impact_dollars"] > 500 else \
                  "high" if impact["total_business_impact_dollars"] > 100 else "medium"

        self.track_slo_breach_impact("latency", "revenue_loss", severity)

        logger.warning(f"💸 Projected business impact: ${impact['total_business_impact_dollars']}")

        return impact

    def get_business_health_summary(self) -> dict[str, Any]:
        """Get current business health summary"""
        return {
            "timestamp": time.time(),
            "metrics_enabled": True,
            "tracking_components": [
                "search_requests",
                "student_interactions",
                "application_actions",
                "revenue_events",
                "slo_business_impact"
            ],
            "base_labels": self.labels,
            "kpi_categories": {
                "engagement": ["search_requests_total", "student_interactions_total"],
                "conversion": ["application_actions_total"],
                "revenue": ["revenue_events_total"],
                "satisfaction": ["customer_satisfaction_score"],
                "risk": ["churn_risk_score", "slo_breach_business_impact_total"]
            }
        }

# Global business telemetry service
business_telemetry_service = BusinessTelemetryService()
