#!/usr/bin/env python3
"""
Generate configurations for all devices from templates and data
"""

from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml
from datetime import datetime
import os

def load_data():
    """Load device and global configuration data"""
    with open('data/devices.yaml') as f:
        devices = yaml.safe_load(f)

    with open('data/global_settings.yaml') as f:
        global_settings = yaml.safe_load(f)

    return devices['devices'], global_settings

def generate_device_config(device, global_settings, env):
    """
    Generate configuration for a single device
    """
    # Combine device-specific and global settings
    data = {**global_settings, **device}
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['template_name'] = device['template']  # used by base_config.j2

    # Load template
    template = env.get_template(device['template'])

    # Render configuration
    config = template.render(data)

    return config

def save_config(hostname, config):
    """Save configuration to file"""
    os.makedirs('configs', exist_ok=True)
    filename = f"configs/{hostname}_config.txt"

    with open(filename, 'w') as f:
        f.write(config)

    return filename

def main():
    """Main function"""
    print("=" * 70)
    print("NETWORK CONFIGURATION GENERATOR")
    print("=" * 70)

    # Setup Jinja2 environment. StrictUndefined makes a missing variable
    # an error instead of a silent blank line in the config (see
    # "Testing and Validating Templates" below)
    env = Environment(
        loader=FileSystemLoader('templates'),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined
    )

    # Load data
    devices, global_settings = load_data()

    print(f"\n✓ Loaded {len(devices)} device(s)")
    print(f"✓ Loaded global settings")

    # Generate configs
    print(f"\n{'=' * 70}")
    print("GENERATING CONFIGURATIONS")
    print("=" * 70)

    generated_configs = []

    for device in devices:
        print(f"\n📝 Generating config for {device['hostname']}...")

        # Generate config
        config = generate_device_config(device, global_settings, env)

        # Save config
        filename = save_config(device['hostname'], config)

        # Track generated files
        generated_configs.append({
            'hostname': device['hostname'],
            'filename': filename,
            'size': len(config)
        })

        print(f"  ✓ Saved to {filename}")
        print(f"  ✓ Size: {len(config):,} bytes")

    # Summary
    print(f"\n{'=' * 70}")
    print("GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total devices: {len(generated_configs)}")
    print(f"Total config size: {sum(c['size'] for c in generated_configs):,} bytes")

    print(f"\n{'=' * 70}")
    print("GENERATED FILES:")
    print("=" * 70)
    for config in generated_configs:
        print(f"  {config['filename']}")

    print()

if __name__ == "__main__":
    main()
