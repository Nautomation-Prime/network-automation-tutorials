"""
Multi-vendor task with platform abstraction
"""

from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command

VENDOR_CONFIGS = {
    'cisco_ios': 'show running-config',
    'cisco_nxos': 'show running-config',
    'arista_eos': 'show running-config',
    'juniper_junos': 'show configuration',
    'paloalto_panos': 'show config running',
}

def backup_multivendor(task: Task) -> Result:
    """Backup any vendor device"""
    
    device_type = task.host.data.get('device_type', 'cisco_ios')
    
    # Get vendor-specific command
    command = VENDOR_CONFIGS.get(device_type)
    
    if not command:
        return Result(
            host=task.host,
            result={'error': f'Unknown device type: {device_type}'},
            failed=True
        )
    
    try:
        result = task.run(netmiko_send_command, command_string=command)
        config = result[0].result
        
        return Result(
            host=task.host,
            result={'config': config, 'vendor': device_type}
        )
    except Exception as e:
        return Result(
            host=task.host,
            result={'error': str(e)},
            failed=True
        )
