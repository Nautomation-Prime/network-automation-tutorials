import json
import math

data = {'value': math.nan}

# This will fail in strict JSON mode
try:
    json.dumps(data, allow_nan=False)
except ValueError as e:
    print(f"Error: {e}")

# Solution: Convert NaN to None or string
data = {'value': None if math.isnan(data['value']) else data['value']}
json.dumps(data)  # Works
