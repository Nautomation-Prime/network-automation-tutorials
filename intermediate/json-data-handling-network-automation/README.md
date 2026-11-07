# JSON Data Handling for Network Automation

Code for the **[JSON Data Handling for Network Automation](https://www.nautomationprime.io/foundation/tutorials/intermediate/json-data-handling-network-automation/)** lesson on Nautomation Prime.

> Master JSON for network automation - REST API interactions, structured logging, data serialization. Learn parsing, generation, and production patterns.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `01_load_json.py` | Basic JSON Loading |
| `02_nested_json.py` | Handling Nested JSON |
| `03_safe_access.py` | Safe JSON Access with Error Handling |
| `04_create_json.py` | Creating JSON from Python Data |
| `05_compact_vs_pretty.py` | Compact vs Pretty JSON |
| `06_rest_api_get.py` | Consuming REST APIs (GET Request) |
| `07_rest_api_post.py` | Sending Data to REST APIs (POST Request) |
| `08_json_logging.py` | JSON Structured Logging |
| `09_device_state.py` | Storing Device State in JSON |
| `10_schema_validation.py` | Validating JSON Structure |
| `11_streaming_large_json.py` | Streaming Large JSON Files |
| `12_nan_and_infinity.py` | Pitfall 4: NaN and Infinity |
| `api_client.py` | api_client.py |
| `config.json` | config.json |
| `devices.json` | What is JSON? |

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

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/intermediate/json-data-handling-network-automation/) · [All lessons](../../README.md)
