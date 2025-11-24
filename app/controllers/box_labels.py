from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, TypedDict

# These DB accessors should each perform a SINGLE DB query and return
# all needed data in one go (no additional DB calls from this controller).
#
# a_get_box_label_data_by_finished_id:
#   input:  unique_finished_product_id: int
#   output: Optional[BoxLabelData]
#
# a_get_box_label_metadata_by_product_code:
#   input:  product_id: str
#   output: Optional[BoxLabelMetadata]
from app.database import (
    a_get_box_label_data_by_finished_id as get_box_label_data_by_finished_id,
)
from app.database import (
    a_get_box_label_metadata_by_product_code as get_box_label_metadata_by_product_code,
)


class LabelTypeContext(TypedDict, total=False):
    company_id: int
    company_name: str
    label_type_id: int
    zpl_name: str
    size_is_large: int  # 1 = large, 0 = small
    label_fields: List[str]
    barcode_formats: List[str]


class BoxLabelData(TypedDict):
    """
    Shape of the data returned by get_box_label_data_by_finished_id.

    Adapt keys to whatever your DB function returns, but keep enough information
    here to build the label and determine size.
    """

    # Identity / linkage
    finished_product_id: int
    brand_id: int
    eol_id: int
    batch_id: str

    # Label configuration
    label_context: LabelTypeContext
    required_fields: List[str]

    # Actual values for those fields (already fetched from EOL/product tables)
    values: Dict[str, Any]


class BoxLabelMetadata(TypedDict, total=False):
    """
    Lightweight metadata shape for the /check/{product_id} endpoint.

    You can expand this as needed, as long as it comes from a single DB call.
    """

    product_id: str
    brand_id: int
    label_context: LabelTypeContext
    required_fields: List[str]


# ---------------------------------------------------------------------------
# Pure helpers – no DB calls
# ---------------------------------------------------------------------------


def _build_label_structure_from_values(
    *,
    required_fields: List[str],
    values: Dict[str, Any],
    eol_id: int,
    batch_id: str,
) -> Dict[str, Any]:
    """
    Build the label structure dict using ONLY the values already provided.

    No database access here – everything must come from the single DB call.
    """
    # Compose working record: merge values + batch/lot (not required)
    record: Dict[str, Any] = {
        **values,
        "batch_id": batch_id,
        "lot": batch_id,
    }

    missing = [k for k in required_fields if record.get(k) in (None, "", [], {}, ())]
    ok = len(missing) == 0

    structure = {
        "ok": ok,
        "missing_required_fields": missing,
        "inputs": {"eol_id": eol_id, "batch_id": batch_id},
        "required_fields": required_fields,
        "values": {k: record.get(k) for k in required_fields},  # only requireds
        "extras": {"batch_id": batch_id, "lot": batch_id},
    }
    return structure


def _derive_label_size_from_context(context: LabelTypeContext) -> str:
    """
    Decide label_size string from the label context.

    Uses size_is_large if present; otherwise falls back to "default".
    """
    size_is_large = context.get("size_is_large")
    if size_is_large is None:
        return "default"
    return "large" if int(size_is_large) == 1 else "small"


# ---------------------------------------------------------------------------
# MAIN: single-call controller used by the /box_label/{id}/{qty} route
# ---------------------------------------------------------------------------


async def main_box_label_function(
    unique_finished_product_id: int,
) -> Tuple[str, str]:
    """
    Main box label generator.

    INPUT:
        unique_finished_product_id: internal finished product id (int)

    Single DB call:
        - get_box_label_data_by_finished_id(unique_finished_product_id)

    OUTPUT:
        (label_size, label_text)

        - label_size: string label size identifier ("large" | "small" | "default" | etc.)
        - label_text: full label payload for a SINGLE label
                      (currently JSON string; you can swap to ZPL if you want)
    """

    # SINGLE DB CALL – returns all necessary information as a dict.
    data: Optional[BoxLabelData] = await get_box_label_data_by_finished_id(
        unique_finished_product_id
    )

    if data is None:
        raise ValueError(
            f"No box label data found for finished_product_id={unique_finished_product_id}"
        )

    # Unpack the single DB result
    eol_id: int = data["eol_id"]
    batch_id: str = data["batch_id"]
    required_fields: List[str] = data["required_fields"]
    values: Dict[str, Any] = data["values"]
    context: LabelTypeContext = data["label_context"]

    # Build the label structure purely from the data we already have.
    structure = _build_label_structure_from_values(
        required_fields=required_fields,
        values=values,
        eol_id=eol_id,
        batch_id=batch_id,
    )

    # Convert structure to a string (this is your "label_text").
    # If you'd prefer ZPL, you'd replace this with a ZPL builder.
    label_text = json.dumps(structure, indent=2, ensure_ascii=False)

    # Derive label_size (large/small/default, etc.) from the context
    label_size = _derive_label_size_from_context(context)

    # Return tuple in the order the router expects
    return label_size, label_text


# ---------------------------------------------------------------------------
# CHECK: single-call metadata lookup for /check/{product_id}
# ---------------------------------------------------------------------------


async def check_box_label_exists(
    product_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Check whether label information exists for a given *string* product_id.

    SINGLE DB CALL:
        - get_box_label_metadata_by_product_code(product_id)

    Returns:
        dict with info if label config exists, or None if not.

        Example response:
        {
          "product_id": "...",
          "brand_id": 123,
          "fields": [...],
          "label_size": "large" | "small" | "default",
          "context": {...}
        }
    """
    meta: Optional[BoxLabelMetadata] = await get_box_label_metadata_by_product_code(
        product_id
    )
    if meta is None:
        return None

    required_fields: List[str] = meta.get("required_fields", [])
    context: LabelTypeContext = meta.get("label_context", {})  # type: ignore[assignment]
    label_size = _derive_label_size_from_context(context)

    return {
        "product_id": product_id,
        "brand_id": int(meta["brand_id"]),
        "fields": required_fields,
        "label_size": label_size,
        "context": context,
    }
