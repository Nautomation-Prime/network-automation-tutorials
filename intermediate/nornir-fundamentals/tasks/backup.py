"""
Nornir Tasks for Configuration Backup
Description: Parallel backup of running configs from Cisco devices
Author: Nautomation Prime
"""

from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_running_config(task: Task) -> Result:
    """
    Backup the running configuration from a device
    
    This is a Nornir task - it runs once per device, in parallel.
    
    Args:
        task: Nornir task object containing device info
        
    Returns:
        Result object with config data and metadata
    """
    device_name = task.host.name
    device_ip = task.host.hostname
    device_type = task.host.data.get('device_type', 'cisco_ios')
    
    logger.info(f"Starting backup for {device_name} ({device_ip})")
    
    try:
        # Send the 'show running-config' command via Netmiko (handled by nornir-netmiko)
        result = task.run(
            netmiko_send_command,
            command_string="show running-config",
            use_textfsm=False,  # We want raw config text, not parsed
            name="Retrieve running config"
        )
        
        config = result[0].result  # Extract the config from the result
        
        # Verify we got config data
        if isinstance(config, str) and len(config) > 100:
            logger.info(f"✓ {device_name}: Retrieved {len(config)} bytes")
            return Result(
                host=task.host,
                result={
                    'config': config,
                    'size': len(config),
                    'status': 'success'
                }
            )
        else:
            logger.warning(f"⚠ {device_name}: Config seems too small or invalid")
            return Result(
                host=task.host,
                result={
                    'config': None,
                    'size': 0,
                    'status': 'invalid-data'
                },
                failed=True
            )
            
    except Exception as e:
        logger.error(f"✗ {device_name}: {str(e)}")
        return Result(
            host=task.host,
            result={
                'config': None,
                'size': 0,
                'status': f'failed: {str(e)}'
            },
            failed=True
        )

def save_config_to_file(task: Task, config_data: dict, backup_dir: str = "configs") -> Result:
    """
    Save configuration to a timestamped file
    
    Args:
        task: Nornir task object
        config_data: Dictionary mapping host name -> that host's backup result
                     (config, size, status) from the previous task. Nornir passes
                     the SAME kwargs to every host, so we look up this host's own
                     entry via task.host.name.
        backup_dir: Directory to save configs
        
    Returns:
        Result object with file info
    """
    device_name = task.host.name
    
    try:
        # Create config directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Pull out THIS host's result from the map of all results
        host_config = config_data.get(device_name, {})
        
        # Only save if we have valid config
        if host_config.get('status') != 'success':
            logger.warning(f"⚠ {device_name}: Skipping save (status: {host_config.get('status')})")
            return Result(
                host=task.host,
                result={
                    'filename': None,
                    'path': None,
                    'status': host_config.get('status')
                },
                failed=True
            )
        
        # Create safe filename
        safe_name = device_name.replace('.', '-')
        filename = f"{safe_name}_running-config.txt"
        filepath = os.path.join(backup_dir, filename)
        
        # Write config to file
        with open(filepath, 'w') as f:
            f.write(host_config['config'])
        
        file_size = os.path.getsize(filepath)
        logger.info(f"✓ {device_name}: Saved to {filepath} ({file_size:,} bytes)")
        
        return Result(
            host=task.host,
            result={
                'filename': filename,
                'path': filepath,
                'size': file_size,
                'status': 'success'
            }
        )
        
    except Exception as e:
        logger.error(f"✗ {device_name}: File save failed - {str(e)}")
        return Result(
            host=task.host,
            result={
                'filename': None,
                'path': None,
                'status': f'save-failed: {str(e)}'
            },
            failed=True
        )
