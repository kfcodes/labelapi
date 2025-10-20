from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TypedDict

from app.database import (
    a_get_brand_id_for_product as get_brand_id_for_product,
)  # product_id: str -> Optional[int]
from app.database import (
    a_get_label_context_for_brand as get_required_fields_for_label,
)  # brand_id: int -> Optional[dict]
from app.database import (
    a_get_required_eol_values as get_finished_product_details,
)  # (eol_id: int, keys: List[str]) -> Dict[str, Any]


class LabelTypeContext(TypedDict, total=False):
    company_id: int
    company_name: str
    label_type_id: int
    zpl_name: str
    size_is_large: int
    label_fields: List[str]
    barcode_formats: List[str]


async def get_brand_id(product_id: str) -> Dict[str, Any]:
    """
    Resolve the brand/company id for a given product_id (string).
    Returns: {"ok": bool, "errors": List[str], "brand_id": Optional[int]}
    """
    result: Dict[str, Any] = {"ok": False, "errors": [], "brand_id": None}
    brand_id = await get_brand_id_for_product(product_id)
    if brand_id is None:
        result["errors"].append(f"No brand/company found for product_id={product_id}.")
        return result
    result["ok"] = True
    result["brand_id"] = int(brand_id)
    return result


async def get_label_fields(brand_id: int) -> Dict[str, Any]:
    """
    Given a brand/company id (int), fetch the label/type context and return fields.
    Returns:
      {
        "ok": bool,
        "errors": List[str],
        "fields": List[str],            # required label fields (ordered, deduped)
        "context": LabelTypeContext|{}, # passthrough (optional)
      }
    """
    out: Dict[str, Any] = {"ok": False, "errors": [], "fields": [], "context": {}}

    ctx: Optional[LabelTypeContext] = await get_required_fields_for_label(brand_id)
    if not ctx:
        out["errors"].append(f"No label context found for brand_id={brand_id}.")
        return out

    # Preserve order, dedupe
    seen = set()
    fields = [
        k for k in (ctx.get("label_fields") or []) if not (k in seen or seen.add(k))
    ]

    out["ok"] = True
    out["fields"] = fields
    out["context"] = ctx
    return out


async def generate_label_structure(
    *,
    required_fields: List[str],
    eol_id: int,
    batch_id: str,
) -> str:
    """
    Build the label structure string (JSON) by projecting only the requested fields
    from EOL, merging batch_id/lot, and reporting any missing fields.
    Returns a STRING suitable for printing to console.
    """
    # Get only what the label actually requires
    eol_values: Dict[str, Any] = await get_finished_product_details(
        eol_id, required_fields
    )

    # Compose working record (batch/lot are merged but NOT required)
    record: Dict[str, Any] = {
        **eol_values,
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
        "extras": {"batch_id": batch_id, "lot": batch_id},  # exposed for downstream
    }

    # Return as a pretty JSON string for direct console printing
    return json.dumps(structure, indent=2, ensure_ascii=False)


async def main_box_label_function(
    *,
    product_id: int,
    eol_id: int,
    batch_id: str,
) -> str:
    """
    Main function:
      1) fetch fields from product_id
      2) generate label structure with eol_id + batch_id
      3) print and return the JSON string
    """
    step1 = await get_label_fields(product_id)
    if not step1["ok"]:
        s = json.dumps(step1, indent=2, ensure_ascii=False)
        print(s)
        return s

    s = await generate_label_structure(
        required_fields=step1["fields"],
        eol_id=eol_id,
        batch_id=batch_id,
    )
    print(s)
    return s
