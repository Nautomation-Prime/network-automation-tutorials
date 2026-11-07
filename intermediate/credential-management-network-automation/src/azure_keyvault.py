# src/azure_keyvault.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from src.vault_client import CredentialRetrievalError

class AzureKeyVaultClient:
    """Retrieve credentials from Azure Key Vault."""
    
    def __init__(self, vault_url):
        """
        Initialize Azure Key Vault client.
        
        Args:
            vault_url: Azure Key Vault URL (e.g., 'https://myvault.vault.azure.net/')
        """
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)
    
    def get_secret(self, secret_name):
        """Retrieve secret from Azure Key Vault."""
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            raise CredentialRetrievalError(f"Failed to retrieve secret: {str(e)}")
    
    def get_device_credentials(self, device_name):
        """Retrieve device credentials (stored as JSON)."""
        import json
        secret_name = f"network-{device_name}"
        secret_value = self.get_secret(secret_name)
        return json.loads(secret_value)
