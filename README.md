# soaptest

Make SOAP services testable from pytest. Point it at a WSDL, get callable Python.

## 30-second example

```bash
pip install soaptest
```

```python
from soaptest import Client

client = Client.from_wsdl(
    "http://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL"
)

# Discover what's available
print(client.describe())
# NumberConversionSoap @ http://www.dataaccess.com/webservicesserver/NumberConversion.wso
#   NumberToWords(ubiNum: nonNegativeInteger) -> string
#   NumberToDollars(dNum: decimal) -> string

# Call any operation by name
result = client.NumberToWords(ubiNum=42)
print(result)  # "forty two "
```

## Why

SOAP testing today means SoapUI (a 200 MB GUI) or hand-rolling `requests` with raw XML.
Neither fits naturally into a pytest suite.

`soaptest` is a thin Pythonic layer on top of [zeep](https://docs.python-zeep.org/).
It gives you WSDL discovery (`describe()`) and operation dispatch (`client.OpName(**kwargs)`)
with zero boilerplate. You write plain pytest test functions; soaptest handles the SOAP.

What it does not do yet: record/replay of responses, fault translation into typed Python
exceptions, type stubs for operations, or a pytest fixture plugin. Those are on the
[Roadmap](#roadmap). v0.1 is intentionally minimal — get the basics right first.

## Installation

```bash
pip install soaptest
```

Python 3.9+ is required. `zeep`, `lxml`, and `httpx` are installed automatically.

## Usage

### Discover operations

```python
from soaptest import Client

client = Client.from_wsdl("https://yourservice.example.com/service?WSDL")
print(client.describe())      # pretty-printed operation list
ops = client.operations       # list of Operation named-tuples
```

Each `Operation` has: `name`, `input_signature`, `output_signature`, `service`, `port`, `port_url`.

### Call an operation

```python
result = client.SomeOperation(param1="value", param2=123)
```

`__getattr__` dispatches to the underlying zeep service. The return value is whatever
zeep returns (usually a `zeep.objects.*` object or a plain Python scalar). No conversion
in v0.1 — that's a future feature.

Unknown operation names raise `AttributeError`, so `hasattr(client, "Op")` works.

### CLI

```bash
soaptest http://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL
```

Prints the operation catalog to stdout and exits.

### In pytest

```python
import pytest
from soaptest import Client

WSDL = "https://yourservice.example.com/service?WSDL"

@pytest.fixture(scope="session")
def soap_client():
    return Client.from_wsdl(WSDL)

def test_something(soap_client):
    result = soap_client.SomeOperation(param="value")
    assert result.status == "OK"
```

## Roadmap

v0.1 ships the discovery layer only. Planned for later releases:

- **Fault translation** — map SOAP faults to a typed `SoapFault` Python exception
- **pytest fixture plugin** — `@pytest.fixture` helpers and a `--wsdl` CLI option
- **Type-stub generation** — emit `.pyi` stubs so IDEs can autocomplete operations
- **Record/replay** — record live responses to YAML cassettes; replay offline

## Contributing

File a bug or feature request in the issue tracker. Pull requests are welcome once
an issue is open. For major changes, open an issue first to discuss scope.

## License

MIT. See LICENSE.
