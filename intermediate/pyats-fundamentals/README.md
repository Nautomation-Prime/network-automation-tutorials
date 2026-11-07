# PyATS Fundamentals

Code for the **[PyATS Fundamentals](https://www.nautomationprime.io/foundation/tutorials/intermediate/pyats-fundamentals/)** lesson on Nautomation Prime.

> Learn PyATS (Python API for Test Automation System), Cisco's enterprise-grade framework used for millions of automated tests monthly. Build reliable network validation.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_device_parsing.py` | 2. Device Parsing |
| `02_before_after.py` | Step 1: Baseline (Before Automation); Step 2: Run Automation |
| `03_test_connection.py` | Step 4: Test Connection |
| `test_interface_configuration.py` | The Test |
| `test_vlans.py` | 3. Test Structure |
| `testbed.yaml` | Step 2: Create Testbed File |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/pyats-fundamentals/) · [All lessons](../../README.md)
