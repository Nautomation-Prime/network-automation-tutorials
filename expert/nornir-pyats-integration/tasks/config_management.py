# tasks/config_management.py
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import time
import logging
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_config, netmiko_send_command
from nornir_napalm.plugins.tasks import napalm_configure
import structlog

logger = structlog.get_logger()


def clean_running_config(config: str) -> str:
    """
    Strip the header IOS prints before 'show running-config' output.

    'Building configuration...' and 'Current configuration : N bytes' aren't
    configuration lines; a config replace would reject them.
    """
    return re.sub(
        r"^(Building configuration\.\.\.|Current configuration : \d+ bytes)\s*$\n?",
        "",
        config,
        flags=re.MULTILINE,
    )


class ChangeState(Enum):
    """Change execution states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ChangeRecord:
    """Track all changes for audit and rollback"""
    device: str
    timestamp: datetime
    commands: List[str]
    state: ChangeState
    pre_config: Optional[str] = None
    post_config: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """
    Centralized configuration management with state tracking,
    rollback capability, and comprehensive error handling.
    """
    
    def __init__(self, dry_run: bool = False, max_retries: int = 3):
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.change_history: List[ChangeRecord] = []
        self.active_changes: Dict[str, ChangeRecord] = {}
        
    def safe_config_push(
        self,
        task: Task,
        commands: List[str],
        validation_commands: Optional[List[str]] = None,
        rollback_timeout: int = 300,
        **kwargs
    ) -> Result:
        """
        Execute configuration changes with full state tracking and rollback capability.
        
        Features:
        - Pre/post configuration backup
        - Automatic retry with exponential backoff
        - Validation command execution
        - Rollback on failure
        - Comprehensive error logging
        
        Args:
            task: Nornir task object
            commands: Configuration commands to execute
            validation_commands: Commands to validate the change
            rollback_timeout: Seconds to wait before auto-rollback on validation failure
            
        Returns:
            Nornir Result object with change metadata
        """
        device_name = task.host.name
        start_time = time.time()
        
        # Initialize change record
        change = ChangeRecord(
            device=device_name,
            timestamp=datetime.utcnow(),
            commands=commands,
            state=ChangeState.PENDING,
            metadata={
                'dry_run': self.dry_run,
                'validation_commands': validation_commands,
                'rollback_timeout': rollback_timeout,
            }
        )
        self.active_changes[device_name] = change
        
        try:
            # Step 1: Capture pre-change configuration
            logger.info(
                "capturing_pre_config",
                device=device_name,
                dry_run=self.dry_run
            )
            
            pre_config_result = task.run(
                task=netmiko_send_command,
                command_string="show running-config",
                name=f"{device_name}: Capture pre-change config"
            )
            change.pre_config = pre_config_result[0].result
            
            # Step 2: Execute configuration changes (with retries)
            if self.dry_run:
                logger.info(
                    "dry_run_mode",
                    device=device_name,
                    commands=commands
                )
                change.state = ChangeState.COMPLETED
                return Result(
                    host=task.host,
                    result={'dry_run': True, 'commands': commands},
                    changed=False
                )
            
            change.state = ChangeState.IN_PROGRESS
            config_result = self._execute_with_retry(
                task,
                commands,
                change
            )
            
            # Step 3: Capture post-change configuration
            logger.info(
                "capturing_post_config",
                device=device_name
            )
            
            post_config_result = task.run(
                task=netmiko_send_command,
                command_string="show running-config",
                name=f"{device_name}: Capture post-change config"
            )
            change.post_config = post_config_result[0].result
            
            # Step 4: Execute validation commands
            if validation_commands:
                validation_passed = self._execute_validations(
                    task,
                    validation_commands,
                    change
                )
                
                if not validation_passed:
                    raise ValidationError(
                        f"Validation failed for {device_name}"
                    )
            
            # Step 5: Mark as completed
            change.state = ChangeState.COMPLETED
            change.execution_time = time.time() - start_time
            self.change_history.append(change)
            
            logger.info(
                "config_push_success",
                device=device_name,
                execution_time=change.execution_time,
                retry_count=change.retry_count
            )
            
            return Result(
                host=task.host,
                result={
                    'changed': True,
                    'config_output': config_result[0].result,
                    'change_record': change,
                },
                changed=True
            )
            
        except Exception as e:
            # Handle failure and attempt rollback
            change.state = ChangeState.FAILED
            change.error = str(e)
            change.execution_time = time.time() - start_time
            
            logger.error(
                "config_push_failed",
                device=device_name,
                error=str(e),
                commands=commands,
                retry_count=change.retry_count
            )
            
            # Attempt rollback if we captured pre-config
            if change.pre_config and not self.dry_run:
                self._attempt_rollback(task, change)
            
            self.change_history.append(change)
            
            return Result(
                host=task.host,
                result={'error': str(e), 'change_record': change},
                failed=True,
                exception=e
            )
            
        finally:
            # Clean up active changes
            self.active_changes.pop(device_name, None)
    
    def _execute_with_retry(
        self,
        task: Task,
        commands: List[str],
        change: ChangeRecord
    ) -> Result:
        """Execute commands with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "config_push_attempt",
                    device=task.host.name,
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                
                result = task.run(
                    task=netmiko_send_config,
                    config_commands=commands,
                    name=f"{task.host.name}: Push configuration (attempt {attempt + 1})"
                )
                
                change.retry_count = attempt
                return result
                
            except Exception as e:
                last_exception = e
                change.retry_count = attempt + 1
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    backoff = 2 ** attempt
                    logger.warning(
                        "config_push_retry",
                        device=task.host.name,
                        attempt=attempt + 1,
                        backoff_seconds=backoff,
                        error=str(e)
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        "config_push_max_retries",
                        device=task.host.name,
                        error=str(e)
                    )
        
        # All retries exhausted
        raise last_exception
    
    def _execute_validations(
        self,
        task: Task,
        validation_commands: List[str],
        change: ChangeRecord
    ) -> bool:
        """Execute validation commands and check for expected state"""
        all_passed = True
        
        for cmd in validation_commands:
            try:
                result = task.run(
                    task=netmiko_send_command,
                    command_string=cmd,
                    name=f"{task.host.name}: Validation - {cmd}"
                )
                
                # Store validation output in metadata
                if 'validations' not in change.metadata:
                    change.metadata['validations'] = {}
                change.metadata['validations'][cmd] = result[0].result
                
                logger.info(
                    "validation_executed",
                    device=task.host.name,
                    command=cmd,
                    output_length=len(result[0].result)
                )
                
            except Exception as e:
                logger.error(
                    "validation_failed",
                    device=task.host.name,
                    command=cmd,
                    error=str(e)
                )
                all_passed = False
        
        return all_passed
    
    def _attempt_rollback(self, task: Task, change: ChangeRecord):
        """Attempt to rollback changes using pre-change configuration"""
        device_name = task.host.name
        
        try:
            logger.warning(
                "attempting_rollback",
                device=device_name,
                original_error=change.error
            )
            
            # Use NAPALM rollback if available, otherwise manual. NAPALM
            # needs its own platform name ('ios'): set it in the host's
            # connection_options, as the Step 1 inventory does
            try:
                rollback_result = task.run(
                    task=napalm_configure,
                    configuration=clean_running_config(change.pre_config),
                    replace=True,
                    name=f"{device_name}: Rollback configuration"
                )
                
                change.state = ChangeState.ROLLED_BACK
                logger.info(
                    "rollback_success",
                    device=device_name
                )
                
            except Exception as napalm_error:
                # NAPALM failed, try manual revert
                logger.warning(
                    "napalm_rollback_failed",
                    device=device_name,
                    error=str(napalm_error)
                )
                # Manual rollback strategy here
                
        except Exception as e:
            logger.critical(
                "rollback_failed",
                device=device_name,
                error=str(e),
                original_error=change.error
            )
            change.metadata['rollback_error'] = str(e)


class ValidationError(Exception):
    """Raised when post-change validation fails"""
    pass


# Advanced Usage Example with Circuit Breaker Pattern
class CircuitBreaker:
    """Prevent cascading failures in large-scale automation"""
    
    def __init__(self, failure_threshold: float = 0.2, window_size: int = 10):
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.results = []
        self.is_open = False
        
    def record(self, success: bool) -> bool:
        """
        Record a result and check circuit status. Returns True if open.

        It doesn't raise: callers check is_open before each device, so the
        deployment stops cleanly (and its report still gets written).
        """
        self.results.append(success)
        if len(self.results) > self.window_size:
            self.results.pop(0)

        # Calculate failure rate
        if len(self.results) >= self.window_size and not self.is_open:
            failure_rate = 1 - (sum(self.results) / len(self.results))

            if failure_rate > self.failure_threshold:
                self.is_open = True
                logger.critical(
                    "circuit_breaker_opened",
                    failure_rate=failure_rate,
                    threshold=self.failure_threshold
                )

        return self.is_open
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.results = []
        self.is_open = False
        logger.info("circuit_breaker_reset")


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker prevents execution"""
    pass


# Example: Orchestrated deployment with circuit breaker
def orchestrated_config_deployment(
    nr,
    commands: List[str],
    validation_commands: List[str],
    dry_run: bool = False
):
    """
    Deploy configuration changes with circuit breaker protection
    """
    config_mgr = ConfigurationManager(dry_run=dry_run, max_retries=3)
    circuit_breaker = CircuitBreaker(failure_threshold=0.2, window_size=10)
    
    results = {}
    
    for host_name, host in nr.inventory.hosts.items():
        # Check circuit breaker
        if circuit_breaker.is_open:
            logger.error(
                "deployment_halted",
                reason="circuit_breaker_open",
                completed=len(results),
                total=len(nr.inventory.hosts)
            )
            break
        
        # Execute change on single host
        result = nr.filter(name=host_name).run(
            task=config_mgr.safe_config_push,
            commands=commands,
            validation_commands=validation_commands
        )
        
        # Record success/failure for circuit breaker. Judge by the task's
        # own result ([0]): the MultiResult also keeps every failed retry
        # attempt, so .failed on the whole host is True even after a
        # retry succeeded
        success = not result[host_name][0].failed
        circuit_breaker.record(success)
        
        results[host_name] = result[host_name]
        
        # Brief pause between devices for safety
        time.sleep(0.5)
    
    return results, config_mgr
