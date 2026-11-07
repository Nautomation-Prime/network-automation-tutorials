# Error Recovery & Rollback Patterns

Code for the **[Error Recovery & Rollback Patterns](https://www.nautomationprime.io/foundation/tutorials/intermediate/error-recovery-rollback-network-automation/)** lesson on Nautomation Prime.

> Safe network changes with automated rollback. Capture pre-state, validate post-state, and automatically undo failures. Production-grade deployment patterns.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/capture_state_example.py` | Pattern 1: State Capture & Comparison → Usage Example |
| `src/deploy.py` | Pattern 3: Automatic Rollback → Production Usage |
| `src/nornir_rollback_task.py` | Pattern 4: Nornir Integration with Rollback |
| `src/rollback.py` | Pattern 3: Automatic Rollback → The Implementation |
| `src/state_management.py` | Pattern 1: State Capture & Comparison → The Implementation |
| `src/validation.py` | Pattern 2: Validation-Driven Rollback → The Implementation |
| `tests/test_rollback.py` | 5. Test Rollback Procedures |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from capture_state_example import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/error-recovery-rollback-network-automation/) · [All lessons](../../README.md)
