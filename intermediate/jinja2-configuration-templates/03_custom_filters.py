#!/usr/bin/env python3
"""
Custom Jinja2 filters for network automation
"""

from jinja2 import Environment, FileSystemLoader
import ipaddress

def subnet_mask_to_cidr(mask):
    """
    Convert subnet mask to CIDR notation
    Example: '255.255.255.0' -> '/24'
    """
    return '/' + str(ipaddress.IPv4Network(f'0.0.0.0/{mask}').prefixlen)

def wildcard_mask(subnet_mask):
    """
    Convert subnet mask to wildcard mask
    Example: '255.255.255.0' -> '0.0.0.255'
    """
    mask_int = int(ipaddress.IPv4Address(subnet_mask))
    wildcard_int = 0xFFFFFFFF ^ mask_int
    return str(ipaddress.IPv4Address(wildcard_int))

def interface_short_name(interface):
    """
    Convert interface name to short form
    Example: 'GigabitEthernet0/0' -> 'Gi0/0'
    """
    replacements = {
        'GigabitEthernet': 'Gi',
        'FastEthernet': 'Fa',
        'TenGigabitEthernet': 'Te',
        'Ethernet': 'Et'
    }

    for long, short in replacements.items():
        if interface.startswith(long):
            return interface.replace(long, short)

    return interface

# Setup Jinja2 environment with custom filters
env = Environment(loader=FileSystemLoader('templates'))
env.filters['subnet_to_cidr'] = subnet_mask_to_cidr
env.filters['wildcard'] = wildcard_mask
env.filters['short_name'] = interface_short_name

# Example template using custom filters
template_string = """
interface {{ interface }}
 ip address {{ ip }} {{ mask }} {# {{ mask | subnet_to_cidr }} #}
!
router ospf 1
 network {{ network }} {{ mask | wildcard }} area 0
!
! Short name: {{ interface | short_name }}
"""

template = env.from_string(template_string)

data = {
    'interface': 'GigabitEthernet0/0',
    'ip': '10.1.1.1',
    'mask': '255.255.255.0',
    'network': '10.1.1.0'
}

print(template.render(data))
