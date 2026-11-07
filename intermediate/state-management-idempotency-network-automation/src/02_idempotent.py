# ✅ IDEMPOTENT
def ensure_access_port(device, interface, vlan):
    """Ensure the port has the standard access configuration (safe to repeat)."""
    wanted = ["switchport mode access", f"switchport access vlan {vlan}"]

    # Read first: what is actually configured?
    current = device.send_command(f"show running-config interface {interface}")
    current_lines = {line.strip() for line in current.splitlines()}

    missing = [line for line in wanted if line not in current_lines]
    if not missing and "shutdown" not in current_lines:
        print(f"{interface} already correct, nothing sent")
        return "unchanged"

    # Change only what differs. No "default interface", so no link flap.
    device.send_config_set([f"interface {interface}", *missing, "no shutdown"])
    print(f"{interface} updated: {missing or ['no shutdown']}")
    return "changed"

# Run 1: ✓ Port updated
# Run 2: ✓ Already correct, nothing sent, no flap
# Run 3-5: ✓ Already correct, nothing sent
