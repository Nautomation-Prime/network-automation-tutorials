# src/state_driver.py
import re


def canonical_interface(name: str) -> str:
    """
    Reduce an interface name to one comparable form.

    The device reports "GigabitEthernet0/0/1"; people write "Gi0/0/1".
    Both become "gi0/0/1", so desired and current state can be matched.
    """
    return re.sub(r"^([A-Za-z]{2})[A-Za-z-]*", lambda m: m.group(1).lower(), name.strip())


class StateDrivenConfigurator:
    """Apply desired state to device (idempotent)."""
    
    def __init__(self, device):
        self.device = device
    
    def get_current_state(self) -> dict:
        """Retrieve current device state."""
        return {
            "interfaces": self._get_interfaces(),
            "vlans": self._get_vlans(),
            "bgp": self._get_bgp_state(),
        }
    
    def _get_interfaces(self) -> dict:
        """Get current interface configuration."""
        output = self.device.send_command("show ip interface brief")
        interfaces = {}
        
        # Columns: Interface, IP-Address, OK?, Method, Status, Protocol
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 6:
                continue
            interfaces[canonical_interface(parts[0])] = {
                "ip": parts[1],
                "status": " ".join(parts[4:-1]),   # "up", "administratively down"
            }
        
        return interfaces
    
    def _get_vlans(self) -> dict:
        """Get current VLAN configuration."""
        output = self.device.send_command("show vlan brief")
        vlans = {}
        
        for line in output.split('\n'):
            if line.split() and line.split()[0].isdigit():
                parts = line.split()
                vlan_id = parts[0]
                vlan_name = parts[1] if len(parts) > 1 else ""
                
                vlans[vlan_id] = {"name": vlan_name}
        
        return vlans
    
    def _get_bgp_state(self) -> dict:
        """Get current BGP state."""
        output = self.device.send_command("show ip bgp summary")
        
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
        
        return {"neighbors_established": established}
    
    def ensure_interfaces(self, desired_interfaces: dict):
        """Ensure interface configuration matches desired state."""
        current = self.get_current_state()["interfaces"]
        
        for interface, desired_config in desired_interfaces.items():
            current_config = current.get(canonical_interface(interface), {})
            
            # Check if interface configuration matches
            if current_config.get("ip") != desired_config.get("ip"):
                print(f"Updating {interface} IP...")
                self.device.send_config_set([
                    f"interface {interface}",
                    f"ip address {desired_config['ip']} {desired_config['netmask']}",
                ])
    
    def ensure_vlans(self, desired_vlans: dict):
        """Ensure VLAN configuration matches desired state."""
        current = self.get_current_state()["vlans"]
        
        for vlan_id, vlan_config in desired_vlans.items():
            if vlan_id not in current:
                print(f"Creating VLAN {vlan_id}...")
                self.device.send_config_set([
                    f"vlan {vlan_id}",
                    f"name {vlan_config['name']}",
                ])
    
    def apply_desired_state(self, desired_state: dict):
        """Apply all desired state (idempotent)."""
        print("Applying desired state...")
        
        if "interfaces" in desired_state:
            self.ensure_interfaces(desired_state["interfaces"])
        
        if "vlans" in desired_state:
            self.ensure_vlans(desired_state["vlans"])
        
        print("✓ Desired state applied")
