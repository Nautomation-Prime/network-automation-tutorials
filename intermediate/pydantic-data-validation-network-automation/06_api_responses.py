#!/usr/bin/env python3
"""
Validate a controller's device inventory response.
"""

from typing import Literal

import requests
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, ValidationError


class ControllerDevice(BaseModel):
    # Controllers add fields between releases — ignore what we don't model
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    hostname: str
    management_ip: IPvAnyAddress = Field(alias="managementIpAddress")
    platform: str = Field(alias="platformId")
    reachability: Literal["Reachable", "Unreachable", "Ping Reachable"] = Field(
        alias="reachabilityStatus"
    )
    # "upTime" is display text ("47 days, 3:55:02.33"); this is the number
    uptime_seconds: int = Field(alias="uptimeSeconds", default=0)


class ControllerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    response: list[ControllerDevice]


def fetch_devices(base_url: str, token: str) -> list[ControllerDevice]:
    reply = requests.get(
        f"{base_url}/dna/intent/api/v1/network-device",
        headers={"X-Auth-Token": token},
        timeout=30,
    )
    reply.raise_for_status()

    try:
        parsed = ControllerResponse.model_validate_json(reply.text)
    except ValidationError as exc:
        raise RuntimeError(
            f"Controller returned data we don't understand:\n{exc}"
        ) from exc

    return parsed.response
