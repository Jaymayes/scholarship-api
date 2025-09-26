"""
Priority 2 Day 2: Flatline and Abrupt Change Alerts
Prometheus alerting rules for domain metrics monitoring
"""

from typing import Any

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)

# Priority 2 Day 2: Alerting Rules for Domain Metrics
ALERTING_RULES = {
    "groups": [
        {
            "name": "scholarship_api_domain_metrics",
            "rules": [
                # Flatline Detection - No activity for extended periods
                {
                    "alert": "SearchRequestsFlatline",
                    "expr": "increase(search_requests_total[5m]) == 0",
                    "for": "10m",
                    "labels": {
                        "severity": "warning",
                        "component": "search_engine"
                    },
                    "annotations": {
                        "summary": "Search requests have flatlined",
                        "description": "No search requests received in the last 10 minutes on {{ $labels.instance }}"
                    }
                },
                {
                    "alert": "ScholarshipIndexingFlatline",
                    "expr": "increase(scholarships_indexed_total[30m]) == 0",
                    "for": "1h",
                    "labels": {
                        "severity": "warning",
                        "component": "data_ingestion"
                    },
                    "annotations": {
                        "summary": "Scholarship indexing has stopped",
                        "description": "No scholarships have been indexed in the last hour on {{ $labels.instance }}"
                    }
                },
                {
                    "alert": "UserInteractionsFlatline",
                    "expr": "increase(user_interactions_total[15m]) == 0",
                    "for": "30m",
                    "labels": {
                        "severity": "info",
                        "component": "user_engagement"
                    },
                    "annotations": {
                        "summary": "User interactions have decreased significantly",
                        "description": "No user interactions recorded in the last 30 minutes on {{ $labels.instance }}"
                    }
                },

                # Abrupt Change Detection - Significant increases/decreases
                {
                    "alert": "SearchErrorRateSpike",
                    "expr": "rate(search_requests_error_total[5m]) / rate(search_requests_total[5m]) > 0.1",
                    "for": "2m",
                    "labels": {
                        "severity": "critical",
                        "component": "search_engine"
                    },
                    "annotations": {
                        "summary": "Search error rate is abnormally high",
                        "description": "Search error rate is {{ $value | humanizePercentage }} on {{ $labels.instance }}, above 10% threshold"
                    }
                },
                {
                    "alert": "SearchResultCountAnomalous",
                    "expr": "histogram_quantile(0.95, rate(search_results_count_bucket[5m])) > 1000 or histogram_quantile(0.95, rate(search_results_count_bucket[5m])) < 1",
                    "for": "5m",
                    "labels": {
                        "severity": "warning",
                        "component": "search_engine"
                    },
                    "annotations": {
                        "summary": "Search result counts are anomalous",
                        "description": "95th percentile search result count is {{ $value }} on {{ $labels.instance }}, which is outside normal range"
                    }
                },
                {
                    "alert": "EligibilityCheckFailureSpike",
                    "expr": "rate(eligibility_checks_error_total[5m]) / rate(eligibility_checks_total[5m]) > 0.05",
                    "for": "3m",
                    "labels": {
                        "severity": "warning",
                        "component": "eligibility_engine"
                    },
                    "annotations": {
                        "summary": "Eligibility check failures are elevated",
                        "description": "Eligibility check error rate is {{ $value | humanizePercentage }} on {{ $labels.instance }}, above 5% threshold"
                    }
                },

                # Performance Degradation
                {
                    "alert": "SearchQueryLatencyHigh",
                    "expr": "histogram_quantile(0.95, rate(search_query_duration_seconds_bucket[5m])) > 2.0",
                    "for": "5m",
                    "labels": {
                        "severity": "warning",
                        "component": "search_engine"
                    },
                    "annotations": {
                        "summary": "Search query latency is high",
                        "description": "95th percentile search query duration is {{ $value }}s on {{ $labels.instance }}, above 2s threshold"
                    }
                },

                # Data Consistency - Fixed: Handle label mismatch with aggregation
                {
                    "alert": "ActiveScholarshipsCountInconsistent",
                    "expr": "abs(active_scholarships_total - sum(indexed_active_scholarships)) > 5",
                    "for": "15m",
                    "labels": {
                        "severity": "warning",
                        "component": "data_consistency"
                    },
                    "annotations": {
                        "summary": "Active scholarships count inconsistent between metrics",
                        "description": "Active scholarships gauge differs from indexed count by more than 5 on {{ $labels.instance }}"
                    }
                },

                # Service Health
                {
                    "alert": "MetricsCollectionDown",
                    "expr": "up{job=\"scholarship_api\"} == 0",
                    "for": "1m",
                    "labels": {
                        "severity": "critical",
                        "component": "monitoring"
                    },
                    "annotations": {
                        "summary": "Metrics collection is down",
                        "description": "Prometheus cannot scrape metrics from {{ $labels.instance }}"
                    }
                }
            ]
        }
    ]
}

class AlertManager:
    """Manages alerting rules and notifications for domain metrics"""

    def __init__(self):
        self.rules = ALERTING_RULES
        self.alert_history = []

    def generate_prometheus_rules(self) -> str:
        """Generate Prometheus alerting rules YAML"""
        return yaml.dump(self.rules, default_flow_style=False, sort_keys=False)

    def save_rules_file(self, filepath: str = "alerting-rules.yml"):
        """Save alerting rules to file for Prometheus"""
        try:
            with open(filepath, 'w') as f:
                f.write(self.generate_prometheus_rules())

            logger.info(f"Alerting rules saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save alerting rules: {e}")
            raise

    def validate_alert_rules(self) -> dict[str, Any]:
        """Validate alert rules configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "rule_count": 0
        }

        try:
            for group in self.rules["groups"]:
                group.get("name", "unnamed")
                rules = group.get("rules", [])
                validation_results["rule_count"] += len(rules)

                for rule in rules:
                    # Check required fields
                    required_fields = ["alert", "expr", "for", "labels", "annotations"]
                    missing_fields = [field for field in required_fields if field not in rule]

                    if missing_fields:
                        validation_results["errors"].append(f"Rule '{rule.get('alert', 'unknown')}' missing fields: {missing_fields}")
                        validation_results["valid"] = False

                    # Check severity levels
                    severity = rule.get("labels", {}).get("severity")
                    valid_severities = ["critical", "warning", "info"]
                    if severity not in valid_severities:
                        validation_results["warnings"].append(f"Rule '{rule.get('alert')}' has invalid severity: {severity}")

                    # Check expression syntax (basic validation)
                    expr = rule.get("expr", "")
                    if not expr or "==" not in expr and ">" not in expr and "<" not in expr:
                        validation_results["warnings"].append(f"Rule '{rule.get('alert')}' has potentially invalid expression")

            logger.info(f"Alert rules validation: {validation_results['rule_count']} rules checked")

        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")

        return validation_results

    def get_alert_summary(self) -> dict[str, Any]:
        """Get summary of configured alerts"""
        summary = {
            "total_groups": len(self.rules["groups"]),
            "total_rules": 0,
            "by_severity": {"critical": 0, "warning": 0, "info": 0},
            "by_component": {}
        }

        for group in self.rules["groups"]:
            rules = group.get("rules", [])
            summary["total_rules"] += len(rules)

            for rule in rules:
                # Count by severity
                severity = rule.get("labels", {}).get("severity", "unknown")
                if severity in summary["by_severity"]:
                    summary["by_severity"][severity] += 1

                # Count by component
                component = rule.get("labels", {}).get("component", "unknown")
                summary["by_component"][component] = summary["by_component"].get(component, 0) + 1

        return summary

# Singleton alert manager
alert_manager = AlertManager()

def setup_alerting() -> AlertManager:
    """Initialize alerting system"""
    logger.info("🚨 Setting up domain metrics alerting")

    # Validate rules
    validation = alert_manager.validate_alert_rules()
    if not validation["valid"]:
        logger.error(f"Alert rules validation failed: {validation['errors']}")
        raise ValueError(f"Invalid alert rules: {validation['errors']}")

    if validation["warnings"]:
        logger.warning(f"Alert rules warnings: {validation['warnings']}")

    # Generate rules file
    alert_manager.save_rules_file("observability/alerting-rules.yml")

    summary = alert_manager.get_alert_summary()
    logger.info(f"Alerting configured: {summary['total_rules']} rules across {summary['total_groups']} groups")
    logger.info(f"Severity distribution: {summary['by_severity']}")
    logger.info(f"Component distribution: {summary['by_component']}")

    return alert_manager

def get_alert_manager() -> AlertManager:
    """Get the singleton alert manager"""
    return alert_manager
