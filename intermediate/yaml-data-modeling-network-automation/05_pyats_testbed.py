#!/usr/bin/env python3
"""
Load PyATS testbed and connect to devices
"""

from pyats.topology import loader

# Load testbed from YAML
testbed = loader.load('testbed.yaml')

# Access device
device = testbed.devices['csr1000v']

# Connect to device
device.connect()
print(f"✓ Connected to {device.name}")

# Parse device output
output = device.parse('show version')
print(f"Device version: {output['version']['version']}")

# Disconnect
device.disconnect()
