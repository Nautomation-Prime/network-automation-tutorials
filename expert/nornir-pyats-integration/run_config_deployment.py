from nornir import InitNornir
from nornir.core.filter import F
from tasks.config_management import orchestrated_config_deployment

# Initialize Nornir with custom configuration
nr = InitNornir(
    inventory={
        'plugin': 'SimpleInventory',
        'options': {
            'host_file': 'inventory/hosts.yaml',
            'group_file': 'inventory/groups.yaml',
        }
    },
    runner={
        'plugin': 'threaded',
        'options': {
            'num_workers': 10,  # Conservative for safety
        }
    },
    logging={
        'enabled': False,  # Use structlog instead
    }
)

# Example deployment
commands = [
    'interface GigabitEthernet0/1',
    'description Managed by Automation',
    'no shutdown',
]

validation_commands = [
    'show interface GigabitEthernet0/1 status',
    'show interface GigabitEthernet0/1 | include line protocol',
]

# Site and role are groups in the Step 1 inventory, not host data, so
# filter on group membership
results, config_mgr = orchestrated_config_deployment(
    nr.filter(F(groups__contains='access-switch') & F(groups__contains='dc1')),
    commands=commands,
    validation_commands=validation_commands,
    dry_run=True  # Start with dry run!
)

# Review change history
for change in config_mgr.change_history:
    print(f"{change.device}: {change.state.value} in {change.execution_time:.2f}s")
