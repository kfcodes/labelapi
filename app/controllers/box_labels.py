from __future__ import annotations

import json
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

    # pprint(data)
    label_size = _label_is_large(meta["label_size"])

    label_text_zpl = _build_label_object_string(meta["template_name"], data, quantity)
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
