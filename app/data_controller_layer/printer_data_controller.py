import json
import ipaddress
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import Request

# In-memory store for full label printer list and IP range map
label_printers_full_list: Dict[str, Dict[str, Dict[str, dict]]] = {}
site_ip_ranges: Dict[str, Dict[str, str]] = {}

# ✅ Load printers from JSON file
def load_printers_from_file(path: str = "env/printers.json"):
    global label_printers_full_list
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Printer config file not found: {file_path}")

    with open(file_path, "r") as f:
        contents = f.read().strip()
        if not contents:
            raise ValueError("Printer config file is empty")
        try:
            label_printers_full_list = json.loads(contents)
            print(label_printers_full_list)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid printer config JSON: {e}")

# ✅ Load site IP ranges from JSON file
def load_site_ip_ranges(path: str = "env/site_ip_ranges.json"):
    global site_ip_ranges
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Site IP range file not found: {file_path}")

    with open(file_path, "r") as f:
        contents = f.read().strip()
        if not contents:
            raise ValueError("Site IP range file is empty")
        try:
            site_ip_ranges = json.loads(contents)
            print(site_ip_ranges)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid site IP range JSON: {e}")

# ✅ Validate a printer entry has a correct IP and port
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

# ✅ Check if an IP falls within a start/end IP range
def ip_in_range(ip: str, start: str, end: str) -> bool:
    ip_val = ipaddress.ip_address(ip)
    return ipaddress.ip_address(start) <= ip_val <= ip_val <= ipaddress.ip_address(end)

# ✅ Resolve site from request IP
async def resolve_site_from_request(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host

    for site, range_data in site_ip_ranges.items():
        if ip_in_range(client_ip, range_data["start"], range_data["end"]):
            return site

    raise ValueError(f"No site mapping found for IP: {client_ip}")

# ✅ Return all valid printer IP/port pairs
def get_all_printer_connections() -> List[dict]:
    results = []
    for site_data in label_printers_full_list.values():
        for line_data in site_data.values():
            for role_data in line_data.values():
                connection = validate_printer_connection(role_data)
                if connection:
                    results.append(connection)
    return results

# ✅ Return printers for a specific site, grouped by line and role
def get_printers_for_site(site: str) -> dict:
    site_data = label_printers_full_list.get(site)
    if not site_data:
        raise ValueError(f"Site '{site}' not found")

    result = {}

    for line_name, roles in site_data.items():
        if line_name == "misc":
            continue  # skip misc for this function

        line_printers = {}
        for role in ("large", "small"):
            printer = roles.get(role)
            connection = validate_printer_connection(printer) if printer else None
            if connection:
                line_printers[role] = connection

        if line_printers:
            result[line_name] = line_printers

    return result

# ✅ Main route-level access: get printers based on request IP's resolved site
async def get_printers_on_site(request: Request) -> dict:
    site = await resolve_site_from_request(request)
    return get_printers_for_site(site)

# Get the pallet label printer for the resolved site
async def get_pallet_label_printer(request: Request) -> dict:
    """
    Returns the pallet label printer details for the resolved site.
    """
    site = await resolve_site_from_request(request)
    site_data = label_printers_full_list.get(site)

    if not site_data:
        raise ValueError(f"Site '{site}' not found in printer config")

    misc = site_data.get("misc", {})
    printer = misc.get("pallet_label_printer")

    connection = validate_printer_connection(printer) if printer else None
    if not connection:
        raise ValueError(f"Pallet label printer not found or invalid for site '{site}'")

    return connection, site
