import pytest
from pyats.topology import loader

@pytest.fixture(scope='session')
def testbed():
    """
    Fixture: Load testbed once per test session
    scope='session' means this runs once for the entire test suite
    Subsequent test functions reuse the same testbed object
    This is efficient—no need to reload testbed.yaml for each test
    """
    return loader.load('testbed.yaml')

@pytest.fixture
def device(testbed):
    """
    Fixture: Connect to a device and yield it to tests
    The fixture:
    1. Gets the device from testbed
    2. Connects via SSH (using credentials from testbed.yaml)
    3. 'yield' passes device to the test function
    4. After test completes, cleanup code runs (disconnect)
    
    Each test function that needs a device parameter receives this
    """
    dev = testbed.devices['switch-01']
    # Connect to device using settings from testbed.yaml
    dev.connect()
    
    # 'yield' pauses fixture and passes device to test
    # Test function runs here
    yield dev
    
    # This code runs AFTER test completes (cleanup)
    dev.disconnect()

def test_vlan_exists(device):
    """
    Test function: Check that VLAN exists
    
    Receives 'device' from the fixture above
    This is the PyATS Device object, already connected
    
    pytest runs this function and:
    1. Calls the device fixture (which connects)
    2. Passes device to this function
    3. Runs the assertions
    4. Fixture cleanup runs (disconnect)
    """
    # Parse show vlan output into structured data
    output = device.parse('show vlan')
    
    # Check: Is VLAN 10 in the vlans dictionary?
    assert '10' in output['vlans'], "VLAN 10 not found!"
    # If assertion passes, test passes
    # If fails, test fails and shows error message

def test_vlan_has_name(device):
    """
    Test function: Check VLAN has correct name
    """
    # Parse show vlan again (same pattern as above)
    output = device.parse('show vlan')
    
    # Access nested dictionary: output['vlans']['10'] gives us VLAN 10 data
    # VLAN 10 data is a dict with keys: 'name', 'state', 'interfaces', etc.
    vlan_10_data = output['vlans']['10']
    
    # Check: Does VLAN 10 have the expected name?
    assert vlan_10_data['name'] == 'DATA', "VLAN 10 name mismatch!"
    # This accesses the 'name' key from the VLAN data dictionary

def test_vlan_has_interfaces(device):
    """
    Test function: Check VLAN has expected interfaces
    """
    output = device.parse('show vlan')
    
    # Navigate nested structure: vlans → 10 → interfaces
    # VLAN 10 interfaces is a list of full interface names
    vlan_10_interfaces = output['vlans']['10']['interfaces']

    # vlan_10_interfaces looks like:
    # ['Ethernet0/1', 'Ethernet0/2', ...]

    # Check: Is Ethernet0/1 in the interfaces?
    assert 'Ethernet0/1' in vlan_10_interfaces, "Ethernet0/1 missing from VLAN 10!"
    # 'in' checks list membership
