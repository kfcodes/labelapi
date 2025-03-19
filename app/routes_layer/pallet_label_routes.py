from fastapi import APIRouter, Request
from data_controller_layer.pallet_label import main_pallet_label_function, upload_pallet_label_data_to_printers

pallet_label_router = APIRouter();

@pallet_label_router.post("/sync_printers")
async def upload_pallet_labels():
    response = await upload_pallet_label_data_to_printers();
    return response

@pallet_label_router.get("/pallet_label/{pallet_id}/{printer_id}")
async def print_pallet_label(pallet_id: int, printer_id: str):
    response = await main_pallet_label_function(pallet_id, printer_id);
    return response

"""
@pallet_label_router.post("/blank_pallet_label")
async def print_blank_label_function():
    response = await print_blank_pallet_label();
    return response;

@pallet_label_router.post("/stacked_pallet_label")
async def print_large_combined_label_function(data: Request):
    json_data =  await data.json();
    response = await print_combined_pallet_label(json_data);
    return response;
"""
