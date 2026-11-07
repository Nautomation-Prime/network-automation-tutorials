from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command

def backup_via_bastion(task: Task) -> Result:
    """Backup config through bastion host"""

    # Nornir hands its ssh.config_file setting (default ~/.ssh/config) to
    # Netmiko, which follows the ProxyJump for this host
    result = task.run(
        netmiko_send_command,
        command_string="show running-config"
    )
    
    return Result(host=task.host, result=result[0].result)

# In inventory/hosts.yaml
# No special config needed - SSH just uses the proxy!
