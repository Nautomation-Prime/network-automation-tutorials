# src/state_management.py
import json
from datetime import datetime, timezone
from netmiko import ConnectHandler
from pathlib import Path

class DeviceStateManager:
    """Capture and compare device states."""
    
    def __init__(self, device):
        """
        Initialize with a connected device.
        
        Args:
            device: Netmiko ConnectHandler instance
        """
        self.device = device
        self.state_history = {}
    
    def capture_state(self, state_name="current", commands=None):
        """
        Capture current device configuration state.
        
        Args:
            state_name: Label for this state (e.g., "pre_change", "post_change")
            commands: List of commands to run (default: common show commands)
        
        Returns:
            dict: Device state snapshot
        """
        if commands is None:
            commands = [
                "show ip route summary",
                "show ip interface brief",
                "show running-config | include vlan",
                "show ip bgp summary",
            ]
        
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device": self.device.host,
            "outputs": {}
        }
        
        for command in commands:
            try:
                output = self.device.send_command(command)
                state["outputs"][command] = output
            except Exception as e:
                state["outputs"][command] = f"ERROR: {str(e)}"
        
        # Store in history
        self.state_history[state_name] = state
        
        return state
    
    def compare_states(self, state1_name, state2_name):
        """
        Compare two captured states.
        
        Args:
            state1_name: Name of first state (e.g., "pre_change")
            state2_name: Name of second state (e.g., "post_change")
        
        Returns:
            dict: Differences between states
        """
        state1 = self.state_history.get(state1_name)
        state2 = self.state_history.get(state2_name)
        
        if not state1 or not state2:
            raise ValueError("Both states must be captured first")
        
        differences = {
            "state1": state1_name,
            "state2": state2_name,
            "changes": {}
        }
        
        # Compare command outputs
        for command in state1["outputs"]:
            output1 = state1["outputs"].get(command, "")
            output2 = state2["outputs"].get(command, "")
            
            if output1 != output2:
                differences["changes"][command] = {
                    "before": output1[:200] + "..." if len(output1) > 200 else output1,
                    "after": output2[:200] + "..." if len(output2) > 200 else output2,
                }
        
        return differences
    
    def save_state_to_file(self, state_name, filename):
        """
        Save state snapshot to file for recovery.
        
        Args:
            state_name: Name of state to save
            filename: File path
        """
        state = self.state_history.get(state_name)
        if not state:
            raise ValueError(f"State '{state_name}' not found")
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"✓ State saved to {filename}")
    
    def load_state_from_file(self, filename):
        """Load previously saved state."""
        with open(filename, 'r') as f:
            state = json.load(f)
        
        self.state_history["loaded"] = state
        return state
