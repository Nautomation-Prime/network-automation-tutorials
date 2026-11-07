import pytest
from pydantic import ValidationError
from models import Interface


def test_access_port_requires_vlan():
    with pytest.raises(ValidationError, match="require an access_vlan"):
        Interface(name="Gi1/0/1", mode="access")


def test_routed_port_rejects_access_vlan():
    with pytest.raises(ValidationError, match="cannot have an access_vlan"):
        Interface(name="Gi1/0/1", mode="routed", ip_address="10.1.1.1", access_vlan=10)
