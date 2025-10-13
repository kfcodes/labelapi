from http import HTTPStatus
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, conint

# Controller now returns (zpl, role, label_size)
from app.controllers.box_labels import main_print_box_label_function
from app.controllers.printers import get_printers_on_site  # async, takes Request
from app.printer_connection.zpl_printer_logic import label_printer_connection

box_label_router = APIRouter()


class BoxLabelRequest(BaseModel):
    quantity: conint(gt=0, le=100000) = Field(
        ..., description="Number of labels to print"
    )
    line: Optional[str] = Field(None, description="Preferred production line")
    role: Optional[Literal["large", "small"]] = Field(
        None, description="Override printer role"
    )
    dry_run: Optional[bool] = Field(
        True, description="If true, return ZPL instead of printing"
    )
    model_config = ConfigDict(extra="allow")


@box_label_router.post("/box_label/{unique_finished_product_id}")
async def print_box_label(
    request: Request, unique_finished_product_id: int, body: BoxLabelRequest
) -> Dict[str, Any]:
    """
    Build ZPL (controller), then select printer and print at the route layer.
    """
    try:
        # 1) ZPL + recommended role from controller (respects override)
        zpl, role, label_size = await main_print_box_label_function(
            unique_id=unique_finished_product_id,
            quantity=int(body.quantity),
            explicit_role=body.role,
        )

        # 2) Resolve available printers for the caller's site
        printers_by_line = await get_printers_on_site(request)
        if not printers_by_line:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="No printers configured for site",
            )

        # 3) Choose line (prefer requested; else first in sorted order)
        if body.line:
            if body.line not in printers_by_line:
                available = ", ".join(sorted(printers_by_line.keys()))
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail=f"Unknown line '{body.line}'. Available lines: {available}",
                )
            selected_line = body.line
        else:
            selected_line = next(iter(sorted(printers_by_line.keys())))

        line_printers = printers_by_line[selected_line]

        # 4) Ensure a printer exists for the chosen role; fall back to the other if missing
        selected_role = role
        if selected_role not in line_printers:
            alt = "small" if selected_role == "large" else "large"
            if alt not in line_printers:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=f"Line '{selected_line}' has no usable printers (needs 'large' or 'small').",
                )
            selected_role = alt

        printer = line_printers[selected_role]
        if (
            not isinstance(printer, dict)
            or "ip" not in printer
            or "port" not in printer
        ):
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Printer config for line '{selected_line}' role '{selected_role}' must include 'ip' and 'port'.",
            )

        # 5) Print or dry-run
        dry_run = True if body.dry_run is None else body.dry_run
        if dry_run:
            return {
                "status": "ok",
                "response": zpl,
                "selected_line": selected_line,
                "role": selected_role,
                "label_size": label_size,
                "printer": {"ip": printer["ip"], "port": printer["port"]},
                "dry_run": True,
            }

        resp = label_printer_connection(
            zpl, printer["ip"], printer["port"], timeout=3.0
        )
        return {
            "status": "ok",
            "response": resp,
            "selected_line": selected_line,
            "role": selected_role,
            "label_size": label_size,
            "printer": {"ip": printer["ip"], "port": printer["port"]},
            "dry_run": False,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_GATEWAY, detail=str(e)) from e


@box_label_router.get("/check/{product_id}")
async def box_label_check(product_id: str):
    raise HTTPException(status_code=501, detail="box_label_check not implemented")
