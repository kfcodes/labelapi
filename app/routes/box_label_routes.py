from data_controller_layer.box_label_controller import *
from data_controller_layer.printer_data_controller import *
from fastapi import APIRouter, Request

box_label_router = APIRouter()


# print box pallet label for unique product
@box_label_router.post("/print_box_label/{unique_finished_product_id}")
async def product_label(unique_finished_product_id: int, body: Request):
    if body:
        body = await body.json()
        quantity = int(body["quantity"])
        printers_on_site = await get_box_label_printers(body)
        response = await main_print_box_label_function(
            unique_finished_product_id, body, quantity, printers_on_site
        )
        return response
    return "LABEL QUANTITY CANNONT BE EMPTY"


# check for box label_data
@box_label_router.get("/box_label_check/{product_id}")
async def box_label_check(product_id: str):
    response = await db_check_for_label(product_id)
    return response
