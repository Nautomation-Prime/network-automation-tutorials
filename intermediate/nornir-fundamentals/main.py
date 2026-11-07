"""
Main script to run Nornir backup tasks
"""

import os
import sys
import getpass
from datetime import datetime
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from tasks.backup import backup_running_config, save_config_to_file

def main():
    """Main function to orchestrate backup"""
    
    print("=" * 70)
    print("Nornir Multi-Device Configuration Backup")
    print("=" * 70)
    
    # Get password
    device_password = getpass.getpass('Enter device password: ')
    
    try:
        # Initialize Nornir from config file
        nornir = InitNornir(config_file="nornir_config.yaml")
        
        # Update passwords in inventory
        for host in nornir.inventory.hosts.values():
            host.password = device_password
        
        print(f"\n✓ Loaded {len(nornir.inventory.hosts)} device(s) from inventory\n")
        
        # Create timestamped backup directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"configs/{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        print(f"✓ Created backup directory: {backup_dir}\n")
        
        # Run backup task on all devices in parallel
        print(f"{'=' * 70}")
        print("Executing parallel backups...\n")
        
        # Task 1: Retrieve configs from all devices (in parallel)
        backup_results = nornir.run(
            task=backup_running_config,
            name="Backup Running Configs"
        )
        
        # Task 2: Process results and save configs
        print(f"\n{'=' * 70}")
        print("Processing results and saving to files...\n")
        
        file_results = nornir.run(
            task=save_config_to_file,
            config_data={
                host_name: backup_results[host_name][0].result
                for host_name in backup_results.keys()
            },
            backup_dir=backup_dir
        )
        
        # Summary
        print(f"\n{'=' * 70}")
        print("BACKUP SUMMARY")
        print(f"{'=' * 70}")
        print(f"Backup Location: {backup_dir}")
        
        # Count successes and failures
        successful = sum(
            1 for result in backup_results.values() 
            if result[0].result.get('status') == 'success'
        )
        failed = len(backup_results) - successful
        
        print(f"Successful Backups: {successful}/{len(nornir.inventory.hosts)}")
        print(f"Failed Backups: {failed}/{len(nornir.inventory.hosts)}")
        print(f"{'=' * 70}")
        
        # Show backed-up devices
        if successful > 0:
            print("\nBacked Up Devices:")
            for host_name, result in backup_results.items():
                if result[0].result.get('status') == 'success':
                    size = result[0].result.get('size', 0)
                    print(f"  ✓ {host_name}: {size:,} bytes")
        
        if failed > 0:
            print("\nFailed Devices:")
            for host_name, result in backup_results.items():
                if result[0].result.get('status') != 'success':
                    status = result[0].result.get('status', 'unknown')
                    print(f"  ✗ {host_name}: {status}")
        
        print()

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
