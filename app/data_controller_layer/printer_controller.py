import json
import ipaddress  # for IP validation
from typing import Dict
from pathlib import Path
import socket

# In-memory printer config
printers_by_site: Dict[str, Dict[str, Dict[str, dict]]] = {}

def load_printers_from_file(path: str = "env/printers.json"):
    global printers_by_site
    file_path = Path(path)
    print(f"🔍 Checking file path: {file_path.resolve()}")

    if not file_path.exists():
        raise FileNotFoundError(f"Printer config file not found: {file_path}")

    with open(file_path, "r") as f:
        contents = f.read().strip()
        print(f"📄 File contents:\n{contents}")
        if not contents:
            raise ValueError("Printer config file is empty")
        printers_by_site = json.loads(contents)

def get_printer(site: str, line: str, use_large: bool = True) -> dict:
    if site not in printers_by_site:
        raise ValueError(f"Site '{site}' not found")
    if line not in printers_by_site[site]:
        raise ValueError(f"Line '{line}' not found in site '{site}'")

    role = "large" if use_large else "small"
    return printers_by_site[site][line][role]

def get_site_printers(site: str) -> Dict[str, Dict[str, dict]]:
    return printers_by_site.get(site, {})


def get_all_printer_ips_ports() -> list:
    """
    Returns a list of all valid printer IP:port pairs.
    Skips any printers with missing or invalid data.
    """
    results = []
    roles = ("large", "small")

    for site, lines in printers_by_site.items():
        for line, printer_roles in lines.items():
            for role in roles:
                printer = printer_roles.get(role)
                if not printer:
                    continue

                ip = printer.get("ip")
                port = printer.get("port")

                # Validate structure
                if not ip or not isinstance(port, int):
                    print(f"⚠️ Skipping printer (missing/invalid data): {printer}")
                    continue

                # Optional: Validate IP format
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    print(f"⚠️ Skipping printer (invalid IP): {ip}")
                    continue

                results.append({"ip": ip, "port": port})

    return results

