# tests/test_credential_management.py
import pytest
from unittest.mock import MagicMock, patch
from hvac.exceptions import InvalidPath
from src.vault_client import VaultClient, CredentialsNotFoundError

class TestVaultClient:
    """Test credential retrieval without real Vault."""
    
    @patch('hvac.Client')
    def test_get_secret_success(self, mock_hvac_client):
        """Successfully retrieve secret from Vault."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.return_value = {
            'data': {'data': {'username': 'admin', 'password': 'secret'}}
        }
        mock_hvac_client.return_value = mock_client
        
        vault = VaultClient(vault_addr="http://localhost:8200", vault_token="token")
        creds = vault.get_secret("network/devices/router1")
        
        assert creds['username'] == 'admin'
        assert creds['password'] == 'secret'
    
    @patch('hvac.Client')
    def test_get_secret_not_found(self, mock_hvac_client):
        """Handle missing secret gracefully."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.side_effect = \
            InvalidPath("secret not found")
        mock_hvac_client.return_value = mock_client
        
        vault = VaultClient(vault_addr="http://localhost:8200", vault_token="token")
        
        with pytest.raises(CredentialsNotFoundError):
            vault.get_secret("nonexistent")
    
    def test_missing_vault_token_raises_error(self):
        """Fail fast if Vault token not set."""
        with pytest.raises(ValueError, match="VAULT_TOKEN"):
            VaultClient(vault_addr="http://localhost:8200", vault_token=None)
