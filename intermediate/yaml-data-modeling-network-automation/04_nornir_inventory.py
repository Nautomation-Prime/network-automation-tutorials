#!/usr/bin/env python3
"""
Use Nornir inventory from YAML files
"""

from nornir import InitNornir
from nornir.core.filter import F

# Initialize Nornir with config file
nr = InitNornir(config_file="nornir_config.yaml")

# Access device data
router1 = nr.inventory.hosts['router1']

print(f"Device: {router1.name}")
print(f"Hostname: {router1.hostname}")
print(f"Location: {router1.data['location']}")
print(f"Username: {router1.username}")  # Inherited from group

# Filter devices by group
ios_devices = nr.filter(F(groups__contains="ios_routers"))
print(f"\nFound {len(ios_devices.inventory.hosts)} IOS routers")

# Filter devices by custom data
prod_devices = nr.filter(lambda h: h.data.get('is_production') == True)
print(f"Found {len(prod_devices.inventory.hosts)} production devices")
