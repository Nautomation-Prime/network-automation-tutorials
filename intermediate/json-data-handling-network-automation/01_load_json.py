#!/usr/bin/env python3
"""
Read JSON from file and string
"""

import json

# Method 1: Load from file
with open('devices.json', 'r') as file:
    data = json.load(file)
    # json.load() parses JSON file and returns Python dict/list

print(f"Device hostname: {data['hostname']}")
print(f"Device IP: {data['ip_address']}")

# Method 2: Parse JSON string
json_string = '{"hostname": "router1", "ip": "10.1.1.1"}'
data = json.loads(json_string)
# json.loads() parses JSON string (note the 's' in loads)

print(f"Parsed hostname: {data['hostname']}")
