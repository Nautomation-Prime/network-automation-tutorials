# src/remediation.py
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from incident_detector import Incident

@dataclass
class RemediationAction:
    """Single remediation step."""
    name: str
    func: Callable
    validate_func: Optional[Callable] = None  # Verify remediation worked
    undo_func: Optional[Callable] = None      # Reverse this step (None = can't)
    
    async def execute(self) -> bool:
        """Execute remediation and validate."""
        try:
            print(f"  Executing: {self.name}")
            await self.func()
            
            if self.validate_func:
                if await self.validate_func():
                    print(f"  ✓ {self.name} successful")
                    return True
                else:
                    print(f"  ✗ {self.name} validation failed")
                    return False
            
            return True
        
        except Exception as e:
            print(f"  ✗ {self.name} failed: {e}")
            return False

class RemediationRunbook:
    """Define remediation steps for an incident type."""
    
    def __init__(self, incident_name: str):
        self.incident_name = incident_name
        self.actions: List[RemediationAction] = []

    def add_action(
        self,
        name: str,
        func: Callable,
        validate_func: Optional[Callable] = None,
        undo_func: Optional[Callable] = None
    ):
        """Add remediation action. Give an undo_func if the step can be reversed."""
        self.actions.append(RemediationAction(name, func, validate_func, undo_func))
    
    async def execute(self, incident: Incident) -> Dict[str, Any]:
        """
        Execute all remediation actions.
        
        Args:
            incident: Incident to remediate
        
        Returns:
            dict with execution results and success status
        """
        print(f"\n🔧 Remediating: {self.incident_name}")
        print(f"   Device: {incident.device}")
        print(f"   Likely causes: {', '.join(incident.likely_causes)}\n")
        
        results = {
            "incident_id": incident.id,
            "actions_taken": [],
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
        
        attempted = []

        for action in self.actions:
            attempted.append(action)
            success = await action.execute()
            results["actions_taken"].append({
                "name": action.name,
                "success": success
            })

            if not success:
                results["success"] = False
                print(f"\n⚠ Remediation failed at: {action.name}")
                print(f"  Rolling back to previous state...")
                await self._roll_back(attempted)
                break

        return results

    async def _roll_back(self, attempted: List[RemediationAction]):
        """
        Undo the steps that ran, newest first.

        Steps after the failure never ran, so there's nothing to undo for
        them. The failed step is included: it may have half-applied.
        """
        for action in reversed(attempted):
            if action.undo_func is None:
                print(f"  Can't undo: {action.name} (no undo step)")
                continue
            print(f"  Undoing: {action.name}")
            try:
                await action.undo_func()
            except Exception as e:
                # Keep undoing the rest, but never hide a failed undo
                print(f"  ✗ Undo of {action.name} failed: {e}")
