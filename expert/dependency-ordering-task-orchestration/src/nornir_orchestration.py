# src/nornir_orchestration.py
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir.core.filter import F

def deploy_to_device(task: Task) -> Result:
    """Stand-in for your real deployment task."""
    return Result(host=task.host, result=f"deployed to {task.host.name}")


def orchestrate_multisite_deployment():
    """Orchestrate deployment across multiple sites."""
    
    # Load inventory
    nr = InitNornir(config_file="config.yaml")
    
    # Define sites and dependencies
    sites = {
        "hub1": {
            "devices": ["hub1-router", "hub1-switch"],
            "depends_on": []
        },
        "site1": {
            "devices": ["site1-router"],
            "depends_on": ["hub1"]
        },
        "site2": {
            "devices": ["site2-router"],
            "depends_on": ["hub1"]
        }
    }
    
    deployed_sites = set()
    results = {}
    
    # Deploy sites in dependency order
    for site, config in sites.items():
        # Wait for dependencies
        if not all(dep in deployed_sites for dep in config["depends_on"]):
            print(f"⏳ Waiting for dependencies for {site}...")
            continue
        
        print(f"\nDeploying site: {site}")
        
        # Filter inventory to this site's devices
        site_inventory = nr.filter(F(name__in=config["devices"]))
        
        # Deploy to site
        site_results = site_inventory.run(
            task=deploy_to_device
        )
        
        # Check results
        if all(not r[0].failed for r in site_results.values()):
            deployed_sites.add(site)
            results[site] = "success"
            print(f"✓ {site} deployment successful")
        else:
            results[site] = "failed"
            print(f"✗ {site} deployment failed")
    
    return results
