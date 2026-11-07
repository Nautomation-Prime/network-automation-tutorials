#!/usr/bin/env python3
"""
Navigate nested JSON structures
"""

import json

# Complex nested JSON
json_data = """
{
  "device": {
    "hostname": "core-router-01",
    "management_ip": "10.1.1.1",
    "interfaces": [
      {
        "name": "GigabitEthernet0/0",
        "ip_address": "192.168.1.1",
        "subnet_mask": "255.255.255.0",
        "status": "up",
        "speed": "1000"
      },
      {
        "name": "GigabitEthernet0/1",
        "ip_address": "192.168.2.1",
        "subnet_mask": "255.255.255.0",
        "status": "up",
        "speed": "1000"
      }
    ],
    "bgp": {
      "asn": 65001,
      "neighbors": [
        {"ip": "10.2.2.2", "remote_asn": 65002, "state": "established"},
        {"ip": "10.3.3.3", "remote_asn": 65003, "state": "established"}
      ]
    }
  }
}
"""

# Parse JSON
data = json.loads(json_data)

# Navigate nested structure
device = data['device']
print(f"Device: {device['hostname']}")
print(f"Management IP: {device['management_ip']}")

# Access list items
print("\nInterfaces:")
for interface in device['interfaces']:
    print(f"  {interface['name']}: {interface['ip_address']} ({interface['status']})")

# Access nested dictionary
print(f"\nBGP ASN: {device['bgp']['asn']}")
print("BGP Neighbors:")
for neighbor in device['bgp']['neighbors']:
    print(f"  {neighbor['ip']} (AS{neighbor['remote_asn']}) - {neighbor['state']}")
