from dnacentersdk import DNACenterAPI
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class DNACenterIntegration:
    """
    Cisco DNA Center integration with:
    - Intent-based networking
    - Device compliance
    - Template provisioning
    - Assurance monitoring
    """
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        verify: bool = False
    ):
        self.api = DNACenterAPI(
            username=username,
            password=password,
            base_url=f"https://{host}",
            verify=verify
        )
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all network devices from DNA Center"""
        try:
            response = self.api.devices.get_device_list()
            
            devices = []
            for device in response['response']:
                devices.append({
                    'id': device['id'],
                    'hostname': device['hostname'],
                    'type': device['type'],
                    'platform_id': device.get('platformId'),
                    'ip': device.get('managementIpAddress'),
                    'status': device.get('managementStatus')
                })
            
            return devices
        
        except Exception as e:
            logger.error(f"Failed to retrieve devices from DNA Center: {e}")
            return []
    
    def get_device_compliance(self, device_id: str) -> Dict[str, Any]:
        """Check device compliance status"""
        try:
            response = self.api.compliance.get_compliance_status(
                device_uuid=device_id
            )

            # One record per device, in a list under 'response'
            records = response.get('response') or []
            if not records:
                return {}

            return {
                'device_id': device_id,
                # COMPLIANT, NON_COMPLIANT, IN_PROGRESS, NOT_AVAILABLE, NOT_APPLICABLE or ERROR
                'compliance_status': records[0].get('complianceStatus'),
                'last_updated': records[0].get('lastUpdateTime')
            }
        
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return {}
    
    def deploy_template(
        self,
        template_id: str,
        target_device_id: str,
        variables: Dict[str, str]
    ) -> Optional[str]:
        """Deploy configuration template to device; returns the task ID"""
        try:
            # Render first, to catch bad variables and log what will be pushed
            preview = self.api.configuration_templates.preview_template(
                templateId=template_id,
                deviceId=target_device_id,
                params=variables
            )
            if preview.get('validationErrors'):
                logger.error(f"Template failed validation: {preview['validationErrors']}")
                return None
            logger.debug(f"Rendered config:\n{preview.get('cliPreview')}")

            # Deploy to device (Catalyst Center renders it again per target)
            deploy_response = self.api.configuration_templates.deploy_template_v2(
                templateId=template_id,
                forcePushTemplate=False,
                targetInfo=[{
                    'id': target_device_id,
                    'type': 'MANAGED_DEVICE_UUID',
                    'params': variables
                }]
            )

            task_id = deploy_response['response']['taskId']
            logger.info(f"Deployed template to {target_device_id}, task: {task_id}")
            
            return task_id
        
        except Exception as e:
            logger.error(f"Failed to deploy template: {e}")
            return None

