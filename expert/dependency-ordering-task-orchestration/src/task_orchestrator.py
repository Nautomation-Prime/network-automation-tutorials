# src/task_orchestrator.py
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Callable
from enum import Enum

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Task:
    """Represents a single task in the workflow."""
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    dependencies: List[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.dependencies is None:
            self.dependencies = []

class TaskOrchestrator:
    """Execute tasks in dependency order."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.execution_order = []
    
    def add_task(
        self,
        name: str,
        func: Callable,
        dependencies: List[str] = None,
        **kwargs
    ):
        """
        Add task to DAG.
        
        Args:
            name: Task name
            func: Function to execute
            dependencies: List of task names this depends on
            **kwargs: Arguments to pass to function
        """
        task = Task(
            name=name,
            func=func,
            kwargs=kwargs,
            dependencies=dependencies or []
        )
        self.tasks[name] = task
    
    def _validate_dependencies(self) -> None:
        """Ensure all dependencies reference known tasks."""
        missing = {
            dep
            for task in self.tasks.values()
            for dep in task.dependencies
            if dep not in self.tasks
        }
        if missing:
            raise ValueError(f"Unknown task dependencies: {sorted(missing)}")
     
    def validate_dag(self) -> bool:
        """Check for cycles in dependency graph."""
        self._validate_dependencies()
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for dep in self.tasks[node].dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_name in self.tasks:
            if task_name not in visited:
                if has_cycle(task_name):
                    return False
        
        return True
    
    def topological_sort(self) -> List[str]:
        """
        Calculate execution order using topological sort.
        
        Returns:
            List of task names in execution order
        """
        if not self.validate_dag():
            raise ValueError("DAG contains cycle - impossible to order")
        
        visited = set()
        order = []
        
        def visit(node):
            if node in visited:
                return
            
            visited.add(node)
            
            # Visit dependencies first
            for dep in self.tasks[node].dependencies:
                visit(dep)
            
            order.append(node)
        
        for task_name in self.tasks:
            visit(task_name)
        
        return order
    
    def execute(self) -> Dict[str, any]:
        """
        Execute all tasks in dependency order.
        
        Returns:
            dict: Results for each task
        """
        execution_order = self.topological_sort()
        results = {}
        
        print(f"Execution order: {' → '.join(execution_order)}\n")
        
        for task_name in execution_order:
            task = self.tasks[task_name]
            
            # Check if any dependencies failed or were skipped. Checking
            # SKIPPED too makes the skip transitive: if the hub fails, a
            # task that depends on a skipped spoke is skipped as well
            deps_failed = [
                dep for dep in task.dependencies
                if self.tasks[dep].status in (TaskStatus.FAILED, TaskStatus.SKIPPED)
            ]

            if deps_failed:
                task.status = TaskStatus.SKIPPED
                print(f"⏭ Skipping '{task_name}' (depends on failed or skipped: {deps_failed})")
                results[task_name] = {
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error
                }
                continue
            
            task.status = TaskStatus.RUNNING
            print(f"▶ Running '{task_name}'...")
            
            try:
                task.result = task.func(**task.kwargs)
                task.status = TaskStatus.SUCCESS
                print(f"✓ '{task_name}' completed\n")
            
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                print(f"✗ '{task_name}' failed: {str(e)}\n")
            
            results[task_name] = {
                "status": task.status.value,
                "result": task.result,
                "error": task.error
            }
        
        return results
    
    def get_dependency_graph(self) -> dict:
        """Get human-readable dependency graph."""
        return {
            name: task.dependencies
            for name, task in self.tasks.items()
        }
