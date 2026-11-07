from pyats.topology import loader
from netmiko import ConnectHandler
import pytest

@pytest.fixture
def testbed():
    return loader.load('testbed.yaml')

@pytest.fixture
def device(testbed):
    dev = testbed.devices['switch-01']
    dev.connect()
    yield dev
    dev.disconnect()

def capture_baseline(device):
    """Capture state BEFORE automation"""
    return {
        'vlans': set(device.parse('show vlan')['vlans'].keys()),
        'interfaces_up': sum(
            1 for iface_data in device.parse('show interfaces').values()
            if iface_data.get('oper_status') == 'up'
        ),
    }

def run_automation(device):
    """Execute your actual automation"""
    from pyats.utils.secret_strings import to_plaintext

    # Reuse the testbed's address and credentials. Netmiko needs plain
    # strings: .ip is an ipaddress object, the password a SecretString
    creds = device.credentials['default']
    net_connect = ConnectHandler(
        device_type='cisco_ios',
        host=str(device.connections.cli.ip),
        username=creds['username'],
        password=to_plaintext(creds['password']),
    )
    
    # Configure new VLAN
    net_connect.send_config_set([
        'vlan 100',
        'name AUTOMATION-TEST',
    ])
    net_connect.disconnect()

def validate_automation(device, baseline):
    """Validate state AFTER automation"""
    after = {
        'vlans': set(device.parse('show vlan')['vlans'].keys()),
        'interfaces_up': sum(
            1 for iface_data in device.parse('show interfaces').values()
            if iface_data.get('oper_status') == 'up'
        ),
    }
    
    # Validate changes
    new_vlans = after['vlans'] - baseline['vlans']
    assert '100' in new_vlans, "VLAN 100 not created!"
    assert after['interfaces_up'] == baseline['interfaces_up'], \
        "Interfaces changed state!"
    
    return after

def test_vlan_automation_with_validation(device):
    """Complete automation with before/after validation"""
    
    baseline = capture_baseline(device)
    print(f"Before: {len(baseline['vlans'])} VLANs, {baseline['interfaces_up']} interfaces up")
    
    run_automation(device)
    
    after = validate_automation(device, baseline)
    print(f"After: {len(after['vlans'])} VLANs, {after['interfaces_up']} interfaces up")
    print("✅ Automation validated successfully")
