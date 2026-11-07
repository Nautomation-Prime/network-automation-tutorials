# validation/pyats_validator.py
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import logging
from pyats.topology import loader
from genie.utils.diff import Diff
import structlog

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    """Structured validation result"""
    device: str
    feature: str
    timestamp: datetime
    passed: bool
    pre_state: Optional[Dict] = None
    post_state: Optional[Dict] = None
    diff: Optional[Dict] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PyATSValidator:
    """
    Comprehensive validation engine using PyATS Genie.
    
    Features:
    - Structured state capture using learn features
    - Intelligent diff analysis
    - Custom validation rules
    - Rollback decision logic
    """
    
    def __init__(self, testbed_file: str, state_dir: str = './states'):
        self.testbed = loader.load(testbed_file)
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.validation_history: List[ValidationResult] = []
        
    def connect_device(self, device_name: str):
        """Establish connection to device"""
        device = self.testbed.devices[device_name]
        
        try:
            if not device.is_connected():
                logger.info("connecting_to_device", device=device_name)
                device.connect(
                    learn_hostname=True,
                    init_exec_commands=[],
                    init_config_commands=[],
                    log_stdout=False
                )
                logger.info("device_connected", device=device_name)
            return device
        except Exception as e:
            logger.error("connection_failed", device=device_name, error=str(e))
            raise
    
    def learn_feature(
        self,
        device_name: str,
        feature: str,
        save_snapshot: bool = True
    ) -> Dict:
        """
        Learn a complete feature using Genie ops models.
        
        Supported features: interface, bgp, ospf, vrf, routing, platform, etc.
        
        Args:
            device_name: Device to learn from
            feature: Feature name (e.g., 'interface', 'bgp', 'ospf')
            save_snapshot: Save snapshot to disk for comparison
            
        Returns:
            Dictionary with complete feature state
        """
        device = self.connect_device(device_name)
        
        try:
            logger.info(
                "learning_feature",
                device=device_name,
                feature=feature
            )
            
            # device.learn() picks the ops model for the device's OS. (The
            # generic classes in genie.libs.ops.<feature> are base classes:
            # calling .learn() on them raises NotImplementedError.)
            ops_obj = device.learn(feature)
            
            # Convert to dictionary
            state = ops_obj.info
            
            if save_snapshot:
                self._save_snapshot(device_name, feature, state)
            
            logger.info(
                "feature_learned",
                device=device_name,
                feature=feature,
                keys_count=len(state.keys()) if state else 0
            )
            
            return state
            
        except Exception as e:
            logger.error(
                "learn_feature_failed",
                device=device_name,
                feature=feature,
                error=str(e)
            )
            raise
    
    def parse_command(
        self,
        device_name: str,
        command: str,
        save_snapshot: bool = False
    ) -> Dict:
        """
        Parse command output using Genie parsers.
        
        Args:
            device_name: Device to execute command on
            command: CLI command to parse
            save_snapshot: Save parsed output
            
        Returns:
            Parsed output as dictionary
        """
        device = self.connect_device(device_name)
        
        try:
            logger.info(
                "parsing_command",
                device=device_name,
                command=command
            )
            
            # Execute and parse
            parsed_output = device.parse(command)
            
            if save_snapshot:
                snapshot_name = f"{command.replace(' ', '_')}"
                self._save_snapshot(device_name, snapshot_name, parsed_output)
            
            logger.info(
                "command_parsed",
                device=device_name,
                command=command,
                output_size=len(str(parsed_output))
            )
            
            return parsed_output
            
        except Exception as e:
            logger.error(
                "parse_command_failed",
                device=device_name,
                command=command,
                error=str(e)
            )
            # Return raw output if parsing fails
            raw_output = device.execute(command)
            return {'raw_output': raw_output, 'parse_failed': True}
    
    def capture_pre_state(
        self,
        device_name: str,
        features: List[str]
    ) -> Dict[str, Dict]:
        """
        Capture pre-change state for multiple features.
        
        Returns:
            Dictionary mapping feature names to their state
        """
        pre_states = {}
        
        for feature in features:
            try:
                state = self.learn_feature(
                    device_name,
                    feature,
                    save_snapshot=True
                )
                pre_states[feature] = state
                
            except Exception as e:
                logger.error(
                    "pre_state_capture_failed",
                    device=device_name,
                    feature=feature,
                    error=str(e)
                )
                pre_states[feature] = {'error': str(e)}
        
        return pre_states
    
    def capture_post_state(
        self,
        device_name: str,
        features: List[str]
    ) -> Dict[str, Dict]:
        """
        Capture post-change state for multiple features.
        
        Returns:
            Dictionary mapping feature names to their state
        """
        return self.capture_pre_state(device_name, features)
    
    def compare_states(
        self,
        device_name: str,
        feature: str,
        pre_state: Dict,
        post_state: Dict,
        exclude_keys: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Compare pre and post states using Genie diff engine.
        
        Args:
            device_name: Device name
            feature: Feature being compared
            pre_state: State before change
            post_state: State after change
            exclude_keys: Keys to exclude from diff (e.g., timestamps, counters)
            
        Returns:
            ValidationResult with diff analysis
        """
        timestamp = datetime.utcnow()
        exclude_keys = exclude_keys or []
        
        try:
            # Use Genie's diff engine
            diff = Diff(pre_state, post_state, exclude=exclude_keys)
            diff.findDiff()
            
            diff_output = str(diff)
            has_diff = len(diff_output) > 0
            
            # This records WHAT changed; it doesn't judge it. 'passed' only
            # means the comparison ran. Pass/fail comes from rules such as
            # validate_bgp_neighbors() or your custom validations
            validation = ValidationResult(
                device=device_name,
                feature=feature,
                timestamp=timestamp,
                passed=True,
                pre_state=pre_state,
                post_state=post_state,
                diff={'diff_text': diff_output, 'has_changes': has_diff}
            )
            
            logger.info(
                "state_comparison_complete",
                device=device_name,
                feature=feature,
                has_diff=has_diff,
                diff_length=len(diff_output)
            )
            
            self.validation_history.append(validation)
            return validation
            
        except Exception as e:
            logger.error(
                "state_comparison_failed",
                device=device_name,
                feature=feature,
                error=str(e)
            )
            
            validation = ValidationResult(
                device=device_name,
                feature=feature,
                timestamp=timestamp,
                passed=False,
                errors=[str(e)]
            )
            self.validation_history.append(validation)
            return validation
    
    def validate_interface_state(
        self,
        device_name: str,
        interface_name: str,
        expected_state: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate specific interface against expected state.
        
        Example expected_state (keys from Genie's interface ops model):
        {
            'oper_status': 'up',
            'enabled': True,
            'bandwidth': 1000000,
            'mtu': 1500,
        }
        """
        timestamp = datetime.utcnow()
        
        try:
            # Learn current interface state
            interfaces = self.learn_feature(device_name, 'interface')
            
            if interface_name not in interfaces:
                return ValidationResult(
                    device=device_name,
                    feature='interface',
                    timestamp=timestamp,
                    passed=False,
                    errors=[f"Interface {interface_name} not found"]
                )
            
            actual_state = interfaces[interface_name]
            errors = []
            
            # Validate each expected attribute
            for key, expected_value in expected_state.items():
                actual_value = actual_state.get(key)
                
                if actual_value != expected_value:
                    errors.append(
                        f"{key}: expected={expected_value}, actual={actual_value}"
                    )
            
            passed = len(errors) == 0
            
            result = ValidationResult(
                device=device_name,
                feature='interface',
                timestamp=timestamp,
                passed=passed,
                post_state=actual_state,
                errors=errors,
                metadata={'interface': interface_name, 'expected': expected_state}
            )
            
            logger.info(
                "interface_validation",
                device=device_name,
                interface=interface_name,
                passed=passed,
                errors=errors
            )
            
            self.validation_history.append(result)
            return result
            
        except Exception as e:
            logger.error(
                "interface_validation_failed",
                device=device_name,
                interface=interface_name,
                error=str(e)
            )
            
            return ValidationResult(
                device=device_name,
                feature='interface',
                timestamp=timestamp,
                passed=False,
                errors=[str(e)]
            )
    
    def validate_bgp_neighbors(
        self,
        device_name: str,
        expected_neighbor_count: Optional[int] = None,
        expected_state: str = 'established'
    ) -> ValidationResult:
        """
        Validate BGP neighbor states.
        
        Args:
            device_name: Device to validate
            expected_neighbor_count: Expected number of BGP neighbors
            expected_state: Expected BGP session state
        """
        timestamp = datetime.utcnow()
        
        try:
            # Learn BGP state
            bgp_state = self.learn_feature(device_name, 'bgp')
            
            if not bgp_state or 'instance' not in bgp_state:
                return ValidationResult(
                    device=device_name,
                    feature='bgp',
                    timestamp=timestamp,
                    passed=False,
                    errors=["No BGP instances found"]
                )
            
            errors = []
            total_neighbors = 0
            down_neighbors = []
            
            # Iterate through all BGP instances and VRFs
            for instance in bgp_state['instance'].values():
                for vrf in instance.get('vrf', {}).values():
                    for neighbor_id, neighbor in vrf.get('neighbor', {}).items():
                        total_neighbors += 1
                        session_state = neighbor.get('session_state', 'unknown').lower()
                        
                        if session_state != expected_state:
                            down_neighbors.append(
                                f"{neighbor_id} (state: {session_state})"
                            )
            
            # Validate neighbor count
            if expected_neighbor_count and total_neighbors != expected_neighbor_count:
                errors.append(
                    f"Neighbor count: expected={expected_neighbor_count}, "
                    f"actual={total_neighbors}"
                )
            
            # Validate neighbor states
            if down_neighbors:
                errors.append(f"Down neighbors: {', '.join(down_neighbors)}")
            
            passed = len(errors) == 0
            
            result = ValidationResult(
                device=device_name,
                feature='bgp',
                timestamp=timestamp,
                passed=passed,
                post_state=bgp_state,
                errors=errors,
                metadata={
                    'total_neighbors': total_neighbors,
                    'down_neighbors': down_neighbors,
                }
            )
            
            logger.info(
                "bgp_validation",
                device=device_name,
                passed=passed,
                total_neighbors=total_neighbors,
                down_neighbors=len(down_neighbors)
            )
            
            self.validation_history.append(result)
            return result
            
        except Exception as e:
            logger.error(
                "bgp_validation_failed",
                device=device_name,
                error=str(e)
            )
            
            return ValidationResult(
                device=device_name,
                feature='bgp',
                timestamp=timestamp,
                passed=False,
                errors=[str(e)]
            )
    
    def _save_snapshot(self, device_name: str, feature: str, state: Dict):
        """Save state snapshot to disk"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{device_name}_{feature}_{timestamp}.json"
        filepath = self.state_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.debug(
                "snapshot_saved",
                device=device_name,
                feature=feature,
                filepath=str(filepath)
            )
        except Exception as e:
            logger.error(
                "snapshot_save_failed",
                device=device_name,
                feature=feature,
                error=str(e)
            )
    
    def load_snapshot(self, device_name: str, feature: str) -> Optional[Dict]:
        """Load most recent snapshot for device/feature"""
        pattern = f"{device_name}_{feature}_*.json"
        snapshots = sorted(self.state_dir.glob(pattern), reverse=True)
        
        if not snapshots:
            logger.warning(
                "no_snapshot_found",
                device=device_name,
                feature=feature
            )
            return None
        
        latest_snapshot = snapshots[0]
        
        try:
            with open(latest_snapshot, 'r') as f:
                state = json.load(f)
            
            logger.info(
                "snapshot_loaded",
                device=device_name,
                feature=feature,
                filepath=str(latest_snapshot)
            )
            return state
            
        except Exception as e:
            logger.error(
                "snapshot_load_failed",
                device=device_name,
                feature=feature,
                error=str(e)
            )
            return None
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        total = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v.passed)
        failed = total - passed
        
        report = {
            'summary': {
                'total_validations': total,
                'passed': passed,
                'failed': failed,
                'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            'validations': [
                {
                    'device': v.device,
                    'feature': v.feature,
                    'timestamp': v.timestamp.isoformat(),
                    'passed': v.passed,
                    'errors': v.errors,
                }
                for v in self.validation_history
            ]
        }
        
        return report


# Usage Example: Complete Pre/Post Validation Workflow
def complete_validation_workflow(
    device_name: str,
    testbed_file: str,
    features: List[str] = ['interface', 'bgp', 'ospf']
):
    """
    Demonstrates complete validation workflow:
    1. Capture pre-state
    2. Make changes (simulated here)
    3. Capture post-state
    4. Compare and validate
    """
    validator = PyATSValidator(testbed_file)
    
    # Step 1: Capture pre-change state
    logger.info("capturing_pre_state", device=device_name)
    pre_states = validator.capture_pre_state(device_name, features)
    
    # Step 2: Make configuration changes
    # (This would be your Nornir config push task)
    logger.info("applying_changes", device=device_name)
    # ... config push happens here ...
    
    # Step 3: Capture post-change state
    logger.info("capturing_post_state", device=device_name)
    post_states = validator.capture_post_state(device_name, features)
    
    # Step 4: Compare states
    validation_results = []
    for feature in features:
        if feature in pre_states and feature in post_states:
            result = validator.compare_states(
                device_name,
                feature,
                pre_states[feature],
                post_states[feature],
                exclude_keys=['counters', 'in_pkts', 'out_pkts', 'in_octets', 'out_octets']
            )
            validation_results.append(result)
    
    # Step 5: Generate report
    report = validator.generate_validation_report()
    
    return validation_results, report
