import pytest
from pyats.topology import loader

@pytest.fixture
def device_with_timeout(testbed):
    """Connect with timeout handling"""
    device = testbed.devices['slow_switch']
    
    try:
        device.connect(connection_timeout=30)  # give up after 30 seconds
        yield device
    except Exception as e:
        pytest.fail(f"Failed to connect to device: {e}")
    finally:
        try:
            device.disconnect()
        except:
            pass  # Connection already closed or never opened

def test_with_retry(device_with_timeout):
    """Retry parsing if device is slow"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            vlan_data = device_with_timeout.parse('show vlan')
            break  # Success
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                pytest.fail(f"Failed after {max_retries} retries: {e}")
            print(f"⚠️  Retry {retry_count}/{max_retries}")


def test_with_graceful_fallback(device):
    """
    Validate routing even if BGP isn't configured
    """
    
    # Try to get BGP data, but don't fail if not available
    bgp_data = None
    try:
        bgp_data = device.parse('show ip bgp summary')
    except Exception:
        print("⚠️  BGP not configured on this device")
    
    # Validate routing (always available)
    routes = device.parse('show ip route')
    assert routes is not None, "No routing table?"
    
    # Optional: validate BGP only if available
    if bgp_data:
        neighbors = bgp_data['vrf']['default']['neighbor']
        assert len(neighbors) > 0, "BGP neighbors not established"
    
    print("✅ Validation passed")
