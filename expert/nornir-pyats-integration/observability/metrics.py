# observability/metrics.py
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, push_to_gateway
import time
import structlog

logger = structlog.get_logger()


class AutomationMetrics:
    """
    Prometheus metrics for automation observability.
    
    Tracks:
    - Deployment counts and success rates
    - Execution duration
    - Error rates by type
    - Device inventory stats
    - Validation pass/fail rates
    """
    
    def __init__(self, pushgateway_url: Optional[str] = None):
        self.registry = CollectorRegistry()
        self.pushgateway_url = pushgateway_url
        
        # Deployment metrics
        self.deployments_total = Counter(
            'automation_deployments_total',
            'Total number of deployments',
            ['status', 'dry_run'],
            registry=self.registry
        )
        
        self.deployment_duration = Histogram(
            'automation_deployment_duration_seconds',
            'Deployment execution time',
            ['deployment_type'],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
            registry=self.registry
        )
        
        # Device metrics
        self.devices_processed = Counter(
            'automation_devices_processed_total',
            'Total devices processed',
            ['status', 'site'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'automation_errors_total',
            'Total errors encountered',
            ['error_type', 'severity'],
            registry=self.registry
        )
        
        # Validation metrics
        self.validations_total = Counter(
            'automation_validations_total',
            'Total validations performed',
            ['feature', 'status'],
            registry=self.registry
        )
        
        logger.info("metrics_initialized", pushgateway=pushgateway_url or 'none')
    
    def record_deployment(
        self,
        status: str,
        duration: float,
        dry_run: bool = False
    ):
        """Record deployment execution"""
        self.deployments_total.labels(
            status=status,
            dry_run=str(dry_run)
        ).inc()
        
        self.deployment_duration.labels(
            deployment_type='standard'
        ).observe(duration)
        
        if self.pushgateway_url:
            self._push_metrics()
    
    def _push_metrics(self):
        """Push metrics to Prometheus Pushgateway"""
        try:
            push_to_gateway(
                self.pushgateway_url,
                job='network_automation',
                registry=self.registry
            )
        except Exception as e:
            logger.error("metrics_push_failed", error=str(e))


class AlertingEngine:
    """Send alerts for critical conditions"""
    
    def __init__(self):
        self.alert_channels = []
    
    def add_slack_channel(self, webhook_url: str):
        """Add Slack alerting"""
        self.alert_channels.append({
            'type': 'slack',
            'webhook': webhook_url
        })
    
    def send_alert(
        self,
        severity: str,
        title: str,
        message: str,
        context: Optional[Dict] = None
    ):
        """Send alert through all configured channels"""
        
        logger.warning(
            "sending_alert",
            severity=severity,
            title=title,
            message=message
        )
        
        # Implementation would send to actual channels
