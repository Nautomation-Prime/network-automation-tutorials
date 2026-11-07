"""
Multi-Device Netmiko Script: Show Version to Excel
Description: Connects to multiple Cisco devices from CSV inventory and exports to Excel
Author: Nautomation Prime
"""

# Import required libraries
from netmiko import ConnectHandler
import pandas as pd
import getpass
import csv

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
                    'secret': row.get('secret', ''),  # Optional enable password
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

def collect_from_device(device):
    """
    Connect to a single device and collect show version data
    
    Args:
        device: Dictionary with connection parameters
        
    Returns:
        Tuple of (hostname, dataframe) or (hostname, None) on error
    """
    hostname = device['host']
    
    try:
        print(f"  Connecting to {hostname}...")
        connection = ConnectHandler(**device)
        
        # Send show command with TextFSM parsing
        output = connection.send_command('show version', use_textfsm=True)
        
        # Check if parsing was successful
        if isinstance(output, list) and len(output) > 0:
            df = pd.DataFrame(output)
            connection.disconnect()
            print(f"  ✓ Success: {hostname} - {len(output)} row(s) collected")
            return (hostname, df)
        else:
            connection.disconnect()
            print(f"  ⚠ Warning: {hostname} - TextFSM parsing returned no data")
            return (hostname, None)
            
    except Exception as e:
        print(f"  ✗ Failed: {hostname} - {str(e)}")
        return (hostname, None)

def main():
    """Main function to orchestrate multi-device collection"""
    
    # Define inventory file
    inventory_file = 'devices.csv'
    
    print("=" * 60)
    print("Multi-Device Show Version Collection")
    print("=" * 60)
    
    # Read device inventory
    devices = read_inventory(inventory_file)
    
    if not devices:
        print("No devices to process. Exiting.")
        return
    
    # Collect data from all devices
    print(f"\nCollecting data from {len(devices)} device(s)...\n")
    
    results = {}
    for device in devices:
        hostname, df = collect_from_device(device)
        if df is not None:
            results[hostname] = df
    
    # Export results to Excel
    if results:
        excel_file = 'multi_device_show_version.xlsx'
        
        print(f"\n{'=' * 60}")
        print(f"Exporting to Excel: {excel_file}")
        
        # Create Excel writer object
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            for hostname, df in results.items():
                # Excel sheet names have a 31-character limit
                sheet_name = hostname[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"  ✓ Sheet created: {sheet_name}")
        
        print(f"\n✓ Successfully exported {len(results)} device(s) to {excel_file}")
        print(f"{'=' * 60}")
    else:
        print("\n✗ No data collected. No Excel file created.")

# Script entry point
if __name__ == "__main__":
    main()
