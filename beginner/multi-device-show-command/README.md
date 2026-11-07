# Multi-Device Show Commands

Code for the **[Multi-Device Show Commands](https://www.nautomationprime.io/foundation/tutorials/beginner/multi-device-show-command/)** lesson on Nautomation Prime.

> Build on Tutorial #1 to collect show commands from multiple Cisco devices using CSV inventory and export to Excel with per-device error handling.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `devices.csv` | Step 1: Create the Inventory CSV |
| `multi_device_show_version.py` | The Complete Script |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/beginner/multi-device-show-command/) · [All lessons](../../README.md)
