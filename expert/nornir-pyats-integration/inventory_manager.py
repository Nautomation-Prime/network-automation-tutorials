# inventory_manager.py
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import pynetbox
from nornir import InitNornir
from nornir.core.inventory import Inventory, Host, Group
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeviceCredentials:
    """Secure credential structure"""
    username: str
    password: str
    enable_password: Optional[str] = None
    
    @classmethod
    def from_vault(cls, device_name: str):
        """Pull credentials from HashiCorp Vault"""
        # Implementation would connect to actual vault
        import hvac
        client = hvac.Client(url='https://vault.local')
        secret = client.secrets.kv.v2.read_secret_version(
            path=f'network/devices/{device_name}'
        )
        return cls(**secret['data']['data'])


class UnifiedInventoryManager:
    """
    Manages inventory for both Nornir and PyATS from a single NetBox source.
    Implements caching, validation, and dynamic updates.
    """
    
    def __init__(self, netbox_url: str, netbox_token: str, cache_ttl: int = 300):
        self.nb = pynetbox.api(netbox_url, token=netbox_token)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamp = 0
        
    def get_devices(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch devices from NetBox with filtering.
        
        Args:
            filters: NetBox filter dict, e.g., {'site': 'dc1', 'status': 'active'}
            
        Returns:
            List of device dictionaries with enriched metadata
        """
        filters = filters or {'status': 'active'}
        
        devices = []
        for device in self.nb.dcim.devices.filter(**filters):
            try:
                # Enrich with primary IP, platform, and custom fields
                device_data = {
                    'name': device.name,
                    'hostname': str(device.primary_ip4).split('/')[0] if device.primary_ip4 else None,
                    'platform': device.platform.slug if device.platform else 'unknown',
                    'site': device.site.slug if device.site else 'unknown',
                    'role': self._role_slug(device),
                    'vendor': device.device_type.manufacturer.slug if device.device_type else 'unknown',
                    'model': device.device_type.model if device.device_type else 'unknown',
                    'serial': device.serial or 'unknown',
                    'tags': [tag.slug for tag in device.tags],
                    'custom_fields': device.custom_fields,
                }
                
                # Add management interface details
                if device.primary_ip4:
                    device_data['mgmt_interface'] = self._get_mgmt_interface(device)
                
                devices.append(device_data)
                
            except Exception as e:
                logger.error(f"Failed to process device {device.name}: {e}")
                continue
                
        logger.info(f"Loaded {len(devices)} devices from NetBox")
        return devices
    
    @staticmethod
    def _role_slug(device) -> str:
        """Device role slug. NetBox 4 renamed the field from device_role to role."""
        # Read the returned fields: getattr on a missing field makes
        # pynetbox fetch the whole device again (an extra API call)
        fields = dict(device)
        role = fields.get('role') or fields.get('device_role')
        return role['slug'] if role else 'unknown'

    def _get_mgmt_interface(self, device) -> Optional[Dict]:
        """Get management interface details"""
        # Interfaces are their own endpoint; a device record doesn't list them
        for interface in self.nb.dcim.interfaces.filter(device_id=device.id):
            if 'mgmt' in interface.name.lower() or 'management' in interface.name.lower():
                fields = dict(interface)
                # NetBox 4.2 moved the MAC to a separate primary_mac_address object
                mac = fields.get('mac_address') or (fields.get('primary_mac_address') or {}).get('mac_address')
                return {
                    'name': interface.name,
                    'mac_address': mac,
                    'enabled': interface.enabled
                }
        return None
    
    def generate_nornir_inventory(self, filters: Optional[Dict] = None) -> Dict:
        """
        Generate Nornir-compatible inventory structure.
        
        Returns:
            Dictionary suitable for Nornir SimpleInventory plugin
        """
        devices = self.get_devices(filters)
        
        hosts = {}
        groups = {}
        
        # Build groups dynamically from sites and roles
        for device in devices:
            platform = self._map_platform_to_driver(device['platform'])

            # Create host entry
            hosts[device['name']] = {
                'hostname': device['hostname'],
                'platform': platform,
                # NAPALM names platforms differently from Netmiko ('ios', not
                # 'cisco_ios'); the rollback in Step 2 uses NAPALM
                'connection_options': {
                    'napalm': {'platform': self._map_driver_to_napalm(platform)}
                },
                'groups': [device['site'], device['role'], device['vendor']],
                'data': {
                    'model': device['model'],
                    'serial': device['serial'],
                    'tags': device['tags'],
                    'custom_fields': device['custom_fields'],
                }
            }
            
            # Ensure groups exist
            for group_name in [device['site'], device['role'], device['vendor']]:
                if group_name not in groups:
                    groups[group_name] = {'data': {}}
        
        return {
            'hosts': hosts,
            'groups': groups
        }
    
    def generate_pyats_testbed(self, filters: Optional[Dict] = None) -> Dict:
        """
        Generate PyATS testbed YAML structure.
        
        Returns:
            Dictionary suitable for PyATS testbed
        """
        devices = self.get_devices(filters)
        
        testbed = {
            'testbed': {
                'name': 'dynamic_testbed',
                'credentials': {
                    'default': {
                        'username': '%ENV{NETAUTO_USER}',
                        'password': '%ENV{NETAUTO_PASS}',
                    }
                }
            },
            'devices': {}
        }
        
        for device in devices:
            testbed['devices'][device['name']] = {
                'alias': device['name'],
                'os': self._map_platform_to_os(device['platform']),
                'type': device['vendor'],
                'connections': {
                    'cli': {
                        'protocol': 'ssh',
                        'ip': device['hostname'],
                        'port': 22,
                    }
                },
                'custom': {
                    'model': device['model'],
                    'site': device['site'],
                    'role': device['role'],
                }
            }
        
        return testbed
    
    def _map_platform_to_driver(self, platform: str) -> str:
        """Map NetBox platform to Nornir driver"""
        mapping = {
            'ios': 'cisco_ios',
            'ios-xe': 'cisco_ios',
            'nxos': 'cisco_nxos',
            'eos': 'arista_eos',
            'junos': 'juniper_junos',
        }
        return mapping.get(platform, 'cisco_ios')
    
    def _map_driver_to_napalm(self, driver: str) -> str:
        """Map a Netmiko platform name to NAPALM's name for it"""
        mapping = {
            'cisco_ios': 'ios',
            'cisco_nxos': 'nxos_ssh',
            'arista_eos': 'eos',
            'juniper_junos': 'junos',
        }
        return mapping.get(driver, driver)

    def _map_platform_to_os(self, platform: str) -> str:
        """Map NetBox platform to PyATS OS"""
        mapping = {
            'ios': 'ios',
            'ios-xe': 'iosxe',
            'nxos': 'nxos',
            'eos': 'eos',
            'junos': 'junos',
        }
        return mapping.get(platform, 'ios')
    
    def save_testbed(self, testbed: Dict, filepath: str):
        """Save PyATS testbed to YAML file"""
        with open(filepath, 'w') as f:
            yaml.dump(testbed, f, default_flow_style=False)
        logger.info(f"Saved PyATS testbed to {filepath}")

    def save_nornir_inventory(self, inventory: Dict, host_file: str, group_file: str):
        """Save the generated Nornir inventory as SimpleInventory YAML files"""
        with open(host_file, 'w') as f:
            yaml.dump(inventory['hosts'], f, default_flow_style=False)
        with open(group_file, 'w') as f:
            yaml.dump(inventory['groups'], f, default_flow_style=False)
        logger.info(f"Saved Nornir inventory to {host_file} and {group_file}")


# Usage Example
if __name__ == '__main__':
    # Initialize inventory manager
    inv_mgr = UnifiedInventoryManager(
        netbox_url='https://netbox.local',
        netbox_token='your_token_here'
    )
    
    # Get devices for a specific site and role
    filters = {
        'site': 'dc1',
        'role': 'spine',
        'status': 'active'
    }
    
    # Generate both inventory types
    nornir_inv = inv_mgr.generate_nornir_inventory(filters)
    pyats_testbed = inv_mgr.generate_pyats_testbed(filters)
    
    # Save both inventories
    inv_mgr.save_testbed(pyats_testbed, 'testbed.yaml')
    inv_mgr.save_nornir_inventory(nornir_inv, 'hosts.yaml', 'groups.yaml')

    # Initialize Nornir with dynamic inventory
    nr = InitNornir(
        inventory={
            'plugin': 'SimpleInventory',
            'options': {
                'host_file': 'hosts.yaml',  # Generated from nornir_inv
                'group_file': 'groups.yaml',
            }
        },
        runner={
            'plugin': 'threaded',
            'options': {
                'num_workers': 20,
            }
        }
    )
