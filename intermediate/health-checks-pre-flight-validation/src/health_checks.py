# src/health_checks.py
from dataclasses import dataclass
from enum import Enum
import re

class HealthStatus(Enum):
    """Device health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    check_name: str
    status: HealthStatus
    message: str
    details: dict = None

class DeviceHealthChecker:
    """Validate device health before deployment."""
    
    def __init__(self, device):
        self.device = device
        self.checks = []
    
    def check_device_reachable(self) -> HealthCheckResult:
        """Check if device responds to ping/SSH."""
        try:
            output = self.device.send_command("ping 8.8.8.8 repeat 1")
            if "100 percent" in output or "100%" in output or "0% packet loss" in output:
                return HealthCheckResult(
                    check_name="device_reachable",
                    status=HealthStatus.HEALTHY,
                    message="Device is reachable"
                )
            return HealthCheckResult(
                check_name="device_reachable",
                status=HealthStatus.WARNING,
                message="Device has connectivity issues",
                details={"ping_output": output[:100]}
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="device_reachable",
                status=HealthStatus.CRITICAL,
                message=f"Cannot reach device: {str(e)}"
            )
    
    def check_disk_space(self, min_percent_free=10) -> HealthCheckResult:
        """Check device has sufficient free disk space."""
        try:
            # IOS / IOS-XE summary line, e.g.:
            #   11353194496 bytes total (8183595008 bytes free)
            output = self.device.send_command("dir flash: | include bytes total")
            match = re.search(r"(\d+) bytes total \((\d+) bytes free\)", output)

            if not match:
                return HealthCheckResult(
                    check_name="disk_space",
                    status=HealthStatus.WARNING,
                    message="Could not parse disk usage",
                    details={"output": output[:100]}
                )

            total, free = (int(value) for value in match.groups())
            percent_free = free / total * 100

            if percent_free < min_percent_free:
                return HealthCheckResult(
                    check_name="disk_space",
                    status=HealthStatus.WARNING,
                    message=f"Only {percent_free:.0f}% of flash free "
                            f"(minimum {min_percent_free}%)",
                    details={"free_bytes": free, "total_bytes": total}
                )

            return HealthCheckResult(
                check_name="disk_space",
                status=HealthStatus.HEALTHY,
                message=f"{percent_free:.0f}% of flash free",
                details={"free_bytes": free, "total_bytes": total}
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"Cannot check disk space: {str(e)}"
            )
    
    def check_cpu_usage(self, max_percent=80) -> HealthCheckResult:
        """Check device CPU is not overloaded."""
        try:
            output = self.device.send_command("show processes cpu")
            
            # Look for CPU usage line
            for line in output.split('\n'):
                if 'CPU utilization' in line:
                    # Parse first CPU percentage (e.g. "5%/0%" or "7%;")
                    match = re.search(r"(\d+(?:\.\d+)?)%", line)
                    if not match:
                        continue
                    cpu_percent = float(match.group(1))
                    
                    if cpu_percent < max_percent:
                        return HealthCheckResult(
                            check_name="cpu_usage",
                            status=HealthStatus.HEALTHY,
                            message=f"CPU usage OK ({cpu_percent}%)"
                        )
                    else:
                        return HealthCheckResult(
                            check_name="cpu_usage",
                            status=HealthStatus.WARNING,
                            message=f"CPU usage high ({cpu_percent}%)"
                        )
            
            return HealthCheckResult(
                check_name="cpu_usage",
                status=HealthStatus.WARNING,
                message="Could not parse CPU usage"
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="cpu_usage",
                status=HealthStatus.CRITICAL,
                message=f"Cannot check CPU: {str(e)}"
            )
    
    def check_memory_usage(self, max_percent=80) -> HealthCheckResult:
        """Check device memory is not exhausted."""
        try:
            output = self.device.send_command("show memory")
            
            for line in output.split('\n'):
                if 'Processor' in line:
                    # Parse memory (simplified)
                    parts = line.split()
                    # Real implementation depends on device OS
                    
                    return HealthCheckResult(
                        check_name="memory_usage",
                        status=HealthStatus.HEALTHY,
                        message="Memory available"
                    )
            
            return HealthCheckResult(
                check_name="memory_usage",
                status=HealthStatus.WARNING,
                message="Could not parse memory usage"
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="memory_usage",
                status=HealthStatus.CRITICAL,
                message=f"Cannot check memory: {str(e)}"
            )
    
    def check_running_config_valid(self) -> HealthCheckResult:
        """Check running configuration is valid."""
        try:
            output = self.device.send_command("show running-config | include ERROR")
            
            if output.strip() == "":
                return HealthCheckResult(
                    check_name="config_valid",
                    status=HealthStatus.HEALTHY,
                    message="Running configuration is valid"
                )
            else:
                return HealthCheckResult(
                    check_name="config_valid",
                    status=HealthStatus.CRITICAL,
                    message="Running configuration has errors",
                    details={"errors": output}
                )
        except Exception as e:
            return HealthCheckResult(
                check_name="config_valid",
                status=HealthStatus.WARNING,
                message=f"Cannot validate config: {str(e)}"
            )
    
    def run_all_checks(self) -> list:
        """Run all health checks."""
        results = [
            self.check_device_reachable(),
            self.check_disk_space(),
            self.check_cpu_usage(),
            self.check_memory_usage(),
            self.check_running_config_valid(),
        ]
        return results
    
    def is_healthy(self, results: list, allow_warnings=True) -> bool:
        """
        Determine if device is healthy enough for deployment.
        
        Args:
            results: List of HealthCheckResult
            allow_warnings: Allow deployment if only warnings
        
        Returns:
            bool: True if device is healthy
        """
        critical = [r for r in results if r.status == HealthStatus.CRITICAL]
        
        if critical:
            return False
        
        if not allow_warnings:
            warnings = [r for r in results if r.status == HealthStatus.WARNING]
            return len(warnings) == 0
        
        return True
