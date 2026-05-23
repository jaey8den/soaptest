"""CLI entry-point: ``soaptest <wsdl-url>`` prints the operation catalog."""

from __future__ import annotations

import sys


def main() -> None:
    """Print the operation catalog for a given WSDL URL."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print("Usage: soaptest <wsdl-url-or-path>", file=sys.stderr)
        sys.exit(1)

    from soaptest import Client  # local import keeps startup fast when --help is enough

    url = sys.argv[1]
    try:
        client = Client.from_wsdl(url)
        client.describe()
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
