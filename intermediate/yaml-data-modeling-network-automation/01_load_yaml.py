#!/usr/bin/env python3
"""
Read YAML file and convert to Python data structures
"""

import yaml

# Read YAML file
with open('devices.yaml', 'r') as file:
    data = yaml.safe_load(file)
    # safe_load() parses YAML and returns Python dict/list
    # Always use safe_load() (not load()) for security

# Access the data
print(f"Router 1 IP: {data['router1']['ip']}")
print(f"Router 2 Username: {data['router2']['username']}")

# Iterate through devices
for device_name, device_info in data.items():
    print(f"Device: {device_name}")
    print(f"  IP: {device_info['ip']}")
    print(f"  Type: {device_info['device_type']}")
