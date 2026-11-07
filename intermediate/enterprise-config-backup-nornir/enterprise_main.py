"""
Enterprise Configuration Backup System
Parallel execution with change detection and compliance checking
"""

import os
import sys
import getpass
from datetime import datetime
from nornir import InitNornir
import sqlite3
import tabulate
from tasks.enterprise_backup import (
    backup_config,
    save_config,
    detect_changes,
    compliance_check,
    generate_report
)

def main():
    """Main orchestration function"""
    
    print("=" * 70)
    print("Enterprise Configuration Backup System")
    print("=" * 70)
    
    # Get password
    device_password = getpass.getpass('Enter device password: ')
    
    try:
        # Initialize Nornir
        nornir = InitNornir(config_file="nornir_config.yaml")
        
        # Update passwords
        for host in nornir.inventory.hosts.values():
            host.password = device_password
        
        print(f"✓ Loaded {len(nornir.inventory.hosts)} devices\n")
        
        # ================================================================
        # STAGE 1: Backup Configurations (Parallel)
        # ================================================================
        print(f"{'=' * 70}")
        print("STAGE 1: Retrieving Configurations")
        print(f"{'=' * 70}\n")
        
        backup_results = nornir.run(
            task=backup_config,
            name="Backup Configurations"
        )
        
        # Extract config data for next stages
        config_data = {}
        for device_name, result in backup_results.items():
            if result[0].result.get('success'):
                config_data[device_name] = result[0].result
            else:
                config_data[device_name] = None
        
        # ================================================================
        # STAGE 2: Save Configurations (Parallel)
        # ================================================================
        print(f"\n{'=' * 70}")
        print("STAGE 2: Saving Configurations & Creating Database Records")
        print(f"{'=' * 70}\n")

        # on_failed=True: Nornir skips hosts that failed an earlier run
        # unless told otherwise. Every stage must still produce a result
        # for every host (the tasks handle a missing config themselves),
        # or stage 5's lookups by host name raise KeyError.
        save_results = nornir.run(
            task=save_config,
            config_data=config_data,
            backup_dir="enterprise_configs",
            db_file="backup.db",
            on_failed=True
        )
        
        # ================================================================
        # STAGE 3: Detect Changes (Parallel)
        # ================================================================
        print(f"\n{'=' * 70}")
        print("STAGE 3: Detecting Configuration Changes")
        print(f"{'=' * 70}\n")
        
        changes_results = nornir.run(
            task=detect_changes,
            current_config={
                device_name: config_data[device_name]['config']
                if config_data[device_name] else None
                for device_name in config_data.keys()
            },
            db_file="backup.db",
            on_failed=True
        )

        # ================================================================
        # STAGE 4: Compliance Checking (Parallel)
        # ================================================================
        print(f"\n{'=' * 70}")
        print("STAGE 4: Running Compliance Checks")
        print(f"{'=' * 70}\n")
        
        compliance_results = nornir.run(
            task=compliance_check,
            config={
                device_name: config_data[device_name]['config']
                if config_data[device_name] else ""
                for device_name in config_data.keys()
            },
            db_file="backup.db",
            on_failed=True
        )
        
        # ================================================================
        # STAGE 5: Generate Summary Report
        # ================================================================
        print(f"\n{'=' * 70}")
        print("STAGE 5: Generating Summary Report")
        print(f"{'=' * 70}\n")
        
        # Aggregate all results for reporting
        all_aggregated = {}
        for device_name in nornir.inventory.hosts.keys():
            all_aggregated[device_name] = {
                'backup_config': backup_results[device_name][0].result,
                'save_config': save_results[device_name][0].result,
                'detect_changes': changes_results[device_name][0].result,
                'compliance_check': compliance_results[device_name][0].result,
            }
        
        report_results = nornir.run(
            task=generate_report,
            all_results={
                device_name: all_aggregated[device_name]
                for device_name in nornir.inventory.hosts.keys()
            },
            on_failed=True
        )

        for device_name, result in report_results.items():
            print(result[0].result.get('report', ''))
        
        # ================================================================
        # PRINT FINAL SUMMARY
        # ================================================================
        print(f"\n{'=' * 70}")
        print("FINAL SUMMARY")
        print(f"{'=' * 70}\n")
        
        # Database analysis
        conn = sqlite3.connect("backup.db")
        cursor = conn.cursor()
        
        # Summary table
        summary_data = []
        for device_name in nornir.inventory.hosts.keys():
            config_success = backup_results[device_name][0].result.get('success', False)
            save_success = save_results[device_name][0].result.get('success', False)
            
            if compliance_results[device_name][0].result.get('success'):
                compliance = f"{compliance_results[device_name][0].result['score']}/100"
            else:
                compliance = "n/a"

            changed = changes_results[device_name][0].result.get('changed', False)
            if not config_success:
                status = "n/a"
            else:
                status = "Changed" if changed else "Same"

            summary_data.append([
                device_name,
                "✓" if config_success else "✗",
                "✓" if save_success else "✗",
                status,
                compliance
            ])
        
        headers = ["Device", "Config Retrieved", "Saved", "Status", "Compliance"]
        print(tabulate.tabulate(summary_data, headers=headers, tablefmt="grid"))
        
        # Statistics
        successful = sum(1 for d in summary_data if d[1] == "✓")
        changed_count = sum(1 for d in summary_data if d[3] == "Changed")
        scores = [int(d[4].split('/')[0]) for d in summary_data if d[4] != "n/a"]

        print(f"\nSuccessful Backups: {successful}/{len(nornir.inventory.hosts)}")
        print(f"Changed Configs: {changed_count}/{len(nornir.inventory.hosts)}")
        if scores:
            print(f"Average Compliance: {sum(scores) / len(scores):.1f}/100 "
                  f"(across {len(scores)} devices checked)")
        
        print(f"\n✓ Backup database: backup.db")
        print(f"✓ Config files: enterprise_configs/")
        
        conn.close()

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
