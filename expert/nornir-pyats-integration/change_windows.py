# change_windows.py
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class ChangeWindow:
    """Define an approved change window"""
    name: str
    day_of_week: int  # 0 = Monday, 6 = Sunday
    start_time: time
    end_time: time
    allowed_device_groups: List[str]
    
    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Check if change window is currently active"""
        now = now or datetime.now()
        current_time = now.time()

        if self.start_time <= self.end_time:
            # Window doesn't cross midnight: one day, one time range
            return (now.weekday() == self.day_of_week
                    and self.start_time <= current_time <= self.end_time)

        # Window crosses midnight (e.g. Fri 22:00-02:00): it's open late on
        # its own day, and early on the FOLLOWING day
        next_day = (self.day_of_week + 1) % 7
        return ((now.weekday() == self.day_of_week and current_time >= self.start_time)
                or (now.weekday() == next_day and current_time <= self.end_time))


class ChangeWindowEnforcer:
    """Enforce change window policies"""
    
    def __init__(self, windows: List[ChangeWindow]):
        self.windows = windows
    
    def can_deploy(
        self,
        device_group: str,
        now: Optional[datetime] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if deployment is allowed for device group.
        
        Returns:
            (allowed, reason)
        """
        now = now or datetime.now()
        
        for window in self.windows:
            if device_group in window.allowed_device_groups:
                if window.is_active(now):
                    return True, f"Active window: {window.name}"
        
        # Find next available window
        next_window = self._find_next_window(device_group, now)
        
        if next_window:
            return False, f"Next window: {next_window[0].name} in {next_window[1]}"
        else:
            return False, "No change window available for this device group"
    
    def _find_next_window(
        self,
        device_group: str,
        now: datetime
    ) -> Optional[tuple[ChangeWindow, timedelta]]:
        """Find the next available change window"""
        next_window = None
        min_delta = None
        
        for window in self.windows:
            if device_group not in window.allowed_device_groups:
                continue
            
            # Calculate next occurrence
            days_ahead = (window.day_of_week - now.weekday()) % 7
            if days_ahead == 0:
                # Same day - check if window is in the future
                window_datetime = datetime.combine(now.date(), window.start_time)
                if window_datetime <= now:
                    days_ahead = 7  # Next week
            
            next_occurrence = now + timedelta(days=days_ahead)
            next_occurrence = datetime.combine(
                next_occurrence.date(),
                window.start_time
            )
            
            delta = next_occurrence - now
            
            if min_delta is None or delta < min_delta:
                min_delta = delta
                next_window = window
        
        if next_window and min_delta:
            return next_window, min_delta
        
        return None


# Integration Example
from orchestrator.integration import OrchestrationEngine


class WindowedOrchestrationEngine(OrchestrationEngine):
    """Orchestration engine with change window enforcement"""
    
    def __init__(self, *args, change_windows: List[ChangeWindow], **kwargs):
        super().__init__(*args, **kwargs)
        self.window_enforcer = ChangeWindowEnforcer(change_windows)
    
    def deploy_with_validation(self, devices: Optional[List[str]] = None, **kwargs):
        """Override to check change windows"""
        
        # Group devices by their device group
        device_groups = self._get_device_groups(devices)
        
        # Check each group
        allowed_devices = []
        blocked_devices = []
        
        for group, group_devices in device_groups.items():
            can_deploy, reason = self.window_enforcer.can_deploy(group)
            
            if can_deploy:
                logger.info(
                    "change_window_active",
                    group=group,
                    devices=len(group_devices),
                    reason=reason
                )
                allowed_devices.extend(group_devices)
            else:
                logger.warning(
                    "change_window_blocked",
                    group=group,
                    devices=len(group_devices),
                    reason=reason
                )
                blocked_devices.extend(group_devices)
        
        if not allowed_devices:
            raise ChangeWindowViolation(
                f"No devices in active change window. Blocked: {len(blocked_devices)}"
            )
        
        # Deploy only to allowed devices
        return super().deploy_with_validation(devices=allowed_devices, **kwargs)
    
    def _get_device_groups(self, devices: List[str]) -> Dict[str, List[str]]:
        """Get device group mapping from inventory"""
        device_groups = {}
        
        for device in devices:
            host = self.nr.inventory.hosts[device]
            # Assume devices have a 'device_group' data attribute
            group = host.data.get('device_group', 'default')
            
            if group not in device_groups:
                device_groups[group] = []
            device_groups[group].append(device)
        
        return device_groups


class ChangeWindowViolation(Exception):
    """Raised when deployment attempted outside change window"""
    pass


# Usage Example
def setup_change_windows():
    """Configure production change windows"""
    
    windows = [
        # Tuesday maintenance window for core devices
        ChangeWindow(
            name="Core Maintenance",
            day_of_week=1,  # Tuesday
            start_time=time(2, 0),  # 2:00 AM
            end_time=time(6, 0),  # 6:00 AM
            allowed_device_groups=['core', 'spine']
        ),
        # Friday evening for access devices
        ChangeWindow(
            name="Access Maintenance",
            day_of_week=4,  # Friday
            start_time=time(20, 0),  # 8:00 PM
            end_time=time(23, 59),  # 11:59 PM
            allowed_device_groups=['access', 'edge']
        ),
        # Sunday morning for all non-production
        ChangeWindow(
            name="Non-Prod Anytime",
            day_of_week=6,  # Sunday
            start_time=time(0, 0),
            end_time=time(23, 59),
            allowed_device_groups=['dev', 'test', 'lab']
        ),
    ]
    
    engine = WindowedOrchestrationEngine(
        nornir_config='config.yaml',
        pyats_testbed='testbed.yaml',
        change_windows=windows
    )
    
    return engine
