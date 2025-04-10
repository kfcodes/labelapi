from fastapi import APIRouter, Request
from data_controller_layer.printer_data_controller import *

printer_controller_router = APIRouter()

@printer_controller_router.on_event("startup")
def startup():
    load_printers_from_file()
    load_site_ip_ranges()
