import pytest
from pyats.topology import loader

@pytest.fixture
def testbed():
    return loader.load('testbed.yaml')

@pytest.fixture
def device(testbed):
    dev = testbed.devices['switch-01']
    dev.connect()
    yield dev
    dev.disconnect()

def test_vlan_deployment_end_to_end(device):
    """
    Test the complete workflow:
    1. Capture baseline
    2. Deploy configuration
    3. Validate immediately
    4. Verify no side effects
    """
    
    # Baseline
    baseline_vlans = set(device.parse('show vlan')['vlans'].keys())
    baseline_interfaces = sum(
        1 for iface in device.parse('show interfaces').values()
        if iface.get('oper_status') == 'up'
    )
    
    # Deploy (via Netmiko)
    from netmiko import ConnectHandler
    net_connect = ConnectHandler(
        device_type='cisco_ios',
        host=str(device.connections.cli.ip),  # Netmiko needs a string
        username='admin',
        password='...',
    )
    net_connect.send_config_set(['vlan 100', 'name TEST'])
    net_connect.disconnect()
    
    # Validate
    after_vlans = set(device.parse('show vlan')['vlans'].keys())
    assert '100' in after_vlans, "VLAN 100 not deployed!"
    assert len(after_vlans) == len(baseline_vlans) + 1, "Unexpected VLAN change!"
    
    # Verify no side effects
    after_interfaces = sum(
        1 for iface in device.parse('show interfaces').values()
        if iface.get('oper_status') == 'up'
    )
    assert after_interfaces == baseline_interfaces, "Interfaces went down!"
    
    print("✅ Complete workflow validated")
