from fastapi import APIRouter
from data_controller_layer.printer_data_controller import *
from data_controller_layer.pallet_label_controller import upload_pallet_label_data_to_printers
# from data_controller_layer.box_label_controller import upload_box_label_data_to_printers
from data_controller_layer.global_config_controller import load_all_config_data

printer_controller_router = APIRouter()

@printer_controller_router.on_event("startup")
def startup():
    load_all_config_data()

@printer_controller_router.post("/sync_label_structures")
async def upload_label_structures_to_all_printers():
    all_printers = get_all_printer_connections()
    response = await upload_pallet_label_data_to_printers(all_printers)
    # box_label_response = await upload_box_label_data_to_printers(all_printers)
    return response, box_label_response
