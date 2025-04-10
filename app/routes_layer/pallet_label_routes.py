from fastapi import APIRouter, Request
from data_controller_layer.pallet_label_controller import *
from data_controller_layer.printer_data_controller import *

pallet_label_router = APIRouter()

@pallet_label_router.get("/pallet_label/{printer_id}/{pallet_id}")
async def print_pallet_label(printer_id: str, pallet_id: int, request: Request):
    printers = get_printers_on_site(request);
    response = await main_pallet_label_function(printers, pallet_id)
    return response

@pallet_label_router.post("/stacked_pallet_label/{printer_id}")
async def print_large_combined_label_function(data: Request, printer_id: str):
    json_data =  await data.json()
    printers = get_printers_on_site(data)
    response = await print_combined_pallet_label(json_data, printer_id)
    return response

@pallet_label_router.post("/sync_pallet_label_structures")
async def upload_pallet_labels():
    all_printers = get_all_printer_connections()
    response = await upload_pallet_label_data_to_printers(all_printers)
    return response
