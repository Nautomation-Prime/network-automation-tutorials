import functools
import logging

def handle_errors(default_return=None, notify=True, reraise=True):
    """
    Unified error handling for network operations.
    
    Args:
        default_return: What to return if error occurs (if reraise=False)
        notify: Whether to notify critical errors
        reraise: Whether to re-raise the exception after handling
    
    Example:
        @handle_errors(notify=True, reraise=True)
        def deploy_config(device, config):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__name__}: {str(e)}"
                logging.error(error_msg)
                
                if notify:
                    # Send critical alert to operations team
                    send_alert(f"AUTOMATION FAILURE: {error_msg}")
                
                if not reraise:
                    return default_return
                
                raise
        
        return wrapper
    return decorator

def send_alert(message):
    """Placeholder for actual alerting (email, Slack, PagerDuty, etc.)"""
    print(f"[ALERT] {message}")


@handle_errors(notify=True, reraise=True)
def deploy_bgp_config(device, bgp_config):
    """Deploy BGP configuration to device."""
    commands = [f"router bgp {bgp_config['asn']}"]
    for neighbor in bgp_config['neighbors']:
        commands.append(f"neighbor {neighbor['ip']} remote-as {neighbor['asn']}")
    device.send_config_set(commands)
    return True

@handle_errors(default_return=False, notify=False, reraise=False)
def check_device_health(device):
    """Check device health (non-critical operation)."""
    output = device.send_command("show version")
    return "uptime is" in output
