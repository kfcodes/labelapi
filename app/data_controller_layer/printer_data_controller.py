import ipaddress
from typing import Dict, List, Optional

from data_controller_layer.json_controller import (label_printers_full_list,
                                                   site_ip_ranges)
from fastapi import Request


# Validate a printer entry has a correct IP and port
def validate_printer_connection(printer: dict) -> Optional[dict]:
    ip = printer.get("ip")
    port = printer.get("port")

    if not ip or not isinstance(port, int):
        return None
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return None
    return {"ip": ip, "port": port}


# Check if an IP falls within a start/end IP range
def ip_in_range(ip: str, start: str, end: str) -> bool:
    ip_val = ipaddress.ip_address(ip)
    return ipaddress.ip_address(start) <= ip_val <= ip_val <= ipaddress.ip_address(end)


# Resolve site from request IP using site_ip_ranges
async def resolve_site_from_request(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = (
        forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host
    )

    for site, range_data in site_ip_ranges.items():
        if ip_in_range(client_ip, range_data["start"], range_data["end"]):
            return site

    raise ValueError(f"No site mapping found for IP: {client_ip}")


# Return all valid printer IP/port pairs
def get_all_printer_connections() -> List[dict]:
    results = []
    for site_data in label_printers_full_list.values():
        for line_data in site_data.values():
            for role_data in line_data.values():
                connection = validate_printer_connection(role_data)
                if connection:
                    results.append(connection)
    return results


# Return printers for a specific site, grouped by line and role
def get_printers_for_site(site: str) -> dict:
    site_data = label_printers_full_list.get(site)
    if not site_data:
        raise ValueError(f"Site '{site}' not found")

    result = {}
    for line_name, roles in site_data.items():
        if line_name == "misc":
            continue  # skip misc

        line_printers = {}
        for role in ("large", "small"):
            printer = roles.get(role)
            connection = validate_printer_connection(printer) if printer else None
            if connection:
                line_printers[role] = connection

        if line_printers:
            result[line_name] = line_printers

    return result


# Main route-level access: get printers based on request IP's resolved site
async def get_printers_on_site(request: Request) -> dict:
    site = await resolve_site_from_request(request)
    return get_printers_for_site(site)


# Get the pallet label printer for the resolved site
async def get_pallet_label_printer(request: Request) -> dict:
    site = await resolve_site_from_request(request)
    site_data = label_printers_full_list.get(site)

    if not site_data:
        raise ValueError(f"Site '{site}' not found in printer config")

    misc = site_data.get("non_production", {})
    printer = misc.get("pallet_label_printer")

    connection = validate_printer_connection(printer) if printer else None
    if not connection:
        raise ValueError(f"Pallet label printer not found or invalid for site '{site}'")

    return connection, site
