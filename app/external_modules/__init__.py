"""
Convenience re-exports for external modules.

Usage:
    from app.external_modules import (
        label_printer_connection,
        create_box_label_zpl,
        create_blend_label_zpl,
        create_pallet_label_zpl,
        create_combined_pallet_label_data,
    )
"""

from .printer_connection_logic import label_printer_connection
from .zpl_logic import (
    create_blend_label_zpl,
    create_box_label_zpl,
    create_combined_pallet_label_data,
    create_pallet_label_zpl,
)

__all__ = [
    "label_printer_connection",
    "create_box_label_zpl",
    "create_blend_label_zpl",
    "create_pallet_label_zpl",
    "create_combined_pallet_label_data",
]
