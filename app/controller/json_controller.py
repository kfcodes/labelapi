# app/controller/json_controller.py
import json
from pathlib import Path
from typing import Dict

# Resolve app/env no matter where the process is started from
BASE_DIR = Path(__file__).resolve().parents[1]  # -> .../app
ENV_DIR = BASE_DIR / "env"

# -------------------------------
# In-memory stores
# -------------------------------
label_printers_full_list: Dict[str, Dict[str, Dict[str, dict]]] = {}
site_ip_ranges: Dict[str, Dict[str, str]] = {}
box_label_variables: Dict[str, str] = {}
pallet_label_variables: Dict[str, str] = {}


# -------------------------------
# Generic JSON file loader
# -------------------------------
def load_json_file(
    path: str | Path, error_context: str = "config", print_output: bool = False
) -> dict:
    file_path = Path(path)

    # Robust resolution:
    # - absolute path -> use as-is
    # - "env/..."     -> relative to BASE_DIR
    # - anything else -> relative to ENV_DIR
    if not file_path.is_absolute():
        parts = file_path.parts
        if parts and parts[0] == "env":
            file_path = BASE_DIR / file_path
        else:
            file_path = ENV_DIR / file_path

    if not file_path.exists():
        raise FileNotFoundError(f"{error_context.title()} file not found: {file_path}")

    contents = file_path.read_text().strip()
    if not contents:
        raise ValueError(f"{error_context.title()} file is empty: {file_path}")

    try:
        data = json.loads(contents)
        if print_output:
            print(
                f"[{error_context}] Loaded from {file_path}:\n{json.dumps(data, indent=4)}"
            )
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {error_context} JSON in {file_path}: {e}")


# -------------------------------
# Specific loaders (defaults are absolute)
# -------------------------------
def load_printers_from_file(path: str | Path = ENV_DIR / "printers.json") -> Dict:
    global label_printers_full_list
    label_printers_full_list = load_json_file(
        path, error_context="printer config", print_output=True
    )
    return label_printers_full_list


def load_site_ip_ranges(path: str | Path = ENV_DIR / "site_ip_ranges.json") -> Dict:
    global site_ip_ranges
    site_ip_ranges = load_json_file(
        path, error_context="site IP ranges", print_output=True
    )
    return site_ip_ranges


def load_box_label_variables(
    path: str | Path = ENV_DIR / "box_label_zpl_variables.json",
) -> Dict:
    global box_label_variables
    box_label_variables = load_json_file(
        path, error_context="box ZPL variable map", print_output=True
    )
    return box_label_variables


def load_pallet_label_variables(
    path: str | Path = ENV_DIR / "pallet_label_zpl_variables.json",
) -> Dict:
    global pallet_label_variables
    pallet_label_variables = load_json_file(
        path, error_context="pallet ZPL variable map", print_output=True
    )
    return pallet_label_variables


# -------------------------------
# Helper selector & bulk loader
# -------------------------------
def get_label_variables(label_type: str = "box") -> Dict[str, str]:
    if label_type == "box":
        return box_label_variables
    elif label_type == "pallet":
        return pallet_label_variables
    else:
        raise ValueError("Unsupported label type. Use 'box' or 'pallet'.")


def load_all_config_data():
    load_printers_from_file()
    load_site_ip_ranges()
    load_box_label_variables()
    load_pallet_label_variables()
