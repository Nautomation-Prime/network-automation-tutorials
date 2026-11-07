# PyATS Production Patterns

Code for the **[PyATS Production Patterns](https://www.nautomationprime.io/foundation/tutorials/intermediate/building-reliable-automation-with-pyats/)** lesson on Nautomation Prime.

> Integrate PyATS validation into your Netmiko and Nornir automation. Learn production patterns for reliable network changes with measurable ROI proof.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `deploy_and_validate_vlan.py` | The Setup (Nornir + PyATS); Pattern 1: Netmiko + PyATS (Simple Approach) → The Implementation (Nornir + PyATS) |
| `prime_workflow.py` | Example: Complete PRIME Workflow with PyATS |
| `test_vlan_deployment.py` | Testing Your Automation |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/building-reliable-automation-with-pyats/) · [All lessons](../../README.md)
