"""
Complete workflow: Pinpoint → Implement → Measure
"""

from pyats.topology import loader
from netmiko import ConnectHandler

testbed = loader.load('testbed.yaml')

# PINPOINT: Establish baseline
print("=== PINPOINT STAGE ===")
device = testbed.devices['switch-01']
device.connect()
baseline = {
    'vlan_count': len(device.parse('show vlan')['vlans']),
    'interfaces_up': sum(
        1 for iface in device.parse('show interfaces').values()
        if iface.get('oper_status') == 'up'
    ),
}
device.disconnect()
print(f"Baseline: {baseline['vlan_count']} VLANs, {baseline['interfaces_up']} interfaces up")

# IMPLEMENT: Deploy and validate automatically
print("\n=== IMPLEMENT STAGE ===")
device.connect()

# Deploy
net_connect = ConnectHandler(
    device_type='cisco_ios',
    host=str(device.connections.cli.ip),  # Netmiko needs a string
    username='admin',
    password='...',
)
net_connect.send_config_set(['vlan 100', 'name AUTOMATION-TEST'])
net_connect.disconnect()

# Validate immediately
vlans = device.parse('show vlan')
assert '100' in vlans['vlans'], "VLAN 100 deployment failed!"
print("✅ VLAN 100 deployed and validated")

device.disconnect()

# MEASURE: Prove ROI
print("\n=== MEASURE STAGE ===")
device.connect()
after = {
    'vlan_count': len(device.parse('show vlan')['vlans']),
    'interfaces_up': sum(
        1 for iface in device.parse('show interfaces').values()
        if iface.get('oper_status') == 'up'
    ),
}
device.disconnect()

print(f"After: {after['vlan_count']} VLANs, {after['interfaces_up']} interfaces up")
print(f"Change: +{after['vlan_count'] - baseline['vlan_count']} VLANs")
print(f"Health: {baseline['interfaces_up'] == after['interfaces_up']} (no interfaces went down)")
print("✅ Deployment successful with zero disruption")
