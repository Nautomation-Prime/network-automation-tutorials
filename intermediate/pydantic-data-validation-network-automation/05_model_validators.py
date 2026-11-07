from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class Interface(BaseModel):
    name: str
    mode: Literal["access", "trunk", "routed", "unused"]
    access_vlan: Optional[int] = None
    ip_address: Optional[str] = None

    @model_validator(mode="after")
    def check_mode_consistency(self):
        if self.mode == "access" and self.access_vlan is None:
            raise ValueError(f"{self.name}: access ports require an access_vlan")
        if self.mode == "routed" and self.ip_address is None:
            raise ValueError(f"{self.name}: routed ports require an ip_address")
        if self.mode == "routed" and self.access_vlan is not None:
            raise ValueError(f"{self.name}: routed ports cannot have an access_vlan")
        return self
