from fastapi import APIRouter, Request
from data_controller_layer.utility_label_controller import *

utility_label_router = APIRouter()

# LABEL PRINTER API ROUTES
@utility_label_router.get("/this_way_up/{qty}")
async def print_this_label_function(qty: int):
    response = await print_this_label(qty)
    return response

@utility_label_router.post("/print_specific_label")
async def print_specific_label_function():
    response = await print_specific_label_now()
    return response

# testing route for new label samples
@utility_label_router.post("/test_label_route")
async def test_label():
    response = await print_specific_label_now_2(id)
    return response
