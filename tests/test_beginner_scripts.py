"""
Run each beginner script end to end against fake devices.

The scripts are run exactly as a learner runs them (`python script.py` with
devices.csv beside them). Only two things are swapped out: the password
prompt, and Netmiko's ConnectHandler, which is replaced by a fake that
returns real-shaped output, so no device or network is needed.
"""

import runpy
import shutil
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
BEGINNER = ROOT / "beginner"

# What ntc-templates' cisco_ios "show version" template returns for a
# Catalyst 9300, captured from a real parse (lists included).
SHOW_VERSION = {
    "software_image": "CAT9K_IOSXE", "version": "17.9.4a", "release": "fc3",
    "rommon": "IOS-XE", "hostname": "lab-sw-01",
    "uptime": "2 weeks, 3 days, 4 hours, 5 minutes", "reload_reason": "Reload Command",
    "running_image": "packages.conf", "hardware": ["C9300-48P"],
    "serial": ["FOC2140L0AB"], "config_register": "0x102",
    "mac_address": ["00:11:22:33:44:55"],
}

RUNNING_CONFIG = """Building configuration...

Current configuration : 1024 bytes
!
hostname {host}
!
interface GigabitEthernet1/0/1
 description uplink
!
end
"""


class FakeConnection:
    """Stands in for a Netmiko connection. Hosts in `unreachable` raise."""

    unreachable: set[str] = set()
    opened: list[str] = []

    def __init__(self, **device):
        host = device["host"]
        if host in self.unreachable:
            from netmiko.exceptions import NetmikoTimeoutException
            raise NetmikoTimeoutException(f"TCP connection to device failed: {host}")
        self.host = host
        FakeConnection.opened.append(host)

    def send_command(self, command, use_textfsm=False, **kwargs):
        if command == "show version" and use_textfsm:
            return [dict(SHOW_VERSION, hostname=f"sw-{self.host.replace('.', '-')}")]
        if command == "show running-config":
            return RUNNING_CONFIG.format(host=self.host)
        return f"% output of {command}"

    def find_prompt(self):
        return f"sw-{self.host}#"

    def enable(self):
        pass

    def disconnect(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.disconnect()


@pytest.fixture
def run_lesson_script(tmp_path, monkeypatch):
    """Copy a lesson folder to tmp, fake the device layer, run the script."""
    FakeConnection.unreachable = set()
    FakeConnection.opened = []

    import netmiko
    fake = types.ModuleType("netmiko")
    fake.__dict__.update(netmiko.__dict__)
    fake.ConnectHandler = FakeConnection
    monkeypatch.setitem(sys.modules, "netmiko", fake)
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "lab-password")

    def run(lesson: str, script: str, unreachable: tuple[str, ...] = ()) -> Path:
        FakeConnection.unreachable = set(unreachable)
        work = tmp_path / lesson
        shutil.copytree(BEGINNER / lesson, work)
        monkeypatch.chdir(work)
        runpy.run_path(str(work / script), run_name="__main__")
        return work

    return run


def test_show_version_to_excel(run_lesson_script, capsys):
    work = run_lesson_script("netmiko-show-command-to-excel", "show_version_to_excel.py")

    output = work / "192.168.1.1_show_version.xlsx"
    assert output.exists(), capsys.readouterr().out
    sheet = pd.read_excel(output, sheet_name="Show Version")
    assert sheet.loc[0, "version"] == "17.9.4a"
    assert "Data exported to" in capsys.readouterr().out


def test_multi_device_show_version(run_lesson_script, capsys):
    work = run_lesson_script("multi-device-show-command", "multi_device_show_version.py")

    workbooks = list(work.glob("*.xlsx"))
    assert len(workbooks) == 1, capsys.readouterr().out
    sheets = pd.read_excel(workbooks[0], sheet_name=None)
    assert len(sheets) == 3                      # one sheet per device in devices.csv
    assert FakeConnection.opened == ["10.1.1.1", "10.1.1.2", "10.1.1.3"]


def test_multi_device_show_version_survives_a_dead_device(run_lesson_script, capsys):
    work = run_lesson_script("multi-device-show-command", "multi_device_show_version.py",
                             unreachable=("10.1.1.2",))

    sheets = pd.read_excel(next(work.glob("*.xlsx")), sheet_name=None)
    assert len(sheets) == 2                      # the other two still collected


def test_backup_running_configs(run_lesson_script, capsys):
    work = run_lesson_script("multi-device-config-backup", "backup_running_configs.py",
                             unreachable=("10.1.1.10",))

    runs = [p for p in (work / "backups").iterdir() if p.is_dir()]
    assert len(runs) == 1, capsys.readouterr().out
    configs = sorted(p.name for p in runs[0].glob("*.txt"))
    assert len(configs) == 2                     # 10.1.1.10 was unreachable
    assert "hostname 10.1.1.1" in (runs[0] / configs[0]).read_text()

    manifest = list(runs[0].glob("*.xlsx"))
    assert len(manifest) == 1
    rows = pd.read_excel(manifest[0])
    assert len(rows) == 3                        # the failure is recorded too
