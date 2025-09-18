from app.controller import (
    get_all_printer_connections,
    load_all_config_data,
    upload_box_label_structures_to_printers,
    upload_pallet_label_data_to_printers,
)
from fastapi import APIRouter, HTTPException

label_utility_router = APIRouter()


@label_utility_router.on_event("startup")
def startup():
    # Load printers, IP ranges, etc., into memory
    load_all_config_data()


@label_utility_router.post("/sync-label-structures")
async def upload_label_structures_to_all_printers():
    try:
        all_printers = get_all_printer_connections()
        pallet_label_response = await upload_pallet_label_data_to_printers(all_printers)
        box_label_response = await upload_box_label_structures_to_printers(all_printers)
        return {"pallet": pallet_label_response, "box": box_label_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# The older utility endpoints referenced functions that aren’t implemented in your controllers.
# If you need them, implement in app/controller/utility_label_controller.py and re-export via the facade.
# For now, omit or keep placeholders that return 501 to avoid runtime errors.
