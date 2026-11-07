#!/usr/bin/env python3
"""
Render device configuration from a validated model.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from models import load_inventory

env = Environment(
    loader=FileSystemLoader("templates"),
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,   # unknown variable = error, not blank
)

inventory = load_inventory("inventory.yaml")
template = env.get_template("switch.j2")
Path("output").mkdir(exist_ok=True)

for device in inventory.devices:
    config = template.render(device=device, site=inventory.site)
    with open(f"output/{device.name}.cfg", "w") as handle:
        handle.write(config)
    print(f"✓ rendered output/{device.name}.cfg")
