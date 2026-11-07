from task_orchestrator import TaskOrchestrator

def setup_hub():
    print("  Setting up hub router...")
    # hub setup logic
    return {"hub": "ready"}

def setup_spoke(spoke_id):
    print(f"  Setting up spoke {spoke_id}...")
    # spoke setup logic
    return {"spoke": spoke_id}

def verify_hub_connectivity():
    print("  Verifying hub connectivity...")
    return True

# Create orchestrator
orchestrator = TaskOrchestrator()

# Add tasks with dependencies
orchestrator.add_task("setup_hub", setup_hub)
orchestrator.add_task(
    "verify_hub",
    verify_hub_connectivity,
    dependencies=["setup_hub"]
)
orchestrator.add_task(
    "setup_spoke_1",
    setup_spoke,
    spoke_id=1,
    dependencies=["verify_hub"]
)
orchestrator.add_task(
    "setup_spoke_2",
    setup_spoke,
    spoke_id=2,
    dependencies=["verify_hub"]
)

# Visualize
print("Dependency Graph:")
print(orchestrator.get_dependency_graph())

# Execute
results = orchestrator.execute()

print("\nFinal Results:")
for task, result in results.items():
    print(f"  {task}: {result['status']}")
