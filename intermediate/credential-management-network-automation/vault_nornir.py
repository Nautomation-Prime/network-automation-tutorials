from nornir import InitNornir
from nornir.core.task import Task, Result
from src.vault_client import VaultClient

vault = VaultClient()

def get_device_credentials_task(task: Task) -> Result:
    """Nornir task to inject credentials from Vault."""
    device_name = task.host.name
    
    try:
        creds = vault.get_device_credentials(device_name)
        
        # Inject credentials into Nornir inventory
        task.host.username = creds["username"]
        task.host.password = creds["password"]
        
        return Result(
            host=task.host,
            result=f"Credentials loaded for {device_name}"
        )
    except Exception as e:
        return Result(
            host=task.host,
            failed=True,
            result=f"Failed to load credentials: {str(e)}"
        )

# Usage
nr = InitNornir(config_file="config.yaml")
nr.run(task=get_device_credentials_task)
