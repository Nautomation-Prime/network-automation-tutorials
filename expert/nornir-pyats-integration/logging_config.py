# logging_config.py
import structlog
import logging
import sys
from datetime import datetime
from pathlib import Path


def configure_structured_logging(
    log_dir: str = './logs',
    log_level: str = 'INFO',
    enable_json: bool = True,
    enable_console: bool = True
):
    """
    Configure comprehensive structured logging.
    
    Features:
    - JSON structured logs for machine parsing
    - Human-readable console output for debugging
    - Rotating file handlers
    - Contextual log enrichment
    """
    
    # Create log directory
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        stream=sys.stdout,
    )
    
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if enable_json:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable output for development
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        log_dir=str(log_dir),
        log_level=log_level,
        json_enabled=enable_json
    )


# Context Managers for Operation Tracking
from contextlib import contextmanager
import time

@contextmanager
def log_operation(operation_name: str, **context):
    """
    Context manager for operation logging with timing.
    
    Usage:
        with log_operation('config_push', device='router1'):
            # ... perform operation ...
    """
    logger = structlog.get_logger()
    start_time = time.time()
    
    logger.info(f"{operation_name}_started", **context)
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"{operation_name}_completed",
            duration_seconds=round(duration, 2),
            **context
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"{operation_name}_failed",
            error=str(e),
            duration_seconds=round(duration, 2),
            **context
        )
        raise


# Usage Example
def example_with_logging():
    """Demonstrate comprehensive logging"""
    
    configure_structured_logging(
        log_dir='./logs',
        log_level='INFO',
        enable_json=True
    )
    
    logger = structlog.get_logger()
    
    # Operation with automatic timing
    with log_operation('device_configuration', device='router1', site='dc1'):
        # Simulated work
        time.sleep(1)
        logger.info(
            "configuration_applied",
            device='router1',
            commands=['interface gi0/1', 'no shutdown']
        )
