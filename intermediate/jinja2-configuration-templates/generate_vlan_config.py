#!/usr/bin/env python3
"""
Generate VLAN configuration from template and data
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
import yaml
from datetime import datetime

def generate_vlan_config(data_file, template_file, output_file):
    """
    Generate VLAN configuration
    """
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader('templates'),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Load data
    with open(data_file) as f:
        data = yaml.safe_load(f)

    # Add generation timestamp
    data['generation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Load and render template
    template = env.get_template(template_file)
    config = template.render(data)

    # Save configuration (creating the output folder if needed)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(config)

    print(f"✓ Configuration generated: {output_file}")
    print(f"  Device: {data['hostname']}")
    print(f"  VLANs: {len(data['vlans'])}")
    print(f"  Interfaces: {len(data['interfaces'])}")

    return config

if __name__ == "__main__":
    config = generate_vlan_config(
        'vlan_data.yaml',
        'vlan_config.j2',
        'configs/access-switch-01_config.txt'
    )

    print("\nGenerated Configuration Preview:")
    print("=" * 70)
    print(config[:500])  # Show first 500 characters
