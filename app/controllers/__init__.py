"""
Public API for controllers.

Usage in routes/services:
    from app.controller import (
        # box labels
        main_print_box_label_function, upload_box_label_structures_to_printers,
        load_label_template_from_env, apply_zpl_placeholders,
        # internal label
        blend_label_function,
        # pallet labels
        main_pallet_label_function, print_blank_pallet_labels,
        generate_and_print_combo_label, upload_pallet_label_data_to_printers,
        # printer data
        validate_printer_connection, ip_in_range, resolve_site_from_request,
        get_all_printer_connections, get_printers_for_site,
        get_printers_on_site, get_pallet_label_printer,
        # config/json
        load_printers_from_file, load_site_ip_ranges, load_box_label_variables,
        load_pallet_label_variables, get_label_variables, load_all_config_data,
        label_printers_full_list, site_ip_ranges,
    )

Keep this file light: only imports/re-exports; no I/O at import time.
"""

# --- Box label ---
from .box_labels import (
    apply_zpl_placeholders,
    load_label_template_from_env,
    main_print_box_label_function,
    upload_box_label_structures_to_printers,
)

# --- Internal label ---
from .internal_label_controller import blend_label_function

# --- JSON/config helpers & in-memory stores ---
from .json_readers import (
    get_label_variables,
    label_printers_full_list,
    load_all_config_data,
    load_box_label_variables,
    load_pallet_label_variables,
    load_printers_from_file,
    load_site_ip_ranges,
    site_ip_ranges,
)

# --- Pallet label ---
from .pallet_labels import (
    generate_and_print_combo_label,
    main_pallet_label_function,
    print_blank_pallet_labels,
    upload_pallet_label_data_to_printers,
)

# --- Printer data / site resolution ---
from .printers import (
    get_all_printer_connections,
    get_pallet_label_printer,
    get_printers_for_site,
    get_printers_on_site,
    ip_in_range,
    resolve_site_from_request,
    validate_printer_connection,
)

__all__ = [
    # box
    "main_print_box_label_function",
    "upload_box_label_structures_to_printers",
    "load_label_template_from_env",
    "apply_zpl_placeholders",
    # internal
    "blend_label_function",
    # pallet
    "main_pallet_label_function",
    "print_blank_pallet_labels",
    "generate_and_print_combo_label",
    "upload_pallet_label_data_to_printers",
    # printer data
    "validate_printer_connection",
    "ip_in_range",
    "resolve_site_from_request",
    "get_all_printer_connections",
    "get_printers_for_site",
    "get_printers_on_site",
    "get_pallet_label_printer",
    # json/config
    "load_printers_from_file",
    "load_site_ip_ranges",
    "load_box_label_variables",
    "load_pallet_label_variables",
    "get_label_variables",
    "load_all_config_data",
    "label_printers_full_list",
    "site_ip_ranges",
]
