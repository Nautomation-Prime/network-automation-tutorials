from nornir import InitNornir
from nornir.core.task import Task, Result

def test_bastion_path(task: Task) -> Result:
    """Verify connectivity through bastion"""

    try:
        # Open the same Netmiko connection the backup will use, with the
        # same SSH config and credentials. (A bare paramiko.SSHClient would
        # be no test at all: paramiko never reads ~/.ssh/config, so it
        # would try to reach the device directly.)
        conn = task.host.get_connection("netmiko", task.nornir.config)
        prompt = conn.find_prompt()

        return Result(
            host=task.host,
            result={'status': 'reachable', 'message': f'Connected through bastion: {prompt}'}
        )
        
    except Exception as e:
        return Result(
            host=task.host,
            result={'status': 'unreachable', 'error': str(e)},
            failed=True
        )

# Usage
nr = InitNornir(config_file="nornir_config.yaml")
results = nr.run(task=test_bastion_path)

for device, result in results.items():
    status = "✓" if not result.failed else "✗"
    print(f"{device}: {status} {result[0].result['status']}")
