# src/contextual_logging.py
from contextlib import contextmanager
from structured_logger import StructuredLogger

class OperationLogger:
    """Logger with automatic operation context."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.operation_stack = []
    
    @contextmanager
    def operation(self, operation_name: str, **context):
        """
        Context manager for logging operations.
        
        Example:
            with op_logger.operation("deploy_to_device", device="router1"):
                configure_device()
                # All logs within this block include device context
        """
        # Add operation to stack
        self.operation_stack.append({
            "operation": operation_name,
            **context
        })
        
        try:
            self.logger.info(
                f"{operation_name} started",
                **context
            )
            yield
            
            self.logger.info(
                f"{operation_name} completed",
                status="success",
                **context
            )
        
        except Exception as e:
            self.logger.error(
                f"{operation_name} failed",
                status="failed",
                exception=e,
                **context
            )
            raise
        
        finally:
            self.operation_stack.pop()
