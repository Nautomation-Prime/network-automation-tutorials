# Incident Response Automation

Code for the **[Incident Response Automation](https://www.nautomationprime.io/foundation/tutorials/expert/incident-response-automation/)** lesson on Nautomation Prime.

> Detect, remediate, and recover from network incidents automatically. Pattern matching, self-healing networks, and incident tracking. Enterprise-grade automation.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/adaptive_remediation.py` | Pattern 4: Adaptive Response Based on History |
| `src/automation_engine.py` | Production Deployment Example |
| `src/incident_detector.py` | Pattern 1: Event Detection Engine → The Implementation |
| `src/incident_tracker.py` | Pattern 3: Incident Tracking & History |
| `src/patterns.py` | Pattern Registration Examples |
| `src/remediation.py` | Pattern 2: Automatic Remediation Engine |
| `src/remediation_runbooks.py` | Remediation Runbook Examples |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from adaptive_remediation import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/expert/incident-response-automation/) · [All lessons](../../README.md)
