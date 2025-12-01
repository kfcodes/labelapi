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
    # if barcode_format is not null format barcode otherwise leave alone
    # ^FN^FD{values.get("barcode_format", "")}^FS
    # barcode_format
    # apply the varaibles then to the string and append the barcode to the end

    return f"""
^XA
^PQ{int(quantity)}
^XFE:{values.get("template_name", "")}.ZPL^FS
^FN999^FD{values.get("", "")}^FS

^FN1^FD{values.get("customer_po_id", "")}^FS

^FN3^FD{values.get("product_description", "")}^FS

^FX Product Metadata
^FN4^FD{values.get("brand_name", "")}^FS
^FN6^FD{values.get("customer_specified_description", "")}^FS
^FN7^FD{values.get("product_group", "")}^FS
^FN9^FD{values.get("flavour", "")}^FS
^FN11^FD{values.get("sku_code", "")}^FS
^FN12^FD{values.get("unit_net_weight", "")}^FS
^FN13^FD{values.get("case_unit_quantity", "")}^FS

^FX Unique Identifying information
^FN16^FD{values.get("lot_code", "")}^FS
^FN17^FD{values.get("bbe_code", "")}^FS
^FN18^FD{values.get("batch_code", "")}^FS
^FN20^FD{values.get("unit_gtin", "")}^FS
^FN21^FD{values.get("case_gtin", "")}^FS

^XZ
"""


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
    return "large" if is_large else "small"


async def main_box_label_function(
    unique_finished_product_id: int,
    blend_id: int,
    quantity: int,
) -> Tuple[str, str]:

    data = await get_unique_box_label_info(unique_finished_product_id, blend_id)

    if data is None:
        raise ValueError(
            f"No box label data found for finished_product_id={unique_finished_product_id}"
        )

    # print(data)
    label_size = _label_is_large(data["label_type_size_is_large"])

    label_text_zpl = _build_label_object_string(data, quantity)
    print(label_text_zpl)

    return label_size, label_text_zpl


async def check_box_label_exists(product_ids: tuple) -> str:

    meta = await get_box_label_metadata_by_product_code(product_ids)
    if meta is None:
        return None

    print(meta)
    # print(meta.get("product_description"))
    return meta[0].get("product_description")
    # return {
    #     product_id: meta.get("product_description") for product_id, meta in info.items()
    # }
