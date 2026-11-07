import pytest
from pyats.topology import loader

@pytest.fixture(scope='session')
def testbed():
    return loader.load('testbed.yaml')

@pytest.mark.parametrize('device_name', ['switch-01', 'switch-02', 'switch-03'])
def test_vlan_on_all_switches(testbed, device_name):
    """
    Run the same test on all switches
    PyTest will run this 3 times (once per device)
    """
    device = testbed.devices[device_name]
    device.connect()
    
    # Validate VLAN 10 exists
    vlans = device.parse('show vlan')
    assert '10' in vlans['vlans'], f"VLAN 10 missing on {device_name}!"
    
    device.disconnect()


def test_consistent_vlan_config(testbed):
    """
    Ensure all switches have the same VLAN configuration
    """
    
    all_devices_vlans = {}
    
    # Collect VLAN data from all switches
    for device_name in ['switch-01', 'switch-02', 'switch-03']:
        device = testbed.devices[device_name]
        device.connect()
        
        vlans = device.parse('show vlan')
        all_devices_vlans[device_name] = set(vlans['vlans'].keys())
        
        device.disconnect()
    
    # Compare
    reference_vlans = all_devices_vlans['switch-01']
    
    for device_name, vlans in all_devices_vlans.items():
        assert vlans == reference_vlans, \
            f"{device_name} VLAN config differs from switch-01!"
    
    print("✅ All switches have consistent VLAN configuration")
