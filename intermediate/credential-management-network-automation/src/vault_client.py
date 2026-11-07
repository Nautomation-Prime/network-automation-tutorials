# src/vault_client.py
import hvac
import os

class VaultClient:
    """Wrapper for HashiCorp Vault credential retrieval."""
    
    def __init__(self, vault_addr=None, vault_token=None, mount_point="secret"):
        """
        Initialize Vault client.

        Args:
            vault_addr: Vault server URL (default: env var VAULT_ADDR)
            vault_token: Vault auth token (default: env var VAULT_TOKEN)
            mount_point: Where the KV v2 secrets engine is mounted
        """
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point
        
        if not self.vault_addr:
            raise ValueError("VAULT_ADDR environment variable not set")
        if not self.vault_token:
            raise ValueError("VAULT_TOKEN environment variable not set")
        
        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.vault_token
        )
        
        # Verify authentication
        if not self.client.is_authenticated():
            raise RuntimeError("Failed to authenticate with Vault")
    
    def get_secret(self, secret_path):
        """
        Retrieve secret from Vault.
        
        Args:
            secret_path: Path inside the mount (e.g., 'network/devices/router1').
                Don't repeat the mount name: hvac adds it, so
                'secret/network/...' would look up secret/secret/network/...

        Returns:
            dict: Secret data (username, password, etc.)
        """
        try:
            response = self.client.secrets.kv.read_secret_version(
                path=secret_path,
                mount_point=self.mount_point,
                raise_on_deleted_version=True,  # explicit, avoids a hvac warning
            )
            return response['data']['data']
        except hvac.exceptions.InvalidPath:
            raise CredentialsNotFoundError(
                f"Secret not found at {secret_path}"
            )
        except Exception as e:
            raise CredentialRetrievalError(
                f"Failed to retrieve secret: {str(e)}"
            )
    
    def get_device_credentials(self, device_name):
        """
        Retrieve device credentials from Vault.
        
        Args:
            device_name: Device identifier (e.g., 'router1')
        
        Returns:
            dict: Credentials with 'username' and 'password'
        """
        secret_path = f"network/devices/{device_name}"
        return self.get_secret(secret_path)
    
    def rotate_secret(self, secret_path, new_data):
        """
        Update secret in Vault (credential rotation).
        
        Args:
            secret_path: Path inside the mount (e.g., 'network/devices/router1')
            new_data: New secret data (dict)
        """
        try:
            self.client.secrets.kv.create_or_update_secret(
                path=secret_path,
                secret=new_data,
                mount_point=self.mount_point,
            )
        except Exception as e:
            raise CredentialRotationError(
                f"Failed to rotate credential: {str(e)}"
            )

# Custom exceptions
class CredentialsNotFoundError(Exception):
    pass

class CredentialRetrievalError(Exception):
    pass

class CredentialRotationError(Exception):
    pass
