# src/nornir_idempotent_tasks.py
from nornir import InitNornir
from nornir.core.task import Task, Result
from idempotent_operations import IdempotentOperations

def ensure_vlans(task: Task) -> Result:
    """Nornir task: Ensure VLANs exist (idempotent)."""
    device = task.host.get_connection("netmiko", task.nornir.config)
    ops = IdempotentOperations()
    
    # Get VLAN configuration from inventory or task data
    vlans = task.host.get("vlans", {})
    
    results = []
    for vlan_id, vlan_config in vlans.items():
        result = ops.ensure_vlan_exists(
            device,
            vlan_id,
            vlan_config["name"]
        )
        results.append(result)
    
    return Result(
        host=task.host,
        result={
            "vlans": [
                {
                    "vlan_id": r.details["vlan_id"],
                    "status": r.status.value,
                    "message": r.message
                }
                for r in results
            ]
        }
    )

# Usage
nr = InitNornir(config_file="config.yaml")
results = nr.run(task=ensure_vlans)

# Results show what changed
for hostname, result in results.items():
    for vlan in result[0].result["vlans"]:
        print(f"{hostname}: VLAN {vlan['vlan_id']} - {vlan['status']}")
