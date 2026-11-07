# src/automation_engine.py
import asyncio
import re
from datetime import datetime
from typing import List
from netmiko import ConnectHandler
from incident_detector import Incident, PatternMatcher, RemediationType, SeverityLevel
from remediation_runbooks import build_bgp_flapping_runbook
from incident_tracker import IncidentTracker

class AutomationEngine:
    """Main orchestration for incident detection and response."""
    
    def __init__(self, devices: List[dict]):
        self.devices = devices
        self.detector = PatternMatcher()
        self.tracker = IncidentTracker()
        self.runbook_builders = {}
        
        # Register patterns
        self._register_patterns()
        
        # Register runbooks
        self._register_runbooks()
    
    def _register_patterns(self):
        """Register all incident detection patterns."""
        # BGP flapping: a session changed state within the hour, and at
        # least one neighbour is down right now
        self.detector.register_pattern(
            name="BGP Session Flapping",
            check_func=lambda m: (
                m.get("bgp_changes_hour", 0) > 0 and
                not m.get("bgp_established", True)
            ),
            severity=SeverityLevel.HIGH,
            remediation_type=RemediationType.AUTOMATIC
        )
        # ... more patterns
    
    def _register_runbooks(self):
        """Register runbook builders: runbooks are built per device on demand."""
        self.runbook_builders["BGP Session Flapping"] = build_bgp_flapping_runbook

    # --- Metric parsers: plain functions of CLI text, easy to unit test ---

    @staticmethod
    def _bgp_neighbor_rows(bgp_summary: str) -> List[List[str]]:
        """Split the neighbour table of 'show ip bgp summary' into columns."""
        _, found, table = bgp_summary.partition("Neighbor")
        if not found:
            return []
        return [line.split() for line in table.splitlines()[1:] if line.strip()]

    def _count_bgp_changes(self, bgp_summary: str) -> int:
        """
        Neighbours whose session went up or down within the last hour.

        Up/Down shows hh:mm:ss for times under a day (longer ones look like
        2d03h), so 00:mm:ss means the state changed less than an hour ago.
        """
        return sum(
            1 for row in self._bgp_neighbor_rows(bgp_summary)
            if re.fullmatch(r"00:\d\d:\d\d", row[-2])
        )

    def _check_bgp_established(self, bgp_summary: str) -> bool:
        """True if every neighbour shows a prefix count (not Idle/Active...)."""
        return all(row[-1].isdigit() for row in self._bgp_neighbor_rows(bgp_summary))

    def _get_interface_errors(self, input_error_lines: str) -> int:
        """Total input errors across all interfaces."""
        return sum(int(n) for n in re.findall(r"(\d+) input errors", input_error_lines))

    def _collect_metrics(self, device: dict) -> dict:
        """Blocking Netmiko work; check_device() runs it in a worker thread."""
        with ConnectHandler(**device) as conn:
            bgp_summary = conn.send_command("show ip bgp summary")
            input_errors = conn.send_command("show interfaces | include input errors")

        return {
            "reachable": True,
            "bgp_changes_hour": self._count_bgp_changes(bgp_summary),
            "bgp_established": self._check_bgp_established(bgp_summary),
            "interface_errors": self._get_interface_errors(input_errors)
        }

    async def check_device(self, device: dict) -> List[Incident]:
        """Collect metrics and detect incidents."""
        try:
            metrics = await asyncio.to_thread(self._collect_metrics, device)
            return self.detector.detect(device["host"], metrics)

        except Exception as e:
            return [Incident(
                id="INC-UNREACHABLE",
                name="Device Unreachable",
                severity=SeverityLevel.CRITICAL,
                device=device["host"],
                symptoms={"error": str(e)},
                detected_at=datetime.now(),
                remediation_type=RemediationType.ESCALATE,
                likely_causes=["Network down", "Device down"]
            )]
    
    async def run(self, check_interval: int = 60):
        """Main event loop."""
        print("Starting incident response engine...")
        
        while True:
            print(f"\n[{datetime.now()}] Checking devices...")
            
            # Check all devices, keeping each incident with its device
            found = []
            for device in self.devices:
                for incident in await self.check_device(device):
                    found.append((device, incident))

            # Process incidents
            for device, incident in found:
                print(f"\n{incident.severity.value.upper()}: {incident.name} on {incident.device}")

                self.tracker.record_incident(incident)

                # Only auto-remediate lower severity
                if incident.remediation_type == RemediationType.AUTOMATIC:
                    if incident.name in self.runbook_builders:
                        runbook = self.runbook_builders[incident.name](device)
                        result = await runbook.execute(incident)
                        self.tracker.record_remediation(incident.id, result)

                else:
                    print(f"  ⚠ Escalating to NOC: {incident.likely_causes}")
            
            # Wait for next check
            await asyncio.sleep(check_interval)
