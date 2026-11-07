def test_access_port_compliance(device):
    """
    Validate: All access ports must be in VLAN 10 (DATA)
    Except: Port Et1/48 which should be in VLAN 20 (MGMT)
    
    This pattern proves that your VLAN configuration matches requirements
    """
    
    # Parse VLAN data — returns structured dict of all VLANs and their ports
    vlan_data = device.parse('show vlan')
    
    # Define REQUIRED configuration: which ports MUST be in which VLANs
    required_config = {
        '10': ['Ethernet1/1', 'Ethernet1/2', 'Ethernet1/3', 'Ethernet1/4'],
        # VLAN 10 must have these 4 ports (DATA VLAN)
        
        '20': ['Ethernet1/48'],
        # VLAN 20 must have this 1 port (MGMT VLAN)
    }
    
    # For each VLAN in required config, validate all ports are there
    for vlan_id, required_ports in required_config.items():
        # Get actual ports in this VLAN from device parsing
        actual_ports = vlan_data['vlans'][vlan_id]['interfaces']
        # vlan_data['vlans'][vlan_id] gets VLAN's dict
        # ['interfaces'] gets the list of interface names in this VLAN
        
        # Validate: all required ports are actually there
        for port in required_ports:
            # Check each required port
            assert port in actual_ports, \
                f"{port} missing from VLAN {vlan_id}!"
            # If port not found, assertion fails with error message
        
        # Also warn about UNEXPECTED ports (ports that shouldn't be there)
        unexpected = set(actual_ports) - set(required_ports)
        # set() creates set of port names
        # actual_ports - required_ports gives ports in actual but not required
        
        if unexpected:
            # Print warning about extra ports (not required, but not harmful)
            print(f"⚠️  Warning: Unexpected ports in VLAN {vlan_id}: {unexpected}")
            # This warns ops team but doesn't fail test
    
    print("✅ VLAN compliance check passed")
    # All assertions passed = all ports are correctly assigned


def test_interface_health(device, expected_up_count=48):
    """
    Validate: Expected number of interfaces are operational
    Also Check: No disabled ports, no down ports, no errors
    
    This pattern proves infrastructure is healthy after deployment
    """
    
    # Parse show interfaces — get detailed data for every interface
    interfaces = device.parse('show interfaces')
    
    # Initialize counters to track interface status
    interfaces_up = 0
    # Count how many interfaces are operationally up
    
    interfaces_errors = 0
    # Count interfaces with errors (input or output errors)
    
    interfaces_down = []
    # List of interface names that are down
    
    # Iterate through all interfaces on device
    for iface_name, iface_data in interfaces.items():
        # iface_name examples: 'Ethernet1/1', 'Ethernet1/2'
        # iface_data is dict with all interface properties
        
        # Skip loopbacks and management interfaces (not data ports)
        if 'Loopback' in iface_name or 'Management' in iface_name:
            continue
            # Skip these interface types — we're only checking data ports
        
        # Count how many are operationally up
        if iface_data.get('oper_status') == 'up':
            # .get() safely accesses dict key (returns None if missing)
            interfaces_up += 1
            # Increment counter if interface is up
        else:
            # Interface is NOT up (down, testing, etc.)
            interfaces_down.append(iface_name)
            # Add to list of down interfaces for reporting
        
        # Check for error counters (indicates hardware or line problems)
        input_errors = iface_data.get('counters', {}).get('in_errors', 0)
        # Get input error count from counters dict (default 0 if missing)
        
        output_errors = iface_data.get('counters', {}).get('out_errors', 0)
        # Get output error count (default 0 if missing)
        
        # Warn if either error counter is non-zero
        if input_errors > 0 or output_errors > 0:
            interfaces_errors += 1
            # Increment error counter
            
            print(f"⚠️  {iface_name}: errors detected (in:{input_errors}, out:{output_errors})")
            # Print warning with error details
    
    # Run assertions — fail test if any condition not met
    
    # Assertion 1: Minimum number of interfaces must be up
    assert interfaces_up >= expected_up_count, \
        f"Expected {expected_up_count} interfaces up, got {interfaces_up}"
        # Shows expected vs actual in error message
    
    # Assertion 2: No interfaces should have errors
    assert interfaces_errors == 0, \
        f"Found {interfaces_errors} interfaces with errors"
    
    # Assertion 3: All expected interfaces should be up (none down)
    assert len(interfaces_down) == 0, \
        f"Expected all interfaces up, but these are down: {interfaces_down}"
        # List the down interfaces in error message
    
    print(f"✅ Interface health check passed ({interfaces_up} interfaces up)")
    # All assertions passed = infrastructure is healthy


def test_critical_routes(device):
    """
    Validate: Critical routes exist and are reachable
    
    This pattern proves your network topology changes worked
    """
    
    routes = device.parse('show ip route')
    
    required_routes = [
        '10.0.0.0/8',      # Corporate network
        '192.168.0.0/16',  # Management network
        '172.16.0.0/12',   # WAN network
    ]
    
    route_table = routes['vrf']['default']['address_family']['ipv4']['routes']
    available_routes = list(route_table.keys())
    
    for required in required_routes:
        assert required in available_routes, \
            f"Critical route {required} not found in routing table!"
        
        route_info = route_table[required]
        print(f"✅ Route {required} exists")
    
    print("✅ Routing validation passed")


def test_bgp_neighbors(device):
    """
    Validate: All BGP neighbors are established
    """
    
    bgp = device.parse('show ip bgp summary')
    
    # Get neighbors
    neighbors = bgp['vrf']['default']['neighbor']
    
    required_neighbors = {
        '10.0.1.1': 'Primary ISP peer',
        '10.0.2.1': 'Secondary ISP peer',
        '192.168.1.2': 'Internal peer',
    }

    for neighbor_ip, role in required_neighbors.items():
        actual_neighbor = neighbors.get(neighbor_ip, {})
        # 'show ip bgp summary' reports one address family, keyed ''
        af_data = actual_neighbor.get('address_family', {}).get('', {})
        state_or_prefixes = af_data.get('state_pfxrcd', 'Down')
        
        assert state_or_prefixes.isdigit(), \
            f"BGP neighbor {neighbor_ip} ({role}): not established, got {state_or_prefixes}"
        
        # Check message counts
        messages_received = af_data.get('msg_rcvd', 0)
        assert messages_received > 0, \
            f"BGP neighbor {neighbor_ip}: no messages received!"
        
        print(f"✅ BGP neighbor {neighbor_ip}: {state_or_prefixes} prefixes ({messages_received} messages)")
    
    print("✅ BGP validation passed")
