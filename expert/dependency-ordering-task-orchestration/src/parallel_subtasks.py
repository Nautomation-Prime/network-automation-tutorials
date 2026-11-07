# src/parallel_subtasks.py
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable

class ParallelTask:
    """Task that can execute sub-tasks in parallel."""
    
    def __init__(self, name: str, items: List, worker_func: Callable):
        self.name = name
        self.items = items
        self.worker_func = worker_func
    
    def execute(self, max_workers: int = 5) -> dict:
        """
        Execute task across items in parallel.
        
        Example:
            # Configure 100 devices in parallel
            task = ParallelTask(
                "configure_all_spokes",
                items=spoke_devices,
                worker_func=configure_device
            )
            results = task.execute(max_workers=10)
        """
        results = {"success": [], "failed": []}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.worker_func, item): item
                for item in self.items
            }
            
            for future in futures:
                item = futures[future]
                try:
                    result = future.result()
                    results["success"].append(item)
                except Exception as e:
                    results["failed"].append((item, str(e)))
        
        return results

# Stand-in for your real per-device task, so the example runs as written
def configure_spoke_device(name: str) -> str:
    return f"{name} configured"

# Usage
task = ParallelTask(
    "configure_spokes",
    items=[f"spoke{i}" for i in range(1, 51)],
    worker_func=configure_spoke_device
)

results = task.execute(max_workers=10)
print(f"✓ {len(results['success'])} spokes configured")
print(f"✗ {len(results['failed'])} spokes failed")
