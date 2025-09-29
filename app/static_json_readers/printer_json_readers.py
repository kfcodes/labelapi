from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple, TypedDict

from .json_reader_core import ENV_DIR, JsonConfigLoader

# =========================
# Types
# =========================

Logger = Callable[[str], None]


class IpRange(TypedDict):
    start: str
    end: str


class PrinterConn(TypedDict):
    ip: str
    port: int


LineRoleMap = Dict[str, Dict[str, PrinterConn]]
AddressesMap = Dict[str, LineRoleMap]


class PrintersConfig(TypedDict):
    Ranges: Dict[str, IpRange]
    Addresses: AddressesMap


# =========================
# Validation helpers
# =========================


def _require_mapping(value: Any, *, ctx: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{ctx} must be an object")
    # Narrow type for mypy/pyright without runtime change
    return value  # type: ignore[return-value]


def _validate_port(port: Any, *, ctx: str) -> int:
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValueError(f"{ctx} must be an integer in range 1..65535")
    return port


def _validate_ip(value: Any, *, ctx: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{ctx} must be a non-empty string")
    return value


def _validate_ip_range(site_id: str, rng: Any) -> IpRange:
    rng_map = _require_mapping(rng, ctx=f"Ranges['{site_id}']")
    start = _validate_ip(rng_map.get("start"), ctx=f"Ranges['{site_id}'].start")
    end = _validate_ip(rng_map.get("end"), ctx=f"Ranges['{site_id}'].end")
    return {"start": start, "end": end}


def _validate_printer_conn(
    site_id: str, line_name: str, role: str, conn: Any
) -> PrinterConn:
    conn_map = _require_mapping(
        conn,
        ctx=f"Addresses['{site_id}']['{line_name}']['{role}']",
    )
    ip = _validate_ip(
        conn_map.get("ip"), ctx=f"Addresses['{site_id}']['{line_name}']['{role}'].ip"
    )
    port = _validate_port(
        conn_map.get("port"),
        ctx=f"Addresses['{site_id}']['{line_name}']['{role}'].port",
    )
    return {"ip": ip, "port": port}


# =========================
# Top-level validator
# =========================


def _validate_printers(data: Any) -> PrintersConfig:
    root = _require_mapping(data, ctx="printers.json root")

    ranges_raw = root.get("Ranges")
    addrs_raw = root.get("Addresses")

    ranges_map = _require_mapping(ranges_raw, ctx="printers.json 'Ranges'")
    addrs_map = _require_mapping(addrs_raw, ctx="printers.json 'Addresses'")

    # Ranges
    norm_ranges: Dict[str, IpRange] = {}
    for site_id, rng in ranges_map.items():
        site_key = str(site_id)
        norm_ranges[site_key] = _validate_ip_range(site_key, rng)

    # Addresses
    norm_addrs: AddressesMap = {}
    for site_id, lines in addrs_map.items():
        site_key = str(site_id)
        lines_map = _require_mapping(lines, ctx=f"Addresses['{site_key}']")
        site_line_map: LineRoleMap = {}

        for line_name, roles in lines_map.items():
            line_key = str(line_name)
            roles_map = _require_mapping(
                roles, ctx=f"Addresses['{site_key}']['{line_key}']"
            )
            role_map: Dict[str, PrinterConn] = {}

            for role, conn in roles_map.items():
                role_key = str(role)
                role_map[role_key] = _validate_printer_conn(
                    site_key, line_key, role_key, conn
                )

            site_line_map[line_key] = role_map

        norm_addrs[site_key] = site_line_map

    # Cross-check: every site in Addresses must exist in Ranges
    missing_ranges = sorted(s for s in norm_addrs if s not in norm_ranges)
    if missing_ranges:
        raise ValueError(
            f"Sites present in Addresses but missing in Ranges: {missing_ranges}"
        )

    return {"Ranges": norm_ranges, "Addresses": norm_addrs}


# =========================
# Loader instance
# =========================

DEFAULT_PATH = ENV_DIR / "printers.json"

_loader = JsonConfigLoader[PrintersConfig](
    default_path=DEFAULT_PATH,
    context="printers",
    validator=_validate_printers,
)


# =========================
# Public API
# =========================


def load_printers_config(
    path: Optional[str | Path] = None, *, logger: Optional[Logger] = None
) -> PrintersConfig:
    """Load and cache the printers config (use during startup)."""
    return _loader.load(path, logger=logger)


def get_printers_config() -> PrintersConfig:
    """
    Return a shallow copy of the cached config.
    Callers who mutate deeply should copy those parts themselves.
    """
    cfg = _loader.get()
    return {
        "Ranges": dict(cfg["Ranges"]),
        "Addresses": dict(cfg["Addresses"]),
    }


def get_site_ranges() -> Dict[str, IpRange]:
    """Convenience accessor for Ranges."""
    return dict(_loader.get()["Ranges"])


def get_addresses() -> AddressesMap:
    """
    Shallow copy of Addresses (site -> line -> role -> PrinterConn).
    """
    return {site: dict(lines) for site, lines in _loader.get()["Addresses"].items()}


def get_addresses_for_site(site_id: str | int) -> LineRoleMap:
    """Return all line/role mappings for a site (shallow copy)."""
    addrs = get_addresses()
    key = str(site_id)
    if key not in addrs:
        raise KeyError(
            f"Site '{site_id}' not found in Addresses (known: {sorted(addrs.keys())})"
        )
    return dict(addrs[key])


def get_printer_conn(site_id: str | int, line_name: str, role: str) -> PrinterConn:
    """Get a specific printer connection for a site/line/role."""
    site_map = get_addresses_for_site(site_id)
    if line_name not in site_map:
        raise KeyError(
            f"Line '{line_name}' not found for site '{site_id}' (known: {sorted(site_map.keys())})"
        )
    role_map = site_map[line_name]
    if role not in role_map:
        raise KeyError(
            f"Role '{role}' not found for site '{site_id}', line '{line_name}' (known: {sorted(role_map.keys())})"
        )
    conn = role_map[role]
    return {"ip": conn["ip"], "port": conn["port"]}


def iter_printer_connections():
    """
    Iterate (site_id, line_name, role, PrinterConn) over all entries.
    """
    cfg = _loader.get()
    for site_id, lines in cfg["Addresses"].items():
        for line_name, roles in lines.items():
            for role, conn in roles.items():
                yield site_id, line_name, role, {"ip": conn["ip"], "port": conn["port"]}


def get_last_loaded_meta() -> Tuple[Optional[Path], Optional[float]]:
    """Return (path, mtime) for the last successful load."""
    return _loader.get_last_loaded_meta()


def get_pallet_label_printer_for_site(site_id: str | int) -> PrinterConn:
    """
    Convenience accessor for non_production.pallet_label_printer.
    """
    site_map = get_addresses_for_site(site_id)
    non_prod = site_map.get("non_production") or {}
    conn = non_prod.get("pallet_label_printer")
    if not isinstance(conn, dict) or "ip" not in conn or "port" not in conn:
        raise KeyError(
            f"non_production.pallet_label_printer missing for site '{site_id}'"
        )
    return {"ip": conn["ip"], "port": conn["port"]}


def get_all_printer_endpoints(
    *, unique: bool = True, sort: bool = True
) -> List[Tuple[str, int]]:
    """
    Return a list of (ip, port) for every printer in the config.

    Args:
        unique: remove duplicates while preserving first-seen order.
        sort:   sort the final list by (ip, port).

    Example:
        endpoints = get_all_printer_endpoints()
        # -> [("10.0.0.10", 9100), ("10.0.0.11", 9100), ...]

    """
    endpoints: List[Tuple[str, int]] = []
    seen: Set[Tuple[str, int]] = set()

    cfg = _loader.get()
    for lines in cfg["Addresses"].values():
        for roles in lines.values():
            for conn in roles.values():
                pair = (conn["ip"], conn["port"])
                if not unique or pair not in seen:
                    endpoints.append(pair)
                    seen.add(pair)

    if sort:
        endpoints.sort()  # sorts by ip then port
    return endpoints


def get_all_printer_conns(
    *, unique: bool = True, sort: bool = True
) -> List[PrinterConn]:
    """
    Same as get_all_printer_endpoints, but returns PrinterConn dicts.
    Useful if your downstream expects {'ip': str, 'port': int} items.
    """
    pairs = get_all_printer_endpoints(unique=unique, sort=sort)
    return [{"ip": ip, "port": port} for ip, port in pairs]
