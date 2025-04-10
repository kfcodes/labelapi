from fastapi import APIRouter, Request
from data_controller_layer.pallet_label_controller import *
from data_controller_layer.printer_data_controller import get_printers_on_site, get_all_printer_connections

pallet_label_router = APIRouter()

@pallet_label_router.get("/pallet_label/{pallet_id}")
async def print_pallet_label(pallet_id: int, request: Request):
    printers = get_printers_on_site(request)
    response = await main_pallet_label_function(printers['misc']['pallet_label_printer'], pallet_id)
    return response

@pallet_label_router.post("/stacked_pallet_label")
async def print_large_combined_label_function(data: Request):
    json_data =  await data.json()
    printers = get_printers_on_site(data)
    response = await print_combined_pallet_label(json_data, printers['misc']['pallet_label_printer'])
    return response

@pallet_label_router.post("/sync_pallet_label_structures")
async def upload_pallet_labels():
    all_printers = get_all_printer_connections()
    response = await upload_pallet_label_data_to_printers(all_printers)
    return response
