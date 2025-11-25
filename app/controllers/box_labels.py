from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from box_label_json_reader import get_box_variables  # <- this is the key one

from app.database import (get_box_label_metadata_by_product_code,
                          get_unique_box_label_info)
from app.static_json_readers.box_label_json_reader import get_box_variables


def _build_label_object_string(values: Dict[str, Any]) -> str:
    vars_map = get_box_variables()  # e.g. {"brand": 1, "product_description": 2, ...}
    parts: list[str] = []
    for field_name, fn_number in vars_map.items():
        if field_name not in values:
            continue
        raw_value = values[field_name]
        value_str = "" if raw_value is None else str(raw_value)
        parts.append(f"FN{fn_number}FD{value_str}FS")
    return "".join(parts)

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
) -> Tuple[str, str]:

    # SINGLE DB CALL – returns all necessary information as a dict.
    data: Optional[BoxLabelData] = await get_unique_box_label_info(
        unique_finished_product_id
    )

    if data is None:
        raise ValueError(
            f"No box label data found for finished_product_id={unique_finished_product_id}"
        )

     label_text_zpl = _build_label_object_string(data)

    label_text = json.dumps(label_text_zpl, indent=2, ensure_ascii=False)

    label_size = _label_is_large(data["label_size"])

    return label_size, label_text


async def check_box_label_exists(product_ids: list) -> str:
    """
    Returns only the box label description for the given product_id.
    """
    meta = await get_box_label_metadata_by_product_code(product_ids)
    if meta is None:
        return None

    return meta.get("product_description")
