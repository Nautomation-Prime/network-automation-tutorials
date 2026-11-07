"""
Multi-Device Configuration Backup Script
Description: Backs up running configs from multiple Cisco devices with timestamps and manifest
Author: Nautomation Prime
"""

# Import required libraries
from netmiko import ConnectHandler
import pandas as pd
import getpass
import csv
import os
from datetime import datetime

# Get password once (used for all devices)
device_password = getpass.getpass('Enter device password: ')

def read_inventory(csv_file):
    """
    Read device inventory from CSV file
    
    Args:
        csv_file: Path to CSV file containing device information
        
    Returns:
        List of device dictionaries ready for Netmiko
    """
    devices = []
    
    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                device = {
                    'device_type': row['device_type'],
                    'host': row['host'],
                    'username': row['username'],
                    'password': device_password,
                    'secret': row.get('secret', ''),
                }
                devices.append(device)
        
        print(f"✓ Loaded {len(devices)} device(s) from {csv_file}")
        return devices
        
    except FileNotFoundError:
        print(f"✗ Error: Could not find file '{csv_file}'")
        return []
    except KeyError as e:
        print(f"✗ Error: Missing required column in CSV: {e}")
        return []

def create_backup_directory(base_directory='backups'):
    """
    Create a timestamped backup directory
    
    Args:
        base_directory: Parent directory for backups (default: 'backups')
        
    Returns:
        Path to the created timestamp directory
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(base_directory, timestamp)
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"✓ Created backup directory: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"✗ Error creating backup directory: {e}")
        return None

def backup_device_config(device, backup_dir):
    """
    Connect to a device and backup its running configuration
    
    Args:
        device: Dictionary with connection parameters
        backup_dir: Directory where backups will be stored
        
    Returns:
        Tuple of (hostname, config_filename, file_size, status) or (hostname, None, 0, 'failed')
    """
    hostname = device['host']
    device_type = device['device_type']
    
    try:
        print(f"  Connecting to {hostname} ({device_type})...")
        connection = ConnectHandler(**device)
        if device.get('secret'):
            connection.enable()
        
        # Get running configuration
        print(f"    Retrieving running configuration...")
        config = connection.send_command('show running-config')
        
        # Verify we got data
        if isinstance(config, str) and len(config) > 0:
            # Create safe filename: replace dots with dashes in IP addresses
            safe_hostname = hostname.replace('.', '-')
            config_filename = f"{safe_hostname}_running-config.txt"
            config_filepath = os.path.join(backup_dir, config_filename)
            
            # Write configuration to file
            with open(config_filepath, 'w') as f:
                f.write(config)
            
            # Get file size to confirm write
            file_size = os.path.getsize(config_filepath)
            
            connection.disconnect()
            print(f"  ✓ Success: {hostname} - {file_size} bytes backed up")
            return (hostname, config_filename, file_size, 'success')
        else:
            connection.disconnect()
            print(f"  ⚠ Warning: {hostname} - No configuration data received")
            return (hostname, None, 0, 'no-data')
            
    except Exception as e:
        print(f"  ✗ Failed: {hostname} - {str(e)}")
        return (hostname, None, 0, 'failed')

def create_backup_manifest(backup_dir, results):
    """
    Create an Excel manifest of all backup operations
    
    Args:
        backup_dir: Directory containing backups
        results: List of backup operation results
        
    Returns:
        Path to created manifest file
    """
    # Prepare data for manifest
    manifest_data = []
    
    for hostname, filename, size, status in results:
        manifest_data.append({
            'Device IP': hostname,
            'Backup File': filename if filename else 'N/A',
            'File Size (bytes)': size,
            'Status': status,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Create DataFrame
    df = pd.DataFrame(manifest_data)
    
    # Write to Excel
    manifest_filename = 'backup_manifest.xlsx'
    manifest_filepath = os.path.join(backup_dir, manifest_filename)
    
    try:
        df.to_excel(manifest_filepath, index=False, sheet_name='Backup Manifest')
        print(f"\n✓ Manifest created: {manifest_filename}")
        return manifest_filepath
    except Exception as e:
        print(f"✗ Error creating manifest: {e}")
        return None

def main():
    """Main function to orchestrate multi-device backup"""
    
    # Define settings
    inventory_file = 'devices.csv'
    base_backup_dir = 'backups'
    
    print("=" * 70)
    print("Multi-Device Configuration Backup")
    print("=" * 70)
    
    # Read device inventory
    devices = read_inventory(inventory_file)
    
    if not devices:
        print("No devices to process. Exiting.")
        return
    
    # Create timestamped backup directory
    backup_dir = create_backup_directory(base_backup_dir)
    
    if not backup_dir:
        print("Failed to create backup directory. Exiting.")
        return
    
    # Backup configurations from all devices
    print(f"\nBacking up {len(devices)} device(s)...\n")
    
    results = []
    successful_backups = 0
    failed_backups = 0
    
    for device in devices:
        hostname, filename, size, status = backup_device_config(device, backup_dir)
        results.append((hostname, filename, size, status))
        
        if status == 'success':
            successful_backups += 1
        else:
            failed_backups += 1
    
    # Create backup manifest
    print(f"\n{'=' * 70}")
    create_backup_manifest(backup_dir, results)
    
    # Print summary
    print(f"\n{'=' * 70}")
    print("BACKUP SUMMARY")
    print(f"{'=' * 70}")
    print(f"Backup Location: {backup_dir}")
    print(f"Successful Backups: {successful_backups}/{len(devices)}")
    print(f"Failed Backups: {failed_backups}/{len(devices)}")
    print(f"{'=' * 70}\n")
    
    if successful_backups > 0:
        print("Backed Up Devices:")
        for hostname, filename, size, status in results:
            if status == 'success':
                print(f"  ✓ {hostname}: {filename} ({size:,} bytes)")
    
    if failed_backups > 0:
        print("\nFailed Devices:")
        for hostname, filename, size, status in results:
            if status != 'success':
                print(f"  ✗ {hostname}: {status}")

# Script entry point
if __name__ == "__main__":
    main()
