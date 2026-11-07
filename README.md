# Network Automation Tutorials — Companion Code

Working code for every lesson in the
[Nautomation Prime Academy tutorials](https://www.nautomationprime.io/foundation/tutorials/): one folder per lesson,
holding the scripts, templates and data files the lesson builds.

The capstone project has its own repo, with a checkpoint for every chapter:
[netpipe-capstone](https://github.com/Nautomation-Prime/netpipe-capstone).

## Build it first, then compare

Each lesson explains its code line by line, and you'll learn more by typing it
than by downloading it. Use this repo to check your work when something
doesn't run, to grab the data files and templates so you can focus on the
Python, or to see the finished result before you start.

## Get the code

```bash
git clone https://github.com/Nautomation-Prime/network-automation-tutorials.git
cd network-automation-tutorials/beginner/netmiko-show-command-to-excel
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No git? Use **Code → Download ZIP** on GitHub and open the lesson's folder.
Each folder has its own `README.md` and `requirements.txt`.

> **Use a lab.** Lessons that connect to devices need equipment you're allowed
> to change: CML, EVE-NG, GNS3, a Cisco DevNet sandbox, or spare switches on a
> bench. Never run a tutorial against production.

## Beginner

| Lesson | Code | Some files need |
|---|---|---|
| [Show Command to Excel](https://www.nautomationprime.io/foundation/tutorials/beginner/netmiko-show-command-to-excel/) | [`beginner/netmiko-show-command-to-excel/`](beginner/netmiko-show-command-to-excel/) | lab devices |
| [Multi-Device Show Commands](https://www.nautomationprime.io/foundation/tutorials/beginner/multi-device-show-command/) | [`beginner/multi-device-show-command/`](beginner/multi-device-show-command/) | lab devices |
| [Multi-Device Configuration Backup](https://www.nautomationprime.io/foundation/tutorials/beginner/multi-device-config-backup/) | [`beginner/multi-device-config-backup/`](beginner/multi-device-config-backup/) | lab devices |

## Intermediate

| Lesson | Code | Some files need |
|---|---|---|
| [Nornir Fundamentals](https://www.nautomationprime.io/foundation/tutorials/intermediate/nornir-fundamentals/) | [`intermediate/nornir-fundamentals/`](intermediate/nornir-fundamentals/) | lab devices |
| [YAML Data Modelling for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/yaml-data-modeling-network-automation/) | [`intermediate/yaml-data-modeling-network-automation/`](intermediate/yaml-data-modeling-network-automation/) | lab devices |
| [JSON Data Handling for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/json-data-handling-network-automation/) | [`intermediate/json-data-handling-network-automation/`](intermediate/json-data-handling-network-automation/) | lab devices and an API or secrets service |
| [Pydantic Data Validation for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/pydantic-data-validation-network-automation/) | [`intermediate/pydantic-data-validation-network-automation/`](intermediate/pydantic-data-validation-network-automation/) | an API or secrets service |
| [Jinja2 Configuration Templates for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/jinja2-configuration-templates/) | [`intermediate/jinja2-configuration-templates/`](intermediate/jinja2-configuration-templates/) | nothing: it all runs offline |
| [Decorators in Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/decorators-network-automation/) | [`intermediate/decorators-network-automation/`](intermediate/decorators-network-automation/) | lab devices |
| [Structured Logging for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/structured-logging-network-automation/) | [`intermediate/structured-logging-network-automation/`](intermediate/structured-logging-network-automation/) | lab devices and an API or secrets service |
| [Credential Management in Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/credential-management-network-automation/) | [`intermediate/credential-management-network-automation/`](intermediate/credential-management-network-automation/) | lab devices and an API or secrets service |
| [Testing Network Automation Scripts](https://www.nautomationprime.io/foundation/tutorials/intermediate/testing-network-automation/) | [`intermediate/testing-network-automation/`](intermediate/testing-network-automation/) | nothing: it all runs offline |
| [State Management & Idempotency](https://www.nautomationprime.io/foundation/tutorials/intermediate/state-management-idempotency-network-automation/) | [`intermediate/state-management-idempotency-network-automation/`](intermediate/state-management-idempotency-network-automation/) | lab devices |
| [Error Recovery & Rollback Patterns](https://www.nautomationprime.io/foundation/tutorials/intermediate/error-recovery-rollback-network-automation/) | [`intermediate/error-recovery-rollback-network-automation/`](intermediate/error-recovery-rollback-network-automation/) | lab devices |
| [Health Checks & Pre-Flight Validation](https://www.nautomationprime.io/foundation/tutorials/intermediate/health-checks-pre-flight-validation/) | [`intermediate/health-checks-pre-flight-validation/`](intermediate/health-checks-pre-flight-validation/) | lab devices |
| [Enterprise Config Backup](https://www.nautomationprime.io/foundation/tutorials/intermediate/enterprise-config-backup-nornir/) | [`intermediate/enterprise-config-backup-nornir/`](intermediate/enterprise-config-backup-nornir/) | lab devices |
| [Advanced Nornir Patterns](https://www.nautomationprime.io/foundation/tutorials/intermediate/advanced-nornir-patterns/) | [`intermediate/advanced-nornir-patterns/`](intermediate/advanced-nornir-patterns/) | lab devices and an API or secrets service |
| [PyATS Fundamentals](https://www.nautomationprime.io/foundation/tutorials/intermediate/pyats-fundamentals/) | [`intermediate/pyats-fundamentals/`](intermediate/pyats-fundamentals/) | lab devices |
| [PyATS Network Validation](https://www.nautomationprime.io/foundation/tutorials/intermediate/pyats-network-validation/) | [`intermediate/pyats-network-validation/`](intermediate/pyats-network-validation/) | lab devices |
| [PyATS Production Patterns](https://www.nautomationprime.io/foundation/tutorials/intermediate/building-reliable-automation-with-pyats/) | [`intermediate/building-reliable-automation-with-pyats/`](intermediate/building-reliable-automation-with-pyats/) | lab devices |

## Expert

| Lesson | Code | Some files need |
|---|---|---|
| [Asyncio for Network Automation](https://www.nautomationprime.io/foundation/tutorials/expert/asyncio-network-automation/) | [`expert/asyncio-network-automation/`](expert/asyncio-network-automation/) | lab devices and an API or secrets service |
| [Circuit Breakers & Backpressure Patterns](https://www.nautomationprime.io/foundation/tutorials/expert/circuit-breakers-backpressure-network-automation/) | [`expert/circuit-breakers-backpressure-network-automation/`](expert/circuit-breakers-backpressure-network-automation/) | nothing: it all runs offline |
| [Dependency Management & Task Orchestration](https://www.nautomationprime.io/foundation/tutorials/expert/dependency-ordering-task-orchestration/) | [`expert/dependency-ordering-task-orchestration/`](expert/dependency-ordering-task-orchestration/) | lab devices |
| [DevOps and Observability for Network Automation](https://www.nautomationprime.io/foundation/tutorials/expert/devops-observability-network-automation/) | [`expert/devops-observability-network-automation/`](expert/devops-observability-network-automation/) | nothing: it all runs offline |
| [Incident Response Automation](https://www.nautomationprime.io/foundation/tutorials/expert/incident-response-automation/) | [`expert/incident-response-automation/`](expert/incident-response-automation/) | lab devices |
| [Secure Credential Vaulting for Network Automation](https://www.nautomationprime.io/foundation/tutorials/expert/secure-credential-vaulting/) | [`expert/secure-credential-vaulting/`](expert/secure-credential-vaulting/) | lab devices and an API or secrets service |
| [Tool Ecosystem Integration for Network Automation](https://www.nautomationprime.io/foundation/tutorials/expert/tool-ecosystem-integration/) | [`expert/tool-ecosystem-integration/`](expert/tool-ecosystem-integration/) | an API or secrets service |
| [Nornir + PyATS Integration](https://www.nautomationprime.io/foundation/tutorials/expert/nornir-pyats-integration/) | [`expert/nornir-pyats-integration/`](expert/nornir-pyats-integration/) | lab devices and an API or secrets service |

## How this repo is checked

No lesson here is tested against real devices, because CI has none. Every
lesson is checked every week and on every change:

- every YAML, JSON and Jinja2 file parses
- every import resolves, the way you'd run the lesson (from its folder, or
  from `src/` where the lesson keeps its modules there)
- every script that doesn't need a device or an API runs to completion
- each lesson's own tests pass, apart from the PyATS lessons, whose tests
  need a live testbed
- the beginner scripts run end to end against a fake Netmiko connection

Run the same checks yourself:

```bash
pip install ruff pytest
cat */*/requirements.txt | sort -u > /tmp/all-requirements.txt
pip install -r /tmp/all-requirements.txt
ruff check --select E9,F63,F7,F82 .
pytest tests/
python scripts/check_lessons.py
```

Found something that doesn't work? Open an issue with the lesson name and
the error.

## Licence

Apache 2.0. See [LICENSE](LICENSE). Use it, adapt it, and run it at work.
