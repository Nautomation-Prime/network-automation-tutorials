# tests/test_idempotent_operations.py
from idempotent_operations import IdempotentOperations, OperationStatus


class FakeSwitch:
    """
    Just enough of a Netmiko connection to test idempotency: it remembers
    VLANs, so a second run sees what the first run created. A MagicMock
    can't do that, and a stateless fake would make the test meaningless.
    """

    def __init__(self):
        self.vlans = {}

    def send_command(self, command):
        vlan_id = command.split()[-1]          # "show vlan id 100"
        if vlan_id not in self.vlans:
            return f"VLAN id {vlan_id} not found in current VLAN database"
        return (
            "VLAN Name                             Status    Ports\n"
            "---- -------------------------------- --------- -----\n"
            f"{vlan_id:<4} {self.vlans[vlan_id]:<32} active\n"
        )

    def send_config_set(self, commands):
        vlan_id = commands[0].split()[1]       # "vlan 100"
        self.vlans[vlan_id] = commands[1].split()[1]   # "name DATA"


def test_operation_is_idempotent():
    """Running the same operation repeatedly must be safe and honest."""
    switch = FakeSwitch()
    ops = IdempotentOperations()

    # Run 1 creates it
    assert ops.ensure_vlan_exists(switch, 100, "DATA").status == OperationStatus.CREATED

    # Runs 2 and 3 change nothing
    assert ops.ensure_vlan_exists(switch, 100, "DATA").status == OperationStatus.UNCHANGED
    assert ops.ensure_vlan_exists(switch, 100, "DATA").status == OperationStatus.UNCHANGED

    # A different desired name is an update, not a recreate
    assert ops.ensure_vlan_exists(switch, 100, "VOICE").status == OperationStatus.UPDATED
