#!/usr/bin/env python3
"""
Inventory models and a loader that fails fast with readable errors.
"""

import sys
from typing import Annotated, Literal, Optional

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    ValidationError,
    model_validator,
)

VlanId = Annotated[int, Field(ge=1, le=4094)]


class Vlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: VlanId
    name: Annotated[str, Field(min_length=1, max_length=32)]


class Interface(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    mode: Literal["access", "trunk", "routed", "unused"]
    access_vlan: Optional[VlanId] = None
    ip_address: Optional[IPvAnyAddress] = None
    enabled: bool = True

    @model_validator(mode="after")
    def check_mode_consistency(self):
        # The cross-field rule from "Model validators" below
        if self.mode == "access" and self.access_vlan is None:
            raise ValueError(f"{self.name}: access ports require an access_vlan")
        if self.mode == "routed" and self.ip_address is None:
            raise ValueError(f"{self.name}: routed ports require an ip_address")
        if self.mode == "routed" and self.access_vlan is not None:
            raise ValueError(f"{self.name}: routed ports cannot have an access_vlan")
        return self


class Device(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mgmt_ip: IPvAnyAddress
    platform: Literal["ios", "iosxe", "nxos", "iosxr"]
    role: Literal["core", "distribution", "access", "edge"]
    vlans: list[Vlan] = []
    interfaces: list[Interface] = []


class Inventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site: Annotated[str, Field(pattern=r"^[A-Z]{3}\d$")]
    devices: Annotated[list[Device], Field(min_length=1)]


def load_inventory(path: str) -> Inventory:
    """
    Load and validate an inventory file.

    Exits with a non-zero status and an operator-readable report if the
    file is malformed. Returns a fully typed Inventory on success.
    """
    try:
        with open(path) as handle:
            raw = yaml.safe_load(handle)
    except FileNotFoundError:
        sys.exit(f"✗ Inventory not found: {path}")
    except yaml.YAMLError as exc:
        sys.exit(f"✗ {path} is not valid YAML:\n  {exc}")

    try:
        return Inventory.model_validate(raw)
    except ValidationError as exc:
        print(f"✗ {path} failed validation ({exc.error_count()} problems):\n")
        for err in exc.errors():
            location = " -> ".join(str(part) for part in err["loc"])
            print(f"  {location}")
            print(f"      {err['msg']}")
            print(f"      you supplied: {err['input']!r}\n")
        sys.exit(1)


if __name__ == "__main__":
    inventory = load_inventory("inventory.yaml")
    print(f"✓ {inventory.site}: {len(inventory.devices)} devices validated")
    for device in inventory.devices:
        print(f"  {device.name:<16} {device.mgmt_ip}  {device.platform}")
