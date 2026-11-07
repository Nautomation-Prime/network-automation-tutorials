# src/nornir_preflight_tasks.py
from nornir import InitNornir
from nornir.core.task import Task, Result
from health_checks import DeviceHealthChecker, HealthStatus
from config_backup import ConfigurationBackup

def preflight_validation(task: Task) -> Result:
    """
    Nornir task: Validate device before deployment.
    """
    try:
        device = task.host.get_connection("netmiko", task.nornir.config)
        checker = DeviceHealthChecker(device)
        backup = ConfigurationBackup(device)
        
        # Run health checks
        health_results = checker.run_all_checks()
        
        # Determine status
        critical_issues = [
            r for r in health_results 
            if r.status == HealthStatus.CRITICAL
        ]
        
        if critical_issues:
            return Result(
                host=task.host,
                failed=True,
                result={
                    "preflight_status": "FAILED",
                    "critical_issues": [
                        {
                            "check": r.check_name,
                            "message": r.message
                        }
                        for r in critical_issues
                    ]
                }
            )
        
        # Backup configuration
        backup_result = backup.backup_running_config()
        
        if backup_result["status"] == "failed":
            return Result(
                host=task.host,
                failed=True,
                result={
                    "preflight_status": "FAILED",
                    "reason": "Could not backup configuration",
                    "error": backup_result.get("error")
                }
            )
        
        return Result(
            host=task.host,
            result={
                "preflight_status": "PASSED",
                "health_checks": [
                    {
                        "check": r.check_name,
                        "status": r.status.value,
                        "message": r.message
                    }
                    for r in health_results
                ],
                "backup": backup_result
            }
        )
    
    except Exception as e:
        return Result(
            host=task.host,
            failed=True,
            result={"error": str(e)}
        )

# Usage
nr = InitNornir(config_file="config.yaml")
results = nr.run(task=preflight_validation)

# Filter: Only deploy to passing devices
passing_devices = [
    hostname for hostname, result in results.items()
    if not result[0].failed and result[0].result["preflight_status"] == "PASSED"
]

print(f"✓ {len(passing_devices)} devices passed pre-flight validation")
print(f"✗ {len(results) - len(passing_devices)} devices failed pre-flight")

# Deploy only to passing devices
# nr = InitNornir(config_file="config.yaml")
# nr.inventory.hosts = {h: nr.inventory.hosts[h] for h in passing_devices}
# nr.run(task=deploy_to_devices)
