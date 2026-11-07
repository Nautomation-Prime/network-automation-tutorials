# Nornir Fundamentals

Code for the **[Nornir Fundamentals](https://www.nautomationprime.io/foundation/tutorials/intermediate/nornir-fundamentals/)** lesson on Nautomation Prime.

> Master Nornir's core concepts - inventory management, task creation, parallel execution, and result processing with complete working examples.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `main.py` | File 6: main.py |
| `minimal_example.py` | Minimal Example: Ping 3 Devices in Parallel |
| `nornir_config.yaml` | File 1: nornir_config.yaml |
| `verify_commands.py` | Test 3: Test Command Execution |
| `verify_reachability.py` | Test 2: Verify Device Reachability |
| `inventory/defaults.yaml` | File 2: inventory/defaults.yaml |
| `inventory/groups.yaml` | File 3: inventory/groups.yaml |
| `inventory/hosts.yaml` | File 4: inventory/hosts.yaml |
| `tasks/backup.py` | File 5: tasks/backup.py |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/nornir-fundamentals/) · [All lessons](../../README.md)
