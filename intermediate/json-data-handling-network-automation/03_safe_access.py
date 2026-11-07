#!/usr/bin/env python3
"""
Safely access JSON with error handling
"""

import json

def safe_get(data, *keys, default=None):
    """
    Safely navigate nested dictionary structure
    Returns default if any key doesn't exist
    """
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            return default
    return data

# Sample JSON (some fields may be missing)
json_data = '{"device": {"hostname": "router1", "interfaces": [{"name": "Gi0/0"}]}}'
data = json.loads(json_data)

# Safe access (won't crash if keys missing)
hostname = safe_get(data, 'device', 'hostname', default='unknown')
print(f"Hostname: {hostname}")

# This would crash without safe_get
bgp_asn = safe_get(data, 'device', 'bgp', 'asn', default='not configured')
print(f"BGP ASN: {bgp_asn}")

# Access first interface name
first_interface = safe_get(data, 'device', 'interfaces', 0, 'name', default='no interfaces')
print(f"First Interface: {first_interface}")
