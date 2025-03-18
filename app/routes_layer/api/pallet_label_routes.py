from fastapi import APIRouter, Request
from data_controller_layer.pallet_label import format_and_print_pallet_label, upload_pallet_label_data_to_printers

pallet_label_router = APIRouter();

@pallet_label_router.post("/upload_pallet_labels")
async def upload_pallet_labels():
    response = await upload_pallet_label_data_to_printers();
    return response

@pallet_label_router.get("/pallet_label/{pallet_id}/{printer_id}")
async def print_pallet_label_function_function(pallet_id: int, printer_id: str):
    response = await format_and_print_pallet_label(pallet_id, printer_id);
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
