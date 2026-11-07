# src/incident_detector.py
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Callable
from datetime import datetime
from enum import Enum
import json

class SeverityLevel(Enum):
    """Incident severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "info"

class RemediationType(Enum):
    """Type of remediation available."""
    AUTOMATIC = "automatic"  # Can be fixed without approval
    MANUAL = "manual"        # Requires engineer approval
    ESCALATE = "escalate"    # Escalate to NOC

@dataclass
class Incident:
    """Detected incident."""
    id: str
    name: str
    severity: SeverityLevel
    device: str
    symptoms: Dict[str, Any]
    detected_at: datetime
    remediation_type: RemediationType
    likely_causes: List[str]
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "device": self.device,
            "symptoms": self.symptoms,
            "detected_at": self.detected_at.isoformat(),
            "remediation_type": self.remediation_type.value,
            "likely_causes": self.likely_causes
        }

class PatternMatcher:
    """Detect incidents from device metrics and events."""
    
    def __init__(self):
        self.patterns = {}
        self.incident_counter = 0
    
    def register_pattern(
        self,
        name: str,
        check_func: Callable,
        severity: SeverityLevel,
        remediation_type: RemediationType,
        likely_causes: List[str] = None
    ):
        """
        Register pattern to detect.
        
        Args:
            name: Pattern name
            check_func: Function to detect pattern (returns True if found)
            severity: Incident severity
            remediation_type: Type of remediation available
            likely_causes: List of possible root causes
        """
        self.patterns[name] = {
            "check_func": check_func,
            "severity": severity,
            "remediation_type": remediation_type,
            "likely_causes": likely_causes or []
        }
    
    def detect(self, device: str, metrics: Dict) -> List[Incident]:
        """
        Check all patterns against device metrics.
        
        Args:
            device: Device name
            metrics: Device metrics/state
        
        Returns:
            List of detected incidents
        """
        incidents = []
        
        for pattern_name, pattern in self.patterns.items():
            try:
                if pattern["check_func"](metrics):
                    incident = Incident(
                        id=f"INC-{self.incident_counter:05d}",
                        name=pattern_name,
                        severity=pattern["severity"],
                        device=device,
                        symptoms=metrics,
                        detected_at=datetime.now(),
                        remediation_type=pattern["remediation_type"],
                        likely_causes=pattern["likely_causes"]
                    )
                    incidents.append(incident)
                    self.incident_counter += 1
            
            except Exception as e:
                # Log pattern check failure, continue
                print(f"⚠ Pattern '{pattern_name}' check failed: {e}")
        
        return incidents
