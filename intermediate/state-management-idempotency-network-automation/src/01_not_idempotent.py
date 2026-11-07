# ❌ NOT IDEMPOTENT
def reset_access_port(device, interface, vlan):
    """Put a port back to the standard access configuration."""
    device.send_config_set([
        f"default interface {interface}",   # wipes the port first
        f"interface {interface}",
        "switchport mode access",
        f"switchport access vlan {vlan}",
        "no shutdown",
    ])

# Run 1: ✓ Port configured
# Run 2: ✗ Port wiped and rebuilt — the link drops, though nothing needed to change
# Run 3-5: ✗ Another outage for that user on every scheduled run
