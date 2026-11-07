# src/sanity_tests.py
class SanityTestResult:
    def __init__(self, test_name: str, passed: bool, message: str):
        self.test_name = test_name
        self.passed = passed
        self.message = message

class SanityTests:
    """Verify deployment had expected effect."""
    
    def __init__(self, device):
        self.device = device
    
    def test_interfaces_still_up(self, expected_up=2) -> SanityTestResult:
        """Verify interfaces didn't break."""
        output = self.device.send_command("show ip interface brief")
        # Columns: Interface, IP-Address, OK?, Method, Status, Protocol.
        # IOS prints the last two in lower case: "up up" means up/up.
        up_count = sum(
            1 for line in output.splitlines()[1:]
            if line.split()[-2:] == ["up", "up"]
        )
        
        if up_count >= expected_up:
            return SanityTestResult(
                "interfaces_up",
                True,
                f"{up_count} interfaces up (expected {expected_up})"
            )
        else:
            return SanityTestResult(
                "interfaces_up",
                False,
                f"Only {up_count} interfaces up (expected {expected_up})"
            )
    
    def test_config_saved(self) -> SanityTestResult:
        """Verify configuration was saved."""
        try:
            self.device.send_command("write memory")
            return SanityTestResult(
                "config_saved",
                True,
                "Configuration saved successfully"
            )
        except Exception as e:
            return SanityTestResult(
                "config_saved",
                False,
                f"Failed to save configuration: {str(e)}"
            )
    
    def test_device_responsive(self) -> SanityTestResult:
        """Verify device still responds to commands."""
        try:
            self.device.send_command("show version")
            return SanityTestResult(
                "device_responsive",
                True,
                "Device is responsive"
            )
        except Exception as e:
            return SanityTestResult(
                "device_responsive",
                False,
                f"Device not responsive: {str(e)}"
            )
