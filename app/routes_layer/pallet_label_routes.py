from fastapi import APIRouter, Request

from data_controller_layer.pallet_label_controller import *
from data_controller_layer.printer_data_controller import (
    get_all_printer_connections, get_pallet_label_printer,
    get_printers_on_site)

pallet_label_router = APIRouter()


@pallet_label_router.get("/pallet_label/{pallet_id}")
async def print_pallet_label(pallet_id: int, request: Request):
    printer, site = await get_pallet_label_printer(request)
    response = await main_pallet_label_function(site, printer, pallet_id)
    return response


@pallet_label_router.post("/stacked_pallet_label")
async def print_large_combined_label_function(data: Request):
    json_data = await data.json()
    printer = await get_pallet_label_printer(data)
    response = await print_combined_pallet_label(json_data, printer)
    return response
