#!/usr/bin/env python3
"""
Validate YAML files before using them in automation
"""

import yaml
import sys

def validate_yaml_file(filepath):
    """
    Validate YAML file syntax and structure
    Returns True if valid, False otherwise
    """
    try:
        with open(filepath, 'r') as file:
            data = yaml.safe_load(file)

        # Check if data was parsed
        if data is None:
            print(f"✗ {filepath}: File is empty or invalid")
            return False

        # Type check (expecting dict for most network configs)
        if not isinstance(data, dict):
            print(f"⚠ {filepath}: Root element is not a dictionary")

        print(f"✓ {filepath}: Valid YAML")
        return True

    except yaml.YAMLError as e:
        print(f"✗ {filepath}: YAML syntax error")
        print(f"  Error: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ {filepath}: File not found")
        return False
    except Exception as e:
        print(f"✗ {filepath}: Unexpected error")
        print(f"  Error: {e}")
        return False

def validate_nornir_inventory(hosts_file, groups_file, defaults_file):
    """
    Validate Nornir inventory structure
    """
    print("Validating Nornir inventory...")

    # Validate each file
    if not validate_yaml_file(hosts_file):
        return False
    if not validate_yaml_file(groups_file):
        return False
    if not validate_yaml_file(defaults_file):
        return False

    # Load and check structure
    with open(hosts_file) as f:
        hosts = yaml.safe_load(f)

    # Check hosts have required fields
    for host_name, host_data in hosts.items():
        if 'hostname' not in host_data:
            print(f"✗ Host '{host_name}' missing 'hostname' field")
            return False

    print("✓ Nornir inventory structure valid")
    return True

if __name__ == "__main__":
    # Validate single file
    validate_yaml_file('devices.yaml')

    # Validate Nornir inventory
    validate_nornir_inventory(
        'inventory/hosts.yaml',
        'inventory/groups.yaml',
        'inventory/defaults.yaml'
    )
