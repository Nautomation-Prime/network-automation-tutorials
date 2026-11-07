#!/usr/bin/env python3
"""
A minimal device model.
"""

from pydantic import BaseModel, ValidationError


class Device(BaseModel):
    name: str
    hostname: str
    platform: str
    mtu: int


# Valid data — this works
device = Device(
    name="core-sw-01",
    hostname="10.1.1.1",
    platform="ios",
    mtu=1500,
)

print(device)
print(device.name)     # attribute access, not device['name']
print(device.mtu + 1)  # a real int — arithmetic just works
