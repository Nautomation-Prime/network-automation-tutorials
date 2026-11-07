# src/remediation_runbooks.py
import asyncio
from netmiko import ConnectHandler
from remediation import RemediationRunbook

# Netmiko is blocking, so every step runs its session in a worker thread
# with asyncio.to_thread() rather than stalling the event loop

def _session(device: dict, work):
    """Open a Netmiko session, run work(conn), and close it again."""
    with ConnectHandler(**device) as conn:
        return work(conn)

def all_bgp_neighbors_established(bgp_summary: str) -> bool:
    """
    True if every neighbour row of 'show ip bgp summary' ends in a number.

    IOS never prints the word "Established" here: an established peer
    shows its received-prefix count in the last column, and a down peer
    shows its state (Idle, Active, Connect...).
    """
    _, found, table = bgp_summary.partition("Neighbor")
    if not found:
        return False
    states = [line.split()[-1] for line in table.splitlines()[1:] if line.strip()]
    return bool(states) and all(state.isdigit() for state in states)

# --- BGP Flapping Remediation -------------------------------------------

async def clear_bgp_session(device):
    """Soft-reset BGP (re-sends routes without dropping the sessions)."""
    await asyncio.to_thread(_session, device, lambda conn: conn.send_command("clear ip bgp * soft"))

async def verify_bgp_stable(device):
    """Verify every BGP neighbour is established."""
    output = await asyncio.to_thread(
        _session, device, lambda conn: conn.send_command("show ip bgp summary")
    )
    return all_bgp_neighbors_established(output)

def build_bgp_flapping_runbook(device: dict) -> RemediationRunbook:
    """BGP runbook for one device (a Netmiko connection dict)."""
    runbook = RemediationRunbook("BGP Session Flapping")
    runbook.add_action(
        name="Clear BGP session",
        func=lambda: clear_bgp_session(device),
        validate_func=lambda: verify_bgp_stable(device),
        # A soft clear changes no configuration, so there's no undo_func
    )
    return runbook

# --- Interface Error Remediation ----------------------------------------

async def restart_interface(device, interface):
    """Bounce the interface (shutdown / no shutdown)."""
    await asyncio.to_thread(_session, device, lambda conn: conn.send_config_set([
        f"interface {interface}",
        "shutdown",
        "no shutdown"
    ]))

async def enable_interface(device, interface):
    """Undo step: make sure a failed bounce doesn't leave the port shut down."""
    await asyncio.to_thread(_session, device, lambda conn: conn.send_config_set([
        f"interface {interface}",
        "no shutdown"
    ]))

async def verify_interface_healthy(device, interface):
    """
    Verify the interface came back up/up.

    Error counters don't reset when an interface bounces, so the error
    *rate* is judged by the monitor's next measurement, not here.
    """
    output = await asyncio.to_thread(
        _session, device, lambda conn: conn.send_command(f"show interfaces {interface}")
    )
    return "is up, line protocol is up" in output

def build_interface_error_runbook(device: dict, interface: str) -> RemediationRunbook:
    """Interface runbook for one port on one device."""
    runbook = RemediationRunbook("High Interface Error Rate")
    runbook.add_action(
        name=f"Restart interface {interface}",
        func=lambda: restart_interface(device, interface),
        validate_func=lambda: verify_interface_healthy(device, interface),
        undo_func=lambda: enable_interface(device, interface),
    )
    return runbook
