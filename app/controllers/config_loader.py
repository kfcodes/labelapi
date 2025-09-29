from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, TypedDict

from app.static_json_readers import (
    get_addresses,
    get_all_printer_conns,
    get_box_variables,
    get_pallet_variables,
    get_site_ranges,
    list_box_label_names,
    list_pallet_label_names,
    load_box_config,
    load_pallet_config,
    load_printers_config,
    validate_all_box_structures,
    validate_all_pallet_structures,
)
from app.static_json_readers.box_json_readers import get_compiled_box_label_zpl
from app.static_json_readers.pallet_json_readers import get_compiled_pallet_label_zpl
from app.static_json_readers.pallet_json_readers import (
    validate_placeholder_usage as validate_pallet_placeholders,
)

Logger = Callable[[str], None]


# -------------------- Types --------------------
class PrintersSummary(TypedDict):
    sites_in_ranges: int
    sites_in_addresses: int
    sites: List[str]
    targets: List[Tuple[str, int]]  # (ip, port)


class DomainSummary(TypedDict):
    variables_count: int
    variables_map: Dict[str, int]
    structures: List[str]


class ConfigSummary(TypedDict):
    printers: PrintersSummary
    box: DomainSummary
    pallet: DomainSummary


# -------------------- ZPL helpers --------------------
def _zpl_escape_fd(text: str) -> str:
    """Minimal ^FD escaping; extend to ^FH if needed."""
    s = str(text).replace("^", " ").replace("~", " ")
    return s


def _append_field_data_block(
    compiled_zpl: str, name_to_fn: Mapping[str, int], values: Mapping[str, str] | None
) -> str:
    if not values:
        return compiled_zpl
    lines = [compiled_zpl]
    for name, value in values.items():
        fn = name_to_fn.get(name)
        if fn is not None:
            lines.append(f"^FN{fn}^FD{_zpl_escape_fd(value)}^FS")
    return "\n".join(lines)


def _ensure_has_xa_xz(zpl: str) -> str:
    s = zpl.strip()
    up = s.upper()
    if not up.startswith("^XA"):
        s = "^XA\n" + s
        up = s.upper()
    if not up.endswith("^XZ"):
        s = s + "\n^XZ"
    return s


def _prefer_utf8(zpl: str) -> str:
    # Respect existing ^CI28
    if "^CI28" in zpl.upper():
        return zpl
    head, sep, tail = zpl.partition("\n")
    if head.upper().startswith("^XA"):
        return f"{head}\n^FX UTF-8 ^CI28\n{tail}"
    return "^CI28\n" + zpl


# -------------------- Load + (optional) validate --------------------
def load_all_config_data(
    *,
    printers_path: Optional[str | Path] = None,
    box_path: Optional[str | Path] = None,
    pallet_path: Optional[str | Path] = None,
    strict_validate: bool = False,
    logger: Optional[Logger] = None,
) -> None:
    """Load configs into memory. Call at startup."""
    log = logger or (lambda *_: None)
    load_printers_config(printers_path or None, logger=log)
    load_box_config(box_path or None, logger=log)
    load_pallet_config(pallet_path or None, logger=log)

    if strict_validate:
        validate_all_box_structures()
        validate_all_pallet_structures()


# -------------------- Summaries & previews --------------------
def summarize_config(
    *,
    include_variables: bool = True,
    include_targets: bool = True,
) -> ConfigSummary:
    """Return a typed, deterministic summary of loaded config."""
    ranges = get_site_ranges()
    addrs = get_addresses()
    box_vars = get_box_variables()
    pallet_vars = get_pallet_variables()
    box_structs = sorted(list_box_label_names())
    pallet_structs = sorted(list_pallet_label_names())
    targets = get_all_printer_conns()

    printers_summary: PrintersSummary = {
        "sites_in_ranges": len(ranges),
        "sites_in_addresses": len(addrs),
        "sites": sorted(addrs.keys()),
        "targets": (
            sorted(((c["ip"], c["port"]) for c in targets)) if include_targets else []
        ),
    }

    box_summary: DomainSummary = {
        "variables_count": len(box_vars),
        "variables_map": dict(box_vars) if include_variables else {},
        "structures": box_structs,
    }
    pallet_summary: DomainSummary = {
        "variables_count": len(pallet_vars),
        "variables_map": dict(pallet_vars) if include_variables else {},
        "structures": pallet_structs,
    }

    return {
        "printers": printers_summary,
        "box": box_summary,
        "pallet": pallet_summary,
    }


def render_label_previews(
    *,
    box_values: Optional[Mapping[str, str]] = None,
    pallet_values: Optional[Mapping[str, str]] = None,
    logger: Optional[Logger] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Compile + inject runtime values, ensuring ^XA/^XZ and UTF-8.
    Returns {"box": {name:zpl}, "pallet": {name:zpl}} for consumers to log or display.
    """
    log = logger or (lambda *_: None)
    previews: Dict[str, Dict[str, str]] = {"box": {}, "pallet": {}}

    # Box
    box_vars = get_box_variables()
    for name in sorted(list_box_label_names()):
        try:
            compiled = get_compiled_box_label_zpl(name)
            rendered = _append_field_data_block(compiled, box_vars, box_values)
            rendered = _prefer_utf8(_ensure_has_xa_xz(rendered))
            previews["box"][name] = rendered
        except Exception as e:
            log(f"[WARN] Box preview failed for '{name}': {e}")

    # Pallet
    pallet_vars = get_pallet_variables()
    for name in sorted(list_pallet_label_names()):
        try:
            try:
                validate_pallet_placeholders(name)
            except Exception as ve:
                log(f"[WARN] Placeholder validation failed for '{name}': {ve}")

            compiled = get_compiled_pallet_label_zpl(name)
            rendered = _append_field_data_block(compiled, pallet_vars, pallet_values)
            rendered = _prefer_utf8(_ensure_has_xa_xz(rendered))
            previews["pallet"][name] = rendered
        except Exception as e:
            log(f"[WARN] Pallet preview failed for '{name}': {e}")

    return previews
