#!/usr/bin/env python3
"""
Load and render Jinja2 templates from files
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
import yaml

# Create Jinja2 environment
env = Environment(
    loader=FileSystemLoader('templates'),  # Template directory
    trim_blocks=True,      # Remove first newline after block
    lstrip_blocks=True     # Strip leading spaces from blocks
)

# Load template from file
template = env.get_template('router_config.j2')

# Load data from YAML
with open('device_data.yaml') as f:
    data = yaml.safe_load(f)

# Render template
config = template.render(data)

# Save to file (creating configs/ the first time)
Path('configs').mkdir(exist_ok=True)
with open(f"configs/{data['hostname']}_config.txt", 'w') as f:
    f.write(config)

print(f"✓ Configuration generated for {data['hostname']}")
