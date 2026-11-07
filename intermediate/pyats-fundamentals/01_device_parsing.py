from pyats.topology import loader

# Load testbed — This reads testbed.yaml and creates device objects
# The testbed contains all device definitions, credentials, and connectivity details
testbed = loader.load('testbed.yaml')

# Get a specific device from the testbed
# testbed.devices is a dictionary of all devices defined in testbed.yaml
# 'switch-01' must match a device name in testbed.yaml
device = testbed.devices['switch-01']

# Connect to the device
# This initiates SSH connection using credentials from testbed.yaml
# PyATS handles connection pooling and session management automatically
device.connect()

# Parse CLI output automatically
# device.parse() sends 'show vlan' to the device and processes the output
# Instead of getting raw text, PyATS uses Genie parsers to convert output to structured data
# This parser is specific to the device OS (defined in testbed.yaml)
output = device.parse('show vlan')

# The output is a structured dictionary, not raw text:
# {
#   'vlans': {
#     '1': {
#       'vlan_id': '1',
#       'name': 'default',
#       'state': 'active',
#       'interfaces': ['Ethernet0/1', ...]
#     },
#     '10': {
#       'vlan_id': '10',
#       'name': 'DATA',
#       'state': 'active',
#       'interfaces': ['Ethernet0/2', ...]
#     }
#   }
# }
# Genie expands short port names, so you'll see 'GigabitEthernet1/0/1'
# rather than the 'Gi1/0/1' printed by the device

# Easy to validate using dictionary access (no regex, no parsing strings)
assert '10' in output['vlans'], "VLAN 10 missing!"
# This checks if key '10' exists in vlans dictionary
# Much more reliable than searching for "VLAN 10" in text output
