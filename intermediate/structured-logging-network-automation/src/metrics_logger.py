# src/metrics_logger.py
import time
from structured_logger import StructuredLogger

class MetricsLogger:
    """Log operation metrics (duration, throughput, etc.)."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_duration(self, operation: str, duration_ms: float, **context):
        """Log operation duration."""
        self.logger.info(
            f"{operation} duration",
            operation=operation,
            duration_ms=f"{duration_ms:.2f}",
            **context
        )
    
    def log_throughput(self, operation: str, items: int, duration_ms: float, **context):
        """Log throughput (items per second)."""
        throughput = (items / duration_ms) * 1000 if duration_ms > 0 else 0
        
        self.logger.info(
            f"{operation} throughput",
            operation=operation,
            items=items,
            duration_ms=f"{duration_ms:.2f}",
            throughput_per_sec=f"{throughput:.2f}",
            **context
        )
    
    def time_operation(self, operation: str, **context):
        """Context manager to automatically time operations."""
        class Timer:
            def __enter__(timer_self):
                timer_self.start = time.time()
                return timer_self
            
            def __exit__(timer_self, *args):
                duration = (time.time() - timer_self.start) * 1000  # ms
                self.log_duration(operation, duration, **context)
        
        return Timer()
