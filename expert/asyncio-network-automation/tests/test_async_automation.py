# Added for the repo: the page's tests use these names from
# the module above without showing the import.
from async_automation import (  # noqa: F401
    AsyncConnectionPool, CircuitBreaker, CircuitState, DeviceConfig,
    TransportType,
)

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_connection_pool_success():
    """Test successful connection batch"""
    pool = AsyncConnectionPool(max_concurrent=5)
    
    devices = [
        DeviceConfig(host=f"router-{i}", timeout=10)
        for i in range(3)
    ]
    
    # Patch the name where the pool module looks it up. Patching
    # 'scrapli.driver.core.AsyncIOSXEDriver' would miss: the module
    # already imported its own reference to the class
    with patch(f"{AsyncConnectionPool.__module__}.AsyncIOSXEDriver") as mock_ssh:
        mock_instance = AsyncMock()
        mock_instance.send_command = AsyncMock(
            return_value=AsyncMock(result="show version output")
        )
        mock_ssh.return_value.__aenter__.return_value = mock_instance
        
        results = await pool.execute_batch(devices, command="show version")
        
        assert len(results) == 3
        assert all(r['status'] == 'success' for r in results)

@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    """Test circuit breaker opens after failures"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    for _ in range(3):
        with pytest.raises(RuntimeError):
            failing_call = AsyncMock(side_effect=RuntimeError("Device error"))
            await breaker.call(failing_call())
    
    assert breaker.state == CircuitState.OPEN

