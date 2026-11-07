from netmiko import ConnectHandler
from src.vault_client import VaultClient

# Initialize Vault client (uses VAULT_ADDR and VAULT_TOKEN from env)
vault = VaultClient()

# Get credentials for a device
creds = vault.get_device_credentials("router1")
# Returns: {"username": "admin", "password": "SuperSecurePassword123!"}

# Connect to device
device = ConnectHandler(
    device_type="cisco_ios",
    host="10.0.0.1",
    username=creds["username"],
    password=creds["password"]
)

config = device.send_command("show running-config")
device.disconnect()
