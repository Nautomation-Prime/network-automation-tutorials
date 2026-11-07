#!/usr/bin/env python3
"""
Validate JSON data against a schema
Ensures API responses and config files match expected structure
"""

import json
import jsonschema
from jsonschema import validate

# Define JSON schema (what structure we expect)
device_schema = {
    "type": "object",
    "properties": {
        "hostname": {"type": "string"},
        "ip_address": {
            "type": "string",
            "pattern": "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$"  # IP regex
        },
        "device_type": {
            "type": "string",
            "enum": ["cisco_ios", "cisco_nxos", "cisco_iosxr"]
        },
        "vlans": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 4094}
        },
        "enabled": {"type": "boolean"}
    },
    "required": ["hostname", "ip_address", "device_type"]
}

def validate_device_data(data):
    """
    Validate device data against schema
    Returns True if valid, raises exception if invalid
    """
    try:
        validate(instance=data, schema=device_schema)
        print("✓ Data is valid")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"✗ Validation error: {e.message}")
        print(f"  Failed at: {' -> '.join(str(x) for x in e.path)}")
        return False

def main():
    """Main function"""

    # Valid data
    valid_device = {
        "hostname": "router1",
        "ip_address": "10.1.1.1",
        "device_type": "cisco_ios",
        "vlans": [10, 20, 30],
        "enabled": True
    }

    print("Testing valid data:")
    validate_device_data(valid_device)

    # Invalid data (wrong IP format)
    invalid_device1 = {
        "hostname": "router2",
        "ip_address": "invalid_ip",  # ✗ Wrong format
        "device_type": "cisco_ios"
    }

    print("\nTesting invalid IP:")
    validate_device_data(invalid_device1)

    # Invalid data (missing required field)
    invalid_device2 = {
        "hostname": "router3",
        # Missing ip_address (required field)
        "device_type": "cisco_ios"
    }

    print("\nTesting missing required field:")
    validate_device_data(invalid_device2)

    # Invalid data (wrong VLAN range)
    invalid_device3 = {
        "hostname": "router4",
        "ip_address": "10.1.1.4",
        "device_type": "cisco_ios",
        "vlans": [10, 5000]  # ✗ VLAN 5000 exceeds maximum
    }

    print("\nTesting invalid VLAN range:")
    validate_device_data(invalid_device3)

if __name__ == "__main__":
    main()
