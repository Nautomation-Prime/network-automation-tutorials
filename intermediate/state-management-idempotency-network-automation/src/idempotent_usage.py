from netmiko import ConnectHandler
from idempotent_operations import IdempotentOperations, OperationStatus

device = ConnectHandler(
    device_type="cisco_ios",
    host="10.0.0.1",
    username="admin",
    password="password"
)

ops = IdempotentOperations()

# Run 1: Creates VLAN 100
result = ops.ensure_vlan_exists(device, 100, "DATA")
print(f"{result.status.value}: {result.message}")
# Output: created: VLAN 100 created with name DATA

# Run 2: Detects VLAN 100 already exists
result = ops.ensure_vlan_exists(device, 100, "DATA")
print(f"{result.status.value}: {result.message}")
# Output: unchanged: VLAN 100 exists with correct name

# Run 3: Safe to call again and again
result = ops.ensure_vlan_exists(device, 100, "DATA")
print(f"{result.status.value}: {result.message}")
# Output: unchanged: VLAN 100 exists with correct name

device.disconnect()
