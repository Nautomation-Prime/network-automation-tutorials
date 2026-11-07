# src/credentials.py
import os

class CredentialsNotFoundError(Exception):
    pass

def get_device_credentials(device_name):
    """Get credentials from environment variables."""
    username = os.getenv(f"DEVICE_{device_name.upper()}_USERNAME")
    password = os.getenv(f"DEVICE_{device_name.upper()}_PASSWORD")
    
    if not username or not password:
        raise CredentialsNotFoundError(
            f"Credentials for {device_name} not found in environment"
        )
    
    return {
        "username": username,
        "password": password
    }
