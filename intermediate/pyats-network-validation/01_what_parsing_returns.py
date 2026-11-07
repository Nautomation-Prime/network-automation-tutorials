from pyats.topology import loader

# Load testbed — reads device definitions and credentials
testbed = loader.load('testbed.yaml')

# Get specific device from testbed dictionary
device = testbed.devices['switch-01']

# Connect to device — initiates SSH session using testbed credentials
device.connect()

# Parse VLAN output into structured data
# device.parse() sends 'show vlan' command to device
# Genie parser (specific to device OS) converts text output to dict
vlan_output = device.parse('show vlan')

# Visualize the structure by printing as JSON
import json
print(json.dumps(vlan_output, indent=2))
# This shows exact structure so you know how to access data


# Parse show vlan command and get dictionary
vlans = device.parse('show vlan')

# Navigate to specific VLAN
# vlans is dict with 'vlans' key
# vlans['vlans'] gives us dict of VLAN IDs
# vlans['vlans']['10'] gives us VLAN 10's data

vlan_10 = vlans['vlans']['10']
# vlan_10 now contains: {'name': 'DATA', 'state': 'active', 'interfaces': [...]}

# Access VLAN 10 properties
print(vlan_10['name'])  
# Returns: "DATA" — the VLAN name

print(vlan_10['state'])
# Returns: "active" — whether VLAN is active or suspended

print(vlan_10['interfaces'])
# Returns: ['Ethernet1/3', 'Ethernet1/4'] — list of interface names in this VLAN


# Check if VLAN exists
if '20' in vlans['vlans']:
    print("✅ VLAN 20 found")
else:
    print("❌ VLAN 20 NOT found")

# Check VLAN name
assert vlans['vlans']['10']['name'] == 'DATA', "VLAN 10 name is wrong!"

# Check interfaces in VLAN
vlan_10_ports = vlans['vlans']['10']['interfaces']
assert 'Ethernet1/3' in vlan_10_ports, "Ethernet1/3 not in VLAN 10!"


# Parse show ip route command
routes = device.parse('show ip route')

# IOS/IOS-XE Genie route output is nested by VRF and address family:
# routes['vrf']['default']['address_family']['ipv4']['routes']
# Each prefix maps to route information (next hops, metrics, protocols)

# Navigate routing table
# route_table is dict where keys are IP prefixes (like "10.0.0.0/24")
route_table = routes['vrf']['default']['address_family']['ipv4']['routes']

for prefix, route_data in route_table.items():
    # prefix examples: "10.0.0.0/24", "192.168.1.0/24"
    # route_data is dict with next hop, protocol and (for learned routes) metric

    print(f"{prefix}: {route_data}")
    # Output examples:
    # 10.0.5.0/24: {'source_protocol': 'ospf', 'metric': 20, 'route_preference': 110,
    #               'next_hop': {'next_hop_list': {1: {'next_hop': '10.0.0.2', ...}}}, ...}
    # 10.0.0.0/24: {'source_protocol': 'connected',
    #               'next_hop': {'outgoing_interface': {'GigabitEthernet1': {...}}}, ...}
    # Connected and local routes have no 'metric' key at all


# Check if specific route exists
if '10.0.0.0/24' in route_table:
    print("✅ Route to 10.0.0.0/24 exists")
else:
    print("❌ Route to 10.0.0.0/24 missing!")

# Check how a route was learned, and its metric
route_data = route_table['10.0.5.0/24']
assert route_data['source_protocol'] == 'ospf', \
    f"Expected an OSPF route, got {route_data['source_protocol']}"

# Use .get(): connected routes have no metric key
metric = route_data.get('metric')
assert metric == 20, f"Expected OSPF cost 20, got {metric}"


# Parse show interfaces command
interfaces = device.parse('show interfaces')

# Dictionary where keys are interface names
# interfaces['Ethernet1/1'] has all data for that interface

# Check which interfaces are operationally up
interfaces_up = [
    name for name, data in interfaces.items()
    # Iterate through all interfaces
    if data.get('oper_status') == 'up'
    # Filter only those with oper_status='up'
]

print(f"Interfaces up: {len(interfaces_up)}")
# Output example: Interfaces up: 48

# Detailed interface status
for iface_name, iface_data in interfaces.items():
    status = iface_data.get('oper_status')  # 'up' or 'down'
    mtu = iface_data.get('mtu')  # Interface MTU
    mac = iface_data.get('mac_address')  # MAC address
    errors = iface_data.get('counters', {}).get('in_errors', 0)
    # Safely access nested dict with .get() to avoid KeyError
    
    print(f"{iface_name}: {status} (MTU:{mtu}, MAC:{mac}, Errors:{errors})")


# Check that minimum number of interfaces are up
min_expected_up = 48
assert len(interfaces_up) >= min_expected_up, \
    f"Expected {min_expected_up} up, got {len(interfaces_up)}"

# Check for error counters (indicates hardware problems)
eth1_data = interfaces['Ethernet1/1']
input_errors = eth1_data.get('counters', {}).get('in_errors', 0)
output_errors = eth1_data.get('counters', {}).get('out_errors', 0)

assert input_errors == 0, f"Ethernet1/1 has input errors: {input_errors}"
assert output_errors == 0, f"Ethernet1/1 has output errors: {output_errors}"


# Parse show ip bgp summary command
bgp = device.parse('show ip bgp summary')

# Navigate nested structure: device → bgp_id → neighbors
# bgp['vrf']['default']['neighbor'] gives dict of BGP neighbors

neighbors = bgp['vrf']['default']['neighbor']
# Use a different VRF name if you're validating non-default VRFs

# Iterate through BGP neighbors
for neighbor_ip, neighbor_data in neighbors.items():
    # neighbor_ip examples: "10.0.0.1", "192.168.1.1"
    # neighbor_data['address_family'] holds per-address-family data. For
    # plain 'show ip bgp summary' Genie keys the single entry '' (an empty
    # string), so loop over it rather than hard-coding a name
    for af_name, af_data in neighbor_data['address_family'].items():
        state_or_prefixes = af_data['state_pfxrcd']
        # Established peers show a prefix count; down peers show states like 'Idle' or 'Active'

        print(f"Neighbor {neighbor_ip}: {state_or_prefixes}")
    # Output examples:
    # Neighbor 10.0.0.1: 100
    # Neighbor 10.0.0.2: 42


# Check that all BGP neighbors are established
required_neighbors = ['10.0.0.1', '10.0.0.2']

for neighbor_ip in required_neighbors:
    # Check neighbor exists in BGP summary
    assert neighbor_ip in neighbors, \
        f"BGP neighbor {neighbor_ip} not in summary!"
    
    # Check neighbor is established (state_pfxrcd is a prefix count)
    for af_data in neighbors[neighbor_ip]['address_family'].values():
        state_or_prefixes = af_data['state_pfxrcd']
        assert state_or_prefixes.isdigit(), \
            f"BGP neighbor {neighbor_ip} not established! State: {state_or_prefixes}"
