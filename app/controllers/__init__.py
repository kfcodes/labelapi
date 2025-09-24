from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

from .internal_labels import blend_label_function
from .pallet_labels import (
    generate_and_print_combo_label,
    main_pallet_label_function,
    print_blank_pallet_labels,
    upload_pallet_label_data_to_printers,
)
from .printers import (
    get_all_printer_connections,
    get_pallet_label_printer,
    get_printers_for_site,
    get_printers_on_site,
    resolve_site_id_from_request,
)

# --------------------------------------------------------------------
# Public export surface
# --------------------------------------------------------------------
__all__ = [
    # Box (actions)
    "main_print_box_label_function",
    "upload_box_label_structures_to_printers",
    # Printers (helpers)
    "resolve_site_id_from_request",
    "get_printers_for_site",
    "get_printers_on_site",
    "get_pallet_label_printer",
    "get_all_printer_connections",
    # Printers (core readers)
    "load_printers_config",
    "get_printers_config",
    "get_site_ranges",
    "get_addresses",
    "get_addresses_for_site",
    "get_pallet_label_printer_for_site",
    # Pallet (readers + actions)
    "load_pallet_config",
    "get_pallet_variables",
    "list_pallet_label_names",
    "get_pallet_label_lines",
    "get_pallet_label_zpl",
    "validate_pallet_fn_usage",
    "print_pallet_label",
    "main_pallet_label_function",
    "print_blank_pallet_labels",
    "generate_and_print_combo_label",
    "upload_pallet_label_data_to_printers",
    # Box (readers)
    "blend_label_function",
    # Back-compat exports (legacy names kept working)
    "get_label_variables",
    "load_all_config_data",
    "load_box_label_variables",
    "load_pallet_label_variables",
    "load_printers_from_file",
    "load_site_ip_ranges",
    "site_ip_ranges",
    "label_printers_full_list",
]
