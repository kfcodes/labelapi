from __future__ import annotations

import json
from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from app.database import (
    get_box_label_metadata_by_product_code,
    get_unique_box_label_info,
)
from app.static_json_readers import get_box_variables


def _build_label_object_string(values: dict, quantity: int) -> str:
    return (
        "^XA"
        f"^PQ{int(quantity)}"
        f'^FN1^FD{values.get("barcode_format", "")}^FS'
        f'^FN2^FD{values.get("batch_code", "")}^FS'
        f'^FN3^FD{values.get("batch_number_only", "")}^FS'
        f'^FN4^FD{values.get("bbe_code", "")}^FS'
        f'^FN5^FD{values.get("blend_date", "").strftime("%d/%m/%Y") if hasattr(values.get("blend_date", ""), "strftime") else values.get("blend_date", "")}^FS'
        f'^FN6^FD{values.get("case_gross_weight_kg", "")}^FS'
        f'^FN7^FD{values.get("case_gtin", "")}^FS'
        f'^FN8^FD{values.get("case_unit_quantity", "")}^FS'
        f'^FN9^FD{values.get("customer_po_number", "")}^FS'
        f'^FN10^FD{values.get("customer_specified_description", "")}^FS'
        f'^FN11^FD{values.get("customer_specified_flavour", "")}^FS'
        f'^FN12^FD{values.get("customer_specified_product_group", "")}^FS'
        f'^FN13^FD{values.get("id", "")}^FS'
        f'^FN14^FD{values.get("internal_sku_code", "")}^FS'
        f'^FN15^FD{values.get("label_brand_name", "")}^FS'
        f'^FN16^FD{values.get("label_type_size_is_large", "")}^FS'
        f'^FN17^FD{values.get("label_type_zpl_name", "")}^FS'
        f'^FN18^FD{values.get("lot_code", "")}^FS'
        f'^FN19^FD{values.get("product_description", "")}^FS'
        f'^FN20^FD{values.get("quantity_on_order", "")}^FS'
        f'^FN21^FD{values.get("sku", "")}^FS'
        f'^FN22^FD{values.get("unit_gross_weight_kg", "")}^FS'
        f'^FN23^FD{values.get("unit_gtin", "")}^FS'
        f'^FN24^FD{values.get("unit_net_weight", "")}^FS'
        "^XZ"
    )


def _label_is_large(value: int | bool | str) -> str:
    if isinstance(value, str):
        value = value.strip()
    is_large = False
    if value in (1, "1", True):
        is_large = True
    elif value in (0, "0", False):
        is_large = False
    else:
        raise ValueError(f"Invalid size flag: {value!r}. Expected 1/0 or True/False.")
    return "Large" if is_large else "Small"


async def main_box_label_function(
    unique_finished_product_id: int,
    blend_id: int,
    quantity: int,
) -> Tuple[str, str]:

    data = await get_unique_box_label_info(unique_finished_product_id, blend_id)

    pprint(data)

    if data is None:
        raise ValueError(
            f"No box label data found for finished_product_id={unique_finished_product_id}"
        )

    label_size = _label_is_large(data["label_type_size_is_large"])

    label_text_zpl = _build_label_object_string(data, quantity)

    return label_size, label_text_zpl


async def check_box_label_exists(product_ids: list) -> str:
    meta = await get_box_label_metadata_by_product_code(product_ids)
    if meta is None:
        return None

    print(meta)
    # print(meta.get("product_description"))
    return meta[0].get("product_description")
    # return {
    #     product_id: meta.get("product_description") for product_id, meta in info.items()
    # }
