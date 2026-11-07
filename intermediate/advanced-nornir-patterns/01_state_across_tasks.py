"""
State management across multi-step workflows
"""

from datetime import datetime

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command

def step1_backup(task: Task) -> Result:
    """First step: backup config"""
    result = task.run(netmiko_send_command, command_string="show running-config")
    config = result[0].result
    
    return Result(
        host=task.host,
        result={
            'config': config,
            'timestamp': datetime.now()
        }
    )

def step2_validate(task: Task, config_dict: dict) -> Result:
    """Second step: validate config"""
    # Nornir passes the same dict to every host, so extract this host's config
    config = config_dict[task.host.name]
    is_valid = len(config) > 100
    
    return Result(
        host=task.host,
        result={'valid': is_valid}
    )

# Orchestration:
def main():
    nornir = InitNornir(config_file="nornir_config.yaml")
    
    # Step 1: Backup
    backup_results = nornir.run(task=step1_backup)
    
    # Step 2: Validate (pass data from step 1). Hosts whose backup failed
    # have no config (their result is the error text), and Nornir skips
    # them in later runs anyway, so leave them out
    config_data = {
        host_name: multi_result[0].result['config']
        for host_name, multi_result in backup_results.items()
        if not multi_result.failed
    }
    
    validate_results = nornir.run(
        task=step2_validate,
        config_dict=config_data
    )
