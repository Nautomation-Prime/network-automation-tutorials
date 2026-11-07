import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time

from scrapli.driver.core import AsyncIOSXEDriver
from scrapli.exceptions import ScrapliException

logger = logging.getLogger(__name__)

class TransportType(Enum):
    """Supported transport types for device connections"""
    SSH = "ssh"
    NETCONF = "netconf"
    REST = "rest"

@dataclass
class DeviceConfig:
    """Device connection configuration"""
    host: str
    port: int = 22
    username: str = "admin"
    password: str = ""
    transport_type: TransportType = TransportType.SSH
    timeout: int = 30
    retries: int = 3
    tags: Dict[str, str] = None

class AsyncConnectionPool:
    """
    Advanced async connection pool with:
    - Semaphore-based rate limiting
    - Per-device timeout enforcement
    - Automatic retry with exponential backoff
    - Connection state tracking
    - Metrics collection
    """
    
    def __init__(self, max_concurrent: int = 50, global_timeout: int = 300):
        """
        Args:
            max_concurrent: Max simultaneous connections (semaphore size)
            global_timeout: Timeout for entire batch operation
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.global_timeout = global_timeout
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.metrics = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'timeout': 0,
            'total_duration': 0,
        }
        self.lock = asyncio.Lock()
    
    async def _execute_with_semaphore(
        self,
        device: DeviceConfig,
        command: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Execute command with semaphore rate limiting"""
        async with self.semaphore:
            return await self._execute_device_command(device, command, retry_count)
    
    async def _execute_device_command(
        self,
        device: DeviceConfig,
        command: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Execute single command with timeout and retry logic"""
        async with self.lock:
            self.metrics['total_attempts'] += 1
        
        start_time = time.time()
        
        try:
            if device.transport_type == TransportType.SSH:
                return await self._ssh_command(device, command)
            elif device.transport_type == TransportType.REST:
                return await self._rest_command(device, command)
            else:
                raise ValueError(f"Unsupported transport: {device.transport_type}")
                
        except asyncio.TimeoutError:
            async with self.lock:
                self.metrics['timeout'] += 1
            
            if retry_count < device.retries:
                backoff = 2 ** retry_count  # Exponential backoff
                logger.warning(
                    f"Timeout on {device.host}, retrying in {backoff}s "
                    f"(attempt {retry_count + 1}/{device.retries})",
                    extra={'device': device.host, 'retry': retry_count + 1}
                )
                await asyncio.sleep(backoff)
                return await self._execute_device_command(device, command, retry_count + 1)
            else:
                async with self.lock:
                    self.metrics['failed'] += 1
                return {
                    'device': device.host,
                    'status': 'timeout',
                    'error': f"Command timed out after {device.retries} retries",
                    'duration': time.time() - start_time
                }
        
        except ScrapliException as e:
            async with self.lock:
                self.metrics['failed'] += 1
            
            logger.error(
                f"Scrapli error on {device.host}: {e}",
                extra={'device': device.host, 'error': str(e)}
            )
            return {
                'device': device.host,
                'status': 'error',
                'error': str(e),
                'duration': time.time() - start_time
            }
        
        except Exception as e:
            async with self.lock:
                self.metrics['failed'] += 1
            
            logger.error(
                f"Unexpected error on {device.host}: {e}",
                extra={'device': device.host, 'error': str(e)}
            )
            return {
                'device': device.host,
                'status': 'error',
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    async def _ssh_command(self, device: DeviceConfig, command: str) -> Dict[str, Any]:
        """Execute SSH command with Scrapli"""
        device_dict = {
            'host': device.host,
            'port': device.port,
            'auth_username': device.username,
            'auth_password': device.password,
            'auth_strict_key': False,
            'timeout_socket': device.timeout,
            'timeout_transport': device.timeout,
            'timeout_ops': device.timeout,
            # Async drivers need an async transport; Scrapli's default
            # (system ssh) is synchronous and is refused here
            'transport': 'asyncssh',
        }

        start = time.time()
        # The IOS-XE driver handles the prompt, paging and privilege levels
        # (works for classic IOS too); use the driver for your platform
        async with AsyncIOSXEDriver(**device_dict) as conn:
            result = await asyncio.wait_for(
                conn.send_command(command),
                timeout=device.timeout
            )
        
        async with self.lock:
            self.metrics['successful'] += 1
        
        return {
            'device': device.host,
            'status': 'success',
            'output': result.result,
            'duration': time.time() - start
        }
    
    async def _rest_command(self, device: DeviceConfig, command: str) -> Dict[str, Any]:
        """Execute REST API call with httpx"""
        import httpx
        
        start = time.time()
        timeout = httpx.Timeout(device.timeout, connect=5.0)
        
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            resp = await asyncio.wait_for(
                client.get(
                    f"https://{device.host}:{device.port}/{command}",
                    auth=(device.username, device.password)
                ),
                timeout=device.timeout
            )
        
        if resp.status_code != 200:
            async with self.lock:
                self.metrics['failed'] += 1
            return {
                'device': device.host,
                'status': 'error',
                'error': f"HTTP {resp.status_code}",
                'duration': time.time() - start
            }
        
        async with self.lock:
            self.metrics['successful'] += 1
        
        return {
            'device': device.host,
            'status': 'success',
            'output': resp.json(),
            'duration': time.time() - start
        }
    
    async def execute_batch(
        self,
        devices: List[DeviceConfig],
        command: str = "show version",
        show_progress: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute command on multiple devices concurrently
        
        Args:
            devices: List of device configurations
            command: Command to execute
            show_progress: Enable progress bar with tqdm
        
        Returns:
            List of results, one per device
        """
        if show_progress:
            try:
                from tqdm.asyncio import tqdm
                tasks = [
                    self._execute_with_semaphore(device, command)
                    for device in devices
                ]
                results = await tqdm.gather(*tasks, desc="Collecting data")
            except ImportError:
                logger.warning("tqdm not installed, running without progress bar")
                tasks = [
                    self._execute_with_semaphore(device, command)
                    for device in devices
                ]
                results = await asyncio.gather(*tasks)
        else:
            tasks = [
                asyncio.create_task(self._execute_with_semaphore(device, command))
                for device in devices
            ]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks),
                    timeout=self.global_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Global timeout ({self.global_timeout}s) exceeded")
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                results = []
                for task in tasks:
                    if task.done() and not task.cancelled():
                        try:
                            results.append(task.result())
                        except Exception as e:
                            results.append({
                                'device': 'unknown',
                                'status': 'error',
                                'error': str(e),
                                'duration': 0
                            })
        
        return results
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics"""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful'] / self.metrics['total_attempts']
                if self.metrics['total_attempts'] > 0 else 0
            )
        }


from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject new requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures:
    - CLOSED: Normal operation, requests proceed
    - OPEN: Too many failures detected, requests rejected immediately
    - HALF_OPEN: Attempting recovery, allow limited requests
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    async def call(self, coro):
        """
        Execute coroutine with circuit breaker protection
        
        Args:
            coro: Coroutine to execute
        
        Returns:
            Result if successful
        
        Raises:
            Exception: If circuit is OPEN
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # We'll never await the coroutine, so close it (this also
                # avoids a "coroutine was never awaited" warning)
                coro.close()
                raise RuntimeError(
                    f"Circuit breaker OPEN for {self.timeout}s (device temporarily unavailable)"
                )
        
        try:
            result = await coro
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            if self.state == CircuitState.OPEN:
                logger.error(f"Circuit breaker opened after failure: {e}")
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info("Circuit breaker CLOSED - device recovered")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if (
            self.state == CircuitState.HALF_OPEN
            or self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN - {self.failure_count} failures detected")
    
    def _should_attempt_reset(self) -> bool:
        """Check if timeout has elapsed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout


import json
from typing import Coroutine
from prometheus_client import Counter, Histogram, Gauge
import httpx

# Prometheus metrics
telemetry_collection_duration = Histogram(
    'telemetry_collection_seconds',
    'Time spent collecting telemetry',
    ['device', 'metric_type']
)
telemetry_errors = Counter(
    'telemetry_collection_errors_total',
    'Total telemetry collection errors',
    ['device', 'error_type']
)
telemetry_points_collected = Counter(
    'telemetry_points_collected_total',
    'Total data points collected',
    ['device']
)
active_telemetry_tasks = Gauge(
    'active_telemetry_tasks',
    'Currently active telemetry collection tasks'
)

class AsyncTelemetryCollector:
    """Collect streaming telemetry from multiple data sources concurrently"""
    
    def __init__(self, max_concurrent: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.results = []
        self.circuit_breakers = {}
    
    async def collect_device_metrics(
        self,
        device: DeviceConfig,
        metrics: List[str],
        interval: int = 60
    ) -> None:
        """
        Continuously collect metrics from a device
        
        Args:
            device: Device configuration
            metrics: List of metrics to collect (e.g., ["cpu", "memory", "interfaceStats"])
            interval: Collection interval in seconds
        """
        if device.host not in self.circuit_breakers:
            self.circuit_breakers[device.host] = CircuitBreaker()
        
        async with self.semaphore:
            while True:
                try:
                    active_telemetry_tasks.inc()
                    
                    for metric in metrics:
                        try:
                            result = await self.circuit_breakers[device.host].call(
                                self._fetch_metric(device, metric)
                            )
                            
                            telemetry_collection_duration.labels(
                                device=device.host,
                                metric_type=metric
                            ).observe(result['duration'])
                            
                            telemetry_points_collected.labels(
                                device=device.host
                            ).inc()
                            
                            self.results.append({
                                'timestamp': datetime.now().isoformat(),
                                'device': device.host,
                                'metric': metric,
                                'value': result['value']
                            })
                        
                        except Exception as e:
                            telemetry_errors.labels(
                                device=device.host,
                                error_type=type(e).__name__
                            ).inc()
                            logger.error(
                                f"Error collecting {metric} from {device.host}: {e}",
                                extra={'device': device.host, 'metric': metric}
                            )
                    
                    await asyncio.sleep(interval)
                
                except asyncio.CancelledError:
                    logger.info(f"Telemetry collection cancelled for {device.host}")
                    break
                
                finally:
                    active_telemetry_tasks.dec()
    
    async def _fetch_metric(self, device: DeviceConfig, metric: str) -> Dict[str, Any]:
        """Fetch a specific metric from device"""
        start = time.time()
        
        async with httpx.AsyncClient(verify=False) as client:
            resp = await asyncio.wait_for(
                client.get(
                    f"https://{device.host}/api/v1/metrics/{metric}",
                    auth=(device.username, device.password)
                ),
                timeout=device.timeout
            )
        
        data = resp.json()
        return {
            'value': data.get('value', 0),
            'duration': time.time() - start
        }


from contextlib import asynccontextmanager

class AsyncTaskManager:
    """Manage lifecycle of concurrent tasks with graceful cancellation"""
    
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(self, name: str, coro: Coroutine) -> asyncio.Task:
        """Create and track a task"""
        task = asyncio.create_task(coro)
        self.tasks[name] = task
        return task
    
    async def cancel_all(self) -> None:
        """Cancel all tasks gracefully"""
        for name, task in self.tasks.items():
            if not task.done():
                logger.info(f"Cancelling task: {name}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def close(self) -> None:
        """Close and clean up all tasks"""
        await self.cancel_all()
        self.tasks.clear()
    
    @asynccontextmanager
    async def managed_task(self, name: str, coro: Coroutine):
        """Context manager for task lifecycle"""
        task = self.create_task(name, coro)
        try:
            yield task
        finally:
            if not task.done():
                task.cancel()


async def main():
    """
    Complete async network automation workflow:
    1. Initialize connection pool
    2. Collect configuration from 1000s of devices
    3. Validate configuration changes
    4. Export metrics
    5. Clean gracefully on completion or error
    """
    
    # Define devices
    devices = [
        DeviceConfig(host=f"router-{i}.example.com", username="admin", password="secret")
        for i in range(1, 101)  # 100 devices
    ]
    
    # Initialize connection pool
    pool = AsyncConnectionPool(max_concurrent=50)
    task_manager = AsyncTaskManager()
    
    try:
        # Start telemetry collection
        collector = AsyncTelemetryCollector(max_concurrent=100)
        for device in devices[:10]:  # Collect from subset
            task_manager.create_task(
                f"telemetry-{device.host}",
                collector.collect_device_metrics(device, ["cpu", "memory"], interval=30)
            )
        
        # Execute configuration commands
        results = await pool.execute_batch(
            devices,
            command="show running-config",
            show_progress=True
        )
        
        # Log results
        for result in results:
            logger.info(
                f"Device: {result['device']}, Status: {result['status']}, "
                f"Duration: {result['duration']:.2f}s"
            )
        
        # Display metrics
        metrics = await pool.get_metrics()
        logger.info(f"Pool metrics: {metrics}")
        
        # Simulate processing
        await asyncio.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    
    finally:
        # Graceful cleanup
        await task_manager.cancel_all()
        logger.info("Shutdown complete")

# Run with uvloop if it's installed (Linux/macOS), else the standard loop
if __name__ == "__main__":
    try:
        import uvloop  # Faster event loop implementation
    except ImportError:
        asyncio.run(main())
    else:
        uvloop.run(main())


async def benchmark_pool():
    """Benchmark connection pool performance"""
    import timeit
    
    pool = AsyncConnectionPool(max_concurrent=50)
    devices = [
        DeviceConfig(host=f"router-{i}") for i in range(500)
    ]
    
    start = time.time()
    results = await pool.execute_batch(devices, show_progress=True)
    duration = time.time() - start
    
    metrics = await pool.get_metrics()
    print(f"Processed {len(devices)} devices in {duration:.1f}s")
    print(f"Success rate: {metrics['success_rate']:.1%}")
    print(f"Throughput: {len(devices) / duration:.1f} devices/sec")

