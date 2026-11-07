"""
Custom Nornir inventory plugin for Netbox
Fetches devices from Netbox API instead of YAML files
"""

from nornir.core.inventory import (
    Inventory,
    Group,
    Host,
    Groups,
    Hosts,
    Defaults,
    ParentGroups,
)
from nornir.core.plugins.inventory import InventoryPluginRegister
import os
import requests
from typing import Any, Dict, Optional

class NetboxInventory:
    """
    Fetch inventory from Netbox
    Credentials from environment variables
    """
    
    def __init__(
        self,
        nb_url: Optional[str] = None,
        nb_token: Optional[str] = None,
        filters: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            nb_url: Netbox API URL (default: env var NETBOX_URL)
                    e.g. https://netbox.yourcompany.com/api/
            nb_token: Netbox API token (default: env var NETBOX_API_TOKEN)
            filters: Query filters (e.g., {"site": "new-york"}, a site slug)
        """
        # Nornir doesn't expand ${VARS} in its config file, so the plugin
        # reads the URL and token from the environment itself
        self.nb_url = (nb_url or os.environ["NETBOX_URL"]).rstrip("/") + "/"
        self.nb_token = nb_token or os.environ["NETBOX_API_TOKEN"]
        self.filters = filters or {}
    
    def load(self) -> Inventory:
        """Fetch devices from Netbox and return Nornir Inventory"""
        
        # Fetch devices from Netbox API. Results are paginated (50 per page
        # by default), so keep following 'next' until it's None
        headers = {"Authorization": f"Token {self.nb_token}"}
        url = f"{self.nb_url}dcim/devices/"
        params = {**self.filters, "limit": 1000}
        devices = []

        while url:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            page = response.json()
            devices.extend(page['results'])
            url = page['next']
            params = None  # 'next' already carries the query string
        
        # Build Nornir inventory
        hosts = {}
        groups = {}
        defaults = Defaults()
        
        for device in devices:
            name = device['name']
            primary_ip = device.get('primary_ip') or {}
            ip = primary_ip.get('address', name).split('/')[0]
            device_type = device.get('device_type', {}).get('model', '').lower()
            site = device.get('site', {}).get('name', 'unknown')
            
            # Determine Netmiko device type from Netbox device type
            if 'cat' in device_type or 'switch' in device_type:
                nornir_device_type = 'cisco_ios'
            elif 'router' in device_type:
                nornir_device_type = 'cisco_ios'
            elif '3850' in device_type:
                nornir_device_type = 'cisco_ios'
            else:
                nornir_device_type = 'cisco_ios'  # Default
            
            # Create groups if needed
            if site not in groups:
                groups[site] = Group(name=site)
            
            # Create host
            hosts[name] = Host(
                name=name,
                hostname=ip,
                platform=nornir_device_type,
                groups=ParentGroups([groups[site]]),
                data={
                    'netbox_id': device['id'],
                    'device_type_model': device_type,
                    'serial': device.get('serial', ''),
                }
            )
        
        return Inventory(
            hosts=Hosts(hosts),
            groups=Groups(groups),
            defaults=defaults
        )

# Register the plugin so Nornir can resolve it by name from the config file.
# This runs on import, so import this module before calling InitNornir().
InventoryPluginRegister.register("NetboxInventory", NetboxInventory)

# Usage in nornir_config.yaml (URL and token come from NETBOX_URL and
# NETBOX_API_TOKEN in the environment):
# inventory:
#   plugin: NetboxInventory
#   options:
#     filters:
#       site: "new-york"
