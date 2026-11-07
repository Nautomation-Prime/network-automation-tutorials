# Pydantic Data Validation for Network Automation

Code for the **[Pydantic Data Validation for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/pydantic-data-validation-network-automation/)** lesson on Nautomation Prime.

> Use Pydantic v2 BaseModel to turn untrusted YAML, JSON and API data into typed, validated Python objects before your automation touches a device.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_first_model.py` | Your First Model |
| `02_network_field_types.py` | Network-Native Field Types |
| `03_nested_models.py` | Nested Models |
| `04_field_validators.py` | Field validators — one field at a time |
| `05_model_validators.py` | Model validators — rules that span fields |
| `06_api_responses.py` | Validating API Responses |
| `07_settings_and_secrets.py` | Bonus: Settings and Credentials |
| `inventory.yaml` | Validating a YAML Inventory |
| `models.py` | Validating a YAML Inventory |
| `render_switch.py` | Handing a Validated Model to Jinja2 |
| `test_models.py` | 5. Test your models |
| `templates/switch.j2` | Handing a Validated Model to Jinja2 |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/pydantic-data-validation-network-automation/) · [All lessons](../../README.md)
