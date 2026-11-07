#!/usr/bin/env python3
"""
Load and display network inventory from YAML
"""

import yaml
from pathlib import Path

def load_inventory():
    """Load Nornir-style inventory from YAML files"""

    # Load hosts
    with open('inventory/hosts.yaml') as f:
        hosts = yaml.safe_load(f)

    # Load groups
    with open('inventory/groups.yaml') as f:
        groups = yaml.safe_load(f)

    # Load defaults
    with open('inventory/defaults.yaml') as f:
        defaults = yaml.safe_load(f)

    return hosts, groups, defaults

def display_inventory(hosts, groups):
    """Display inventory in human-readable format"""

    print("=" * 70)
    print("NETWORK INVENTORY")
    print("=" * 70)

    for host_name, host_data in hosts.items():
        print(f"\n{host_name}:")
        print(f"  Hostname: {host_data['hostname']}")
        print(f"  Groups: {', '.join(host_data.get('groups', []))}")

        if 'data' in host_data:
            print("  Data:")
            for key, value in host_data['data'].items():
                print(f"    {key}: {value}")

def main():
    """Main function"""
    try:
        hosts, groups, defaults = load_inventory()
        display_inventory(hosts, groups)

        print(f"\n{'=' * 70}")
        print(f"Total devices: {len(hosts)}")
        print(f"Total groups: {len(groups)}")
        print("=" * 70)

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("  Make sure inventory files exist")
    except yaml.YAMLError as e:
        print(f"✗ YAML error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    main()
