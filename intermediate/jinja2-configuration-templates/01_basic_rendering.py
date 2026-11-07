#!/usr/bin/env python3
"""
Render Jinja2 template with Python
"""

from jinja2 import Template

# Define template
template_string = """
hostname {{ hostname }}
!
interface {{ interface }}
 ip address {{ ip }} {{ mask }}
 no shutdown
"""

# Create template object
template = Template(template_string)

# Data to render
data = {
    'hostname': 'router1',
    'interface': 'GigabitEthernet0/0',
    'ip': '10.1.1.1',
    'mask': '255.255.255.0'
}

# Render template
config = template.render(data)

print(config)
