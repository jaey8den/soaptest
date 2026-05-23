"""Operation catalog: walk zeep's WSDL bindings and build a structured list of operations.

Note: `binding._operations` is technically a private zeep API. It is the only
programmatic way to enumerate operations without parsing raw WSDL XML ourselves.
TODO: revisit if zeep exposes a stable public introspection API in a future release.
"""

from __future__ import annotations

import contextlib
from collections import defaultdict
from typing import NamedTuple


class Operation(NamedTuple):
    """A single WSDL operation with its signatures and provenance."""

    name: str
    input_signature: str
    output_signature: str
    service: str
    port: str
    port_url: str


def _format_element(element: object) -> str:
    """Return a human-readable type string for a zeep WSDL element."""
    try:
        # zeep elements have a .type attribute whose name we can read
        type_obj = getattr(element, "type", None)
        if type_obj is not None:
            qname = getattr(type_obj, "name", None)
            if qname:
                return str(qname)
        # Fall back to the element's own name
        name = getattr(element, "name", None)
        if name:
            return str(name)
    except Exception:  # noqa: BLE001
        pass
    return "any"


def _input_signature(op: object) -> str:
    """Produce 'param: type, ...' from a zeep operation's input message."""
    try:
        op_input = getattr(op, "input", None)
        body = getattr(op_input, "body", None)
        if body is None:
            return ""
        elements = getattr(body, "type", body)
        # zeep exposes elements as an iterable of (name, element) pairs
        parts = getattr(elements, "elements", None)
        if parts:
            return ", ".join(f"{n}: {_format_element(e)}" for n, e in parts)
        # Some operations have a flat type with no sub-elements (scalar input)
        name = getattr(body, "name", None)
        if name:
            return f"{name}: {_format_element(body)}"
    except (AttributeError, TypeError):
        pass
    return ""


def _output_signature(op: object) -> str:
    """Produce a type string from a zeep operation's output message."""
    try:
        op_output = getattr(op, "output", None)
        body = getattr(op_output, "body", None)
        if body is None:
            return "any"
        elements = getattr(body, "type", body)
        parts = getattr(elements, "elements", None)
        if parts:
            pairs = list(parts)
            if len(pairs) == 1:
                return _format_element(pairs[0][1])
            return ", ".join(f"{n}: {_format_element(e)}" for n, e in pairs)
        return _format_element(body)
    except (AttributeError, TypeError):
        pass
    return "any"


def build_catalog(zeep_client: object) -> list[Operation]:
    """Walk zeep_client.wsdl.services to build a list of Operation records."""
    operations: list[Operation] = []

    wsdl = getattr(zeep_client, "wsdl", None)
    if wsdl is None:
        return operations

    services = getattr(wsdl, "services", {})
    for service_name, service in services.items():
        ports = getattr(service, "ports", {})
        for port_name, port in ports.items():
            binding = getattr(port, "binding", None)
            if binding is None:
                continue
            # _operations: dict[str, zeep.wsdl.definitions.Operation]
            # Private API — see module docstring.
            raw_ops = getattr(binding, "_operations", {})
            port_url: str = ""
            with contextlib.suppress(AttributeError, TypeError):
                port_url = str(port.binding_options.get("address", ""))
            for op_name, op in raw_ops.items():
                operations.append(
                    Operation(
                        name=str(op_name),
                        input_signature=_input_signature(op),
                        output_signature=_output_signature(op),
                        service=str(service_name),
                        port=str(port_name),
                        port_url=port_url,
                    )
                )

    return operations


def format_catalog(operations: list[Operation]) -> str:
    """Render the operation list as a human-readable multi-line string.

    Output format::

        ServiceName @ https://endpoint.example.com
          OperationA(param: type) -> returnType
          OperationB() -> returnType
    """
    if not operations:
        return "(no operations found)"

    # Group by (service, port) preserving insertion order
    groups: dict[tuple[str, str, str], list[Operation]] = defaultdict(list)
    for op in operations:
        groups[(op.service, op.port, op.port_url)].append(op)

    lines: list[str] = []
    for (_service, port, url), ops in groups.items():
        header = f"{port}"
        if url:
            header += f" @ {url}"
        lines.append(header)
        for op in ops:
            sig = op.input_signature or ""
            ret = op.output_signature or "any"
            lines.append(f"  {op.name}({sig}) -> {ret}")

    return "\n".join(lines)
