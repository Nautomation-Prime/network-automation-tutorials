import pytest
from pyats.topology import loader
from pyats.utils.secret_strings import to_plaintext
from netmiko import ConnectHandler

@pytest.fixture
def testbed():
    return loader.load('testbed.yaml')

@pytest.fixture
def device(testbed):
    dev = testbed.devices['csr1000v']
    dev.connect()
    yield dev
    dev.disconnect()

def test_interface_configuration(device):
    """
    Scenario: Configure Ethernet0/1 with IP 10.0.1.1/24
    Validate: Interface exists, has correct IP, is up
    """
    
    # Connect via Netmiko to configure, reusing the testbed's credentials.
    # PyATS keeps passwords as SecretString objects; Netmiko needs a str.
    creds = device.credentials['default']
    net_connect = ConnectHandler(
        device_type='cisco_ios',
        host=str(device.connections.cli.ip),
        username=creds['username'],
        password=to_plaintext(creds['password']),
    )
    
    # Run configuration commands
    commands = [
        'interface Ethernet0/1',
        'ip address 10.0.1.1 255.255.255.0',
        'no shutdown',
    ]
    net_connect.send_config_set(commands)
    net_connect.disconnect()
    
    # NOW VALIDATE WITH PYATS
    # Parse interface configuration
    interfaces = device.parse('show interfaces')
    eth01 = interfaces.get('Ethernet0/1', {})
    
    # Validate interface exists
    assert eth01, "Ethernet0/1 not found!"
    
    # Validate interface is up
    assert eth01.get('enabled') == True, "Interface not enabled!"
    assert eth01.get('oper_status') == 'up', "Interface not up!"
    
    # Parse IP address. Genie keys each address by "address/prefix".
    ip_config = device.parse('show ip interface Ethernet0/1')
    ip_addr = ip_config['Ethernet0/1']['ipv4']['10.0.1.1/24']['ip']
    
    # Validate IP address
    assert ip_addr == '10.0.1.1', f"IP mismatch! Got {ip_addr}"
    
    print("✅ Validation passed: Interface configured correctly")
