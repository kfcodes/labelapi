from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, TypedDict

from .json_reader_core import ENV_DIR, JsonConfigLoader


class BoxVariables(TypedDict):
    # key -> FN number
    pass


BoxLabelStructures = Dict[str, List[str]]


class BoxBlock(TypedDict):
    BOXLABELVARIABLES: BoxVariables
    BOXLABELSTRUCTURES: BoxLabelStructures


_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_\-]+)\}")


def _extract_box_block(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise TypeError("Box config root must be an object")
    if "BOX" in data:
        box = data["BOX"]
        if not isinstance(box, Mapping):
            raise TypeError("'BOX' must be an object")
        return box
    if "BOXLABELVARIABLES" in data and "BOXLABELSTRUCTURES" in data:
        return data
    raise TypeError(
        "Config must contain a 'BOX' object or both 'BOXLABELVARIABLES' and 'BOXLABELSTRUCTURES' at root"
    )


def _validate_box(box_block: Mapping[str, Any]) -> BoxBlock:
    vars_any = box_block.get("BOXLABELVARIABLES")
    if not isinstance(vars_any, Mapping):
        raise TypeError("'BOXLABELVARIABLES' must be an object")
    variables: BoxVariables = {}
    for k, v in vars_any.items():
        if not isinstance(k, str):
            raise ValueError("All BOXLABELVARIABLES keys must be strings")
        if isinstance(v, int):
            variables[k] = v
        elif isinstance(v, str) and v.isdigit():
            variables[k] = int(v)
        else:
            raise ValueError(f"Variable '{k}' value must be an int (or numeric string)")
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
    return {"BOXLABELVARIABLES": variables, "BOXLABELSTRUCTURES": structures}


DEFAULT_PATH = ENV_DIR / "box_labels.json"
_loader = JsonConfigLoader[BoxBlock](
    default_path=DEFAULT_PATH,
    context="box labels",
    extractor=_extract_box_block,
    validator=_validate_box,
)


def load_box_config(path: Optional[str | Path] = None, *, logger=None) -> BoxBlock:
    return _loader.load(path, logger=logger)


def get_box_variables() -> BoxVariables:
    return dict(_loader.get()["BOXLABELVARIABLES"])


def list_box_label_names() -> List[str]:
    return sorted(_loader.get()["BOXLABELSTRUCTURES"].keys())


def get_box_label_lines(name: str) -> List[str]:
    try:
        return list(_loader.get()["BOXLABELSTRUCTURES"][name])
    except KeyError as e:
        raise KeyError(
            f"Box label structure '{name}' not found. Available: {', '.join(list_box_label_names())}"
        ) from e


def get_box_label_zpl(name: str) -> str:
    return "\n".join(get_box_label_lines(name))


# Placeholder helpers
def list_placeholders_in_label(name: str) -> List[str]:
    found: Set[str] = set()
    for line in get_box_label_lines(name):
        for m in _PLACEHOLDER_RE.finditer(line):
            found.add(m.group(1))
    return sorted(found)


def list_missing_placeholders(name: str) -> List[str]:
    placeholders = set(list_placeholders_in_label(name))
    vars_map = get_box_variables()
    return sorted(p for p in placeholders if p not in vars_map)


def validate_placeholder_usage(name: str) -> None:
    missing = list_missing_placeholders(name)
    if missing:
        raise ValueError(
            f"Label '{name}' references placeholders with no FN mapping: {missing}. "
            f"Defined variables: {sorted(get_box_variables().keys())}"
        )


def compile_box_label_to_fn(name: str) -> List[str]:
    vars_map = get_box_variables()

    def repl(m: re.Match[str]) -> str:
        var = m.group(1)
        if var not in vars_map:
            raise KeyError(f"Variable '{var}' not found in BOXLABELVARIABLES")
        return str(vars_map[var])

    return [_PLACEHOLDER_RE.sub(repl, line) for line in get_box_label_lines(name)]


def get_compiled_box_label_zpl(name: str) -> str:
    return "\n".join(compile_box_label_to_fn(name))


def validate_all_structures() -> None:
    for n in list_box_label_names():
        validate_placeholder_usage(n)


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

    # local, idempotent guards (so we don't depend on other modules)
    def _ensure_has_xa_xz_block(zpl: str) -> str:
        s = zpl.strip()
        up = s.upper()
        if not up.startswith("^XA"):
            s = "^XA\n" + s
            up = s.upper()
        if not up.endswith("^XZ"):
            s = s + "\n^XZ"
        return s

    def _prefer_utf8_block(zpl: str) -> str:
        if "^CI28" in zpl.upper():
            return zpl
        head, sep, tail = zpl.partition("\n")
        if head.upper().startswith("^XA"):
            return f"{head}\n^FX UTF-8 ^CI28\n{tail}"
        return "^CI28\n" + zpl

    parts: list[str] = []
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


_FN_RE = re.compile(r"\^FN(\d+)")


def get_used_fn_numbers(name: str) -> Set[int]:
    return {
        int(m.group(1))
        for line in get_box_label_lines(name)
        for m in _FN_RE.finditer(line)
    }


def validate_fn_usage(name: str) -> None:
    """
    Ensures any explicit ^FN numbers in the template are present in BOXLABELVARIABLES.
    If your templates never contain raw ^FN (only placeholders), this will usually be a no-op.
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
