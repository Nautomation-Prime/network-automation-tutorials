import functools
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
audit_logger = logging.getLogger("network_audit")

def log_audit(action, include_args=True):
    """
    Log audit events for compliance and troubleshooting.
    
    Args:
        action: Description of the action (e.g., "config_deploy", "interface_enable")
        include_args: Whether to log function arguments
    
    Example:
        @log_audit(action="vlan_provision")
        def create_vlan(device, vlan_id, vlan_name):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.utcnow().isoformat()
            
            # Extract meaningful context
            context = {
                "timestamp": timestamp,
                "action": action,
                "function": func.__name__,
            }
            
            if include_args:
                context["args"] = str(args)
                context["kwargs"] = str(kwargs)
            
            audit_logger.info(f"[AUDIT START] {context}")
            
            try:
                result = func(*args, **kwargs)
                audit_logger.info(
                    f"[AUDIT SUCCESS] action={action}, function={func.__name__}, "
                    f"result_type={type(result).__name__}"
                )
                return result
            except Exception as e:
                audit_logger.error(
                    f"[AUDIT FAILURE] action={action}, function={func.__name__}, "
                    f"error={str(e)}"
                )
                raise
        
        return wrapper
    return decorator
