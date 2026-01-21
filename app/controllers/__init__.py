from __future__ import annotations

from .box_labels import main_box_label_function
from .config_loader import load_all_config_data
from .internal_labels import (
    blank_pallet_labels,
    goodsin_label_function,
    internal_product_id_and_description,
    large_blend_label_function,
    small_blend_label_function,
)
from .label_structure_uploader import (
    upload_box_label_structures_to_printers,
    upload_internal_label_structures_to_printers,
    upload_pallet_label_structures_to_printers,
)
from .pallet_labels import (
    generate_and_print_combo_label,
    main_pallet_label_function,
    print_blank_pallet_labels,
)
from .printers import (
    get_all_printer_connections,
    get_pallet_label_printer,
    get_printers_for_site,
    get_printers_on_site,
    resolve_site_id_from_request,
)
from .test_labels import test_label_function

__all__ = [
    # startup
    "load_all_config_data",
    # internal
    "internal_product_id_and_description",
    "large_blend_label_function",
    "small_blend_label_function",
    "blank_pallet_labels",
    # box
    "main_box_label_function",
    # pallet
    "main_pallet_label_function",
    "print_blank_pallet_labels",
    "generate_and_print_combo_label",
    # upload labels
    "upload_box_label_structures_to_printers",
    "upload_pallet_label_structures_to_printers",
    "upload_internal_label_structures_to_printers",
    # printers
    "resolve_site_id_from_request",
    "get_printers_for_site",
    "get_printers_on_site",
    "get_pallet_label_printer",
    "get_all_printer_connections",
    "test_label_function",
    "goodsin_label_function",
]
