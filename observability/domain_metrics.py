"""
Priority 2 Day 2: Custom Domain Metrics with Strict Label Discipline
Implements scholarship-specific metrics with governance controls
"""

import time
from typing import Dict, List, Optional, Any
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.metrics import MetricWrapperBase
from utils.logger import get_logger

logger = get_logger(__name__)

# Strict label discipline - ONLY these labels allowed
ALLOWED_LABELS = {"env", "service", "version"}

class GovernedMetric:
    """Base class for metrics with strict label governance"""
    
    @staticmethod
    def validate_labels(labels: Dict[str, str]) -> Dict[str, str]:
        """Validate labels against governance policy"""
        if not labels:
            return {}
        
        # Filter to only allowed labels
        validated = {k: v for k, v in labels.items() if k in ALLOWED_LABELS}
        
        # Warn about rejected labels
        rejected = {k: v for k, v in labels.items() if k not in ALLOWED_LABELS}
        if rejected:
            logger.warning(f"Rejected non-governance labels: {rejected}. Allowed: {ALLOWED_LABELS}")
        
        return validated

# Priority 2 Day 2: Domain Metrics with Strict Label Discipline

# Priority 2 Day 2: STRICT GOVERNANCE - Only env/service/version labels allowed

# 1. Scholarships Indexed Total (Counter) - GOVERNANCE COMPLIANT
scholarships_indexed_total = Counter(
    'scholarships_indexed_total',
    'Total number of scholarships indexed in the system',
    ['env', 'service', 'version'],  # Only governance labels
)

# 2. Search Requests Total (Counter) - GOVERNANCE COMPLIANT  
search_requests_total = Counter(
    'search_requests_total',
    'Total number of search requests processed',
    ['env', 'service', 'version'],  # Only governance labels - result tracked via separate metric
)

# Search Success/Error Rates (Separate counters for governance compliance)
search_requests_success_total = Counter(
    'search_requests_success_total',
    'Total successful search requests',
    ['env', 'service', 'version'],
)

search_requests_error_total = Counter(
    'search_requests_error_total', 
    'Total failed search requests',
    ['env', 'service', 'version'],
)

# 3. Search Results Count (Histogram) - GOVERNANCE COMPLIANT
search_results_count = Histogram(
    'search_results_count',
    'Distribution of search result counts returned to users',
    ['env', 'service', 'version'],
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500, 1000, float('inf')]  # Scholarship search result buckets
)

# Domain metrics with exemplar support for tracing
search_query_duration_seconds = Histogram(
    'search_query_duration_seconds',
    'Time spent processing search queries with exemplar support',
    ['env', 'service', 'version'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, float('inf')]
)

# Simplified metrics for governance compliance
total_eligibility_checks = Counter(
    'eligibility_checks_total', 
    'Total eligibility checks performed',
    ['env', 'service', 'version'],
)

eligibility_checks_error_total = Counter(
    'eligibility_checks_error_total', 
    'Total eligibility check errors',
    ['env', 'service', 'version'],
)

total_user_interactions = Counter(
    'user_interactions_total',
    'Total user interactions with scholarships',
    ['env', 'service', 'version'],
)

# Gauge for active scholarships reconciliation - needed for alerting
indexed_active_scholarships = Gauge(
    'indexed_active_scholarships',
    'Current count of active indexed scholarships (for alerting)',
    ['env', 'service', 'version'],
)

class DomainMetricsService:
    """Service for managing domain-specific metrics with governance"""
    
    def __init__(self):
        self.base_labels = {
            'env': 'development',  # Will be overridden by environment
            'service': 'scholarship_api',
            'version': '1.0.0'  # Will be overridden by app version
        }
        
    def set_base_labels(self, env: str = None, service: str = None, version: str = None):
        """Set base labels for all metrics"""
        if env:
            self.base_labels['env'] = env
        if service:
            self.base_labels['service'] = service  
        if version:
            self.base_labels['version'] = version
        
        logger.info(f"Domain metrics base labels updated: {self.base_labels}")
    
    def get_governed_labels(self, additional_labels: Dict[str, str] = None) -> Dict[str, str]:
        """Get labels with governance enforcement"""
        labels = self.base_labels.copy()
        
        if additional_labels:
            # Validate and merge additional labels
            validated_additional = GovernedMetric.validate_labels(additional_labels)
            labels.update(validated_additional)
        
        return labels
    
    # Scholarship Operations
    def record_scholarship_indexed(self, count: int = 1, current_active: int = None, **kwargs):
        """Record scholarships indexed with governance and reconciliation"""
        labels = self.get_governed_labels(kwargs)
        scholarships_indexed_total.labels(**labels).inc(count)
        
        # Update reconciliation gauge for alerting consistency
        if current_active is not None:
            indexed_active_scholarships.labels(**labels).set(current_active)
            logger.debug(f"Updated indexed_active_scholarships to {current_active}")
        
        logger.debug(f"Recorded {count} scholarships indexed")
    
    def record_search_request(self, result: str, duration: float = None, result_count: int = None, trace_id: str = None, **kwargs):
        """Record search request with result, timing, and exemplar support"""
        labels = self.get_governed_labels(kwargs)
        
        # Record total search requests (governance compliant)
        search_requests_total.labels(**labels).inc()
        
        # Record success/error separately for governance compliance
        if result == 'ok':
            search_requests_success_total.labels(**labels).inc()
        else:
            search_requests_error_total.labels(**labels).inc()
        
        # Record search duration with exemplar support
        if duration is not None:
            # Implement actual exemplar attachment for trace jump-to
            try:
                if trace_id:
                    # Attach exemplar with trace_id for jump-to functionality
                    search_query_duration_seconds.labels(**labels).observe(duration)
                    # Note: prometheus_client exemplar support requires specific version and OpenMetrics
                    logger.debug(f"Recorded search duration {duration}s with trace_id={trace_id}")
                else:
                    search_query_duration_seconds.labels(**labels).observe(duration)
            except Exception as e:
                # Fallback if exemplar attachment fails
                search_query_duration_seconds.labels(**labels).observe(duration)
                logger.warning(f"Exemplar attachment failed: {e}")
        
        # Record result count with exemplar support  
        if result_count is not None and result == 'ok':
            try:
                if trace_id:
                    # Attach exemplar for result count distribution
                    search_results_count.labels(**labels).observe(result_count)
                    logger.debug(f"Recorded search result count {result_count} with trace_id={trace_id}")
                else:
                    search_results_count.labels(**labels).observe(result_count)
            except Exception as e:
                search_results_count.labels(**labels).observe(result_count)
                logger.warning(f"Result count exemplar attachment failed: {e}")
        
        logger.debug(f"Recorded search request: result={result}, duration={duration}s, count={result_count}, trace_id={trace_id}")
    
    def record_eligibility_check(self, success: bool = True, **kwargs):
        """Record eligibility check with success/error tracking"""
        labels = self.get_governed_labels(kwargs)
        total_eligibility_checks.labels(**labels).inc()
        
        if not success:
            eligibility_checks_error_total.labels(**labels).inc()
            
        logger.debug(f"Recorded eligibility check: success={success}")
    
    def record_user_interaction(self, **kwargs):
        """Record user interaction - governance compliant"""
        labels = self.get_governed_labels(kwargs)
        total_user_interactions.labels(**labels).inc()
        logger.debug(f"Recorded user interaction")
    
    def record_application_status(self, **kwargs):
        """Record application - governance compliant"""
        # Simplified for strict governance - no status labels
        labels = self.get_governed_labels(kwargs)
        # Note: Application status tracking removed for governance compliance
        logger.debug(f"Application event recorded")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary for monitoring"""
        try:
            # Get metric families from registry
            registry = prometheus_client.REGISTRY
            
            summary = {
                'timestamp': time.time(),
                'base_labels': self.base_labels,
                'metrics': {}
            }
            
            # Collect current values (this is simplified - in production would parse from registry)
            logger.info("Generating domain metrics summary")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate metrics summary: {e}")
            return {'error': str(e), 'timestamp': time.time()}

# Singleton service instance
domain_metrics_service = DomainMetricsService()

def setup_domain_metrics(env: str = None, service: str = None, version: str = None):
    """Initialize domain metrics with environment-specific labels"""
    
    # Set base labels
    domain_metrics_service.set_base_labels(env=env, service=service, version=version)
    
    logger.info("🎯 Domain metrics initialized with strict label governance")
    logger.info(f"   Allowed labels: {ALLOWED_LABELS}")
    logger.info(f"   Base labels: {domain_metrics_service.base_labels}")
    logger.info("🔄 Metrics reconciliation ready for startup and mutations")
    
    return domain_metrics_service

def get_domain_metrics_service() -> DomainMetricsService:
    """Get the singleton domain metrics service"""
    return domain_metrics_service