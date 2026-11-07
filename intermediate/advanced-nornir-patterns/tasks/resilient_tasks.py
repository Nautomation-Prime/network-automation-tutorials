"""
Resilient tasks with automatic retry logic
"""

import time
import logging
from functools import wraps
from nornir.core.task import Task, Result

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Decorator for automatic retry with exponential backoff
    
    Usage:
        @retry_on_failure(max_retries=3, backoff_factor=2.0)
        def my_task(task):
            # This will retry 3 times if it fails
    """
    def decorator(func):
        @wraps(func)
        def wrapper(task: Task, *args, **kwargs) -> Result:
            host = task.host
            attempt = 0
            last_exception = None
            
            while attempt < max_retries:
                try:
                    attempt += 1
                    logger.info(f"[{host.name}] Attempt {attempt}/{max_retries}")
                    
                    # Execute task
                    result = func(task, *args, **kwargs)
                    
                    if not result.failed:
                        if attempt > 1:
                            logger.info(f"[{host.name}] Succeeded on attempt {attempt}")
                        return result
                    else:
                        last_exception = result.exception
                        
                except Exception as e:
                    last_exception = e
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries:
                    wait_time = backoff_factor ** (attempt - 1)
                    logger.warning(f"[{host.name}] Retry in {wait_time}s...")
                    time.sleep(wait_time)
            
            # All retries failed
            logger.error(f"[{host.name}] Failed after {max_retries} attempts")
            return Result(
                host=task.host,
                result={'success': False, 'error': str(last_exception)},
                failed=True
            )
        
        return wrapper
    return decorator

# Usage:
@retry_on_failure(max_retries=3, backoff_factor=1.5)
def resilient_backup(task: Task) -> Result:
    # This automatically retries on failure
    # Waits: 1.5^0=1s, then 1.5^1=1.5s, then 1.5^2=2.25s between retries
    pass
