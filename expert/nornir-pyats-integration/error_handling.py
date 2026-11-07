# error_handling.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import traceback
import sys
import structlog

logger = structlog.get_logger()


class ErrorSeverity(Enum):
    """Classify error severity for escalation"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AutomationError:
    """Structured error with full context"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    device: Optional[str]
    phase: str
    error_type: str
    message: str
    traceback: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/storage"""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'device': self.device,
            'phase': self.phase,
            'error_type': self.error_type,
            'message': self.message,
            'traceback': self.traceback,
            'context': self.context,
            'remediation': self.remediation,
        }


class ErrorRegistry:
    """
    Centralized error tracking and analysis.
    
    Features:
    - Track all errors with full context
    - Identify patterns (same error on multiple devices)
    - Generate remediation suggestions
    - Alert on critical errors
    """
    
    def __init__(self):
        self.errors: List[AutomationError] = []
        self.error_patterns: Dict[str, List[str]] = {}
    
    def register_error(
        self,
        device: Optional[str],
        phase: str,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict] = None
    ) -> AutomationError:
        """Register an error with full context"""
        
        error_id = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.errors)}"
        error_type = type(exception).__name__
        
        # Capture full traceback
        tb = ''.join(traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
        ))
        
        # Generate remediation suggestion
        remediation = self._suggest_remediation(error_type, str(exception))
        
        error = AutomationError(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            device=device,
            phase=phase,
            error_type=error_type,
            message=str(exception),
            traceback=tb,
            context=context or {},
            remediation=remediation
        )
        
        self.errors.append(error)
        
        # Track patterns
        if error_type not in self.error_patterns:
            self.error_patterns[error_type] = []
        if device:
            self.error_patterns[error_type].append(device)
        
        # Log structured error at the matching level (logger.error(...),
        # logger.critical(...)); structlog has no log(level_name, ...) form
        getattr(logger, severity.value)(
            "error_registered",
            error_id=error_id,
            device=device,
            phase=phase,
            error_type=error_type,
            message=str(exception)
        )
        
        # Alert on critical errors
        if severity == ErrorSeverity.CRITICAL:
            self._send_alert(error)
        
        return error
    
    def _suggest_remediation(self, error_type: str, message: str) -> str:
        """Suggest remediation based on error type"""
        
        remediations = {
            'ConnectionError': "Check device connectivity and credentials. Verify SSH/NETCONF is enabled.",
            'TimeoutError': "Increase timeout values. Check network latency. Verify device is responsive.",
            'AuthenticationError': "Verify credentials. Check if account is locked. Verify TACACS/RADIUS is working.",
            'CommandError': "Check command syntax. Verify device is in correct configuration mode.",
            'ParserError': "Parser may not support this platform/version. Check PyATS documentation.",
            'ConfigReplaceError': "Verify configuration syntax. Check for unsupported commands on this platform.",
        }
        
        return remediations.get(error_type, "Review logs and device state. Check documentation.")
    
    def _send_alert(self, error: AutomationError):
        """Send alert for critical errors"""
        # Integration with alerting system (PagerDuty, Slack, Email, etc.)
        logger.critical(
            "critical_error_alert",
            error_id=error.error_id,
            device=error.device,
            message=error.message
        )
        # Actual alerting implementation would go here
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns for insights"""
        analysis = {
            'total_errors': len(self.errors),
            'by_severity': {},
            'by_type': {},
            'by_device': {},
            'patterns': []
        }
        
        # Count by severity
        for error in self.errors:
            severity = error.severity.value
            analysis['by_severity'][severity] = analysis['by_severity'].get(severity, 0) + 1
        
        # Count by type
        for error in self.errors:
            error_type = error.error_type
            analysis['by_type'][error_type] = analysis['by_type'].get(error_type, 0) + 1
        
        # Count by device
        for error in self.errors:
            if error.device:
                analysis['by_device'][error.device] = analysis['by_device'].get(error.device, 0) + 1
        
        # Identify patterns (same error on multiple devices)
        for error_type, devices in self.error_patterns.items():
            if len(devices) >= 3:  # Pattern threshold
                analysis['patterns'].append({
                    'error_type': error_type,
                    'affected_devices': len(devices),
                    'devices': devices[:10],  # First 10
                    'likely_cause': 'Infrastructure issue or common misconfiguration'
                })
        
        return analysis
    
    def generate_error_report(self, output_file: str):
        """Generate comprehensive error report"""
        analysis = self.analyze_patterns()
        
        report = f"""
Error Analysis Report
{'=' * 70}

Generated: {datetime.utcnow().isoformat()}

Summary:
  Total Errors: {analysis['total_errors']}
"""
        
        if analysis['by_severity']:
            report += "\nBy Severity:\n"
            for severity, count in sorted(analysis['by_severity'].items()):
                report += f"  {severity}: {count}\n"
        
        if analysis['by_type']:
            report += "\nBy Error Type:\n"
            for error_type, count in sorted(
                analysis['by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                report += f"  {error_type}: {count}\n"
        
        if analysis['patterns']:
            report += "\nIdentified Patterns (Potential Infrastructure Issues):\n"
            for pattern in analysis['patterns']:
                report += f"\n  {pattern['error_type']}:\n"
                report += f"    Affected Devices: {pattern['affected_devices']}\n"
                report += f"    Sample Devices: {', '.join(pattern['devices'][:5])}\n"
                report += f"    Likely Cause: {pattern['likely_cause']}\n"
        
        if self.errors:
            report += "\n\nDetailed Errors:\n"
            report += "=" * 70 + "\n"
            
            for error in self.errors:
                report += f"\n[{error.timestamp.isoformat()}] {error.severity.value.upper()}\n"
                report += f"  Error ID: {error.error_id}\n"
                if error.device:
                    report += f"  Device: {error.device}\n"
                report += f"  Phase: {error.phase}\n"
                report += f"  Type: {error.error_type}\n"
                report += f"  Message: {error.message}\n"
                if error.remediation:
                    report += f"  Remediation: {error.remediation}\n"
                report += "\n"
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        logger.info("error_report_generated", output_file=output_file)


# Integration with OrchestrationEngine
from orchestrator.integration import OrchestrationEngine


class ErrorAwareOrchestrationEngine(OrchestrationEngine):
    """Engine with comprehensive error handling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_registry = ErrorRegistry()
    
    def deploy_with_validation(self, **kwargs):
        """Override to add error tracking"""
        try:
            return super().deploy_with_validation(**kwargs)
        except Exception as e:
            self.error_registry.register_error(
                device=None,
                phase='deployment',
                exception=e,
                severity=ErrorSeverity.CRITICAL,
                context={'kwargs': kwargs}
            )
            raise
    
    def generate_error_summary(self):
        """Generate error analysis"""
        return self.error_registry.analyze_patterns()
