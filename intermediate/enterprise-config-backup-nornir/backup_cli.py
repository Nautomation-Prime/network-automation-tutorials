#!/usr/bin/env python3
"""
Enterprise Config Backup CLI
Usage: python backup.py --help
"""

import argparse
import sys
from nornir import InitNornir
from nornir.core.filter import F
from tasks.enterprise_backup import backup_config

def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Configuration Backup System",
        epilog="Examples:\n  python backup.py --group ios_devices\n  python backup.py --filter 'router' --dry-run"
    )
    
    # Positional arguments (required)
    # (none in this example)
    
    # Optional arguments
    parser.add_argument(
        '--host',
        help='Backup specific device by name (e.g., "router1")'
    )
    
    parser.add_argument(
        '--group',
        help='Backup entire device group (e.g., "ios_devices")'
    )
    
    parser.add_argument(
        '--filter',
        help='Filter devices by substring in name (e.g., "router" matches "router1", "router2")'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be backed up without actually backing up'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (-v, -vv, -vvv)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of parallel workers (default: 10)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Connection timeout in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize Nornir
        nr = InitNornir(config_file="nornir_config.yaml")
        
        # Apply filters
        if args.host:
            nr = nr.filter(name=args.host)
        elif args.group:
            nr = nr.filter(F(groups__contains=args.group))
        elif args.filter:
            nr = nr.filter(filter_func=lambda h: args.filter.lower() in h.name.lower())
        
        # Show what will run
        if args.dry_run:
            print(f"DRY RUN: Would backup {len(nr.inventory.hosts)} devices:")
            for host in nr.inventory.hosts.values():
                print(f"  - {host.name} ({host.hostname})")
            return 0
        
        # Confirm with user
        if len(nr.inventory.hosts) == 0:
            print("❌ No devices matched criteria")
            return 1
        
        print(f"✓ Backing up {len(nr.inventory.hosts)} devices...")
        
        # Get password
        import getpass
        password = getpass.getpass("Device password: ")
        
        for host in nr.inventory.hosts.values():
            host.password = password
        
        # Run backup
        results = nr.run(task=backup_config)
        
        # Print summary
        failed = sum(1 for r in results.values() if r.failed)
        succeeded = len(results) - failed
        
        print(f"\n✓ Succeeded: {succeeded}/{len(results)}")
        if failed > 0:
            print(f"✗ Failed: {failed}/{len(results)}")
            for host, result in results.items():
                if result.failed:
                    # backup_config catches its own errors and returns them
                    # in the result, so .exception would be None here
                    print(f"  - {host}: {result[0].result.get('error')}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.verbose >= 2:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
