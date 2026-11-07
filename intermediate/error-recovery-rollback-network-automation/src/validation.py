# src/validation.py
from dataclasses import dataclass
from typing import Callable, Any, List

@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    details: dict = None

class DeviceValidator:
    """Validate device state and trigger rollback if needed."""
    
    def __init__(self, device, state_manager):
        """
        Initialize validator.
        
        Args:
            device: Netmiko device
            state_manager: DeviceStateManager instance
        """
        self.device = device
        self.state_manager = state_manager
        self.validators = []
    
    def add_validator(self, name: str, validation_func: Callable):
        """
        Register a validation function.
        
        Args:
            name: Validator name
            validation_func: Function that returns ValidationResult
        """
        self.validators.append((name, validation_func))
    
    def validate_all(self) -> List[ValidationResult]:
        """
        Run all registered validators.
        
        Returns:
            list: Validation results
        """
        results = []
        
        for name, validator_func in self.validators:
            try:
                result = validator_func()
                results.append(result)
                
                status = "✓" if result.passed else "✗"
                print(f"{status} {name}: {result.message}")
            
            except Exception as e:
                result = ValidationResult(
                    passed=False,
                    message=f"Validator failed: {str(e)}",
                    details={"error": str(e)}
                )
                results.append(result)
        
        return results
    
    def all_passed(self, results: List[ValidationResult]) -> bool:
        """Check if all validations passed."""
        return all(r.passed for r in results)


# Example validators for common checks

def validate_no_config_errors(device) -> ValidationResult:
    """Check device has no syntax errors."""
    output = device.send_command("show running-config")
    
    if "ERROR" in output or "invalid" in output.lower():
        return ValidationResult(
            passed=False,
            message="Configuration contains errors"
        )
    
    return ValidationResult(
        passed=True,
        message="No configuration errors detected"
    )


def validate_interfaces_up(device, min_interfaces=2) -> ValidationResult:
    """Check minimum number of interfaces are up."""
    output = device.send_command("show ip interface brief")
    
    # Columns: Interface, IP-Address, OK?, Method, Status, Protocol.
    # IOS prints the last two in lower case: "up up" means up/up.
    up_count = sum(
        1 for line in output.splitlines()[1:]
        if line.split()[-2:] == ["up", "up"]
    )
    
    if up_count < min_interfaces:
        return ValidationResult(
            passed=False,
            message=f"Only {up_count} interfaces up (expected {min_interfaces})",
            details={"up_interfaces": up_count, "required": min_interfaces}
        )
    
    return ValidationResult(
        passed=True,
        message=f"{up_count} interfaces up (required {min_interfaces})"
    )


def validate_bgp_neighbors_established(device, min_neighbors=1) -> ValidationResult:
    """Check BGP neighbors are established."""
    output = device.send_command("show ip bgp summary")
    
    # Established peers show a prefix count in the last column
    # (State/PfxRcd); others show a state such as Idle or Active.
    # IOS never prints the word "Established" in this table.
    established = 0
    in_table = False
    for line in output.splitlines():
        if line.startswith("Neighbor"):
            in_table = True
            continue
        parts = line.split()
        if in_table and parts and parts[-1].isdigit():
            established += 1
    
    if established < min_neighbors:
        return ValidationResult(
            passed=False,
            message=f"Only {established} BGP neighbors established (expected {min_neighbors})"
        )
    
    return ValidationResult(
        passed=True,
        message=f"{established} BGP neighbors established"
    )


def validate_vlans_created(device, expected_vlans: List[int]) -> ValidationResult:
    """Check expected VLANs exist."""
    output = device.send_command("show vlan brief")
    
    missing = []
    for vlan_id in expected_vlans:
        vlan_exists = any(
            line.split() and line.split()[0] == str(vlan_id)
            for line in output.splitlines()
        )
        if not vlan_exists:
            missing.append(vlan_id)
    
    if missing:
        return ValidationResult(
            passed=False,
            message=f"VLANs missing: {missing}",
            details={"missing_vlans": missing}
        )
    
    return ValidationResult(
        passed=True,
        message=f"All {len(expected_vlans)} expected VLANs created"
    )
