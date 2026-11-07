# Health Checks & Pre-Flight Validation

Code for the **[Health Checks & Pre-Flight Validation](https://www.nautomationprime.io/foundation/tutorials/intermediate/health-checks-pre-flight-validation/)** lesson on Nautomation Prime.

> Validate devices before deployment. Pre-flight checks prevent bad configurations from reaching production. Safe deployment starts with validation.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/config_backup.py` | Pattern 2: Configuration Backup Before Deployment → The Implementation |
| `src/health_checks.py` | Pattern 1: Device Health Checks → The Implementation |
| `src/nornir_preflight_tasks.py` | Pattern 3: Nornir Pre-Flight Tasks |
| `src/run_health_checks.py` | Pattern 1: Device Health Checks → Usage |
| `src/sanity_tests.py` | Pattern 4: Sanity Tests After Deployment → The Implementation |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from config_backup import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/health-checks-pre-flight-validation/) · [All lessons](../../README.md)
