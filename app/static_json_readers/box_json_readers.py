from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, TypedDict

# DB function that returns {placeholder_name: fn_number}
# Adjust the import path to wherever you defined it.
from app.database import get_box_label_variables as get_box_label_variables_from_db

from .json_reader_core import ENV_DIR, JsonConfigLoader

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

BoxVariables = Dict[str, int]
BoxLabelStructures = Dict[str, List[str]]


class BoxBlock(TypedDict, total=False):
    # BOXLABELVARIABLES is optional at JSON level; we now fill it from DB.
    BOXLABELVARIABLES: BoxVariables
    BOXLABELSTRUCTURES: BoxLabelStructures


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_\-]+)\}")
_FN_RE = re.compile(r"\^FN(\d+)")


# ---------------------------------------------------------------------------
# JSON loader: only *requires* BOXLABELSTRUCTURES
# ---------------------------------------------------------------------------


def _extract_box_block(data: Any) -> Mapping[str, Any]:
    """
    Accept either:
      { "BOX": { ... } }
    or:
      { "BOXLABELSTRUCTURES": {...}, ... }
    and return the inner block.
    """
    if not isinstance(data, Mapping):
        raise TypeError("Box config root must be an object")

    if "BOX" in data:
        box = data["BOX"]
        if not isinstance(box, Mapping):
            raise TypeError("'BOX' must be an object")
        return box

    if "BOXLABELSTRUCTURES" in data:
        return data

    raise TypeError(
        "Config must contain a 'BOX' object or a 'BOXLABELSTRUCTURES' object at root"
    )


def _validate_box(box_block: Mapping[str, Any]) -> BoxBlock:
    """
    We now only *require* BOXLABELSTRUCTURES.
    BOXLABELVARIABLES is optional and only used if present in JSON
    (main source is now the DB provider).
    """
    # structures are required
    structs_any = box_block.get("BOXLABELSTRUCTURES")
    if not isinstance(structs_any, Mapping):
        raise TypeError("'BOXLABELSTRUCTURES' must be an object")

    structures: BoxLabelStructures = {}
    for name, lines in structs_any.items():
        if not isinstance(name, str) or not (
            isinstance(lines, list) and all(isinstance(s, str) for s in lines)
        ):
            raise ValueError(f"Label '{name}' must be an array of strings (ZPL lines)")
        structures[name] = list(lines)

    # variables in JSON are now optional / legacy
    vars_any = box_block.get("BOXLABELVARIABLES", {})
    variables: BoxVariables = {}
    if vars_any:
        if not isinstance(vars_any, Mapping):
            raise TypeError("'BOXLABELVARIABLES' must be an object if present")

        for key, value in vars_any.items():
            if not isinstance(key, str):
                raise ValueError("All BOXLABELVARIABLES keys must be strings")
            if isinstance(value, int):
                variables[key] = value
            elif isinstance(value, str) and value.isdigit():
                variables[key] = int(value)
            else:
                raise ValueError(
                    f"Variable '{key}' value must be an int (or numeric string)"
                )

    return {
        "BOXLABELSTRUCTURES": structures,
        **({"BOXLABELVARIABLES": variables} if variables else {}),
    }


DEFAULT_PATH = ENV_DIR / "box_labels.json"

_loader = JsonConfigLoader[BoxBlock](
    default_path=DEFAULT_PATH,
    context="box labels",
    extractor=_extract_box_block,
    validator=_validate_box,
)


# ---------------------------------------------------------------------------
# Variables provider (DB, JSON, etc.)
# ---------------------------------------------------------------------------

# Signature for any provider that returns the mapping {placeholder_name: fn_int}
BoxVariablesProvider = Callable[[], BoxVariables]

# Default provider is the DB-backed function
_box_variables_provider: BoxVariablesProvider = get_box_label_variables_from_db


def set_box_variables_provider(provider: BoxVariablesProvider) -> None:
    """
    Override the source of BOXLABELVARIABLES, if needed (for tests or
    alternate loading strategies).
    """
    global _box_variables_provider
    _box_variables_provider = provider


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def load_box_config(
    path: Optional[str | Path] = None,
    *,
    logger: Optional[logging.Logger] = None,
) -> BoxBlock:
    """
    Load box label configuration from JSON (structures), and attach the
    current DB-derived BOXLABELVARIABLES so callers see a complete block.
    """
    block = dict(_loader.load(path, logger=logger))
    # always inject current DB variables into the block
    block["BOXLABELVARIABLES"] = get_box_variables()
    return block  # type: ignore[return-value]


def get_box_variables() -> BoxVariables:
    """Get BOXLABELVARIABLES from the active provider (DB by default)."""
    return dict(_box_variables_provider())


def list_box_label_names() -> List[str]:
    """List all known box label structure names (sorted)."""
    return sorted(_loader.get()["BOXLABELSTRUCTURES"].keys())


def get_box_label_lines(name: str) -> List[str]:
    """Fetch the raw ZPL lines for a label by name."""
    try:
        return list(_loader.get()["BOXLABELSTRUCTURES"][name])
    except KeyError as exc:
        available = ", ".join(list_box_label_names())
        raise KeyError(
            f"Box label structure '{name}' not found. Available: {available}"
        ) from exc


def get_box_label_zpl(name: str) -> str:
    """Return the raw ZPL for a label (no placeholder substitution)."""
    return "\n".join(get_box_label_lines(name))


# ---------------------------------------------------------------------------
# Placeholder helpers
# ---------------------------------------------------------------------------


def list_placeholders_in_label(name: str) -> List[str]:
    """Return all placeholder names used in a label template."""
    found: Set[str] = set()
    for line in get_box_label_lines(name):
        for match in _PLACEHOLDER_RE.finditer(line):
            found.add(match.group(1))
    return sorted(found)


def list_missing_placeholders(name: str) -> List[str]:
    """
    Return placeholder names that are used by a label but missing
    from BOXLABELVARIABLES.
    """
    placeholders = set(list_placeholders_in_label(name))
    vars_map = get_box_variables()
    return sorted(p for p in placeholders if p not in vars_map)


def validate_placeholder_usage(name: str) -> None:
    """Raise if the label uses placeholders with no FN mapping."""
    missing = list_missing_placeholders(name)
    if missing:
        raise ValueError(
            f"Label '{name}' references placeholders with no FN mapping: "
            f"{missing}. Defined variables: {sorted(get_box_variables().keys())}"
        )


def compile_box_label_to_fn(name: str) -> List[str]:
    """
    Replace placeholders like {CODE} in the template with their
    numeric ^FN values from the active provider.
    """
    vars_map = get_box_variables()

    def repl(match: re.Match[str]) -> str:
        var = match.group(1)
        if var not in vars_map:
            raise KeyError(f"Variable '{var}' not found in BOXLABELVARIABLES")
        return str(vars_map[var])

    return [_PLACEHOLDER_RE.sub(repl, line) for line in get_box_label_lines(name)]


def get_compiled_box_label_zpl(name: str) -> str:
    """Return compiled ZPL with placeholders resolved to ^FN numbers."""
    return "\n".join(compile_box_label_to_fn(name))


# ---------------------------------------------------------------------------
# ^FN helpers
# ---------------------------------------------------------------------------


def get_used_fn_numbers(name: str) -> Set[int]:
    """Return all ^FN numbers explicitly used in a template."""
    return {
        int(match.group(1))
        for line in get_box_label_lines(name)
        for match in _FN_RE.finditer(line)
    }


def validate_fn_usage(name: str) -> None:
    """
    Ensure any explicit ^FN numbers in the template appear as values in
    BOXLABELVARIABLES. If templates never contain raw ^FN (only
    placeholders), this will typically be a no-op.
    """
    fn_nums = get_used_fn_numbers(name)
    if not fn_nums:
        return

    vars_map = get_box_variables()
    valid = set(vars_map.values())
    missing = sorted(fn_nums - valid)

    if missing:
        raise ValueError(
            f"Label '{name}' references ^FN numbers with no mapping: {missing}. "
            f"Defined FN numbers: {sorted(valid)}"
        )


def validate_all_structures() -> None:
    """Validate placeholders and ^FN usage across all label structures."""
    for name in list_box_label_names():
        validate_placeholder_usage(name)
        validate_fn_usage(name)


# ---------------------------------------------------------------------------
# ZPL stream utilities
# ---------------------------------------------------------------------------


def _ensure_has_xa_xz_block(zpl: str) -> str:
    """
    Ensure a ZPL snippet is wrapped in ^XA ... ^XZ.
    Idempotent: safe to call multiple times.
    """
    s = zpl.strip()
    up = s.upper()

    if not up.startswith("^XA"):
        s = "^XA\n" + s
        up = s.upper()

    if not up.endswith("^XZ"):
        s = s + "\n^XZ"

    return s


def _prefer_utf8_block(zpl: str) -> str:
    """
    Ensure a ZPL block enables UTF-8 (^CI28) once per block, right
    after ^XA when possible.
    """
    upper = zpl.upper()
    if "^CI28" in upper:
        return zpl

    head, _, tail = zpl.partition("\n")
    if head.upper().startswith("^XA"):
        # Insert comment + ^CI28 immediately after ^XA line
        return f"{head}\n^FX UTF-8\n^CI28\n{tail}"

    # No ^XA line; prepend ^CI28
    return "^CI28\n" + zpl


def get_all_box_label_zpl(
    *,
    validate: bool = True,
    ensure_xa_xz: bool = True,
    ensure_utf8: bool = True,
) -> str:
    """
    Build a single ZPL stream containing ALL box label structures.

    - Validates each structure's placeholders and ^FN usage (if validate=True).
    - Ensures each block has ^XA ... ^XZ (if ensure_xa_xz=True).
    - Ensures UTF-8 (^CI28) once per block, right after ^XA (if ensure_utf8=True).

    Returns:
        One string with all ^XA...^XZ blocks concatenated in sorted name order.
    """
    parts: List[str] = []

    for name in sorted(list_box_label_names()):
        if validate:
            validate_placeholder_usage(name)
            validate_fn_usage(name)

        block = get_compiled_box_label_zpl(name)

        if ensure_xa_xz:
            block = _ensure_has_xa_xz_block(block)
        if ensure_utf8:
            block = _prefer_utf8_block(block)

        parts.append(block)

    return "\n".join(parts)
