# Circuit Breakers & Backpressure Patterns

Code for the **[Circuit Breakers & Backpressure Patterns](https://www.nautomationprime.io/foundation/tutorials/expert/circuit-breakers-backpressure-network-automation/)** lesson on Nautomation Prime.

> Prevent cascade failures at scale. Circuit breaker pattern, exponential backoff, and graceful degradation for fleet deployments. Enterprise-grade safety.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/backpressure_manager.py` | Pattern 2: Backpressure & Rate Limiting → Implementation with Circuit Breakers |
| `src/circuit_breaker.py` | Pattern 1: Circuit Breaker Implementation → The Implementation |
| `src/graceful_degradation.py` | Pattern 3: Graceful Degradation |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from backpressure_manager import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/expert/circuit-breakers-backpressure-network-automation/) · [All lessons](../../README.md)
