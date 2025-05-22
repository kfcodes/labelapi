from fastapi import APIRouter, Request

from data_controller_layer.pallet_label_controller import *
from data_controller_layer.printer_data_controller import \
    get_pallet_label_printer

pallet_label_router = APIRouter()


@pallet_label_router.get("/pallet_label/{pallet_id}")
async def print_pallet_label(pallet_id: int, request: Request):
    printer, site = await get_pallet_label_printer(request)
    response = await main_pallet_label_function(site, printer, pallet_id)
    return response


@pallet_label_router.put("/combine_pallets")
async def print_combined_pallet_label(body: Request):
    if body:
        body = await body.json()
        printer = await get_pallet_label_printer(body)
        pallet_id = int(max(body["pallet_list"]))
        pallet_list = tuple(body["pallet_list"])
        height = int(body["height"])
        response = await generate_and_print_combo_label(
            printer, pallet_id, height, pallet_list
        )
        return response
    else:
        return "Request Body cannot be empty"
