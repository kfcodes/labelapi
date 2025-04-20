import json
from pathlib import Path
from typing import Dict

# ---------------------------------------
# In-memory store for config data
# ---------------------------------------

label_printers_full_list: Dict[str, Dict[str, Dict[str, dict]]] = {}
site_ip_ranges: Dict[str, Dict[str, str]] = {}
box_label_variables: Dict[str, str] = {}
pallet_label_variables: Dict[str, str] = {}

# ---------------------------------------
# Generic JSON file loader
# ---------------------------------------

def load_json_file(path: str, error_context: str = "config", print_output: bool = False) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{error_context.title()} file not found: {file_path}")

    contents = file_path.read_text().strip()
    if not contents:
        raise ValueError(f"{error_context.title()} file is empty: {file_path}")

    try:
        data = json.loads(contents)
        if print_output:
            print(f"[{error_context}] Loaded from {path}:\n{json.dumps(data, indent=4)}")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {error_context} JSON in {path}: {e}")

# ---------------------------------------
# Specific config loaders
# ---------------------------------------

def load_printers_from_file(path: str = "env/printers.json") -> Dict:
    global label_printers_full_list
    label_printers_full_list = load_json_file(path, error_context="printer config", print_output=True)
    return label_printers_full_list

def load_site_ip_ranges(path: str = "env/site_ip_ranges.json") -> Dict:
    global site_ip_ranges
    site_ip_ranges = load_json_file(path, error_context="site IP ranges", print_output=True)
    return site_ip_ranges

def load_box_label_variables(path: str = "env/box_label_zpl_variables.json") -> Dict:
    global box_label_variables
    box_label_variables = load_json_file(path, error_context="box ZPL variable map", print_output=True)
    return box_label_variables

def load_pallet_label_variables(path: str = "env/pallet_label_zpl_variables.json") -> Dict:
    global pallet_label_variables
    pallet_label_variables = load_json_file(path, error_context="pallet ZPL variable map", print_output=True)
    return pallet_label_variables

# ---------------------------------------
# Get correct label variable map based on label type
# ---------------------------------------

def get_label_variables(label_type: str = "box") -> Dict[str, str]:
    """
    Returns the appropriate label variable map based on the label type.

    Args:
        label_type: One of 'box' or 'pallet'

    Returns:
        dict of label variable mappings

    Raises:
        ValueError: If an unsupported label type is passed
    """
    if label_type == "box":
        return box_label_variables
    elif label_type == "pallet":
        return pallet_label_variables
    else:
        raise ValueError(f"Unsupported label type: {label_type}. Use 'box' or 'pallet'.")

# ---------------------------------------
# Load everything in one call
# ---------------------------------------

def load_all_config_data():
    """
    Loads all JSON config data into memory.
    """
    load_printers_from_file()
    load_site_ip_ranges()
    load_box_label_variables()
    load_pallet_label_variables()
