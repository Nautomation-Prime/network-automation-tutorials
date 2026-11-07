import functools
import time
import statistics
from collections import defaultdict
from threading import Lock

class PerformanceMonitor:
    """Thread-safe performance monitor for tracking execution time."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.lock = Lock()
    
    def monitor(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                with self.lock:
                    self.metrics[func.__name__].append(elapsed)
                print(f"[{func.__name__}] took {elapsed:.2f}s")
        
        return wrapper
    
    def report(self):
        """Print performance statistics."""
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)
        
        with self.lock:
            metrics_snapshot = dict(self.metrics)
        
        for func_name, times in metrics_snapshot.items():
            print(f"\n{func_name}:")
            print(f"  Calls:     {len(times)}")
            print(f"  Min:       {min(times):.3f}s")
            print(f"  Max:       {max(times):.3f}s")
            print(f"  Mean:      {statistics.mean(times):.3f}s")
            if len(times) > 1:
                print(f"  Median:    {statistics.median(times):.3f}s")
                print(f"  StdDev:    {statistics.stdev(times):.3f}s")
            print(f"  Total:     {sum(times):.3f}s")

# Global performance monitor
perf = PerformanceMonitor()
