from fastapi import APIRouter, Request
from business_logic_layer.data_controller_layer.label_controllers.print_label_controllers import print_large_product_label, print_small_product_label, print_pallet_label, print_combined_pallet_label, print_blank_pallet_label, get_label_info, print_this_label, print_specific_label_now, print_specific_label_now_2

product_label_router = APIRouter();

# CHECK THE DATABASE TO CONFIRM PALLET LABEL INFORMATION IS PRESENT
@product_label_router.get("/label_info/{id}")
async def label_info_function(id: str):
    response = await get_label_info(id);
    return response

# PRINT THE ACTUAL PALLET LABEL FOR THE PRODUCT BY ID
@product_label_router.post("/print_product_label/{id}")
async def product_label_function(id: int, body: Request):
    if body:
        body =  await body.json();
        quantity = int(body["qty"])
        exp = str(body["exp"])
        if body["qtyPerBox"] == 0 or body["qtyPerBox"] == None:
            quantity_in_a_box = 0;
        else:
            quantity_in_a_box = int(body["qtyPerBox"])
        response = await print_large_product_label(id, quantity, quantity_in_a_box, exp);
        return response;
    else:
        return "Request Body cannot be empty"

# TESING EXAMPLE FOR NEW PRODUCT LABELS
@product_label_router.post("/new_product_labe/{id}")
async def print_specific_label_function(id):
    response = await print_specific_label_now_2(id);
    return response;
