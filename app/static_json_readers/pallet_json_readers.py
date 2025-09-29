from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, TypedDict

from .json_reader_core import ENV_DIR, JsonConfigLoader


class PalletVariables(TypedDict):
    # key -> FN number
    pass


PalletLabelStructures = Dict[str, List[str]]


class PalletBlock(TypedDict):
    PALLETVARIABLES: PalletVariables
    PALLETLABELSTRUCTURES: PalletLabelStructures


def _extract_pallet_block(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise TypeError("Pallet config root must be an object")
    if "Pallet" in data:
        pallet = data["Pallet"]
        if not isinstance(pallet, Mapping):
            raise TypeError("'Pallet' must be an object")
        return pallet
    if "PALLETVARIABLES" in data and "PALLETLABELSTRUCTURES" in data:
        return data
    raise TypeError(
        "Config must contain a 'Pallet' object or both 'PALLETVARIABLES' and 'PALLETLABELSTRUCTURES' at root"
    )


def _validate_pallet(pallet_block: Mapping[str, Any]) -> PalletBlock:
    vars_any = pallet_block.get("PALLETVARIABLES")
    if not isinstance(vars_any, Mapping):
        raise TypeError("'PALLETVARIABLES' must be an object")
    variables: PalletVariables = {}
    for k, v in vars_any.items():
        if not isinstance(k, str) or not isinstance(v, int):
            raise ValueError(
                "All PALLETVARIABLES keys must be str and values must be int"
            )
        variables[k] = v

    structs_any = pallet_block.get("PALLETLABELSTRUCTURES")
    if not isinstance(structs_any, Mapping):
        raise TypeError("'PALLETLABELSTRUCTURES' must be an object")
    structures: PalletLabelStructures = {}
    for name, lines in structs_any.items():
        if not isinstance(name, str) or not (
            isinstance(lines, list) and all(isinstance(s, str) for s in lines)
        ):
            raise ValueError(f"Label '{name}' must be an array of strings (ZPL lines)")
        structures[name] = list(lines)
    return {"PALLETVARIABLES": variables, "PALLETLABELSTRUCTURES": structures}


DEFAULT_PATH = ENV_DIR / "pallet_labels.json"
_loader = JsonConfigLoader[PalletBlock](
    default_path=DEFAULT_PATH,
    context="pallet labels",
    extractor=_extract_pallet_block,
    validator=_validate_pallet,
)


def load_pallet_config(
    path: Optional[str | Path] = None, *, logger=None
) -> PalletBlock:
    return _loader.load(path, logger=logger)


def get_pallet_variables():
    return dict(_loader.get()["PALLETVARIABLES"])


def list_pallet_label_names() -> List[str]:
    return sorted(_loader.get()["PALLETLABELSTRUCTURES"].keys())


def get_pallet_label_lines(name: str) -> List[str]:
    try:
        return list(_loader.get()["PALLETLABELSTRUCTURES"][name])
    except KeyError as e:
        raise KeyError(
            f"Pallet label structure '{name}' not found. Available: {', '.join(list_pallet_label_names())}"
        ) from e


def get_pallet_label_zpl(name: str) -> str:
    return "\n".join(get_pallet_label_lines(name))


_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_\-]+)\}")
_FN_RE = re.compile(r"\^FN(\d+)")


def list_placeholders_in_label(name: str) -> list[str]:
    found: set[str] = set()
    for line in get_pallet_label_lines(name):
        for m in _PLACEHOLDER_RE.finditer(line):
            found.add(m.group(1))
    return sorted(found)


def validate_placeholder_usage(name: str) -> None:
    placeholders = set(list_placeholders_in_label(name))
    vars_map = get_pallet_variables()
    missing = sorted(p for p in placeholders if p not in vars_map)
    if missing:
        raise ValueError(
            f"Label '{name}' references placeholders with no FN mapping: {missing}. "
            f"Defined variables: {sorted(vars_map.keys())}"
        )


def compile_pallet_label_to_fn(name: str) -> list[str]:
    vars_map = get_pallet_variables()

    def repl(m: re.Match[str]) -> str:
        var = m.group(1)
        if var not in vars_map:
            raise KeyError(f"Variable '{var}' not found in PALLETVARIABLES")
        return str(vars_map[var])

    return [_PLACEHOLDER_RE.sub(repl, line) for line in get_pallet_label_lines(name)]


def get_compiled_pallet_label_zpl(name: str) -> str:
    return "\n".join(compile_pallet_label_to_fn(name))


def get_used_fn_numbers(name: str) -> Set[int]:
    return {
        int(m.group(1))
        for line in get_pallet_label_lines(name)
        for m in _FN_RE.finditer(line)
    }


def validate_fn_usage(name: str) -> None:
    fn_nums = get_used_fn_numbers(name)
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


def validate_all_structures() -> None:
    for n in list_pallet_label_names():
        validate_fn_usage(n)
