from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, TypedDict

# --------------------
# Paths
# --------------------
BASE_DIR: Path = Path(__file__).resolve().parents[1]
ENV_DIR: Path = BASE_DIR / "env"
DEFAULT_PATH: Path = ENV_DIR / "printers.json"

Logger = Callable[[str], None]


# --------------------
# Types for printers.json
# --------------------
class IpRange(TypedDict):
    start: str
    end: str


class PrinterConn(TypedDict):
    ip: str
    port: int


# Lines -> roles -> connection; e.g. "line1" -> {"large": {...}, "small": {...}}
LineRoleMap = Dict[str, Dict[str, PrinterConn]]
# SiteId -> {"line1": {...}, "non_production": {...}}
AddressesMap = Dict[str, LineRoleMap]


class PrintersConfig(TypedDict):
    Ranges: Dict[str, IpRange]  # e.g. {"1": {"start": "...", "end": "..."}, ...}
    Addresses: (
        AddressesMap  # e.g. {"1": {"line1": {...}, "non_production": {...}}, ...}
    )


# --------------------
# In-memory store
# --------------------
_printers_config: PrintersConfig = {"Ranges": {}, "Addresses": {}}
_loaded: bool = False


# --------------------
# Path + IO utilities
# --------------------
def resolve_config_path(path: str | Path) -> Path:
    """
    Resolution rules:
      - Absolute path: as-is
      - Starts with 'env/': relative to BASE_DIR
      - Otherwise: relative to ENV_DIR
    """
    p = Path(path)
    if p.is_absolute():
        return p
    return (BASE_DIR / p) if (p.parts and p.parts[0] == "env") else (ENV_DIR / p)


def _read_json(path: Path, error_context: str, logger: Optional[Logger]) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"{error_context.title()} file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise OSError(f"Failed reading {error_context} file {path}: {e}") from e
    if not text:
        raise ValueError(f"{error_context.title()} file is empty: {path}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {error_context} JSON in {path}: {e}") from e
    if logger:
        logger(
            f"[{error_context}] Loaded from {path}:\n{json.dumps(data, indent=4, ensure_ascii=False)}"
        )
    return data


# --------------------
# Validation helpers
# --------------------
def _ensure_printers_config_shape(data: Any) -> PrintersConfig:
    if not isinstance(data, Mapping):
        raise TypeError("printers.json root must be an object")

    ranges = data.get("Ranges")
    addrs = data.get("Addresses")

    if not isinstance(ranges, Mapping):
        raise TypeError("printers.json must contain 'Ranges' as an object")
    if not isinstance(addrs, Mapping):
        raise TypeError("printers.json must contain 'Addresses' as an object")

    # Normalize keys to str and validate range entries
    norm_ranges: Dict[str, IpRange] = {}
    for site_id, rng in ranges.items():
        if not isinstance(rng, Mapping):
            raise TypeError(f"Ranges['{site_id}'] must be an object")
        start, end = rng.get("start"), rng.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            raise ValueError(
                f"Ranges['{site_id}'] must have 'start' and 'end' as strings"
            )
        norm_ranges[str(site_id)] = {"start": start, "end": end}

    # Normalize and lightly validate addresses
    norm_addrs: AddressesMap = {}
    for site_id, lines in addrs.items():
        if not isinstance(lines, Mapping):
            raise TypeError(f"Addresses['{site_id}'] must be an object of lines")
        site_line_map: LineRoleMap = {}
        for line_name, roles in lines.items():
            if not isinstance(roles, Mapping):
                raise TypeError(
                    f"Addresses['{site_id}']['{line_name}'] must be an object of roles"
                )
            role_map: Dict[str, PrinterConn] = {}
            for role, conn in roles.items():
                if not isinstance(conn, Mapping):
                    raise TypeError(
                        f"Addresses['{site_id}']['{line_name}']['{role}'] must be an object"
                    )
                ip, port = conn.get("ip"), conn.get("port")
                if not isinstance(ip, str) or not isinstance(port, int):
                    raise ValueError(
                        f"Addresses['{site_id}']['{line_name}']['{role}'] must include ip:str and port:int"
                    )
                role_map[str(role)] = {"ip": ip, "port": port}
            site_line_map[str(line_name)] = role_map
        norm_addrs[str(site_id)] = site_line_map

    # Cross-check: every site in Addresses should exist in Ranges
    missing_ranges = sorted(s for s in norm_addrs.keys() if s not in norm_ranges)
    if missing_ranges:
        raise ValueError(
            f"Sites present in Addresses but missing in Ranges: {missing_ranges}"
        )

    return {"Ranges": norm_ranges, "Addresses": norm_addrs}


def _ensure_loaded() -> None:
    if not _loaded:
        raise RuntimeError(
            "Printers config not loaded. Call load_printers_config() during startup."
        )


# --------------------
# Public API
# --------------------
def load_printers_config(
    path: str | Path = DEFAULT_PATH,
    *,
    logger: Optional[Logger] = None,
) -> PrintersConfig:
    """
    Load the unified printers config (Ranges + Addresses) into memory.
    """
    global _printers_config, _loaded
    file_path = resolve_config_path(path)
    raw = _read_json(file_path, error_context="printers", logger=logger)
    _printers_config = _ensure_printers_config_shape(raw)
    _loaded = True
    return _printers_config


def get_printers_config() -> PrintersConfig:
    """Return the in-memory printers config. Call load_printers_config() at startup."""
    _ensure_loaded()
    return _printers_config


def get_site_ranges() -> Dict[str, IpRange]:
    """Convenience accessor for Ranges (site-id keyed)."""
    _ensure_loaded()
    return _printers_config["Ranges"]


def get_addresses() -> AddressesMap:
    """Convenience accessor for Addresses (site-id keyed)."""
    _ensure_loaded()
    return _printers_config["Addresses"]


def get_addresses_for_site(site_id: str) -> LineRoleMap:
    """Return line/role map for a specific site-id. Raises KeyError if not found."""
    addrs = get_addresses()
    if site_id not in addrs:
        raise KeyError(f"Site '{site_id}' not found in addresses")
    return addrs[site_id]


def get_pallet_label_printer_for_site(site_id: str) -> PrinterConn:
    """Look up the non-production pallet label printer for a site."""
    site_map = get_addresses_for_site(site_id)
    non_prod = site_map.get("non_production") or {}
    conn = non_prod.get("pallet_label_printer")
    if not isinstance(conn, dict) or "ip" not in conn or "port" not in conn:
        raise KeyError(
            f"non_production.pallet_label_printer missing for site '{site_id}'"
        )
    return {"ip": conn["ip"], "port": conn["port"]}
