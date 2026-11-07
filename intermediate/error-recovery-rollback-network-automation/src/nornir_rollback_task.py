# src/nornir_rollback_task.py
from nornir import InitNornir
from nornir.core.task import Task, Result
from rollback import RollbackManager
from validation import (
    validate_no_config_errors,
    validate_interfaces_up
)

def deploy_with_rollback(task: Task) -> Result:
    """
    Nornir task: Deploy config with automatic rollback.
    """
    try:
        # Get device connection
        device = task.host.get_connection("netmiko", task.nornir.config)
        
        # Initialize rollback manager
        rollback = RollbackManager(device)
        
        # Define change function
        def apply_changes(dev):
            dev.send_config_set(["interface Gi0/0/1", "shutdown"])
        
        # Define validators
        validators = [
            ("config_errors", validate_no_config_errors),
            ("interfaces_up", validate_interfaces_up),
        ]
        
        # Perform safe deployment
        success = rollback.safe_config_deploy(apply_changes, validators)
        
        if success:
            return Result(
                host=task.host,
                result="Deployment successful with all validations passed"
            )
        else:
            return Result(
                host=task.host,
                failed=True,
                result="Deployment failed and was rolled back"
            )
    
    except Exception as e:
        return Result(
            host=task.host,
            failed=True,
            result=f"Deployment error: {str(e)}"
        )

# Usage
nr = InitNornir(config_file="config.yaml")
results = nr.run(task=deploy_with_rollback)

# Print results
for hostname, result in results.items():
    status = "✓" if not result[0].failed else "✗"
    print(f"{status} {hostname}: {result[0].result}")
