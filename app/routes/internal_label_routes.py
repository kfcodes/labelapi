import json

from data_controller_layer.internal_label_controller import *
from data_controller_layer.printer_data_controller import \
    get_pallet_label_printer
from fastapi import APIRouter, Request

# from business_logic_layer.data_controller_layer.label_controllers.print_label_controllers import (
#     get_label_info,
#     print_blank_pallet_label,
#     print_combined_pallet_label,
#     print_large_product_label,
#     print_pallet_label,
#     print_small_product_label,
#     print_specific_label_now,
#     print_specific_label_now_2,
#     print_this_label,
# )


internal_label_router = APIRouter()


# # SAMPLE FOR THE OTHER LABEL ROUTES
# @internal_label_router.get("/this/{qty}")
# async def print_this_label_function(qty: int):
#     response = await print_this_label(qty)
#     return response
#
#
# @internal_label_router.post("/blank_pallet_labels/{printer_id}")
# async def print_blank_label(printer_id: str):
#     response = await print_blank_pallet_labels(printer_id)
#     return response
#


@internal_label_router.post("/blend_label")
async def print_blank_label(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    # printer, site = await get_pallet_label_printer(request)
    # response = await blend_label_function(site, printer, body)

    response = await blend_label_function(body)

    print("Recieved", body)
    return {"Recieved": body}
