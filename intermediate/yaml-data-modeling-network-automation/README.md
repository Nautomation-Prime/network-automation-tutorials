# YAML Data Modelling for Network Automation

Code for the **[YAML Data Modelling for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/yaml-data-modeling-network-automation/)** lesson on Nautomation Prime.

> Master YAML for network automation - device inventories, configuration templates, and structured data. Learn syntax, best practices, and real-world patterns.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_load_yaml.py` | Basic YAML Loading |
| `02_complex_structures.py` | Handling Complex Structures |
| `03_write_yaml.py` | Creating YAML from Python Data |
| `04_nornir_inventory.py` | Using Nornir Inventory in Python |
| `05_pyats_testbed.py` | Using PyATS Testbed in Python |
| `06_configuration_data.py` | Using Configuration Data in Python |
| `07_validate_yaml.py` | Validation Script |
| `defaults.yaml` | defaults.yaml |
| `devices.yaml` | What is YAML? |
| `groups.yaml` | groups.yaml |
| `hosts.yaml` | hosts.yaml |
| `inventory/defaults.yaml` | inventory/defaults.yaml |
| `inventory/groups.yaml` | inventory/groups.yaml |
| `inventory/hosts.yaml` | inventory/hosts.yaml |
| `scripts/load_inventory.py` | scripts/load_inventory.py |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/yaml-data-modeling-network-automation/) · [All lessons](../../README.md)
