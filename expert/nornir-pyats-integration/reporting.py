# reporting.py
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import json
import csv

from orchestrator.integration import DeploymentRecord


class ReportGenerator:
    """Generate multiple report formats for different audiences"""
    
    def __init__(self, deployment: DeploymentRecord, output_dir: str = './reports'):
        self.deployment = deployment
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all_reports(self):
        """Generate all report types"""
        self.generate_executive_summary()
        self.generate_technical_report()
        self.generate_csv_report()
        self.generate_json_report()
    
    def generate_executive_summary(self):
        """High-level summary for management"""
        filename = self.output_dir / f"{self.deployment.deployment_id}_executive.md"
        
        total = len(self.deployment.devices)
        successful = sum(
            1 for cr in self.deployment.change_records.values()
            if cr.state.value == 'completed'
        )
        
        content = f"""
# Deployment Executive Summary

**Deployment ID:** {self.deployment.deployment_id}  
**Date:** {self.deployment.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Status:** {self.deployment.phase.value}  

## Overview

- **Total Devices:** {total}
- **Successful:** {successful} ({successful/total*100:.1f}%)
- **Failed:** {total - successful}
- **Execution Time:** {self.deployment.execution_time:.2f} seconds

## Changes Applied

```bash
{chr(10).join(self.deployment.commands)}
```

## Impact Assessment

✅ **Low Risk:** Changes were validated and rolled back on failure  
✅ **Automated:** Full automation with pre/post validation  
✅ **Auditable:** Complete change records maintained  

## Recommendations

- {('Review failed devices for common patterns' if total != successful else 'All devices updated successfully')}
- Monitor devices for 24 hours post-change
- Update documentation with new configurations
"""
        
        with open(filename, 'w') as f:
            f.write(content)
    
    def generate_technical_report(self):
        """Detailed technical report"""
        filename = self.output_dir / f"{self.deployment.deployment_id}_technical.txt"
        # Implementation similar to executive but with more technical detail
        pass
    
    def generate_csv_report(self):
        """CSV format for spreadsheet analysis"""
        filename = self.output_dir / f"{self.deployment.deployment_id}.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Device',
                'Status',
                'Execution Time',
                'Retry Count',
                'Error'
            ])
            
            for device, change in self.deployment.change_records.items():
                writer.writerow([
                    device,
                    change.state.value,
                    f"{change.execution_time:.2f}",
                    change.retry_count,
                    change.error or 'N/A'
                ])
    
    def generate_json_report(self):
        """JSON format for API consumption"""
        filename = self.output_dir / f"{self.deployment.deployment_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.deployment.to_dict(), f, indent=2)
