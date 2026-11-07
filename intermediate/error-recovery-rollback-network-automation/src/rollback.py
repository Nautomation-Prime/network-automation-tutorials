# src/rollback.py
from state_management import DeviceStateManager
from validation import DeviceValidator

class RollbackManager:
    """Manage configuration rollback."""
    
    def __init__(self, device):
        """Initialize rollback manager."""
        self.device = device
        self.state_manager = DeviceStateManager(device)
        self.rollback_config = None
    
    def safe_config_deploy(self, change_func, validators: list) -> bool:
        """
        Apply configuration changes with automatic rollback on failure.
        
        Args:
            change_func: Function that applies changes (takes device as arg)
            validators: List of (validator_name, validator_func) tuples
        
        Returns:
            bool: True if successful, False if rolled back
        """
        print("Step 1: Capturing pre-change configuration...")
        self.state_manager.capture_state("pre_change")
        self.state_manager.save_state_to_file("pre_change", "pre_change.json")
        
        print("\nStep 2: Applying configuration changes...")
        try:
            change_func(self.device)
        except Exception as e:
            print(f"✗ Configuration deployment failed: {str(e)}")
            print("Performing emergency rollback...")
            self._rollback_to_saved_state()
            return False
        
        print("\nStep 3: Capturing post-change configuration...")
        self.state_manager.capture_state("post_change")
        
        print("\nStep 4: Validating changes...")
        validator = DeviceValidator(self.device, self.state_manager)
        
        # Register all validators
        for validator_name, validator_func in validators:
            validator.add_validator(
                validator_name,
                lambda vf=validator_func: vf(self.device)
            )
        
        results = validator.validate_all()
        
        if not validator.all_passed(results):
            print("\n✗ Post-deployment validation FAILED")
            print("Performing automatic rollback...")
            self._rollback_to_saved_state()
            return False
        
        print("\n✓ All validations PASSED")
        print("Configuration change successful!")
        return True
    
    def _rollback_to_saved_state(self):
        """
        Roll back by reloading onto the startup configuration.

        This works only because the change was never saved: startup-config
        still holds the pre-change state. The SSH session is lost when the
        device reloads, so reconnect before doing anything else with it.
        """
        pre_state = self.state_manager.state_history.get("pre_change")
        
        if not pre_state:
            print("✗ ERROR: No pre-change state available!")
            return
        
        print("Reloading onto the startup configuration...")
        output = self.device.send_command_timing("reload")
        
        # With unsaved changes, IOS asks first:
        #   System configuration has been modified. Save? [yes/no]:
        # Answer "no". Saving now would make the bad change permanent.
        if "save?" in output.lower():
            output = self.device.send_command_timing("no")
        
        # Then: Proceed with reload? [confirm]   (Enter confirms)
        if "confirm" in output.lower():
            try:
                self.device.send_command_timing("")
            except (OSError, EOFError):
                pass  # the device is going down and has closed the session
        
        print("✓ Reload issued: the device will boot on its pre-change startup config")
