from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv

from app.database.read_db import read_db, read_to_list_index

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / "env" / "queries.env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)


async def get_box_label_metadata_by_product_code(product_ids: tuple) -> Optional[dict]:
    label_metadata = str(f"{os.getenv('METADATA')}")
    # print(label_metadata.format(str(product_ids)))
    data = read_db(label_metadata.format(str(product_ids))) or ()

    return data


async def get_unique_box_label_info(
    unique_finished_product_id: int,
    blend_id: int,
) -> Optional[dict]:

    unique_label_data = str(f"{os.getenv('UNIQUE_DATA')}")
    # print(unique_label_data.format(int(blend_id), int(unique_finished_product_id)))

    data = (
        read_db(
            unique_label_data.format(int(blend_id), int(unique_finished_product_id))
        )
        or []
    )

    return data[0]


async def a_get_label_context_for_brand(brand_id: int) -> Optional[Dict[str, Any]]:
    return await to_thread.run_sync(get_label_context_for_brand, brand_id)


async def a_get_required_eol_values(eol_id: int, keys: Sequence[str]) -> Dict[str, Any]:
    return await to_thread.run_sync(get_required_eol_values, eol_id, keys)


def get_brand_id_for_product(product_code: str) -> Optional[Dict[str, Any]]:
    label_metadata = str(f"{os.getenv('BRAND_ID_FOR_PRODUCT')}")
    data = read_to_list_index(label_metadata.format(str(product_code))) or ()

    return data[0] if rows else None


def get_required_fields_for_label(label_type_id: int) -> List[str]:
    label_metadata = str(f"{os.getenv('GET_REQUIRED_FIELDS_FOR_LABEL')}")
    data = read_to_list_index(label_metadata.format(str(label_type_id))) or ()

    return data[0] if rows else None


def get_barcode_formats_for_type(label_type_id: int) -> List[Dict[str, Any]]:
    label_metadata = str(f"{os.getenv('GET_BARCODE_FORMATS_FOR_TYPE')}")
    data = read_to_list_index(label_metadata.format(str(label_type_id))) or ()

    return data[0] if rows else None


def get_box_label_variables() -> BoxVariables:

    label_metadata = str(f"{os.getenv('GET_BOX_LABEL_VARIABLES')}")
    if not label_metadata:
        raise RuntimeError("GET_BOX_LABEL_VARIABLES env var is not set")

    # This gives you: [{'key': 1, 'value': 'product_description'}, ...]
    rows: list[Dict[str, Any]] = read_to_list_index(label_metadata) or []

    # Convert list-of-dicts -> {value: key} mapping
    mapping: BoxVariables = {
        str(row["value"]): int(row["key"])
        for row in rows
        if row.get("key") is not None and row.get("value") is not None
    }

    print(mapping)
    return mapping
