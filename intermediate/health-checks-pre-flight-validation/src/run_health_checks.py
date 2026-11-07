from netmiko import ConnectHandler
from health_checks import DeviceHealthChecker

device = ConnectHandler(
    device_type="cisco_ios",
    host="10.0.0.1",
    username="admin",
    password="password"
)

checker = DeviceHealthChecker(device)
results = checker.run_all_checks()

# Print results
for result in results:
    status_icon = "✓" if result.status.value == "healthy" else "⚠" if result.status.value == "warning" else "✗"
    print(f"{status_icon} {result.check_name}: {result.message}")

# Decide whether to deploy
if checker.is_healthy(results, allow_warnings=True):
    print("\n✓ Device is healthy, proceeding with deployment")
    # deploy_to_device()
else:
    print("\n✗ Device has critical issues, skipping deployment")
    # Log and skip
