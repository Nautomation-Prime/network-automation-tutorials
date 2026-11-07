from netmiko import ConnectHandler
from pyats.topology import loader
from pyats.utils.secret_strings import to_plaintext

# Load testbed (devices, credentials)
testbed = loader.load('testbed.yaml')

# Credentials come from the testbed (%ENV / %ENC secrets, resolved on load)
device = testbed.devices['switch-01']
device.connect(via='cli')
creds = device.credentials['default']

# Netmiko for configuration (faster, simpler syntax).
# Netmiko needs plain strings: the testbed IP is an ipaddress object and
# the password a SecretString.
net_connect = ConnectHandler(
    device_type='cisco_ios',
    host=str(device.connections.cli.ip),
    username=creds['username'],
    password=to_plaintext(creds['password']),
)

# PyATS for validation (structured parsing)
# (already connected via device.connect())


def deploy_and_validate_vlan(testbed_file, device_name, vlan_config):
    """
    Deploy VLAN configuration and validate immediately
    Real-world function that combines Netmiko + PyATS
    
    Args:
        testbed_file: Path to testbed.yaml (e.g., 'testbed.yaml')
        device_name: Device name from testbed (e.g., 'switch-01')
        vlan_config: List of dicts with vlan_id, name, interfaces
                     Example: [{'id': 100, 'name': 'PROD', 'interfaces': [...]}, ...]
    
    Returns:
        dict: Validation results showing passed/failed checks
    """
    
    from pyats.topology import loader
    from pyats.utils.secret_strings import to_plaintext
    from netmiko import ConnectHandler

    # Load testbed — reads device definitions and credentials from YAML
    testbed = loader.load(testbed_file)
    
    # Get device from testbed by name
    device = testbed.devices[device_name]
    # device now has all connection info (IP, credentials, etc.)
    
    # ========== STEP 1: CAPTURE BASELINE ==========
    print(f"[1/4] Capturing baseline...")
    
    # Connect to device for reading state (PyATS)
    device.connect()
    # Opens SSH connection using credentials from testbed.yaml
    
    # Capture VLAN state BEFORE deployment
    baseline_vlans = set(device.parse('show vlan')['vlans'].keys())
    # .parse() returns dict, ['vlans'] gets vlans section, .keys() gets VLAN IDs
    # set() converts to set of VLAN IDs (like {'1', '10', '20'})
    
    device.disconnect()
    # Close connection — we'll reconnect for validation later
    
    print(f"      Baseline: {len(baseline_vlans)} VLANs exist")
    # Show baseline count for debugging
    
    # ========== STEP 2: DEPLOY CONFIGURATION ==========
    print(f"[2/4] Deploying VLAN configuration...")
    
    try:
        # Connect via Netmiko for configuration deployment
        # Netmiko is optimized for sending config commands
        creds = device.credentials['default']
        net_connect = ConnectHandler(
            device_type='cisco_ios',
            # Device OS type (tells Netmiko how to communicate)

            host=str(device.connections.cli.ip),
            # Get device IP from PyATS device object
            # device.connections.cli is the SSH connection config;
            # .ip is an ipaddress object, so convert it to a string

            username=creds['username'],
            password=to_plaintext(creds['password']),
            # Reuse the testbed's credentials (the password is a SecretString)
            
            timeout=20,
            # Timeout for device responses (seconds)
        )
        
        # Build list of configuration commands
        config_commands = []
        
        # For each VLAN in config, create vlan and name commands
        for vlan in vlan_config:
            # vlan is dict: {'id': 100, 'name': 'PROD', ...}
            
            config_commands.extend([
                # .extend() adds multiple items to list (unlike .append())
                
                f"vlan {vlan['id']}",
                # Create VLAN command (e.g., "vlan 100")
                
                f"name {vlan['name']}",
                # Name the VLAN (e.g., "name PROD")
            ])
            # Both commands work together: first creates VLAN, second names it
        
        # Send configuration to device
        output = net_connect.send_config_set(config_commands)
        # .send_config_set() enters config mode, sends the list, and exits
        # output contains device responses
        
        # Gracefully close connection
        net_connect.disconnect()
        
        print(f"      Configuration sent successfully")
        # Configuration deployed — now we validate
        
    except Exception as e:
        # Catch any errors during deployment
        print(f"      ❌ Configuration failed: {e}")
        # Print error details
        
        raise
        # Re-raise exception so caller knows deployment failed
    
    # ========== STEP 3: VALIDATE CONFIGURATION ==========
    print(f"[3/4] Validating configuration...")
    
    # Reconnect for validation (reading state via PyATS)
    device.connect()
    
    # Initialize results dict to track passed/failed validations
    validation_results = {
        'passed': 0,
        # Count of validation checks that passed
        
        'failed': 0,
        # Count of validation checks that failed
        
        'details': [],
        # List of validation messages (one per VLAN)
    }
    
    # Validate each VLAN that we tried to create
    for vlan in vlan_config:
        # vlan is dict: {'id': 100, 'name': 'PROD', ...}
        
        vlan_id = str(vlan['id'])
        # Convert VLAN ID to string (parsing returns string keys)
        
        # Parse current state after deployment
        vlan_data = device.parse('show vlan')
        # Get fresh vlan data (will include newly created VLANs)
        
        # ===== CHECK 1: VLAN EXISTS =====
        if vlan_id not in vlan_data['vlans']:
            # VLAN ID not found in parsed output
            # This means configuration failed to create the VLAN
            
            validation_results['failed'] += 1
            # Increment failed counter
            
            validation_results['details'].append(
                f"❌ VLAN {vlan_id} not found"
                # Add failure message
            )
            
            continue
            # Skip remaining checks for this VLAN and move to next
        
        # ===== CHECK 2: VLAN HAS CORRECT NAME =====
        actual_name = vlan_data['vlans'][vlan_id]['name']
        # Get the name attribute from parsed VLAN data
        
        expected_name = vlan['name']
        # Get expected name from our config
        
        if actual_name != expected_name:
            # VLAN exists but name doesn't match
            # This indicates partial failure
            
            validation_results['failed'] += 1
            validation_results['details'].append(
                f"❌ VLAN {vlan_id} name mismatch: "
                f"expected '{expected_name}', got '{actual_name}'"
            )
            
            continue
            # Skip remaining checks for this VLAN
        
        # ===== CHECK 3: VLAN IS ACTIVE =====
        status = vlan_data['vlans'][vlan_id]['state']
        # Genie calls this field 'state' (should be 'active')
        
        if status != 'active':
            # VLAN exists but is suspended or down
            
            validation_results['failed'] += 1
            validation_results['details'].append(
                f"❌ VLAN {vlan_id} status not active: {status}"
            )
            
            continue
            # Skip remaining checks
        
        # ===== ALL CHECKS PASSED FOR THIS VLAN =====
        validation_results['passed'] += 1
        # Increment passed counter (all 3 checks passed)
        
        validation_results['details'].append(
            f"✅ VLAN {vlan_id} ({expected_name}): deployed and active"
            # Success message with VLAN details
        )
    
    device.disconnect()
    # Close PyATS connection
    
    # ========== STEP 4: REPORT RESULTS ==========
    print(f"[4/4] Validation results...")
    
    # Print each validation message
    for detail in validation_results['details']:
        print(f"      {detail}")
    
    # Print summary
    total = validation_results['passed'] + validation_results['failed']
    # Total validations = passed + failed
    
    print(f"\n      Result: {validation_results['passed']}/{total} validations passed")
    # Show pass rate (e.g., "3/3 validations passed")
    
    if validation_results['failed'] > 0:
        raise AssertionError(
            f"Validation failed: {validation_results['failed']} checks did not pass"
        )
    
    return validation_results

# Usage
vlan_config = [
    {'id': 100, 'name': 'PROD-DATA'},
    {'id': 101, 'name': 'PROD-VOICE'},
    {'id': 102, 'name': 'PROD-VIDEO'},
]

results = deploy_and_validate_vlan('testbed.yaml', 'switch-01', vlan_config)
print(f"✅ All {results['passed']} VLANs deployed and validated")
