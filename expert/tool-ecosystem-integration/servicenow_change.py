import requests
import json
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChangeState(Enum):
    """ServiceNow change_request states (the 'state' field's values)"""
    NEW = "-5"
    ASSESS = "-4"
    AUTHORIZE = "-3"
    SCHEDULED = "-2"
    IMPLEMENT = "-1"
    REVIEW = "0"
    CLOSED = "3"     # Needs close_code and close_notes
    CANCELED = "4"

class ServiceNowChangeManager:
    """
    Advanced ServiceNow integration with:
    - Change ticket creation and tracking
    - Approval workflow integration
    - Risk assessment automation
    - Audit trail generation
    """
    
    def __init__(self, instance_url: str, username: str, password: str):
        self.instance_url = instance_url
        self.auth = (username, password)
        self.base_url = f"https://{instance_url}/api/now"
    
    def create_change_request(
        self,
        short_description: str,
        description: str,
        change_type: str = "Standard",
        priority: int = 3,
        assignment_group: str = "Network Engineering",
        risk_level: str = "Moderate",
        impact: str = "Low to Medium"
    ) -> Optional[str]:
        """
        Create change request in ServiceNow
        
        Args:
            short_description: Brief summary
            description: Detailed change description
            change_type: Standard, Normal, Emergency
            priority: 1-5, where 1 is highest
            assignment_group: Team to assign to (group name)
            risk_level: Low, Moderate, High, Very High
            impact: Expected impact assessment
        
        Returns:
            Change request number (e.g., CHG0123456)
        """
        try:
            # Reference fields such as assignment_group take a sys_id; a
            # dot-walked 'assignment_group.name' is silently ignored on POST
            group_sys_id = self._group_sys_id(assignment_group)
            if not group_sys_id:
                logger.error(f"Assignment group not found: {assignment_group}")
                return None

            payload = {
                'short_description': short_description,
                'description': description,
                'type': change_type.lower(),  # choice values: standard, normal, emergency
                'priority': str(priority),
                'assignment_group': group_sys_id,
                'justification': f'Automated network change via Nautomation. Impact: {impact}',
                'risk_impact_analysis': f'Risk: {risk_level}. Impact: {impact}',
                'cab_required': risk_level in ['High', 'Very High']
            }
            
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            
            response = requests.post(
                f"{self.base_url}/table/change_request",
                auth=self.auth,
                json=payload,
                headers=headers,
                verify=False
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to create change request: {response.text}")
                return None
            
            data = response.json()
            result = data.get('result', {})
            if isinstance(result, list):
                result = result[0] if result else {}
            change_number = result.get('number')
            
            if not change_number:
                logger.error(f"Change request response did not include a number: {data}")
                return None
            
            logger.info(f"Created change request: {change_number}")
            return change_number
        
        except Exception as e:
            logger.error(f"Exception creating change request: {e}")
            return None
    
    def _group_sys_id(self, group_name: str) -> Optional[str]:
        """Look up an assignment group's sys_id by name"""
        response = requests.get(
            f"{self.base_url}/table/sys_user_group",
            params={'sysparm_query': f'name={group_name}', 'sysparm_fields': 'sys_id'},
            auth=self.auth,
            verify=False
        )
        if response.status_code != 200:
            return None
        results = response.json().get('result', [])
        return results[0]['sys_id'] if results else None

    def update_change_status(
        self,
        change_number: str,
        state: ChangeState,
        work_notes: str = "",
        close_code: Optional[str] = None
    ) -> bool:
        """
        Update change request status

        The instance's state model decides which moves are allowed (a
        normal change can't jump from New to Implement without approval).
        Closing needs a close_code: 'successful', 'successful_issues' or
        'unsuccessful'; work_notes become the close notes.
        """
        try:
            change = self.get_change_details(change_number)
            if not change or not change.get('sys_id'):
                logger.error(f"Could not find change request: {change_number}")
                return False

            payload = {
                'state': state.value,
                'work_notes': work_notes
            }
            if state == ChangeState.CLOSED:
                if not close_code:
                    raise ValueError("Closing a change needs a close_code")
                payload['close_code'] = close_code
                payload['close_notes'] = work_notes
            
            headers = {'Content-Type': 'application/json'}
            
            response = requests.patch(
                f"{self.base_url}/table/change_request/{change['sys_id']}",
                auth=self.auth,
                json=payload,
                headers=headers,
                verify=False
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update change: {response.text}")
                return False
            
            logger.info(f"Updated {change_number} to state {state.name}")
            return True
        
        except Exception as e:
            logger.error(f"Exception updating change status: {e}")
            return False
    
    def add_work_notes(self, change_number: str, notes: str) -> bool:
        """Add work notes to change request"""
        try:
            change = self.get_change_details(change_number)
            if not change or not change.get('sys_id'):
                logger.error(f"Could not find change request: {change_number}")
                return False
            
            payload = {'work_notes': notes}
            
            response = requests.patch(
                f"{self.base_url}/table/change_request/{change['sys_id']}",
                auth=self.auth,
                json=payload,
                verify=False
            )
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Failed to add work notes: {e}")
            return False
    
    def get_change_details(self, change_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve change details"""
        try:
            response = requests.get(
                f"{self.base_url}/table/change_request?sysparm_query=number={change_number}",
                auth=self.auth,
                verify=False
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return data['result'][0] if data['result'] else None
        
        except Exception as e:
            logger.error(f"Failed to get change details: {e}")
            return None

