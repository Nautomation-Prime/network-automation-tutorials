# tests/test_device_ops.py
import pytest
from unittest.mock import MagicMock
from src.device_ops import configure_interface, verify_interface_config

# Captured output shape. Write fakes from real device output, not from
# what you expect it to look like: an invented "Gi0/0/1 ... 10.0.0.1"
# line is how a check that can never match on a real switch passes its tests.
SHOW_IP_INT_BRIEF = (
    "Interface              IP-Address      OK? Method Status                Protocol\n"
    "GigabitEthernet0/0/1   {ip:<15} YES manual up                    up\n"
)

class TestDeviceOperations:
    """Test device configuration without real devices."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Netmiko device."""
        device = MagicMock()
        device.send_config_set = MagicMock(return_value="OK")
        return device

    def test_configure_interface_sends_correct_commands(self, mock_device):
        """Verify correct CLI commands are sent in correct order."""
        configure_interface(
            mock_device,
            interface="Gi0/0/1",
            ip_address="10.0.0.1",
            netmask="255.255.255.0"
        )

        # Verify the config block sent, in order, in one call
        mock_device.send_config_set.assert_called_once_with([
            "interface Gi0/0/1",
            "ip address 10.0.0.1 255.255.255.0",
            "no shutdown",
        ])
    
    def test_configure_interface_returns_true_on_success(self, mock_device):
        """Function should return True indicating success."""
        result = configure_interface(
            mock_device,
            interface="Gi0/0/1",
            ip_address="10.0.0.1",
            netmask="255.255.255.0"
        )
        
        assert result is True
    
    def test_configure_interface_handles_device_error(self, mock_device):
        """If device fails, exception should propagate."""
        mock_device.send_config_set.side_effect = Exception("Device unreachable")
        
        with pytest.raises(Exception, match="Device unreachable"):
            configure_interface(
                mock_device,
                interface="Gi0/0/1",
                ip_address="10.0.0.1",
                netmask="255.255.255.0"
            )
    
    def test_verify_interface_config_detects_correct_ip(self, mock_device):
        """When interface has correct IP, should return True."""
        mock_device.send_command.return_value = SHOW_IP_INT_BRIEF.format(ip="10.0.0.1")
        
        result = verify_interface_config(
            mock_device,
            interface="Gi0/0/1",
            expected_ip="10.0.0.1"
        )
        
        assert result is True
    
    def test_verify_interface_config_detects_wrong_ip(self, mock_device):
        """When interface has different IP, should return False."""
        mock_device.send_command.return_value = SHOW_IP_INT_BRIEF.format(ip="192.168.1.1")

        result = verify_interface_config(
            mock_device,
            interface="Gi0/0/1",
            expected_ip="10.0.0.1"
        )

        assert result is False

    def test_verify_interface_config_needs_an_exact_match(self, mock_device):
        """10.0.0.10 is not 10.0.0.1, even though it contains it."""
        mock_device.send_command.return_value = SHOW_IP_INT_BRIEF.format(ip="10.0.0.10")

        assert verify_interface_config(mock_device, "Gi0/0/1", "10.0.0.1") is False
