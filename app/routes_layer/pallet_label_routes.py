from fastapi import APIRouter, Request
from data_controller_layer.pallet_label_controller import *

pallet_label_router = APIRouter();

@pallet_label_router.get("/pallet_label/{printer_id}/{pallet_id}")
async def print_pallet_label(printer_id: str, pallet_id: int):
    response = await main_pallet_label_function(printer_id, pallet_id);
    return response

@pallet_label_router.post("/blank_pallet_label/{printer_id}")
async def print_blank_label(printer_id: str):
    response = await print_blank_pallet_labels(printer_id);
    return response;

@pallet_label_router.post("/stacked_pallet_label/{printer_id}")
async def print_large_combined_label_function(data: Request, printer_id: str):
    json_data =  await data.json();
    response = await print_combined_pallet_label(json_data, printer_id);
    return response;

@pallet_label_router.post("/sync_pallet_label_structures")
async def upload_pallet_labels():
    response = await upload_pallet_label_data_to_printers();
    return response
