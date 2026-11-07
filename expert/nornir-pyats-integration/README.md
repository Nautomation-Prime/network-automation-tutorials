# Nornir + PyATS Integration: Enterprise-Grade Automation and Validation

Code for the **[Nornir + PyATS Integration: Enterprise-Grade Automation and Validation](https://www.nautomationprime.io/foundation/tutorials/expert/nornir-pyats-integration/)** lesson on Nautomation Prime.

> Combine Nornir's parallel execution with PyATS validation for production-ready, scalable network automation.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `async_orchestration.py` | 3. Async/Await Pattern for Maximum Performance |
| `batching.py` | 2. Batching Strategies for Large-Scale Deployments |
| `change_windows.py` | 4. Change Window Management |
| `connection_pool.py` | 1. Connection Pooling and Lifecycle Management |
| `error_handling.py` | Comprehensive Error Handling Strategy |
| `inventory_manager.py` | Production-Grade NetBox Integration |
| `logging_config.py` | Advanced Logging Configuration |
| `main.py` | Production-Ready Implementation |
| `reporting.py` | Reporting Framework |
| `run_config_deployment.py` | Integration with Nornir Inventory |
| `observability/metrics.py` | Comprehensive Observability Stack |
| `orchestrator/integration.py` | The Full Stack: Nornir + PyATS Working Together |
| `security/credential_vault.py` | Enterprise Security Architecture |
| `tasks/config_management.py` | Production-Grade Task Structure |
| `tests/test_orchestration.py` | Comprehensive Testing Pyramid |
| `validation/pyats_validator.py` | Beyond Simple Parsing: Genie Learn Features |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/expert/nornir-pyats-integration/) · [All lessons](../../README.md)
