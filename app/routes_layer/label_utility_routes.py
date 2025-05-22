from fastapi import APIRouter

from data_controller_layer.box_label_controller import \
    upload_box_label_structures_to_printers
from data_controller_layer.json_controller import load_all_config_data
from data_controller_layer.pallet_label_controller import \
    upload_pallet_label_data_to_printers
from data_controller_layer.printer_data_controller import \
    get_all_printer_connections
from data_controller_layer.utility_label_controller import *

label_utility_router = APIRouter()

@label_utility_router.on_event("startup")
def startup():
    load_all_config_data()


@label_utility_router.post("/sync_label_structures")
async def upload_label_structures_to_all_printers():
    all_printers = get_all_printer_connections()
    pallet_label_response = await upload_pallet_label_data_to_printers(all_printers)
    box_label_response = await upload_box_label_structures_to_printers(all_printers)
    return pallet_label_response, box_label_response

@label_utility_router.get("/this_way_up/{qty}")
async def print_this_label_function(qty: int):
    response = await print_this_label(qty)
    return response


@label_utility_router.post("/print_specific_label")
async def print_specific_label_function():
    response = await print_specific_label_now()
    return response


# testing route for new label samples
@label_utility_router.post("/test_label_route")
async def test_label():
    response = await print_specific_label_now_2(id)
    return response


