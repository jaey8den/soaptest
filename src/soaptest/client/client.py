"""Client: thin Pythonic wrapper around zeep for SOAP service discovery and calling."""

from __future__ import annotations

from typing import Any

from soaptest.client.introspect import Operation, build_catalog, format_catalog


class Client:
    """A thin wrapper around a zeep client for a single WSDL.

    Typical usage::

        from soaptest import Client

        client = Client.from_wsdl("http://example.com/service?WSDL")
        print(client.describe())
        result = client.SomeOperation(param="value")
    """

    def __init__(self, zeep_client: Any, catalog: list[Operation]) -> None:
        # Store under mangled names so __getattr__ never intercepts them
        self._zeep_client = zeep_client
        self._catalog = catalog
        self._catalog_index: dict[str, Operation] = {op.name: op for op in catalog}

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_wsdl(cls, url: str) -> Client:
        """Create a Client by loading a WSDL from *url* (http/https or file path).

        Args:
            url: URL or local file path to the WSDL document.

        Returns:
            A ready-to-use Client instance.
        """
        import zeep  # local import so zeep errors surface at call time, not module import

        zeep_client: Any = zeep.Client(wsdl=url)  # type: ignore[no-untyped-call]
        catalog = build_catalog(zeep_client)
        return cls(zeep_client, catalog)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    @property
    def operations(self) -> list[Operation]:
        """Read-only list of Operation named-tuples discovered from the WSDL."""
        return list(self._catalog)

    def describe(self) -> str:
        """Return (and print) a formatted listing of all available operations.

        The output groups operations by service/port::

            NumberConversionSoap @ https://...
              NumberToWords(ubiNum: nonNegativeInteger) -> string
              NumberToDollars(dNum: decimal) -> string
        """
        text = format_catalog(self._catalog)
        print(text)
        return text

    # ------------------------------------------------------------------
    # Dynamic dispatch
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """Enable ``client.OperationName(**kwargs)`` for any catalogued operation.

        Raises:
            AttributeError: if *name* is not a known WSDL operation, so that
                ``hasattr(client, name)`` works correctly.
        """
        # _catalog_index is set in __init__ via object.__setattr__-free assignment,
        # so it IS in __dict__. But during pickling/copy Python may call __getattr__
        # before __dict__ is fully restored — guard against that.
        catalog_index = self.__dict__.get("_catalog_index", {})
        if name not in catalog_index:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {name!r}. "
                f"Available operations: {list(catalog_index)}"
            )

        service = self._zeep_client.service

        def _call(**kwargs: Any) -> Any:
            method = getattr(service, name)
            return method(**kwargs)

        _call.__name__ = name
        _call.__qualname__ = f"Client.{name}"
        return _call

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        n = len(self._catalog)
        return f"<soaptest.Client operations={n}>"
