#!/usr/bin/env python3
"""
Convert Python data structures to YAML files
"""

import yaml

# Python data structure
devices = {
    'router1': {
        'ip': '10.1.1.1',
        'username': 'admin',
        'device_type': 'cisco_ios',
        'vlans': [10, 20, 30]
    },
    'router2': {
        'ip': '10.1.1.2',
        'username': 'admin',
        'device_type': 'cisco_ios',
        'vlans': [10, 20, 30]
    }
}

# Write to YAML file
with open('devices_output.yaml', 'w') as file:
    yaml.dump(devices, file, default_flow_style=False, sort_keys=False)
    # default_flow_style=False makes output readable (not inline)
    # sort_keys=False preserves key order

print("✓ YAML file created: devices_output.yaml")
