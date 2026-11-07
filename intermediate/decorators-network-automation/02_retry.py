import functools
import time
from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException

def retry(max_attempts=3, delay=1, backoff=2, 
          exceptions=(Exception,)):
    """
    Retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch
    
    Example:
        @retry(max_attempts=3, delay=2, backoff=2)
        def connect_to_device(host):
            return connect(host)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    print(f"[{func.__name__}] Attempt {attempt}/{max_attempts}")
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        print(f"[{func.__name__}] All {max_attempts} attempts failed")
                        raise
                    print(f"[{func.__name__}] Failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutException

@retry(
    max_attempts=3, 
    delay=2, 
    backoff=2,
    exceptions=(NetmikoTimeoutException, OSError)
)
def connect_to_device(host, username, password):
    """Connect to network device with automatic retry."""
    device = ConnectHandler(
        device_type="cisco_ios",
        host=host,
        username=username,
        password=password,
        timeout=10
    )
    return device

# Usage
try:
    device = connect_to_device("10.0.0.1", "admin", "password")
    output = device.send_command("show version")
    device.disconnect()
except Exception as e:
    print(f"Connection failed after retries: {e}")
