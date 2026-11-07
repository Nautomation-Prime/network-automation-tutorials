# src/audit_logger.py
import json
import logging
from structured_logger import StructuredLogger

class AuditLogger:
    """Compliance-grade audit logging."""
    
    def __init__(self):
        self.logger = StructuredLogger("audit", level=logging.INFO)
    
    def log_action(self, action: str, actor: str, resource: str, result: str, **context):
        """
        Log an action for compliance.
        
        Args:
            action: What was done (e.g., "configure_vlan")
            actor: Who did it (user, service account)
            resource: What was affected (device, interface)
            result: success or failure
        """
        self.logger.info(
            f"Action: {action}",
            action=action,
            actor=actor,
            resource=resource,
            result=result,
            **context
        )
    
    def log_configuration_change(self, device: str, change_type: str, change_details: dict):
        """Log configuration change."""
        self.logger.info(
            "Configuration change",
            device=device,
            change_type=change_type,
            change_details=json.dumps(change_details),
            audit_required=True
        )
    
    def log_authentication(self, user: str, resource: str, success: bool):
        """Log authentication attempt."""
        self.logger.info(
            "Authentication attempt",
            user=user,
            resource=resource,
            success=success,
            audit_required=True
        )
