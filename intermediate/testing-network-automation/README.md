# Testing Network Automation Scripts

Code for the **[Testing Network Automation Scripts](https://www.nautomationprime.io/foundation/tutorials/intermediate/testing-network-automation/)** lesson on Nautomation Prime.

> Master pytest, mocking, and test patterns for reliable network automation. Test decorators, business logic, and device interactions safely without hardware.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/decorators.py` | Testing @retry Decorator |
| `src/device_ops.py` | Testing Device Operations |
| `tests/conftest.py` | The Problem |
| `tests/test_decorators.py` | Pattern 1: Testing Decorators |
| `tests/test_device_ops.py` | Pattern 2: Testing Business Logic with Mocks |
| `tests/test_integration.py` | Testing Decorator Composition |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/testing-network-automation/) · [All lessons](../../README.md)
