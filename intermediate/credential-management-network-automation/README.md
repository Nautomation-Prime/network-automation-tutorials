# Credential Management in Network Automation

Code for the **[Credential Management in Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/credential-management-network-automation/)** lesson on Nautomation Prime.

> Secure credential handling for production automation. Master HashiCorp Vault, AWS Secrets Manager, environment variables, and encryption patterns.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `audit_credential_access.py` | 4. Audit Credential Access |
| `encrypted_config_usage.py` | Pattern 5: Encrypted Configuration Files → Usage |
| `vault_nornir.py` | Vault in Nornir Workflows |
| `vault_usage.py` | Pattern 2: HashiCorp Vault (Production Standard) → Usage Example |
| `src/aws_secrets.py` | Pattern 3: AWS Secrets Manager → Implementation |
| `src/azure_keyvault.py` | Pattern 4: Azure Key Vault → Implementation |
| `src/credentials.py` | Pattern 1: Environment Variables (Dev/Small Scale) → Implementation |
| `src/encrypted_config.py` | Pattern 5: Encrypted Configuration Files → Implementation |
| `src/tacacs_preflight.py` | Pattern 6: Central Accounts (TACACS+/RADIUS) → Implementation |
| `src/vault_client.py` | Python Integration |
| `tests/test_credential_management.py` | Testing Credential Management |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/credential-management-network-automation/) · [All lessons](../../README.md)
