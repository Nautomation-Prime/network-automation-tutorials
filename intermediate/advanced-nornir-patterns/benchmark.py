#!/usr/bin/env python3
"""
Benchmark your Nornir automation
Measure speed, resource usage, and identify bottlenecks
"""

import time
import psutil
import os
from nornir import InitNornir
from tasks.enterprise_backup import backup_config

class BenchmarkRunner:
    """Run and measure Nornir performance"""
    
    def __init__(self):
        self.metrics = {}
    
    def memory_usage(self):
        """Get current process memory in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def run_benchmark(self, task_name, task, workers=None):
        """Run task and measure performance"""
        
        # Initialize Nornir
        nr = InitNornir(config_file="nornir_config.yaml")
        
        if workers:
            nr.runner.num_workers = workers
        
        # Baseline memory
        mem_start = self.memory_usage()
        time_start = time.time()
        
        # Run task
        results = nr.run(task=task)
        
        # Measurements
        time_end = time.time()
        mem_end = self.memory_usage()
        
        failed = sum(1 for r in results.values() if r.failed)
        succeeded = len(results) - failed
        
        # Record metrics
        self.metrics[task_name] = {
            'total_devices': len(results),
            'succeeded': succeeded,
            'failed': failed,
            'duration_seconds': time_end - time_start,
            'memory_used_mb': mem_end - mem_start,
            'memory_peak_mb': mem_end,
            'devices_per_second': len(results) / (time_end - time_start),
            'workers': nr.runner.num_workers,
        }
        
        return self.metrics[task_name]
    
    def print_report(self):
        """Print benchmark results"""
        
        print("\n" + "="*70)
        print("BENCHMARK REPORT")
        print("="*70)
        
        for test_name, metrics in self.metrics.items():
            print(f"\n{test_name}:")
            print(f"  Devices: {metrics['total_devices']} ({metrics['succeeded']} succeeded, {metrics['failed']} failed)")
            print(f"  Duration: {metrics['duration_seconds']:.2f} seconds")
            print(f"  Throughput: {metrics['devices_per_second']:.1f} devices/second")
            print(f"  Memory used: {metrics['memory_used_mb']:.1f} MB")
            print(f"  Peak memory: {metrics['memory_peak_mb']:.1f} MB")
            print(f"  Workers: {metrics['workers']}")

# Usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Nornir configuration")
    parser.add_argument('--workers', type=int, nargs='+', default=[5, 10, 20],
                        help='Worker counts to test (default: 5 10 20)')
    parser.add_argument('--task', default='backup_config',
                        help='Task to benchmark (default: backup_config)')
    args = parser.parse_args()
    
    runner = BenchmarkRunner()
    
    # Test with different worker counts
    for worker_count in args.workers:
        print(f"Testing with {worker_count} workers...")
        runner.run_benchmark(
            f"backup_config ({worker_count} workers)",
            task=backup_config,
            workers=worker_count
        )
    
    runner.print_report()
