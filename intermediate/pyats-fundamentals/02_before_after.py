def capture_baseline(device):
    """
    Capture network state BEFORE automation runs
    This becomes our "truth" for comparison later
    """
    routes = device.parse('show ip route')
    bgp = device.parse('show ip bgp summary')
    
    # Create dictionary to store baseline measurements
    baseline = {
        # Count how many VLANs exist right now
        'vlan_count': len(device.parse('show vlan')['vlans']),
        # Explanation: device.parse() returns dict, ['vlans'] is the vlans section
        # len() counts how many VLAN IDs (keys in the vlans dictionary)
        
        # Store the IPv4 routing table before changes
        'routes': routes['vrf']['default']['address_family']['ipv4']['routes'],
        # Navigate Genie route structure: vrf → address_family → routes
        
        # Count how many interfaces are operationally up
        'interfaces_up': count_up_interfaces(device),
        # Helper function to count up interfaces (defined below)
        
        # Store BGP neighbor information
        'bgp_neighbors': bgp['vrf']['default']['neighbor'],
        # Navigating Genie BGP structure: vrf → neighbor
    }
    return baseline
    # Return dict for comparison after automation runs

def count_up_interfaces(device):
    """Helper function: Count interfaces that are operationally up"""
    # Parse show interfaces output
    interfaces = device.parse('show interfaces')
    
    # Count how many have oper_status == 'up'
    # Using list comprehension: [name for name, data in interfaces.items() if condition]
    up_count = len([
        name for name, data in interfaces.items()
        if data.get('oper_status') == 'up'
    ])
    # .items() gives us (interface_name, interface_data) tuples
    # .get('oper_status') safely accesses key (returns None if missing)
    # if condition filters only those that are 'up'
    # len() counts how many match
    
    return up_count


def run_automation(device):
    """
    Your actual automation code
    This runs AFTER baseline capture, BEFORE validation
    """
    from netmiko import ConnectHandler
    from pyats.utils.secret_strings import to_plaintext

    # Connect via Netmiko for configuration capability
    # We use Netmiko here because it's optimized for config commands
    # We use PyATS for parsing (read-only), Netmiko for configs (write)
    creds = device.credentials['default']
    conn = ConnectHandler(
        device_type='cisco_ios',
        # Device type tells Netmiko how to communicate with this device

        host=str(device.connections.cli.ip),
        # Get device IP from PyATS device object
        # device.connections.cli is the connection object; .ip is an
        # ipaddress object, and Netmiko needs a plain string

        username=creds['username'],
        password=to_plaintext(creds['password']),
        # Reuse the testbed's credentials. PyATS stores the password as a
        # SecretString, which to_plaintext() turns back into a str
    )
    
    # Your automation commands
    conn.send_config_set([
        # List of configuration commands to send
        'vlan 100',
        'name PROD-VLAN',
        'vlan 101',
        'name PROD-VLAN-2',
        # Each string is a command. Netmiko sends them sequentially
        # Netmiko waits for device prompts so next command doesn't send too early
    ])
    
    # Always disconnect Netmiko connection when done
    conn.disconnect()
    # Important: Don't reuse Netmiko connections, create fresh ones per automation
