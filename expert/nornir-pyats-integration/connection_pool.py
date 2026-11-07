# connection_pool.py
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import threading
import time
from contextlib import contextmanager
import structlog

logger = structlog.get_logger()


class ConnectionPool:
    """
    Manage persistent connections to network devices.
    
    Features:
    - Connection reuse
    - Automatic cleanup of stale connections
    - Thread-safe operations
    - Connection health monitoring
    """
    
    def __init__(self, max_idle_time: int = 300, health_check_interval: int = 60):
        self._connections: Dict[str, Any] = {}
        self._connection_times: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        self.max_idle_time = timedelta(seconds=max_idle_time)
        self.health_check_interval = health_check_interval
        
        # Start background health check
        self._start_health_monitor()
    
    @contextmanager
    def get_connection(self, device_name: str, testbed):
        """
        Get or create a connection to a device.
        
        Usage:
            with pool.get_connection('router1', testbed) as device:
                device.execute('show version')
        """
        device = None
        
        try:
            with self._lock:
                if device_name in self._connections:
                    device = self._connections[device_name]
                    
                    # Check if connection is still alive
                    if not device.is_connected():
                        logger.warning(
                            "connection_dead_reconnecting",
                            device=device_name
                        )
                        device.connect()
                    
                    self._connection_times[device_name] = datetime.now()
                else:
                    # Create new connection
                    device = testbed.devices[device_name]
                    device.connect()
                    
                    self._connections[device_name] = device
                    self._connection_times[device_name] = datetime.now()
                    
                    logger.info("connection_established", device=device_name)
            
            yield device
            
        except Exception as e:
            logger.error(
                "connection_error",
                device=device_name,
                error=str(e)
            )
            # Remove failed connection
            self._remove_connection(device_name)
            raise
    
    def _remove_connection(self, device_name: str):
        """Remove a connection from the pool"""
        with self._lock:
            if device_name in self._connections:
                try:
                    self._connections[device_name].disconnect()
                except:
                    pass
                
                del self._connections[device_name]
                del self._connection_times[device_name]
                
                logger.info("connection_removed", device=device_name)
    
    def _start_health_monitor(self):
        """Background thread to monitor connection health"""
        def monitor():
            while True:
                time.sleep(self.health_check_interval)
                self._cleanup_stale_connections()
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _cleanup_stale_connections(self):
        """Remove connections that have been idle too long"""
        now = datetime.now()
        stale_devices = []
        
        with self._lock:
            for device_name, last_used in self._connection_times.items():
                if now - last_used > self.max_idle_time:
                    stale_devices.append(device_name)
        
        for device_name in stale_devices:
            logger.info("removing_stale_connection", device=device_name)
            self._remove_connection(device_name)
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            for device_name in list(self._connections.keys()):
                self._remove_connection(device_name)


# Integration with OrchestrationEngine
from orchestrator.integration import OrchestrationEngine


class PoolingOrchestrationEngine(OrchestrationEngine):
    """Extended engine with connection pooling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool = ConnectionPool(
            max_idle_time=300,
            health_check_interval=60
        )
    
    def cleanup(self):
        """Cleanup resources"""
        self.connection_pool.close_all()
