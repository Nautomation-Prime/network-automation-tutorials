# Structured Logging for Network Automation

Code for the **[Structured Logging for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/structured-logging-network-automation/)** lesson on Nautomation Prime.

> Production-grade logging with JSON, log levels, and log aggregation integration. Track what happened, when, and why. Centralized observability for automation.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/audit_logger.py` | Pattern 5: Audit Logging for Compliance |
| `src/contextual_logging.py` | Pattern 2: Contextual Logging Across Operations → Implementation |
| `src/elasticsearch_logger.py` | Sending Logs to Elasticsearch |
| `src/metrics_logger.py` | Pattern 3: Performance Metrics Logging → The Implementation |
| `src/nornir_logging_task.py` | Pattern 2: Contextual Logging Across Operations → Usage with Nornir |
| `src/structured_logger.py` | Pattern 1: Structured Logging Basics → The Implementation |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from audit_logger import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/structured-logging-network-automation/) · [All lessons](../../README.md)
