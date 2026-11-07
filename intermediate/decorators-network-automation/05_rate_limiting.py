import functools
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Thread-safe rate limiter using sliding window."""
    
    def __init__(self, max_calls, time_window):
        """
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = Lock()
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                
                # Remove calls outside the time window
                while self.calls and self.calls[0] <= now - self.time_window:
                    self.calls.popleft()
                
                # If we've hit the limit, wait
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.time_window - (now - self.calls[0])
                    print(f"Rate limit reached. Waiting {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                
                self.calls.append(time.time())
            
            return func(*args, **kwargs)
        
        return wrapper

# Create rate limiters for different APIs
dns_limiter = RateLimiter(max_calls=100, time_window=60)
api_limiter = RateLimiter(max_calls=50, time_window=10)
