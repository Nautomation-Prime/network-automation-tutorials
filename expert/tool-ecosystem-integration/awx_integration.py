import requests
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class AWXIntegration:
    """AWX (Ansible Web X) integration for playbook execution"""
    
    def __init__(self, tower_url: str, username: str, password: str):
        self.tower_url = tower_url
        self.auth = (username, password)
        self.headers = {'Content-Type': 'application/json'}
    
    def launch_job_template(
        self,
        template_id: int,
        extra_vars: Dict[str, Any],
        inventory_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Launch Ansible job template
        
        Args:
            template_id: Job template ID in Tower
            extra_vars: Variables to pass to playbook
            inventory_id: Optional override inventory
        
        Returns:
            Job ID
        """
        try:
            payload = {
                'extra_vars': json.dumps(extra_vars)
            }
            
            if inventory_id:
                payload['inventory'] = inventory_id
            
            response = requests.post(
                f"{self.tower_url}/api/v2/job_templates/{template_id}/launch/",
                auth=self.auth,
                json=payload,
                headers=self.headers,
                verify=False
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to launch job: {response.text}")
                return None
            
            job_id = response.json()['job']
            logger.info(f"Launched AWX job: {job_id}")
            
            return job_id
        
        except Exception as e:
            logger.error(f"Exception launching job template: {e}")
            return None
    
    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get AWX job execution status"""
        try:
            response = requests.get(
                f"{self.tower_url}/api/v2/jobs/{job_id}/",
                auth=self.auth,
                verify=False
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return {
                'id': job_id,
                'status': data['status'],
                'started': data['started'],
                'finished': data['finished'],
                'failed': data['failed'],
                'result_stdout': data.get('result_stdout', '')
            }
        
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

