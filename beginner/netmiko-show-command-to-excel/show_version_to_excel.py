"""
Simple Netmiko Script: Show Version to Excel
Description: Connects to a Cisco device, runs 'show version', and exports to Excel
Author: Nautomation Prime
"""

# Import required libraries
from netmiko import ConnectHandler
import pandas as pd
import getpass

# Define device connection parameters
device = {
    'device_type': 'cisco_ios',           # Device platform
    'host': '192.168.1.1',                 # Device IP address
    'username': 'admin',                   # SSH username
    'password': getpass.getpass('Enter password: '),  # Prompt for password
    'secret': '',                          # Enable password (if needed)
}

# Main script execution
def main():
    """Main function to connect, collect data, and export to Excel"""
    
    print(f"Connecting to {device['host']}...")
    
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        print(f"✓ Connected to {device['host']}")
        
        # Send show command with automatic TextFSM parsing
        print("Executing 'show version'...")
        output = connection.send_command('show version', use_textfsm=True)
        
        # Check if TextFSM parsing was successful
        if isinstance(output, list) and len(output) > 0:
            print(f"✓ Received structured data with {len(output)} row(s)")
            
            # Convert parsed data to pandas DataFrame
            df = pd.DataFrame(output)
            
            # Define output Excel filename
            excel_file = f"{device['host']}_show_version.xlsx"
            
            # Export DataFrame to Excel
            df.to_excel(excel_file, index=False, sheet_name='Show Version')
            print(f"✓ Data exported to: {excel_file}")
            
        else:
            print("⚠ TextFSM parsing failed or returned no data")
            print("Raw output:")
            print(output)
        
        # Close the SSH connection
        connection.disconnect()
        print("✓ Connection closed")
        
    except Exception as e:
        print(f"✗ Error occurred: {str(e)}")

# Script entry point
if __name__ == "__main__":
    main()
