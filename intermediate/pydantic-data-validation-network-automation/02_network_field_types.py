#!/usr/bin/env python3
"""
A device model using network-aware types.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, IPvAnyAddress, IPvAnyNetwork

# A VLAN ID is an integer between 1 and 4094 — say so once, reuse everywhere
VlanId = Annotated[int, Field(ge=1, le=4094)]


class Device(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=63)]
    mgmt_ip: IPvAnyAddress
    mgmt_net: IPvAnyNetwork
    platform: Literal["ios", "iosxe", "nxos", "iosxr"]
    mtu: Annotated[int, Field(ge=1500, le=9216)]
    native_vlan: VlanId


device = Device(
    name="core-sw-01",
    mgmt_ip="10.1.1.1",
    mgmt_net="10.1.1.0/24",
    platform="iosxe",
    mtu=9216,
    native_vlan=999,
)

print(type(device.mgmt_ip))          # <class 'ipaddress.IPv4Address'>
print(device.mgmt_ip in device.mgmt_net)   # True — real network maths


from pydantic import ValidationError

for bad in [
    {"mgmt_ip": "10.1.1.300"},   # invalid octet
    {"platform": "iso"},          # transposed platform
    {"native_vlan": 5000},        # out of range
    {"mtu": 68},                  # below the floor
]:
    payload = {
        "name": "test-sw", "mgmt_ip": "10.1.1.1", "mgmt_net": "10.1.1.0/24",
        "platform": "iosxe", "mtu": 1500, "native_vlan": 10,
    }
    payload.update(bad)
    try:
        Device(**payload)
    except ValidationError as e:
        print(f"{list(bad)[0]}: {e.errors()[0]['msg']}")
