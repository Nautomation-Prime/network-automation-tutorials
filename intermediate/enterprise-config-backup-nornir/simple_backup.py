#!/usr/bin/env python3
"""
Simple backup (no database, just files)
Shows task composition pattern
"""

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command
from datetime import datetime
import os

def get_config(task: Task) -> Result:
    """Step 1: Get the config"""
    result = task.run(
        netmiko_send_command,
        command_string="show running-config"
    )
    
    config = result[0].result
    return Result(
        host=task.host,
        result={'config': config, 'timestamp': datetime.now()}
    )

def save_to_file(task: Task, config_data: dict) -> Result:
    """Step 2: Save it to disk"""
    device_name = task.host.name
    
    os.makedirs("configs", exist_ok=True)
    filename = f"configs/{device_name}_backup.txt"
    
    with open(filename, 'w') as f:
        f.write(config_data['config'])
    
    return Result(
        host=task.host,
        result={'filepath': filename, 'size': len(config_data['config'])}
    )

# Initialize and run
nr = InitNornir(config_file="nornir_config.yaml")

# Get password
import getpass
pwd = getpass.getpass("Password: ")
for host in nr.inventory.hosts.values():
    host.password = pwd

# Run pipelines
print("\n✓ Step 1: Getting configs from all devices...")
results1 = nr.run(task=get_config)

print("✓ Step 2: Saving to filesystem...")
# For each device, save its config
for device_name, result_obj in results1.items():
    if not result_obj.failed:
        config_data = result_obj.result
        # Save this device's config
        save_task = nr.filter(name=device_name)
        save_task.run(task=save_to_file, config_data=config_data)

print("\n✓ Done! Check ./configs/ directory")
