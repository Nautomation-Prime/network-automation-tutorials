import json

from netmiko import ConnectHandler
from state_management import DeviceStateManager

# Connect to device
device = ConnectHandler(
    device_type="cisco_ios",
    host="10.0.0.1",
    username="admin",
    password="password"
)

# Initialize state manager
state_mgr = DeviceStateManager(device)

# Step 1: Capture pre-change state
print("Capturing pre-change state...")
state_mgr.capture_state("pre_change")
state_mgr.save_state_to_file("pre_change", "pre_change_backup.json")

# Step 2: Make changes
print("Deploying changes...")
device.send_config_set(["vlan 100", "name DATA"])

# Step 3: Capture post-change state
print("Capturing post-change state...")
state_mgr.capture_state("post_change")

# Step 4: Compare states
print("Analyzing changes...")
diff = state_mgr.compare_states("pre_change", "post_change")
print(json.dumps(diff, indent=2))

device.disconnect()
