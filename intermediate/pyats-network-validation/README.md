# PyATS Network Validation

Code for the **[PyATS Network Validation](https://www.nautomationprime.io/foundation/tutorials/intermediate/pyats-network-validation/)** lesson on Nautomation Prime.

> Master PyATS device parsing, testbed configuration, and validation patterns. Learn how to capture network state and validate automation changes in production.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_what_parsing_returns.py` | What PyATS Parsing Actually Returns; Deep Dive: Device Parsing |
| `real_world_challenges.py` | Challenge 1: Device Connection Timeouts; Challenge 2: Incomplete Device Data |
| `test_before_after.py` | Before/After Pattern (Complete Example) |
| `test_multi_device.py` | Pattern: Multi-Device Validation; Pattern: Validate Configuration Consistency Across Devices |
| `testbed.yaml` | Challenge 3: Credential Management |
| `validation_patterns.py` | Pattern 1: Configuration Compliance Check; Pattern 2: Interface Health Check; Pattern 3: Routing Validation; Pattern 4: BGP Neighbor Validation |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

PyATS runs on Linux and macOS only. On Windows, use [WSL](https://learn.microsoft.com/windows/wsl/install).

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/pyats-network-validation/) · [All lessons](../../README.md)
