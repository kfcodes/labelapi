import json
import ipaddress
from typing import Dict
from pathlib import Path
from fastapi import Request
from .printer_controller import resolve_site_from_request  # Adjust if needed

# In-memory store of all label printers loaded at startup
# Format: site -> line -> role (large/small) -> {"ip": str, "port": int}
label_printers_full_list: Dict[str, Dict[str, Dict[str, dict]]] = {}

# Load all printers from JSON file into memory
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
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid printer config JSON: {e}")

# Validate printer entry has a correct IP and port
def validate_printer_connection(printer: dict) -> dict | None:
    ip = printer.get("ip")
    port = printer.get("port")

    if not ip or not isinstance(port, int):
        return None

    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return None

    return {"ip": ip, "port": port}

# Return a flat list of all valid printer connections (across all sites)
def get_all_printer_connections() -> list:
    results = []
    roles = ("large", "small")

    for site, lines in label_printers_full_list.items():
        for line, printer_roles in lines.items():
            for role in roles:
                printer = printer_roles.get(role)
                if not printer:
                    continue

                connection = validate_printer_connection(printer)
                if connection:
                    results.append(connection)

    return results

# Return grouped printers for a specific site
def get_printers_for_site(site: str) -> dict:
    """
    Returns a dict of printers for the specified site, grouped by line and role.
    Format:
    {
        "line1": {
            "large": {"ip": "...", "port": ...},
            "small": {"ip": "...", "port": ...}
        },
        ...
    }
    """
    site_data = label_printers_full_list.get(site)
    if not site_data:
        raise ValueError(f"Site '{site}' not found")

    printers_by_line = {}

    for line_name, roles in site_data.items():
        line_printers = {}

        for role in ("large", "small"):
            printer = roles.get(role)
            if not printer:
                continue

            connection = validate_printer_connection(printer)
            if connection:
                line_printers[role] = connection

        if line_printers:
            printers_by_line[line_name] = line_printers

    return printers_by_line

# Main access function: resolves site from request and returns its printers
async def get_printers_on_site(request: Request) -> dict:
    """
    Determines the site from the caller's IP and returns all printers
    available on that site, grouped by line and role.
    """
    site = await resolve_site_from_request(request)
    return get_printers_for_site(site)
