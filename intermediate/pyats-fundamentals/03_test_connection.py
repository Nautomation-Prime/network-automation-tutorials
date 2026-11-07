from pyats.topology import loader

# Load testbed — parses YAML and creates device objects
testbed = loader.load('testbed.yaml')

# Get device by name (must match testbed.yaml)
device = testbed.devices['csr1000v']

# Connect to device
# PyATS uses credentials from testbed.yaml
# (%ENC / %ENV values were already resolved when the testbed loaded)
device.connect()

# Verify connection successful
print(f"✅ Connected to {device.name}")
# device.name is hostname or device name from testbed

# Always disconnect when done
device.disconnect()
