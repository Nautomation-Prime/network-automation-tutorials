# src/idempotent_operations.py
from dataclasses import dataclass
from enum import Enum

class OperationStatus(Enum):
    """Status of an idempotent operation."""
    CREATED = "created"
    ALREADY_EXISTS = "already_exists"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    FAILED = "failed"

@dataclass
class OperationResult:
    """Result of an idempotent operation."""
    status: OperationStatus
    message: str
    details: dict = None

class IdempotentOperations:
    """Idempotent network operations (safe to repeat)."""
    
    @staticmethod
    def ensure_vlan_exists(device, vlan_id: int, vlan_name: str) -> OperationResult:
        """
        Ensure VLAN exists with given name (idempotent).
        
        Safe to call multiple times—won't duplicate VLAN.
        """
        # Check if VLAN already exists
        output = device.send_command(f"show vlan id {vlan_id}")
        
        # The VLAN's row starts with its ID and the next column is its name.
        # A missing VLAN prints "VLAN id N not found in current VLAN database".
        row = next(
            (line.split() for line in output.splitlines()
             if line.split()[:1] == [str(vlan_id)]),
            None,
        )
        
        if row is not None:
            # VLAN exists, verify name matches exactly
            if len(row) > 1 and row[1] == vlan_name:
                return OperationResult(
                    status=OperationStatus.UNCHANGED,
                    message=f"VLAN {vlan_id} exists with correct name",
                    details={"vlan_id": vlan_id, "vlan_name": vlan_name}
                )
            else:
                # VLAN exists but name differs, update it
                device.send_config_set([f"vlan {vlan_id}", f"name {vlan_name}"])
                
                return OperationResult(
                    status=OperationStatus.UPDATED,
                    message=f"VLAN {vlan_id} name updated to {vlan_name}",
                    details={"vlan_id": vlan_id, "vlan_name": vlan_name}
                )
        
        # VLAN doesn't exist, create it
        device.send_config_set([f"vlan {vlan_id}", f"name {vlan_name}"])
        
        return OperationResult(
            status=OperationStatus.CREATED,
            message=f"VLAN {vlan_id} created with name {vlan_name}",
            details={"vlan_id": vlan_id, "vlan_name": vlan_name}
        )
    
    @staticmethod
    def ensure_interface_config(device, interface: str, config_lines: list) -> OperationResult:
        """
        Ensure interface has specific configuration (idempotent).
        
        Args:
            device: Netmiko device
            interface: Interface name (e.g., "Gi0/0/1")
            config_lines: List of config commands to apply
        """
        # Get current interface configuration
        current_config = device.send_command(f"show running-config interface {interface}")
        
        # Check if all config lines already exist
        all_exist = all(line in current_config for line in config_lines)
        
        if all_exist:
            return OperationResult(
                status=OperationStatus.UNCHANGED,
                message=f"Interface {interface} already has required configuration",
                details={"interface": interface, "lines": config_lines}
            )
        
        # Apply missing configuration
        device.send_config_set([f"interface {interface}", *config_lines])
        
        return OperationResult(
            status=OperationStatus.UPDATED,
            message=f"Interface {interface} configuration applied",
            details={"interface": interface, "lines": config_lines}
        )
    
    @staticmethod
    def ensure_bgp_neighbor(device, asn: int, neighbor_ip: str, neighbor_asn: int) -> OperationResult:
        """Ensure BGP neighbor is configured (idempotent)."""
        # Check if neighbor already exists
        output = device.send_command("show ip bgp summary")
        
        if neighbor_ip in output:
            return OperationResult(
                status=OperationStatus.UNCHANGED,
                message=f"BGP neighbor {neighbor_ip} already configured",
                details={"neighbor_ip": neighbor_ip}
            )
        
        # Configure BGP neighbor
        device.send_config_set([
            f"router bgp {asn}",
            f"neighbor {neighbor_ip} remote-as {neighbor_asn}",
        ])
        
        return OperationResult(
            status=OperationStatus.CREATED,
            message=f"BGP neighbor {neighbor_ip} configured",
            details={"neighbor_ip": neighbor_ip, "neighbor_asn": neighbor_asn}
        )
