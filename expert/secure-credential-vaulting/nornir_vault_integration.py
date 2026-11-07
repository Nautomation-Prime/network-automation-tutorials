import asyncio
import os
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir.core.inventory import Host

from vault_manager import VaultBackend, VaultManager  # the module above

def set_credentials_from_vault(task: Task) -> Result:
    """
    Nornir task: Inject credentials from vault
    """
    vault_manager = task.host.get('vault_manager')
    
    if not vault_manager:
        return Result(host=task.host, failed=True, result="No vault manager configured")
    
    try:
        # Retrieve credentials (bridge the async vault API from this sync task).
        # No key: we want the whole secret dict (username and password)
        device_creds = asyncio.run(vault_manager.get_secret(
            f"network/credentials/{task.host.name}"
        ))
        
        # Update host credentials
        task.host.username = device_creds.get('username')
        task.host.password = device_creds.get('password')
        
        return Result(host=task.host, result="Credentials injected from vault")
    
    except Exception as e:
        return Result(host=task.host, failed=True, result=f"Failed to inject credentials: {e}")

# Usage in nornir config
nr = InitNornir(config_file="config.yaml")

# Initialize vault manager
vault_manager = VaultManager(
    backend_type=VaultBackend.HASHICORP,
    vault_addr=os.environ['VAULT_ADDR'],
    vault_token=os.environ['VAULT_TOKEN']
)

# Add vault manager to all hosts
for host in nr.inventory.hosts.values():
    host['vault_manager'] = vault_manager

# Run credential injection task
results = nr.run(task=set_credentials_from_vault)


import pytest
from unittest.mock import AsyncMock, MagicMock, patch

def make_manager(**kwargs):
    """VaultManager with hvac mocked: constructing one contacts Vault."""
    with patch("hvac.Client"):
        return VaultManager(
            backend_type=VaultBackend.HASHICORP,
            vault_addr="http://vault.test:8200",
            vault_token="test-token",
            **kwargs
        )

@pytest.mark.asyncio
async def test_vault_manager_caching():
    """Test secret caching with TTL"""
    manager = make_manager(cache_ttl=10)
    
    # Mock backend
    manager.backend.get_secret = AsyncMock(
        return_value={'username': 'admin', 'password': 'secret123'}
    )
    
    # First retrieval (from vault)
    result1 = await manager.get_secret('network/router1')
    assert manager.backend.get_secret.call_count == 1
    
    # Second retrieval (from cache)
    result2 = await manager.get_secret('network/router1')
    assert manager.backend.get_secret.call_count == 1  # Not called again
    assert result1 == result2

@pytest.mark.asyncio
async def test_secret_rotation():
    """Test secret rotation audit trail"""
    manager = make_manager(enable_audit=True)
    manager.backend.rotate_secret = AsyncMock()

    await manager.rotate_secret('network/router1', {'password': 'n3w-Pa55'})
    
    # Check audit log
    assert len(manager.audit_log) > 0
    assert manager.audit_log[-1]['action'] == 'secret_rotated'

