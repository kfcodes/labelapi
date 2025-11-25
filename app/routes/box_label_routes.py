from http import HTTPStatus
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Request

from app.controllers.box_labels import check_box_label_exists

# from pydantic import BaseModel, ConfigDict, Field, conint

# , main_box_label_function
# from app.controllers.printers import get_printers_on_site  # async, takes Request
# from app.printer_connection.zpl_printer_logic import label_printer_connection

box_label_router = APIRouter()


# def _role_from_label_size(label_size: str) -> Literal["large", "small"]:
#     """
#     Map the label_size string from the controller to a printer role.
#
#     For now:
#       - exactly "large" (case-insensitive) -> large printer
#       - anything else                      -> small printer
#     """
#     return "large" if label_size.lower() == "large" else "small"
#
#
# @box_label_router.post("/box_label/{unique_finished_product_id}/{quantity}")
# async def print_box_label(
#     request: Request,
#     unique_finished_product_id: int,
#     quantity: int,
# ) -> Dict[str, Any]:
#     """
#     Generate label text via the controller, then select a printer and print.
#
#     Path params:
#       - unique_finished_product_id: internal finished product id (int)
#       - quantity: number of labels to print (int > 0)
#
#     Logic:
#       1) Controller generates a SINGLE label for this product:
#            (label_size, label_text)
#       2) Router repeats label_text `quantity` times.
#       3) Router selects a printer based on label_size:
#            - label_size == "large" -> large printer
#            - else                  -> small printer
#       4) Sends the combined payload to the chosen printer.
#     """
#     try:
#         # Validate quantity
#         if quantity <= 0:
#             raise HTTPException(
#                 status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
#                 detail="Quantity must be greater than zero.",
#             )
#
#         # 1) Generate a SINGLE label from the controller (single DB call inside)
#         label_size, label_text = await main_box_label_function(
#             unique_finished_product_id
#         )
#
#         # 2) Repeat the label text N times
#         #    (If label_text is ZPL, this usually means multiple prints)
#         label_payload = label_text * quantity
#
#         # 3) Resolve printers for the caller's site
#         printers_by_line = await get_printers_on_site(request)
#         if not printers_by_line:
#             raise HTTPException(
#                 status_code=HTTPStatus.NOT_FOUND,
#                 detail="No printers configured for site",
#             )
#
#         # For now: just pick the first line in sorted order
#         selected_line = next(iter(sorted(printers_by_line.keys())))
#         line_printers = printers_by_line[selected_line]
#
#         # 4) Decide printer role purely from label_size
#         desired_role: Literal["large", "small"] = _role_from_label_size(label_size)
#
#         # Prefer desired_role; if missing, try the other one as a fallback
#         selected_role: Literal["large", "small"] = desired_role
#         if selected_role not in line_printers:
#             alt = "small" if selected_role == "large" else "large"
#             if alt not in line_printers:
#                 raise HTTPException(
#                     status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#                     detail=(
#                         f"Line '{selected_line}' has no usable printers "
#                         "(needs 'large' or 'small')."
#                     ),
#                 )
#             selected_role = alt
#
#         printer = line_printers[selected_role]
#         if (
#             not isinstance(printer, dict)
#             or "ip" not in printer
#             or "port" not in printer
#         ):
#             raise HTTPException(
#                 status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#                 detail=(
#                     f"Printer config for line '{selected_line}' role "
#                     f"'{selected_role}' must include 'ip' and 'port'."
#                 ),
#             )
#
#         # 5) Send to printer
#         resp = label_printer_connection(
#             label_payload,
#             printer["ip"],
#             printer["port"],
#             timeout=3.0,
#         )
#
#         return {
#             "status": "ok",
#             "response": resp,
#             "label_size": label_size,
#             "quantity": quantity,
#             "selected_line": selected_line,
#             "selected_role": selected_role,
#             "printer": {"ip": printer["ip"], "port": printer["port"]},
#         }
#
#     except HTTPException:
#         raise
#     except ValueError as e:
#         # Bubble up controller/DB errors as 422
#         raise HTTPException(
#             status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
#             detail=str(e),
#         ) from e
#     except Exception as e:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_GATEWAY,
#             detail=str(e),
#         ) from e


@box_label_router.get("/check/{product_id}")
async def box_label_check(product_id: str) -> Dict[str, Any]:
    """
    Check whether label information exists for the given product_id (string).
    """
    try:
        info = await check_box_label_exists(product_id)
        print(info)
        if info is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No label configuration found for product_id '{product_id}'.",
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
