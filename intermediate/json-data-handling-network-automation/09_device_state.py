#!/usr/bin/env python3
"""
Store and compare device state in JSON
Track configuration drift over time
"""

import json
from datetime import datetime, timezone
from netmiko import ConnectHandler

def capture_device_state(device_params):
    """
    Capture device state and return as structured data
    """
    # Connect to device
    connection = ConnectHandler(**device_params)

    # Gather device information
    state = {
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'hostname': device_params['host'],
        'device_type': device_params['device_type'],
        'running_config': connection.send_command('show running-config'),
        'version': connection.send_command('show version'),
        'interfaces': connection.send_command('show ip interface brief'),
        'vlan_database': connection.send_command('show vlan brief'),
        'cdp_neighbors': connection.send_command('show cdp neighbors')
    }

    connection.disconnect()
    return state

def save_device_state(device_name, state):
    """
    Save device state to JSON file with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"state_{device_name}_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"✓ State saved to {filename}")
    return filename

def compare_states(state1_file, state2_file):
    """
    Compare two device states
    Returns differences
    """
    # Load states
    with open(state1_file) as f:
        state1 = json.load(f)
    with open(state2_file) as f:
        state2 = json.load(f)

    differences = {}

    # Compare running configs
    if state1['running_config'] != state2['running_config']:
        differences['running_config'] = 'CHANGED'

    # Compare VLAN databases
    if state1['vlan_database'] != state2['vlan_database']:
        differences['vlan_database'] = 'CHANGED'

    # Compare CDP neighbors
    if state1['cdp_neighbors'] != state2['cdp_neighbors']:
        differences['cdp_neighbors'] = 'CHANGED'

    return differences

def main():
    """Main function"""
    device_params = {
        'device_type': 'cisco_ios',
        'host': '10.1.1.1',
        'username': 'admin',
        'password': 'password'
    }

    # Capture current state
    print("Capturing device state...")
    state = capture_device_state(device_params)

    # Save to JSON
    filename = save_device_state('router1', state)

    print(f"\n✓ Device state captured and saved")
    print(f"  Timestamp: {state['timestamp']}")
    print(f"  Hostname: {state['hostname']}")

if __name__ == "__main__":
    main()
