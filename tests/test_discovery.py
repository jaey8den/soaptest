"""Integration tests against the public NumberConversion WSDL.

Run all tests:       pytest
Skip network tests:  pytest -m "not integration"
"""

from __future__ import annotations

import pytest

from soaptest import Client

WSDL = "http://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL"


@pytest.mark.integration
def test_describe_lists_operations() -> None:
    """describe() output must mention both known operations."""
    client = Client.from_wsdl(WSDL)
    output = client.describe()
    assert "NumberToWords" in output
    assert "NumberToDollars" in output


@pytest.mark.integration
def test_call_number_to_words() -> None:
    """Calling NumberToWords(1234) should return a string containing 'thousand'."""
    client = Client.from_wsdl(WSDL)
    result = client.NumberToWords(ubiNum=1234)
    assert "thousand" in str(result).lower()


@pytest.mark.integration
def test_operations_property_is_non_empty() -> None:
    """client.operations must return at least the two known operations."""
    client = Client.from_wsdl(WSDL)
    names = [op.name for op in client.operations]
    assert "NumberToWords" in names
    assert "NumberToDollars" in names


def test_getattr_raises_for_unknown_operation() -> None:
    """Accessing a non-existent operation must raise AttributeError (not any other error)."""

    class _FakeOp:
        name = "FakeOp"
        input_signature = ""
        output_signature = "str"
        service = "FakeSvc"
        port = "FakePort"
        port_url = ""

    from soaptest.client.introspect import Operation

    fake_op = Operation(
        name="FakeOp",
        input_signature="",
        output_signature="str",
        service="FakeSvc",
        port="FakePort",
        port_url="",
    )

    # Build a Client without touching the network
    import unittest.mock as mock

    fake_zeep = mock.MagicMock()
    client = Client(fake_zeep, [fake_op])

    with pytest.raises(AttributeError):
        _ = client.NonExistentOperation


def test_hasattr_returns_false_for_unknown_operation() -> None:
    """hasattr() must return False (not raise) for unknown operations."""
    import unittest.mock as mock

    from soaptest.client.introspect import Operation

    fake_op = Operation(
        name="FakeOp",
        input_signature="",
        output_signature="str",
        service="FakeSvc",
        port="FakePort",
        port_url="",
    )
    fake_zeep = mock.MagicMock()
    client = Client(fake_zeep, [fake_op])

    assert hasattr(client, "FakeOp") is True
    assert hasattr(client, "DoesNotExist") is False
