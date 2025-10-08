from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, Union

from dotenv import load_dotenv

from app.database.read_db import read_db, read_to_list_index
from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.zpl.internal_label_zpl_logic import (
    create_blank_label_zpl,
    create_blend_label_zpl,
    create_id_with_description,
)

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / "env" / "label_variables.env")


async def internal_product_id_and_description(product_id, quantity, printer):
    try:

        label_structure_name = "INTLPREP"

        product_description = read_to_list_index(
            str(os.getenv("GETPRODUCTDESCRIPTION")).format(product_id)
        )
        product_description = product_description[0]["product_description"]
        print("List_index")
        print(product_description)

        pallet_label_zpl = create_id_with_description(
            label_structure_name,
            str.upper(product_id),
            str.upper(product_description),
            quantity,
        )

        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )

        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def large_blend_label_function(body, printer):
    try:
        label_structure_name = "INTLBULK"
        print(body)
        pallet_label_zpl = create_blend_label_zpl(
            label_structure_name, body["blend_id"], body["allergens"]
        )
        print(pallet_label_zpl)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def small_blend_label_function(printer):
    try:
        label_structure_name = "INTSBULK"
        pallet_label_zpl = create_blank_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def blank_pallet_labels(printer):
    try:
        label_structure_name = "INTLPLBK"
        pallet_label_zpl = create_blank_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)
