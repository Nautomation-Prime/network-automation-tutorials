#!/usr/bin/env python3
"""
Nested models: a device with interfaces and VLANs.
"""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, IPvAnyAddress

VlanId = Annotated[int, Field(ge=1, le=4094)]


class Vlan(BaseModel):
    id: VlanId
    name: Annotated[str, Field(min_length=1, max_length=32)]


class Interface(BaseModel):
    name: str
    description: str = ""                      # default — optional in the data
    mode: Literal["access", "trunk", "routed", "unused"]
    access_vlan: Optional[VlanId] = None
    ip_address: Optional[IPvAnyAddress] = None
    enabled: bool = True


class Device(BaseModel):
    name: str
    mgmt_ip: IPvAnyAddress
    platform: Literal["ios", "iosxe", "nxos", "iosxr"]
    vlans: list[Vlan] = []
    interfaces: list[Interface] = []


device = Device(
    name="access-sw-01",
    mgmt_ip="10.1.1.3",
    platform="iosxe",
    vlans=[
        {"id": 10, "name": "USERS"},
        {"id": 20, "name": "VOICE"},
    ],
    interfaces=[
        {"name": "GigabitEthernet1/0/1", "mode": "access", "access_vlan": 10},
        {"name": "GigabitEthernet1/0/2", "mode": "unused", "enabled": False},
    ],
)

print(device.vlans[0].name)              # USERS — typed all the way down
print(len(device.interfaces))            # 2
