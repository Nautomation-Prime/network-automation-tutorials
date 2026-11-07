# src/conditional_execution.py
class ConditionalTask:
    """Execute task only if condition is met."""
    
    def __init__(self, name, func, condition=None, dependencies=None):
        self.name = name
        self.func = func
        self.condition = condition or (lambda: True)
        self.dependencies = dependencies or []
    
    def should_execute(self) -> bool:
        """Determine if this task should run."""
        return self.condition()

# Stand-ins for your own task functions, so the example runs as written
def check_if_hub_needs_update():
    return True

def hub_deployment_failed():
    return False

def update_hub_config():
    print("✓ hub configuration updated")

def rollback_hub_config():
    print("⟲ hub configuration rolled back")

# Usage
tasks = [
    ConditionalTask(
        "update_hub",
        update_hub_config,
        condition=lambda: check_if_hub_needs_update()
    ),
    ConditionalTask(
        "rollback_hub",
        rollback_hub_config,
        condition=lambda: hub_deployment_failed(),
        dependencies=["update_hub"]
    )
]

# Only run tasks where condition is True
for task in tasks:
    if task.should_execute():
        task.func()
