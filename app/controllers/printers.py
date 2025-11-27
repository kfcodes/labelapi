from __future__ import annotations

import ipaddress
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, TypedDict

from fastapi import Request

from app.static_json_readers import (
    get_addresses,
    get_addresses_for_site,
    get_site_ranges,
)


class PrinterConn(TypedDict):
    ip: str
    port: int


def _parse_client_ip(request: Request) -> str:
    """
    Extract the best-guess client IP.
    - Prefer first value in X-Forwarded-For (left-most).
    - Fallback to request.client.host.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.client.host  # type: ignore[return-value]


def validate_printer_connection(
    printer: Mapping[str, object] | None,
) -> Optional[PrinterConn]:
    """
    Validate a printer entry has a correct IP and port.
    Returns a normalized dict {'ip': str, 'port': int} or None if invalid.
    """
    if not isinstance(printer, Mapping):
        return None

    ip = printer.get("ip")
    port = printer.get("port")

    if not isinstance(ip, str) or not isinstance(port, int):
        return None

    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return None

    return {"ip": ip, "port": port}


def ip_in_range(ip: str, start: str, end: str) -> bool:
    """
    True if ip is between [start, end], inclusive.
    Works for both IPv4 and IPv6.
    """
    ip_val = ipaddress.ip_address(ip)
    start_val = ipaddress.ip_address(start)
    end_val = ipaddress.ip_address(end)
    return start_val <= ip_val <= end_val


async def resolve_site_id_from_request(request: Request) -> str:
    """
    Resolve a site *id* (e.g. '1', '2') from the client IP using the unified printers config.
    Raises ValueError if no match is found.
    """
    client_ip = _parse_client_ip(request)

    for site_id, range_data in get_site_ranges().items():
        start = range_data.get("start")
        end = range_data.get("end")
        if (
            isinstance(start, str)
            and isinstance(end, str)
            and ip_in_range(client_ip, start, end)
        ):
            return site_id

    raise ValueError(f"No site mapping found for IP: {client_ip}")


def get_printers_for_site(site_id: str) -> Dict[str, Dict[str, PrinterConn]]:
    """
    Return printers for a specific site-id, grouped by line and role.
    Includes only roles 'large' and 'small'. Skips the 'non_production' block.
    Example:
      {
        "line1": {
          "large": {"ip": "...", "port": 9100},
          "small": {"ip": "...", "port": 9100}
        },
        ...
      }
    """
    site_map = get_addresses_for_site(site_id)
    result: Dict[str, Dict[str, PrinterConn]] = {}

    for line_name, roles in site_map.items():
        if line_name == "non_production":
            continue
        if not isinstance(roles, Mapping):
            continue

        line_printers: Dict[str, PrinterConn] = {}
        for role in ("large", "small"):
            raw = roles.get(role)
            conn = validate_printer_connection(
                raw if isinstance(raw, Mapping) else None
            )
            if conn:
                line_printers[role] = conn

        if line_printers:
            result[str(line_name)] = line_printers

    return result


async def get_printers_on_site(request: Request) -> Dict[str, Dict[str, PrinterConn]]:
    """
    Route-level access: derive site-id from request IP, then return that site's printers.
    """
    site_id = await resolve_site_id_from_request(request)
    return get_printers_for_site(site_id)


async def get_pallet_label_printer(request: Request) -> Tuple[PrinterConn, str]:
    """
    Return (connection, site_id) for the site's non_production.pallet_label_printer.
    """
    site_id = await resolve_site_id_from_request(request)
    site_map = get_addresses_for_site(site_id)

    non_prod = site_map.get("non_production")
    printer = (
        non_prod.get("pallet_label_printer") if isinstance(non_prod, Mapping) else None
    )

    conn = validate_printer_connection(
        printer if isinstance(printer, Mapping) else None
    )
    if not conn:
        raise ValueError(
            f"Pallet label printer not found or invalid for site '{site_id}'"
        )

    return conn, site_id


def get_all_printer_connections(
    *, include_non_production: bool = True
) -> List[PrinterConn]:
    """
    Collect all valid printer connections across all sites/lines/roles.
    Optionally include 'non_production' entries (default: True).
    Safe to call from async routes (it's synchronous).
    """
    # Ensure config is available; if not, load it now.
    try:
        addrs = get_addresses()
    except RuntimeError:
        load_printers_config()
        addrs = get_addresses()

    results: List[PrinterConn] = []
    for line_map in addrs.values():  # site -> lines
        if not isinstance(line_map, Mapping):
            continue
        for line_name, roles in line_map.items():
            if not include_non_production and line_name == "non_production":
                continue
            if not isinstance(roles, Mapping):
                continue
            for conn in roles.values():  # role -> {ip, port} or nested
                valid = validate_printer_connection(
                    conn if isinstance(conn, Mapping) else None
                )
                if valid:
                    results.append(valid)

    seen = set()
    deduped: List[PrinterConn] = []
    for c in results:
        key = (c["ip"], c["port"])
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return deduped
