#!/usr/bin/env python3
"""
Structured logging with JSON output
Makes logs machine-parsable for analysis
"""

import json
import logging
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs JSON
    Makes logs queryable by log aggregation systems
    """

    def format(self, record):
        """
        Format log record as JSON
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add custom fields if present
        if hasattr(record, 'device'):
            log_data['device'] = record.device
        if hasattr(record, 'ip'):
            log_data['ip'] = record.ip
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
        if hasattr(record, 'device_count'):
            log_data['device_count'] = record.device_count

        return json.dumps(log_data)

# Configure logger with JSON formatter
logger = logging.getLogger('network_automation')
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def backup_device_config(device_name, device_ip):
    """
    Backup device configuration with structured logging
    """
    import time
    start_time = time.time()

    # Log start
    logger.info(
        f"Starting backup for {device_name}",
        extra={'device': device_name, 'ip': device_ip}
    )

    try:
        # Simulate backup operation
        time.sleep(2)  # Simulate work

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log success
        logger.info(
            f"Backup completed for {device_name}",
            extra={'device': device_name, 'duration': duration_ms}
        )

        return True

    except Exception as e:
        # Log error with exception info
        logger.error(
            f"Backup failed for {device_name}: {str(e)}",
            extra={'device': device_name},
            exc_info=True
        )
        return False

def main():
    """Main function"""
    devices = [
        {'name': 'router1', 'ip': '10.1.1.1'},
        {'name': 'router2', 'ip': '10.1.1.2'},
        {'name': 'switch1', 'ip': '10.1.1.10'}
    ]

    logger.info("Starting network backup job", extra={'device_count': len(devices)})

    for device in devices:
        backup_device_config(device['name'], device['ip'])

    logger.info("Backup job completed")

if __name__ == "__main__":
    main()
