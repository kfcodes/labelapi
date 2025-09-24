from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

from .box_json_readers import (
    compile_box_label_to_fn,
    get_box_label_lines,
    get_box_label_zpl,
    get_box_variables,
    get_compiled_box_label_zpl,
    list_box_label_names,
    list_placeholders_in_label,
    load_box_config,
    print_compiled_box_label,
)
from .box_json_readers import (
    validate_placeholder_usage as validate_box_placeholder_usage,
)
from .pallet_json_readers import (
    get_pallet_label_lines,
    get_pallet_label_zpl,
    get_pallet_variables,
    list_pallet_label_names,
    load_pallet_config,
    print_pallet_label,
)
from .pallet_json_readers import validate_fn_usage as validate_pallet_fn_usage
from .printer_json_readers import (
    get_addresses,
    get_addresses_for_site,
    get_pallet_label_printer_for_site,
    get_printers_config,
    get_site_ranges,
    load_printers_config,
)

# --------------------------------------------------------------------
# Backward-compatibility helpers
# --------------------------------------------------------------------
# Legacy mirrors for back-compat (populated by _refresh_legacy_mirrors)
site_ip_ranges: Dict[str, Dict[str, str]] = {}
label_printers_full_list: Dict[str, Dict[str, Dict[str, dict]]] = {}


def _refresh_legacy_mirrors() -> None:
    """Sync legacy globals from the new printers config to avoid breaking old imports."""
    global site_ip_ranges, label_printers_full_list
    site_ip_ranges = dict(get_site_ranges())
    label_printers_full_list = {
        site: dict(lines) for site, lines in get_addresses().items()
    }


def load_printers_from_file(
    path: Optional[str | Path] = None, *, logger: Optional[Callable[[str], None]] = None
):
    """
    Back-compat alias for loading printers.json.
    - If `path` is provided, load from there; otherwise use default env path.
    - Returns the legacy-shaped Addresses map (label_printers_full_list).
    """
    if path is None:
        load_printers_config(logger=logger)
    else:
        load_printers_config(path, logger=logger)
    _refresh_legacy_mirrors()
    return label_printers_full_list


def load_site_ip_ranges(
    path: Optional[str | Path] = None, *, logger: Optional[Callable[[str], None]] = None
):
    """
    Back-compat shim: ranges now live inside printers.json.
    - If `path` is provided, we reload printers.json from that path first.
    - Returns the Ranges map (legacy name).
    """
    if path is not None:
        load_printers_config(path, logger=logger)
    if not site_ip_ranges:
        _refresh_legacy_mirrors()
    return site_ip_ranges


def load_box_label_variables(
    path: Optional[str | Path] = None, *, logger: Optional[Callable[[str], None]] = None
):
    """Back-compat alias to load_box_config(). Returns the variables map for BOX labels."""
    if path is None:
        load_box_config(logger=logger)
    else:
        load_box_config(path, logger=logger)
    return get_box_variables()


def load_pallet_label_variables(
    path: Optional[str | Path] = None, *, logger: Optional[Callable[[str], None]] = None
):
    """Back-compat alias to load_pallet_config(). Returns the variables map for Pallet labels."""
    if path is None:
        load_pallet_config(logger=logger)
    else:
        load_pallet_config(path, logger=logger)
    return get_pallet_variables()


def get_label_variables(label_type: str = "box"):
    """Back-compat helper: 'box' -> box variables, 'pallet' -> pallet variables."""
    if label_type == "box":
        return get_box_variables()
    if label_type == "pallet":
        return get_pallet_variables()
    raise ValueError("Unsupported label type. Use 'box' or 'pallet'.")


def load_all_config_data(
    *,
    printers_path: Optional[str | Path] = None,
    box_path: Optional[str | Path] = None,
    pallet_path: Optional[str | Path] = None,
    verbose: bool = False,
) -> None:
    """
    Back-compat bulk loader used by some apps at startup.
    Loads printers.json, then box & pallet label configs.
    Set `verbose=True` to echo loaded JSON via print and a summary.
    """
    logger = print if verbose else None

    # --- Printers (unified) ---
    if printers_path is None:
        load_printers_config(logger=logger)
    else:
        load_printers_config(printers_path, logger=logger)
    _refresh_legacy_mirrors()

    # --- Box labels ---
    if box_path is None:
        load_box_config(logger=logger)
    else:
        load_box_config(box_path, logger=logger)

    # --- Pallet labels ---
    if pallet_path is None:
        load_pallet_config(logger=logger)
    else:
        load_pallet_config(pallet_path, logger=logger)

    if not verbose:
        return

    # ---------- Pretty summary ----------
    try:
        ranges = get_site_ranges()
        addrs = get_addresses()
        total_sites_ranges = len(ranges)
        total_sites_addrs = len(addrs)

        # Count printers (dedup by ip:port)
        from .printers import get_all_printer_connections

        conns = get_all_printer_connections()
        unique_conns = {(c["ip"], c["port"]) for c in conns}

        print("\n=== CONFIG SUMMARY ====================================")
        print(f"Printers:")
        print(f"  Sites in Ranges   : {total_sites_ranges}")
        print(f"  Sites in Addresses: {total_sites_addrs}")
        print(f"  Total printers    : {len(conns)} (unique {len(unique_conns)})")

        # Show a quick per-site overview
        for site_id, lines in addrs.items():
            line_names = list(lines.keys())
            print(f"    - Site {site_id}: lines={line_names}")

        # Box
        box_vars = get_box_variables()
        box_structs = list_box_label_names()
        print("\nBox labels:")
        print(f"  Variables count   : {len(box_vars)}")
        print(
            f"  Structures        : {', '.join(box_structs) if box_structs else '(none)'}"
        )

        # Pallet
        pallet_vars = get_pallet_variables()
        pallet_structs = list_pallet_label_names()
        print("\nPallet labels:")
        print(f"  Variables count   : {len(pallet_vars)}")
        print(
            f"  Structures        : {', '.join(pallet_structs) if pallet_structs else '(none)'}"
        )
        print("=======================================================\n")

    except Exception as e:
        # Never crash the app on summary printing
        print(f"[load_all_config_data] Summary print failed: {e}")


__all__ = [
    # Printers (core readers)
    "load_printers_config",
    "get_printers_config",
    "get_site_ranges",
    "get_addresses",
    "get_addresses_for_site",
    "get_pallet_label_printer_for_site",
    # Pallet (readers + actions)
    "load_pallet_config",
    "get_pallet_variables",
    "list_pallet_label_names",
    "get_pallet_label_lines",
    "get_pallet_label_zpl",
    "validate_pallet_fn_usage",
    "print_pallet_label",
    # Box (readers)
    "load_box_config",
    "get_box_variables",
    "list_box_label_names",
    "get_box_label_lines",
    "get_box_label_zpl",
    "compile_box_label_to_fn",
    "get_compiled_box_label_zpl",
    "list_placeholders_in_label",
    "validate_box_placeholder_usage",
    "print_compiled_box_label",
    # Internal / blend
    # Back-compat exports (legacy names kept working)
    "get_label_variables",
    "load_all_config_data",
    "load_box_label_variables",
    "load_pallet_label_variables",
    "load_printers_from_file",
    "load_site_ip_ranges",
    "site_ip_ranges",
    "label_printers_full_list",
]
