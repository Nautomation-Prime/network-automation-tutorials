import re

from pydantic import BaseModel, field_validator

HOSTNAME_PATTERN = re.compile(r"^[a-z]{3}\d-(core|dist|acc)-sw-\d{2}$")


class Device(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def enforce_naming_standard(cls, value: str) -> str:
        if not HOSTNAME_PATTERN.match(value):
            raise ValueError(
                f"'{value}' does not match the naming standard "
                "<site><n>-<role>-sw-<nn>, e.g. man1-core-sw-01"
            )
        return value
