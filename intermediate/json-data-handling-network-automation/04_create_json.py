#!/usr/bin/env python3
"""
Convert Python data to JSON
"""

import json
from datetime import datetime

# Python dictionary
device_data = {
    'hostname': 'router1',
    'ip_address': '10.1.1.1',
    'device_type': 'cisco_ios',
    'vlans': [10, 20, 30, 40],
    'interfaces': {
        'GigabitEthernet0/0': {
            'ip': '192.168.1.1',
            'mask': '255.255.255.0',
            'status': 'up'
        },
        'GigabitEthernet0/1': {
            'ip': '192.168.2.1',
            'mask': '255.255.255.0',
            'status': 'up'
        }
    },
    'enabled': True,
    'last_backup': datetime.now().isoformat()
}

# Method 1: Write to file
with open('device_output.json', 'w') as file:
    json.dump(device_data, file, indent=2)
    # indent=2 makes output readable (pretty-printed)

print("✓ JSON file created: device_output.json")

# Method 2: Convert to JSON string
json_string = json.dumps(device_data, indent=2)
# json.dumps() returns JSON string (note the 's')

print("\nJSON output:")
print(json_string)
