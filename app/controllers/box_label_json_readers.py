# box_json_reader.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, TypedDict

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parents[1]
ENV_DIR: Path = BASE_DIR / "env"

Logger = Callable[[str], None]


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------
class BoxVariables(TypedDict):
    # e.g. {"brand": 1, "sku": 2, ...}  (values are ZPL ^FN numbers)
    pass


BoxLabelStructures = Dict[str, List[str]]  # {"STD": ["^XA...", ..., "^XZ"]}


class BoxBlock(TypedDict):
    BOXLABELVARIABLES: BoxVariables
    BOXLABELSTRUCTURES: BoxLabelStructures


# -----------------------------------------------------------------------------
# In-memory store
# -----------------------------------------------------------------------------
_box_config: BoxBlock = {"BOXLABELVARIABLES": {}, "BOXLABELSTRUCTURES": {}}

# Matches placeholders like {brand}, {ean-13}, {product_group_and_weight}
_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_\-]+)\}")


# -----------------------------------------------------------------------------
# Path & IO
# -----------------------------------------------------------------------------
def _resolve_path(path: str | Path) -> Path:
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


# -----------------------------------------------------------------------------
# Validation / normalization
# -----------------------------------------------------------------------------
def _extract_box_block(data: Any) -> Mapping[str, Any]:
    """
    Accept either:
      { "BOX": { "BOXLABELVARIABLES": {...}, "BOXLABELSTRUCTURES": {...} } }
    or (back-compat)
      { "BOXLABELVARIABLES": {...}, "BOXLABELSTRUCTURES": {...} }
    """
    if not isinstance(data, Mapping):
        raise TypeError("Box config root must be an object")

    if "BOX" in data:
        box = data["BOX"]
        if not isinstance(box, Mapping):
            raise TypeError("'BOX' must be an object")
        return box

    if "BOXLABELVARIABLES" in data and "BOXLABELSTRUCTURES" in data:
        return data  # type: ignore[return-value]

    raise TypeError(
        "Config must contain a 'BOX' object or both 'BOXLABELVARIABLES' and 'BOXLABELSTRUCTURES' at root"
    )


def _ensure_box_shape(box_block: Mapping[str, Any]) -> BoxBlock:
    # variables (convert numeric strings to int)
    vars_any = box_block.get("BOXLABELVARIABLES")
    if not isinstance(vars_any, Mapping):
        raise TypeError("'BOXLABELVARIABLES' must be an object")

    variables: BoxVariables = {}
    for k, v in vars_any.items():
        if not isinstance(k, str):
            raise ValueError("All BOXLABELVARIABLES keys must be strings")
        # Accept "1" or 1; normalize to int
        if isinstance(v, int):
            variables[k] = v
        elif isinstance(v, str) and v.isdigit():
            variables[k] = int(v)
        else:
            raise ValueError(
                f"Variable '{k}' value must be an int (or numeric string), got {type(v).__name__}"
            )

    # label structures
    structs_any = box_block.get("BOXLABELSTRUCTURES")
    if not isinstance(structs_any, Mapping):
        raise TypeError("'BOXLABELSTRUCTURES' must be an object")

    structures: BoxLabelStructures = {}
    for name, lines in structs_any.items():
        if not isinstance(name, str):
            raise ValueError("Label structure names must be strings")
        if isinstance(lines, list) and all(isinstance(s, str) for s in lines):
            structures[name] = lines
        else:
            raise ValueError(f"Label '{name}' must be an array of strings (ZPL lines)")

    return {"BOXLABELVARIABLES": variables, "BOXLABELSTRUCTURES": structures}


# -----------------------------------------------------------------------------
# Public API: load + getters
# -----------------------------------------------------------------------------
def load_box_config(
    path: str | Path = ENV_DIR / "box_labels.json",
    *,
    logger: Optional[Logger] = None,
) -> BoxBlock:
    """
    Load and validate box label variables & structures into memory.

    Example accepted JSON:
    {
      "BOX": {
        "BOXLABELVARIABLES": {"brand":"1","sku":"2",...},
        "BOXLABELSTRUCTURES": {"STD": ["^XA...", "^FN{brand}^FS", "...", "^XZ"]}
      }
    }
    """
    global _box_config
    file_path = _resolve_path(path)
    raw = _read_json(file_path, ctx="box labels", logger=logger)
    box_block = _extract_box_block(raw)
    _box_config = _ensure_box_shape(box_block)
    return _box_config


def get_box_variables() -> BoxVariables:
    """Return the in-memory BOXLABELVARIABLES map (name -> FN number)."""
    return _box_config["BOXLABELVARIABLES"]


def list_box_label_names() -> List[str]:
    """List all available box label structure names."""
    return sorted(_box_config["BOXLABELSTRUCTURES"].keys())


def get_box_label_lines(name: str) -> List[str]:
    """Get the ZPL lines for a given box label structure (with {placeholders})."""
    try:
        return _box_config["BOXLABELSTRUCTURES"][name]
    except KeyError as e:
        raise KeyError(
            f"Box label structure '{name}' not found. Available: {', '.join(list_box_label_names())}"
        ) from e


def get_box_label_zpl(name: str) -> str:
    """Return the full ZPL (joined with newlines) using the stored {placeholders}."""
    return "\n".join(get_box_label_lines(name))


# -----------------------------------------------------------------------------
# Placeholder helpers (swap {var} -> FN number)
# -----------------------------------------------------------------------------
def list_placeholders_in_label(name: str) -> List[str]:
    """Return all unique {placeholders} referenced in the label."""
    lines = get_box_label_lines(name)
    found = set()
    for line in lines:
        for m in _PLACEHOLDER_RE.finditer(line):
            found.add(m.group(1))
    return sorted(found)


def validate_placeholder_usage(name: str) -> None:
    """
    Ensure every {placeholder} used in the label exists in BOXLABELVARIABLES.
    Raises ValueError on mismatch.
    """
    placeholders = set(list_placeholders_in_label(name))
    vars_map = get_box_variables()
    missing = sorted(p for p in placeholders if p not in vars_map)
    if missing:
        raise ValueError(
            f"Label '{name}' references placeholders with no FN mapping: {missing}. "
            f"Defined variables: {sorted(vars_map.keys())}"
        )


def compile_box_label_to_fn(name: str) -> List[str]:
    """
    Replace {placeholders} inside ^FN{var} with their numeric FN values (e.g., ^FN{brand} -> ^FN1).
    Returns a *new* list of lines; original remains unchanged.
    """
    vars_map = get_box_variables()

    def repl(m: re.Match[str]) -> str:
        var = m.group(1)
        if var not in vars_map:
            raise KeyError(f"Variable '{var}' not found in BOXLABELVARIABLES")
        return str(vars_map[var])

    compiled: List[str] = []
    for line in get_box_label_lines(name):
        compiled.append(_PLACEHOLDER_RE.sub(repl, line))
    return compiled


def get_compiled_box_label_zpl(name: str) -> str:
    """
    Joined ZPL where ^FN{var} placeholders have been replaced with ^FN<number>.
    """
    return "\n".join(compile_box_label_to_fn(name))


# -----------------------------------------------------------------------------
# Debug helper: print compiled label to console
# -----------------------------------------------------------------------------
def print_compiled_box_label(name: str, *, header: bool = True) -> None:
    """
    Compile placeholders to numbers, join to a single string, and print it.
    Useful for quick debugging.
    """
    if header:
        print(f"--- Compiled ZPL for box label '{name}' ---")
    compiled = get_compiled_box_label_zpl(name)
    print(compiled)
    if header:
        print("--- end compiled ZPL ---")
