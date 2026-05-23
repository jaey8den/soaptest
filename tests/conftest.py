"""pytest configuration: register custom markers."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require network access to a live WSDL endpoint",
    )
