from fastapi import APIRouter, Request
from data_controller_layer.printer_controller import *

printer_controller_router = APIRouter();

@printer_controller_router.on_event("startup")
def startup():
    load_printers_from_file("env/printers.json")

@printer_controller_router.get("/printer")
async def printer_lookup(request: Request, site: str, line: str, use_large: bool = True):
    printer = get_printer(site, line, use_large)
    return {"ip": printer["ip"], "port": printer["port"]}
