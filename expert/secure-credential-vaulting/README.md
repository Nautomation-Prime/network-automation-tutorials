# Secure Credential Vaulting for Network Automation: HashiCorp Vault, AWS Secrets Manager, and Beyond

Code for the **[Secure Credential Vaulting for Network Automation: HashiCorp Vault, AWS Secrets Manager, and Beyond](https://www.nautomationprime.io/foundation/tutorials/expert/secure-credential-vaulting/)** lesson on Nautomation Prime.

> How to integrate enterprise-grade secrets management into your automation workflows for safety and compliance.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `nornir_vault_integration.py` | Integration with Nornir; Testing Vault Integration |
| `vault_manager.py` | Comprehensive Vault Manager Implementation |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/expert/secure-credential-vaulting/) · [All lessons](../../README.md)
