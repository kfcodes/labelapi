# app/controllers/pallet_json_readers.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, TypedDict

# Reuse your existing base/env dirs if you keep this in the same package
BASE_DIR: Path = Path(__file__).resolve().parents[1]
ENV_DIR: Path = BASE_DIR / "env"

Logger = Callable[[str], None]


# ---------- Types ----------
class PalletVariables(TypedDict):
    # e.g. {"id": 1, "weight": 2, "height": 3, "dimensions": 4}
    # (values are ZPL ^FN numbers)
    # NOTE: keep values "int" (not str) for correctness
    pass


PalletLabelStructures = Dict[
    str, List[str]
]  # e.g. {"PALSTD1": ["^XA...", "...", "^XZ"]}


class PalletBlock(TypedDict):
    PALLETVARIABLES: PalletVariables
    PALLETLABELSTRUCTURES: PalletLabelStructures


class PalletConfig(TypedDict):
    # Prefer top-level {"Pallet": {...}} but also support direct {"PALLETVARIABLES":...}
    Pallet: PalletBlock


# ---------- In-memory store ----------
_pallet_config: PalletBlock = {"PALLETVARIABLES": {}, "PALLETLABELSTRUCTURES": {}}


# ---------- Path & IO ----------
def _resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (BASE_DIR / p) if (p.parts and p.parts[0] == "env") else (ENV_DIR / p)


def _read_json(path: Path, ctx: str, logger: Optional[Logger]) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"{ctx.title()} file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise OSError(f"Failed reading {ctx} file {path}: {e}") from e
    if not text:
        raise ValueError(f"{ctx.title()} file is empty: {path}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {ctx} JSON in {path}: {e}") from e
    if logger:
        logger(
            f"[{ctx}] Loaded from {path}:\n{json.dumps(data, indent=4, ensure_ascii=False)}"
        )
    return data


# ---------- Validation / normalization ----------
def _extract_pallet_block(data: Any) -> Mapping[str, Any]:
    """
    Accept either:
      { "Pallet": { "PALLETVARIABLES": {...}, "PALLETLABELSTRUCTURES": {...} } }
    or (back-compat)
      { "PALLETVARIABLES": {...}, "PALLETLABELSTRUCTURES": {...} }
    """
    if not isinstance(data, Mapping):
        raise TypeError("Pallet config root must be an object")

    if "Pallet" in data:
        pallet = data["Pallet"]
        if not isinstance(pallet, Mapping):
            raise TypeError("'Pallet' must be an object")
        return pallet

    # fall back to direct keys
    if "PALLETVARIABLES" in data and "PALLETLABELSTRUCTURES" in data:
        return data  # type: ignore[return-value]

    raise TypeError(
        "Config must contain a 'Pallet' object or both 'PALLETVARIABLES' and 'PALLETLABELSTRUCTURES' at root"
    )


def _ensure_pallet_shape(pallet_block: Mapping[str, Any]) -> PalletBlock:
    # variables
    vars_any = pallet_block.get("PALLETVARIABLES")
    if not isinstance(vars_any, Mapping):
        raise TypeError("'PALLETVARIABLES' must be an object")
    variables: PalletVariables = {}
    for k, v in vars_any.items():
        if not isinstance(k, str) or not isinstance(v, int):
            raise ValueError(
                "All PALLETVARIABLES keys must be str and values must be int (FN numbers)"
            )
        variables[k] = v

    # label structures
    structs_any = pallet_block.get("PALLETLABELSTRUCTURES")
    if not isinstance(structs_any, Mapping):
        raise TypeError("'PALLETLABELSTRUCTURES' must be an object")
    structures: PalletLabelStructures = {}
    for name, lines in structs_any.items():
        if not isinstance(name, str):
            raise ValueError("Label structure names must be strings")
        if isinstance(lines, list) and all(isinstance(s, str) for s in lines):
            structures[name] = lines  # list-of-lines ZPL
        else:
            raise ValueError(f"Label '{name}' must be an array of strings (ZPL lines)")
    return {"PALLETVARIABLES": variables, "PALLETLABELSTRUCTURES": structures}


# ---------- Public API ----------
def load_pallet_config(
    path: str | Path = ENV_DIR / "pallet_labels.json",
    *,
    logger: Optional[Logger] = None,
) -> PalletBlock:
    """
    Load and validate pallet label variables & structures into memory.
    """
    global _pallet_config
    file_path = _resolve_path(path)
    raw = _read_json(file_path, ctx="pallet labels", logger=logger)
    pallet_block = _extract_pallet_block(raw)
    _pallet_config = _ensure_pallet_shape(pallet_block)
    return _pallet_config


def get_pallet_variables() -> PalletVariables:
    return _pallet_config["PALLETVARIABLES"]


def list_pallet_label_names() -> List[str]:
    return sorted(_pallet_config["PALLETLABELSTRUCTURES"].keys())


def get_pallet_label_lines(name: str) -> List[str]:
    try:
        return _pallet_config["PALLETLABELSTRUCTURES"][name]
    except KeyError as e:
        raise KeyError(
            f"Pallet label structure '{name}' not found. Available: {', '.join(list_pallet_label_names())}"
        ) from e


def get_pallet_label_zpl(name: str) -> str:
    """
    Return the full ZPL for a structure (joined with newlines).
    """
    return "\n".join(get_pallet_label_lines(name))


def validate_fn_usage(name: str) -> None:
    """
    Ensure every ^FN<number> referenced in the label exists in PALLETVARIABLES.
    Lightweight static check; does not fully parse ZPL.

    Raises:
        ValueError: if the label references FN numbers not present in PALLETVARIABLES.
    """
    import re

    lines = get_pallet_label_lines(name)
    fn_nums = {
        int(m.group(1)) for line in lines for m in re.finditer(r"\^FN(\d+)", line)
    }
    if not fn_nums:
        return

    vars_map = get_pallet_variables()
    valid_nums = set(vars_map.values())
    missing = sorted(fn_nums - valid_nums)
    if missing:
        raise ValueError(
            f"Label '{name}' references ^FN numbers with no mapping: {missing}. "
            f"Defined FN numbers: {sorted(valid_nums)}"
        )


# ---------- Debug helper ----------
def print_pallet_label(name: str, *, header: bool = True) -> None:
    """
    Print the joined ZPL to the console (useful during development).
    """
    if header:
        print(f"--- ZPL for pallet label '{name}' ---")
    print(get_pallet_label_zpl(name))
    if header:
        print("--- end ZPL ---")
