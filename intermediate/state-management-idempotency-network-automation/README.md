# State Management & Idempotency

Code for the **[State Management & Idempotency](https://www.nautomationprime.io/foundation/tutorials/intermediate/state-management-idempotency-network-automation/)** lesson on Nautomation Prime.

> Build repeatable, safe automations. Run the same script multiple times without breaking things. Idempotent operations and state tracking for reliable automation.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/01_not_idempotent.py` | The Problem: Non-Idempotent Operations |
| `src/02_idempotent.py` | The Solution: Idempotent Operations |
| `src/idempotent_operations.py` | Pattern 1: Check-Before-Change → The Implementation |
| `src/idempotent_usage.py` | Pattern 1: Check-Before-Change → Usage Example |
| `src/nornir_idempotent_tasks.py` | Pattern 3: Nornir with Idempotent Tasks |
| `src/state_driver.py` | Pattern 2: State-Driven Configuration → Implementation |
| `tests/test_idempotent_operations.py` | 4. Test Idempotency Explicitly |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from idempotent_operations import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/state-management-idempotency-network-automation/) · [All lessons](../../README.md)
