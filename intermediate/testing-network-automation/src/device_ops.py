# src/device_ops.py
import re


def short_name(interface):
    """GigabitEthernet0/0/1 and Gi0/0/1 both become gi0/0/1."""
    return re.sub(r"^([A-Za-z]{2})[A-Za-z-]*", lambda m: m.group(1).lower(), interface)


def configure_interface(device, interface, ip_address, netmask):
    """Configure interface with IP address."""
    commands = [
        f"interface {interface}",
        f"ip address {ip_address} {netmask}",
        "no shutdown",
    ]
    # send_config_set enters config mode, sends the lines and exits again
    device.send_config_set(commands)
    return True


def verify_interface_config(device, interface, expected_ip):
    """Verify interface has expected IP."""
    output = device.send_command("show ip interface brief")
    # The device prints GigabitEthernet0/0/1 even if you wrote Gi0/0/1, and
    # "10.0.0.1" is a substring of "10.0.0.10" — so match row and column.
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and short_name(parts[0]) == short_name(interface):
            return parts[1] == expected_ip
    return False
