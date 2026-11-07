# Multi-Device Configuration Backup

Code for the **[Multi-Device Configuration Backup](https://www.nautomationprime.io/foundation/tutorials/beginner/multi-device-config-backup/)** lesson on Nautomation Prime.

> Build on Tutorial #2 to automatically backup running configurations from multiple Cisco devices with timestamped filenames, organised by device type.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `backup_running_configs.py` | The Complete Script |
| `devices.csv` | Step 1: Create the Inventory CSV |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/beginner/multi-device-config-backup/) · [All lessons](../../README.md)
