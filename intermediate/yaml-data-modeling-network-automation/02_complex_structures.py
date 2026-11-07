#!/usr/bin/env python3
"""
Read nested YAML and extract specific data
"""

import yaml

# Sample YAML file: network_inventory.yaml
yaml_content = """
---
datacenters:
  dc1:
    location: "New York"
    devices:
      - hostname: nyc-core-01
        ip: 10.1.1.1
        vlans: [10, 20, 30]
      - hostname: nyc-core-02
        ip: 10.1.1.2
        vlans: [10, 20, 30]
"""

# Parse YAML
data = yaml.safe_load(yaml_content)

# Navigate nested structure
dc1_location = data['datacenters']['dc1']['location']
print(f"DC1 Location: {dc1_location}")

# Access list items
for device in data['datacenters']['dc1']['devices']:
    print(f"\nDevice: {device['hostname']}")
    print(f"  IP: {device['ip']}")
    print(f"  VLANs: {', '.join(map(str, device['vlans']))}")
