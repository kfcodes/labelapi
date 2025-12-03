from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from app.database import (
    get_box_label_metadata,
    get_box_label_metadata_by_product_code,
    get_unique_box_label_info,
)
from app.static_json_readers import get_box_variables


def _build_label_object_string(name: str, values: dict, quantity: int) -> str:
    """
    name: ZPL template name (without .ZPL extension)
    values: dict[int, str | None] mapping FN number -> FD value
    quantity: number of labels to print
    """

    # Build the FN/FD lines from the dict
    fn_lines = []
    for fn, field_value in sorted(values.items()):
        fd_text = "" if field_value is None else str(field_value)
        fn_lines.append(f"^FN{fn}^FD{fd_text}^FS")

    fn_block = "\n".join(fn_lines)

    # Build the full label object string
    return f"""
^XA
^XFE:{name}.ZPL^FS
^PQ{int(quantity)}
{fn_block}
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


def _format_unit_net_weight(raw: str | None) -> str:
    """
    Format unit_net_weight so that:
      - If value < 1 (e.g. 0.03000), treat as kg and convert to grams.
      - Trim trailing zeros after the decimal.
      - No decimal point if it's an integer (50g, not 50.0g).
    """
    if raw in (None, ""):
        return ""

    s = str(raw).strip()

    try:
        dec = Decimal(s)
    except InvalidOperation:
        # Not a number? Return as-is.
        return s

    if dec == 0:
        return "0g"

    # Check if there's anything before the decimal in the original string
    if "." in s:
        int_part, _ = s.split(".", 1)
    else:
        int_part = s

    # If no number above the decimal -> convert kg → g
    if int_part in ("0", "-0"):
        grams = dec * Decimal("1000")

        # normalize() removes trailing zeros; {:f} avoids scientific notation
        grams_str = "{:f}".format(grams.normalize()).rstrip(".")

        return f"{grams_str}g"

    # Otherwise, treat as kg, but still trim trailing zeros
    kg_str = "{:f}".format(dec.normalize()).rstrip(".")

    return f"{kg_str}Kg"


async def main_box_label_function(
    unique_finished_product_id: int,
    blend_id: int,
    quantity: int,
) -> Tuple[str, str]:

    meta = await get_box_label_metadata(unique_finished_product_id)

    data = await get_unique_box_label_info(unique_finished_product_id, blend_id)

    if data is None:
        raise ValueError(
            f"No box label data found for finished_product_id={unique_finished_product_id}"
        )

    # if "unit_net_weight" in data:
    if 7 in data:
        data[7] = _format_unit_net_weight(data[7])
        pprint(data)

    label_size = _label_is_large(meta["label_size"])

    label_text_zpl = _build_label_object_string(meta["template_name"], data, quantity)

    print(label_text_zpl)

    return label_size, label_text_zpl


async def check_box_label_exists(product_ids: tuple) -> str:

    meta = await get_box_label_metadata_by_product_code(product_ids)
    if meta is None:
        return None

    rows = list(meta.values())  # print(meta.get("product_description"))
    # return meta[0].get("product_description")

    return rows

    # return {
    #     product_id: meta.get("product_description") for product_id, meta in info.items()
    # }
