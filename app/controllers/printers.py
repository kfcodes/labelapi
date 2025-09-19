from __future__ import annotations

import ipaddress
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, TypedDict

from fastapi import Request

from app.controllers.json_readers import label_printers_full_list, site_ip_ranges


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
    if not printer:
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


async def resolve_site_from_request(request: Request) -> str:
    """
    Resolve a site key from the request's client IP using `site_ip_ranges`.
    Raises ValueError if no match is found.
    """
    client_ip = _parse_client_ip(request)

    for site, range_data in site_ip_ranges.items():
        start = range_data.get("start")
        end = range_data.get("end")
        if (
            isinstance(start, str)
            and isinstance(end, str)
            and ip_in_range(client_ip, start, end)
        ):
            return site

    raise ValueError(f"No site mapping found for IP: {client_ip}")


def _iter_all_role_dicts(cfg: Mapping[str, object]) -> Iterable[Mapping[str, object]]:
    """
    Walk the nested `label_printers_full_list` structure and yield leaf role dicts.
    Expected structure:
      site -> line -> role -> {ip, port}
    """
    for site_data in cfg.values():
        if not isinstance(site_data, Mapping):
            continue
        for line_data in site_data.values():
            if not isinstance(line_data, Mapping):
                continue
            for role_data in line_data.values():
                if isinstance(role_data, Mapping):
                    yield role_data


def get_all_printer_connections() -> List[PrinterConn]:
    """
    Return all valid printer connections across all sites/lines/roles.
    """
    results: List[PrinterConn] = []
    for role_data in _iter_all_role_dicts(label_printers_full_list):
        conn = validate_printer_connection(role_data)
        if conn:
            results.append(conn)
    return results


def get_printers_for_site(site: str) -> Dict[str, Dict[str, PrinterConn]]:
    """
    Return printers for a specific site, grouped by line and role.
    Includes only roles 'large' and 'small'. Skips the 'misc' line.
    Example return:
    {
      "line_a": {
        "large": {"ip": "...", "port": 9100},
        "small": {"ip": "...", "port": 9100}
      },
      ...
    }
    """
    site_data = label_printers_full_list.get(site)
    if not isinstance(site_data, Mapping):
        raise ValueError(f"Site '{site}' not found")

    result: Dict[str, Dict[str, PrinterConn]] = {}

    for line_name, roles in site_data.items():
        if line_name == "misc":
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
    Main route-level access: get printers based on request IP's resolved site.
    """
    site = await resolve_site_from_request(request)
    return get_printers_for_site(site)


async def get_pallet_label_printer(request: Request) -> Tuple[PrinterConn, str]:
    """
    Get the pallet label printer connection and the resolved site.
    Looks under the 'non_production' -> 'pallet_label_printer' path.
    """
    site = await resolve_site_from_request(request)
    site_data = label_printers_full_list.get(site)

    if not isinstance(site_data, Mapping):
        raise ValueError(f"Site '{site}' not found in printer config")

    non_prod = site_data.get("non_production")
    printer = None
    if isinstance(non_prod, Mapping):
        printer = non_prod.get("pallet_label_printer")

    conn = validate_printer_connection(
        printer if isinstance(printer, Mapping) else None
    )
    if not conn:
        raise ValueError(f"Pallet label printer not found or invalid for site '{site}'")

    return conn, site
