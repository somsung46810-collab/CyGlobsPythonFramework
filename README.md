# CyGlobs Python Client Server Framework

A lightweight Python client/server framework built around this methodology:

- Comparators
- Inverse Operators
- Contingency Planning
- Level Of Indirection
- Best Practices

## Architecture

| Methodology | Framework Role |
|---|---|
| Comparators | Validate protocol versions and payload contracts. |
| Inverse Operators | Map abstract client operations to server-side handlers. |
| Contingency Planning | Provide retries, timeouts, safe fallback envelopes, and error handling. |
| Level Of Indirection | Separate transport, protocol, service logic, configuration, and tests. |
| Best Practices | Type hints, dataclasses, Pydantic envelopes, tests, and clear entry points. |

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run server

```bash
uvicorn server:app --reload
```

## Run client

In another terminal:

```bash
python client.py
```

## Run tests

```bash
pytest
```

## Example RPC request

```json
{
  "protocol_version": "1.0",
  "operation": "compare",
  "payload": {
    "left": 10,
    "right": 10
  }
}
```

## Example RPC response

```json
{
  "protocol_version": "1.0",
  "status": "ok",
  "result": {
    "left": 10,
    "right": 10,
    "equal": true,
    "inverse_equal": false
  },
  "error": null
}
```

## Add a new operation

1. Create a function in `framework/services.py`.
2. Register it in `server.py` with `operators.register("operation_name", handler)`.
3. Call it from `client.py` with `client.call("operation_name", payload)`.
