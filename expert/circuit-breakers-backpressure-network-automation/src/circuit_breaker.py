# src/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
import time
from threading import Lock

class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.name = name

class CircuitBreaker:
    """
    Circuit breaker for preventing cascade failures.
    
    Usage:
        breaker = CircuitBreaker(
            CircuitBreakerConfig(failure_threshold=5)
        )
        
        for device in devices:
            try:
                result = breaker.call(configure_device, device)
            except CircuitBreakerOpen:
                print(f"Skipping {device} - circuit open")
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker.
        
        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.config.name}' is OPEN"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _record_success(self):
        """Record successful call."""
        with self.lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    print(f"✓ Circuit '{self.config.name}' closed (recovered)")
    
    def _record_failure(self):
        """Record failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            self.success_count = 0
            
            if (
                self.state == CircuitState.HALF_OPEN
                or self.failure_count >= self.config.failure_threshold
            ):
                self.state = CircuitState.OPEN
                print(f"✗ Circuit '{self.config.name}' opened (threshold hit)")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try resetting."""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout
    
    def get_state(self) -> dict:
        """Get circuit breaker state."""
        with self.lock:
            return {
                "name": self.config.name,
                "state": self.state.value,
                "failures": self.failure_count,
                "successes": self.success_count,
                "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
            }

class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass
