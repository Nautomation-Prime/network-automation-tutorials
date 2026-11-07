# orchestrator/integration.py
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import structlog
from nornir import InitNornir
from nornir.core.task import Task, Result

from nornir_napalm.plugins.tasks import napalm_configure

# Import our previous modules
from tasks.config_management import (
    ConfigurationManager, ChangeRecord, CircuitBreaker, clean_running_config
)
from validation.pyats_validator import PyATSValidator, ValidationResult

logger = structlog.get_logger()


class DeploymentPhase(Enum):
    """Phases of deployment workflow"""
    INIT = "initialization"
    PRE_CHECK = "pre_check"
    BACKUP = "backup"
    EXECUTION = "execution"
    VALIDATION = "validation"
    ROLLBACK = "rollback"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class DeploymentRecord:
    """Complete record of a deployment workflow"""
    deployment_id: str
    timestamp: datetime
    phase: DeploymentPhase
    devices: List[str]
    commands: List[str]
    dry_run: bool
    change_records: Dict[str, ChangeRecord] = field(default_factory=dict)
    validation_results: Dict[str, List[ValidationResult]] = field(default_factory=dict)
    rollback_devices: List[str] = field(default_factory=list)
    errors: Dict[str, List[str]] = field(default_factory=dict)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'deployment_id': self.deployment_id,
            'timestamp': self.timestamp.isoformat(),
            'phase': self.phase.value,
            'devices': self.devices,
            'commands': self.commands,
            'dry_run': self.dry_run,
            'change_records': {
                k: {
                    'device': v.device,
                    'state': v.state.value,
                    'execution_time': v.execution_time,
                    'retry_count': v.retry_count,
                    'error': v.error,
                }
                for k, v in self.change_records.items()
            },
            'validation_results': {
                k: [
                    {
                        'feature': vr.feature,
                        'passed': vr.passed,
                        'errors': vr.errors,
                    }
                    for vr in vr_list
                ]
                for k, vr_list in self.validation_results.items()
            },
            'rollback_devices': self.rollback_devices,
            'errors': self.errors,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
        }


class OrchestrationEngine:
    """
    Complete orchestration engine integrating Nornir and PyATS.
    
    Features:
    - Pre-flight validation
    - Parallel execution with throttling
    - Post-flight validation
    - Automatic rollback on failure
    - Comprehensive reporting
    - Circuit breaker protection
    - Dry-run mode
    """
    
    def __init__(
        self,
        nornir_config: str,
        pyats_testbed: str,
        state_dir: str = './states',
        report_dir: str = './reports',
        dry_run: bool = False,
        max_retries: int = 3,
        circuit_breaker_threshold: float = 0.20,
    ):
        self.nr = InitNornir(config_file=nornir_config)
        self.validator = PyATSValidator(
            testbed_file=pyats_testbed,
            state_dir=state_dir
        )
        self.config_mgr = ConfigurationManager(
            dry_run=dry_run,
            max_retries=max_retries
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            window_size=10
        )
        
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.deployment_history: List[DeploymentRecord] = []
        
    def deploy_with_validation(
        self,
        devices: Optional[List[str]] = None,
        commands: List[str] = None,
        validation_features: List[str] = ['interface', 'bgp'],
        custom_validations: Optional[List[Callable]] = None,
        rollback_on_failure: bool = True,
        parallel: bool = True,
        max_workers: int = 5,
    ) -> DeploymentRecord:
        """
        Execute complete deployment workflow with validation.
        
        Workflow:
        1. Pre-flight validation (ensure devices are reachable and stable)
        2. Capture pre-change state
        3. Execute configuration changes
        4. Capture post-change state
        5. Validate changes
        6. Rollback if validation fails
        7. Generate comprehensive report
        
        Args:
            devices: List of device names (None = all devices)
            commands: Configuration commands to execute
            validation_features: Genie features to validate
            custom_validations: Custom validation functions
            rollback_on_failure: Auto-rollback on validation failure
            parallel: Execute in parallel
            max_workers: Max parallel workers
            
        Returns:
            DeploymentRecord with complete execution details
        """
        deployment_id = f"deploy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        
        # Filter devices
        if devices:
            nr_filtered = self.nr.filter(filter_func=lambda h: h.name in devices)
        else:
            nr_filtered = self.nr
            devices = list(nr_filtered.inventory.hosts.keys())
        
        # Initialize deployment record
        deployment = DeploymentRecord(
            deployment_id=deployment_id,
            timestamp=datetime.utcnow(),
            phase=DeploymentPhase.INIT,
            devices=devices,
            commands=commands,
            dry_run=self.config_mgr.dry_run
        )
        
        logger.info(
            "deployment_started",
            deployment_id=deployment_id,
            devices=len(devices),
            commands=len(commands),
            dry_run=self.config_mgr.dry_run
        )
        
        try:
            # Phase 1: Pre-flight validation
            deployment.phase = DeploymentPhase.PRE_CHECK
            logger.info("preflight_validation", deployment_id=deployment_id)
            
            preflight_passed = self._preflight_validation(
                devices,
                validation_features,
                deployment
            )
            
            if not preflight_passed:
                raise PreflightValidationError(
                    "Pre-flight validation failed. Aborting deployment."
                )
            
            # Phase 2: Capture pre-change state
            deployment.phase = DeploymentPhase.BACKUP
            logger.info("capturing_pre_state", deployment_id=deployment_id)
            
            pre_states = self._capture_pre_states(
                devices,
                validation_features,
                deployment
            )
            
            # Phase 3: Execute configuration changes
            deployment.phase = DeploymentPhase.EXECUTION
            logger.info("executing_changes", deployment_id=deployment_id)
            
            if parallel:
                execution_results = self._execute_parallel(
                    nr_filtered,
                    commands,
                    deployment,
                    max_workers
                )
            else:
                execution_results = self._execute_serial(
                    nr_filtered,
                    commands,
                    deployment
                )
            
            # Phase 4: Post-flight validation
            deployment.phase = DeploymentPhase.VALIDATION
            logger.info("postflight_validation", deployment_id=deployment_id)
            
            validation_passed = self._postflight_validation(
                devices,
                validation_features,
                pre_states,
                deployment,
                custom_validations
            )
            
            # Phase 5: Rollback if needed
            if not validation_passed and rollback_on_failure:
                deployment.phase = DeploymentPhase.ROLLBACK
                logger.warning(
                    "initiating_rollback",
                    deployment_id=deployment_id,
                    failed_devices=len([
                        d for d, v in deployment.validation_results.items()
                        if not all(vr.passed for vr in v)
                    ])
                )
                
                self._execute_rollback(deployment)
            
            # Phase 6: Complete
            deployment.phase = DeploymentPhase.COMPLETE
            deployment.execution_time = time.time() - start_time
            
            logger.info(
                "deployment_complete",
                deployment_id=deployment_id,
                execution_time=deployment.execution_time,
                success=validation_passed
            )
            
        except Exception as e:
            deployment.phase = DeploymentPhase.FAILED
            deployment.execution_time = time.time() - start_time
            
            logger.error(
                "deployment_failed",
                deployment_id=deployment_id,
                error=str(e),
                phase=deployment.phase.value
            )
            
            # Add error to deployment record
            deployment.errors['orchestration'] = [str(e)]
        
        finally:
            # Always generate report
            self._generate_report(deployment)
            self.deployment_history.append(deployment)
        
        return deployment
    
    def _preflight_validation(
        self,
        devices: List[str],
        features: List[str],
        deployment: DeploymentRecord
    ) -> bool:
        """
        Execute pre-flight checks to ensure devices are ready.
        
        Checks:
        - Device connectivity
        - Stable state (no flapping interfaces, stable BGP)
        - No active alarms/alerts
        """
        all_passed = True
        
        for device in devices:
            try:
                # Test connectivity
                self.validator.connect_device(device)
                
                # Validate stable state for each feature
                for feature in features:
                    if feature == 'interface':
                        # Check for interface flapping
                        result = self.validator.parse_command(
                            device,
                            'show interface status'
                        )
                        # Custom logic to detect flapping would go here
                        
                    elif feature == 'bgp':
                        # Validate all BGP sessions are stable
                        result = self.validator.validate_bgp_neighbors(
                            device,
                            expected_state='established'
                        )
                        
                        if not result.passed:
                            all_passed = False
                            if device not in deployment.errors:
                                deployment.errors[device] = []
                            deployment.errors[device].extend(result.errors)
                
                logger.info(
                    "preflight_passed",
                    device=device,
                    features=features
                )
                
            except Exception as e:
                all_passed = False
                logger.error(
                    "preflight_failed",
                    device=device,
                    error=str(e)
                )
                if device not in deployment.errors:
                    deployment.errors[device] = []
                deployment.errors[device].append(f"Pre-flight: {str(e)}")
        
        return all_passed
    
    def _capture_pre_states(
        self,
        devices: List[str],
        features: List[str],
        deployment: DeploymentRecord
    ) -> Dict[str, Dict[str, Dict]]:
        """Capture pre-change state for all devices"""
        pre_states = {}
        
        for device in devices:
            try:
                device_states = self.validator.capture_pre_state(device, features)
                pre_states[device] = device_states
                
                logger.info(
                    "pre_state_captured",
                    device=device,
                    features=list(device_states.keys())
                )
                
            except Exception as e:
                logger.error(
                    "pre_state_capture_failed",
                    device=device,
                    error=str(e)
                )
                if device not in deployment.errors:
                    deployment.errors[device] = []
                deployment.errors[device].append(f"Pre-state: {str(e)}")
        
        return pre_states
    
    def _execute_serial(
        self,
        nr_filtered,
        commands: List[str],
        deployment: DeploymentRecord
    ) -> Dict:
        """Execute changes serially with circuit breaker protection"""
        results = {}
        
        for host_name in nr_filtered.inventory.hosts.keys():
            # Check circuit breaker
            if self.circuit_breaker.is_open:
                logger.error(
                    "circuit_breaker_halted_deployment",
                    completed=len(results),
                    total=len(nr_filtered.inventory.hosts)
                )
                break
            
            # Execute on single device
            result = nr_filtered.filter(name=host_name).run(
                task=self.config_mgr.safe_config_push,
                commands=commands,
            )
            
            # Record result (the task's own result: see Step 2)
            success = not result[host_name][0].failed
            self.circuit_breaker.record(success)
            results[host_name] = result[host_name]
            
            # Store change record
            if hasattr(result[host_name][0].result, 'get'):
                change_record = result[host_name][0].result.get('change_record')
                if change_record:
                    deployment.change_records[host_name] = change_record
            
            # Brief pause for safety
            time.sleep(0.5)
        
        return results
    
    def _execute_parallel(
        self,
        nr_filtered,
        commands: List[str],
        deployment: DeploymentRecord,
        max_workers: int
    ) -> Dict:
        """Execute changes in parallel with controlled concurrency"""
        results = {}
        
        # Use ThreadPoolExecutor for controlled parallelism
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._execute_single_device,
                    nr_filtered,
                    host_name,
                    commands
                ): host_name
                for host_name in nr_filtered.inventory.hosts.keys()
            }
            
            for future in as_completed(futures):
                host_name = futures[future]
                
                try:
                    result = future.result()
                    results[host_name] = result
                    
                    # Store change record
                    if hasattr(result[0].result, 'get'):
                        change_record = result[0].result.get('change_record')
                        if change_record:
                            deployment.change_records[host_name] = change_record
                    
                    # Record for circuit breaker (the task's own result)
                    success = not result[0].failed
                    self.circuit_breaker.record(success)
                    
                except Exception as e:
                    logger.error(
                        "parallel_execution_failed",
                        device=host_name,
                        error=str(e)
                    )
                    if host_name not in deployment.errors:
                        deployment.errors[host_name] = []
                    deployment.errors[host_name].append(f"Execution: {str(e)}")
        
        return results
    
    def _execute_single_device(self, nr_filtered, host_name: str, commands: List[str]):
        """Execute on a single device (helper for parallel execution)"""
        result = nr_filtered.filter(name=host_name).run(
            task=self.config_mgr.safe_config_push,
            commands=commands,
        )
        return result[host_name]
    
    def _postflight_validation(
        self,
        devices: List[str],
        features: List[str],
        pre_states: Dict[str, Dict[str, Dict]],
        deployment: DeploymentRecord,
        custom_validations: Optional[List[Callable]] = None
    ) -> bool:
        """Execute post-flight validation and diff analysis"""
        all_passed = True
        
        for device in devices:
            device_validations = []
            
            try:
                # Capture post-state
                post_states = self.validator.capture_post_state(device, features)
                
                # Compare states for each feature
                for feature in features:
                    if feature in pre_states.get(device, {}) and feature in post_states:
                        result = self.validator.compare_states(
                            device,
                            feature,
                            pre_states[device][feature],
                            post_states[feature],
                            exclude_keys=['counters', 'in_pkts', 'out_pkts', 'last_clear']
                        )
                        device_validations.append(result)

                        if not result.passed:
                            all_passed = False

                # compare_states() only records diffs, so judge BGP with an
                # explicit rule: every neighbour must be established again
                if 'bgp' in features:
                    bgp_result = self.validator.validate_bgp_neighbors(device)
                    device_validations.append(bgp_result)
                    if not bgp_result.passed:
                        all_passed = False

                # Execute custom validations
                if custom_validations:
                    for validation_func in custom_validations:
                        try:
                            custom_result = validation_func(
                                self.validator,
                                device,
                                pre_states.get(device, {}),
                                post_states
                            )
                            device_validations.append(custom_result)
                            
                            if not custom_result.passed:
                                all_passed = False
                                
                        except Exception as e:
                            logger.error(
                                "custom_validation_error",
                                device=device,
                                error=str(e)
                            )
                
                deployment.validation_results[device] = device_validations
                
                logger.info(
                    "postflight_complete",
                    device=device,
                    validations=len(device_validations),
                    passed=all(v.passed for v in device_validations)
                )
                
            except Exception as e:
                all_passed = False
                logger.error(
                    "postflight_failed",
                    device=device,
                    error=str(e)
                )
                if device not in deployment.errors:
                    deployment.errors[device] = []
                deployment.errors[device].append(f"Post-flight: {str(e)}")
        
        return all_passed
    
    def _execute_rollback(self, deployment: DeploymentRecord):
        """Execute rollback for failed devices"""
        # Identify devices that need rollback
        failed_devices = [
            device for device, validations in deployment.validation_results.items()
            if not all(v.passed for v in validations)
        ]
        
        for device in failed_devices:
            change_record = deployment.change_records.get(device)
            
            if change_record and change_record.pre_config:
                try:
                    logger.info("rolling_back_device", device=device)

                    # Replace the running config with the pre-change copy
                    result = self.nr.filter(name=device).run(
                        task=napalm_configure,
                        configuration=clean_running_config(change_record.pre_config),
                        replace=True,
                        name=f"{device}: Roll back to pre-change config",
                        on_failed=True,  # the host may have failed earlier
                    )
                    if result[device][0].failed:
                        raise RuntimeError(
                            result[device][0].exception or result[device][0].result
                        )

                    # Only record the device once the rollback really happened
                    deployment.rollback_devices.append(device)
                    
                    logger.info("rollback_complete", device=device)
                    
                except Exception as e:
                    logger.critical(
                        "rollback_failed",
                        device=device,
                        error=str(e)
                    )
                    if device not in deployment.errors:
                        deployment.errors[device] = []
                    deployment.errors[device].append(f"Rollback: {str(e)}")
    
    def _generate_report(self, deployment: DeploymentRecord):
        """Generate comprehensive deployment report"""
        report_file = self.report_dir / f"{deployment.deployment_id}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(deployment.to_dict(), f, indent=2)
            
            logger.info(
                "report_generated",
                deployment_id=deployment.deployment_id,
                report_file=str(report_file)
            )
            
            # Also generate human-readable summary
            self._generate_summary_report(deployment)
            
        except Exception as e:
            logger.error(
                "report_generation_failed",
                deployment_id=deployment.deployment_id,
                error=str(e)
            )
    
    def _generate_summary_report(self, deployment: DeploymentRecord):
        """Generate human-readable summary"""
        summary_file = self.report_dir / f"{deployment.deployment_id}_summary.txt"
        
        total_devices = len(deployment.devices)
        successful_changes = sum(
            1 for cr in deployment.change_records.values()
            if cr.state.value == 'completed'
        )
        failed_changes = sum(
            1 for cr in deployment.change_records.values()
            if cr.state.value == 'failed'
        )
        rolled_back = len(deployment.rollback_devices)
        
        summary = f"""
Deployment Summary: {deployment.deployment_id}
{'=' * 70}

Timestamp: {deployment.timestamp.isoformat()}
Phase: {deployment.phase.value}
Dry Run: {deployment.dry_run}
Execution Time: {deployment.execution_time:.2f}s

Devices:
  Total: {total_devices}
  Successful: {successful_changes}
  Failed: {failed_changes}
  Rolled Back: {rolled_back}

Commands Executed:
{chr(10).join(f'  - {cmd}' for cmd in deployment.commands)}

Validation Results:
"""
        
        for device, validations in deployment.validation_results.items():
            passed = all(v.passed for v in validations)
            summary += f"\n  {device}: {'✓ PASSED' if passed else '✗ FAILED'}"
            
            if not passed:
                for v in validations:
                    if not v.passed:
                        summary += f"\n    - {v.feature}: {', '.join(v.errors)}"
        
        if deployment.errors:
            summary += "\n\nErrors:"
            for device, errors in deployment.errors.items():
                summary += f"\n  {device}:"
                for error in errors:
                    summary += f"\n    - {error}"
        
        summary += f"\n\n{'=' * 70}\n"
        
        try:
            with open(summary_file, 'w') as f:
                f.write(summary)
            
            logger.info(
                "summary_generated",
                deployment_id=deployment.deployment_id,
                summary_file=str(summary_file)
            )
            
        except Exception as e:
            logger.error(
                "summary_generation_failed",
                error=str(e)
            )


class PreflightValidationError(Exception):
    """Raised when pre-flight validation fails"""
    pass


# Complete Usage Example
def main():
    """Complete end-to-end deployment example"""
    
    # Initialize orchestration engine
    engine = OrchestrationEngine(
        nornir_config='config.yaml',
        pyats_testbed='testbed.yaml',
        dry_run=False,  # Set to True for testing
        max_retries=3,
        circuit_breaker_threshold=0.20
    )
    
    # Define deployment
    devices = ['router1', 'router2', 'router3']
    commands = [
        'interface GigabitEthernet0/1',
        'description Managed by Automation - Updated',
        'no shutdown',
    ]
    validation_features = ['interface', 'bgp']
    
    # Execute deployment with full orchestration
    deployment = engine.deploy_with_validation(
        devices=devices,
        commands=commands,
        validation_features=validation_features,
        rollback_on_failure=True,
        parallel=True,
        max_workers=5
    )
    
    # Review results
    print(f"\nDeployment ID: {deployment.deployment_id}")
    print(f"Phase: {deployment.phase.value}")
    print(f"Execution Time: {deployment.execution_time:.2f}s")
    print(f"Successful: {len([cr for cr in deployment.change_records.values() if cr.state.value == 'completed'])}/{len(devices)}")
    
    if deployment.errors:
        print("\nErrors encountered:")
        for device, errors in deployment.errors.items():
            print(f"  {device}: {errors}")


if __name__ == '__main__':
    main()
