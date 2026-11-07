# All credential retrievals should be logged
import logging
import os
from datetime import datetime, timezone
from src.vault_client import VaultClient

logger = logging.getLogger(__name__)

def get_device_credentials(device_name):
    """
    Retrieve credentials (with audit logging).
    
    Args:
        device_name: Device to get credentials for
    
    Returns:
        dict: Credentials
    """
    logger.info(
        f"Retrieved credentials",
        extra={
            "device": device_name,
            "user": os.getenv("USER"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    vault = VaultClient()
    return vault.get_device_credentials(device_name)
