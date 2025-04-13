from fastapi import APIRouter, Request
from data_controller_layer.box_label_controller import *

box_label_router = APIRouter()

# print box pallet label for unique product
@box_label_router.post("/print_box_label/{unique_finished_product_id})
async def product_label(unique_finished_product_id: int, body: Request):
    if body:
        body =  await body.json()
        quantity = int(body["quantity"])
        response = await main_print_box_label_function(unique_finished_product_id, quantity)
        return response
    else:
        return "LABEL QUANTITY CANNONT BE EMPTY"

# confirm label information is available
@box_label_router.get("/box_label_check/{product_id}")
async def box_label_check(product_id: str):
    response = await db_check_for_label(product_id)
    return response

# testing route for new label samples
@box_label_router.post("/test_label_route}")
async def test_label():
    response = await print_specific_label_now_2(id)
    return response

# Sync the box label structures with the printers
@box_label_router.post("/sync_box_label_templates")
async def upload_pallet_labels():
    response = await upload_box_label_data_to_printers()
    return response
