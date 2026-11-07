#!/usr/bin/env python3
"""Test SSH connectivity to each device"""

from nornir import InitNornir
from nornir.core.task import Task, Result

def test_connectivity(task: Task) -> Result:
    """Try to connect to device, return success/failure"""
    try:
        # This triggers a connection attempt
        task.host.get_connection("netmiko", task.nornir.config)
        return Result(host=task.host, result="✓ Connected")
    except Exception as e:
        return Result(
            host=task.host,
            result=f"✗ Failed: {str(e)}",
            failed=True
        )

nr = InitNornir(config_file="nornir_config.yaml")
results = nr.run(task=test_connectivity)

# Summary
passed = sum(1 for r in results.values() if not r.failed)
failed = sum(1 for r in results.values() if r.failed)

print(f"\n✓ Passed: {passed}/{len(results)}")
if failed > 0:
    print(f"✗ Failed: {failed}/{len(results)}")
    print("\nFailed devices:")
    for device, result in results.items():
        if result.failed:
            print(f"  - {device}: {result.result}")
