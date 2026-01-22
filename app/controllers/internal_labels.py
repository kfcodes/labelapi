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
    create_goodsin_label_zpl,
    create_id_with_description,
)

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / "env" / "label_variables.env")


def _build_goodsin_barcode(unit_id: int) -> str:
    uid = str(int(unit_id)).zfill(14)
    return f"{uid}"


async def internal_product_id_and_description(product_id, quantity, printer):
    try:

        label_structure_name = "IN_DESCR"

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
        label_structure_name = "IN_BULK"
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
        label_structure_name = "IN_MICRO"
        pallet_label_zpl = create_blank_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def goodsin_label_function(labels: list[dict], printer: dict):
    try:
        label_structure_name = "GOODSIN"

        full_zpl = create_goodsin_labels_zpl(
            label_structure_name=label_structure_name,
            labels=labels,
        )

        print("\n" + "=" * 80)
        print("🖨️ FULL GOODS-IN ZPL (ALL LABELS)")
        print("=" * 80)
        print(full_zpl)
        print("=" * 80 + "\n")

        return label_printer_connection(
            full_zpl,
            printer["ip"],
            printer["port"],
        )

    except Exception as ex:
        print("❌ Goods-in labels could not be created:\n", ex)
        raise


def create_goodsin_labels_zpl(label_structure_name: str, labels: list[dict]) -> str:
    zpl_parts: list[str] = []

    required_keys = {
        "product_id",
        "intake_date",
        "weight_kg",
        "batch_code",
        "unit_id",
        "unit_index",
        "labels_requested",
        "product_description",
    }
    optional_keys = {"order_no"}

    for i, item in enumerate(labels, start=1):
        missing = required_keys - item.keys()
        if missing:
            raise KeyError(f"Label #{i} missing keys: {sorted(missing)}")

        zpl_parts.append(
            create_goodsin_label_zpl(
                label_structure_name=label_structure_name,
                product_id=item["product_id"],
                intake_date=item["intake_date"],
                order_no=item.get("order_no"),
                weight_kg=item["weight_kg"],
                batch_code=item["batch_code"],
                labels_requested=item.get("labels_requested"),
                product_description=item["product_description"],
                barcode=_build_goodsin_barcode(item["unit_id"]),
            )
        )
    return "\n".join(zpl_parts)


async def blank_pallet_labels(printer):
    try:
        label_structure_name = "IN_PBLNK"
        pallet_label_zpl = create_blank_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Label could not be created due to: \n", ex)
