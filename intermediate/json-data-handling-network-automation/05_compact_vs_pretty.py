#!/usr/bin/env python3
"""
Compare compact and pretty-printed JSON
"""

import json

data = {'hostname': 'router1', 'ip': '10.1.1.1', 'vlans': [10, 20, 30]}

# Compact (for APIs and storage efficiency)
compact = json.dumps(data, separators=(',', ':'))
print(f"Compact ({len(compact)} bytes):")
print(compact)

# Pretty (for humans)
pretty = json.dumps(data, indent=2)
print(f"\nPretty ({len(pretty)} bytes):")
print(pretty)
