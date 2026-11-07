# tests/test_integration.py
import pytest
from unittest.mock import MagicMock, patch
from src.decorators import retry
from src.device_ops import configure_interface

class TestDecoratorIntegration:
    """Test decorators + business logic together."""
    
    def test_retry_recovers_from_transient_failure(self):
        """Verify retry decorator works with real business logic."""
        mock_device = MagicMock()
        
        # Device fails first time, succeeds second time
        mock_device.send_config_set.side_effect = [
            Exception("Device timeout"),  # First attempt fails
            "OK",                         # Second attempt succeeds
        ]
        
        @retry(max_attempts=3, delay=0)
        def configure_with_retry(device, interface, ip):
            return configure_interface(device, interface, ip, "255.255.255.0")
        
        # Should succeed on second retry
        result = configure_with_retry(
            mock_device,
            interface="Gi0/0/1",
            ip="10.0.0.1"
        )
        
        assert result is True
    
    def test_retry_gives_up_after_max_attempts(self):
        """If all retries fail, exception should propagate."""
        mock_device = MagicMock()
        mock_device.send_config_set.side_effect = Exception("Device down")
        
        @retry(max_attempts=2, delay=0)
        def configure_with_retry(device, interface, ip):
            return configure_interface(device, interface, ip, "255.255.255.0")
        
        with pytest.raises(Exception, match="Device down"):
            configure_with_retry(
                mock_device,
                interface="Gi0/0/1",
                ip="10.0.0.1"
            )
    
    @patch('src.decorators.logger')
    def test_audit_logging_decorator_logs_attempts(self, mock_logger):
        """Verify audit logging captures operations."""
        from src.decorators import log_audit
        
        mock_device = MagicMock()
        mock_device.send_command.return_value = "OK"
        
        @log_audit(action="configure")
        def configure_with_logging(device, interface):
            device.send_command(f"interface {interface}")
            return True
        
        configure_with_logging(mock_device, "Gi0/0/1")
        
        # Verify something was logged (implementation details depend on your logging)
        assert mock_logger.info.called or mock_logger.debug.called
