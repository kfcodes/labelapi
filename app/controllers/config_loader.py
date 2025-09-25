from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from app.static_json_readers import (
    get_addresses,
    get_box_variables,
    get_pallet_variables,
    get_site_ranges,
    list_box_label_names,
    list_pallet_label_names,
    load_box_config,
    load_pallet_config,
    load_printers_config,
)

try:
    from static_json_readers import (
        validate_all_structures as validate_all_box_structures,
    )  # type: ignore
except Exception:
    validate_all_box_structures = None
try:
    from static_json_readers.pallet_json_readers import (
        validate_all_structures as validate_all_pallet_structures,
    )  # type: ignore
except Exception:
    validate_all_pallet_structures = None


def load_all_config_data(
    *,
    printers_path: Optional[str | Path] = None,
    box_path: Optional[str | Path] = None,
    pallet_path: Optional[str | Path] = None,
    verbose: bool = False,
    strict_validate: bool = False,
) -> Dict[str, Any]:
    """
    Load printers, box, and pallet configs into memory.
    If verbose=True, print a human-readable summary.
    If strict_validate=True, run structure/placeholder validations and raise on errors.
    Returns a summary dict (handy for tests/health endpoints).
    """
    logger = print if verbose else None

    # Load
    printers_cfg = load_printers_config(printers_path or None, logger=logger)
    box_cfg = load_box_config(box_path or None, logger=logger)
    pallet_cfg = load_pallet_config(pallet_path or None, logger=logger)

    # Optional strict validation
    if strict_validate:
        if validate_all_box_structures:
            validate_all_box_structures()
        if validate_all_pallet_structures:
            validate_all_pallet_structures()

    # Build summary
    ranges = get_site_ranges()
    addrs = get_addresses()
    box_vars = get_box_variables()
    pallet_vars = get_pallet_variables()
    box_structs = list_box_label_names()
    pallet_structs = list_pallet_label_names()

    summary = {
        "printers": {
            "sites_in_ranges": len(ranges),
            "sites_in_addresses": len(addrs),
            "sites": sorted(addrs.keys()),
        },
        "box": {
            "variables_count": len(box_vars),
            "structures": box_structs,
        },
        "pallet": {
            "variables_count": len(pallet_vars),
            "structures": pallet_structs,
        },
        # raw (if you ever need them)
        # "raw": {"printers": printers_cfg, "box": box_cfg, "pallet": pallet_cfg},
    }

    if verbose:
        print("\n=== CONFIG SUMMARY ====================================")
        print(
            f"Printers: sites in Ranges={summary['printers']['sites_in_ranges']}, "
            f"sites in Addresses={summary['printers']['sites_in_addresses']}"
        )
        for site_id, lines in addrs.items():
            print(f"  - Site {site_id}: lines={list(lines.keys())}")

        print("\nBox labels:")
        print(f"  Variables: {summary['box']['variables_count']}")
        print(f"  Structures: {', '.join(box_structs) or '(none)'}")

        print("\nPallet labels:")
        print(f"  Variables: {summary['pallet']['variables_count']}")
        print(f"  Structures: {', '.join(pallet_structs) or '(none)'}")
        print("=======================================================\n")

    return summary
