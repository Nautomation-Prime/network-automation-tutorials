#!/usr/bin/env python3
"""
Absolute minimal Nornir example
Ping 3 devices in parallel
"""

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command

def ping_device(task: Task) -> Result:
    """
    Ping a device and return result
    This runs once per device, in parallel
    """
    device_name = task.host.name
    
    result = task.run(
        netmiko_send_command,
        command_string="ping 8.8.8.8 repeat 3"
    )
    
    return Result(
        host=task.host,
        result=result.result
    )

# Initialize Nornir
nr = InitNornir(config_file="nornir_config.yaml")

# Run the task on all devices
results = nr.run(task=ping_device)

# Print results
for device_name, result_obj in results.items():
    if result_obj.failed:
        print(f"✗ {device_name}: FAILED")
    else:
        print(f"✓ {device_name}: SUCCESS")
