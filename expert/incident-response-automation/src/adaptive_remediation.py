# src/adaptive_remediation.py
from typing import List
from incident_tracker import IncidentTracker
from remediation import RemediationRunbook

class AdaptiveRemediationEngine:
    """Learn from incident history and adjust remediation."""
    
    def __init__(self, tracker: IncidentTracker):
        self.tracker = tracker
        self.success_rates = {}
    
    def calculate_success_rate(self, remediation_name: str) -> float:
        """Calculate success rate of remediation type."""
        incidents = self.tracker.get_incident_history()
        
        total = 0
        successful = 0
        
        for record in incidents:
            if record["type"] == "remediation_executed":
                for action in record["result"].get("actions_taken", []):
                    if action["name"] == remediation_name:
                        total += 1
                        if action["success"]:
                            successful += 1
        
        if total == 0:
            return 0.0
        
        return (successful / total) * 100
    
    def select_remediation_strategy(
        self,
        incident_name: str,
        available_strategies: List[RemediationRunbook]
    ) -> RemediationRunbook:
        """
        Select best remediation based on historical success.
        
        Args:
            incident_name: Type of incident
            available_strategies: Possible remediation approaches
        
        Returns:
            Best remediation strategy based on history
        """
        strategy_scores = {}
        
        for strategy in available_strategies:
            success_rate = self.calculate_success_rate(strategy.incident_name)
            strategy_scores[strategy.incident_name] = success_rate
        
        # Return strategy with highest success rate
        best_strategy = max(
            available_strategies,
            key=lambda s: strategy_scores.get(s.incident_name, 0)
        )
        
        print(f"Selected strategy: {best_strategy.incident_name} "
              f"(success rate: {strategy_scores[best_strategy.incident_name]:.1f}%)")
        
        return best_strategy
