from http import HTTPStatus
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, conint, constr

from app.controllers.box_labels import check_box_label_exists, main_box_label_function
from app.controllers.printers import get_printers_on_site  # async, takes Request
from app.printer_connection.zpl_printer_logic import label_printer_connection

box_label_router = APIRouter()

# Type for a single product ID: starts with a letter, then letters/digits, max length 60
ProductID = constr(
    min_length=1,
    max_length=60,
    pattern=r"^[A-Za-z][A-Za-z0-9]{0,59}$",
)


class BoxLabelCheckRequest(BaseModel):
    product_ids: List[ProductID]


class PrintBoxLabelRequest(BaseModel):
    unique_finished_product_id: int
    blend_id: int
    quantity: int


@box_label_router.post("/box_label")
async def print_box_label(
    request: Request,
    body: PrintBoxLabelRequest,
) -> Dict[str, Any]:
    unique_finished_product_id = body.unique_finished_product_id
    blend_id = body.blend_id
    quantity = body.quantity

    if quantity <= 0:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Quantity must be greater than zero.",
        )

    try:
        label_size, label_zpl = await main_box_label_function(
            unique_finished_product_id, blend_id, quantity
        )

        # 3) Resolve printers for the caller's site
        printers_by_line = await get_printers_on_site(request)
        if not printers_by_line:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="No printers configured for site",
            )

        # For now: just pick the first line in sorted order
        selected_line = next(iter(sorted(printers_by_line.keys())))
        line_printers = printers_by_line[selected_line]
        # print("printers", line_printers)

        # 4) Decide printer based on label size
        desired_role: Literal["large", "small"] = str(label_size)
        selected_role: Literal["large", "small"] = desired_role
        if selected_role not in line_printers:
            alt = "small" if selected_role == "large" else "large"
            if alt not in line_printers:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=(
                        f"Line '{selected_line}' has no usable printers "
                        "(needs 'large' or 'small')."
                    ),
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
                detail=(
                    f"Printer config for line '{selected_line}' role "
                    f"'{selected_role}' must include 'ip' and 'port'."
                ),
            )

        # 5) Send to printer
        resp = label_printer_connection(
            label_zpl,
            printer["ip"],
            printer["port"],
        )

        return resp

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail=str(e),
        ) from e


@box_label_router.post("/check")
async def box_label_check(body: BoxLabelCheckRequest) -> Dict[str, Any]:
    product_ids = body.product_ids

    if not product_ids:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="At least one product_id must be provided.",
        )
    try:
        if len(product_ids) == 1:
            info = await check_box_label_exists(f"('{product_ids[0]}')")
            # print("product ids length", product_ids.len())
        else:
            info = await check_box_label_exists(tuple(product_ids))

        if not info:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=("No label configuration found for the provided product_id(s)."),
            )
        return {
            "status": "ok",
            "data": info,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail=str(e),
        ) from e
