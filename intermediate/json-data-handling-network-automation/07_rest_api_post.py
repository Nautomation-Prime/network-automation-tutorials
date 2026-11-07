#!/usr/bin/env python3
"""
Send JSON data to REST API
Example: Create VLAN via API
"""

import requests
import json

def create_vlan(device_ip, vlan_id, vlan_name, username, password):
    """
    Create VLAN via REST API
    Sends JSON payload with VLAN configuration
    """
    url = f"https://{device_ip}/restconf/data/Cisco-IOS-XE-native:native/vlan"

    # JSON payload
    # vlan-list is a YANG list, so RESTCONF expects a JSON array,
    # even when you're creating a single VLAN
    payload = {
        "Cisco-IOS-XE-vlan:vlan-list": [
            {
                "id": vlan_id,
                "name": vlan_name
            }
        ]
    }

    headers = {
        'Content-Type': 'application/yang-data+json',
        'Accept': 'application/yang-data+json'
    }

    try:
        response = requests.post(
            url,
            auth=(username, password),  # Basic authentication
            headers=headers,
            data=json.dumps(payload),  # Convert dict to JSON string
            verify=False  # Disable SSL verification (lab only!)
        )

        response.raise_for_status()

        print(f"✓ VLAN {vlan_id} ({vlan_name}) created successfully")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")

        # Try to parse error response
        try:
            error_data = e.response.json()
            print(f"  Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"  Response: {e.response.text}")

        return False

def main():
    """Main function"""
    # Device credentials
    device_ip = "10.1.1.1"
    username = "admin"
    password = "password"

    # Create multiple VLANs
    vlans = [
        {'id': 100, 'name': 'DATA'},
        {'id': 200, 'name': 'VOICE'},
        {'id': 300, 'name': 'GUEST'}
    ]

    print("Creating VLANs via REST API...")

    for vlan in vlans:
        create_vlan(device_ip, vlan['id'], vlan['name'], username, password)

if __name__ == "__main__":
    main()
