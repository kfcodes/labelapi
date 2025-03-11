from fastapi import APIRouter, Request
from business_logic_layer.data_controller_layer.label_controllers.print_label_controllers import print_large_product_label, print_small_product_label, print_pallet_label, print_combined_pallet_label, print_blank_pallet_label, get_label_info, print_this_label, print_specific_label_now, print_specific_label_now_2

pallet_label_router = APIRouter();

@pallet_label_router.get("/pallet_label/{id}")
async def print_pallet_label_function_function(id: int):
    response = await print_pallet_label(id);
    return response

@pallet_label_router.post("/blank_pallet_label")
async def print_blank_label_function():
    response = await print_blank_pallet_label();
    return response;

@pallet_label_router.post("/stacked_pallet_label")
async def print_large_combined_label_function(data: Request):
    json_data =  await data.json();
    response = await print_combined_pallet_label(json_data);
    return response;
