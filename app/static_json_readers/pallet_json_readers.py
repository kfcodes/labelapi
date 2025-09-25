from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, TypedDict

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parents[1]
ENV_DIR: Path = BASE_DIR / "env"
DEFAULT_PATH: Path = ENV_DIR / "pallet_labels.json"

Logger = Callable[[str], None]


# -------------------------------------------------------------------
# Types
# -------------------------------------------------------------------
class PalletVariables(TypedDict):
    # e.g. {"id": 1, "weight": 2, "height": 3, "dimensions": 4}
    # values are ZPL ^FN numbers (must be int)
    pass


PalletLabelStructures = Dict[str, List[str]]  # {"PALSTD1": ["^XA...", "...", "^XZ"]}


class PalletBlock(TypedDict):
    PALLETVARIABLES: PalletVariables
    PALLETLABELSTRUCTURES: PalletLabelStructures


# -------------------------------------------------------------------
# In-memory store
# -------------------------------------------------------------------
_pallet_config: PalletBlock = {"PALLETVARIABLES": {}, "PALLETLABELSTRUCTURES": {}}
_loaded: bool = False
_LOCK = threading.Lock()


# -------------------------------------------------------------------
# Path & IO
# -------------------------------------------------------------------
def _resolve_path(path: Optional[str | Path]) -> Path:
    """
    Resolution rules:
      - None: use DEFAULT_PATH
      - Absolute path: as-is
      - Starts with 'env/': relative to BASE_DIR
      - Otherwise: relative to ENV_DIR
    """
    if path is None:
        return DEFAULT_PATH
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


# -------------------------------------------------------------------
# Validation / normalization
# -------------------------------------------------------------------
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
            structures[name] = list(lines)  # copy
        else:
            raise ValueError(f"Label '{name}' must be an array of strings (ZPL lines)")
    return {"PALLETVARIABLES": variables, "PALLETLABELSTRUCTURES": structures}


def _ensure_loaded() -> None:
    if not _loaded:
        raise RuntimeError(
            "Pallet config not loaded. Call load_pallet_config() during startup."
        )


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------
def load_pallet_config(
    path: Optional[str | Path] = None, *, logger: Optional[Logger] = None
) -> PalletBlock:
    """
    Load and validate pallet label variables & structures into memory.
    """
    global _pallet_config, _loaded
    with _LOCK:
        file_path = _resolve_path(path)
        raw = _read_json(file_path, ctx="pallet labels", logger=logger)
        pallet_block = _extract_pallet_block(raw)
        _pallet_config = _ensure_pallet_shape(pallet_block)
        _loaded = True
        return _pallet_config


def get_pallet_variables() -> PalletVariables:
    _ensure_loaded()
    return dict(_pallet_config["PALLETVARIABLES"])


def list_pallet_label_names() -> List[str]:
    _ensure_loaded()
    return sorted(_pallet_config["PALLETLABELSTRUCTURES"].keys())


def get_pallet_label_lines(name: str) -> List[str]:
    _ensure_loaded()
    try:
        # return a copy
        return list(_pallet_config["PALLETLABELSTRUCTURES"][name])
    except KeyError as e:
        raise KeyError(
            f"Pallet label structure '{name}' not found. Available: {', '.join(list_pallet_label_names())}"
        ) from e


def get_pallet_label_zpl(name: str) -> str:
    """Return the full ZPL for a structure (joined with newlines)."""
    return "\n".join(get_pallet_label_lines(name))


# -------------------------------------------------------------------
# NEW: Placeholder helpers (swap {var} -> FN number)
# -------------------------------------------------------------------
def list_placeholders_in_label(name: str) -> list[str]:
    """Return all unique {placeholders} referenced in the structure."""
    lines = get_pallet_label_lines(name)
    found: set[str] = set()
    for line in lines:
        for m in _PLACEHOLDER_RE.finditer(line):
            found.add(m.group(1))
    return sorted(found)


def validate_placeholder_usage(name: str) -> None:
    """
    Ensure every {placeholder} used in the label exists in PALLETVARIABLES.
    Raises ValueError on mismatch.
    """
    placeholders = set(list_placeholders_in_label(name))
    vars_map = get_pallet_variables()
    missing = sorted(p for p in placeholders if p not in vars_map)
    if missing:
        raise ValueError(
            f"Label '{name}' references placeholders with no FN mapping: {missing}. "
            f"Defined variables: {sorted(vars_map.keys())}"
        )


def compile_pallet_label_to_fn(name: str) -> list[str]:
    """
    Replace {placeholders} inside ^FN{var} with their numeric FN values (e.g., ^FN{pallet_id} -> ^FN1).
    Returns a *new* list of lines; original remains unchanged.
    """
    vars_map = get_pallet_variables()

    def repl(m: re.Match[str]) -> str:
        var = m.group(1)
        if var not in vars_map:
            raise KeyError(f"Variable '{var}' not found in PALLETVARIABLES")
        return str(vars_map[var])

    compiled: list[str] = []
    for line in get_pallet_label_lines(name):
        compiled.append(_PLACEHOLDER_RE.sub(repl, line))
    return compiled


def get_compiled_pallet_label_zpl(name: str) -> str:
    """Joined ZPL where ^FN{var} placeholders have been replaced with ^FN<number>."""
    return "\n".join(compile_pallet_label_to_fn(name))


# -------------------------------------------------------------------
# Validation helpers
# -------------------------------------------------------------------
_FN_RE = re.compile(r"\^FN(\d+)")


def get_used_fn_numbers(name: str) -> Set[int]:
    """
    Return the set of ^FN numbers referenced by a named structure.
    """
    nums = {
        int(m.group(1))
        for line in get_pallet_label_lines(name)
        for m in _FN_RE.finditer(line)
    }
    return nums


def validate_fn_usage(name: str) -> None:
    """
    Ensure every ^FN<number> referenced in the label exists in PALLETVARIABLES.
    Lightweight static check; does not fully parse ZPL.
    """
    fn_nums = get_used_fn_numbers(name)
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


def validate_all_structures() -> None:
    """Run validate_fn_usage for every structure."""
    for name in list_pallet_label_names():
        validate_fn_usage(name)


# -------------------------------------------------------------------
# Debug helper
# -------------------------------------------------------------------
def print_pallet_label(
    name: str, *, compiled: bool = True, header: bool = True
) -> None:
    """
    Print the pallet label ZPL.

    compiled=True  -> placeholders {var} are replaced by their FN numbers (^FN{var} -> ^FN<n>)
    compiled=False -> print the raw structure (with placeholders intact)
    """
    if header:
        print(f"--- ZPL for pallet label '{name}' ---")

    if compiled:
        # optional safety: ensure every placeholder has a mapping
        print("compiled")
        validate_placeholder_usage(name)
        print(get_compiled_pallet_label_zpl(name))
    else:
        print("NOT!! compiled")
        print(get_pallet_label_zpl(name))

    if header:
        print("--- end ZPL ---")


print_pallet_label("PALSTD1", compiled=True)
