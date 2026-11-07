# src/incident_tracker.py
import json
from datetime import datetime
from pathlib import Path
from typing import List
from incident_detector import Incident

class IncidentTracker:
    """Track incidents and remediation history."""
    
    def __init__(self, history_file: str = "incidents.jsonl"):
        self.history_file = Path(history_file)
    
    def record_incident(self, incident: Incident):
        """Log detected incident."""
        with open(self.history_file, "a") as f:
            record = {
                "type": "incident_detected",
                "timestamp": datetime.now().isoformat(),
                "incident": incident.to_dict()
            }
            f.write(json.dumps(record) + "\n")
    
    def record_remediation(self, incident_id: str, result: dict):
        """Log remediation attempt."""
        with open(self.history_file, "a") as f:
            record = {
                "type": "remediation_executed",
                "timestamp": datetime.now().isoformat(),
                "incident_id": incident_id,
                "result": result
            }
            f.write(json.dumps(record) + "\n")
    
    def get_incident_history(self, device: str = None) -> List[dict]:
        """Get incident history for device."""
        if not self.history_file.exists():
            return []
        
        incidents = []
        with open(self.history_file, "r") as f:
            for line in f:
                record = json.loads(line)
                
                # Filter by device if specified
                if device and record["type"] == "incident_detected":
                    if record["incident"]["device"] != device:
                        continue
                
                incidents.append(record)
        
        return incidents
    
    def get_mttr(self, days: int = 7) -> float:
        """
        Calculate Mean Time To Repair.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Average repair time in minutes
        """
        incidents = self.get_incident_history()
        
        incident_times = {}
        for record in incidents:
            if record["type"] == "incident_detected":
                incident_id = record["incident"]["id"]
                incident_times[incident_id] = {
                    "detected": record["timestamp"]
                }
            
            elif record["type"] == "remediation_executed":
                incident_id = record["incident_id"]
                if incident_id in incident_times:
                    incident_times[incident_id]["remediated"] = record["timestamp"]
        
        # Calculate repair time for incidents with remediation
        repair_times = []
        for inc_id, times in incident_times.items():
            if "remediated" in times:
                detected = datetime.fromisoformat(times["detected"])
                remediated = datetime.fromisoformat(times["remediated"])
                repair_time = (remediated - detected).total_seconds() / 60
                repair_times.append(repair_time)
        
        if repair_times:
            return sum(repair_times) / len(repair_times)
        return 0
