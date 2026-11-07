"""
Unit tests for Nornir tasks
Using pytest and mocking
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from nornir.core.task import Result
from nornir.core.inventory import Host, Group
from tasks.enterprise_backup import backup_config, compliance_check

@pytest.fixture
def mock_host():
    """Create a mock host for testing"""
    host = Mock(spec=Host)
    host.name = "test-router"
    host.hostname = "192.168.1.1"
    host.password = "testpass"
    host.data = {'device_type': 'cisco_ios'}
    host.groups = []
    return host

@pytest.fixture
def mock_task(mock_host):
    """Create a mock Nornir task"""
    from nornir.core.task import Task
    task = Mock(spec=Task)
    task.host = mock_host
    task.run = Mock()
    return task

def test_backup_config_success(mock_task):
    """Test successful config backup"""
    
    # Mock the netmiko response
    test_config = "hostname test-router\n" * 100  # Simulated config
    mock_result = Mock()
    mock_result.result = test_config
    
    mock_task.run.return_value = [mock_result]
    
    # Call the task
    result = backup_config(mock_task)
    
    # Assertions
    assert result.result['success'] == True
    assert result.result['config'] == test_config
    assert len(result.result['hash']) == 64  # SHA256 hash length

def test_backup_config_failure(mock_task):
    """Test backup failure handling"""
    
    # Mock a failed connection
    mock_task.run.side_effect = Exception("Connection timeout")
    
    # Call the task
    result = backup_config(mock_task)
    
    # Assertions
    assert result.failed == True
    assert result.result['success'] == False

def test_compliance_check():
    """Test compliance scoring"""
    
    # Create a compliant config
    compliant_config = """
    banner motd # Authorized Access Only #
    logging 10.1.1.1
    enable secret 5 $1$12345...
    access-list 1 permit any
    ntp server 8.8.8.8
    snmp-server host 10.1.1.2
    """
    
    # Create a non-compliant config
    non_compliant_config = "hostname test-device\n"
    
    # Test with mock task
    from unittest.mock import patch
    
    with patch('sqlite3.connect'):
        mock_task = Mock()
        mock_task.host.name = "test"
        
        # Example assertions (call the real function in your test suite)
        result_good = compliance_check(mock_task, {"test": compliant_config})
        result_bad = compliance_check(mock_task, {"test": non_compliant_config})
        
        assert result_good.result['score'] > result_bad.result['score']
        assert result_bad.result['score'] < 70

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
