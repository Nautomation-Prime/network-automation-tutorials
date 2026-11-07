# Advanced Nornir Patterns

Code for the **[Advanced Nornir Patterns](https://www.nautomationprime.io/foundation/tutorials/intermediate/advanced-nornir-patterns/)** lesson on Nautomation Prime.

> Master advanced Nornir patterns for enterprise deployment - custom plugins, middleware, multi-vendor support, memory optimisation, and testing.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_state_across_tasks.py` | Pattern 4: Managing State Across Tasks |
| `02_multi_vendor_support.py` | Pattern 5: Multi-Vendor Support |
| `03_debugging_workflows.py` | Pattern 8: Debugging Complex Workflows |
| `benchmark.py` | Benchmark Your Current System |
| `nornir_config.yaml` | Using the Plugin |
| `middleware/example_middleware.py` | Pattern 2: Middleware for Cross-Cutting Concerns |
| `plugins/netbox_inventory.py` | Solution: Netbox Plugin |
| `tasks/enterprise_backup.py` | copied from [enterprise-config-backup-nornir](https://www.nautomationprime.io/foundation/tutorials/intermediate/enterprise-config-backup-nornir/), which this lesson builds on |
| `tasks/resilient_tasks.py` | Pattern 3: Error Handling with Exponential Backoff |
| `tests/test_tasks.py` | Pattern 7: Testing Nornir Tasks |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/advanced-nornir-patterns/) · [All lessons](../../README.md)
