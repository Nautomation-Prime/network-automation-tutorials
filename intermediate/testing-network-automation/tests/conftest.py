# tests/conftest.py (shared across all tests)
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_device():
    """Reusable mock Netmiko device."""
    device = MagicMock()
    device.send_command = MagicMock(return_value="")
    device.send_config_set = MagicMock(return_value="OK")
    return device

@pytest.fixture
def mock_device_with_output():
    """Mock device that returns realistic (captured-shape) output."""
    device = MagicMock()
    responses = {
        "show ip route": "S*    0.0.0.0/0 [1/0] via 192.168.1.1",
        "show running-config": "hostname R1\nip domain name example.com",
        "show ip interface brief": (
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "GigabitEthernet0/0/1   10.0.0.1        YES manual up                    up\n"
        ),
    }
    device.send_command = MagicMock(side_effect=lambda command, **kwargs: responses.get(command, ""))
    return device

@pytest.fixture
def mock_device_fails():
    """Mock device whose session has dropped: every call fails."""
    device = MagicMock()
    device.send_command.side_effect = Exception("Connection timeout")
    device.send_config_set.side_effect = Exception("Connection timeout")
    return device
