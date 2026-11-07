# Jinja2 Configuration Templates for Network Automation

Code for the **[Jinja2 Configuration Templates for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/jinja2-configuration-templates/)** lesson on Nautomation Prime.

> Master Jinja2 templating for Cisco network automation - generate configurations dynamically from data. Learn syntax, filters, inheritance, and production patterns.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_basic_rendering.py` | Basic Template Rendering |
| `02_templates_from_files.py` | Loading Templates from Files |
| `03_custom_filters.py` | 4. Custom Filters |
| `acl_data.yaml` | ACL Data (acl_data.yaml) |
| `check_templates.py` | Template Testing Script |
| `device_data.yaml` | sample data added for the repo (not shown on the page) |
| `generate_configs.py` | generate_configs.py |
| `generate_vlan_config.py` | Generate Script (generate_vlan_config.py) |
| `vlan_data.yaml` | VLAN Data (vlan_data.yaml) |
| `data/devices.yaml` | devices.yaml |
| `data/global_settings.yaml` | global_settings.yaml |
| `templates/acl_config.j2` | ACL Template (templates/acl_config.j2) |
| `templates/base_config.j2` | 1. Template Inheritance |
| `templates/router_config.j2` | Templates |
| `templates/switch_config.j2` | Templates |
| `templates/vlan_config.j2` | VLAN Template (templates/vlan_config.j2) |
| `test_data/router_test.yaml` | sample data added for the repo (not shown on the page) |
| `test_data/switch_test.yaml` | sample data added for the repo (not shown on the page) |
| `test_data/vlan_test.yaml` | sample data added for the repo (not shown on the page) |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/jinja2-configuration-templates/) · [All lessons](../../README.md)
