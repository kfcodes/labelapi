from http import HTTPStatus
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, conint

from app.controllers.box_labels import main_print_box_label_function

box_label_router = APIRouter()


class BoxLabelRequest(BaseModel):
    quantity: conint(gt=0, le=100000) = Field(
        ..., description="Number of labels to print"
    )
    # Optional: prefer a specific production line (e.g. 'line1'); controller will validate/fallback
    line: Optional[str] = Field(None, description="Preferred production line")
    # Optional: override role ('large' | 'small'); if not given, controller derives from label_size
    role: Optional[Literal["large", "small"]] = Field(
        None, description="Override printer role"
    )
    # Optional: return ZPL instead of printing (defaults True for safety)
    dry_run: Optional[bool] = Field(
        True, description="If true, return ZPL instead of printing"
    )

    # Keep your existing permissive behavior for forward compatibility
    model_config = ConfigDict(extra="allow")


@box_label_router.post("/box_label/{unique_finished_product_id}")
async def print_box_label(
    request: Request, unique_finished_product_id: int, body: BoxLabelRequest
) -> Dict[str, Any]:
    """
    Print a box label. Controller resolves site from the request, selects printer (large/small)
    and either returns ZPL (dry run) or sends it to the printer.
    """
    try:
        resp = await main_print_box_label_function(
            request=request,
            unique_id=unique_finished_product_id,
            quantity=int(body.quantity),
            line=body.line,
            role=body.role,
            dry_run=True if body.dry_run is None else body.dry_run,
        )
        return {"status": "ok", "response": resp}
    except HTTPException:
        raise
    except ValueError as e:
        # Controller uses ValueError for bad input/missing data (e.g., unknown id, no printers)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except Exception as e:
        # Unexpected downstream/IO issues (e.g., printer connection)
        raise HTTPException(status_code=HTTPStatus.BAD_GATEWAY, detail=str(e)) from e


# Placeholder for the old “box_label_check”
@box_label_router.get("/check/{product_id}")
async def box_label_check(product_id: str):
    raise HTTPException(status_code=501, detail="box_label_check not implemented")
