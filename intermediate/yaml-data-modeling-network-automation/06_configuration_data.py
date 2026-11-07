#!/usr/bin/env python3
"""
Generate Cisco configuration from YAML data
"""

import yaml
from netmiko import ConnectHandler

# Load YAML configuration data
with open('vlan_config.yaml', 'r') as file:
    config_data = yaml.safe_load(file)

# Connect to device
device = ConnectHandler(
    device_type='cisco_ios',
    host='10.1.1.1',
    username='admin',
    password='password'
)

# Generate VLAN configuration commands
vlan_commands = []
for vlan in config_data['vlans']:
    if vlan['enabled']:
        vlan_commands.extend([
            f"vlan {vlan['id']}",
            f"name {vlan['name']}"
        ])

# Generate interface configuration commands
interface_commands = []
for interface, config in config_data['interface_assignments'].items():
    interface_commands.append(f"interface {interface}")
    interface_commands.append(f"description {config['description']}")

    if config['mode'] == 'access':
        interface_commands.extend([
            "switchport mode access",
            f"switchport access vlan {config['vlan']}"
        ])
    elif config['mode'] == 'trunk':
        vlans_str = ','.join(map(str, config['allowed_vlans']))
        interface_commands.extend([
            "switchport mode trunk",
            f"switchport trunk allowed vlan {vlans_str}"
        ])

# Deploy configuration
print("Deploying VLAN configuration...")
output = device.send_config_set(vlan_commands)
print(output)

print("\nDeploying interface configuration...")
output = device.send_config_set(interface_commands)
print(output)

device.disconnect()
print("\n✓ Configuration deployed successfully")
