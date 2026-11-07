# src/deploy.py
from netmiko import ConnectHandler
from rollback import RollbackManager
from validation import (
    validate_no_config_errors,
    validate_interfaces_up,
    validate_vlans_created
)

def deploy_vlan_config(device):
    """Apply VLAN configuration (not saved, so a reload can undo it)."""
    device.send_config_set([
        "vlan 100",
        "name DATA",
        "vlan 101",
        "name VOICE",
    ])
    print("✓ VLAN configuration commands sent")

# Main deployment workflow
device = ConnectHandler(
    device_type="cisco_ios",
    host="10.0.0.1",
    username="admin",
    password="password"
)

rollback = RollbackManager(device)

validators = [
    ("config_errors", validate_no_config_errors),
    ("interfaces_up", validate_interfaces_up),
    ("vlans_created", lambda d: validate_vlans_created(d, [100, 101])),
]

success = rollback.safe_config_deploy(deploy_vlan_config, validators)

if success:
    print("\n✓ Deployment successful!")
else:
    print("\n✗ Deployment failed and rolled back")

device.disconnect()
