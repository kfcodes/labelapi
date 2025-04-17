import json
from pathlib import Path
from typing import Dict

label_printers_full_list: Dict[str, Dict[str, Dict[str, dict]]] = {}
site_ip_ranges: Dict[str, Dict[str, str]] = {}
box_label_variables: Dict[str, int] = {}
pallet_label_variables: Dict[str, int] = {}

def load_json_file(path: str, error_context: str = "config", print_output: bool = False) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{error_context.title()} file not found: {file_path}")

    contents = file_path.read_text().strip()
    if not contents:
        raise ValueError(f"{error_context.title()} file is empty: {file_path}")

    try:
        data = json.loads(contents)
        # Serialize to a JSON-formatted str with indentation
        print_data = json.dumps(data, indent=4, sort_keys=True)
        if print_output:
            print(f"[{error_context}] Loaded from {path}:\n{print_data}")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {error_context} JSON in {path}: {e}")

def load_printers_from_file(path: str = "env/printers.json"):
    global label_printers_full_list
    label_printers_full_list = load_json_file(path, error_context="printer config", print_output=True)

def load_site_ip_ranges(path: str = "env/site_ip_ranges.json"):
    global site_ip_ranges
    site_ip_ranges = load_json_file(path, error_context="site IP ranges", print_output=True)

def load_box_label_variables(path: str = "env/box_label_zpl_variables.json"):
    global box_label_variables
    box_label_variables = load_json_file(path, error_context="box ZPL variable map", print_output=True)

def load_pallet_label_variables(path: str = "env/pallet_label_zpl_variables.json"):
    global pallet_label_variables
    pallet_label_variables = load_json_file(path, error_context="pallet ZPL variable map", print_output=True)

# Main function to load all json data into global variables
def load_all_config_data():
    load_printers_from_file()
    load_site_ip_ranges()
    load_box_label_variables()
    load_pallet_label_variables()
