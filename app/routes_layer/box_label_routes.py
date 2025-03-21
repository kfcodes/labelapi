from fastapi import APIRouter, Request
from data_controller_layer.box_label_controller import main_print_box_label_function, db_check_for_label, print_specific_label_now_2

box_label_router = APIRouter();

# confirm label information is available
@box_label_router.get("/box_label_check/{product_id}")
async def box_label_check(product_id: str):
    response = await db_check_for_label(product_id);
    return response

# print box pallet label for unique product
@box_label_router.post("/print_box_label/{unique_item_id}")
async def product_label(unique_item_id: int, body: Request):
    if body:
        body =  await body.json();
        quantity = int(body["qty"])
        exp = str(body["exp"])
        if body["qtyPerBox"] == 0 or body["qtyPerBox"] == None:
            quantity_in_a_box = 0;
        else:
            quantity_in_a_box = int(body["qtyPerBox"])
        response = await main_print_box_label_function(unique_item_id, quantity, quantity_in_a_box, exp);
        return response;
    else:
        return "Request Body cannot be empty"

# testing route for new label samples
@box_label_router.post("/test_label_route}")
async def test_label():
    response = await print_specific_label_now_2(id);
    return response;
