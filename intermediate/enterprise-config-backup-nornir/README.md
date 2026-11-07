# Enterprise Config Backup

Code for the **[Enterprise Config Backup](https://www.nautomationprime.io/foundation/tutorials/intermediate/enterprise-config-backup-nornir/)** lesson on Nautomation Prime.

> Build a production-grade config backup system with Nornir including database integration, change detection, compliance checking, and reporting.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `backup_cli.py` | Basic CLI with `argparse` |
| `bastion_backup.py` | Jump/Bastion Host Support |
| `check_bastion_path.py` | Testing Bastion Connectivity |
| `check_last_run.py` | Scheduling in Production |
| `enterprise_main.py` | Orchestration Script |
| `init_db.py` | Database Schema |
| `query_backups.py` | Querying the Database |
| `simple_backup.py` | Step 1: Basic Multi-Step Task Pipeline |
| `ssh_tunnel_backup.py` | Pattern 3: SSH Tunneling (Maximum Flexibility) |
| `tasks/enterprise_backup.py` | The Complete Production Script |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/enterprise-config-backup-nornir/) · [All lessons](../../README.md)
