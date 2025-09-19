from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.controllers import (  # we’ll derive the correct printer from the request/site
    get_printers_on_site,
    main_print_box_label_function,
)

box_label_router = APIRouter()


class BoxLabelRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Number of labels to print")
    # Optional: choose a specific production line; else first available line is used
    line: str | None = None
    model_config = ConfigDict(extra="allow")


@box_label_router.post("/print/{unique_finished_product_id}")
async def print_box_label(
    request: Request, unique_finished_product_id: int, body: BoxLabelRequest
) -> Dict[str, Any]:
    """
    Print a box label. Chooses the printer pair (large/small) from site+line.
    """
    try:
        # Get available printers for the resolved site
        printers_by_line = await get_printers_on_site(request)
        if not printers_by_line:
            raise HTTPException(
                status_code=404, detail="No printers configured for site"
            )

        # Pick a line (use requested line if valid, else first available)
        selected = None
        if body.line and body.line in printers_by_line:
            selected = printers_by_line[body.line]
        else:
            # first non-empty line
            selected = next(iter(printers_by_line.values()))

        # Controller expects (unique_id, quantity, printer_dict)
        resp = await main_print_box_label_function(
            unique_finished_product_id,
            body.quantity,
            selected,  # must contain {"large": {...}, "small": {...}}
        )
        return {"status": "ok", "response": resp}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Placeholder for the old “box_label_check” which doesn’t exist in controllers you shared.
# Keep it returning 501 until you implement a real check.
@box_label_router.get("/check/{product_id}")
async def box_label_check(product_id: str):
    raise HTTPException(status_code=501, detail="box_label_check not implemented")
