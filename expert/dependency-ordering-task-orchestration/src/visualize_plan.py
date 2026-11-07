import json

def visualize_dag(orchestrator):
    """Print DAG visualization."""
    graph = orchestrator.get_dependency_graph()
    
    print("\nTask Dependencies:")
    for task, deps in graph.items():
        if deps:
            print(f"  {task} ← {deps}")
        else:
            print(f"  {task} (no dependencies)")
    
    execution_order = orchestrator.topological_sort()
    print(f"\nExecution Order: {' → '.join(execution_order)}")
