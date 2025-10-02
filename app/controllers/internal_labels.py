from __future__ import annotations

from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.zpl.internal_label_zpl_logic import (
    create_blank_label_zpl,
    create_blend_label_zpl,
    create_id_with_description,
)


async def internal_product_id_and_description(product_id, quantity, printer):
    try:
        label_structure_name = "INTLBLND"
        product_description = get_product_description(product_id)
        pallet_label_zpl = create_id_with_description(
            label_structure_name, product_id, product_description, quantity
        )
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def large_blend_label_function(body, printer):
    try:
        label_structure_name = "INTLBLND"
        pallet_label_zpl = create_blend_label_zpl(
            label_structure_name, body["blend_id"], body["allergens"]
        )
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def small_blend_label_function(printer):
    try:
        label_structure_name = "INTSBLND"
        pallet_label_zpl = create_blank_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def blank_pallet_labels(printer):
    try:
        label_structure_name = "INTLBLNK"
        pallet_label_zpl = create_blank_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)
