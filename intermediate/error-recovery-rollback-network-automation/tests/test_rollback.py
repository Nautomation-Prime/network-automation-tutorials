# tests/test_rollback.py (pytest)
from unittest.mock import MagicMock

from rollback import RollbackManager
from validation import validate_interfaces_up


def test_rollback_works(tmp_path, monkeypatch):
    """A change that fails validation must trigger the reload."""
    monkeypatch.chdir(tmp_path)          # pre_change.json is written here

    device = MagicMock()
    device.host = "10.0.0.1"             # saved into the JSON state file
    # After the bad change, no interface is up/up
    device.send_command.return_value = (
        "Interface     IP-Address   OK? Method Status  Protocol\n"
        "Gi0/0/1       10.0.0.1     YES manual down    down\n"
    )
    device.send_command_timing.return_value = "Proceed with reload? [confirm]"

    rollback = RollbackManager(device)

    def bad_change(dev):
        dev.send_config_set(["interface Gi0/0/1", "shutdown"])  # BAD!

    success = rollback.safe_config_deploy(
        bad_change, [("interfaces_up", validate_interfaces_up)])

    assert success is False                           # rolled back
    device.send_command_timing.assert_any_call("reload")
