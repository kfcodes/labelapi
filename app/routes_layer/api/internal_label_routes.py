from fastapi import APIRouter, Request
from business_logic_layer.data_controller_layer.label_controllers.print_label_controllers import print_large_product_label, print_small_product_label, print_pallet_label, print_combined_pallet_label, print_blank_pallet_label, get_label_info, print_this_label, print_specific_label_now, print_specific_label_now_2

internal_label_router = APIRouter();

# SAMPLE FOR THE OTHER LABEL ROUTES
@internal_label_router.get("/this/{qty}")
async def print_this_label_function(qty: int):
    response = await print_this_label(qty);
    return response;
