#!/usr/bin/env python3
"""
Get data from REST API and process JSON response
Example: Cisco Meraki Dashboard API
"""

import requests
import json

# API configuration
API_KEY = "your_meraki_api_key_here"
ORG_ID = "your_org_id_here"
BASE_URL = "https://api.meraki.com/api/v1"

headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def get_networks(org_id):
    """
    Get all networks in an organisation
    Returns list of network dictionaries
    """
    url = f"{BASE_URL}/organizations/{org_id}/networks"

    try:
        response = requests.get(url, headers=headers)

        # Check if request was successful
        response.raise_for_status()
        # Raises HTTPError for bad responses (4xx, 5xx)

        # Parse JSON response
        networks = response.json()
        # .json() method automatically parses JSON response

        return networks

    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print(f"  Response: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        print("✗ Connection Error: Could not reach API")
        return None
    except json.JSONDecodeError:
        print("✗ Invalid JSON response")
        return None

def main():
    """Main function"""
    print("Fetching networks from Meraki API...")

    networks = get_networks(ORG_ID)

    if networks:
        print(f"\n✓ Found {len(networks)} networks:")

        for network in networks:
            # Access JSON fields
            print(f"\n  Network: {network['name']}")
            print(f"    ID: {network['id']}")
            print(f"    Type: {', '.join(network['productTypes'])}")
            print(f"    Time Zone: {network.get('timeZone', 'Not set')}")

        # Save to file for later analysis
        with open('meraki_networks.json', 'w') as f:
            json.dump(networks, f, indent=2)

        print(f"\n✓ Data saved to meraki_networks.json")
    else:
        print("✗ Failed to retrieve networks")

if __name__ == "__main__":
    main()
