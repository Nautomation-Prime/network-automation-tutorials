# src/patterns.py
from incident_detector import PatternMatcher, SeverityLevel, RemediationType

detector = PatternMatcher()

# Pattern: BGP session flapping
detector.register_pattern(
    name="BGP Session Flapping",
    check_func=lambda m: (
        m.get("bgp_session_changes_last_hour", 0) > 10 and
        m.get("bgp_session_state") != "Established"
    ),
    severity=SeverityLevel.HIGH,
    remediation_type=RemediationType.AUTOMATIC,
    likely_causes=[
        "BGP configuration mismatch",
        "Network connectivity issue",
        "Peer interface bouncing",
        "CPU overload"
    ]
)

# Pattern: High interface error rate
detector.register_pattern(
    name="High Interface Error Rate",
    check_func=lambda m: (
        m.get("interface_crc_errors", 0) > 100 or
        m.get("interface_errors_percent", 0) > 5
    ),
    severity=SeverityLevel.CRITICAL,
    remediation_type=RemediationType.MANUAL,
    likely_causes=[
        "Duplex mismatch",
        "Defective cable",
        "Port flapping",
        "Controller issue"
    ]
)

# Pattern: Low memory
detector.register_pattern(
    name="Low Available Memory",
    check_func=lambda m: m.get("available_memory_percent", 100) < 10,
    severity=SeverityLevel.HIGH,
    remediation_type=RemediationType.MANUAL,
    likely_causes=[
        "Memory leak in process",
        "Process consuming too much memory",
        "Device needs restart"
    ]
)

# Pattern: Reachability loss
detector.register_pattern(
    name="Device Unreachable",
    check_func=lambda m: not m.get("reachable", True),
    severity=SeverityLevel.CRITICAL,
    remediation_type=RemediationType.ESCALATE,
    likely_causes=[
        "Network connectivity issue",
        "Device down",
        "Routing issues",
        "Management interface failure"
    ]
)
