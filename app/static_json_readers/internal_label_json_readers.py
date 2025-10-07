from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Set, TypedDict

from .json_reader_core import ENV_DIR, JsonConfigLoader

__all__ = [
    "load_ipallet_config",
    "get_pallet_variables",
    "list_pallet_label_names",
    "get_pallet_label_zpl",
    "get_compiled_pallet_label_zpl",
    "build_single_pallet_label_zpl",
    "get_all_pallet_label_zpl",  # alias to internal
    "validate_all_structures",
    "get_all_internal_label_zpl",
    "validate_ipallet_label",
]

# key -> FN number
InternalVariables = Dict[str, int]
InternalLabelStructures = Dict[str, List[str]]


class InternalBlock(TypedDict):
    PALLETVARIABLES: InternalVariables
    INTERNALLABELSTRUCTURES: InternalLabelStructures


class LoggerProtocol(Protocol):
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


# ==================
# Extract / Validate (internal)
# ==================


def _extract_internal_block(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise TypeError("Internal label config root must be an object")

    # Case 1: Nested under "INTERALLABELS"
    if "INTERALLABELS" in data:
        inner = data["INTERALLABELS"]
        if not isinstance(inner, Mapping):
            raise TypeError("'INTERALLABELS' must be an object")
        data = inner  # continue with same checks below

    # Now expect PALLETVARIABLES + INTERNALLABELSTRUCTURES at this level
    if "PALLETVARIABLES" not in data or "INTERNALLABELSTRUCTURES" not in data:
        raise TypeError(
            "Config must contain 'PALLETVARIABLES' and 'INTERNALLABELSTRUCTURES' "
            "(optionally wrapped inside 'INTERALLABELS')."
        )

    return {
        "PALLETVARIABLES": data["PALLETVARIABLES"],
        "INTERNALLABELSTRUCTURES": data["INTERNALLABELSTRUCTURES"],
    }


def _validate_internal(block: Mapping[str, Any]) -> InternalBlock:
    vars_any = block.get("PALLETVARIABLES")
    if not isinstance(vars_any, Mapping):
        raise TypeError("'PALLETVARIABLES' must be an object")
    variables: InternalVariables = {}
    for k, v in vars_any.items():
        if not isinstance(k, str) or not isinstance(v, int):
            raise ValueError(
                "All PALLETVARIABLES keys must be str and values must be int"
            )
        if v < 1:
            raise ValueError(f"FN number for '{k}' must be >= 1, got {v}")
        variables[k] = v

    structs_any = block.get("INTERNALLABELSTRUCTURES")
    if not isinstance(structs_any, Mapping):
        raise TypeError("'INTERNALLABELSTRUCTURES' must be an object")
    structures: InternalLabelStructures = {}
    for name, lines in structs_any.items():
        if not isinstance(name, str) or not (
            isinstance(lines, list) and all(isinstance(s, str) for s in lines)
        ):
            raise ValueError(f"Label '{name}' must be an array of strings (ZPL lines)")
        structures[name] = list(lines)

    return {
        "PALLETVARIABLES": variables,
        "INTERNALLABELSTRUCTURES": structures,
    }


# ==================
# Loader
# ==================

DEFAULT_PATH = ENV_DIR / "internal_labels.json"
_loader = JsonConfigLoader[InternalBlock](
    default_path=DEFAULT_PATH,
    context="internal labels",
    extractor=_extract_internal_block,
    validator=_validate_internal,
)

# ==================
# Public Helper Functions
# ==================


def load_ipallet_config(
    path: Optional[str | Path] = None, *, logger: Optional[LoggerProtocol] = None
) -> InternalBlock:
    return _loader.load(path, logger=logger)


def get_pallet_variables() -> InternalVariables:
    # Return a copy to avoid accidental external mutation
    return dict(_loader.get()["PALLETVARIABLES"])


def list_pallet_label_names() -> List[str]:
    return sorted(_loader.get()["INTERNALLABELSTRUCTURES"].keys())


def get_pallet_label_zpl(name: str) -> str:
    return "\n".join(_get_internal_label_lines(name))


def get_compiled_pallet_label_zpl(name: str) -> str:
    return "\n".join(_compile_label_to_fn(name))


def validate_all_structures() -> None:
    for n in list_pallet_label_names():
        _validate_placeholder_usage(n)
        _validate_fn_usage(n)


# ==================
# Internal regexes
# ==================

_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_\-]+)\}")
_FN_RE = re.compile(r"\^FN(\d+)")


# ==================
# Internal Helpers
# ==================


def _get_internal_label_lines(name: str) -> List[str]:
    try:
        return list(_loader.get()["INTERNALLABELSTRUCTURES"][name])
    except KeyError as e:
        raise KeyError(
            f"Internal label structure '{name}' not found. "
            f"Available: {', '.join(list_pallet_label_names())}"
        ) from e


def _list_placeholders_in_label(name: str) -> list[str]:
    found: set[str] = set()
    for line in _get_internal_label_lines(name):
        for m in _PLACEHOLDER_RE.finditer(line):
            found.add(m.group(1))
    return sorted(found)


def _validate_placeholder_usage(name: str) -> None:
    placeholders = set(_list_placeholders_in_label(name))
    vars_map = get_pallet_variables()
    missing = sorted(p for p in placeholders if p not in vars_map)
    if missing:
        raise ValueError(
            f"Label '{name}' references placeholders with no FN mapping: {missing}. "
            f"Defined variables: {sorted(vars_map.keys())}"
        )


def _compile_label_to_fn(name: str) -> list[str]:
    vars_map = get_pallet_variables()

    def repl(m: re.Match[str]) -> str:
        var = m.group(1)
        if var not in vars_map:
            avail = ", ".join(sorted(vars_map.keys()))
            raise KeyError(
                f"Variable '{var}' not found in PALLETVARIABLES. Available: {avail}"
            )
        return str(vars_map[var])

    return [_PLACEHOLDER_RE.sub(repl, line) for line in _get_internal_label_lines(name)]


def _get_used_fn_numbers(name: str) -> Set[int]:
    return {
        int(m.group(1))
        for line in _get_internal_label_lines(name)
        for m in _FN_RE.finditer(line)
    }


def _validate_fn_usage(name: str) -> None:
    fn_nums = _get_used_fn_numbers(name)
    if not fn_nums:
        return
    vars_map = get_pallet_variables()
    valid = set(vars_map.values())
    missing = sorted(fn_nums - valid)
    if missing:
        raise ValueError(
            f"Label '{name}' references ^FN numbers with no mapping: {missing}. "
            f"Defined FN numbers: {sorted(valid)}"
        )


# ==================
# ZPL Builders (public + internal)
# ==================


def _ensure_has_xa_xz_block(zpl: str) -> str:
    """
    Ensure a ZPL block is wrapped by ^XA ... ^XZ.
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
    Ensure ^CI28 (UTF-8) appears once per block, immediately after ^XA if present.
    Idempotent: leaves existing ^CI28 untouched.
    """
    if "^CI28" in zpl.upper():
        return zpl
    head, sep, tail = zpl.partition("\n")
    if head.upper().startswith("^XA"):
        return f"{head}\n^FX UTF-8 ^CI28\n{tail}"
    return "^CI28\n" + zpl


def build_single_pallet_label_zpl(
    name: str,
    *,
    validate: bool = True,
    ensure_xa_xz: bool = True,
    ensure_utf8: bool = True,
) -> str:
    """
    Build a ready-to-print ZPL block for a single internal label structure.
    """
    if validate:
        _validate_placeholder_usage(name)
        _validate_fn_usage(name)

    block = get_compiled_pallet_label_zpl(name)

    if ensure_xa_xz:
        block = _ensure_has_xa_xz_block(block)
    if ensure_utf8:
        block = _prefer_utf8_block(block)

    return block.strip()


def validate_ipallet_label(name: str) -> None:
    """Validate placeholders and ^FN usage for a single internal label."""
    _validate_placeholder_usage(name)
    _validate_fn_usage(name)


def get_all_internal_label_zpl(
    *,
    validate: bool = True,
    ensure_xa_xz: bool = True,
    ensure_utf8: bool = True,
) -> str:
    """
    Build a single ZPL stream containing ALL internal label structures.
    """
    parts: list[str] = []
    for name in sorted(list_pallet_label_names()):
        if validate:
            _validate_placeholder_usage(name)
            _validate_fn_usage(name)

        block = get_compiled_pallet_label_zpl(name)

        if ensure_xa_xz:
            block = _ensure_has_xa_xz_block(block)
        if ensure_utf8:
            block = _prefer_utf8_block(block)

        parts.append(block.strip())
    return "\n".join(parts)


# Back-compat alias: if any code still expects this name
def get_all_pallet_label_zpl(
    *, validate: bool = True, ensure_xa_xz: bool = True, ensure_utf8: bool = True
) -> str:
    return get_all_internal_label_zpl(
        validate=validate, ensure_xa_xz=ensure_xa_xz, ensure_utf8=ensure_utf8
    )
