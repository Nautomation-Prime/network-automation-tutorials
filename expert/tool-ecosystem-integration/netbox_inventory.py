import pynetbox
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from functools import lru_cache
import asyncio
import httpx

logger = logging.getLogger(__name__)

@dataclass
class NetworkDevice:
    """Normalized device representation"""
    name: str
    site: str
    role: str
    platform: str
    primary_ip: str
    serial_number: str
    asset_tag: str
    device_type: str
    custom_fields: Dict[str, Any]

class NetBoxInventoryManager:
    """
    Advanced NetBox integration with:
    - Pagination handling
    - Caching and refresh
    - Filtering and querying
    - Relationship traversal
    - Bulk operations
    """
    
    def __init__(
        self,
        netbox_url: str,
        netbox_token: str,
        verify_ssl: bool = True,
        cache_ttl: int = 3600
    ):
        self.api = pynetbox.api(netbox_url, token=netbox_token)
        self.api.http_session.verify = verify_ssl
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Any] = {}
        self.cache_time: Dict[str, float] = {}
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        import time
        if key not in self.cache_time:
            return False
        return (time.time() - self.cache_time[key]) < self.cache_ttl

    @staticmethod
    def _role_name(device) -> str:
        """Device role name. NetBox 4 renamed the field from device_role to role."""
        # Read the fields NetBox returned. (getattr on a field that isn't
        # there makes pynetbox fetch the whole device again: one extra API
        # call per device.)
        fields = dict(device)
        role = fields.get('role') or fields.get('device_role')
        return role['name'] if role else 'unknown'

    def get_all_devices(
        self,
        site: Optional[str] = None,
        role: Optional[str] = None,
        status: str = "active"
    ) -> List[NetworkDevice]:
        """
        Query all devices with filtering
        
        Args:
            site: Filter by site name
            role: Filter by device role
            status: Device status (active, decommissioning, etc.)
        
        Returns:
            List of NetworkDevice objects
        """
        cache_key = f"devices:{site}:{role}:{status}"
        
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit: {cache_key}")
            return self.cache[cache_key]
        
        try:
            filters = {'status': status}
            if site:
                filters['site'] = site
            if role:
                filters['role'] = role
            
            all_devices = []
            for device in self.api.dcim.devices.filter(**filters):
                try:
                    net_device = NetworkDevice(
                        name=device.name,
                        site=device.site.name if device.site else 'unknown',
                        role=self._role_name(device),
                        platform=device.platform.name if device.platform else 'unknown',
                        primary_ip=str(device.primary_ip) if device.primary_ip else '',
                        serial_number=device.serial or '',
                        asset_tag=device.asset_tag or '',
                        device_type=device.device_type.model if device.device_type else 'unknown',
                        custom_fields=device.custom_fields or {}
                    )
                    all_devices.append(net_device)
                
                except Exception as e:
                    logger.warning(f"Failed to parse device {device.name}: {e}")
                    continue
            
            # Cache result
            import time
            self.cache[cache_key] = all_devices
            self.cache_time[cache_key] = time.time()
            
            logger.info(f"Retrieved {len(all_devices)} devices from NetBox")
            return all_devices
        
        except Exception as e:
            logger.error(f"Failed to retrieve devices from NetBox: {e}")
            raise
    
    def get_device_by_name(self, name: str) -> Optional[NetworkDevice]:
        """Retrieve specific device by name"""
        try:
            device = self.api.dcim.devices.get(name=name)
            
            return NetworkDevice(
                name=device.name,
                site=device.site.name if device.site else 'unknown',
                role=self._role_name(device),
                platform=device.platform.name if device.platform else 'unknown',
                primary_ip=str(device.primary_ip) if device.primary_ip else '',
                serial_number=device.serial or '',
                asset_tag=device.asset_tag or '',
                device_type=device.device_type.model if device.device_type else 'unknown',
                custom_fields=device.custom_fields or {}
            )
        
        except Exception as e:
            logger.error(f"Device not found: {name}")
            return None
    
    def get_device_interfaces(self, device_name: str) -> List[Dict[str, Any]]:
        """Get all interfaces for a device"""
        try:
            device = self.api.dcim.devices.get(name=device_name)
            
            interfaces = []
            for iface in self.api.dcim.interfaces.filter(device=device.id):
                interfaces.append({
                    'name': iface.name,
                    'type': iface.type.get('value', ''),
                    'mtu': iface.mtu,
                    'enabled': iface.enabled,
                    'description': iface.description,
                    'speed': iface.speed,
                    'duplex': iface.duplex.get('value', '') if iface.duplex else ''
                })
            
            return interfaces
        
        except Exception as e:
            logger.error(f"Failed to retrieve interfaces for {device_name}: {e}")
            return []
    
    def create_device(self, device_data: Dict[str, Any]) -> bool:
        """Create new device in NetBox"""
        try:
            created = self.api.dcim.devices.create(**device_data)
            logger.info(f"Created device in NetBox: {created.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create device: {e}")
            return False
    
    def update_device(self, device_name: str, updates: Dict[str, Any]) -> bool:
        """Update existing device in NetBox"""
        try:
            device = self.api.dcim.devices.get(name=device_name)
            
            for key, value in updates.items():
                setattr(device, key, value)
            
            device.save()
            logger.info(f"Updated device in NetBox: {device_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update device {device_name}: {e}")
            return False
    
    def invalidate_cache(self):
        """Clear all caches to force refresh"""
        self.cache.clear()
        self.cache_time.clear()
        logger.info("NetBox cache invalidated")

