#!/usr/bin/env python3
"""Test that you can run real commands"""

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command

def test_commands(task: Task) -> Result:
    """Run a simple show command"""
    result = task.run(
        netmiko_send_command,
        command_string="show version | include Cisco"
    )
    
    output = result.result
    return Result(host=task.host, result=output)

nr = InitNornir(config_file="nornir_config.yaml")
results = nr.run(task=test_commands)

for device, result_obj in results.items():
    output = result_obj.result[:50] + "..."  # First 50 chars
    print(f"{device}: {output}")
