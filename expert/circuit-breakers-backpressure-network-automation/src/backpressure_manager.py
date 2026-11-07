# src/backpressure_manager.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpen

class BackpressureManager:
    """Manage concurrency with circuit breaker protection."""
    
    def __init__(self, max_workers: int = 10, circuit_breaker: CircuitBreaker = None):
        self.max_workers = max_workers
        self.breaker = circuit_breaker
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.results = {
            "success": [],
            "failed": [],
            "circuit_open": []
        }
    
    def execute(self, tasks: list) -> dict:
        """
        Execute tasks with backpressure and circuit breaker.
        
        Args:
            tasks: List of (func, args, kwargs) tuples
        
        Returns:
            dict: Results organized by outcome
        """
        self.results = {
            "success": [],
            "failed": [],
            "circuit_open": []
        }
        futures = {}
        
        # Submit all tasks (executor will queue them)
        for task_id, (func, args, kwargs) in enumerate(tasks):
            if self.breaker:
                # Wrap function with circuit breaker
                future = self.executor.submit(
                    self._execute_with_breaker,
                    func,
                    args,
                    kwargs,
                    task_id
                )
            else:
                future = self.executor.submit(func, *args, **kwargs)
            
            futures[future] = task_id
        
        # Process completions as they arrive
        for future in as_completed(futures):
            task_id = futures[future]
            
            try:
                result = future.result()
                self.results["success"].append({
                    "task_id": task_id,
                    "result": result
                })
            except CircuitBreakerOpen:
                self.results["circuit_open"].append(task_id)
            except Exception as e:
                self.results["failed"].append({
                    "task_id": task_id,
                    "error": str(e)
                })
        
        return self.results
    
    def _execute_with_breaker(self, func, args, kwargs, task_id):
        """Execute function through circuit breaker."""
        return self.breaker.call(func, *args, **kwargs)
