# src/structured_logger.py
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict
import uuid

# Attribute names a LogRecord already uses ("module", "name", "filename",
# "lineno", ...). logging raises KeyError if extra= tries to reuse one.
LOG_RECORD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}

class StructuredLogger:
    """Structured JSON logging for network automation."""
    
    def __init__(self, name: str, level=logging.INFO):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove default handlers
        self.logger.handlers = []
        
        # Create JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        
        # Unique ID for this execution
        self.correlation_id = str(uuid.uuid4())
    
    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add standard context to log entry."""
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": self.correlation_id,
        }
        for key, value in extra.items():
            # A field called "module" or "name" would make logging raise
            # KeyError, usually in the error path. Prefix it instead.
            context[f"ctx_{key}" if key in LOG_RECORD_ATTRS else key] = value
        return context
    
    def info(self, message: str, **context):
        """Log info level with context."""
        self.logger.info(
            message,
            extra=self._add_context(context)
        )
    
    def warning(self, message: str, **context):
        """Log warning level with context."""
        self.logger.warning(
            message,
            extra=self._add_context(context)
        )
    
    def error(self, message: str, exception=None, **context):
        """Log error level with context and optional exception."""
        if exception:
            context["exception"] = str(exception)
            context["exception_type"] = type(exception).__name__
        
        self.logger.error(
            message,
            extra=self._add_context(context),
            exc_info=exception
        )
    
    def debug(self, message: str, **context):
        """Log debug level with context."""
        self.logger.debug(
            message,
            extra=self._add_context(context)
        )


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for machine parsing."""
    
    def format(self, record):
        """Convert log record to JSON."""
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "timestamp"):
            log_data["timestamp"] = record.timestamp
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add any custom fields from extra={}: everything that isn't a
        # standard LogRecord attribute (this also skips taskName, which
        # Python 3.12 added)
        for key, value in record.__dict__.items():
            if key not in LOG_RECORD_ATTRS:
                log_data[key] = value

        # default=str keeps a stray datetime or IP object from breaking logging
        return json.dumps(log_data, default=str)
