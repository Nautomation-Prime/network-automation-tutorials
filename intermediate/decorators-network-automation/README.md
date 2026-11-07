# Decorators in Network Automation

Code for the **[Decorators in Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/decorators-network-automation/)** lesson on Nautomation Prime.

> Master Python decorators for production network automation. Build retry logic, logging, error handling, rate limiting, and monitoring—all patterns proven in enterprise environments.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_decorator_basics.py` | What is a Decorator? |
| `02_retry.py` | Pattern 1: Automatic Retry with Exponential Backoff → The Implementation; Pattern 1: Automatic Retry with Exponential Backoff → Real-World Usage |
| `03_audit_logging.py` | Pattern 2: Audit Logging for Compliance → The Implementation |
| `04_error_handling.py` | Pattern 3: Error Handling and Recovery → The Implementation; Pattern 3: Error Handling and Recovery → Real-World Usage |
| `05_rate_limiting.py` | Pattern 4: Rate Limiting → The Implementation |
| `06_performance_monitoring.py` | Pattern 5: Performance Monitoring → The Implementation |
| `07_functools_wraps.py` | 1. Always Use `functools.wraps` |
| `08_documented_decorators.py` | 3. Document Decorator Parameters; 5. Test Decorators Independently |
| `09_production_grade.py` | 6. Make Decorators Production-Grade; Problem: Decorator Doesn't Seem to Work |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/decorators-network-automation/) · [All lessons](../../README.md)
